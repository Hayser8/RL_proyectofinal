"""Motor causal del laboratorio: exposición → clic → compra → abandono.

Una compra aporta recompensa solo si es la primera de la sesión, con idéntica
regla para orgánico y patrocinado. El dinero siempre es contabilidad CPC y una
restricción; nunca se transforma en una recompensa por gastar.
"""
from collections import deque
from copy import deepcopy
from pathlib import Path

import numpy as np

from .lab_catalog import present_candidate, present_product
from .lab_competition import CompetitionAudit

from .lab_model import (BRANDS, CATALOGUE, CATEGORIES, CPC_CENTS, DAILY_BUDGET_CENTS,
                        SLOTS, N_ACTIONS, SERVING_ID, LabModel, organic_product, select_action, visible_factor)


SCENARIOS = {
    'balanced': {'name': 'Mercado equilibrado', 'description': 'Tráfico y demanda habituales; promociones con clics que no siempre compran.', 'traffic_factor': 1.},
    'clickbait': {'name': 'Clics sin intención', 'description': 'Las ofertas de CTR alto atraen más clics, pero convierten menos y generan más abandono.', 'traffic_factor': 1.},
    'scarce': {'name': 'Tráfico escaso', 'description': 'Solo llega el 22% del tráfico previsto; la inversión puede ser inviable.', 'traffic_factor': .22},
    'shift': {'name': 'Cambio de demanda', 'description': 'La mayoría de usuarios busca deporte y cambia la respuesta de una marca.', 'traffic_factor': 1.},
}


def _response_rates(context, action, scenario='balanced'):
    """Private synthetic ground truth. Neither state nor policy receives it."""
    if action == 0:
        ctr, buy, leave = .052, .088, .0012
    else:
        product = CATALOGUE[action - 1]
        quality, brand = product['quality'], product['brand_id']
        variant = product['variant']
        ctr = .080 + ((variant * 7) % 5) * .003
        buy = ((.135 if quality == 0 else .195) + (((variant * 11) % 7) - 3) * .004) * (1.0, .98, 1.04)[brand]
        leave = .0025 if quality == 0 else .0015
        if product['category_id'] != context['segment']:
            buy *= .35
        if scenario == 'clickbait' and quality == 0:
            ctr *= 1.7
            buy *= .2
            leave *= 2.
        if scenario == 'shift' and brand == 2:
            ctr *= .82
            buy *= .77
    ctr *= visible_factor(context, action)
    return min(.95, ctr), min(.95, buy), min(.3, leave)


def sample_transition(context, action, draws, scenario='balanced'):
    """Only factual, executed-action response; no probabilities in the return."""
    click_p, buy_p, leave_p = _response_rates(context, action, scenario)
    clicked = bool(draws[0] < click_p)
    purchased = bool(clicked and draws[1] < buy_p)
    if action and CATALOGUE[action - 1]['quality'] == 0 and clicked:
        leave_p += .035
    left = bool(draws[2] < min(.4, leave_p))
    reward = float(purchased and not context.get('converted', False))
    return {'clicked': clicked, 'purchased': purchased, 'left': left, 'reward': reward}


