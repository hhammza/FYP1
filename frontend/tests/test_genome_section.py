"""Section 5 'Genome models' on /models (progress/formats/README.md §6).

    python -m unittest discover -s frontend/tests

Needs no backend: the /api/models/ report is mocked with the committed
backend/trained_models/model_report.json.
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

with open(os.path.join(HERE, '..', '..', 'backend', 'trained_models', 'model_report.json'), encoding='utf-8-sig') as fh:
    REPORT = json.load(fh)
REPORT['live'] = {'lgbm_loaded': True, 'kmer_loaded': True}


def models_page(report):
    with mock.patch.object(app, 'backend_get', return_value=(report, 200)):
        r = app.app.test_client().get('/models')
    return r.status_code, r.get_data(as_text=True)


def section(h):
    """Section 5 as shown (the report JSON embedded further down holds every run)."""
    return h[h.index('id="genome"'):h.index('Updating this page')]


def run(id_, version, auc, n=1000, split='grouped'):
    return {'id': id_, 'description': 'd', 'clean_version': version, 'model': 'lightgbm', 'features': 'genes',
            'split': split, 'plasmids_excluded': True, 'auc_roc': auc, 'auc_roc_lab': auc,
            'auc_roc_lab_ci': [auc - 0.01, auc + 0.01], 'n_lab': n, 'lab_genomes': 10}


class GenomeSection(unittest.TestCase):
    def test_hidden_without_genome_runs(self):
        status, h = models_page({k: v for k, v in REPORT.items() if k != 'genome_runs'})
        self.assertEqual(status, 200)
        self.assertNotIn('id="genome"', h)

    def test_shows_only_the_newest_cleaning_version(self):
        runs = [run('OLD_v5', 'v5', 0.9), run('NEW_a_v6', 'v6', 0.95, n=40553), run('NEW_b_v6', 'v6', 0.8)]
        _, h = models_page(dict(REPORT, genome_runs=runs))
        s = section(h)
        self.assertIn('NEW_a_v6', s)
        self.assertIn('NEW_b_v6', s)
        self.assertNotIn('OLD_v5', s)
        self.assertIn('40,553', s)                                        # the lab row count is shown
        self.assertIn('cleaning v6', s)

    def test_runs_without_a_lab_score_are_left_out(self):
        runs = [run('A_v6', 'v6', 0.9), dict(run('NOLAB_v6', 'v6', 0.9), auc_roc_lab=None)]
        _, h = models_page(dict(REPORT, genome_runs=runs))
        self.assertNotIn('NOLAB_v6', section(h))

    def test_served_run_is_named(self):
        served = REPORT['shipped']['kmer']['run_id']
        _, h = models_page(REPORT)
        self.assertIn(f'Served on <a href="/predict">/predict</a>: <code>{served}</code>', h)

    def test_real_report_renders_and_stays_out_of_the_tabular_runs(self):
        status, h = models_page(REPORT)
        self.assertEqual(status, 200)
        self.assertIn('Genome models, scored on lab results', h)
        self.assertIn('id="genomeChart"', h)
        tabular = re.search(r'id="experiments".*?id="best"', h, re.S).group(0)
        self.assertNotIn('B6L_genes_v6', tabular)


if __name__ == '__main__':
    unittest.main()
