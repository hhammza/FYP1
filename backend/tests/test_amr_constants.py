"""Checks on backend/amr_constants.py, the one home of antibiotic names.

    python -m unittest discover -s backend/tests
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import amr_constants as c  # noqa: E402


def is_clean(name):
    return name == ' '.join(name.split()).lower()


class FrontendCopy(unittest.TestCase):
    def test_frontend_json_matches(self):
        with open(c.FRONTEND_COPY, encoding='utf-8') as fh:
            on_disk = json.load(fh)
        self.assertEqual(on_disk, json.loads(json.dumps(c.frontend_names())),
                         'frontend/antibiotic_names.json is stale: run python backend/amr_constants.py')


class LibraryCopy(unittest.TestCase):
    """amrpredict installs without backend/, so it carries its own copy."""

    def test_library_copy_matches(self):
        import importlib.util
        path = os.path.join(os.path.dirname(os.path.dirname(c.FRONTEND_COPY)), 'amrpredict-lib',
                            'src', 'amrpredict', 'amr_constants.py')
        spec = importlib.util.spec_from_file_location('amrpredict_constants', path)
        lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lib)
        for name in ('DRUG_CLASS_MAP', 'ANTIBIOTIC_ALIASES', 'PHENOTYPE_MAP', 'MIC_SIGN_ALIASES',
                     'UI_ANTIBIOTICS', 'LGBM_TRAIN_PHENOTYPES', 'KMER_TRAIN_PHENOTYPES'):
            self.assertEqual(getattr(lib, name), getattr(c, name),
                             f'amrpredict-lib/src/amrpredict/amr_constants.py {name} is stale: '
                             'copy it from backend/amr_constants.py')


class Names(unittest.TestCase):
    def test_alias_targets_are_canonical_and_classed(self):
        for variant, canonical in c.ANTIBIOTIC_ALIASES.items():
            self.assertTrue(is_clean(variant), variant)
            if canonical is None:
                continue
            self.assertNotIn(canonical, c.ANTIBIOTIC_ALIASES, f'{variant} -> {canonical} is a chain')
            self.assertIn(canonical, c.DRUG_CLASS_MAP, f'{canonical} has no drug class')

    def test_dropdown_names(self):
        self.assertEqual(len(c.UI_ANTIBIOTICS), len(set(c.UI_ANTIBIOTICS)), 'duplicate in UI_ANTIBIOTICS')
        for name in c.UI_ANTIBIOTICS:
            self.assertTrue(is_clean(name), name)
            self.assertNotIn(name, c.ANTIBIOTIC_ALIASES, f'{name} is a variant, list its canonical name')
            self.assertIn(name, c.DRUG_CLASS_MAP, f'{name} has no drug class')

    def test_class_map_keys_are_clean(self):
        for name in c.DRUG_CLASS_MAP:
            self.assertTrue(is_clean(name), name)

    def test_normalize(self):
        self.assertEqual(c.normalize_antibiotic('  Rifampin '), 'rifampicin')
        self.assertEqual(c.normalize_antibiotic('Nalidixic  Acid'), 'nalidixic acid')
        self.assertEqual(c.normalize_antibiotic('carbapenem'), 'carbapenem')
        self.assertIsNone(c.normalize_antibiotic(None))


class Labels(unittest.TestCase):
    def test_trainer_phenotypes_are_known(self):
        for p in c.LGBM_TRAIN_PHENOTYPES + c.KMER_TRAIN_PHENOTYPES:
            self.assertIn(p, c.PHENOTYPE_MAP)
        self.assertTrue(set(c.PHENOTYPE_MAP.values()) <= {0, 1})


if __name__ == '__main__':
    unittest.main()
