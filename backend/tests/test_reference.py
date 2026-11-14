"""The lookup tables in backend/reference/ are complete and consistent.

    python -m unittest discover -s backend/tests
"""
import os
import re
import unittest

import pandas as pd

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(BACKEND, 'reference')
ROOT = os.path.dirname(BACKEND)
CLEANED = os.path.join(ROOT, 'experiments', 'cache', 'clean_v7_amr_full_norm.pkl')


def table(name):
    return pd.read_csv(os.path.join(REF, name), dtype=str).fillna('')


class Tables(unittest.TestCase):
    def test_every_drug_has_one_row_with_a_known_family(self):
        a, f = table('antibiotics.csv'), table('families.csv')
        self.assertFalse(a.antibiotic.duplicated().any())
        pairs = set(zip(f.family, f.subfamily))
        for _, r in a.iterrows():
            self.assertIn((r.family, r.subfamily), pairs, r.antibiotic)
            self.assertIn(r.aware, {'Access', 'Watch', 'Reserve', 'Not classified'}, r.antibiotic)
            self.assertTrue(r.chemical_group, r.antibiotic)

    def test_aliases_point_to_a_drug_in_the_table(self):
        a = table('antibiotics.csv')
        for alias in a.alias_of[a.alias_of != '']:
            self.assertIn(alias, set(a.antibiotic))

    def test_every_chemical_group_is_described(self):
        a, c = table('antibiotics.csv'), table('chemical_groups.csv')
        self.assertEqual(set(a.chemical_group), set(c.chemical_group))
        self.assertTrue((c.core_structure != '').all())

    def test_gram_stain_values(self):
        o = table('organisms.csv')
        self.assertTrue(o.gram_stain.isin({'positive', 'negative', 'other'}).all())
        self.assertEqual(o.loc[o.genus == 'Staphylococcus', 'gram_stain'].item(), 'positive')
        self.assertEqual(o.loc[o.genus == 'Escherichia', 'gram_stain'].item(), 'negative')

    def test_infection_rules_compile_and_use_known_fields(self):
        rules = table('infection_types.csv')
        for _, r in rules.iterrows():
            re.compile(r.pattern)
            self.assertIn(r.field, {'disease', 'host_health', 'body_sample_site', 'isolation_source'})
        d = table('diseases.csv')
        self.assertTrue(set(d.infection_type) <= set(rules.infection_type) | {'Other or unspecified'})

    def test_resistance_types_name_known_drugs_and_genera(self):
        a, o, t = table('antibiotics.csv'), table('organisms.csv'), table('resistance_types.csv')
        for _, r in t.iterrows():
            for drug in r.antibiotics.split(';'):
                self.assertIn(drug, set(a.antibiotic), r.resistance_type)
            for g in r.genera.split(';'):
                if g.startswith('@'):
                    self.assertIn(g[1:], set(o.order_group))
                else:
                    self.assertIn(g, set(o.genus), r.resistance_type)


@unittest.skipUnless(os.path.exists(CLEANED), 'cleaned table not on this machine')
class CoversTheData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_pickle(CLEANED)[['Antibiotic', 'genus']]

    def test_every_drug_in_the_data_has_a_row(self):
        missing = set(self.df.Antibiotic.unique()) - set(table('antibiotics.csv').antibiotic)
        self.assertEqual(missing, set())

    def test_every_genus_in_the_data_has_a_row(self):
        missing = set(self.df.genus.unique()) - set(table('organisms.csv').genus)
        self.assertEqual(missing, set())


if __name__ == '__main__':
    unittest.main()
