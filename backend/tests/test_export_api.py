"""POST /api/export/<page>.<fmt> (the downloads, moved from the Flask frontend
so the React one in web/ can use them) and /api/antibiotics/?model=.

    python -m unittest discover -s backend/tests
"""
import base64
import csv
import io
import json
import os
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.test import Client, override_settings  # noqa: E402
from django_ratelimit import core as ratelimit_core  # noqa: E402
from amr_constants import ANTIBIOTIC_ALIASES  # noqa: E402
from api import exports, model_registry  # noqa: E402

FORECAST = {'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.81,
            'confidence': 81.0, 'threshold': 0.15, 'drug_class': 'fluoroquinolone',
            'model_used': 'LightGBM', 'comparison_chart': [{'antibiotic': 'ampicillin',
                                                            'resistance_probability': 64.2}]}
INPUTS = {'genus': 'Escherichia', 'species': 'coli', 'taxon_id': '562', 'mic_value': '4', 'mic_sign': '>='}
TIMELINE = {'antibiotic': 'ciprofloxacin', 'n_weeks': 2, 'seed': 42, 'failure_week': None,
            'final_resistant_percent': 12.0, 'sequence_length': 1000, 'gc_content': 50.0, 'summary': 's',
            'timeline': [{'week': w, 'susceptible_fraction': 90.0, 'intermediate_fraction': 5.0,
                          'resistant_fraction': 5.0, 'cumulative_mutations': w, 'mic_fold_change': 1.0,
                          'treatment_effective': True} for w in (1, 2)]}
# the smallest valid PNG: 1x1 pixel
PNG = ('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGA'
       'hKmMIQAAAABJRU5ErkJggg==')


def post(path, **fields):
    return Client().post(path, {k: json.dumps(v) if isinstance(v, dict) else v for k, v in fields.items()},
                         REMOTE_ADDR='10.9.9.9')


class Export(unittest.TestCase):
    def setUp(self):
        off = override_settings(RATELIMIT_ENABLE=False)
        off.enable()
        self.addCleanup(off.disable)

    def test_forecast_csv_has_the_result_and_the_served_models_auc(self):
        r = post('/api/export/forecast.csv', result=FORECAST, inputs=INPUTS)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'text/csv')
        self.assertRegex(r['Content-Disposition'], r'attachment; filename="amr-forecast-\d{8}-\d{4}\.csv"')
        self.assertIn('Content-Disposition', r['Access-Control-Expose-Headers'])
        rows = list(csv.DictReader(io.StringIO(r.content.decode())))
        self.assertEqual(rows[0]['prediction'], 'Resistant')
        self.assertEqual(rows[0]['genus'], 'Escherichia')
        lgbm = model_registry.get_lgbm()
        self.assertEqual(rows[0]['model_auc_unseen_genomes'],
                         exports.summarize_metrics(lgbm.status if lgbm else None)['auc_ci'])

    def test_pdf_with_a_chart(self):
        r = post('/api/export/forecast.pdf', result=FORECAST, inputs=INPUTS, chart=PNG)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r['Content-Type'], 'application/pdf')
        self.assertTrue(r.content.startswith(b'%PDF'))

    def test_timeline_downloads_say_simulation(self):
        r = post('/api/export/timeline.csv', result=TIMELINE)
        self.assertEqual(r.status_code, 200)
        self.assertIn(exports.SIMULATION, r.content.decode())
        self.assertEqual(post('/api/export/timeline.pdf', result=TIMELINE).status_code, 200)

    def test_refuses_an_empty_result(self):
        r = post('/api/export/forecast.csv', inputs=INPUTS)
        self.assertEqual(r.status_code, 400)
        self.assertIn('Nothing to export', r.json()['error'])
        self.assertEqual(post('/api/export/forecast.csv', result='not json').status_code, 400)

    def test_batch_is_csv_only(self):
        r = post('/api/export/batch.pdf', result={'rows': []})
        self.assertEqual(r.status_code, 400)
        r = post('/api/export/batch.csv', result={'rows': [{'row': 1, 'antibiotic': 'ampicillin',
                                                             'prediction': 'Resistant', 'probability': 0.7}]})
        self.assertEqual(r.status_code, 200)
        self.assertIn('ampicillin', r.content.decode())

    def test_a_result_it_cannot_read_is_a_400_not_a_crash(self):
        r = post('/api/export/timeline.pdf', result={'timeline': [{'week': 1}]})
        self.assertEqual(r.status_code, 400)
        self.assertIn('Could not build', r.json()['error'])

    def test_unknown_pages_and_formats_are_not_routes(self):
        self.assertEqual(post('/api/export/genes.csv', result=FORECAST).status_code, 404)
        self.assertEqual(post('/api/export/forecast.xlsx', result=FORECAST).status_code, 404)

    def test_a_spreadsheet_formula_stays_text(self):
        r = post('/api/export/forecast.csv', result=dict(FORECAST, antibiotic='=HYPERLINK("x")'), inputs=INPUTS)
        self.assertIn("'=HYPERLINK", r.content.decode())


