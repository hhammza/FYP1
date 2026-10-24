"""The timeline ML model behind /api/timeline/'s `ml_forecast` block (format §8).

    python -m unittest discover -s backend/tests
"""
import importlib.util
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from ml_models import timeline_ml  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(BACKEND)
SERVED = os.path.join(BACKEND, 'trained_models')
TRAINING = os.path.join(ROOT, 'experiments', 'timeline_ml', 'timeline_model.py')


def post(**body):
    return Client().post('/api/timeline/', data=json.dumps(body), content_type='application/json')


class Features(unittest.TestCase):
    def test_backend_features_equal_training_features(self):
        spec = importlib.util.spec_from_file_location('timeline_training', TRAINING)
        training = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(training)
        years, pcts, ns = [2004, 2005, 2007, 2010, 2011], [10.0, 12.5, 20.0, 18.0, 30.0], [40, 25, 60, 30, 90]
        for t in (2005, 2008, 2011, 2012):
            self.assertEqual(timeline_ml.history_features(years, pcts, ns, t),
                             training.history_features(years, pcts, ns, t))


@unittest.skipUnless(os.path.exists(os.path.join(SERVED, 'timeline_ml', 'model.txt')), 'no timeline model promoted')
class Forecast(unittest.TestCase):
    def setUp(self):
        cache.clear()
        self.model = timeline_ml.TimelineMLForecaster(SERVED)

    def test_block_shape(self):
        m = self.model.forecast('salmonella', 'Ciprofloxacin')
        self.assertEqual((m['organism'], m['antibiotic']), ('Salmonella', 'ciprofloxacin'))
        self.assertGreaterEqual(len(m['history']), 2)
        self.assertEqual(len(m['forecast']), timeline_ml.YEARS_AHEAD)
        years = [f['year'] for f in m['forecast']]
        self.assertEqual(years[0], m['history'][-1]['year'] + 1)
        for f in m['forecast']:
            self.assertTrue(0 <= f['lo'] <= f['resistant_pct'] <= f['hi'] <= 100)
        self.assertIn('model', m['metrics'])
        self.assertIn('last_value', m['metrics'])

    def test_unknown_organism_or_drug_gives_nothing(self):
        self.assertIsNone(self.model.forecast('Notagenus', 'ciprofloxacin'))
        self.assertIsNone(self.model.forecast('Salmonella', 'not-a-drug'))

    def test_endpoint_adds_the_forecast_and_keeps_the_simulation(self):
        r = post(fasta_text='>a\n' + 'ACGT' * 50, antibiotic='ciprofloxacin', genus='Salmonella')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn('timeline', d)
        self.assertEqual(d['ml_forecast']['organism'], 'Salmonella')

    def test_no_genus_and_a_short_sequence_gives_the_simulation_only(self):
        r = post(fasta_text='>a\n' + 'ACGT' * 50, antibiotic='ciprofloxacin')
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('ml_forecast', r.json())


if __name__ == '__main__':
    unittest.main()
