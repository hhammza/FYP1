"""/timeline on the Flask site, two tabs: the timeline ML model (POST
/api/timeline/, format §8; the default), where the organism is chosen or
identified by the backend from an uploaded genome, and the what-if
simulation (POST /api/timeline/simulate/, format §4; not a trained model).

    python -m unittest discover -s frontend/tests

Needs no backend: backend_post, the vocabulary and the health are mocked.
"""
import io
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
HEALTH = {'models': {'timeline_ml': {'trained': True, 'metrics': {
    'data': {'series': 467, 'lab_results': 534996, 'train_until': 2016},
    'test_mae_pp': {'model': [13.98, [11.84, 16.33]], 'last value': [14.33, [12.16, 16.73]],
                    'linear trend': [16.75, [14.32, 19.3]], 'historical mean': [17.25, [15.07, 19.67]]}}}}}
BLOCK = {'model_run': 'TL_timeline_ml', 'organism': 'Salmonella', 'antibiotic': 'ciprofloxacin',
         'history': [{'year': 2020, 'resistant_pct': 50.0, 'n': 4}, {'year': 2021, 'resistant_pct': 52.0, 'n': 30}],
         'forecast': [{'year': 2022, 'resistant_pct': 51.0, 'lo': 30.0, 'hi': 72.0},
                      {'year': 2023, 'resistant_pct': 49.5, 'lo': 20.0, 'hi': 79.0}],
         'metrics': {'model': {'mae_pct': 13.98, 'ci': [11.84, 16.33]},
                     'last_value': {'mae_pct': 14.33, 'ci': [12.16, 16.73]}},
         'label': 'ML model trained on BV-BRC laboratory results'}


