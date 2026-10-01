"""/api/predict/ with the gene model (genome_genes/, AMRFinderPlus features).

    python -m unittest discover -s backend/tests

AMRFinderPlus does not run on Windows, so these replace it with a stand-in
that returns fixed hits; everything around it is the real code: choosing the
gene model, the species call, building the gene features, `genes_found`, and
answering with the k-mer model when AMRFinderPlus fails. That the features
match training (experiments/genome/genes.py) was checked on 3,600 real
genome-drug rows from the gene matrix: identical.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from api import model_registry  # noqa: E402
from ml_models import genome_predictor as gp  # noqa: E402
from test_genome_wiring import fasta, write_model  # noqa: E402

ANTIBIOTICS = ['ciprofloxacin', 'ampicillin']
RULES = {'class_to_amrfinder': {'fluoroquinolone': ['QUINOLONE'], 'beta_lactam': ['BETA-LACTAM']},
         'key_determinants': {'ciprofloxacin': ['gyrA_S83']},
         'efflux_classes': ['EFFLUX', 'MULTIDRUG'], 'point_subtypes': ['POINT', 'POINT_DISRUPT']}
FEATURES = ['Antibiotic', 'drug_class', 'g_gyrA_S83L', 'g_blaTEM-1', 'gene_class_n', 'mutation_class_n',
            'gene_class_any', 'key_determinant', 'amr_genes_total', 'efflux_n']
HITS = pd.DataFrame({'symbol': ['gyrA_S83L', 'blaTEM-1', 'acrF'],
                     'name': ['', 'class A beta-lactamase TEM-1', ''],
                     'class': ['QUINOLONE', 'BETA-LACTAM', 'EFFLUX'],
                     'subclass': ['QUINOLONE', 'BETA-LACTAM', 'EFFLUX'],
                     'type': ['point_mutation', 'gene', 'gene']})


def write_gene_model(model_dir):
    """A tiny gene model: resistant to ciprofloxacin exactly when gyrA_S83 is there."""
    import lightgbm as lgb
    rng = np.random.default_rng(0)
    n = 400
    X = pd.DataFrame({
        'Antibiotic': pd.Categorical(rng.choice(ANTIBIOTICS, n), categories=ANTIBIOTICS),
        'drug_class': pd.Categorical(rng.choice(['fluoroquinolone', 'beta_lactam'], n),
                                     categories=['beta_lactam', 'fluoroquinolone']),
        'g_gyrA_S83L': rng.integers(0, 2, n), 'g_blaTEM-1': rng.integers(0, 2, n)})
    for f in FEATURES[4:]:
        X[f] = rng.integers(0, 3, n)
    X['key_determinant'] = X['g_gyrA_S83L']
    y = X['g_gyrA_S83L']
    booster = lgb.train({'objective': 'binary', 'verbose': -1, 'min_data_in_leaf': 5},
                        lgb.Dataset(X[FEATURES], y), num_boost_round=20)
    target = os.path.join(model_dir, gp.GENE_FOLDER)
    os.makedirs(target)
    booster.save_model(os.path.join(target, 'model.txt'))
    with open(os.path.join(target, 'feature_meta.json'), 'w', encoding='utf-8') as fh:
        json.dump({'model_type': 'lightgbm', 'run_id': 'TEST_genes', 'threshold': 0.5, 'features': FEATURES,
                   'category_levels': {'Antibiotic': ANTIBIOTICS,
                                       'drug_class': ['beta_lactam', 'fluoroquinolone']},
                   'drug_class_map': {'ciprofloxacin': 'fluoroquinolone', 'ampicillin': 'beta_lactam'},
                   'gene_features': RULES}, fh)
    with open(os.path.join(target, 'genome_metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump({'schema': 1, 'model': 'genome_genes_lightgbm', 'run_id': 'TEST_genes', 'threshold': 0.5,
                   'test': {'auc_roc': 0.97, 'auc_roc_ci': [0.96, 0.98]}}, fh)
    # Species profiles: the random test genome is nearest to "Escherichia coli"
    profile = gp.genome_counts(fasta(150_000))[0].astype(np.float32)
    np.savez_compressed(os.path.join(target, 'species_profiles.npz'),
                        species_taxon_id=np.array(['562', '573']),
                        species_name=np.array(['Escherichia coli', 'Klebsiella pneumoniae']),
                        genus_name=np.array(['Escherichia', 'Klebsiella']), genomes=np.array([10, 10]),
                        profile=np.stack([profile, np.roll(profile, 7)]))


def post(text, antibiotic='ciprofloxacin'):
    return Client().post('/api/predict/', data=json.dumps({'fasta_text': text, 'antibiotic': antibiotic}),
                         content_type='application/json')


class GeneModel(unittest.TestCase):
    def setUp(self):
        cache.clear()
        self.saved = model_registry._kmer
        self.dir = tempfile.mkdtemp()
        write_gene_model(self.dir)
        self.calls = []

    def tearDown(self):
        model_registry._kmer = self.saved
        shutil.rmtree(self.dir, ignore_errors=True)

    def fake_amrfinder(self, hits=HITS, fail=None):
        def run(fasta_text, organism=None, amrfinder=None):
            self.calls.append(organism)
            if fail:
                raise RuntimeError(fail)
            return hits, ''
        return [mock.patch.object(gp, 'find_amrfinder', return_value='/usr/bin/amrfinder'),
                mock.patch.object(gp, 'run_amrfinder', side_effect=run),
                mock.patch.object(gp, 'supported_organisms', return_value={'Escherichia', 'Klebsiella_pneumoniae'})]

    def serve(self, patches):
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        model_registry._kmer = model_registry.predict_model(self.dir)
        return model_registry._kmer

    def test_without_amrfinder_the_gene_model_is_not_served(self):
        with mock.patch.object(gp, 'find_amrfinder', return_value=None):
            model = model_registry.predict_model(self.dir)
        self.assertFalse(isinstance(model, gp.GenomeModelPredictor) and model.uses_genes)

    def test_gene_model_answers_with_genes_found(self):
        model = self.serve(self.fake_amrfinder())
        self.assertTrue(model.uses_genes and model.is_trained)
        r = post(fasta(150_000))
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn('AMRFinderPlus', d['model_used'])
        self.assertEqual(d['prediction'], 'Resistant')          # gyrA_S83L present
        genes = d['genes_found']
        self.assertEqual([g['gene'] for g in genes][:1], ['gyrA_S83L'])   # relevant first
        self.assertEqual({g['gene']: g['relevant'] for g in genes},
                         {'gyrA_S83L': True, 'blaTEM-1': False, 'acrF': False})
        self.assertEqual(genes[0]['type'], 'point_mutation')
        self.assertEqual(genes[0]['drug_class'], 'quinolone')
        self.assertNotIn('top_kmers', d)                        # gene-only model: the page hides the cards
        self.assertEqual(d['species_detected']['species'], 'Escherichia coli')
        self.assertEqual(self.calls, ['Escherichia'])           # --organism as in training

    def test_no_hits_is_an_empty_list_not_a_missing_field(self):
        self.serve(self.fake_amrfinder(hits=HITS.iloc[:0]))
        d = post(fasta(150_000)).json()
        self.assertEqual(d['genes_found'], [])
        self.assertEqual(d['prediction'], 'Susceptible')

    def test_relevance_follows_the_requested_drug(self):
        self.serve(self.fake_amrfinder())
        genes = post(fasta(150_000), 'ampicillin').json()['genes_found']
        self.assertEqual(genes[0]['gene'], 'blaTEM-1')
        self.assertTrue(genes[0]['relevant'])

    def test_amrfinder_failure_falls_back_to_the_kmer_model(self):
        write_model(self.dir)                                   # a k-mer model in genome/
        self.serve(self.fake_amrfinder(fail='AMRFinderPlus took longer than 100 s'))
        r = post(fasta(150_000))
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertIn('TEST_kmer4_lgbm', d['model_used'])
        self.assertIn('longer than 100 s', d['warning'])
        self.assertNotIn('genes_found', d)                      # not searched

    def test_short_genome_is_refused_before_amrfinder_runs(self):
        self.serve(self.fake_amrfinder())
        r = post(fasta(20_000))
        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.calls, [])

    def test_health_reports_the_gene_model(self):
        self.serve(self.fake_amrfinder())
        st = Client().get('/api/health/').json()['models']['kmer_resistance']
        self.assertTrue(st['searches_genes'])
        self.assertEqual(st['run_id'], 'TEST_genes')


class Parsing(unittest.TestCase):
    def test_amrfinder_report_keeps_core_amr_hits(self):
        tsv = ('Protein id\tContig id\tStart\tStop\tStrand\tElement symbol\tElement name\tScope\tType\tSubtype\t'
               'Class\tSubclass\tMethod\n'
               'NA\tc1\t1\t2\t+\tgyrA_S83L\tgyrase\tcore\tAMR\tPOINT\tQUINOLONE\tQUINOLONE\tPOINTX\n'
               'NA\tc1\t1\t2\t+\tblaTEM-1\tTEM-1\tcore\tAMR\tAMR\tBETA-LACTAM\tBETA-LACTAM\tEXACTX\n'
               'NA\tc1\t1\t2\t+\tfosA\tfosA\tplus\tAMR\tAMR\tFOSFOMYCIN\tFOSFOMYCIN\tEXACTX\n'
               'NA\tc1\t1\t2\t+\tmerA\tmerA\tplus\tSTRESS\tMETAL\tMERCURY\tMERCURY\tEXACTX\n')
        hits = gp.parse_amrfinder(tsv)
        self.assertEqual(list(hits['symbol']), ['gyrA_S83L', 'blaTEM-1'])
        self.assertEqual(list(hits['type']), ['point_mutation', 'gene'])

    def test_old_column_names_are_read_too(self):
        tsv = ('Gene symbol\tSequence name\tScope\tElement type\tElement subtype\tClass\tSubclass\n'
               'blaTEM-1\tTEM-1\tcore\tAMR\tAMR\tBETA-LACTAM\tBETA-LACTAM\n')
        self.assertEqual(list(gp.parse_amrfinder(tsv)['symbol']), ['blaTEM-1'])


if __name__ == '__main__':
    unittest.main()
