import unittest
from unittest.mock import patch
import json
from pathlib import Path

from retail_media.lab_catalog import ORGANIC, SPONSORED, present_product
from retail_media.lab_engine import LabSimulation
from retail_media.lab_model import CATALOGUE, LabModel, fingerprint, organic_product


class CatalogPresentationTests(unittest.TestCase):
    def test_twenty_distinct_organic_products_per_category(self):
        for category in range(3):
            for depth in range(3):
                products = [present_product(organic_product(category, p), depth) for p in range(1, 21)]
                self.assertEqual(len({p['name'] for p in products}), 20)
                self.assertEqual(len({p['image_key'] for p in products}), 20)
                self.assertTrue(all(p['price_cents'] > 0 for p in products))
                self.assertEqual({p['action'] for p in products}, {0})

    def test_sponsored_metadata_never_changes_learned_catalogue_or_profile(self):
        before = fingerprint()
        for raw in CATALOGUE:
            original = dict(raw)
            shown = present_product(raw)
            for field in ('action', 'brand_id', 'category_id', 'quality', 'rating'):
                self.assertEqual(raw[field], shown[field])
            self.assertEqual(raw, original)
        self.assertEqual(before, fingerprint())
        self.assertEqual(len({present_product(p)['image_key'] for p in CATALOGUE}), 48)

    def test_grid_decision_event_and_candidate_share_the_same_display_sku(self):
        simulation = LabSimulation(seed=2026, sessions=2, policy='bid', model=LabModel())
        simulation._draws[:, :, 0] = 0.
        simulation._draws[:, :, 1:] = 1.
        snapshot = simulation.advance(1)
        decision = snapshot['last_decision']
        chosen = next(c for c in decision['candidates'] if c['action'] == decision['action'])
        card = snapshot['current']['products'][decision['position'] - 1]
        self.assertEqual(decision['product_name'], chosen['name'])
        self.assertEqual(card['name'], chosen['name'])
        self.assertEqual(card['image_key'], chosen['image_key'])
        event = next(e for e in snapshot['events'] if e['kind'] == 'click')
        self.assertIn(card['name'], event['text'])

    def test_organic_fallback_matches_preview_after_block_rotation(self):
        simulation = LabSimulation(seed=2026, sessions=2, policy='organic', model=LabModel())
        simulation._draws[:, :, 2] = 1.
        for _ in range(9):
            before = simulation.snapshot()['current']
            expected = before['products'][before['position'] - 1]
            decision = simulation.advance(1)['last_decision']
            self.assertEqual(decision['product_name'], expected['name'])
            self.assertEqual(decision['candidates'][0]['name'], expected['name'])

    def test_every_display_product_has_an_image_in_the_public_manifest(self):
        manifest = json.loads((Path(__file__).resolve().parents[1] / 'retail_media/web/images/catalogue/manifest.json').read_text())
        keys = {present_product(p)['image_key'] for p in CATALOGUE}
        keys.update(present_product(organic_product(c, pos))['image_key'] for c in range(3) for pos in range(1, 21))
        self.assertTrue(keys <= set(manifest['images']))
        self.assertEqual(len(keys), 60)

    def test_presentation_does_not_change_actions_finances_rewards_or_cvr(self):
        for policy in ('random', 'bid'):
            shown = LabSimulation(seed=207, sessions=10, policy=policy, model=LabModel())
            with patch('retail_media.lab_engine.present_product', side_effect=lambda p, depth=0: dict(p)), patch('retail_media.lab_engine.present_candidate', side_effect=lambda p, context: dict(p)):
                raw = LabSimulation(seed=207, sessions=10, policy=policy, model=LabModel())
            for _ in range(10):
                shown_snapshot = shown.advance(20)
                with patch('retail_media.lab_engine.present_product', side_effect=lambda p, depth=0: dict(p)), patch('retail_media.lab_engine.present_candidate', side_effect=lambda p, context: dict(p)):
                    raw_snapshot = raw.advance(20)
                self.assertEqual(shown_snapshot['metrics'], raw_snapshot['metrics'])
                self.assertEqual(shown_snapshot['last_decision']['action'], raw_snapshot['last_decision']['action'])
                self.assertEqual(shown_snapshot['last_decision']['reward'], raw_snapshot['last_decision']['reward'])
