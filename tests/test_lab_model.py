import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from retail_media.lab_engine import LabSimulation, sample_transition
from retail_media.lab_model import LabModel, N_ACTIONS, select_action
from retail_media.lab_training import evaluate_lab, integrity_checks, strong_baseline_comparisons, train_lab


CONTEXT = dict(segment=0, position=3, depth=0, ads_seen=0, converted=False)


class RewardAlignmentTests(unittest.TestCase):
    def test_click_without_purchase_never_rewards_revenue_or_exposure(self):
        for action in (0, 1, 2, 8, 14):
            with self.subTest(action=action):
                outcome = sample_transition(CONTEXT, action, [0., 1., 1.])
                self.assertTrue(outcome['clicked'])
                self.assertFalse(outcome['purchased'])
                self.assertEqual(outcome['reward'], 0.)

    def test_organic_and_sponsored_purchase_have_equal_reward(self):
        for action in (0, 1, 2, 8, 14):
            self.assertEqual(sample_transition(CONTEXT, action, [0., 0., 1.])['reward'], 1.)

    def test_already_converted_session_has_no_additional_purchase_reward(self):
        outcome = sample_transition({**CONTEXT, 'converted': True}, 2, [0., 0., 1.])
        self.assertTrue(outcome['purchased'])
        self.assertEqual(outcome['reward'], 0.)

    def test_full_session_reward_cannot_be_farmed_with_repeat_purchases(self):
        simulation = LabSimulation(seed=12, sessions=5, policy='organic', model=LabModel())
        simulation._draws[:, :, :2] = 0.
        simulation._draws[:, :, 2] = 1.
        while not simulation.done:
            simulation.advance(200)
        self.assertLessEqual(simulation.purchase_rewards, 5.)
        self.assertGreater(simulation.item_purchases, simulation.purchase_rewards)


