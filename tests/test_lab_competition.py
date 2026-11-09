import json
from pathlib import Path
import unittest

from retail_media.lab_engine import LabSimulation
from retail_media.lab_model import CPC_CENTS, N_ACTIONS, LabModel
from retail_media.lab_competition import CompetitionAudit, build_report


class CompetitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = LabModel.load(Path(__file__).resolve().parents[1] / 'artifacts/lab_model.npz')

    def test_observer_cannot_change_actions_metrics_or_rng(self):
        for policy in ('safe_rl', 'random', 'bid'):
            with self.subTest(policy=policy):
                plain = LabSimulation(seed=921, sessions=25, policy=policy, model=self.model)
                audited = LabSimulation(seed=921, sessions=25, policy=policy, model=self.model, audit_competition=True)
                while not plain.done:
                    a, b = plain.advance(1), audited.advance(1)
                    self.assertEqual(a, b)

    def test_counts_partition_every_actual_opportunity_and_reconcile_cpc(self):
        sim = LabSimulation(seed=91031, sessions=40, model=self.model, audit_competition=True)
        while not sim.done:
            sim.advance(200)
        plps = sim.competition.snapshot()
        self.assertEqual(sum(p['visits'] for p in plps), sim.sessions_completed)
        self.assertEqual(sum(a['impressions'] for p in plps for a in p['ads']), sim.sponsored_impressions)
        for brand in range(3):
            rows = [a for p in plps for a in p['ads'] if a['brand_id'] == brand]
            self.assertEqual(sum(a['spend_cents'] for a in rows), sim.spent[brand])
            self.assertEqual(sum(a['clicks'] for a in rows), sim.brand_clicks[brand])
        for plp in plps:
            self.assertEqual(plp['opportunities'], plp['organic_wins'] + sum(a['impressions'] for a in plp['ads']))
            self.assertEqual(plp['timeline'][0], {'visits': 0, 'impressions': [0] * (N_ACTIONS - 1)})
            self.assertEqual([plp['timeline'][-1]['impressions'][a['action'] - 1] for a in plp['ads']], [a['impressions'] for a in plp['ads']])
            for row in plp['ads']:
                self.assertEqual(row['considered'], plp['opportunities'])
                self.assertEqual(row['eligible'], row['impressions'] + row['lost_ranking'] + row['lost_pacing'] + row['lost_coverage'])
                self.assertEqual(row['considered'], row['eligible'] + sum(row['blocked'].values()))
                self.assertEqual(row['spend_cents'], row['clicks'] * CPC_CENTS[row['brand_id']])
            points = plp['timeline']
            for before, after in zip(points, points[1:]):
                self.assertLessEqual(before['visits'], after['visits'])
                self.assertTrue(all(a <= b for a, b in zip(before['impressions'], after['impressions'])))

    def test_clusters_are_fixed_before_exposure_and_ignore_bids_and_budget(self):
        sim = LabSimulation(seed=921, sessions=15, model=self.model, audit_competition=True)
        initial = [p['clusters'] for p in sim.competition.snapshot()]
        identity = self.model.identity()
        for plp in sim.competition.snapshot():
            self.assertTrue(all(row['impressions'] == 0 for row in plp['ads']))
            clusters = plp['clusters']['groups']
            winners = set(clusters['winners']['actions'])
            others = set(clusters['others']['actions'])
            self.assertFalse(winners & others)
            self.assertEqual(winners | others, {ad['action'] for ad in plp['ads']})
            self.assertEqual(len(winners), 8)
            self.assertEqual(len(others), 8)
            self.assertTrue(all(ad['category'] == plp['category'] for ad in plp['ads']))
            for ad in plp['ads']:
                if ad['cluster'] == 'winners':
                    self.assertGreater(ad['reference_lift'], 0)
        while not sim.done:
            sim.advance(200)
        self.assertEqual(initial, [p['clusters'] for p in sim.competition.snapshot()])
        zero = LabSimulation(seed=100, sessions=15, budget_scale=0, model=self.model, audit_competition=True)
        self.assertEqual(initial, [p['clusters'] for p in zero.competition.snapshot()])
        self.assertEqual(identity, self.model.identity())

    def test_no_budget_produces_zero_exposure_and_explicit_exclusions(self):
        sim = LabSimulation(seed=921, sessions=5, budget_scale=0, model=self.model, audit_competition=True)
        while not sim.done:
            sim.advance(200)
        for plp in sim.competition.snapshot():
            for row in plp['ads']:
                self.assertEqual(row['impressions'], 0)
                self.assertEqual(row['eligible'], 0)
                self.assertEqual(sum(row['blocked'].values()), plp['opportunities'])

    def test_all_48_ads_receive_real_exposures_in_default_and_scarce_traffic(self):
        for scenario in ('balanced', 'scarce'):
            sim = LabSimulation(seed=91031, sessions=1000, scenario=scenario, model=self.model, audit_competition=True)
            while not sim.done:
                sim.advance(200)
            self.assertEqual(sim.coverage_decisions, 48)
            self.assertEqual(sim.metrics()['ads_with_impressions'], 48)
            for plp in sim.competition.snapshot():
                self.assertEqual(plp['coverage']['served'], 16)
                self.assertGreaterEqual(plp['coverage']['minimum'], 1)
                self.assertFalse(plp['coverage']['pending'])
            self.assertEqual(sum(sim.ad_impressions), sim.sponsored_impressions)
            self.assertEqual(sim.metrics()['budget_overshoots'], 0)

    def test_short_or_unfunded_runs_report_pending_exposure_without_fabricating_it(self):
        sim = LabSimulation(seed=921, sessions=1, budget_scale=0, model=self.model, audit_competition=True)
        while not sim.done:
            sim.advance(200)
        self.assertEqual(sim.coverage_decisions, 0)
        for plp in sim.competition.snapshot():
            self.assertFalse(plp['coverage']['complete'])
            self.assertEqual(len(plp['coverage']['pending']), 16)
            self.assertEqual(plp['coverage']['minimum'], 0)

    def test_actual_decisions_only_include_same_plp_and_never_repeat_a_visible_sku(self):
        sim = LabSimulation(seed=2026, sessions=12, model=self.model)
        while not sim.done:
            before = sim.snapshot()['current']
            decision = sim.advance(1)['last_decision']
            segment = decision['guidance']['segment_id']
            actions = {c['action'] for c in decision['candidates'] if c['action']}
            self.assertEqual(actions, set(range(segment * 16 + 1, segment * 16 + 17)))
            self.assertEqual(len(decision['candidates']), 17)
            for block in [sim.snapshot()['current'], *sim.completed_blocks]:
                seen = [p['sku_index'] for p in block['products'] if p['observed']]
                self.assertEqual(len(seen), len(set(seen)))
        with self.assertRaisesRegex(ValueError, 'PLP'):
            fresh = LabSimulation(seed=2026, sessions=2, model=self.model)
            wrong = 17 if fresh._context()['segment'] != 1 else 1
            fresh._view(wrong)

    def test_first_exposure_priority_does_not_mislabel_an_eligible_loss_as_ranking(self):
        sim = LabSimulation(seed=2026, sessions=30, model=self.model, audit_competition=True)
        found = False
        for _ in range(150):
            before = {a['action']: dict(a) for p in sim.competition.plps for a in p['ads']}
            decision = sim.advance(1)['last_decision']
            if decision['coverage_exploration']:
                chosen = next(c for c in decision['candidates'] if c['action'] == decision['action'])
                for candidate in decision['candidates']:
                    action = candidate['action']
                    if action and candidate['eligible'] and candidate['score'] > chosen['score'] and before[action]['impressions'] > 0:
                        row = next(a for p in sim.competition.plps for a in p['ads'] if a['action'] == action)
                        self.assertEqual(row['lost_coverage'], before[action]['lost_coverage'] + 1)
                        self.assertEqual(row['lost_ranking'], before[action]['lost_ranking'])
                        found = True
            if found or sim.done:
                break
        self.assertTrue(found)

    def test_reproducible_report_uses_current_model_and_bounded_history(self):
        a = build_report(self.model, sessions=10, seed=921, scenarios=['balanced'])
        b = build_report(self.model, sessions=10, seed=921, scenarios=['balanced'])
        self.assertEqual(a, b)
        self.assertEqual(a['model_id'], self.model.identity())
        json.dumps(a, allow_nan=False)
        self.assertEqual(len(a['scenarios']['balanced']['plps']), 3)
        observer = CompetitionAudit(20000, self.model)
        for _ in range(20000):
            observer.close_visit(0)
        self.assertLessEqual(len(observer.snapshot()[0]['timeline']), 102)


if __name__ == '__main__':
    unittest.main()