class ExportRateLimit(unittest.TestCase):
    def test_limited_per_ip(self):
        from django.conf import settings
        n = int(settings.RATE_LIMITS['export'].split('/')[0])
        # django-ratelimit counts per clock minute: hold the clock so the
        # requests cannot straddle a minute boundary
        frozen = SimpleNamespace(time=lambda t=ratelimit_core.time.time(): t)
        with override_settings(RATELIMIT_ENABLE=True), mock.patch.object(ratelimit_core, 'time', frozen):
            codes = [Client().post('/api/export/forecast.csv', {'result': json.dumps(FORECAST)},
                                   REMOTE_ADDR='10.7.7.7').status_code for _ in range(n + 1)]
        self.assertEqual(codes[-1], 429)


class MetricsSummary(unittest.TestCase):
    def test_matches_the_frontends(self):
        s = exports.summarize_metrics({'default_threshold': 0.15, 'metrics': {
            'test': {'auc_roc': 0.7741, 'auc_roc_ci': [0.7702, 0.778]}, 'run_id': 'v7'}})
        self.assertEqual(s['auc_ci'], '0.774 [0.770–0.778]')
        self.assertEqual(s['threshold'], 0.15)
        self.assertEqual(s['run_id'], 'v7')
        self.assertEqual(exports.summarize_metrics(None)['auc_ci'], 'not measured')


class AntibioticsForModel(unittest.TestCase):
    def test_lgbm_names_are_canonical_known_and_unique(self):
        names = Client().get('/api/antibiotics/?model=lgbm').json()['antibiotics']
        lgbm = model_registry.get_lgbm()
        if not (lgbm and lgbm.is_trained):
            self.skipTest('no trained forecaster')
        self.assertEqual(len(names), len(set(names)))
        known = {ANTIBIOTIC_ALIASES.get(n, n) for n in lgbm.vocabulary['antibiotics']}
        self.assertTrue(set(names) <= known)
        self.assertIn('ciprofloxacin', names)
        # drug classes the cleaning drops are never offered
        dropped = {k for k, v in ANTIBIOTIC_ALIASES.items() if not v}
        self.assertFalse(dropped & set(names))

    def test_kmer_names(self):
        kmer = model_registry.get_kmer()
        names = Client().get('/api/antibiotics/?model=kmer').json()['antibiotics']
        if not (kmer and kmer.ab_list):
            self.skipTest('no genome model')
        self.assertTrue(set(names) <= {ANTIBIOTIC_ALIASES.get(n, n) for n in kmer.ab_list})

    def test_an_unknown_model_gets_the_full_list(self):
        self.assertEqual(Client().get('/api/antibiotics/?model=x').json(),
                         Client().get('/api/antibiotics/').json())


if __name__ == '__main__':
    unittest.main()