class LabEngineTests(unittest.TestCase):
    def test_decision_event_keeps_original_session_when_it_ends_that_session(self):
        simulation = LabSimulation(seed=92000, sessions=2, policy='organic', model=LabModel())
        simulation._draws[:, :, 2] = 1.
        simulation._draws[0, simulation.cursor, 2] = 0.
        snapshot = simulation.advance(1)
        event = next(row for row in reversed(snapshot['events']) if row['kind'] == 'decision')
        self.assertEqual(snapshot['last_decision']['session'], 1)
        self.assertEqual(event['session'], 1)
        self.assertEqual(snapshot['current']['session'], 2)

    def test_guidance_keeps_pre_decision_context_when_session_changes(self):
        simulation = LabSimulation(seed=92000, sessions=2, policy='organic', model=LabModel())
        before = simulation._context()
        remaining = [int(b - s) for b, s in zip(simulation.budgets, simulation.spent)]
        simulation._draws[:, :, 2] = 1.
        simulation._draws[0, simulation.cursor, 2] = 0.
        snapshot = simulation.advance(1)
        guidance = snapshot['last_decision']['guidance']
        self.assertEqual(guidance['segment_id'], before['segment'])
        self.assertEqual(guidance['converted_before'], before['converted'])
        self.assertEqual(guidance['ads_seen'], before['ads_seen'])
        self.assertEqual(guidance['remaining_cents'], remaining)
        self.assertEqual(snapshot['current']['session'], 2)

    def test_strong_baselines_are_available(self):
        for policy in ('quality', 'greedy'):
            simulation = LabSimulation(seed=8, sessions=2, policy=policy, model=LabModel())
            simulation.advance(1)

    def test_metrics_do_not_include_unobserved_future_sessions(self):
        simulation = LabSimulation(seed=92000, sessions=100, model=LabModel())
        metrics = simulation.metrics()
        self.assertEqual(metrics['sessions_completed'], 0)
        self.assertIsNone(metrics['session_cvr'])
        self.assertIsNone(metrics['organic_session_cvr'])
        self.assertEqual(len(simulation.snapshot()['current']['products']), 20)
        self.assertTrue(any(not p['observed'] for p in simulation.snapshot()['current']['products']))

    def test_budget_and_click_accounts_reconcile_under_adversarial_clicks(self):
        simulation = LabSimulation(seed=12, sessions=5, policy='bid', budget_scale=.01, model=LabModel())
        simulation._draws[:, :, 0] = 0.
        simulation._draws[:, :, 1:] = 1.
        while not simulation.done:
            simulation.advance(200)
        metrics = simulation.metrics()
        self.assertEqual(metrics['spend_cents'], [120, 0, 0])
        self.assertEqual(metrics['spend_cents'], [n * cost for n, cost in zip(metrics['brand_clicks'], (120, 100, 80))])
        self.assertTrue(all(s <= b for s, b in zip(metrics['spend_cents'], metrics['budget_cents'])))
        self.assertEqual(metrics['budget_overshoots'], 0)

    def test_zero_budget_has_only_organic_exposure(self):
        simulation = LabSimulation(seed=1, sessions=5, budget_scale=0, model=LabModel())
        while not simulation.done:
            simulation.advance(200)
        self.assertEqual(simulation.spent, [0, 0, 0])
        self.assertEqual(simulation.sponsored_impressions, 0)

    def test_organic_trajectory_matches_paired_organic_reference(self):
        simulation = LabSimulation(seed=97, sessions=100, policy='organic', model=LabModel())
        while not simulation.done:
            simulation.advance(200)
        metrics = simulation.metrics()
        self.assertEqual(metrics['session_cvr'], metrics['organic_session_cvr'])
        self.assertEqual(metrics['delta_cvr'], 0)

    def test_reproducible_snapshot_and_no_updates_after_done(self):
        one = LabSimulation(seed=8, sessions=4, policy='random', model=LabModel())
        two = LabSimulation(seed=8, sessions=4, policy='random', model=LabModel())
        while not one.done:
            self.assertEqual(one.advance(200), two.advance(200))
        before = one.snapshot()
        self.assertEqual(before, one.advance(200))
        json.dumps(before, allow_nan=False)

    def test_sponsors_never_appear_outside_eight_slots(self):
        simulation = LabSimulation(seed=6, sessions=10, policy='random', model=LabModel())
        while not simulation.done:
            snapshot = simulation.advance(8)
            for block in snapshot['completed_blocks']:
                for product in block['products']:
                    if product['sponsored']:
                        self.assertIn(product['position'], (3, 4, 5, 6, 11, 12, 13, 14))

    def test_invalid_requests_are_rejected_without_work(self):
        for kwargs in ({'sessions': 0}, {'sessions': True}, {'seed': -1},
                       {'budget_scale': float('nan')}, {'policy': 'invented'}, {'scenario': 'invented'}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                LabSimulation(model=LabModel(), **kwargs)
        simulation = LabSimulation(model=LabModel())
        for invalid in (0, -1, 201, True, .5):
            with self.subTest(steps=invalid), self.assertRaises(ValueError):
                simulation.advance(invalid)


class LearnedModelTests(unittest.TestCase):
    def test_identity_depends_on_parameters_and_structure_not_metadata_timing(self):
        model = LabModel()
        identity = model.identity()
        model.metadata['elapsed_seconds'] = 987654
        self.assertEqual(identity, model.identity())
        model.trials[0, 0] += 1
        self.assertNotEqual(identity, model.identity())
        model.trials[0, 0] -= 1
        model.continuation[0] += .01
        self.assertNotEqual(identity, model.identity())

    def test_greedy_uses_same_quality_filter_but_immediate_purchase_score(self):
        model = LabModel()
        model.trials.fill(1000)
        model.exposures.fill(1000.)
        model.clicks.fill(100)
        model.purchases.fill(10)
        model.purchases[0, 2] = 20
        model.purchases[0, 8] = 30
        model._q = np.zeros((3, 3, 20, 8, N_ACTIONS))
        model._q[0, 0, 2, 0, 2] = .9
        model._q[0, 0, 2, 0, 8] = .2
        arguments = ([0] * 3, [100] * 3, [0] * 3, .1, np.random.default_rng(1))
        self.assertEqual(select_action(model, CONTEXT, [0, 2, 8], 'safe_rl', *arguments).action, 2)
        self.assertEqual(select_action(model, CONTEXT, [0, 2, 8], 'greedy', *arguments).action, 8)

    def test_quality_baseline_ranks_quality_and_retains_organic_without_ads(self):
        arguments = ([0] * 3, [100] * 3, [0] * 3, .1, np.random.default_rng(1))
        choice = select_action(LabModel(), CONTEXT, [0, 1, 3, 4], 'quality', *arguments)
        self.assertEqual(choice.action, 4)
        self.assertEqual(select_action(LabModel(), CONTEXT, [0], 'quality', *arguments).action, 0)

    def test_model_learns_purchase_response_instead_of_click_rate(self):
        model = LabModel()
        # Promoted action 1 gets many clicks and no purchases. Action 2 gets
        # fewer clicks but actually converts. Only factual events are observed.
        for index in range(1000):
            model.observe(CONTEXT, 0, clicked=index < 60, purchased=index < 5, left=False)
            model.observe(CONTEXT, 1, clicked=index < 300, purchased=False, left=False)
            model.observe(CONTEXT, 2, clicked=index < 100, purchased=index < 25, left=False)
        estimates = [model.estimates(CONTEXT, action) for action in (1, 2)]
        self.assertGreater(estimates[0]['click_probability'], estimates[1]['click_probability'])
        self.assertLess(estimates[0]['purchase_probability'], estimates[1]['purchase_probability'])
        choice = select_action(model, CONTEXT, [0, 1, 2], 'safe_rl', [0, 0, 0], [100, 100, 100], [0, 0, 0], .1, np.random.default_rng(1))
        self.assertEqual(choice.action, 2)

    def test_no_evidence_falls_back_instead_of_forcing_unsafe_spend(self):
        choice = select_action(LabModel(), CONTEXT, [0, 1, 2], 'safe_rl', [0, 0, 0], [100, 100, 100], [0, 0, 0], .7, np.random.default_rng(1))
        self.assertEqual(choice.action, 0)
        self.assertTrue(choice.conflict)

    def test_converted_session_has_zero_value_and_excludes_ad_candidates(self):
        model = LabModel()
        context = {**CONTEXT, 'converted': True}
        np.testing.assert_equal(model.scores(context), np.zeros(N_ACTIONS))
        choice = select_action(model, context, [0, 2, 8], 'safe_rl', [0] * 3, [100] * 3, [0] * 3, .5, np.random.default_rng(1))
        self.assertEqual(choice.action, 0)
        self.assertFalse(any(row['eligible'] for row in choice.candidates if row['action']))

    def test_observation_rejects_impossible_purchase(self):
        model = LabModel()
        with self.assertRaises(ValueError):
            model.observe(CONTEXT, 2, clicked=False, purchased=True, left=False)
        self.assertEqual(model.trials.sum(), 0)

    def test_persistence_round_trip_and_corrupt_statistics_rejected(self):
        model = LabModel()
        model.observe(CONTEXT, 2, clicked=True, purchased=True, left=False)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'model.npz'
            model.save(path)
            restored = LabModel.load(path)
            np.testing.assert_equal(restored.purchases, model.purchases)
            self.assertEqual(restored.identity(), model.identity())
            self.assertEqual(restored.metadata['model_id'], model.identity())
            restored.purchases[0, 2] = 100
            restored.save(path)
            with self.assertRaises(ValueError):
                LabModel.load(path)

    def test_inference_is_frozen_and_training_split_cannot_be_reused_as_test(self):
        model = LabModel()
        model.metadata['training_seed'] = 123
        before = model.trials.tobytes()
        select_action(model, CONTEXT, [0, 2], 'safe_rl', [0] * 3, [100] * 3, [0] * 3, .5, np.random.default_rng(1))
        self.assertEqual(before, model.trials.tobytes())
        with self.assertRaises(ValueError):
            evaluate_lab(model, seeds=[123, 124], sessions=2)

    def test_directed_integrity_checks_are_real_boolean_results(self):
        checks = integrity_checks(LabModel())
        self.assertGreaterEqual(len(checks), 7)
        self.assertTrue(all(check['passed'] is True for check in checks), checks)

    def test_strong_comparator_does_not_claim_superiority_from_point_estimate(self):
        rows = [dict(scenario='balanced', policy=policy, seed=seed, session_cvr=cvr)
                for seed, values in [(1, (.15, .12, .12)), (2, (.10, .11, .11))]
                for policy, cvr in zip(('safe_rl', 'quality', 'greedy'), values)]
        comparisons = strong_baseline_comparisons(rows, 'balanced')
        for value in comparisons.values():
            self.assertGreater(value['delta_cvr'], 0)
            self.assertLess(value['delta_cvr_ci95'][0], 0)
            self.assertFalse(value['superiority_demonstrated'])


if __name__ == '__main__':
    unittest.main()
