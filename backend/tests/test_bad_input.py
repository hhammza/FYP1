"""Bad input gets a 400 with a plain message, never a 500 with a Python error
(Hamza's code review, 2026-09-30).

    python -m unittest discover -s backend/tests
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402  (configures Django)

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

FASTA = '>x\n' + 'ACGT' * 50


def post(path, body, raw=False):
    data = body if raw else json.dumps(body)
    return Client().post(path, data=data, content_type='application/json')


class BadInput(unittest.TestCase):
    def setUp(self):
        cache.clear()                                    # rate limits start fresh

    def assert_400(self, r, words):
        self.assertEqual(r.status_code, 400, r.content)
        message = r.json()['error']
        self.assertIn(words, message)
        for python_text in ('NoneType', 'Traceback', 'could not convert', 'Expecting value', 'invalid literal'):
            self.assertNotIn(python_text, message)

    # ── the cases from the review ────────────────────────────────
    def test_forecast_malformed_json(self):
        self.assert_400(post('/api/forecast/', '{"antibiotic": ', raw=True), 'not valid JSON')

    def test_forecast_threshold_not_a_number(self):
        self.assert_400(post('/api/forecast/', {'antibiotic': 'ampicillin', 'threshold': 'abc'}),
                        'threshold must be a number between 0 and 1')

    def test_forecast_antibiotic_null(self):
        self.assert_400(post('/api/forecast/', {'antibiotic': None}), 'antibiotic is required')

    def test_timeline_n_weeks_not_a_number(self):
        self.assert_400(post('/api/timeline/', {'fasta_text': FASTA, 'antibiotic': 'ampicillin', 'n_weeks': 'x'}),
                        'n_weeks must be a whole number from 1 to 52')

    # ── more of the same kind ────────────────────────────────────
    def test_threshold_out_of_range(self):
        for value in (0, 1, 1.5, -0.2, 'nan', True):
            self.assert_400(post('/api/forecast/', {'antibiotic': 'ampicillin', 'threshold': value}),
                            'threshold must be a number between 0 and 1')

    def test_forecast_wrong_types(self):
        self.assert_400(post('/api/forecast/', {'antibiotic': 42}), 'antibiotic must be text')
        self.assert_400(post('/api/forecast/', {'antibiotic': 'ampicillin', 'mic_value': 'lots'}),
                        'mic_value must be a positive number')
        self.assert_400(post('/api/forecast/', {'antibiotic': 'ampicillin', 'taxon_id': '56.2'}),
                        'taxon_id must be a positive whole number')
        self.assert_400(post('/api/forecast/', {'antibiotic': 'ampicillin', 'mic_sign': '~'}), 'mic_sign must be')

    def test_body_must_be_an_object(self):
        self.assert_400(post('/api/forecast/', '[1, 2]', raw=True), 'must be a JSON object')

    def test_predict_bad_input(self):
        self.assert_400(post('/api/predict/', '{oops', raw=True), 'not valid JSON')
        self.assert_400(post('/api/predict/', {'fasta_text': FASTA, 'antibiotic': 'ampicillin', 'threshold': 'x'}),
                        'threshold must be a number')
        self.assert_400(post('/api/predict/', {'fasta_text': 123, 'antibiotic': 'ampicillin'}), 'fasta_text must be text')

    def test_timeline_weeks_out_of_range_or_fractional(self):
        for value in (0, 53, 2.5, 'inf'):
            self.assert_400(post('/api/timeline/', {'fasta_text': FASTA, 'antibiotic': 'ampicillin', 'n_weeks': value}),
                            'n_weeks must be a whole number from 1 to 52')

    def test_train_malformed_json(self):
        r = Client().post('/api/train/', data='{', content_type='application/json',
                          HTTP_X_ADMIN_TOKEN=django_setup.TOKEN)
        self.assert_400(r, 'not valid JSON')

    # ── good input still works ───────────────────────────────────
    def test_good_input_unchanged(self):
        r = post('/api/forecast/', {'antibiotic': 'ciprofloxacin', 'taxon_id': '562', 'mic_value': '4',
                                    'mic_sign': '>=', 'threshold': '0.3', 'genus': 'Escherichia'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['threshold'], 0.3)
        r = post('/api/timeline/', {'fasta_text': FASTA, 'antibiotic': 'ampicillin', 'n_weeks': '8'})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(len(r.json()['timeline']), 9)


if __name__ == '__main__':
    unittest.main()
