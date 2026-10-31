import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from retail_media.config import Config, load_config
from retail_media.environment import RetailMediaEnv
from retail_media.agent import QAgent
from retail_media.experiment import choose_action, evaluate, train
from retail_media.reporting import write_report


class ConfigurationTests(unittest.TestCase):
    def test_sponsored_slots_expose_their_configured_commercial_multiplier(self):
        config = load_config()
        self.assertEqual(config.position_multiplier(3), 1.30)
        self.assertEqual(config.position_multiplier(14), 0.70)

    def test_invalid_position_multiplier_configuration_is_rejected(self):
        config = load_config()
        with self.assertRaises(ValueError):
            replace(config, position_multipliers=(1.30,) * 7).validate()
        with self.assertRaises(ValueError):
            replace(config, position_multipliers=(1.30, 1.18, 1.08, 1.00, 0.90, 0.82, 0.76, 0.0)).validate()

    def test_campaign_requires_positive_conversion_value(self):
        config = load_config()
        invalid_brands = ({**config.brands[0], 'conversion_value_cents': 0}, *config.brands[1:])
        with self.assertRaises(ValueError):
            replace(config, brands=invalid_brands).validate()


class EnvironmentTests(unittest.TestCase):
    def setUp(self):
        self.config = replace(load_config(), sessions=20)

    def test_only_eight_positions_allow_sponsored_products(self):
        env = RetailMediaEnv(self.config, seed=1)
        self.assertEqual(env.config.sponsored_slots, (3, 4, 5, 6, 11, 12, 13, 14))
        while not env.done:
            self.assertIn(env.position, self.config.sponsored_slots)
            env.step(0)
        self.assertEqual(env.metrics()['sessions'], 20)
        self.assertEqual(env.metrics()['spend_cents'], [0, 0, 0])

    def test_cpc_costs_only_on_click_and_never_exceeds_budget(self):
        env = RetailMediaEnv(self.config, seed=4)
        while not env.done:
            available = env.allowed_actions()
            action = next((a for a in available if a), 0)
            _, _, info = env.step(action)
            self.assertEqual(info['cost_cents'], self.config.brands[info['brand']]['cpc_cents'] if info['sponsored_click'] else 0)
        for spent, budget in zip(env.spent, env.budgets):
            self.assertLessEqual(spent, budget)
        self.assertGreater(sum(env.spent), 0)

    def test_invalid_action_does_not_mutate_environment(self):
        env = RetailMediaEnv(self.config, seed=0)
        with self.assertRaises(ValueError):
            env.step(-1)
        self.assertEqual(env.index, 0)

    def test_budget_smaller_than_click_leaves_organic_available(self):
        brands = tuple({**b, 'budget_cents': 1} for b in self.config.brands)
        env = RetailMediaEnv(replace(self.config, brands=brands), seed=4)
        self.assertEqual(env.allowed_actions(), [0])

    def test_identical_seeds_replay_organic_sessions(self):
        first = RetailMediaEnv(self.config, seed=12)
        second = RetailMediaEnv(self.config, seed=12)
        while not first.done:
            first.step(0)
            second.step(0)
        self.assertEqual(first.metrics(), second.metrics())
        self.assertEqual(first.metrics()['session_cvr'], first.metrics()['organic_session_cvr'])

    def test_pacing_can_require_an_underexposed_brand(self):
        env = RetailMediaEnv(self.config, seed=8)
        while env.progress < .45:
            env.step(0)  # Organic baseline explicitly bypasses commercial pacing.
        choices = env.allowed_actions()
        self.assertNotIn(0, choices)
        self.assertGreater(len(choices), 0)

    def test_zero_traffic_rejected(self):
        with self.assertRaises(ValueError):
            RetailMediaEnv(replace(self.config, sessions=0))

    def test_duplicate_sponsored_product_is_masked_within_block(self):
        env = RetailMediaEnv(self.config, seed=6)
        action = env.allowed_actions()[1]
        env.step(action)
        self.assertNotIn(action, env.allowed_actions())

    def test_position_multiplier_changes_sponsored_click_probability(self):
        top = RetailMediaEnv(self.config, seed=6)
        lower = RetailMediaEnv(self.config, seed=6)
        top.item_segments[:] = 0
        lower.item_segments[:] = 0
        lower.index = 7  # Slot 14 in the same 20-product block.

        _, _, top_info = top.step(2)  # Nova · Tecnología Plus
        _, _, lower_info = lower.step(2)

        expected_top_ctr = (.057 + .027) * np.exp(-.018 * 2) * 1.30
        expected_lower_ctr = (.057 + .027) * np.exp(-.018 * 13) * .70
        self.assertAlmostEqual(top_info['sponsored_ctr'], expected_top_ctr)
        self.assertAlmostEqual(lower_info['sponsored_ctr'], expected_lower_ctr)
        self.assertGreater(top_info['sponsored_ctr'], lower_info['sponsored_ctr'])

    def test_sponsored_events_and_metrics_report_realized_commercial_value(self):
        env = RetailMediaEnv(self.config, seed=6)
        env.click_draws.fill(0.0)
        env.purchase_draws.fill(0.0)

        _, _, info = env.step(2)  # Nova · Tecnología Plus at slot 3
        metrics = env.metrics()

        self.assertEqual(info['position'], 3)
        self.assertEqual(info['position_multiplier'], 1.30)
        self.assertEqual(info['cpc_revenue_cents'], 120)
        self.assertEqual(info['conversion_value_cents'], 24000)
        self.assertEqual(metrics['cpc_revenue_cents'], 120)
        self.assertEqual(metrics['sponsored_conversion_value_cents'], 24000)

    def test_reward_reports_conversion_revenue_and_cvr_protection_components(self):
        env = RetailMediaEnv(self.config, seed=6, cvr_multiplier=7.0)
        env.click_draws.fill(0.0)
        env.purchase_draws.fill(0.0)

        _, reward, info = env.step(2)  # Nova · Tecnología Plus at slot 3

        self.assertEqual(info['reward_components']['conversion_value'], 240.0)
        self.assertEqual(info['reward_components']['cpc_revenue'], 0.24)
        self.assertEqual(info['reward_components']['cvr_protection'], 7.0)
        self.assertEqual(reward, 247.24)


