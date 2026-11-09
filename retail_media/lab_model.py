"""Modelo de transiciones aprendido y control mediante Bellman de horizonte finito.

La recompensa es primera conversión de una sesión. CPC, puja y presupuesto no
son entradas de la recompensa ni del estimador de respuesta. El modelo aprende
solo eventos de acciones ejecutadas; la política no recibe los sorteos ni las
probabilidades verdaderas del generador.
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np


SCHEMA = 'retail_lab_transition_v2_plp16'
SERVING_ID = 'plp16-min1-v1'
ADS_PER_PLP = 16
N_ACTIONS = 1 + 3 * ADS_PER_PLP
SLOTS = (3, 4, 5, 6, 11, 12, 13, 14)
POSITION_MULTIPLIERS = (1.30, 1.18, 1.08, 1.00, .90, .82, .76, .70)
CATEGORIES = ('Tecnología', 'Hogar', 'Deporte')
BRANDS = ('Nova', 'Casa', 'Pulse')
CPC_CENTS = (120, 100, 80)
DAILY_BUDGET_CENTS = (13333, 8333, 5000)
NAMES = (('Auriculares Pop', 'Auriculares Studio'),
         ('Lámpara Halo', 'Lámpara Forma'), ('Zapatillas Sprint', 'Zapatillas Motion'))
IMAGE_KEYS = ('tech', 'home', 'sport')
EXPOSURE_COEFFICIENTS = {
    'position_decay': .017, 'depth_retention': .9, 'fatigue_cap': 7,
    'ad_fatigue_floor': .55, 'ad_fatigue_step': .035,
    'organic_fatigue_floor': .70, 'organic_fatigue_step': .018,
    'intent_mismatch': .25,
}


def catalogue():
    return [dict(action=1 + category * ADS_PER_PLP + variant,
                 id=f'{IMAGE_KEYS[category]}-ad-{variant:02d}',
                 name=f'{BRANDS[variant % 3]} Producto {variant + 1}',
                 brand=BRANDS[variant % 3], brand_id=variant % 3,
                 category=CATEGORIES[category], category_id=category,
                 variant=variant, quality=variant % 2,
                 rating=4.8 if variant % 2 == 0 else 4.5,
                 image_key=f'{IMAGE_KEYS[category]}-organic-{variant:02d}',
                 price_cents=(4900, 3900, 7900)[category] + variant * 500,
                 promotion='Patrocinado')
            for category in range(3) for variant in range(ADS_PER_PLP)]


CATALOGUE = catalogue()


def organic_product(segment, position=1):
    quality = int(position % 2 == 0)
    return dict(action=0, id=f'organic-{segment}-{position}',
                name=NAMES[segment][quality], brand='Selección orgánica', brand_id=None,
                category=CATEGORIES[segment], category_id=segment, quality=quality,
                image_key=f'{IMAGE_KEYS[segment]}-{quality}', rating=4.6,
                price_cents=(6500, 4800, 8900)[segment], promotion=None)


def visible_factor(context, action):
    """Public structural exposure features, not hidden purchase propensity."""
    position = int(context['position'])
    depth = int(context['depth'])
    coefficients = EXPOSURE_COEFFICIENTS
    ads = min(coefficients['fatigue_cap'], int(context['ads_seen']))
    factor = float(np.exp(-coefficients['position_decay'] * (position - 1)) * coefficients['depth_retention'] ** depth)
    if action:
        factor *= POSITION_MULTIPLIERS[SLOTS.index(position)]
        factor *= max(coefficients['ad_fatigue_floor'], 1 - coefficients['ad_fatigue_step'] * ads)
        if CATALOGUE[action - 1]['category_id'] != context['segment']:
            factor *= coefficients['intent_mismatch']
    else:
        factor *= max(coefficients['organic_fatigue_floor'], 1 - coefficients['organic_fatigue_step'] * ads)
    return factor


def fingerprint():
    return hashlib.sha256(json.dumps({'schema': SCHEMA, 'catalogue': CATALOGUE,
                                      'slots': SLOTS, 'visibility': POSITION_MULTIPLIERS,
                                      'exposure_coefficients': EXPOSURE_COEFFICIENTS},
                                     sort_keys=True).encode()).hexdigest()


class LabModel:
    """Empirical transition kernel + finite-horizon, undiscounted value iteration."""
    def __init__(self):
        shape = (3, N_ACTIONS)
        self.exposures = np.zeros(shape, dtype=float)
        self.trials = np.zeros(shape, dtype=np.int64)
        self.clicks = np.zeros(shape, dtype=np.int64)
        self.purchases = np.zeros(shape, dtype=np.int64)
        self.leaves = np.zeros(shape, dtype=np.int64)
        self.continuation = np.array([.5, .4], dtype=float)
        self.metadata = {'trained': False, 'schema': SCHEMA,
                         'algorithm': 'Empirical model-based RL / finite-horizon Bellman',
                         'reward': 'first_session_purchase', 'reward_max_per_session': 1}
        self._q = None
        self._estimate_cache = {}

    def observe(self, context, action, *, clicked, purchased, left):
        if type(action) is not int or not 0 <= action < N_ACTIONS:
            raise ValueError('Acción fuera del catálogo')
        if purchased and not clicked:
            raise ValueError('Una compra debe estar precedida de un clic')
        segment = int(context['segment'])
        key = segment, action
        self.trials[key] += 1
        self.exposures[key] += visible_factor(context, action)
        self.clicks[key] += bool(clicked)
        self.purchases[key] += bool(purchased)
        self.leaves[key] += bool(left)
        self._q = None
        self._estimate_cache.clear()

    def estimates(self, context, action):
        segment = int(context['segment'])
        cache_key = (segment, int(context['position']), int(context['depth']), min(7, int(context['ads_seen'])), action)
        if cache_key in self._estimate_cache:
            return self._estimate_cache[cache_key]
        key = segment, action
        factor = visible_factor(context, action)
        # Gamma-Poisson exposure adjustment and Beta conditional purchase model.
        # These are model assumptions, not a distribution-free safety proof.
        click_shape = self.clicks[key] + .5
        click_rate = self.exposures[key] + 10.
        base_click = click_shape / click_rate
        buy_a = self.purchases[key] + 1.
        buy_b = self.clicks[key] - self.purchases[key] + 19.
        conditional_buy = buy_a / (buy_a + buy_b)
        click_p = float(np.clip(base_click * factor, 0, .95))
        purchase_p = float(np.clip(click_p * conditional_buy, 0, .95))
        var_click = click_shape / (click_rate ** 2) * factor ** 2
        var_buy = buy_a * buy_b / ((buy_a + buy_b) ** 2 * (buy_a + buy_b + 1))
        sd = float(np.sqrt(max(0, conditional_buy ** 2 * var_click + click_p ** 2 * var_buy)))
        leave = float((self.leaves[key] + .5) / (self.trials[key] + 400.))
        estimate = {'click_probability': click_p, 'purchase_probability': purchase_p,
                    'purchase_lower': max(0., purchase_p - sd),
                    'uncertainty': sd, 'leave_probability': leave,
                    'observations': int(self.trials[key])}
        self._estimate_cache[cache_key] = estimate
        return estimate

    def _build_values(self):
        # Position, block depth and fatigue are explicit. Future action masks are
        # approximated by the safe catalogue; exact cash/slate masks apply now.
        # No access to the future session length is needed: continuation comes
        # from observed traffic and is a forecast, not a revealed random draw.
        q = np.zeros((3, 3, 20, 8, N_ACTIONS), dtype=float)
        value = np.zeros((3, 3, 21, 8), dtype=float)
        for segment in range(3):
            for depth in range(2, -1, -1):
                for position in range(20, 0, -1):
                    actions = [0] + [p['action'] for p in CATALOGUE if p['category_id'] == segment] if position in SLOTS else (0,)
                    for fatigue in range(8):
                        context = dict(segment=segment, position=position, depth=depth, ads_seen=fatigue)
                        reference = self.estimates(context, 0)['purchase_probability']
                        for action in actions:
                            estimate = self.estimates(context, action)
                            next_fatigue = min(7, fatigue + bool(action))
                            if position == 20:
                                future = value[segment, depth + 1, 0, next_fatigue] * self.continuation[depth] if depth < 2 else 0.
                            else:
                                future = value[segment, depth, position, next_fatigue]
                            p = estimate['purchase_probability']
                            q[segment, depth, position - 1, fatigue, action] = p + (1 - p) * (1 - estimate['leave_probability']) * future
                        safe = [a for a in actions if a == 0 or self.estimates(context, a)['purchase_lower'] >= reference]
                        value[segment, depth, position - 1, fatigue] = max(q[segment, depth, position - 1, fatigue, safe])
        self._q = q

    def scores(self, context):
        if context.get('converted', False):
            return np.zeros(N_ACTIONS, dtype=float)
        if self._q is None:
            self._build_values()
        return self._q[int(context['segment']), min(2, int(context['depth'])),
                       int(context['position']) - 1, min(7, int(context['ads_seen']))].copy()

    def identity(self):
        """Content identity of learned parameters and structural interpretation.

        Training duration, timestamps, display labels and other run metadata
        cannot change this ID. Dtype, shape and raw content delimit each array.
        """
        digest = hashlib.sha256()
        digest.update(fingerprint().encode('ascii'))
        for key in ('exposures', 'trials', 'clicks', 'purchases', 'leaves', 'continuation'):
            array = np.ascontiguousarray(getattr(self, key))
            digest.update(json.dumps([key, array.dtype.str, list(array.shape)], separators=(',', ':')).encode('ascii'))
            digest.update(array.tobytes())
        return digest.hexdigest()

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        metadata = {**self.metadata, 'schema': SCHEMA, 'fingerprint': fingerprint(),
                    'model_id': self.identity()}
        self.metadata = metadata
        with path.open('wb') as handle:
            np.savez_compressed(handle, exposures=self.exposures, trials=self.trials,
                                clicks=self.clicks, purchases=self.purchases, leaves=self.leaves,
                                continuation=self.continuation, metadata=json.dumps(metadata))

    @classmethod
    def load(cls, path):
        model = cls()
        with np.load(path, allow_pickle=False) as data:
            metadata = json.loads(str(data['metadata']))
            if metadata.get('schema') != SCHEMA or metadata.get('fingerprint') != fingerprint():
                raise ValueError('Modelo incompatible con el motor del laboratorio')
            for key in ('exposures', 'trials', 'clicks', 'purchases', 'leaves'):
                value = data[key]
                if value.shape != (3, N_ACTIONS) or not np.isfinite(value).all() or np.any(value < 0):
                    raise ValueError('Estadísticas del modelo inválidas')
                setattr(model, key, value.copy())
            if np.any(model.purchases > model.clicks) or np.any(model.clicks > model.trials) or np.any(model.leaves > model.trials):
                raise ValueError('Contabilidad de transiciones inconsistente')
            model.continuation = data['continuation'].copy()
            if model.continuation.shape != (2,) or not np.isfinite(model.continuation).all() or np.any((model.continuation < 0) | (model.continuation > 1)):
                raise ValueError('Continuación de tráfico inválida')
            model.metadata = metadata
            if metadata.get('model_id') != model.identity():
                raise ValueError('La identidad del modelo no coincide con sus parámetros')
        return model


@dataclass(frozen=True)
class Selection:
    action: int
    reason: str
    forced_pacing: bool
    conflict: bool
    candidates: list
    coverage_exploration: bool = False


def select_action(model, context, allowed, policy, spent, budgets, impressions, progress, rng, ad_impressions=None):
    """Budget/duplicate legality precedes learned quality and delivery pacing."""
    allowed = [a for a in allowed if a == 0 or CATALOGUE[a - 1]['category_id'] == context['segment']]
    scores = model.scores(context)
    reference = model.estimates(context, 0)['purchase_probability']
    safe = [0] + [a for a in allowed if a and model.estimates(context, a)['purchase_lower'] >= reference
                  and model.estimates(context, a)['observations'] >= 100]
    urgency = [progress - s / max(1, b) if b else -1 for s, b in zip(spent, budgets)]
    lag = int(np.argmax(urgency))
    urgent = progress >= .12 and urgency[lag] > .07
    forced = False
    conflict = False
    candidates = []
    for action in [0] + [p['action'] for p in CATALOGUE if p['category_id'] == context['segment']]:
        product = CATALOGUE[action - 1] if action else organic_product(context['segment'], context['position'])
        estimate = model.estimates(context, action)
        legal = action in allowed
        quality_ok = action in safe
        reason = 'Disponible' if legal else 'Sin saldo para un clic, repetido en este bloque o fuera del ritmo de entrega'
        if legal and not quality_ok:
            reason = 'Respuesta conservadora inferior al orgánico o evidencia insuficiente'
        if context.get('converted') and action:
            reason = 'La sesión ya convirtió; no hay recompensa adicional por publicidad'
        selector_ok = quality_ok or policy not in ('safe_rl', 'greedy')
        if policy == 'quality' and action:
            selector_ok = product['category_id'] == context['segment']
            if not selector_ok:
                reason = 'La referencia de calidad conserva orgánico sin un producto de calidad y categoría coincidente'
        if policy == 'organic' and action:
            selector_ok = False
            reason = 'La referencia orgánica no inserta publicidad'
        candidates.append({'action': action, 'name': product['name'], 'brand': product['brand'],
                           'brand_id': product['brand_id'], 'score': float(scores[action]),
                           'estimated_conversion': estimate['purchase_probability'],
                           'lower_estimate': estimate['purchase_lower'], 'observations': estimate['observations'],
                           'eligible': bool(legal and selector_ok and (not context.get('converted') or action == 0)),
                           'budget_eligible': legal, 'quality_eligible': quality_ok, 'reason': reason})
    if context.get('converted') or policy == 'organic':
        return Selection(0, 'La sesión ya convirtió; se conserva orgánico' if context.get('converted') else 'Política de referencia orgánica', False, False, candidates)
    pool = safe if policy in ('safe_rl', 'greedy') else list(allowed)
    # Shared delivery contract: an initial real exposure before concentrating.
    # Exact budget/slate masks and the policy's quality filter already apply.
    unseen = [a for a in pool if a and ad_impressions is not None and ad_impressions[a] < 1]
    if unseen:
        action = max(unseen, key=lambda a: (float(scores[a]), -a))
        return Selection(int(action), 'Primera exposición: cobertura mínima entre anuncios aptos de esta PLP',
                         False, False, candidates, True)
    if urgent and policy != 'organic':
        recovery = [a for a in pool if a and CATALOGUE[a - 1]['brand_id'] == lag]
        if recovery:
            pool = recovery
            forced = True
        elif policy in ('safe_rl', 'greedy'):
            conflict = True
    if len(pool) == 1:
        action = pool[0]
    elif policy == 'random':
        action = int(rng.choice(pool))
    elif policy == 'bid':
        ads = [a for a in pool if a]
        action = max(ads, key=lambda a: CPC_CENTS[CATALOGUE[a - 1]['brand_id']]) if ads else 0
    elif policy == 'relevance':
        # Observable category + rating heuristic. Rating can be misleading in
        # the synthetic clickbait catalogue; the quality comparator is stronger.
        action = max(pool, key=lambda a: .5 if a == 0 else float(CATALOGUE[a - 1]['category_id'] == context['segment']) + .1 * CATALOGUE[a - 1]['rating'])
    elif policy == 'quality':
        action = max(pool, key=lambda a: (-1, -a) if a == 0 else (CATALOGUE[a - 1]['quality'], -a))
    elif policy == 'greedy':
        action = max(pool, key=lambda a: (model.estimates(context, a)['purchase_probability'], -a))
    else:
        # Deterministic tie-breaking makes frozen inference reproducible.
        action = max(pool, key=lambda a: (float(scores[a]), -a))
    reason = ('Recuperación de marca atrasada entre opciones aptas' if forced else
              'Mayor valor de conversión de sesión estimado por Bellman' if policy == 'safe_rl' and action else
              'Mayor compra inmediata estimada; sin planificar el resto de la sesión' if policy == 'greedy' else
              'Se conserva el orgánico: mayor valor estimado o evidencia insuficiente' if policy == 'safe_rl' else
              'Selección según ' + policy)
    if conflict:
        reason += '; existe conflicto entre entrega pendiente y calidad estimada'
    return Selection(int(action), reason, forced, conflict, candidates)
