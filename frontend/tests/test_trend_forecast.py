"""The ML trend forecast on /timeline: the timeline ML model on its own
(POST /api/timeline/forecast/, format §8), beside the what-if simulation.

    python -m unittest discover -s frontend/tests

Needs no backend: backend_post and the vocabulary are mocked.
"""
import os
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
os.environ.pop('PORT', None)
import app  # noqa: E402

VOCAB = {'timeline': {'genera': {'ciprofloxacin': ['Salmonella', 'Escherichia']}}}
BLOCK = {'model_run': 'TL_timeline_ml', 'organism': 'Salmonella', 'antibiotic': 'ciprofloxacin',
         'history': [{'year': 2020, 'resistant_pct': 50.0, 'n': 40}, {'year': 2021, 'resistant_pct': 52.0, 'n': 30}],
         'forecast': [{'year': 2022, 'resistant_pct': 51.0, 'lo': 30.0, 'hi': 72.0},
                      {'year': 2023, 'resistant_pct': 49.5, 'lo': 20.0, 'hi': 79.0}],
         'metrics': {'model': {'mae_pct': 13.98, 'ci': [11.84, 16.33]},
                     'last_value': {'mae_pct': 14.33, 'ci': [12.16, 16.73]}},
         'label': 'ML model trained on BV-BRC laboratory results'}


class TrendForecast(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.patches = [mock.patch.object(app, 'model_vocabulary', return_value=VOCAB),
                        mock.patch.object(app, 'model_health', return_value={})]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_page_offers_the_ml_forecast_with_its_choices(self):
        html = self.client.get('/timeline').get_data(as_text=True)
        self.assertIn('ML Trend Forecast', html)
        self.assertIn('Trained ML model.', html)
        self.assertIn('"ciprofloxacin": ["Salmonella", "Escherichia"]', html)
        self.assertIn('What-if Simulation', html)

    def test_forecast_is_posted_and_shown(self):
        with mock.patch.object(app, 'backend_post', return_value=({'ml_forecast': BLOCK}, 200)) as post:
            html = self.client.post('/timeline', data={'mode': 'trend', 'antibiotic': 'ciprofloxacin',
                                                       'genus': 'Salmonella', 'years_ahead': '2'}).get_data(as_text=True)
        post.assert_called_once_with('timeline/forecast/', json_data={
            'antibiotic': 'ciprofloxacin', 'genus': 'Salmonella', 'years_ahead': '2'})
        self.assertIn('id="trendResult"', html)
        self.assertIn('id="trend-data"', html)
        self.assertIn('Forecast 2023: <span class="text-white">49.5%', html)
        self.assertIn('14.0 percentage points', html)
        self.assertNotIn('Generate Resistance Timeline', html)

    def test_backend_refusal_is_shown(self):
        refusal = ({'error': 'Notagenus has too little yearly lab history for ciprofloxacin to forecast'}, 404)
        with mock.patch.object(app, 'backend_post', return_value=refusal):
            html = self.client.post('/timeline', data={'mode': 'trend', 'antibiotic': 'ciprofloxacin',
                                                       'genus': 'Notagenus'}).get_data(as_text=True)
        self.assertIn('too little yearly lab history', html)
        self.assertNotIn('id="trendResult"', html)


if __name__ == '__main__':
    unittest.main()
