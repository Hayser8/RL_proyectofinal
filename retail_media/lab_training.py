"""Experimentos del laboratorio: exploración factual, holdouts y pruebas de estrés."""
import argparse
import csv
from pathlib import Path
import json
import time

import numpy as np

from .lab_engine import LabSimulation, SCENARIOS, sample_transition
from .lab_model import CATALOGUE, LabModel, SLOTS, N_ACTIONS, ADS_PER_PLP, SERVING_ID, select_action


def _validation_observations(seed=2700, n=3000):
    rng = np.random.default_rng(seed)
    rows = []
    for _ in range(n):
        context = {'segment': int(rng.integers(3)), 'position': int(rng.choice(SLOTS)),
                   'depth': int(rng.integers(3)), 'ads_seen': int(rng.integers(8)), 'converted': False}
        index = int(rng.integers(ADS_PER_PLP + 1))
        action = 0 if index == 0 else context['segment'] * ADS_PER_PLP + index
        outcome = sample_transition(context, action, rng.random(3))
        rows.append((context, action, outcome))
    return rows


def _calibration(model, rows):
    predicted, actual = [], []
    for context, action, outcome in rows:
        predicted.append(model.estimates(context, action)['purchase_probability'])
        actual.append(outcome['purchased'])
    predicted, actual = np.asarray(predicted), np.asarray(actual, dtype=float)
    p = np.clip(predicted, 1e-7, 1 - 1e-7)
    return {'brier_score': float(np.mean((predicted - actual) ** 2)),
            'log_loss': float(-np.mean(actual * np.log(p) + (1 - actual) * np.log(1 - p))),
            'mean_prediction': float(predicted.mean()), 'observed_rate': float(actual.mean())}


