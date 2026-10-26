"""Entrenamiento reproducible y evaluación en tráfico emparejado."""
from copy import deepcopy
import csv
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from .agent import QAgent
from .environment import RetailMediaEnv

POLICIES = ('organic', 'random', 'relevance', 'untrained', 'rl')


def train(config, episodes=120, seed=42, output=Path('artifacts')):
    if type(episodes) is not int or episodes < 1:
        raise ValueError('episodes debe ser positivo')
    config.validate()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    agent = QAgent(seed=seed)
    history = []
    training_seeds = [seed + ep for ep in range(episodes)]
    for ep, environment_seed in enumerate(training_seeds):
        epsilon = .10 + .85 * (1 - ep / max(1, episodes - 1)) ** 1.5
        env = RetailMediaEnv(config, environment_seed, agent.cvr_multiplier)
        state = env.state()
        allowed = env.allowed_actions()
        total_reward = 0.
        while not env.done:
            action = agent.act(state, allowed, epsilon)
            next_state, reward, _ = env.step(action)
            next_allowed = env.allowed_actions()
            agent.update(state, action, reward, next_state, next_allowed, env.done)
            state, allowed = next_state, next_allowed
            total_reward += reward
        metrics = env.metrics()
        # Empirical constraint penalty, not a safety guarantee. In production this
        # comparator requires a randomized organic holdout, unavailable in logs alone.
        violation = metrics['organic_session_cvr'] - metrics['session_cvr'] - config.cvr_tolerance
        agent.cvr_multiplier = float(np.clip(agent.cvr_multiplier + 200 * violation, 0, 200))
        history.append({'episode': ep + 1, 'seed': environment_seed, 'epsilon': epsilon,
                        'reward': total_reward, 'session_cvr': metrics['session_cvr'],
                        'organic_session_cvr': metrics['organic_session_cvr'],
                        'delivery_mean': float(np.mean(metrics['brand_delivery'])),
                        'cvr_multiplier': agent.cvr_multiplier,
                        'q_states': len(agent.table)})
        if ep == 0 or (ep + 1) % 10 == 0 or ep + 1 == episodes:
            print(f"Episodio {ep + 1:3}/{episodes} | CVR {metrics['session_cvr']:.2%} | orgánico {metrics['organic_session_cvr']:.2%} | entrega {np.mean(metrics['brand_delivery']):.1%} | ε {epsilon:.2f}", flush=True)
    agent.metadata = {'training_seeds': training_seeds, 'episodes': episodes,
                      'training_sessions_per_episode': config.sessions, 'seed': seed,
                      'config': asdict(config)}
    agent.save(output / 'model.npz', config)
    with (output / 'training.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)
    (output / 'training.json').write_text(json.dumps(history, indent=2), encoding='utf-8')
    return agent, history


def confidence_interval(values):
    """Paired, independent episode means; conservative Student-t critical values."""
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return [mean, mean]  # Caller rejects this case for evaluation.
    df = len(values) - 1
    critical = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
                6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262}.get(df)
    if critical is None:
        critical = 2.228 if df < 20 else 2.093 if df < 30 else 2.042 if df < 60 else 2.0 if df < 120 else 1.98
    half = critical * float(values.std(ddof=1)) / np.sqrt(len(values))
    return [float(mean - half), float(mean + half)]


def choose_action(policy, env, agent, rng):
    if policy == 'organic':
        return 0
    allowed = env.allowed_actions()
    if policy == 'random':
        return int(rng.choice(allowed))
    if policy == 'relevance':
        segment = env.state()[0]
        # Only observable product metadata; does not read response probabilities.
        scores = [0.7 if a == 0 else 1.0 * (env.products[a - 1]['category'] == segment) + .2 * env.products[a - 1]['quality'] for a in allowed]
        best = np.flatnonzero(np.asarray(scores) == max(scores))
        return int(allowed[int(rng.choice(best))])
    return agent.act(env.state(), allowed, epsilon=0.)


def evaluate(config, agent, seeds=None, trace_sessions=12):
    seeds = list(range(30000, 30030)) if seeds is None else list(seeds)
    if len(set(seeds)) != len(seeds) or len(seeds) < 2:
        raise ValueError('Usa al menos dos semillas distintas de evaluación')
    if set(seeds) & set(agent.metadata.get('training_seeds', [])):
        raise ValueError('Las semillas de evaluación coinciden con entrenamiento')
    runs, traces = [], {p: [] for p in POLICIES}
    for policy in POLICIES:
        for seed_index, seed in enumerate(seeds):
            # Never mutate the trained model, its RNG or its Q-state inventory.
            actor = deepcopy(agent) if policy == 'rl' else QAgent(seed=seed)
            actor.rng = np.random.default_rng(seed + 1000000)
            env = RetailMediaEnv(config, seed=seed)
            rng = np.random.default_rng(seed + 2000000)
            while not env.done:
                action = choose_action(policy, env, actor, rng)
                _, _, info = env.step(action)
                if seed_index == 0 and info['session'] < trace_sessions:
                    traces[policy].append(info)
            runs.append({'policy': policy, 'seed': seed, **env.metrics()})
        print(f'Evaluación {policy}: {len(seeds)} semillas', flush=True)
    summary = {}
    for policy in POLICIES:
        rows = [r for r in runs if r['policy'] == policy]
        delta = [r['session_cvr'] - r['organic_session_cvr'] for r in rows]
        interval = confidence_interval(delta)
        summary[policy] = {
            'session_cvr': float(np.mean([r['session_cvr'] for r in rows])),
            'delta_cvr': float(np.mean(delta)), 'delta_cvr_ci95': interval,
            'cvr_point_pass': float(np.mean(delta)) >= -config.cvr_tolerance,
            'cvr_ci_pass': interval[0] >= -config.cvr_tolerance,
            'sponsored_ctr': float(sum(r['sponsored_clicks'] for r in rows) / max(1, sum(r['sponsored_impressions'] for r in rows))),
            'ad_fill_rate': float(sum(r['sponsored_impressions'] for r in rows) / sum(r['sponsored_opportunities'] for r in rows)),
            'spend_cents': np.mean([r['spend_cents'] for r in rows], axis=0).tolist(),
            'brand_delivery': np.mean([r['brand_delivery'] for r in rows], axis=0).tolist(),
            'brand_impressions': np.mean([r['brand_impressions'] for r in rows], axis=0).tolist(),
            'delivery_pass_rate': [float(np.mean([r['brand_delivery'][b] >= config.minimum_delivery for r in rows])) for b in range(3)],
            'pacing_forced_share': float(np.mean([r['pacing_forced_share'] for r in rows])),
            'budget_overshoots': sum(any(s > b for s, b in zip(r['spend_cents'], r['daily_budget_cents'])) for r in rows)
        }
    return {'config': asdict(config), 'seeds': seeds, 'sessions_per_policy': len(seeds) * config.sessions,
            'model_metadata': agent.metadata, 'policies': summary, 'runs': runs,
            'catalog': env.products, 'traces': traces}
