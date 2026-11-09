import copy
import unittest
from retail_media.lab_assessment import assess
from retail_media.lab_model import SERVING_ID


class AssessmentTests(unittest.TestCase):
    def setUp(self):
        self.report = {'model_id': 'm', 'scenarios': {'balanced': {'plps': [
            {'category': 'Tecnología', 'ads': [{'category': 'Tecnología'} for _ in range(16)],
             'coverage': {'complete': True}}]}}}
        self.evaluation = {'model_id': 'm', 'serving_id': SERVING_ID,
                           'integrity_checks': [{'passed': True}],
                           'runs': [{'policy': 'safe_rl', 'ad_impressions': [0] + [1] * 48, 'budget_overshoots': 0}]}

    def test_explicit_weights_and_score_are_not_percent_accuracy(self):
        rating = assess(self.report, self.evaluation)
        self.assertEqual(sum(r['maximum'] for r in rating['rows']), 100)
        self.assertEqual(rating['score'], 88)
        self.assertEqual(rating['before_score'], 55)
        self.assertIn('no una métrica', rating['note'])

    def test_missing_exposure_cannot_receive_full_coverage_credit(self):
        self.evaluation['runs'][0]['ad_impressions'][4] = 0
        rating = assess(self.report, self.evaluation)
        self.assertEqual(rating['coverage_runs_passed'], 0)
        self.assertEqual(rating['rows'][3]['points'], 0)

    def test_wrong_model_or_serving_does_not_pass_as_compatible(self):
        for key in ('model_id', 'serving_id'):
            evaluation = copy.deepcopy(self.evaluation)
            evaluation[key] = 'old'
            rating = assess(self.report, evaluation)
            self.assertFalse(rating['complete'])
            self.assertEqual(rating['rows'][1]['points'], 0)

    def test_wrong_plp_or_broken_integrity_loses_its_corresponding_credit(self):
        self.report['scenarios']['balanced']['plps'][0]['ads'][0]['category'] = 'Hogar'
        self.evaluation['integrity_checks'][0]['passed'] = False
        rating = assess(self.report, self.evaluation)
        self.assertEqual(rating['rows'][0]['points'], 0)
        self.assertEqual(rating['rows'][2]['points'], 0)
