"""The resistance-genes panel on /predict (templates/_genes_panel.html, Week 3).

    python -m unittest discover -s frontend/tests

Needs no backend: the /predict response is mocked, in each of the three
states the format defines (progress/formats/README.md §2).
"""
import json
import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
os.environ.pop('PORT', None)
import app  # noqa: E402

with open(os.path.join(HERE, '..', '..', 'progress', 'formats', 'genome_response.sample.json'),
          encoding='utf-8') as fh:
    SAMPLE = json.load(fh)
SAMPLE.pop('_comment', None)


def page_text(result):
    with mock.patch.object(app, 'backend_post', return_value=(result, 200)):
        h = app.app.test_client().post('/predict', data={'antibiotic': 'ciprofloxacin',
                                                         'fasta_text': 'ACGT' * 50}).get_data(as_text=True)
    return h, re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>', '', h, flags=re.S)))


class GenesPanel(unittest.TestCase):
    def test_genes_listed_linked_first(self):
        h, t = page_text(SAMPLE)
        self.assertIn('Resistance genes found 3', t)
        self.assertIn('which supports the Resistant call', t)
        self.assertEqual(re.findall(r'gyrA_S83L|parC_S80I|blaCTX-M-15', h)[:3],
                         ['gyrA_S83L', 'parC_S80I', 'blaCTX-M-15'])
        self.assertEqual(h.count('gene-chip-linked'), 2)

    def test_susceptible_with_linked_genes_warns(self):
        _, t = page_text(dict(SAMPLE, prediction='Susceptible'))
        self.assertIn('Treat this call with care', t)

    def test_searched_and_nothing_found(self):
        _, t = page_text(dict(SAMPLE, genes_found=[]))
        self.assertIn('no known resistance gene or mutation was found', t)

    def test_not_searched_shows_one_line_and_no_panel(self):
        result = dict(SAMPLE)
        result.pop('genes_found')
        _, t = page_text(result)
        self.assertNotIn('Resistance genes found', t)
        self.assertIn('Not searched', t)

    def test_gene_names_are_escaped(self):
        h, _ = page_text(dict(SAMPLE, genes_found=[{'gene': '<b>x</b>', 'drug_class': 'y', 'relevant': True}]))
        self.assertNotIn('<b>x</b>', h)

    def test_no_kmers_hides_the_kmer_cards(self):
        result = dict(SAMPLE, model_used='LightGBM on genes (trained)')
        result.pop('top_kmers')
        _, t = page_text(result)
        self.assertNotIn('4-mer Frequency Spectrum', t)
        self.assertNotIn('K-mer Genome Analysis', t)

    def test_sample_preview_is_local_only(self):
        c = app.app.test_client()
        self.assertEqual(c.get('/predict/sample').status_code, 200)
        with mock.patch.dict(os.environ, {'PORT': '8080'}):
            self.assertEqual(c.get('/predict/sample').status_code, 404)


if __name__ == '__main__':
    unittest.main()
