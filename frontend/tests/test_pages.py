"""Every page renders, with the backend up and with it down, and the small
routes no other test covers (T2.7: every page; export content types).

    python -m unittest discover -s frontend/tests

Needs no backend: backend calls are mocked with the committed report files.
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

MODELS = os.path.join(HERE, '..', '..', 'backend', 'trained_models')


def report(name):
    with open(os.path.join(MODELS, name), encoding='utf-8-sig') as fh:
        return json.load(fh)


MODEL_REPORT = dict(report('model_report.json'), live={'lgbm_loaded': True, 'kmer_loaded': True})
GENE_REPORT = report('gene_report.json')
DOWN = ({'error': 'Django backend not running. Start it with: python manage.py runserver'}, 503)


def fake_backend(endpoint, timeout=10):
    return {'models/': (MODEL_REPORT, 200), 'genes/': (GENE_REPORT, 200)}.get(endpoint, ({}, 200))


def client():
    return app.app.test_client()


PAGES = ['/', '/forecast', '/predict', '/timeline', '/train', '/datasets', '/about', '/library',
         '/models', '/compare', '/genes']


class EveryPage(unittest.TestCase):
    def setUp(self):
        app._vocab_cache.clear()

    def test_every_page_renders_with_the_backend_up(self):
        with mock.patch.object(app, 'model_health', return_value={}), \
                mock.patch.object(app, 'backend_get', side_effect=fake_backend):
            for path in PAGES:
                r = client().get(path)
                self.assertEqual(r.status_code, 200, path)
                self.assertIn('</html>', r.get_data(as_text=True), path)

    def test_every_page_renders_with_the_backend_down(self):
        with mock.patch.object(app, 'model_health', return_value={}), \
                mock.patch.object(app, 'backend_get', return_value=DOWN):
            for path in PAGES:
                self.assertEqual(client().get(path).status_code, 200, path)
            for path in ('/models', '/compare', '/genes'):            # these say why, instead of a blank page
                self.assertIn('Django backend not running', client().get(path).get_data(as_text=True), path)

    def test_report_pages_show_the_reports(self):
        with mock.patch.object(app, 'model_health', return_value={}), \
                mock.patch.object(app, 'backend_get', side_effect=fake_backend):
            compare = client().get('/compare').get_data(as_text=True)
            genes = client().get('/genes').get_data(as_text=True)
            home = client().get('/').get_data(as_text=True)
            library = client().get('/library').get_data(as_text=True)
        self.assertIn(MODEL_REPORT['shipped']['kmer']['name'], compare)
        self.assertIn(GENE_REPORT['top_genes'][0]['gene'] if isinstance(GENE_REPORT['top_genes'][0], dict)
                      else str(GENE_REPORT['top_genes'][0][0]), genes)
        self.assertIn('Dashboard', home)
        self.assertIn(app.LIB_VERSION, library)


class BatchPage(unittest.TestCase):
    def test_no_file_says_so(self):
        with mock.patch.object(app, 'model_health', return_value={}):
            r = client().post('/forecast/batch', data={})
        self.assertEqual(r.status_code, 200)
        self.assertIn('Choose a CSV file to upload.', r.get_data(as_text=True))

    def test_results_are_shown(self):
        import io
        batch = {'rows': [{'row': 1, 'antibiotic': 'ciprofloxacin', 'genus': 'Escherichia', 'species': 'coli',
                           'taxon_id': '562', 'mic_value': '4', 'mic_sign': '>=', 'prediction': 'Resistant',
                           'probability': 0.91, 'error': ''}],
                 'summary': {'rows': 1, 'predicted': 1, 'errors': 0, 'resistant': 1, 'susceptible': 0,
                             'by_antibiotic': [{'antibiotic': 'ciprofloxacin', 'n': 1, 'resistant': 1}]},
                 'threshold': 0.15, 'model_run': 'D3_forecaster_deploy_v7', 'calibrated': True}
        with mock.patch.object(app, 'model_health', return_value={}), \
                mock.patch.object(app, 'backend_post', return_value=(batch, 200)):
            r = client().post('/forecast/batch', data={'batch_file': (io.BytesIO(b'antibiotic\nciprofloxacin\n'), 'b.csv')},
                              content_type='multipart/form-data')
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('ciprofloxacin', h)
        self.assertIn('Resistant', h)


class SmallRoutes(unittest.TestCase):
    def setUp(self):
        app._vocab_cache.clear()

    def test_favicon(self):
        r = client().get('/favicon.ico')
        self.assertEqual(r.status_code, 200)
        self.assertGreater(len(r.data), 100)
        r.close()

    def test_antibiotics_static_list_without_a_backend(self):
        names = client().get('/api/antibiotics').get_json()
        self.assertIn('ciprofloxacin', names)
        self.assertEqual(names, app.ANTIBIOTICS)

    def test_antibiotics_for_a_model_are_canonical_and_unique(self):
        app._vocab_cache['data'] = {'lgbm': {'antibiotics': ['rifampin', 'rifampicin', 'ampicillin']}}
        names = client().get('/api/antibiotics?model=lgbm').get_json()
        self.assertEqual(names.count('rifampicin'), 1)
        self.assertNotIn('rifampin', names)

    def test_vocabulary_without_a_backend(self):
        self.assertEqual(client().get('/api/vocabulary').get_json(), {'lgbm': None, 'kmer': None})

    def test_organisms(self):
        self.assertEqual(client().get('/api/organisms').get_json(), app.BACTERIA_LIST)

    def test_reload_passes_the_token_and_clears_caches(self):
        app._vocab_cache['data'] = {'lgbm': None}
        seen = {}

        def fake_post(endpoint, **kw):
            seen.update(endpoint=endpoint, headers=kw.get('headers'))
            return {'status': 'reloaded'}, 200
        with mock.patch.object(app, 'backend_post', side_effect=fake_post):
            r = client().post('/reload', headers={'X-Admin-Token': 'secret'})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(seen['endpoint'], 'reload/')
        self.assertEqual(seen['headers'], {'X-Admin-Token': 'secret'})
        self.assertNotIn('data', app._vocab_cache)

    def test_reload_refused_is_passed_on(self):
        with mock.patch.object(app, 'backend_post', return_value=({'error': 'Admin token missing or wrong.'}, 401)):
            self.assertEqual(client().post('/reload').status_code, 401)

    def test_gene_csv_passthrough(self):
        answer = mock.Mock(status_code=200, content=b'Genome ID,blaTEM-1\n562.1,1\n',
                           headers={'Content-Disposition': 'attachment; filename="gene_matrix.csv"'})
        with mock.patch.object(app.requests, 'get', return_value=answer):
            r = client().get('/genes/matrix.csv')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.mimetype, 'text/csv')
        self.assertIn('gene_matrix.csv', r.headers['Content-Disposition'])
        self.assertEqual(r.data, answer.content)

    def test_gene_csv_without_a_backend_is_a_503(self):
        self.assertEqual(client().get('/genes/info.csv').status_code, 503)

    def test_gene_lookup_passthrough(self):
        answer = ({'genome_id': '562.1', 'searched': True, 'genes': []}, 200)
        with mock.patch.object(app, 'backend_get', return_value=answer) as get:
            r = client().get('/api/genes/562.1')
        self.assertEqual(r.get_json()['genome_id'], '562.1')
        get.assert_called_once_with('genes/562.1/')


class ExportTypes(unittest.TestCase):
    """Each download comes back with the right Content-Type and a file name."""
    RESULTS = {
        'forecast': {'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.9, 'confidence': 90.0,
                     'threshold': 0.15, 'drug_class': 'fluoroquinolone', 'model_used': 'LightGBM (trained)'},
        'predict': {'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.8, 'confidence': 80.0,
                    'threshold': 0.43, 'sequence_length': 5_000_000, 'gc_content': 50.6, 'model_used': 'LightGBM on 4-mers'},
        'timeline': {'antibiotic': 'ciprofloxacin', 'antibiotic_class': 'fluoroquinolone', 'n_weeks': 2, 'failure_week': None,
                     'final_resistant_percent': 12.0, 'sequence_length': 1000, 'gc_content': 50.0, 'summary': 's', 'seed': 42,
                     'timeline': [{'week': w, 'susceptible_fraction': 90.0, 'intermediate_fraction': 5.0,
                                   'resistant_fraction': 5.0, 'cumulative_mutations': 0, 'mic_fold_change': 1.0,
                                   'treatment_effective': True} for w in range(3)]},
        'batch': {'rows': [{'row': 1, 'antibiotic': 'ciprofloxacin', 'prediction': 'Resistant', 'probability': 0.9,
                            'error': ''}]},
    }

    def export(self, page, fmt):
        with mock.patch.object(app, 'model_health', return_value={}):
            return client().post(f'/export/{page}.{fmt}', data={'result': json.dumps(self.RESULTS[page])})

    def test_csv_downloads(self):
        for page in ('forecast', 'predict', 'timeline', 'batch'):
            r = self.export(page, 'csv')
            self.assertEqual(r.status_code, 200, page)
            self.assertEqual(r.mimetype, 'text/csv', page)
            self.assertRegex(r.headers['Content-Disposition'], rf'attachment; filename="amr-{page}-\d{{8}}-\d{{4}}\.csv"')

    def test_pdf_downloads(self):
        for page in ('forecast', 'predict', 'timeline'):
            r = self.export(page, 'pdf')
            self.assertEqual(r.status_code, 200, page)
            self.assertEqual(r.mimetype, 'application/pdf', page)
            self.assertTrue(r.data.startswith(b'%PDF'), page)

    def test_batch_has_no_pdf(self):
        self.assertEqual(self.export('batch', 'pdf').status_code, 400)


if __name__ == '__main__':
    unittest.main()
