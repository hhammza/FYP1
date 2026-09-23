"""Lazily-constructed shared predictor instances.

Loading the artifacts costs real time and memory (the k-mer model alone is
~5.5 MB), so nothing is read from disk until the first call. Each predictor is
built once and reused for the process lifetime.
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


def kmer(model_dir=None):
    """Shared :class:`~amrpredict.kmer.KmerResistancePredictor`."""
    from .kmer import KmerResistancePredictor
    return _get('kmer', KmerResistancePredictor, model_dir)


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
