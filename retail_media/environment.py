"""Entorno finito: un día, muchas sesiones y oportunidades secuenciales.

Las variables exógenas se generan antes de actuar. Las políticas evaluadas con
la misma semilla ven idénticos usuarios, profundidades y sorteos de respuesta.
Las probabilidades verdaderas son privadas al simulador, no parte del estado.
"""
import numpy as np

from .config import Config


class RetailMediaEnv:
    def __init__(self, config: Config, seed=0, cvr_multiplier=0.0, budget_cents=None):
        self.config = config.validate()
        if budget_cents is None:
            budget_cents = [b['budget_cents'] // config.campaign_days for b in config.brands]
        if (not isinstance(budget_cents, (list, tuple)) or len(budget_cents) != 3
                or any(type(v) is not int or not 0 <= v <= b['budget_cents']
                       for v, b in zip(budget_cents, config.brands))):
            raise ValueError('La asignación debe contener tres importes enteros dentro del presupuesto de campaña')
        self.rng = np.random.default_rng(seed)
        self.cvr_multiplier = cvr_multiplier
        self.products = [
            {'action': 1 + b * 6 + c * 2 + v, 'brand': b, 'category': c,
             'quality': v, 'name': f'{config.brands[b]["name"]} · {config.categories[c]} {"Plus" if v else "Esencial"}'}
            for b in range(3) for c in range(3) for v in range(2)
        ]
        self.budgets = np.array(budget_cents, dtype=np.int64)
        self.spent = np.zeros(3, dtype=np.int64)
        self.brand_impressions = np.zeros(3, dtype=np.int64)
        self.brand_clicks = np.zeros(3, dtype=np.int64)
        self.index = 0
        self._allowed_cache = None
        self.used = set()
        self.session_ads = 0
        self.forced_decisions = 0
        segments = self.rng.choice(3, config.sessions, p=[.45, .35, .20])
        depths = self.rng.choice([1, 2, 3], config.sessions, p=[.55, .30, .15])
        block_sessions = np.repeat(np.arange(config.sessions), depths)
        block_depths = np.concatenate([np.arange(d) for d in depths])
        self.item_sessions = np.repeat(block_sessions, 20)
        self.item_depths = np.repeat(block_depths, 20)
        self.item_segments = segments[self.item_sessions]
        self.item_positions = np.tile(np.arange(1, 21), len(block_sessions))
        self.click_draws = self.rng.random(len(self.item_sessions))
        self.purchase_draws = self.rng.random(len(self.item_sessions))
        self.organic_ctr = .052 * np.exp(-.018 * (self.item_positions - 1)) * np.power(.88, self.item_depths)
        self.organic_purchase_given_click = .080 + .008 * (self.item_segments == 0)
        self.organic_click = self.click_draws < self.organic_ctr
        self.organic_purchase = self.organic_click & (self.purchase_draws < self.organic_purchase_given_click)
        self.organic_session_counts = np.bincount(self.item_sessions, weights=self.organic_purchase, minlength=config.sessions).astype(int)
        self.session_counts = self.organic_session_counts.copy()
        self.total_purchases = int(self.organic_purchase.sum())
        self.total_clicks = int(self.organic_click.sum())
        self.decisions = np.flatnonzero(np.isin(self.item_positions, config.sponsored_slots))
        self.sponsored_purchases = 0

    @property
    def done(self):
        return self.index >= len(self.decisions)

    @property
    def progress(self):
        return self.index / len(self.decisions)

    @property
    def item(self):
        return int(self.decisions[self.index])

    @property
    def position(self):
        return int(self.item_positions[self.item])

    def lagging_brand(self):
        gap = self.progress - self.spent / np.maximum(self.budgets, 1)
        gap[self.budgets == 0] = -np.inf
        return int(np.argmax(gap))

    def state(self):
        if self.done:
            return (-1,)
        item = self.item
        return (int(self.item_segments[item]), self.index % 8 // 4,
                min(1, int(self.item_depths[item])), int(self.session_ads >= 4),
                min(2, int(self.progress * 3)), self.lagging_brand())

    def allowed_actions(self, pacing=True):
        if self.done:
            return [0]
        if pacing and self._allowed_cache is not None:
            return self._allowed_cache
        candidates = []
        remaining = (self.budgets - self.spent).tolist()
        fill = (self.spent / np.maximum(self.budgets, 1)).tolist()
        for p in self.products:
            b = p['brand']
            if p['action'] not in self.used and self.config.brands[b]['cpc_cents'] <= remaining[b]:
                if not pacing or fill[b] <= self.progress + .12:
                    candidates.append(p['action'])
        if pacing and self.progress >= .15:
            lag = self.lagging_brand()
            deficit = self.progress - self.spent[lag] / max(self.budgets[lag], 1)
            urgent = [a for a in candidates if self.products[a - 1]['brand'] == lag]
            if deficit > self.config.pacing_slack and urgent:
                self._allowed_cache = urgent
                return urgent
        result = [0] + candidates
        if pacing:
            self._allowed_cache = result
        return result

    def step(self, action):
        if self.done:
            raise RuntimeError('El episodio terminó')
        # Pacing is a controller. Physical validity is independent, allowing a
        # purely organic baseline to bypass commercial commitments explicitly.
        if type(action) is not int or not 0 <= action <= len(self.products):
            raise ValueError(f'Acción inválida: {action}')
        if action:
            b = self.products[action - 1]['brand']
            if action in self.used or self.spent[b] + self.config.brands[b]['cpc_cents'] > self.budgets[b]:
                raise ValueError(f'Acción fuera de presupuesto o duplicada: {action}')
        item = self.item
        session = int(self.item_sessions[item])
        organic_click = bool(self.organic_click[item])
        organic_purchase = bool(self.organic_purchase[item])
        clicked, purchase = organic_click, organic_purchase
        brand, cost = -1, 0
        urgency = 0.
        forced = 0 not in self.allowed_actions()
        if action:
            product = self.products[action - 1]
            brand = product['brand']
            match = product['category'] == self.item_segments[item]
            affinity = 1.0 if match else .30
            fatigue = max(.55, 1. - .045 * self.session_ads)
            ctr = (.057 + .027 * product['quality']) * affinity * np.exp(-.018 * (self.position - 1)) * (.88 ** self.item_depths[item]) * fatigue
            purchase_rate = (.065 + .070 * product['quality']) * (1.0 if match else .4)
            clicked = bool(self.click_draws[item] < ctr)
            purchase = bool(clicked and self.purchase_draws[item] < purchase_rate)
            cost = self.config.brands[brand]['cpc_cents'] if clicked else 0
            urgency = max(0., self.progress - self.spent[brand] / max(1, self.budgets[brand]))
            self.spent[brand] += cost
            self.brand_impressions[brand] += 1
            self.brand_clicks[brand] += int(clicked)
            self.sponsored_purchases += int(purchase)
            self.used.add(action)
            self.session_ads += 1
        self.forced_decisions += int(forced and action != 0)
        self.session_counts[session] += int(purchase) - int(organic_purchase)
        self.total_purchases += int(purchase) - int(organic_purchase)
        self.total_clicks += int(clicked) - int(organic_click)
        reward = (100. + self.cvr_multiplier) * int(purchase) + (.20 + 4. * urgency) * cost / 100.
        info = {'session': session, 'block': int(self.item_depths[item]),
                'position': self.position, 'absolute_position': int(self.item_depths[item]) * 20 + self.position,
                'segment': int(self.item_segments[item]), 'action': action, 'brand': brand,
                'clicked': clicked, 'purchase': purchase,
                'sponsored_click': bool(action and clicked), 'cost_cents': cost,
                'forced_pacing': bool(forced and action), 'spent_cents': self.spent.tolist()}
        self.index += 1
        self._allowed_cache = None
        if self.index % 8 == 0:
            self.used.clear()
        if not self.done and self.item_sessions[self.item] != session:
            self.session_ads = 0
        if self.done:
            shortfall = np.maximum(0, self.config.minimum_delivery - self.spent / np.maximum(1, self.budgets))
            reward -= 4 * float(np.mean(shortfall))
        return self.state(), reward, info

    def metrics(self):
        sponsored = int(self.brand_impressions.sum())
        converted = self.session_counts > 0
        organic = self.organic_session_counts > 0
        return {
            'sessions': self.config.sessions, 'product_impressions': len(self.item_sessions),
            'sponsored_opportunities': len(self.decisions), 'sponsored_impressions': sponsored,
            'sponsored_clicks': int(self.brand_clicks.sum()),
            'session_cvr': float(converted.mean()), 'organic_session_cvr': float(organic.mean()),
            'item_cvr': self.total_purchases / len(self.item_sessions),
            'sponsored_ctr': float(self.brand_clicks.sum()) / max(1, sponsored),
            'ad_fill_rate': sponsored / len(self.decisions),
            'spend_cents': self.spent.tolist(), 'daily_budget_cents': self.budgets.tolist(),
            'brand_impressions': self.brand_impressions.tolist(), 'brand_clicks': self.brand_clicks.tolist(),
            'brand_delivery': (self.spent / np.maximum(1, self.budgets)).tolist(),
            'pacing_forced_share': self.forced_decisions / max(1, sponsored),
            'converted_sessions': int(converted.sum()),
            'organic_converted_sessions': int(organic.sum())
        }
