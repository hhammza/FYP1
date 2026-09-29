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
    _kmer = predict_model(model_dir)
    _timeline = MutationTimelinePredictor(model_dir)
    print("[Registry] All models initialized.")

def predict_model(model_dir):
    """/predict serves the complete-genome model once one is promoted
    (experiments/promote.py --genome), else the old K-mer RandomForest. A gene
    model reports is_trained=False until the server runs AMRFinderPlus, so it
    is never served with guessed gene features."""
    from ml_models.genome_predictor import GenomeModelPredictor
    from ml_models.resistance_predictor import KmerResistancePredictor
    genome = GenomeModelPredictor(model_dir)
    return genome if genome.is_trained else KmerResistancePredictor(model_dir)

def reload_kmer():
    """Choose and load the /predict model again, so a model promoted (or
    removed) while the server runs is picked up whole: which model, its
    features and its metrics, not just the old model's file."""
    global _kmer
    from django.conf import settings
    _kmer = predict_model(str(settings.TRAINED_MODELS_DIR))
    return _kmer

def get_lgbm():
    return _lgbm

def get_kmer():
    return _kmer

def get_timeline():
    return _timeline
