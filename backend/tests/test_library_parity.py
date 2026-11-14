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


SERVED = os.path.join(BACKEND, 'trained_models')


def library_or_skip():
    try:
        import amrpredict  # noqa: F401
    except ImportError as e:
        raise unittest.SkipTest(f'amrpredict not importable: {e}')


class GenomeParity(unittest.TestCase):
    """amrpredict.predict_fasta(use_genes=False) and /predict's k-mer model (0.3.0 on)."""

    def test_same_answer(self):
        library_or_skip()
        import random
        from amrpredict.genome import GenomeModelPredictor as Library
        from ml_models.genome_predictor import GenomeModelPredictor as Served
        rng = random.Random(3)
        fasta = '>a\n' + ''.join(rng.choice('ACGT') for _ in range(120_000)) + '\n>b\n' + 'GATTACA' * 2000
        lib, served = Library(folder='genome'), Served(SERVED, folder='genome')
        self.assertEqual(lib.meta.get('run_id'), served.meta.get('run_id'))
        for ab in ('ciprofloxacin', 'Meropenem', 'not-a-drug'):
            with self.subTest(ab):
                self.assertEqual(lib.predict(fasta, ab), served.predict(fasta, ab))


class TrendParity(unittest.TestCase):
    """amrpredict.forecast_trend and /api/timeline/forecast/'s model."""

    def test_same_forecast(self):
        library_or_skip()
        from amrpredict.timeline_ml import TimelineMLForecaster as Library
        from ml_models.timeline_ml import TimelineMLForecaster as Served
        lib, served = Library(), Served(SERVED)
        for genus, ab in (('Salmonella', 'ciprofloxacin'), ('Escherichia', 'ampicillin'),
                          ('Klebsiella', 'meropenem')):
            with self.subTest(genus=genus, ab=ab):
                self.assertEqual(lib.forecast(genus, ab, years_ahead=7), served.forecast(genus, ab, years_ahead=7))


class RLParity(unittest.TestCase):
    """amrpredict.plan_treatment and /api/timeline/'s `rl` block."""

    def test_same_plan(self):
        library_or_skip()
        from amrpredict import rl_agent as library
        from ml_models import rl_agent as served
        lib, srv = library.load(), served.load(SERVED)
        for ab, weeks in (('ciprofloxacin', 12), ('imipenem', 52)):
            with self.subTest(ab=ab, weeks=weeks):
                self.assertEqual(lib.block(ab, weeks), srv.block(ab, weeks))


if __name__ == '__main__':
    unittest.main()
