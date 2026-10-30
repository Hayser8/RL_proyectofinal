import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from retail_media.agent import QAgent
from retail_media.campaign import CampaignLedger, run_campaign, write_campaign_report
from retail_media.config import load_config
from retail_media.environment import RetailMediaEnv


class CampaignLedgerTests(unittest.TestCase):
    def setUp(self):
        self.config = replace(load_config(), campaign_days=3, sessions=4,
                              brands=tuple({**b, 'budget_cents': 100, 'cpc_cents': 10}
                                           for b in load_config().brands))

    def test_unspent_budget_carries_and_rounding_reaches_exact_total(self):
        ledger = CampaignLedger(self.config)
        self.assertEqual(ledger.start_day(), [33, 33, 33])
        ledger.finish_day([10, 20, 0])
        self.assertEqual(ledger.start_day(), [56, 46, 66])
        ledger.finish_day([50, 40, 60])
        self.assertEqual(ledger.start_day(), [40, 40, 40])
        ledger.finish_day([40, 40, 40])
        self.assertEqual(ledger.spent, [100, 100, 100])
        with self.assertRaises(RuntimeError):
            ledger.start_day()

    def test_invalid_close_does_not_change_balance_or_lose_open_day(self):
        ledger = CampaignLedger(self.config)
        ledger.start_day()
        for invalid in ([34, 0, 0], [-1, 0, 0], [1, 2], [True, 0, 0]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                ledger.finish_day(invalid)
        self.assertEqual(ledger.spent, [0, 0, 0])
        self.assertEqual(ledger.day, 0)
        ledger.finish_day([0, 0, 0])
        self.assertEqual(ledger.start_day(), [66, 66, 66])

    def test_cannot_open_or_close_a_day_twice(self):
        ledger = CampaignLedger(self.config)
        with self.assertRaises(RuntimeError):
            ledger.finish_day([0, 0, 0])
        ledger.start_day()
        with self.assertRaises(RuntimeError):
            ledger.start_day()

    def test_environment_uses_carried_allocation_and_checks_limit(self):
        env = RetailMediaEnv(self.config, seed=3, budget_cents=[100, 50, 0])
        self.assertEqual(env.budgets.tolist(), [100, 50, 0])
        env.click_draws.fill(0.)
        while not env.done:
            allowed = env.allowed_actions()
            env.step(next((a for a in allowed if a), 0))
        self.assertTrue(np.all(env.spent <= [100, 50, 0]))
        self.assertEqual(env.spent.tolist(), [100, 50, 0])
        for invalid in ([101, 0, 0], [-1, 0, 0], [1, 2], [1.5, 0, 0]):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                RetailMediaEnv(self.config, budget_cents=invalid)


class CampaignRunnerTests(unittest.TestCase):
    def setUp(self):
        self.config = replace(load_config(), campaign_days=3, sessions=10,
                              brands=tuple({**b, 'budget_cents': 100, 'cpc_cents': 10}
                                           for b in load_config().brands))

    def test_zero_traffic_day_preserves_balance_and_cvr_uses_sessions(self):
        result = run_campaign(self.config, QAgent(), seed=50000,
                              sessions_per_day=[0, 2, 10], policy='organic')
        self.assertEqual(len(result['days']), 3)
        self.assertEqual(result['days'][0]['metrics']['sessions'], 0)
        self.assertEqual(result['days'][1]['allocation_cents'], [66, 66, 66])
        self.assertEqual(result['days'][2]['allocation_cents'], [100, 100, 100])
        self.assertEqual(result['summary']['sessions'], 12)
        converted = sum(day['metrics']['converted_sessions'] for day in result['days'])
        self.assertEqual(result['summary']['session_cvr'], converted / 12)
        self.assertEqual(result['summary']['session_cvr'], result['summary']['organic_session_cvr'])
        self.assertEqual(result['summary']['spend_cents'], [0, 0, 0])
        self.assertEqual(result['summary']['remaining_cents'], [100, 100, 100])
        self.assertFalse(result['summary']['delivery_pass'])

    def test_seed_replay_and_frozen_policy(self):
        agent = QAgent()
        agent.values((0, 0))[1] = 5.
        before = {k: v.copy() for k, v in agent.table.items()}
        first = run_campaign(self.config, agent, seed=50000)
        second = run_campaign(self.config, agent, seed=50000)
        self.assertEqual(first, second)
        self.assertEqual(set(before), set(agent.table))
        for key in before:
            np.testing.assert_array_equal(before[key], agent.table[key])
        self.assertTrue(all(s <= 100 for s in first['summary']['spend_cents']))

    def test_all_zero_traffic_reports_null_cvr_and_under_delivery(self):
        result = run_campaign(self.config, QAgent(), sessions_per_day=[0, 0, 0])
        self.assertIsNone(result['summary']['session_cvr'])
        self.assertIsNone(result['summary']['delta_cvr'])
        self.assertEqual(result['summary']['brand_status'], ['under_target'] * 3)

    def test_bad_schedule_or_overlapping_training_seeds_rejected(self):
        agent = QAgent()
        for schedule in ([0, 1], [0, -1, 1], [1., 1, 1], [True, 1, 1]):
            with self.subTest(schedule=schedule), self.assertRaises(ValueError):
                run_campaign(self.config, agent, sessions_per_day=schedule)
        agent.metadata = {'training_seeds': [50001]}
        with self.assertRaises(ValueError):
            run_campaign(self.config, agent, seed=50000)
        with self.assertRaises(ValueError):
            run_campaign(self.config, agent, policy='typo')

    def test_report_exports_daily_brand_balance(self):
        result = run_campaign(self.config, QAgent(), sessions_per_day=[0, 1, 2])
        with tempfile.TemporaryDirectory() as directory:
            write_campaign_report(result, directory)
            path = Path(directory)
            persisted = json.loads((path / 'campaign-rl.json').read_text())
            self.assertEqual(persisted['summary'], result['summary'])
            self.assertEqual(persisted['days'], result['days'])
            csv = (path / 'campaign-rl.csv').read_text()
            self.assertEqual(len(csv.splitlines()), 10)  # Header + 3 days × 3 brands.
            self.assertIn('cumulative_spend_cents', csv)


if __name__ == '__main__':
    unittest.main()