class AgentTests(unittest.TestCase):
    def test_model_rejects_obsolete_state_schema(self):
        config = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'old.npz'
            metadata = {'version': 1, 'config_fingerprint': config.fingerprint(),
                        'actions': 19, 'alpha': .01, 'gamma': .8, 'cvr_multiplier': 0}
            np.savez(path, keys=json.dumps([[0, 0, 0, 0, 0, 0]]), values=np.zeros((1, 19)), metadata=json.dumps(metadata))
            with self.assertRaises(ValueError):
                QAgent.load(path, config)

    def test_model_rejects_position_agnostic_state_schema(self):
        config = load_config()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'position_agnostic.npz'
            metadata = {'version': 2, 'state_schema': 'intent_depth_v1',
                        'config_fingerprint': config.fingerprint(), 'actions': 19,
                        'alpha': .01, 'gamma': .8, 'cvr_multiplier': 0}
            np.savez(path, keys=json.dumps([[0, 0]]), values=np.zeros((1, 19)), metadata=json.dumps(metadata))
            with self.assertRaises(ValueError):
                QAgent.load(path, config)

    def test_position_groups_keep_distinct_q_values_for_the_same_intent(self):
        agent = QAgent()
        first = (0, 0, 0, 0, 0, 1)
        later = (0, 1, 0, 1, 2, 2)
        other_intent = (1, 0, 0, 0, 0, 1)
        agent.update(first, 2, 5., later, [0], done=True)
        self.assertGreater(agent.values(first)[2], 0)
        self.assertEqual(agent.values(later)[2], 0)
        self.assertEqual(agent.values(other_intent)[2], 0)

    def test_q_update_learns_reward_and_masks_invalid_action(self):
        agent = QAgent(actions=3, seed=2)
        state = (0, 1)
        agent.update(state, 2, 5., state, [0, 2], done=True)
        self.assertGreater(agent.values(state)[2], 0)
        self.assertEqual(agent.act(state, [0, 2], epsilon=0), 2)
        self.assertEqual(agent.act(state, [0], epsilon=0), 0)

    def test_model_round_trip(self):
        config = load_config()
        agent = QAgent(actions=19, seed=2)
        agent.update((1, 2), 1, 10., (1, 2), [0], done=True)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'model.npz'
            agent.save(path, config)
            restored = QAgent.load(path, config)
            np.testing.assert_array_equal(agent.values((1, 2)), restored.values((1, 2)))
            incompatible = replace(config, brands=tuple({**b, 'cpc_cents': b['cpc_cents'] + 1} for b in config.brands))
            with self.assertRaises(ValueError):
                QAgent.load(path, incompatible)

    def test_policy_learns_distinct_contexts(self):
        agent = QAgent(actions=3)
        for _ in range(50):
            for context, best in [(0, 1), (1, 2)]:
                for action in [0, 1, 2]:
                    agent.update((context,), action, float(action == best), (context,), [0, 1, 2], done=True)
        self.assertEqual(agent.act((0,), [0, 1, 2], 0), 1)
        self.assertEqual(agent.act((1,), [0, 1, 2], 0), 2)


