"""/predict with the gene model's new fields (format §2, 2026-09-30):
`species_detected` shown as "Identified as ...", `warning` shown as a warning,
and both in the CSV and PDF.

    python -m unittest discover -s frontend/tests

Needs no backend: the result is rendered straight from the agreed sample.
"""
import copy
import csv
import io
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

with open(os.path.join(HERE, '..', '..', 'progress', 'formats', 'genome_response.sample.json'),
          encoding='utf-8-sig') as fh:
    SAMPLE = json.load(fh)
SAMPLE.pop('_comment', None)

# What the k-mer model sends when AMRFinderPlus failed on the upload
FALLBACK = {k: v for k, v in SAMPLE.items() if k not in ('genes_found', 'species_detected')}
FALLBACK.update(model_used='LightGBM on 4-mers (G_kmer_deploy)', model_run='G_kmer_deploy',
                warning='AMRFinderPlus timed out after 100 s; the k-mer model answered instead.')


def render(result):
    with app.app.test_request_context('/predict'), \
            mock.patch.object(app, 'model_health', return_value={}):
        return app.render_template('resistance_prediction.html', result=result, error=None,
                                   form_data={'antibiotic': result.get('antibiotic', ''), 'threshold': ''})


def export(fmt, result):
    with mock.patch.object(app, 'model_health', return_value={}):
        return app.app.test_client().post(f'/export/predict.{fmt}', data={'result': json.dumps(result)})


class GeneModelDisplay(unittest.TestCase):
    def test_species_is_shown(self):
        h = render(SAMPLE)
        self.assertIn('Identified as <em>Escherichia coli</em>', h)
        self.assertIn('Species (from the genome)', h)

    def test_genus_only_and_unknown_species(self):
        r = copy.deepcopy(SAMPLE)
        r['species_detected'].update(species=None)
        self.assertIn('Identified as <em>Escherichia</em> (species unclear)', render(r))
        r['species_detected'].update(genus=None)
        self.assertIn('Species not identified from the genome', render(r))

    def test_no_species_line_for_the_kmer_model(self):
        h = render(FALLBACK)
        self.assertNotIn('data-species', h)
        self.assertNotIn('Species (from the genome)', h)

    def test_warning_is_shown_and_explains_the_missing_genes(self):
        h = render(FALLBACK)
        self.assertIn('Resistance genes were not searched for this genome.', h)
        self.assertIn('AMRFinderPlus timed out after 100 s', h)
        self.assertIn('the gene search failed on this genome', h)
        self.assertNotIn('Resistance genes found', h)                  # no genes panel without genes_found
        self.assertNotIn('Resistance genes were not searched', render(SAMPLE))

    def test_gene_chip_tooltip_has_the_full_name(self):
        self.assertIn('title="class A extended-spectrum beta-lactamase CTX-M-15 (cephalosporin)"', render(SAMPLE))

    def test_csv_has_species_and_warning(self):
        rows = list(csv.DictReader(io.StringIO(export('csv', SAMPLE).get_data(as_text=True))))
        self.assertEqual(rows[0]['species_identified'], 'Escherichia coli')
        self.assertEqual(rows[0]['warning'], '')
        rows = list(csv.DictReader(io.StringIO(export('csv', FALLBACK).get_data(as_text=True))))
        self.assertEqual(rows[0]['species_identified'], '')
        self.assertIn('timed out', rows[0]['warning'])

    def test_pdf_builds_with_both(self):
        for result in (SAMPLE, FALLBACK):
            r = export('pdf', result)
            self.assertEqual(r.status_code, 200)
            self.assertEqual(r.mimetype, 'application/pdf')


if __name__ == '__main__':
    unittest.main()
