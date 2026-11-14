"""The dashboard endpoints (/api/explore/*, docs/INSTRUCTOR_REQUIREMENTS_PLAN.md).

    python -m unittest discover -s backend/tests
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.test import Client  # noqa: E402

from api import explorer  # noqa: E402


def get(path):
    return Client().get('/api/explore/' + path)


@unittest.skipUnless(explorer.available(), 'dashboard data not built')
class Explore(unittest.TestCase):
    def test_meta_lists_every_filter(self):
        m = get('meta/').json()
        self.assertEqual([o['gram'] for o in m['organisms']], ['positive', 'negative', 'other'])
        self.assertEqual(m['antibiotic_hierarchy'][0]['family'], 'Beta-lactams')
        for key in ('chemical_groups', 'countries', 'infection_types', 'diseases', 'resistance_types', 'year_range'):
            self.assertTrue(m[key], key)

    def test_rate_is_resistant_over_tested_without_intermediate(self):
        cube = explorer.data()['cube']
        sub = cube[cube.antibiotic == 'ciprofloxacin']
        n = int(sub.tested.sum() - sub.intermediate.sum())
        r = get('summary/?by=antibiotic&antibiotic=ciprofloxacin').json()['rows'][0]
        self.assertEqual((r['n'], r['r']), (n, int(sub.resistant.sum())))
        self.assertAlmostEqual(r['resistant_pct'], round(100 * r['r'] / r['n'], 1))

    def test_intermediate_toggle_counts_them_as_resistant(self):
        off = get('summary/?by=antibiotic&antibiotic=ciprofloxacin').json()['rows'][0]
        on = get('summary/?by=antibiotic&antibiotic=ciprofloxacin&include_intermediate=1').json()['rows'][0]
        self.assertEqual(on['n'], off['n'] + off['intermediate'])
        self.assertEqual(on['r'], off['r'] + off['intermediate'])

    def test_filters_narrow_the_rows(self):
        everything = get('summary/?by=family').json()['total']['tested']
        negative = get('summary/?by=family&gram=negative').json()['total']['tested']
        both = get('summary/?by=family&gram=negative&country=PAK').json()['total']['tested']
        self.assertGreater(everything, negative)
        self.assertGreater(negative, both)

    def test_group_filter_selects_its_drugs(self):
        rows = get('summary/?by=antibiotic&subfamily=Carbapenems').json()['rows']
        self.assertEqual({r['value'] for r in rows}, {'imipenem', 'meropenem', 'ertapenem', 'doripenem'})

    def test_low_sample_flag_and_order(self):
        rows = get('summary/?by=antibiotic&min_n=500').json()['rows']
        flags = [r['low_sample'] for r in rows]
        self.assertEqual(flags, sorted(flags))           # small groups last
        self.assertTrue(all(r['n'] < 500 for r in rows if r['low_sample']))

    def test_countries_carry_types_and_organism(self):
        c = get('countries/?family=Beta-lactams').json()['countries']
        pak = next(x for x in c if x['iso3'] == 'PAK')
        self.assertLessEqual(len(pak['top_types']), 3)
        self.assertTrue(pak['top_organism'])

    def test_drug_detail(self):
        d = get('drug/meropenem/').json()
        self.assertEqual((d['family'], d['subfamily'], d['aware']), ('Beta-lactams', 'Carbapenems', 'Watch'))
        self.assertTrue(d['components'][0]['molecular_formula'])
        self.assertEqual(get(d['components'][0]['structure_url'].replace('explore/', '')).status_code, 200)

    def test_alias_is_resolved(self):
        self.assertEqual(get('drug/colomycin/').json()['antibiotic'], 'colistin')

    def test_bad_input(self):
        self.assertEqual(get('drug/not-a-drug/').status_code, 404)
        self.assertEqual(get('summary/?by=nope').status_code, 400)
        self.assertEqual(get('summary/?min_n=abc').status_code, 400)


if __name__ == '__main__':
    unittest.main()