class Timeline(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        self.patches = [mock.patch.object(app, 'model_vocabulary', return_value=VOCAB),
                        mock.patch.object(app, 'model_health', return_value=HEALTH)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def post(self, **form):
        return self.client.post('/timeline', data=form, content_type='multipart/form-data').get_data(as_text=True)

    def test_page_opens_on_the_ml_model(self):
        html = self.client.get('/timeline').get_data(as_text=True)
        self.assertIn('"ciprofloxacin": ["Salmonella", "Escherichia"]', html)
        self.assertIn('Forecast a Resistance Trend', html)
        self.assertIn('534,996', html)
        self.assertIn('off by 14.0 pp on average, against 14.3 pp for', html)
        # the ML tab is shown, the what-if tab is there but hidden
        self.assertRegex(html, r'id="trendPane" class=""')
        self.assertRegex(html, r'id="simulationPane" class="d-none"')
        self.assertIn('Simulation, not a trained model.', html)
        self.assertNotIn('rlPanel', html)

    def test_chosen_organism_is_posted_and_shown(self):
        with mock.patch.object(app, 'backend_post',
                               return_value=({'ml_forecast': BLOCK, 'organism_source': 'chosen'}, 200)) as post:
            html = self.post(antibiotic='ciprofloxacin', organism_from='choose', genus='Salmonella', years_ahead='2')
        post.assert_called_once_with('timeline/', json_data={
            'antibiotic': 'ciprofloxacin', 'years_ahead': '2', 'genus': 'Salmonella'})
        self.assertIn('id="mlForecast"', html)
        self.assertIn('id="trend-data"', html)
        self.assertIn('id="mlForecastChart"', html)
        self.assertIn('Forecast for 2023 (80%: 20.0 to 79.0)', html)
        self.assertIn('Hollow points are years with fewer than 30 lab', html)
        self.assertIn('off by 13.98 percentage points on average, against 14.33 for last year’s value.', html)
        self.assertIn('data-export-page="timeline"', html)
        self.assertNotIn('id="genusFromGenome"', html)

    def test_pasted_genome_is_sent_without_a_genus(self):
        with mock.patch.object(app, 'backend_post',
                               return_value=({'ml_forecast': BLOCK, 'organism_source': 'genome'}, 200)) as post:
            html = self.post(antibiotic='ciprofloxacin', organism_from='genome', genus='Escherichia',
                             fasta_text='>g\nACGT')
        post.assert_called_once_with('timeline/', json_data={
            'antibiotic': 'ciprofloxacin', 'years_ahead': '5', 'fasta_text': '>g\nACGT'})
        self.assertIn('The uploaded genome was identified as <em>Salmonella</em>', html)

    def test_uploaded_genome_is_sent_as_a_file(self):
        with mock.patch.object(app, 'backend_post',
                               return_value=({'ml_forecast': BLOCK, 'organism_source': 'genome'}, 200)) as post:
            self.post(antibiotic='ciprofloxacin', organism_from='genome', years_ahead='3',
                      fasta_file=(io.BytesIO(b'>g\nACGT'), 'g.fasta'))
        args, kwargs = post.call_args
        self.assertEqual(args, ('timeline/',))
        self.assertEqual(kwargs['data'], {'antibiotic': 'ciprofloxacin', 'years_ahead': '3'})
        self.assertIn('fasta_file', kwargs['files'])

    def test_genome_mode_without_a_genome_asks_for_one(self):
        with mock.patch.object(app, 'backend_post') as post:
            html = self.post(antibiotic='ciprofloxacin', organism_from='genome')
        post.assert_not_called()
        self.assertIn('Upload a FASTA file or paste a sequence, or choose the organism instead.', html)

    def test_backend_refusal_is_shown(self):
        refusal = ({'error': 'The organism could not be identified from this genome'}, 422)
        with mock.patch.object(app, 'backend_post', return_value=refusal):
            html = self.post(antibiotic='ciprofloxacin', organism_from='genome', fasta_text='>g\nACGT')
        self.assertIn('could not be identified', html)
        self.assertNotIn('id="mlForecast"', html)

    def test_simulation_posts_to_its_own_endpoint_and_is_labelled(self):
        sim = {'antibiotic': 'ciprofloxacin', 'antibiotic_class': 'fluoroquinolone', 'n_weeks': 2, 'failure_week': None,
               'final_resistant_percent': 12.0, 'sequence_length': 1000, 'gc_content': 50.0, 'summary': 's',
               'model_used': 'Biological Simulation', 'mutation_hotspots': [], 'resistance_genes': [],
               'timeline': [{'week': w, 'susceptible_fraction': 90.0, 'intermediate_fraction': 5.0,
                             'resistant_fraction': 5.0, 'cumulative_mutations': w, 'mic_fold_change': 1.0,
                             'treatment_effective': True} for w in (0, 1, 2)]}
        with mock.patch.object(app, 'backend_post', return_value=(sim, 200)) as post:
            html = self.post(mode='simulation', antibiotic='ciprofloxacin', n_weeks='2', fasta_text='>g\nACGT')
        post.assert_called_once_with('timeline/simulate/', json_data={
            'antibiotic': 'ciprofloxacin', 'n_weeks': '2', 'fasta_text': '>g\nACGT'})
        self.assertRegex(html, r'id="simulationPane" class=""')
        self.assertIn('id="timelineChart"', html)
        self.assertIn('data-export-page="simulation"', html)
        self.assertIn('Every download is labelled "Simulation, not a trained model".', html)
        self.assertNotIn('id="mlForecast"', html)

    def test_simulation_without_a_genome_asks_for_one(self):
        with mock.patch.object(app, 'backend_post') as post:
            html = self.post(mode='simulation', antibiotic='ciprofloxacin', n_weeks='8')
        post.assert_not_called()
        self.assertIn('Upload a FASTA file or paste a sequence before generating a timeline.', html)

    def test_sample_route_opens_the_what_if_tab(self):
        html = self.client.get('/timeline/sample').get_data(as_text=True)
        self.assertIn('Sample response, not a real simulation.', html)
        self.assertRegex(html, r'id="simulationPane" class=""')


if __name__ == '__main__':
    unittest.main()
