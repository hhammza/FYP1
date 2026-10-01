"""amrpredict.forecast() and /forecast give the same answer for the same model.

    python -m unittest discover -s backend/tests

The library carries its own copy of the forecaster loader (amrpredict/lgbm.py,
ported from ml_models/lgbm_predictor.py) and of the model files. When both hold
the same promoted run, any difference in output means the two loaders have
drifted apart.
"""
import os
import sys
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRARY_SRC = os.path.join(os.path.dirname(BACKEND), 'amrpredict-lib', 'src')
sys.path.insert(0, BACKEND)
sys.path.insert(0, LIBRARY_SRC)

from ml_models.lgbm_predictor import LGBMResistancePredictor as Backend  # noqa: E402

CASES = [
    dict(antibiotic='ciprofloxacin', taxon_id=562, mic_value=4, genus='Escherichia', species='coli'),
    dict(antibiotic='Meropenem', taxon_id=573, genus='Klebsiella'),
    dict(antibiotic='rifampin'),
    dict(antibiotic='gentamicin', taxon_id=1280, mic_value=0.5, mic_sign='<='),
    dict(antibiotic='not-a-drug', taxon_id=1045010, mic_value=64, mic_sign='>='),
]


class Parity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from amrpredict.lgbm import LGBMResistancePredictor as Library
        except ImportError as e:
            raise unittest.SkipTest(f'amrpredict not importable: {e}')
        cls.backend = Backend(os.path.join(BACKEND, 'trained_models'))
        cls.library = Library()
        if not (cls.backend.is_trained and cls.library.is_trained):
            raise unittest.SkipTest('a forecaster is missing')
        if cls.backend.run_id != cls.library.run_id:
            raise unittest.SkipTest(f'different runs: backend {cls.backend.run_id}, '
                                    f'library {cls.library.run_id} (promote.py --library)')

    def test_same_probability_call_and_evidence(self):
        for case in CASES:
            with self.subTest(**case):
                b, lib = self.backend.predict(**case), self.library.predict(**case)
                for key in ('probability', 'prediction', 'threshold', 'drug_class', 'antibiotic',
                            'calibrated', 'model_run'):
                    self.assertEqual(b[key], lib[key], key)
                self.assertEqual(b['evidence'], lib['evidence'])


if __name__ == '__main__':
    unittest.main()
