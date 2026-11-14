"""amrpredict — antimicrobial resistance prediction from genomic data.

The models the project's web app serves, behind one flat API:

>>> import amrpredict
>>> amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)['prediction']
'Susceptible'

Trained models:

* ``forecast`` — resistance from metadata and an MIC value (LightGBM).
* ``predict_fasta`` — resistance from a complete genome: the gene model
  (LightGBM on AMRFinderPlus genes) when AMRFinderPlus is installed, the k-mer
  model (LightGBM on 4-mer frequencies) otherwise.
* ``forecast_trend`` — the yearly % resistant of a genus and antibiotic, and its
  forecast for the coming years (LightGBM on BV-BRC laboratory results).
* ``plan_treatment`` — which drug to give each week, from an RL agent (PPO)
  trained on the simulation, against fixed schedules.

``simulate_timeline`` projects week-by-week resistance under treatment and is
a biological simulation, not a trained model.
"""
from . import registry
from ._paths import default_model_dir

__version__ = '0.3.0'

__all__ = [
    'forecast',
    'predict_fasta',
    'identify_species',
    'forecast_trend',
    'trend_series',
    'plan_treatment',
    'simulate_timeline',
    'antibiotics',
    'status',
    'registry',
    'default_model_dir',
    'LGBMResistancePredictor',
    'GenomeModelPredictor',
    'TimelineMLForecaster',
    'RLAgent',
    'MutationTimelinePredictor',
    '__version__',
]


def forecast(antibiotic, *, taxon_id=None, mic_value=None, mic_sign=None,
             genus='unknown', species='unknown', threshold=None, model_dir=None):
    """Forecast resistance from genome metadata and (optionally) an MIC value.

    Args:
        antibiotic: Antibiotic name, case-insensitive (e.g. ``'ciprofloxacin'``).
        taxon_id: NCBI taxonomy ID of the organism, e.g. ``562`` for *E. coli*.
        mic_value: Minimum inhibitory concentration in mg/L.
        mic_sign: Comparator recorded with the MIC — ``'='``, ``'>'``, ``'<='`` …
        genus: Genus name, e.g. ``'Escherichia'``.
        species: Species name, e.g. ``'coli'``.
        threshold: Probability at or above which the call is ``'Resistant'``.
            Default: the threshold the bundled model was promoted with
            (``status()['lgbm_forecasting']['default_threshold']``).
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``prediction``, ``probability`` (calibrated), ``confidence``,
        ``drug_class``, ``model_run``, ``evidence`` (which inputs the model
        recognised) and related fields.
    """
    return registry.lgbm(model_dir).predict(
        antibiotic, taxon_id=taxon_id, mic_value=mic_value, mic_sign=mic_sign,
        genus=genus, species=species, threshold=threshold,
    )


def predict_fasta(fasta_text, antibiotic, *, threshold=None, genus=None, species=None,
                  use_genes=None, model_dir=None):
    """Predict resistance from a complete genome assembly (at least 100,000 bp).

    Args:
        fasta_text: FASTA contents as a string; every contig is read.
        antibiotic: Antibiotic name, case-insensitive.
        threshold: Probability at or above which the call is ``'Resistant'``.
            Default: the model's own threshold, chosen on validation genomes.
        genus, species: The organism, if known (the k-mer model uses them).
        use_genes: ``None`` (default) uses the gene model when AMRFinderPlus is
            installed and the k-mer model otherwise; ``False`` always uses the
            k-mer model; ``True`` requires the gene model.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``prediction``, ``probability``, ``confidence``,
        ``gc_content``, ``sequence_length``, ``model_used``; ``top_kmers`` from
        the k-mer model; ``genes_found`` and ``species_detected`` from the gene
        model. Bad input gives a dict with ``error`` instead of raising.
    """
    if use_genes is False:
        model = registry.genome_kmers(model_dir)
    else:
        model = registry.genome(model_dir)
        if use_genes and not model.uses_genes:
            return {'error': 'the gene model needs AMRFinderPlus (the `amrfinder` program), '
                             'which was not found; pass use_genes=None to use the k-mer model'}
    return model.predict(fasta_text, antibiotic, threshold, genus, species)


def identify_species(fasta_text, *, model_dir=None):
    """Species and genus of a complete genome from its 6-mer profile.

    Returns:
        dict with ``species``, ``genus`` (``None`` when no reference is close)
        and ``distance``; or a dict with ``error``.
    """
    from .genome import GENE_FOLDER, GenomeModelPredictor, SpeciesProfiles, genome_counts
    import os
    path = os.path.join(model_dir or default_model_dir(), GENE_FOLDER, 'species_profiles.npz')
    counts, _, length = genome_counts(fasta_text)
    if length < GenomeModelPredictor.MIN_BP:
        return {'error': f'genome too short ({length:,} bp): upload a complete assembly',
                'sequence_length': length}
    found = SpeciesProfiles(path).identify(counts) or {'species': None, 'genus': None, 'distance': None}
    return {k: (str(v) if isinstance(v, str) else v) for k, v in found.items()}


