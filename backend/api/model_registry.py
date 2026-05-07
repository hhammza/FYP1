"""Global model registry — loaded once at startup."""
import os
import sys

_lgbm = None
_kmer = None
_timeline = None

def init_models():
    global _lgbm, _kmer, _timeline
    if _lgbm is not None:
        return

    from django.conf import settings
    model_dir = str(settings.TRAINED_MODELS_DIR)

    sys.path.insert(0, str(settings.BASE_DIR))

    from ml_models.lgbm_predictor import LGBMResistancePredictor
    from ml_models.resistance_predictor import KmerResistancePredictor
    from ml_models.mutation_timeline import MutationTimelinePredictor

    _lgbm = LGBMResistancePredictor(model_dir)
    _kmer = KmerResistancePredictor(model_dir)
    _timeline = MutationTimelinePredictor(model_dir)
    print("[Registry] All models initialized.")

def get_lgbm():
    return _lgbm

def get_kmer():
    return _kmer

def get_timeline():
    return _timeline
