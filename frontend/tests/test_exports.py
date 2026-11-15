"""CSV and PDF downloads (frontend/exports.py) and the export route (T2.2).

    python -m unittest discover -s frontend/tests

Needs no backend: with none running, the model details read "not measured".
"""
import base64
import csv
import io
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
import app  # noqa: E402
import exports  # noqa: E402

MODEL = {'auc_ci': '0.804 [0.800–0.808]', 'algorithm': 'LightGBM', 'run_id': 'D3', 'threshold': 0.23,
         'threshold_rule': 'VME <= 10%', 'split': 'genome-grouped'}
FORECAST = {'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.98, 'confidence': 98.0,
            'threshold': 0.23, 'drug_class': 'fluoroquinolone', 'model_used': 'LightGBM (trained)',
            'comparison_chart': [{'antibiotic': 'ampicillin', 'resistance_probability': 28.8}]}
TIMELINE = {'organism_source': 'chosen', 'ml_forecast': {
    'model_run': 'TL_timeline_ml', 'organism': 'Salmonella', 'antibiotic': 'ciprofloxacin',
    'history': [{'year': 2020, 'resistant_pct': 10.0, 'n': 40}, {'year': 2021, 'resistant_pct': 12.5, 'n': 55}],
    'forecast': [{'year': 2022, 'resistant_pct': 13.0, 'lo': 0.0, 'hi': 38.2},
                 {'year': 2023, 'resistant_pct': 13.4, 'lo': 0.0, 'hi': 49.1}],
    'label': 'ML model trained on BV-BRC laboratory results'}}
STATUS = {'trained': True, 'run_id': 'TL_timeline_ml', 'algorithm': 'LightGBM regression',
          'metrics': {'test_mae_pp': {'model': [13.98, [11.84, 16.33]], 'last value': [14.33, [12.16, 16.73]]},
                      'interval_abs_error_pp': {'q80': 25.24}}}
TL_MODEL = exports.timeline_summary(STATUS)
SIM = {'antibiotic': 'ciprofloxacin', 'antibiotic_class': 'fluoroquinolone', 'n_weeks': 2, 'failure_week': None,
       'final_resistant_percent': 12.34, 'sequence_length': 1000, 'gc_content': 50.0, 'summary': 's', 'seed': 42,
       'timeline': [{'week': w, 'susceptible_fraction': 90.0, 'intermediate_fraction': 5.0, 'resistant_fraction': 5.0,
                     'cumulative_mutations': w, 'mic_fold_change': 1.0, 'treatment_effective': True} for w in (0, 1, 2)]}


def rows(text):
    return list(csv.reader(io.StringIO(text)))


class Csv(unittest.TestCase):
    def test_forecast_is_one_row_with_the_model_auc(self):
        r = rows(exports.build_csv('forecast', FORECAST, {'genus': 'Escherichia'}, MODEL))
        self.assertEqual(len(r), 2)
        self.assertIn('0.804 [0.800–0.808]', r[1])

    def test_timeline_is_one_row_per_year_with_the_models_error(self):
        r = rows(exports.build_csv('timeline', TIMELINE, {}, TL_MODEL))
        self.assertEqual([(x[0], x[1]) for x in r[1:]],
                         [('2020', 'observed'), ('2021', 'observed'), ('2022', 'forecast'), ('2023', 'forecast')])
        self.assertTrue(all(x[9] == 'TL_timeline_ml' for x in r[1:]))
        self.assertTrue(r[1][10].startswith('13.98 pp (95% CI 11.84 to 16.33)'))
        self.assertNotIn('Simulation', '\n'.join(','.join(x) for x in r))

    def test_simulation_is_one_row_per_week_labelled_as_a_simulation(self):
        r = rows(exports.build_csv('simulation', SIM, {}, MODEL))
        self.assertEqual([x[0] for x in r[1:]], ['0', '1', '2'])
        self.assertTrue(all(x[-1] == exports.SIMULATION for x in r[1:]))

    def test_timeline_summary_without_metrics_says_not_measured(self):
        self.assertEqual(exports.timeline_summary(None)['mae'], 'not measured')

    def test_formulas_are_neutralised_but_numbers_are_not(self):
        batch = {'rows': [{'row': 1, 'antibiotic': '=cmd()', 'mic_value': '-2', 'genus': '+x', 'species': '@y'}]}
        r = rows(exports.build_csv('batch', batch, {}, MODEL))[1]
        self.assertEqual(r[1], "'=cmd()")
        self.assertEqual(r[2], "'+x")
        self.assertEqual(r[3], "'@y")
        self.assertEqual(r[5], '-2')


class Pdf(unittest.TestCase):
    def test_pdfs_build(self):
        for page, result, model in (('forecast', FORECAST, MODEL), ('timeline', TIMELINE, TL_MODEL)):
            self.assertTrue(exports.build_pdf(page, result, {}, model).startswith(b'%PDF'), page)

    def test_only_real_pngs_are_embedded(self):
        from PIL import Image
        buf = io.BytesIO()
        Image.new('RGB', (4, 4)).save(buf, 'PNG')
        good = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()
        self.assertIsNotNone(exports.decode_chart(good))
        self.assertIsNone(exports.decode_chart('data:image/png;base64,bm90IGEgcG5n'))
        self.assertIsNone(exports.decode_chart('data:text/html;base64,PGI+'))
        self.assertIsNone(exports.decode_chart(''))


class Route(unittest.TestCase):
    def setUp(self):
        self.c = app.app.test_client()

    def post(self, path, result):
        return self.c.post(path, data={'result': json.dumps(result), 'inputs': '{}'})

    def test_content_types(self):
        r = self.post('/export/forecast.csv', FORECAST)
        self.assertEqual((r.status_code, r.mimetype), (200, 'text/csv'))
        self.assertIn('attachment', r.headers['Content-Disposition'])
        r = self.post('/export/timeline.pdf', TIMELINE)
        self.assertEqual((r.status_code, r.mimetype), (200, 'application/pdf'))
        r = self.post('/export/simulation.csv', SIM)
        self.assertEqual((r.status_code, r.mimetype), (200, 'text/csv'))
        self.assertIn('Simulation, not a trained model', r.get_data(as_text=True))
        r = self.post('/export/simulation.pdf', SIM)
        self.assertEqual((r.status_code, r.mimetype), (200, 'application/pdf'))

    def test_model_numbers_come_from_the_server_not_the_page(self):
        # the backend is down, so the page cannot smuggle in an AUC
        text = self.post('/export/forecast.csv', dict(FORECAST, model_auc='0.99')).get_data(as_text=True)
        self.assertIn('not measured', text)
        self.assertNotIn('0.99', text.split('\n')[1].split(',')[-2])

    def test_bad_requests(self):
        self.assertEqual(self.c.post('/export/forecast.csv', data={}).status_code, 400)
        self.assertEqual(self.post('/export/batch.pdf', {'rows': []}).status_code, 400)
        self.assertEqual(self.c.post('/export/other.csv', data={'result': '{}'}).status_code, 404)

    def test_template_download(self):
        r = self.c.get('/forecast/template.csv')
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.get_data(as_text=True).startswith('antibiotic,'))


if __name__ == '__main__':
    unittest.main()
