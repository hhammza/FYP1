"""The "fill from Genome ID" helper on /forecast: GET /api/genome/<id>/.

    python -m unittest discover -s backend/tests
"""
import gzip
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.conf import settings  # noqa: E402
from django.test import Client  # noqa: E402

LAB = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'api', 'genome_lab_results.json.gz')


def get(genome_id, antibiotic=''):
    return Client().get(f'/api/genome/{genome_id}/', {'antibiotic': antibiotic})


class GenomeLookup(unittest.TestCase):
    def test_fills_the_organism_from_the_taxon_prefix(self):
        d = get('1001988.3').json()                                       # an E. coli strain's genome
        self.assertEqual(d['taxon_id'], 1001988)
        self.assertEqual((d['organism']['genus'], d['organism']['species'], d['organism']['taxon_id']),
                         ('Escherichia', 'coli', 562))
        self.assertIn('Escherichia coli', d['organism']['name'])
        self.assertEqual(d['genes_url'], '/genes#genome=1001988.3')

    def test_says_whether_each_model_trained_on_it(self):
        d = get('1001988.3').json()                                       # Hamza's example: a training genome of all three
        self.assertEqual(d['models']['forecast']['role'], 'train')
        split = json.load(gzip.open(os.path.join(str(settings.TRAINED_MODELS_DIR), 'lgbm_split_genomes.json.gz'), 'rt'))
        self.assertEqual(get(split['test'][0]).json()['models']['forecast']['role'], 'test')

    def test_lab_results_are_lab_only_and_follow_the_antibiotic(self):
        lab = json.load(gzip.open(LAB, 'rt', encoding='utf-8'))
        self.assertIn('Laboratory Method', lab['source'])
        gid, rows = next(iter(lab['genomes'].items()))
        drug = rows[0][0]
        d = get(gid, drug).json()
        self.assertEqual(len(d['lab_results']), len(rows))
        self.assertTrue(d['lab_for_antibiotic'])
        self.assertTrue(all(r['antibiotic'] == drug for r in d['lab_for_antibiotic']))
        self.assertEqual(get(gid).json()['lab_for_antibiotic'], [])          # no drug chosen: none picked

    def test_a_ratio_or_a_zone_is_not_offered_as_a_mic(self):
        d = get('106654.148', 'trimethoprim/sulfamethoxazole').json()
        if not d['lab_for_antibiotic']:
            self.skipTest('genome not in the local lab table')
        self.assertEqual(d['lab_for_antibiotic'][0]['value'], '1/19')
        self.assertFalse(d['lab_for_antibiotic'][0]['is_mic'])
        self.assertTrue(get('106654.148', 'gentamicin').json()['lab_for_antibiotic'][0]['is_mic'])

    def test_unknown_organism_fills_nothing(self):
        o = get('999999999.1').json()['organism']
        self.assertEqual((o['genus'], o['species'], o['taxon_id']), (None, None, None))

    def test_malformed_ids_are_a_400(self):
        for bad in ('abc', '562', '562.12.3', '..', '562.', '1' * 12 + '.1'):
            r = get(bad)
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn('562.1234', r.json()['error'])


if __name__ == '__main__':
    unittest.main()
