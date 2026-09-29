"""/datasets after the switch to complete genomes: Dataset 2 is marked
superseded, and its numbers are the original model's, not the served one's.

    python -m unittest discover -s frontend/tests

Needs no backend: /api/health/ is mocked.
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

HEALTH = {'models': {'kmer_resistance': {'trained': True, 'metrics': {
    'test': {'auc_roc': 0.9345}, 'data': {'train_rows': 287774}}}}}


class DatasetsPage(unittest.TestCase):
    def setUp(self):
        with mock.patch.object(app, 'model_health', return_value=HEALTH):
            self.h = app.app.test_client().get('/datasets').get_data(as_text=True)

    def test_dataset_2_is_marked_superseded(self):
        self.assertIn('Superseded by <a href="#ds-assemblies">Dataset 3</a>, kept to reproduce the original K-mer model.',
                      self.h)

    def test_dataset_2_numbers_are_the_original_models(self):
        ds2 = self.h[self.h.index('id="ds-fasta"'):self.h.index('id="ds-assemblies"')]
        self.assertIn('6,002 genome–antibiotic pairs', ds2)
        self.assertNotIn('287,774', ds2)                 # the served model's rows belong to Dataset 3

    def test_predict_model_card_names_dataset_3(self):
        self.assertIn('K-mer LightGBM', self.h)
        self.assertIn('Dataset 3  Complete genomes', self.h)
        self.assertIn('287,774 genome–antibiotic pairs', self.h)


if __name__ == '__main__':
    unittest.main()
