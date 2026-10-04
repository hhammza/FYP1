"""ml_models/training_genomes.py: was a genome in a served model's training data?

    python -m unittest discover -s backend/tests
"""
import gzip
import json
import os
import shutil
import sys
import tempfile
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

from ml_models.training_genomes import genome_status  # noqa: E402

SERVED = os.path.join(BACKEND, 'trained_models')


def write(path, run_id, train, test):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with gzip.open(path, 'wt', encoding='utf-8') as fh:
        json.dump({'run_id': run_id, 'split': 'grouped', 'clean_version': 'v7',
                   'train': train, 'test': test}, fh)


class Lookup(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        write(os.path.join(self.dir, 'lgbm_split_genomes.json.gz'), 'F', ['562.10', '573.2'], ['195.304'])
        write(os.path.join(self.dir, 'genome', 'split_genomes.json.gz'), 'K', ['573.2'], ['562.10'])

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_roles(self):
        s = genome_status(self.dir, '562.10')
        self.assertEqual(s['forecast']['role'], 'train')
        self.assertEqual(s['genome_kmers']['role'], 'test')
        self.assertIn('fair test', s['genome_kmers']['detail'])
        self.assertNotIn('genome_genes', s)              # no file, no entry

    def test_ids_are_text(self):
        self.assertEqual(genome_status(self.dir, '195.304')['forecast']['role'], 'test')
        self.assertIsNone(genome_status(self.dir, '195.3040')['forecast']['role'])
        self.assertEqual(genome_status(self.dir, ' 195.304 ')['forecast']['role'], 'test')

    def test_a_new_file_is_read_again(self):
        path = os.path.join(self.dir, 'lgbm_split_genomes.json.gz')
        self.assertEqual(genome_status(self.dir, '573.2')['forecast']['role'], 'train')
        write(path, 'F2', [], ['573.2'])
        os.utime(path, (os.path.getmtime(path) + 5,) * 2)
        s = genome_status(self.dir, '573.2')['forecast']
        self.assertEqual((s['run_id'], s['role']), ('F2', 'test'))


@unittest.skipUnless(os.path.exists(os.path.join(SERVED, 'lgbm_split_genomes.json.gz')),
                     'no split file for the served forecaster')
class Served(unittest.TestCase):
    def test_served_files_cover_every_model_and_never_overlap(self):
        from ml_models.training_genomes import FILES, load_split
        for name, rel in FILES.items():
            split = load_split(os.path.join(SERVED, rel))
            if split is None:
                continue
            with self.subTest(model=name):
                self.assertTrue(split['test'])
                self.assertFalse(split['train'] & split['test'])


if __name__ == '__main__':
    unittest.main()
