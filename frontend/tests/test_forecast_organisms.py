"""/forecast's genus -> species -> taxon ID dropdowns and MIC suggestions.

    python -m unittest discover -s frontend/tests

Needs no backend: the page is rendered, and the MIC route is checked with the
backend unreachable and with a mocked answer.
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


def page(form=None):
    with mock.patch.object(app, 'model_health', return_value={}):
        client = app.app.test_client()
        if form is None:
            return client.get('/forecast').get_data(as_text=True)
        with mock.patch.object(app, 'backend_post', return_value=({'error': 'x'}, 400)):
            return client.post('/forecast', data=form).get_data(as_text=True)


class ForecastOrganisms(unittest.TestCase):
    def test_genus_species_taxon_are_dropdowns(self):
        h = page()
        self.assertIn('<select name="genus" id="genusSelect"', h)
        self.assertIn('<select name="species" id="speciesSelect"', h)
        self.assertIn('<select name="taxon_id" id="taxonSelect"', h)
        self.assertIn('list="micList"', h)
        self.assertNotIn('id="genusInput"', h)                           # the old free-text fields are gone
        # order on the form: antibiotic, genus, species, taxon ID, MIC
        order = [h.index(s) for s in ('name="antibiotic"', 'id="genusSelect"', 'id="speciesSelect"',
                                      'id="taxonSelect"', 'id="micInput"')]
        self.assertEqual(order, sorted(order))

    def test_choices_are_kept_after_a_submit(self):
        h = page({'antibiotic': 'ciprofloxacin', 'genus': 'Escherichia', 'species': 'coli', 'taxon_id': '562'})
        self.assertIn('data-selected="Escherichia"', h)
        self.assertIn('data-selected="coli"', h)
        self.assertIn('data-selected="562"', h)

    def test_mic_route_without_a_backend(self):
        r = app.app.test_client().get('/api/mic-values?antibiotic=ciprofloxacin')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {'values': [], 'level': None})

    def test_mic_route_passes_the_choice_on(self):
        answer = mock.Mock(status_code=200)
        answer.json.return_value = {'values': [0.5, 1.0], 'level': 'species'}
        with mock.patch.object(app.requests, 'get', return_value=answer) as get:
            r = app.app.test_client().get('/api/mic-values?antibiotic=ciprofloxacin&genus=Escherichia&species=coli')
        self.assertEqual(r.get_json()['level'], 'species')
        self.assertEqual(get.call_args.kwargs['params'],
                         {'antibiotic': 'ciprofloxacin', 'genus': 'Escherichia', 'species': 'coli'})


if __name__ == '__main__':
    unittest.main()
