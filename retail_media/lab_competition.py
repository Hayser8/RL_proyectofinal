"""Descriptive exposure audit. Observes serving; never changes scores or actions."""
from copy import deepcopy
import json
from pathlib import Path

from .lab_catalog import present_product
from .lab_model import CATALOGUE, CATEGORIES, CPC_CENTS, N_ACTIONS, SERVING_ID


BLOCK_LABELS = {
    'converted': 'La visita ya compró', 'budget': 'Sin saldo para otro clic',
    'duplicate': 'Ya apareció en este bloque', 'pacing': 'Presupuesto adelantado',
    'quality': 'Evidencia de compra insuficiente frente al orgánico',
    'policy': 'Excluido por la política de referencia',
}


def model_clusters(model, segment):
    """Fixed pre-run cohorts; neither bids nor observed exposure define winners."""
    context = dict(segment=segment, position=3, depth=0, ads_seen=0, converted=False)
    scores = model.scores(context)
    organic = model.estimates(context, 0)['purchase_probability']
    rows = []
    for product in CATALOGUE:
        if product['category_id'] != segment:
            continue
        action = product['action']
        estimate = model.estimates(context, action)
        lift = float(scores[action] - scores[0])
        supported = estimate['observations'] >= 100 and estimate['purchase_lower'] >= organic
        rows.append({'action': action, 'reference_lift': lift,
                     'supported': bool(supported), 'cluster': 'others'})
    ranked = sorted(rows, key=lambda r: (r['supported'], r['reference_lift'], -r['action']), reverse=True)
    for row in ranked[:8]:
        row['cluster'] = 'winners'
    return {'reference_context': context, 'organic_value': float(scores[0]),
            'ads': rows,
            'groups': {key: {'actions': [r['action'] for r in rows if r['cluster'] == key],
                             'mean_reference_lift': float(sum(r['reference_lift'] for r in rows if r['cluster'] == key)
                                                          / max(1, sum(r['cluster'] == key for r in rows)))}
                       for key in ('winners', 'others')}}


class CompetitionAudit:
    def __init__(self, sessions, model):
        self.stride = max(1, (sessions + 99) // 100)
        self.plps = []
        for segment, category in enumerate(CATEGORIES):
            clusters = model_clusters(model, segment)
            by_action = {r['action']: r for r in clusters['ads']}
            self.plps.append({'category': category, 'visits': 0, 'opportunities': 0,
                              'organic_wins': 0, 'clusters': clusters,
                              'ads': [{**present_product(p), **by_action[p['action']],
                                       'considered': 0, 'eligible': 0,
                                       'impressions': 0, 'clicks': 0, 'spend_cents': 0,
                                       'lost_ranking': 0, 'lost_pacing': 0, 'lost_coverage': 0,
                                       'blocked': {k: 0 for k in BLOCK_LABELS}} for p in CATALOGUE if p['category_id'] == segment],
                              'timeline': [{'visits': 0, 'impressions': [0] * len(CATALOGUE)}]})

    def observe_decision(self, context, selection, *, policy, spent, budgets, used):
        plp = self.plps[context['segment']]
        plp['opportunities'] += 1
        winner_brand = CATALOGUE[selection.action - 1]['brand_id'] if selection.action else None
        for candidate in selection.candidates:
            action = candidate['action']
            if not action:
                continue
            row = next(a for a in plp['ads'] if a['action'] == action)
            row['considered'] += 1
            if candidate['eligible']:
                row['eligible'] += 1
                if action != selection.action:
                    pacing_loss = selection.forced_pacing and row['brand_id'] != winner_brand
                    coverage_loss = selection.coverage_exploration and row['impressions'] >= 1
                    row['lost_coverage' if coverage_loss else 'lost_pacing' if pacing_loss else 'lost_ranking'] += 1
                continue
            brand = row['brand_id']
            if context['converted']:
                reason = 'converted'
            elif policy == 'organic':
                reason = 'policy'
            elif spent[brand] + CPC_CENTS[brand] > budgets[brand]:
                reason = 'budget'
            elif action in used or candidate.get('exclusion_code') == 'duplicate':
                reason = 'duplicate'
            elif not candidate['budget_eligible']:
                reason = 'pacing'
            elif policy in ('safe_rl', 'greedy'):
                reason = 'quality'
            else:
                reason = 'policy'
            row['blocked'][reason] += 1

    def observe_action(self, context, action, outcome, cost):
        plp = self.plps[context['segment']]
        if action:
            row = next(a for a in plp['ads'] if a['action'] == action)
            row['impressions'] += 1
            row['clicks'] += int(outcome['clicked'])
            row['spend_cents'] += cost
        else:
            plp['organic_wins'] += 1

    def close_visit(self, segment):
        plp = self.plps[segment]
        plp['visits'] += 1
        if plp['visits'] % self.stride == 0:
            plp['timeline'].append(self._point(plp))

    @staticmethod
    def _point(plp):
        values = [0] * (N_ACTIONS - 1)
        for ad in plp['ads']:
            values[ad['action'] - 1] = ad['impressions']
        return {'visits': plp['visits'], 'impressions': values}

    def snapshot(self):
        result = deepcopy(self.plps)
        for plp in result:
            counts = [a['impressions'] for a in plp['ads']]
            plp['coverage'] = {'served': sum(n >= 1 for n in counts), 'target': len(counts),
                               'minimum': min(counts), 'complete': all(n >= 1 for n in counts),
                               'pending': [a['action'] for a in plp['ads'] if a['impressions'] < 1]}
            point = self._point(plp)
            if plp['timeline'][-1] != point:
                plp['timeline'].append(point)
        return result


def build_report(model, *, seed=91031, sessions=1000, scenarios=None):
    # Local import prevents a circular dependency with the simulation observer.
    from .lab_engine import LabSimulation, SCENARIOS
    result = {'schema': 'retail_lab_competition_v3_plp16', 'serving_id': SERVING_ID, 'model_id': model.identity(),
              'seed': seed, 'requested_sessions': sessions, 'policy': 'safe_rl',
              'budget_scale': 1., 'block_labels': BLOCK_LABELS, 'scenarios': {}}
    for scenario in scenarios or SCENARIOS:
        simulation = LabSimulation(seed=seed, sessions=sessions, scenario=scenario, model=model,
                                   audit_competition=True)
        while not simulation.done:
            simulation.advance(200)
        result['scenarios'][scenario] = {'metrics': simulation.metrics(),
                                         'plps': simulation.competition.snapshot()}
    from .lab_assessment import assess
    evaluation_path = Path(__file__).resolve().parents[1] / 'reports/lab_evaluation.json'
    evaluation = json.loads(evaluation_path.read_text()) if evaluation_path.exists() else None
    result['assessment'] = assess(result, evaluation)
    return result


if __name__ == '__main__':
    from .lab_model import LabModel
    root = Path(__file__).resolve().parents[1]
    model = LabModel.load(root / 'artifacts/lab_model.npz')
    report = build_report(model)
    path = root / 'reports/lab_competition.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Informe descriptivo: {path}')
