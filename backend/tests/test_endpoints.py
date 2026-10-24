"""The API endpoints no other test file covers (T2.7: every endpoint):
/api/antibiotics/, /api/models/, /api/genes/, the two gene CSV downloads and
/api/genes/<id>/.

    python -m unittest discover -s backend/tests
"""
import csv
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.conf import settings  # noqa: E402
from django.test import Client, override_settings  # noqa: E402

HITS = os.path.join(str(settings.TRAINED_MODELS_DIR), 'gene_hits.json')


def get(path):
    return Client().get(path)


class Antibiotics(unittest.TestCase):
    def test_list_is_sorted_canonical_names(self):
        r = get('/api/antibiotics/')
        self.assertEqual(r.status_code, 200)
        names = r.json()['antibiotics']
        self.assertGreater(len(names), 40)
        self.assertEqual(names, sorted(names))
        self.assertEqual(len(names), len(set(names)))
        self.assertIn('ciprofloxacin', names)


class ModelReport(unittest.TestCase):
    def test_report_with_live_status(self):
        r = get('/api/models/')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        for key in ('runs', 'best_run', 'split', 'shipped', 'genome_runs'):
            self.assertIn(key, d)
        self.assertIn(d['best_run'], {run['id'] for run in d['runs']})
        self.assertEqual(set(d['live']), {'lgbm_loaded', 'kmer_loaded'})   # added by the view, not the file

    def test_missing_report_is_a_404_with_the_fix(self):
        with tempfile.TemporaryDirectory() as empty, override_settings(TRAINED_MODELS_DIR=empty):
            r = get('/api/models/')
        self.assertEqual(r.status_code, 404)
        self.assertIn('export_report.py', r.json()['error'])


class GeneReport(unittest.TestCase):
    def test_report(self):
        r = get('/api/genes/')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        for key in ('summary', 'matrix', 'top_genes', 'classes'):
            self.assertIn(key, d)

    def test_missing_report_is_a_404_with_the_fix(self):
        with tempfile.TemporaryDirectory() as empty, override_settings(TRAINED_MODELS_DIR=empty):
            r = get('/api/genes/')
        self.assertEqual(r.status_code, 404)
        self.assertIn('export_gene_report.py', r.json()['error'])


class GeneDownloads(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(HITS, encoding='utf-8') as fh:
            cls.hits = json.load(fh)

    def csv_rows(self, path, filename):
        r = get(path)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r['Content-Type'].startswith('text/csv'))
        self.assertIn(f'filename="{filename}"', r['Content-Disposition'])
        return list(csv.reader(io.StringIO(r.content.decode('utf-8'))))

    def test_matrix_is_one_row_per_genome_one_column_per_gene(self):
        rows = self.csv_rows('/api/genes/matrix.csv', 'gene_matrix.csv')
        header, body = rows[0], rows[1:]
        self.assertEqual(header[0], 'Genome ID')
        self.assertEqual(len(header) - 1, len(self.hits['symbols']))
        self.assertEqual(len(body), len(self.hits['genomes']))
        gid = next(iter(self.hits['genomes']))
        row = next(r for r in body if r[0] == gid)
        expected = {h[0] for h in self.hits['genomes'][gid]['hits']}
        self.assertEqual({header[i] for i, v in enumerate(row) if i and v == '1'}, expected)
        self.assertTrue(all(v in ('0', '1') for v in row[1:]))

    def test_info_names_every_column(self):
        rows = self.csv_rows('/api/genes/info.csv', 'gene_info.csv')
        self.assertEqual(rows[0], ['symbol', 'type', 'class', 'subclass', 'genomes', 'name'])
        self.assertEqual({r[0] for r in rows[1:]}, set(self.hits['symbols']))
        self.assertTrue(all(int(r[4]) >= 0 for r in rows[1:]))


class GeneLookup(unittest.TestCase):
    def test_searched_genome_lists_its_genes(self):
        with open(HITS, encoding='utf-8') as fh:
            hits = json.load(fh)
        gid, entry = next((g, e) for g, e in hits['genomes'].items() if e['hits'])
        d = get(f'/api/genes/{gid}/').json()
        self.assertTrue(d['searched'])
        self.assertEqual(len(d['genes']), len(entry['hits']))
        self.assertEqual(set(d['genes'][0]), {'gene', 'name', 'type', 'class', 'subclass', 'identity', 'coverage', 'method'})

    def test_unknown_genome_is_not_searched_not_an_error(self):
        r = get('/api/genes/999999999.9/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {'genome_id': '999999999.9', 'searched': False, 'genes': []})


if __name__ == '__main__':
    unittest.main()
