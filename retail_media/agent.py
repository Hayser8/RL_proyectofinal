"""Q-learning tabular con selección epsilon-greedy y acciones enmascaradas."""
import json
from pathlib import Path

import numpy as np


class QAgent:
    def __init__(self, actions=19, seed=0, alpha=.01, gamma=.8):
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.rng = np.random.default_rng(seed)
        self.table = {}
        self.cvr_multiplier = 0.
        self.metadata = {}

    def values(self, state):
        # State aggregation shares sparse feedback only within the same intent,
        # sponsored-position group and scroll depth. Fatigue and pacing still
        # determine legal actions through the operational controller.
        key = (int(state[0]), int(state[1]), int(state[2])) if len(state) == 6 else tuple(state)
        if key not in self.table:
            self.table[key] = np.zeros(self.actions, dtype=np.float64)
        return self.table[key]

    def act(self, state, allowed, epsilon=0.):
        if not allowed:
            raise ValueError('No hay acciones disponibles')
        if len(allowed) == 1:
            return int(allowed[0])
        if self.rng.random() < epsilon:
            return int(self.rng.choice(allowed))
        scores = self.values(state)[allowed]
        # Random tie-breaking avoids preferring a brand by catalog order.
        best = np.flatnonzero(scores == scores.max())
        return int(allowed[int(self.rng.choice(best))])

    def update(self, state, action, reward, next_state, allowed, done=False):
        future = 0. if done else float(self.values(next_state)[allowed].max())
        q = self.values(state)
        q[action] += self.alpha * (reward + self.gamma * future - q[action])

    def save(self, path, config):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        keys = list(self.table)
        meta = {**self.metadata, 'version': 3, 'state_schema': 'intent_position_depth_v3',
                'config_fingerprint': config.fingerprint(),
                'actions': self.actions, 'alpha': self.alpha, 'gamma': self.gamma,
                'cvr_multiplier': self.cvr_multiplier}
        # JSON keys support variable-length terminal state without object/pickle arrays.
        with path.open('wb') as handle:
            np.savez_compressed(handle, keys=json.dumps(keys),
                                values=np.stack([self.table[k] for k in keys]) if keys else np.empty((0, self.actions)),
                                metadata=json.dumps(meta))

    @classmethod
    def load(cls, path, config, seed=0):
        with np.load(path, allow_pickle=False) as data:
            meta = json.loads(str(data['metadata']))
            if (meta.get('version') != 3 or meta.get('state_schema') != 'intent_position_depth_v3'
                    or meta['config_fingerprint'] != config.fingerprint()):
                raise ValueError('El modelo no corresponde al catálogo/configuración; vuelve a entrenar')
            agent = cls(meta['actions'], seed, meta['alpha'], meta['gamma'])
            keys = json.loads(str(data['keys']))
            if data['values'].shape != (len(keys), agent.actions):
                raise ValueError('Tabla Q inválida')
            agent.table = {tuple(k): v.copy() for k, v in zip(keys, data['values'])}
            agent.cvr_multiplier = meta['cvr_multiplier']
            agent.metadata = meta
        return agent
