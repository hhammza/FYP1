"""amrpredict — antimicrobial resistance prediction from genomic data.

Three models behind one flat API:

>>> import amrpredict
>>> amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)['prediction']
'Susceptible'

``forecast`` works from genome metadata and MIC values (LightGBM), while
``predict_fasta`` works from a genome sequence (k-mer RandomForest).
``simulate_timeline`` projects resistance evolution under antibiotic pressure
and is a biological simulation, not a trained model.
"""
from . import registry
from ._paths import default_model_dir

__version__ = '0.1.0'

__all__ = [
    'forecast',
    'predict_fasta',
    'simulate_timeline',
    'antibiotics',
    'status',
    'registry',
    'default_model_dir',
    'LGBMResistancePredictor',
    'KmerResistancePredictor',
    'MutationTimelinePredictor',
    '__version__',
]


def forecast(antibiotic, *, taxon_id=None, mic_value=None, mic_sign=None,
             genus='unknown', species='unknown', threshold=0.40, model_dir=None):
    """Forecast resistance from genome metadata and (optionally) an MIC value.

    Args:
        antibiotic: Antibiotic name, case-insensitive (e.g. ``'ciprofloxacin'``).
        taxon_id: NCBI taxonomy ID of the organism, e.g. ``562`` for *E. coli*.
        mic_value: Minimum inhibitory concentration in mg/L.
        mic_sign: Comparator recorded with the MIC — ``'='``, ``'>'``, ``'<='`` …
        genus: Genus name, e.g. ``'Escherichia'``.
        species: Species name, e.g. ``'coli'``.
        threshold: Probability at or above which the call is ``'Resistant'``.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``prediction``, ``probability``, ``confidence``, ``drug_class``
        and related fields.
    """
    return registry.lgbm(model_dir).predict(
        antibiotic, taxon_id=taxon_id, mic_value=mic_value, mic_sign=mic_sign,
        genus=genus, species=species, threshold=threshold,
    )


def predict_fasta(fasta_text, antibiotic, *, threshold=0.5, model_dir=None):
    """Predict resistance from a genome sequence via 4-mer composition.

    Args:
        fasta_text: FASTA contents as a string (headers optional).
        antibiotic: Antibiotic name, case-insensitive.
        threshold: Probability at or above which the call is ``'Resistant'``.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``prediction``, ``probability``, ``confidence``,
        ``gc_content``, ``sequence_length`` and ``top_kmers``.
    """
    return registry.kmer(model_dir).predict(fasta_text, antibiotic, threshold)


def simulate_timeline(fasta_text, antibiotic, *, n_weeks=8, model_dir=None):
    """Simulate week-by-week resistance evolution under antibiotic pressure.

    This is a deterministic biological simulation, not a trained model — it
    carries no AUC or accuracy score. Treat its output as illustrative.

    Args:
        fasta_text: FASTA contents as a string.
        antibiotic: Antibiotic name, case-insensitive.
        n_weeks: Number of weeks to project.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with a ``weeks`` series, mutation events and gene activations.
    """
    return registry.timeline(model_dir).predict(fasta_text, antibiotic, n_weeks)


def antibiotics(model_dir=None):
    """Sorted list of antibiotic names the k-mer model was trained on."""
    return sorted(registry.kmer(model_dir).ab_list)


def status(model_dir=None):
    """Report which models loaded, keyed by model name."""
    return {
        'version': __version__,
        'lgbm_forecasting': registry.lgbm(model_dir).status,
        'kmer_resistance': registry.kmer(model_dir).status,
        'mutation_timeline': registry.timeline(model_dir).status,
    }


def __getattr__(name):
    # Re-export the classes without importing numpy/pandas/lightgbm at import time.
    if name == 'LGBMResistancePredictor':
        from .lgbm import LGBMResistancePredictor
        return LGBMResistancePredictor
    if name == 'KmerResistancePredictor':
        from .kmer import KmerResistancePredictor
        return KmerResistancePredictor
    if name == 'MutationTimelinePredictor':
        from .timeline import MutationTimelinePredictor
        return MutationTimelinePredictor
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
