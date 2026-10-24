"""/forecast's linked lists: genus -> species -> taxon ID, and MIC suggestions.

    python -m unittest discover -s backend/tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402


class OrganismTree(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vocab = Client().get('/api/vocabulary/').json()['lgbm']
        cls.tree = {g['genus']: g for g in cls.vocab['organisms']}

    def species(self, genus):
        return {s['name']: s for s in self.tree[genus]['species']}

    def test_only_what_the_model_knows(self):
        genera = {g.lower() for g in self.vocab['genera']}
        species = {s.lower() for s in self.vocab['species']}
        taxa = set(self.vocab['taxon_ids'])
        self.assertEqual({g.lower() for g in self.tree}, genera)        # every genus the model knows, no other
        for g in self.tree.values():
            for s in g['species']:
                self.assertIn(s['name'], species)
                self.assertTrue(set(s['taxon_ids']) <= taxa)
            self.assertTrue({o['id'] for o in g['other_taxon_ids']} <= taxa)

    def test_species_belong_to_their_genus(self):
        self.assertEqual(self.species('Escherichia')['coli']['taxon_ids'], [562])
        self.assertEqual(self.species('Campylobacter')['coli']['taxon_ids'], [195])  # same name, other genus
        self.assertIn('pneumoniae', self.species('Klebsiella'))
        self.assertNotIn('aureus', self.species('Escherichia'))
        for g in self.tree.values():
            for s in g['species']:
                self.assertTrue(s['label'].startswith(g['genus'] + ' '), s['label'])

    def test_renamed_genera_and_genus_level_ids(self):
        self.assertIn('butzleri', self.species('Arcobacter'))            # NCBI: Aliarcobacter
        self.assertIn('stutzeri', self.species('Pseudomonas'))           # NCBI: Stutzerimonas
        self.assertIn(590, [o['id'] for o in self.tree['Salmonella']['other_taxon_ids']])

    def test_nearly_every_taxon_id_is_offered(self):
        offered = {t for g in self.tree.values() for s in g['species'] for t in s['taxon_ids']}
        offered |= {o['id'] for g in self.tree.values() for o in g['other_taxon_ids']}
        missing = set(self.vocab['taxon_ids']) - offered
        self.assertLessEqual(len(missing), 1, missing)                     # 1733: "uncultured bacterium", no genus


class MicValues(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def get(self, **q):
        return Client().get('/api/mic-values/', q)

    def test_most_specific_level_answers(self):
        d = self.get(antibiotic='ciprofloxacin', genus='Escherichia', species='coli').json()
        self.assertEqual(d['level'], 'species')
        self.assertIn(1.0, d['values'])
        self.assertEqual(d['values'], sorted(d['values']))
        self.assertEqual(self.get(antibiotic='ciprofloxacin', genus='Escherichia').json()['level'], 'genus')
        self.assertEqual(self.get(antibiotic='ciprofloxacin').json()['level'], 'antibiotic')

    def test_falls_back_when_a_species_has_no_records(self):
        d = self.get(antibiotic='ciprofloxacin', genus='Staphylococcus', species='aureus').json()
        self.assertIn(d['level'], ('genus', 'antibiotic'))
        self.assertTrue(d['values'])

    def test_spelling_variant_is_canonical(self):
        self.assertEqual(self.get(antibiotic='rifampin').json()['antibiotic'], 'rifampicin')

    def test_unknown_drug_and_missing_antibiotic(self):
        self.assertEqual(self.get(antibiotic='notadrug').json(), {'antibiotic': 'notadrug', 'genus': '',
                                                                   'species': '', 'values': [], 'level': None})
        self.assertEqual(self.get().status_code, 400)


if __name__ == '__main__':
    unittest.main()