def train_lab(output=Path('artifacts/lab_model.npz'), n=600000, seed=1700, verbose=True):
    """Explore a generative MDP with random executed actions, no oracle labels.

    Each logged row has observable state, chosen action and factual click,
    purchase and departure. Propensities are never stored in the learned data.
    This is a learned transition model, not a fitted model of simulator formulas.
    """
    if type(n) is not int or not 1000 <= n <= 3000000:
        raise ValueError('n debe estar entre 1000 y 3000000 transiciones')
    if type(seed) is not int or seed < 0 or seed == 2700:
        raise ValueError('Usa una semilla de entrenamiento válida distinta de validación')
    model = LabModel()
    rng = np.random.default_rng(seed)
    validation = _validation_observations()
    history = []
    checkpoints = {max(1, n // 10), n // 4, n // 2, 3 * n // 4, n}
    start = time.monotonic()
    # Stratification makes rare intent/action cells learnable without exposing
    # counterfactual responses. All actions still generate exactly one outcome.
    segments = rng.integers(3, size=n)
    indices = rng.integers(ADS_PER_PLP + 1, size=n)
    actions = np.where(indices == 0, 0, segments * ADS_PER_PLP + indices)
    positions = rng.choice(SLOTS, size=n)
    depths = rng.integers(3, size=n)
    fatigue = rng.integers(8, size=n)
    draws = rng.random((n, 3))
    for index in range(n):
        context = {'segment': int(segments[index]), 'position': int(positions[index]),
                   'depth': int(depths[index]), 'ads_seen': int(fatigue[index]), 'converted': False}
        action = int(actions[index])
        outcome = sample_transition(context, action, draws[index])
        model.observe(context, action, clicked=outcome['clicked'], purchased=outcome['purchased'], left=outcome['left'])
        if index + 1 in checkpoints:
            history.append({'observations': index + 1, **_calibration(model, validation)})
            if verbose:
                print(f"Aprendizaje {index + 1:,}/{n:,}: Brier validación {history[-1]['brier_score']:.6f}", flush=True)
    # Traffic continuation is estimated from separate factual traffic draws.
    observed_depths = rng.choice([1, 2, 3], size=10000, p=[.5, .3, .2])
    model.continuation = np.array([(observed_depths >= 2).mean(), (observed_depths == 3).sum() / max(1, (observed_depths >= 2).sum())])
    model.metadata.update(trained=True, observations=n, training_seed=seed, validation_seed=2700,
                          dataset='stratified factual MDP transitions',
                          training_scenarios=['balanced'], transition_observations=n,
                          held_out_validation_observations=len(validation), history=history,
                          elapsed_seconds=round(time.monotonic() - start, 3),
                          limitations=['Gamma-Poisson visibility adjustment is a model assumption.',
                                       'Conservative response filter is empirical, not a formal safety guarantee.',
                                       'Finite-horizon planning approximates future budget and duplicate masks.',
                                       'Synthetic behavior is not evidence about a real retail website.'])
    model.save(output)
    if verbose:
        print(f'Modelo guardado: {Path(output).resolve()}', flush=True)
    return model


def _run(model, policy, scenario, seed, sessions):
    simulation = LabSimulation(seed=seed, policy=policy, scenario=scenario, sessions=sessions, model=model)
    while not simulation.done:
        simulation.advance(200)
    return simulation.metrics()


def _paired_interval(values):
    # Each value is a paired difference from an independent day. Conservative t
    # critical values; no treating within-campaign dependent sessions as clusters.
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return None
    critical = 12.706 if len(values) == 2 else 4.303 if len(values) == 3 else 3.182 if len(values) == 4 else 2.776 if len(values) == 5 else 2.571 if len(values) <= 6 else 2.447 if len(values) <= 7 else 2.365 if len(values) <= 8 else 2.306 if len(values) <= 9 else 2.262 if len(values) <= 10 else 2.228 if len(values) <= 20 else 2.093
    half = critical * float(values.std(ddof=1)) / np.sqrt(len(values))
    return [float(mean - half), float(mean + half)]


def integrity_checks(model):
    """Directed adversarial probes. Passing them does not prove universal safety."""
    identity_before = model.identity()
    context = {'segment': 0, 'position': 3, 'depth': 0, 'ads_seen': 0, 'converted': False}
    # A true click with no purchase must never receive purchase reward.
    from .lab_engine import sample_transition
    click_no_buy = sample_transition(context, 1, [0., 1., 1.])
    converted_context = {**context, 'converted': True}
    repeat_buy = sample_transition(converted_context, 2, [0., 0., 1.])
    organic_buy = sample_transition(context, 0, [0., 0., 1.])
    sponsored_buy = sample_transition(context, 2, [0., 0., 1.])
    no_budget = LabSimulation(seed=91000, sessions=8, budget_scale=0, model=model)
    while not no_budget.done:
        no_budget.advance(200)
    zero = no_budget.metrics()
    test_model = LabModel()
    before = {key: getattr(model, key).tobytes() for key in ('exposures', 'trials', 'clicks', 'purchases', 'leaves')}
    selection = select_action(model, context, [0, 2, 8, 14], 'safe_rl', [0, 0, 0], [100, 100, 100], [0, 0, 0], .5, np.random.default_rng(1))
    after = {key: getattr(model, key).tobytes() for key in before}
    fresh = LabSimulation(seed=92000, sessions=5, model=model)
    no_future = fresh.metrics()['sessions_completed'] == 0 and fresh.metrics()['session_cvr'] is None
    repeat = LabSimulation(seed=93000, sessions=4, policy='organic', model=model)
    repeat._draws[:, :, :2] = 0.
    repeat._draws[:, :, 2] = 1.
    while not repeat.done:
        repeat.advance(200)
    capped_reward = repeat.purchase_rewards <= repeat.sessions and repeat.item_purchases > repeat.purchase_rewards
    revenue_context = {**context, 'cpc_cents': 100000000, 'conversion_value_cents': 100000000,
                       'spent_cents': 100000000, 'impressions': 100000000}
    no_financial_reward = sample_transition(revenue_context, 2, [0., 1., 1.])['reward'] == 0
    checks = [
        {'id': 'click_only', 'name': 'Los clics sin compra no dan recompensa', 'passed': click_no_buy['clicked'] and not click_no_buy['purchased'] and click_no_buy['reward'] == 0},
        {'id': 'reward_symmetry', 'name': 'Orgánico y patrocinado reciben la misma recompensa por compra', 'passed': organic_buy['reward'] == sponsored_buy['reward'] == 1},
        {'id': 'one_reward', 'name': 'No se premian compras repetidas en una sesión convertida', 'passed': repeat_buy['reward'] == 0},
        {'id': 'budget_zero', 'name': 'Sin presupuesto no hay patrocinados ni cobros', 'passed': sum(zero['spend_cents']) == zero['sponsored_impressions'] == 0},
        {'id': 'frozen', 'name': 'La inferencia no actualiza los parámetros aprendidos', 'passed': before == after and identity_before == model.identity()},
        {'id': 'no_future', 'name': 'Las métricas parciales no cuentan resultados futuros', 'passed': no_future},
        {'id': 'fallback', 'name': 'La selección sin evidencia conserva orgánico o declara conflicto',
         'passed': select_action(test_model, context, [0, 1, 2], 'safe_rl', [0, 0, 0], [100, 100, 100], [0, 0, 0], .5, np.random.default_rng(1)).action == 0},
        {'id': 'session_cap', 'name': 'La suma de recompensa no supera una unidad por sesión', 'passed': capped_reward},
        {'id': 'financial_proxy', 'name': 'Inflar puja, valor monetario o gasto sin compra no da recompensa', 'passed': no_financial_reward},
    ]
    return checks


def strong_baseline_comparisons(rows, scenario):
    indexed = {(row['policy'], row['seed']): row for row in rows if row['scenario'] == scenario}
    seeds = sorted(seed for policy, seed in indexed if policy == 'safe_rl')
    comparisons = {}
    for baseline in ('quality', 'greedy'):
        differences = [indexed['safe_rl', seed]['session_cvr'] - indexed[baseline, seed]['session_cvr'] for seed in seeds]
        interval = _paired_interval(differences)
        comparisons[f'safe_rl_vs_{baseline}'] = {
            'delta_cvr': float(np.mean(differences)), 'delta_cvr_ci95': interval,
            'superiority_demonstrated': bool(interval and interval[0] > 0),
            'note': 'Paired independent-day comparison; a positive point estimate alone does not establish superiority.'}
    return comparisons


def evaluate_lab(model=None, output=Path('reports/lab_evaluation.json'), seeds=None, sessions=1000, verbose=True):
    model = model or LabModel.load(Path('artifacts/lab_model.npz'))
    identity_before = model.identity()
    seeds = list(range(80020, 80028)) if seeds is None else list(seeds)
    if len(seeds) < 2 or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
        raise ValueError('Se requieren al menos dos semillas independientes')
    if set(seeds) & {model.metadata.get('training_seed'), model.metadata.get('validation_seed')}:
        raise ValueError('Semillas de evaluación contaminadas por entrenamiento/validación')
    policies = ['organic', 'random', 'bid', 'relevance', 'quality', 'greedy', 'safe_rl']
    scenarios = {}
    all_rows = []
    before = {key: getattr(model, key).tobytes() for key in ('exposures', 'trials', 'clicks', 'purchases', 'leaves')}
    for scenario in SCENARIOS:
        summary = {}
        for policy in policies:
            rows = []
            for seed in seeds:
                metrics = _run(model, policy, scenario, seed, sessions)
                row = dict(scenario=scenario, policy=policy, seed=seed, **metrics)
                rows.append(row)
                all_rows.append(row)
            delta = [row['delta_cvr'] for row in rows]
            interval = _paired_interval(delta)
            delivery = np.mean([row['delivery'] for row in rows], axis=0).tolist()
            summary[policy] = {
                'session_cvr': float(np.mean([row['session_cvr'] for row in rows])),
                'organic_session_cvr': float(np.mean([row['organic_session_cvr'] for row in rows])),
                'delta_cvr': float(np.mean(delta)), 'delta_cvr_ci95': interval,
                'delivery': delivery, 'delivery_mean': float(np.mean(delivery)),
                'delivery_pass_rate': [float(np.mean([row['delivery'][b] >= .9 for row in rows])) for b in range(3)],
                'spend_cents': np.mean([row['spend_cents'] for row in rows], axis=0).tolist(),
                'sponsored_ctr': float(np.mean([row['sponsored_ctr'] or 0 for row in rows])),
                'budget_overshoots': sum(row['budget_overshoots'] for row in rows),
                'constraint_conflicts': int(sum(row['constraint_conflicts'] for row in rows)),
                'sessions': sum(row['sessions_completed'] for row in rows),
                'cvr_empirical_pass': interval[0] >= 0 if interval else False,
                'delivery_empirical_pass': all(v >= .9 for v in delivery),
            }
            if verbose:
                value = summary[policy]
                print(f"{scenario:10} {policy:10} CVR {value['session_cvr']:.2%} Δ {value['delta_cvr'] * 100:+.2f} pp entrega {value['delivery_mean']:.1%}", flush=True)
        scenarios[scenario] = {'name': SCENARIOS[scenario]['name'], 'description': SCENARIOS[scenario]['description'], 'policies': summary,
                               'comparisons': strong_baseline_comparisons(all_rows, scenario)}
    after = {key: getattr(model, key).tobytes() for key in before}
    assert before == after and identity_before == model.identity(), 'La evaluación alteró el modelo'
    result = {'schema': 'retail_lab_evaluation_v2', 'serving_id': SERVING_ID, 'model_id': model.identity(), 'training': model.metadata,
              'policy_descriptions': {
                  'organic': 'Referencia orgánica', 'random': 'Selección aleatoria', 'bid': 'Mayor CPC disponible',
                  'relevance': 'Categoría y rating visible; rating puede ser engañoso en el catálogo sintético',
                  'quality': 'Categoría y atributo de calidad; referencia heurística fuerte',
                  'greedy': 'Mayor compra inmediata aprendida; mismo filtro conservador, presupuesto y pacing que RL',
                  'safe_rl': 'Valor de conversión de sesión con Bellman y filtro conservador'},
              'test': {'seeds': seeds, 'sessions_requested_per_run': sessions,
                       'independent_days': len(seeds), 'seed_split_disjoint': True,
                       'reference': 'Paired organic trajectory on the same exogenous user draws; abandonment may change exposure.'},
              'policies': policies, 'scenarios': scenarios, 'runs': all_rows,
              'integrity_checks': integrity_checks(model),
              'limitations': ['Las pruebas dirigidas no demuestran ausencia universal de reward hacking.',
                              'La simulación sintética no garantiza CVR de una tienda real.',
                              'La calidad tiene prioridad ante restricciones comerciales incompatibles; se informa inversión no entregada.',
                              'El filtro conservador usa incertidumbre de un modelo paramétrico, no una cota formal de seguridad.']}
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    with path.with_suffix('.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(all_rows)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--observations', type=int, default=600000)
    parser.add_argument('--sessions', type=int, default=1000)
    parser.add_argument('--runs', type=int, default=8)
    parser.add_argument('--evaluate-only', action='store_true')
    args = parser.parse_args()
    model = LabModel.load('artifacts/lab_model.npz') if args.evaluate_only else train_lab(n=args.observations)
    evaluate_lab(model, sessions=args.sessions, seeds=range(80020, 80020 + args.runs))
