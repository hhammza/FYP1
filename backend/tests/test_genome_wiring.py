"""/api/predict/ with the complete-genome model (model_registry.predict_model).

    python -m unittest discover -s backend/tests

A tiny LightGBM model is trained into a temp folder in the layout
experiments/promote.py --genome writes (genome/model.txt, feature_meta.json,
genome_metrics.json), so these do not depend on the promoted model.
"""
import json
import os
import random
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from api import model_registry  # noqa: E402
from ml_models.genome_predictor import GenomeModelPredictor, kmer_names  # noqa: E402
from ml_models.resistance_predictor import KmerResistancePredictor  # noqa: E402

ANTIBIOTICS = ['ampicillin', 'ciprofloxacin', 'gentamicin']
GENERA = ['Escherichia', 'Klebsiella']


def fasta(n_bp, seed=1):
    rng = random.Random(seed)
    seq = ''.join(rng.choice('ACGT') for _ in range(n_bp))
    return '>contig_1\n' + '\n'.join(seq[i:i + 80] for i in range(0, n_bp, 80)) + '\n'


def write_model(model_dir, extra_features=()):
    """A LightGBM genome model on 4-mers + GC + length + antibiotic + genus."""
    import lightgbm as lgb
    features = kmer_names(4) + ['genome_gc', 'genome_length_mb', 'Antibiotic', 'genus'] + list(extra_features)
    rng = np.random.default_rng(0)
    n = 200
    X = pd.DataFrame(rng.random((n, 258)), columns=features[:258])
    X['Antibiotic'] = pd.Categorical(rng.choice(ANTIBIOTICS, n), categories=ANTIBIOTICS)
    X['genus'] = pd.Categorical(rng.choice(GENERA, n), categories=GENERA)
    for f in extra_features:
        X[f] = rng.integers(0, 2, n)
    y = (X['genome_gc'] > 0.5).astype(int)
    booster = lgb.train({'objective': 'binary', 'verbose': -1, 'min_data_in_leaf': 5},
                        lgb.Dataset(X[features], y), num_boost_round=5)
    target = os.path.join(model_dir, 'genome')
    os.makedirs(target)
    booster.save_model(os.path.join(target, 'model.txt'))
    with open(os.path.join(target, 'feature_meta.json'), 'w', encoding='utf-8') as fh:
        json.dump({'model_type': 'lightgbm', 'run_id': 'TEST_kmer4_lgbm', 'kmer_k': 4, 'threshold': 0.4,
                   'features': features,
                   'category_levels': {'Antibiotic': ANTIBIOTICS, 'genus': GENERA}}, fh)
    with open(os.path.join(target, 'genome_metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump({'schema': 1, 'model': 'genome_kmer_lightgbm', 'run_id': 'TEST_kmer4_lgbm',
                   'threshold': 0.4, 'test': {'auc_roc': 0.9, 'auc_roc_ci': [0.88, 0.92]}}, fh)


def predict(text, antibiotic='ciprofloxacin', **extra):
    return Client().post('/api/predict/', data=json.dumps(dict(fasta_text=text, antibiotic=antibiotic, **extra)),
                         content_type='application/json')


class GenomeWiring(unittest.TestCase):
    def setUp(self):
        cache.clear()
        self.saved = model_registry._kmer
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        model_registry._kmer = self.saved
        shutil.rmtree(self.dir, ignore_errors=True)

    def serve(self, **kw):
        write_model(self.dir, **kw)
        model_registry._kmer = model_registry.predict_model(self.dir)
        return model_registry._kmer

    def test_genome_model_is_chosen_once_promoted(self):
        self.assertIsInstance(self.serve(), GenomeModelPredictor)
        d = predict(fasta(150_000)).json()
        self.assertIn('TEST_kmer4_lgbm', d['model_used'])
        self.assertEqual(d['threshold'], 0.4)                          # the promoted model's own threshold
        self.assertEqual(d['sequence_length'], 150_000)
        self.assertEqual(len(d['top_kmers']), 10)                      # same fields as the old model
        self.assertIsNotNone(d['gc_content'])

    def test_threshold_from_the_request_is_used(self):
        self.serve()
        self.assertEqual(predict(fasta(150_000), threshold=0.7).json()['threshold'], 0.7)

    def test_partial_genome_is_a_400_with_the_reason(self):
        self.serve()
        r = predict(fasta(50_000))
        self.assertEqual(r.status_code, 400)
        self.assertIn('complete assembly', r.json()['error'])

    def test_health_and_vocabulary_describe_the_served_model(self):
        self.serve()
        k = Client().get('/api/health/').json()['models']['kmer_resistance']
        self.assertEqual(k['run_id'], 'TEST_kmer4_lgbm')
        self.assertEqual(k['metrics']['test']['auc_roc'], 0.9)
        self.assertEqual(Client().get('/api/vocabulary/').json()['kmer']['antibiotics'], sorted(ANTIBIOTICS))

    def test_gene_model_is_not_served_until_amrfinder_runs(self):
        model = self.serve(extra_features=['g_blaTEM-1'])
        self.assertIsInstance(model, KmerResistancePredictor)

    def test_empty_folder_means_the_old_kmer_model(self):
        self.assertIsInstance(model_registry.predict_model(self.dir), KmerResistancePredictor)

    def test_reload_picks_up_a_model_promoted_while_running(self):
        from django.conf import settings
        if not os.path.exists(os.path.join(str(settings.TRAINED_MODELS_DIR), 'genome', 'model.txt')):
            self.skipTest('no promoted genome model in trained_models/')
        model_registry._kmer = KmerResistancePredictor(self.dir)       # as if started before the promotion
        r = Client().post('/api/reload/', HTTP_X_ADMIN_TOKEN=django_setup.TOKEN)
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(model_registry._kmer, GenomeModelPredictor)
        self.assertTrue(r.json()['models']['kmer']['run_id'])


if __name__ == '__main__':
    unittest.main()
