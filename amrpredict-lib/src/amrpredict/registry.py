"""Lazily-constructed shared predictor instances.

Loading the artifacts costs real time and memory (the forecaster and the
genome models are a few MB each), so nothing is read from disk until the first
call. Each predictor is built once and reused for the process lifetime.
"""
import threading

_lock = threading.Lock()
_instances = {}


def _get(key, factory, model_dir=None):
    if model_dir is not None:
        # An explicit directory bypasses the shared cache entirely.
        return factory(model_dir)
    with _lock:
        if key not in _instances:
            _instances[key] = factory()
        return _instances[key]


def lgbm(model_dir=None):
    """Shared :class:`~amrpredict.lgbm.LGBMResistancePredictor`."""
    from .lgbm import LGBMResistancePredictor
    return _get('lgbm', LGBMResistancePredictor, model_dir)


def genome(model_dir=None):
    """Shared :class:`~amrpredict.genome.GenomeModelPredictor`: the gene model
    when AMRFinderPlus is installed, the k-mer model otherwise."""
    from .genome import GenomeModelPredictor
    return _get('genome', GenomeModelPredictor, model_dir)


def genome_kmers(model_dir=None):
    """Shared k-mer genome model, whatever is installed."""
    from .genome import KMER_FOLDER, GenomeModelPredictor
    return _get('genome_kmers', lambda d=None: GenomeModelPredictor(d, folder=KMER_FOLDER), model_dir)


def trend(model_dir=None):
    """Shared :class:`~amrpredict.timeline_ml.TimelineMLForecaster`."""
    from .timeline_ml import TimelineMLForecaster
    return _get('trend', TimelineMLForecaster, model_dir)


def rl(model_dir=None):
    """Shared :class:`~amrpredict.rl_agent.RLAgent`, or None when it is not bundled."""
    from .rl_agent import load
    return _get('rl', load, model_dir)


def timeline(model_dir=None):
    """Shared :class:`~amrpredict.timeline.MutationTimelinePredictor`."""
    from .timeline import MutationTimelinePredictor
    return _get('timeline', MutationTimelinePredictor, model_dir)


def reset():
    """Drop the cached predictors, freeing their memory.

    Mainly useful in tests, or after pointing the library at different
    artifacts.
    """
    with _lock:
        _instances.clear()
