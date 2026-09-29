"""/predict shows the served model's own numbers (from its metrics file via
/api/health/), and shows a refused genome as an error.

    python -m unittest discover -s frontend/tests

Needs no backend: /api/health/ and /api/predict/ are mocked.
"""
import json
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
os.environ.pop('PORT', None)
import app  # noqa: E402

HEALTH = {'status': 'running', 'models': {'kmer_resistance': {
    'trained': True, 'run_id': 'G_kmer_deploy', 'default_threshold': 0.43,
    'metrics': {'run_id': 'G_kmer_deploy', 'threshold': 0.43,
                'test': {'auc_roc': 0.9345, 'auc_roc_ci': [0.93, 0.94]},
                'data': {'train_rows': 287774, 'antibiotics': 111}}}}}


def get_page():
    with mock.patch.object(app, 'model_health', return_value=HEALTH):
        return app.app.test_client().get('/predict').get_data(as_text=True)


class PredictPage(unittest.TestCase):
    def test_strip_numbers_come_from_the_metrics(self):
        h = get_page()
        self.assertIn('>0.934<', h)                      # AUC
        self.assertIn('>287.8K<', h)                     # training rows
        self.assertIn('>111<', h)                        # antibiotics
        self.assertIn('>0.43<', h)                       # validated threshold
        for stale in ('>6,002<', '>62<', 'Decision trees (RF)', 'max 500K bp'):
            self.assertNotIn(stale, h)

    def test_refused_genome_shows_the_reason(self):
        refusal = ({'error': 'genome too short (5,000 bp): upload a complete assembly', 'sequence_length': 5000}, 400)
        with mock.patch.object(app, 'model_health', return_value=HEALTH), \
                mock.patch.object(app, 'backend_post', return_value=refusal):
            h = app.app.test_client().post('/predict', data={'antibiotic': 'ampicillin',
                                                             'fasta_text': '>x\nACGT'}).get_data(as_text=True)
        self.assertIn('upload a complete assembly', h)
        self.assertNotIn('Resistance Probability', h)

    def test_predict_waits_longer_than_other_pages(self):
        seen = {}

        def fake_post(endpoint, **kw):
            seen['timeout'] = kw.get('timeout')
            return {'error': 'x'}, 400
        with mock.patch.object(app, 'model_health', return_value=HEALTH), \
                mock.patch.object(app, 'backend_post', side_effect=fake_post):
            app.app.test_client().post('/predict', data={'antibiotic': 'ampicillin', 'fasta_text': '>x\nACGT'})
        self.assertEqual(seen['timeout'], app.PREDICT_TIMEOUT)
        self.assertGreaterEqual(app.PREDICT_TIMEOUT, 90)              # AMRFinderPlus alone takes up to 45 s

    def test_a_timeout_is_a_clear_message(self):
        import requests
        with mock.patch.object(app.requests, 'post', side_effect=requests.exceptions.ReadTimeout('read timed out')):
            data, status = app.backend_post('predict/', json_data={}, timeout=120)
        self.assertEqual(status, 504)
        self.assertIn('within 120 seconds', data['error'])
        self.assertNotIn('HTTPConnectionPool', data['error'])

    def test_page_says_it_is_working_for_as_long_as_it_waits(self):
        h = get_page()
        self.assertIn('data-loading-text="Analysing the genome…"', h)
        ms = int(h.split('data-loading-ms="')[1].split('"')[0])
        self.assertGreater(ms, app.PREDICT_TIMEOUT * 1000)          # the button is not given back mid-request
        self.assertIn('data-loading-note', h)

    def test_backend_timeout_stays_above_the_page_wait(self):
        dockerfile = os.path.join(HERE, '..', '..', 'backend', 'Dockerfile')
        with open(dockerfile, encoding='utf-8') as fh:
            gunicorn = int(fh.read().split('--timeout ')[1].split('"')[0])
        self.assertGreater(gunicorn, app.PREDICT_TIMEOUT)

    def test_export_without_gc_content(self):
        result = {'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.8, 'threshold': 0.43,
                  'sequence_length': 5_000_000, 'gc_content': None, 'model_used': 'LightGBM on 4-mers (G_kmer_deploy)'}
        with mock.patch.object(app, 'model_health', return_value=HEALTH):
            r = app.app.test_client().post('/export/predict.pdf', data={'result': json.dumps(result)})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'application/pdf')


if __name__ == '__main__':
    unittest.main()
