"""Reloading the forecaster after a promotion picks up the whole new model.

    python -m unittest discover -s backend/tests

Before 2026-09-30, _load() re-read the booster and lgbm_meta.joblib but not
lgbm_metrics.json, so after promote.py + POST /api/reload/ the page showed the
old run's id and metrics next to the new model's predictions.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from ml_models.lgbm_predictor import LGBMResistancePredictor  # noqa: E402

SERVED = os.path.join(BACKEND, 'trained_models')
FILES = ('amr_lgbm_final_model.txt', 'ab_rate_full.joblib', 'taxon_ab_rate_full.joblib',
         'genus_ab_rate_full.joblib', 'lgbm_meta.joblib', 'lgbm_metrics.json')


@unittest.skipUnless(all(os.path.exists(os.path.join(SERVED, f)) for f in FILES),
                     'no promoted forecaster in backend/trained_models')
class Reload(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        for f in FILES:
            shutil.copy(os.path.join(SERVED, f), self.dir)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_reload_reads_the_new_metrics(self):
        model = LGBMResistancePredictor(self.dir)
        before = model.run_id
        path = os.path.join(self.dir, 'lgbm_metrics.json')
        with open(path, encoding='utf-8') as fh:
            metrics = json.load(fh)
        metrics['run_id'] = 'promoted_later'
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(metrics, fh)
        model._load()
        self.assertNotEqual(before, 'promoted_later')
        self.assertEqual(model.run_id, 'promoted_later')
        self.assertEqual(model.status['metrics']['run_id'], 'promoted_later')

    def test_reload_without_a_model_forgets_the_old_one(self):
        model = LGBMResistancePredictor(self.dir)
        self.assertTrue(model.is_trained)
        for f in FILES:
            os.remove(os.path.join(self.dir, f))
        model._load()
        self.assertFalse(model.is_trained)
        self.assertIsNone(model.calibration)
        self.assertIsNone(model.metrics)


if __name__ == '__main__':
    unittest.main()