def forecast_trend(genus, antibiotic, *, years_ahead=5, model_dir=None):
    """Yearly % resistant of a genus and antibiotic, and the timeline ML model's forecast.

    Args:
        genus: Genus name, case-insensitive (e.g. ``'Salmonella'``);
            ``trend_series()`` lists those with enough history.
        antibiotic: Antibiotic name, case-insensitive.
        years_ahead: Years to forecast, 1 to 10. The 80% band widens with each.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``history`` (year, resistant_pct, n lab results),
        ``forecast`` (year, resistant_pct, lo, hi), the model's held-out
        ``metrics`` against the baselines and a ``label``; or a dict with
        ``error`` when the pair has too little history.
    """
    years_ahead = int(years_ahead)
    if not 1 <= years_ahead <= 10:
        return {'error': 'years_ahead must be from 1 to 10'}
    model = registry.trend(model_dir)
    if not model.is_trained:
        return {'error': 'the timeline ML model is not bundled'}
    result = model.forecast(genus, antibiotic, years_ahead=years_ahead)
    return result or {'error': f'{genus} has too little yearly lab history for {antibiotic} to forecast'}


def trend_series(model_dir=None):
    """``{genus: [antibiotic, ...]}`` that ``forecast_trend`` can forecast."""
    return registry.trend(model_dir).series


def plan_treatment(antibiotic, *, n_weeks=52, seed=42, model_dir=None):
    """Which drug to give each week: the RL agent against fixed schedules.

    The agent (PPO) was trained on the cycling simulation for ciprofloxacin,
    gentamicin and imipenem; ``antibiotic`` is the first drug, the other two
    are the alternatives. It learned from simulated episodes, not patients.

    Args:
        antibiotic: One of the agent's drugs, case-insensitive.
        n_weeks: Weeks to plan, 1 to 104 (its training horizon).
        seed: Seed of the simulated episode.
        model_dir: Override the bundled artifacts.

    Returns:
        dict with ``drugs``, ``policies`` (the agent and each baseline: the drug
        per week, resistance curves, ``failure_week``, ``total_reward``) and
        ``best``; or a dict with ``error``.
    """
    from .amr_constants import normalize_antibiotic
    agent = registry.rl(model_dir)
    if agent is None:
        return {'error': 'the RL agent is not bundled'}
    n_weeks = int(n_weeks)
    if not 1 <= n_weeks <= agent.train_weeks:
        return {'error': f'n_weeks must be from 1 to {agent.train_weeks}'}
    block = agent.block(normalize_antibiotic(antibiotic), n_weeks, seed=seed)
    return block or {'error': f'the RL agent was trained on {", ".join(agent.drugs)} only'}


def simulate_timeline(fasta_text, antibiotic, *, n_weeks=8, seed=42, model_dir=None):
    """Simulate week-by-week resistance evolution under antibiotic pressure.

    This is a biological simulation, not a trained model — it carries no AUC
    or accuracy score. Treat its output as illustrative. The same inputs and
    seed give the same output, and the three shares sum to 100 every week.
    For a trained forecast of yearly resistance, use ``forecast_trend``.

    Args:
        fasta_text: FASTA contents as a string.
        antibiotic: Antibiotic name, case-insensitive.
        n_weeks: Number of weeks to project.
        seed: Seed for the random parts (mutation counts and types).
        model_dir: Override the bundled artifacts.

    Returns:
        dict with a ``weeks`` series, mutation events and gene activations.
    """
    return registry.timeline(model_dir).predict(fasta_text, antibiotic, n_weeks, seed=seed)


def antibiotics(model='genome', model_dir=None):
    """Sorted antibiotic names a model was trained on.

    Args:
        model: ``'genome'`` (``predict_fasta``), ``'forecast'`` (``forecast``),
            ``'trend'`` (``forecast_trend``) or ``'rl'`` (``plan_treatment``).
    """
    if model == 'genome':
        return registry.genome_kmers(model_dir).ab_list
    if model == 'forecast':
        return sorted(registry.lgbm(model_dir).vocabulary.get('antibiotics') or [])
    if model == 'trend':
        return sorted({ab for drugs in trend_series(model_dir).values() for ab in drugs})
    if model == 'rl':
        agent = registry.rl(model_dir)
        return sorted(agent.drugs) if agent else []
    raise ValueError("model must be 'genome', 'forecast', 'trend' or 'rl'")


def status(model_dir=None):
    """Report which models loaded, keyed by model name, with their measured
    test metrics where they have them."""
    agent = registry.rl(model_dir)
    return {
        'version': __version__,
        'lgbm_forecasting': registry.lgbm(model_dir).status,
        'genome_resistance': registry.genome(model_dir).status,
        'trend_forecast': registry.trend(model_dir).status,
        'rl_agent': {'trained': agent is not None,
                     'model_type': agent.label if agent else None,
                     'drugs': agent.drugs if agent else [],
                     'description': 'Plans which drug to give each week; trained on the simulation'},
        'mutation_timeline': registry.timeline(model_dir).status,
    }


def __getattr__(name):
    # Re-export the classes without importing numpy/pandas/lightgbm at import time.
    if name == 'LGBMResistancePredictor':
        from .lgbm import LGBMResistancePredictor
        return LGBMResistancePredictor
    if name == 'GenomeModelPredictor':
        from .genome import GenomeModelPredictor
        return GenomeModelPredictor
    if name == 'TimelineMLForecaster':
        from .timeline_ml import TimelineMLForecaster
        return TimelineMLForecaster
    if name == 'RLAgent':
        from .rl_agent import RLAgent
        return RLAgent
    if name == 'MutationTimelinePredictor':
        from .timeline import MutationTimelinePredictor
        return MutationTimelinePredictor
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