class ExperimentTests(unittest.TestCase):
    def test_bid_only_prefers_highest_cpc_even_when_it_is_irrelevant(self):
        env = RetailMediaEnv(replace(load_config(), sessions=3), seed=6)
        env.item_segments[:] = 1  # Hogar; action 1 is Nova · Tecnología Esencial.

        action = choose_action('bid', env, QAgent(), np.random.default_rng(1))

        self.assertEqual(action, 1)
        self.assertEqual(env.products[action - 1]['brand'], 0)
        self.assertNotEqual(env.products[action - 1]['category'], env.state()[0])

    def test_rotation_uses_another_brand_after_a_brand_receives_an_impression(self):
        env = RetailMediaEnv(replace(load_config(), sessions=3), seed=6)
        rng = np.random.default_rng(1)
        first = choose_action('rotation', env, QAgent(), rng)
        first_brand = env.products[first - 1]['brand']
        env.step(first)

        second = choose_action('rotation', env, QAgent(), rng)

        self.assertNotEqual(env.products[second - 1]['brand'], first_brand)

    def test_training_produces_nonzero_q_and_artifacts(self):
        config = replace(load_config(), sessions=6)
        with tempfile.TemporaryDirectory() as tmp:
            agent, history = train(config, episodes=2, seed=7, output=Path(tmp))
            self.assertEqual(len(history), 2)
            self.assertTrue(any(np.any(q != 0) for q in agent.table.values()))
            self.assertTrue((Path(tmp) / 'model.npz').exists())
            self.assertTrue((Path(tmp) / 'training.csv').exists())

    def test_evaluation_uses_paired_traffic_and_never_trains_model(self):
        config = replace(load_config(), sessions=6)
        agent = QAgent()
        agent.values((0,))
        before = {k: v.copy() for k, v in agent.table.items()}
        result = evaluate(config, agent, seeds=[10001, 10002], trace_sessions=2)
        self.assertEqual(set(result['policies']), {'organic', 'random', 'relevance', 'bid', 'rotation', 'untrained', 'rl'})
        rows = result['runs']
        for seed in [10001, 10002]:
            same_seed = [r for r in rows if r['seed'] == seed]
            self.assertEqual(len({r['organic_session_cvr'] for r in same_seed}), 1)
            self.assertEqual(len({r['product_impressions'] for r in same_seed}), 1)
        self.assertEqual(set(before), set(agent.table))
        for k, v in before.items():
            np.testing.assert_array_equal(v, agent.table[k])
        self.assertEqual(result['policies']['organic']['delta_cvr_ci95'], [0., 0.])
        self.assertEqual(len(result['policies']['rl']['position_brand_impressions']), 3)
        self.assertEqual(len(result['policies']['rl']['position_brand_impressions'][0]), 8)
        self.assertTrue(result['traces']['rl'])

    def test_report_is_standalone_and_contains_real_grid_traces(self):
        config = replace(load_config(), sessions=4)
        result = evaluate(config, QAgent(), seeds=[10001, 10002], trace_sessions=2)
        with tempfile.TemporaryDirectory() as tmp:
            write_report(result, [], Path(tmp))
            html = (Path(tmp) / 'demo.html').read_text()
            self.assertIn('IntersectionObserver', html)
            self.assertIn('application/json', html)
            self.assertNotIn('__RESULTS__', html)
            self.assertIn('CPC', html)
            self.assertTrue((Path(tmp) / 'evaluation.csv').exists())

    def test_empty_or_training_seed_evaluation_rejected(self):
        config = replace(load_config(), sessions=3)
        agent = QAgent()
        agent.metadata = {'training_seeds': [8]}
        with self.assertRaises(ValueError):
            evaluate(config, agent, seeds=[])
        with self.assertRaises(ValueError):
            evaluate(config, agent, seeds=[8, 9])


if __name__ == '__main__':
    unittest.main()