class LabSimulation:
    def __init__(self, seed=60000, policy='safe_rl', scenario='balanced', sessions=1000,
                 budget_scale=1., model_path=None, *, model=None, audit_competition=False):
        if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
            raise ValueError('La semilla debe ser un entero entre 0 y 4294967295')
        if type(sessions) is not int or not 1 <= sessions <= 20000:
            raise ValueError('Las sesiones previstas deben estar entre 1 y 20000')
        if type(budget_scale) not in (float, int) or not np.isfinite(budget_scale) or not 0 <= budget_scale <= 10:
            raise ValueError('El factor de presupuesto debe estar entre 0 y 10')
        if policy not in ('safe_rl', 'organic', 'relevance', 'quality', 'greedy', 'bid', 'random'):
            raise ValueError('Política desconocida')
        if scenario not in SCENARIOS:
            raise ValueError('Escenario desconocido')
        self.seed, self.policy, self.scenario = seed, policy, scenario
        self.requested_sessions = sessions
        self.sessions = max(1, int(sessions * SCENARIOS[scenario]['traffic_factor']))
        self.budgets = [int(value * budget_scale) for value in DAILY_BUDGET_CENTS]
        self.spent = [0, 0, 0]
        self.brand_impressions = [0, 0, 0]
        self.brand_clicks = [0, 0, 0]
        self.ad_impressions = [0] * N_ACTIONS
        self.coverage_decisions = 0
        self.model = model if model is not None else LabModel.load(model_path or Path(__file__).resolve().parents[1] / 'artifacts' / 'lab_model.npz')
        self.competition = CompetitionAudit(self.sessions, self.model) if audit_competition else None
        self.rng = np.random.default_rng(seed + 1000000)
        traffic_rng = np.random.default_rng(seed)
        weights = [.15, .2, .65] if scenario == 'shift' else [.45, .35, .20]
        self._segments = traffic_rng.choice(3, self.sessions, p=weights)
        self._depths = traffic_rng.choice([1, 2, 3], self.sessions, p=[.5, .3, .2])
        self._draws = traffic_rng.random((self.sessions, 60, 3))
        self.done = False
        self.session = 0
        self.cursor = 0
        self.ads_seen = 0
        self.converted = False
        self.used = set()
        self.sessions_completed = 0
        self.converted_sessions = 0
        self.organic_converted_sessions = 0
        self.clicks = 0
        self.item_purchases = 0
        self.purchase_rewards = 0.
        self.sponsored_impressions = 0
        self.product_impressions = 0
        self.forced_decisions = 0
        self.conflicts = 0
        self.block_products = self._new_block()
        self.completed_blocks = deque(maxlen=2)
        self.events = deque(maxlen=40)
        self.last_decision = None
        self._event_number = 0
        self._seek_decision()

    def _new_block(self):
        segment = int(self._segments[self.session])
        return [{**present_product(organic_product(segment, position), self.session + self.cursor // 20), 'position': position,
                 'sku_index': (position - 1 + (self.session + self.cursor // 20) * 7) % 20,
                 'sponsored': False, 'status': 'pending', 'observed': False,
                 'clicked': None, 'purchase': None, 'cost_cents': None}
                for position in range(1, 21)]

    def _context(self):
        return {'segment': int(self._segments[self.session]), 'position': self.cursor % 20 + 1,
                'depth': self.cursor // 20, 'ads_seen': self.ads_seen, 'converted': self.converted,
                'catalogue_rotation': self.session + self.cursor // 20}

    def _allowed(self):
        actions = [0]
        progress = self.sessions_completed / self.sessions
        for product in CATALOGUE:
            if product['category_id'] != int(self._segments[self.session]):
                continue
            if any(card['observed'] and card['sku_index'] == product['variant'] for card in self.block_products):
                continue
            brand = product['brand_id']
            if product['action'] in self.used or self.spent[brand] + CPC_CENTS[brand] > self.budgets[brand]:
                continue
            # Delivery has an upper pacing cap as well as a lower recovery signal.
            if self.spent[brand] / max(1, self.budgets[brand]) > progress + .14:
                continue
            actions.append(product['action'])
        return actions

    def _record(self, kind, text, **values):
        self._event_number += 1
        self.events.append({'id': self._event_number, 'kind': kind, 'text': text,
                            'session': self.session + 1, **values})

    def _view(self, action):
        context = self._context()
        position = context['position']
        if action and position not in SLOTS:
            raise ValueError('Esta posición siempre es orgánica')
        if action:
            product = CATALOGUE[action - 1]
            brand = product['brand_id']
            if product['category_id'] != context['segment']:
                raise ValueError('El anuncio no pertenece a esta PLP')
            if action in self.used or self.spent[brand] + CPC_CENTS[brand] > self.budgets[brand]:
                raise ValueError('Producto repetido o sin saldo para un clic')
        outcome = sample_transition(context, action, self._draws[self.session, self.cursor], self.scenario)
        cost = 0
        self.product_impressions += 1
        self.clicks += int(outcome['clicked'])
        self.item_purchases += int(outcome['purchased'])
        self.purchase_rewards += outcome['reward']
        self.converted = self.converted or outcome['purchased']
        if action:
            self.used.add(action)
            self.ads_seen += 1
            self.sponsored_impressions += 1
            self.brand_impressions[brand] += 1
            self.ad_impressions[action] += 1
            if outcome['clicked']:
                cost = CPC_CENTS[brand]
                self.spent[brand] += cost
                self.brand_clicks[brand] += 1
        if self.competition is not None and position in SLOTS:
            self.competition.observe_action(context, action, outcome, cost)
        raw_product = CATALOGUE[action - 1] if action else organic_product(context['segment'], position)
        product = present_product(raw_product, context['catalogue_rotation']) if action else dict(self.block_products[position - 1])
        if action:
            product['sku_index'] = raw_product['variant']
            # Swap the unobserved organic copy with the displaced SKU: no visual
            # duplicates and no changes to already observed products.
            displaced = dict(self.block_products[position - 1])
            for index, card in enumerate(self.block_products):
                if index != position - 1 and not card['observed'] and card['sku_index'] == product['sku_index']:
                    self.block_products[index] = {**displaced, 'position': index + 1}
                    break
        self.block_products[position - 1] = {**product, 'position': position, 'sponsored': bool(action),
                                             'status': 'observed', 'observed': True,
                                             'clicked': outcome['clicked'], 'purchase': outcome['purchased'],
                                             'cost_cents': cost, 'reward': outcome['reward']}
        if outcome['clicked']:
            self._record('purchase' if outcome['purchased'] else 'click',
                         ('Compra' if outcome['purchased'] else 'Clic') + ' en ' + product['name'],
                         position=position, sponsored=bool(action), cost_cents=cost, reward=outcome['reward'])
        self.cursor += 1
        finished_block = self.cursor % 20 == 0
        left = outcome['left']
        if finished_block or left:
            for card in self.block_products:
                if not card['observed']:
                    card['status'] = 'not_viewed' if left else 'pending'
            self.completed_blocks.append({'session': self.session + 1, 'block': context['depth'] + 1,
                                          'segment': CATEGORIES[context['segment']],
                                          'products': deepcopy(self.block_products)})
        if left or self.cursor >= int(self._depths[self.session]) * 20:
            self._finish_session()
        elif finished_block:
            self.used.clear()
            self.block_products = self._new_block()
        return context, outcome, product, cost

    def _organic_reference(self, session):
        converted = False
        for cursor in range(int(self._depths[session]) * 20):
            context = dict(segment=int(self._segments[session]), position=cursor % 20 + 1,
                           depth=cursor // 20, ads_seen=0, converted=converted)
            outcome = sample_transition(context, 0, self._draws[session, cursor], self.scenario)
            converted = converted or outcome['purchased']
            if outcome['left']:
                break
        return converted

    def _finish_session(self):
        if self.competition is not None:
            self.competition.close_visit(int(self._segments[self.session]))
        self.converted_sessions += int(self.converted)
        self.organic_converted_sessions += int(self._organic_reference(self.session))
        self.sessions_completed += 1
        self.session += 1
        if self.session >= self.sessions:
            self.done = True
            return
        self.cursor = 0
        self.ads_seen = 0
        self.converted = False
        self.used.clear()
        self.block_products = self._new_block()

    def _seek_decision(self):
        while not self.done and self.cursor % 20 + 1 not in SLOTS:
            self._view(0)

    def advance(self, steps=1):
        if type(steps) is not int or not 1 <= steps <= 200:
            raise ValueError('Avanza entre 1 y 200 decisiones por solicitud')
        for _ in range(steps):
            if self.done:
                break
            context = self._context()
            organic_preview = dict(self.block_products[context['position'] - 1])
            selection = select_action(self.model, context, self._allowed(), self.policy,
                                      self.spent, self.budgets, self.brand_impressions,
                                      self.sessions_completed / self.sessions, self.rng, self.ad_impressions)
            for candidate in selection.candidates:
                if candidate['action'] and not candidate['budget_eligible']:
                    sku = CATALOGUE[candidate['action'] - 1]['variant']
                    if candidate['action'] in self.used or any(card['observed'] and card['sku_index'] == sku for card in self.block_products):
                        candidate['exclusion_code'] = 'duplicate'
                        candidate['reason'] = 'Este producto ya apareció en el bloque, de forma orgánica o patrocinada'
            self.coverage_decisions += int(selection.coverage_exploration)
            if self.competition is not None:
                self.competition.observe_decision(context, selection,
                                                  policy=self.policy, spent=self.spent,
                                                  budgets=self.budgets, used=self.used)
            self.forced_decisions += int(selection.forced_pacing)
            self.conflicts += int(selection.conflict)
            guidance = {'segment_id': context['segment'], 'segment': CATEGORIES[context['segment']],
                        'converted_before': bool(context['converted']), 'ads_seen': int(context['ads_seen']),
                        'remaining_cents': [int(b - s) for b, s in zip(self.budgets, self.spent)]}
            session, block = self.session + 1, context['depth'] + 1
            _, outcome, product, cost = self._view(selection.action)
            estimate = self.model.estimates(context, selection.action)
            self.last_decision = {'session': session, 'block': block, 'position': context['position'],
                                  'action': selection.action, 'product_name': product['name'], 'guidance': guidance,
                                  'brand': product['brand'], 'brand_id': product['brand_id'],
                                  'reason': selection.reason, 'forced_pacing': selection.forced_pacing,
                                  'constraint_conflict': selection.conflict,
                                  'coverage_exploration': selection.coverage_exploration,
                                  'estimated_conversion': estimate['purchase_probability'],
                                  'reward': outcome['reward'], 'clicked': outcome['clicked'],
                                  'purchase': outcome['purchased'], 'cost_cents': cost,
                                  'candidates': [{**present_candidate(c, context), **({k: organic_preview[k] for k in ('name', 'image_key', 'catalogue_id', 'price_cents') if k in organic_preview} if c['action'] == 0 else {})} for c in selection.candidates]}
            self._record('decision', selection.reason, position=context['position'],
                         action=selection.action, brand=product['brand'], session=session)
            self._seek_decision()
        return self.snapshot()

    def metrics(self):
        closed = self.sessions_completed
        cvr = self.converted_sessions / closed if closed else None
        organic = self.organic_converted_sessions / closed if closed else None
        coverage = []
        for category in range(3):
            counts = [self.ad_impressions[p['action']] for p in CATALOGUE if p['category_id'] == category]
            coverage.append({'category': CATEGORIES[category], 'served': sum(n >= 1 for n in counts),
                             'target': len(counts), 'minimum': min(counts), 'complete': all(n >= 1 for n in counts)})
        return {'sessions_completed': closed, 'sessions_target': self.sessions,
                'sessions_started': min(self.sessions, self.session + int(not self.done)),
                'session_cvr': cvr, 'organic_session_cvr': organic,
                'delta_cvr': cvr - organic if closed else None,
                'converted_sessions': self.converted_sessions,
                'organic_converted_sessions': self.organic_converted_sessions,
                'spend_cents': self.spent.copy(), 'budget_cents': self.budgets.copy(),
                'remaining_cents': [b - s for b, s in zip(self.budgets, self.spent)],
                'brand_impressions': self.brand_impressions.copy(), 'brand_clicks': self.brand_clicks.copy(),
                'ad_impressions': self.ad_impressions.copy(),
                'ads_with_impressions': sum(n > 0 for n in self.ad_impressions[1:]),
                'ads_target': len(CATALOGUE), 'coverage_decisions': self.coverage_decisions,
                'coverage_by_plp': coverage,
                'sponsored_impressions': self.sponsored_impressions,
                'product_impressions': self.product_impressions, 'clicks': self.clicks,
                'purchases': self.item_purchases, 'session_rewards': self.purchase_rewards,
                'sponsored_ctr': sum(self.brand_clicks) / self.sponsored_impressions if self.sponsored_impressions else None,
                'delivery': [s / b if b else 1. for s, b in zip(self.spent, self.budgets)],
                'pacing_interventions': self.forced_decisions,
                'constraint_conflicts': self.conflicts,
                'budget_overshoots': sum(s > b for s, b in zip(self.spent, self.budgets))}

    def snapshot(self):
        if self.done:
            current = deepcopy(self.completed_blocks[-1]) if self.completed_blocks else None
            if current:
                current.update(position=None, category_id=None)
        else:
            current = {'session': self.session + 1, 'block': self.cursor // 20 + 1,
                       'segment': CATEGORIES[int(self._segments[self.session])],
                       'category_id': int(self._segments[self.session]),
                       'position': self.cursor % 20 + 1, 'products': deepcopy(self.block_products)}
        metrics = self.metrics()
        return {'seed': self.seed, 'policy': self.policy, 'scenario': self.scenario,
                'serving_id': SERVING_ID,
                'scenario_name': SCENARIOS[self.scenario]['name'],
                'requested_sessions': self.requested_sessions,
                'metrics': metrics, 'current': current,
                'last_decision': deepcopy(self.last_decision),
                'completed_blocks': list(deepcopy(self.completed_blocks)),
                'events': list(deepcopy(self.events)),
                'progress': self.sessions_completed / self.sessions, 'done': self.done,
                'model': {'id': self.model.identity(), 'trained': bool(self.model.metadata.get('trained')),
                          'algorithm': self.model.metadata['algorithm'],
                          'observations': int(self.model.trials.sum()),
                          'reward': self.model.metadata['reward']},
                'warnings': ['Conflicto de calidad y entrega: se conserva el orgánico antes que forzar un anuncio de respuesta inferior.'] if self.conflicts else []}
