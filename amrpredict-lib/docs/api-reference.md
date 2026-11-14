# API reference

All public functions live on the `amrpredict` top-level module. Every one takes
an optional `model_dir` to override the bundled artifacts.

---

## `forecast(antibiotic, *, ...)`

Resistance from organism metadata and MIC values, via LightGBM.

**Parameters**

| Name | Type | Default | Meaning |
|---|---|---|---|
| `antibiotic` | `str` | — | Antibiotic name, case-insensitive. Positional. |
| `taxon_id` | `int` | `None` | NCBI taxonomy ID, e.g. `562` (*E. coli*). |
| `mic_value` | `float` | `None` | Minimum inhibitory concentration, mg/L. |
| `mic_sign` | `str` | `None` | MIC comparator: `'='`, `'>'`, `'<='`, … |
| `genus` | `str` | `'unknown'` | e.g. `'Escherichia'`. |
| `species` | `str` | `'unknown'` | e.g. `'coli'`. |
| `threshold` | `float` | `None` | Probability at/above which the call is Resistant. `None`: the bundled model's own threshold (`status()['lgbm_forecasting']['default_threshold']`, 0.15). |
| `model_dir` | `str` | `None` | Directory of alternative artifacts. |

**Returns** `dict`

| Key | Type | Meaning |
|---|---|---|
| `prediction` | `str` | `'Resistant'` or `'Susceptible'` |
| `probability` | `float` | Probability of resistance, 0–1, calibrated when the model carries a calibration |
| `confidence` | `float` | Confidence in the call, **percent** |
| `antibiotic` | `str` | Echoed, lowercased |
| `drug_class` | `str` | e.g. `'fluoroquinolone'`, or `'other'` if unrecognised |
| `model_used` | `str` | `'LightGBM (trained)'` |
| `threshold` | `float` | The threshold used |
| `model_run` | `str` | Experiment run the bundled model came from |
| `calibrated` | `bool` | Whether `probability` went through the calibration |
| `evidence` | `dict` | Per input: used, missing or not recognised, and the estimate's level (`full`, `mic`, `organism`, `drug_only`) |

**Notes**

- Unknown antibiotics do not raise; `drug_class` becomes `'other'` and the
  model falls back to population-level rates.
- Deterministic: identical inputs give identical output.

```python
amrpredict.forecast('meropenem', taxon_id=287, mic_value=8, genus='Pseudomonas')
```

---

## `predict_fasta(fasta_text, antibiotic, *, ...)`

Resistance from a complete genome assembly: the gene model (LightGBM on the
resistance genes and mutations NCBI AMRFinderPlus finds; lab AUC 0.977) when
the `amrfinder` program is installed, else the k-mer model (LightGBM on 4-mer
frequencies; lab AUC 0.935). The same code and models as the web app's
`/predict`.

**Parameters**

| Name | Type | Default | Meaning |
|---|---|---|---|
| `fasta_text` | `str` | — | FASTA contents; every contig is read |
| `antibiotic` | `str` | — | Antibiotic name, case-insensitive |
| `threshold` | `float` | `None` | Probability at/above which the call is Resistant; `None` = the model's own (k-mer 0.43, gene 0.58) |
| `genus`, `species` | `str` | `None` | The organism, if known |
| `use_genes` | `bool \| None` | `None` | `None`: gene model if AMRFinderPlus is installed; `False`: always the k-mer model; `True`: require the gene model |
| `model_dir` | `str` | `None` | Directory of alternative artifacts |

**Returns** `dict` — on success:

| Key | Type | Meaning |
|---|---|---|
| `prediction` | `str` | `'Resistant'` or `'Susceptible'` |
| `probability` | `float` | 0–1 |
| `confidence` | `float` | Percent |
| `threshold` | `float` | The threshold used |
| `antibiotic`, `antibiotic_known` | `str`, `bool` | Canonical name; whether the model was trained on it |
| `sequence_length` | `int` | ACGT bases read |
| `gc_content` | `float` | **Percent** |
| `model_used`, `model_run` | `str` | e.g. `'LightGBM on 4-mers (G_kmer_deploy)'` |
| `top_kmers` | `list[dict]` | k-mer model: ten most frequent 4-mers, `{'kmer', 'frequency'}` |
| `genes_found` | `list[dict]` | Gene model: every core AMR gene and mutation, `relevant` when its class covers the drug |
| `species_detected` | `dict` | Gene model: species from the 6-mer profile, and the `--organism` given to AMRFinderPlus |
| `warning` | `str` | AMRFinderPlus failed on this genome and the k-mer model answered |

On invalid input it returns `{'error': str, ...}` instead — **with no
`prediction` key**. Always check:

```python
r = amrpredict.predict_fasta(text, 'ciprofloxacin')
if 'error' in r:
    ...
```

**Input handling**

| Input | Behaviour |
|---|---|
| Lowercase bases | Counted as uppercase |
| `N`, `R`, `Y`, other ambiguity codes | Not counted; k-mers spanning them are skipped |
| Multiple records (contigs) | k-mers counted inside each contig, as in training |
| No `>` header | Accepted |
| Under 100,000 bp | Error dict: upload a complete assembly |

AMRFinderPlus is configured through the environment: `AMRFINDER_PATH`,
`AMRFINDER_THREADS` (4), `AMRFINDER_TIMEOUT` (100 s) and `AMRFINDER_DATABASE`
(training used database `2026-08-07.1`).

---

## `identify_species(fasta_text, *, model_dir=None)`

Species and genus of a complete genome: the nearest of 99 reference profiles
by cosine distance of 6-mer frequencies (right species for 98.0%, right genus
for 99.8% of held-out genomes). Returns `{'species', 'genus', 'distance'}`;
`species` and `genus` are `None` when no reference is within 0.01. Under
100,000 bp: an error dict.

---

## `forecast_trend(genus, antibiotic, *, years_ahead=5, model_dir=None)`

The timeline ML model: a genus's yearly share of resistant isolates in BV-BRC
laboratory results, and LightGBM's forecast for the next `years_ahead` years
(1 to 10), made one year at a time. The same code and model as the web app's
`/timeline` "ML trend forecast".

**Returns** `dict`

| Key | Type | Meaning |
|---|---|---|
| `organism`, `antibiotic` | `str` | As the series spell them |
| `history` | `list[dict]` | `year`, `resistant_pct`, `n` (lab results that year, at least 20) |
| `forecast` | `list[dict]` | `year`, `resistant_pct`, `lo`, `hi` (80% band, widening as √years) |
| `metrics` | `dict` | Held-out mean absolute error (percentage points, with CI) of the model and of the baselines `last_value`, `linear_trend`, `historical_mean` |
| `label`, `model_run` | `str` | What to call the forecast; the run |

A pair with fewer than two years of history returns `{'error': str}`.

## `trend_series(model_dir=None)`

`{genus: [antibiotic, ...]}`: every pair `forecast_trend` can forecast.

---

## `plan_treatment(antibiotic, *, n_weeks=52, seed=42, model_dir=None)`

Which drug to give each week, from a PPO agent trained on the project's cycling
simulation, compared with fixed schedules on the same simulated episode. The
same agent as the `rl` block of the web app's `/timeline`.

> **Trained on a simulation, not patient data.** Use it to explore cycling
> strategies, not to treat patients.

`antibiotic` (ciprofloxacin, gentamicin or imipenem) comes first; the other two
are the alternatives. `n_weeks`: 1 to 104, the agent's training horizon.

**Returns** `dict`

| Key | Type | Meaning |
|---|---|---|
| `drugs` | `list[str]` | The three drugs, the requested one first |
| `policies` | `list[dict]` | The agent (`name: 'rl'`) then each baseline: `policy` (drug per week), `resistant_fraction` (percent per drug per week), `failure_week` (`None` = never), `effective_weeks`, `total_reward`, `mean_burden` |
| `best` | `str` | The policy that fails latest, then the highest reward |
| `agent`, `n_weeks` | `str`, `int` | |

Another drug, or weeks outside 1–104, returns `{'error': str}`.

---

## `simulate_timeline(fasta_text, antibiotic, *, ...)`

Week-by-week resistance evolution under sustained antibiotic pressure.

> **This is a simulation, not a trained model.** It has no AUC or accuracy
> score. Do not present its output as a prediction.

**Parameters**

| Name | Type | Default | Meaning |
|---|---|---|---|
| `fasta_text` | `str` | — | FASTA contents |
| `antibiotic` | `str` | — | Antibiotic name |
| `n_weeks` | `int` | `8` | Weeks to project |
| `seed` | `int` | `42` | Seed for the random parts; same inputs and seed, same output |
| `model_dir` | `str` | `None` | Alternative artifacts |

**Returns** `dict`

| Key | Type | Meaning |
|---|---|---|
| `timeline` | `list[dict]` | **`n_weeks + 1`** entries; week 0 is baseline |
| `mutation_hotspots` | `list[dict]` | `position`, `original`, `mutated`, `type` |
| `resistance_genes` | `list[dict]` | Gene, activation week, contribution |
| `failure_week` | `int \| None` | First week treatment is ineffective |
| `final_resistant_percent` | `float` | Resistance at the last week |
| `peak_resistance` | `float` | Maximum across the run |
| `antibiotic_class` | `str` | Drug class |
| `gc_content` | `float` | Percent |
| `summary` | `str` | Human-readable description |
| `model_used` | `str` | Always `Biological Simulation` |
| `simulation`, `seed` | `bool`, `int` | `True`, and the seed used |
| `calibration` | `dict \| None` | Fit against published curves, from `timeline_calibration.json` |

Each `timeline` entry:

| Key | Type | Meaning |
|---|---|---|
| `week` | `int` | 0-indexed |
| `resistant_fraction` | `float` | **Percent (0–100)**, despite the name |
| `susceptible_fraction` | `float` | Percent |
| `intermediate_fraction` | `float` | Percent; the three shares sum to 100 every week |
| `cumulative_mutations` | `int` | Mutations accumulated |
| `mic_fold_change` | `float` | MIC multiple vs baseline |
| `treatment_effective` | `bool` | Whether treatment still works |

See [Known issues](known-issues.md) for why the fraction fields hold percentages.

---

## `antibiotics(model='genome', model_dir=None)`

Sorted `list[str]` of the antibiotics a model was trained on: `'genome'`
(`predict_fasta`, 111), `'forecast'` (`forecast`), `'trend'`
(`forecast_trend`) or `'rl'` (`plan_treatment`). `forecast()` and
`predict_fasta()` accept other names too, with less to go on.

---

## `status(model_dir=None)`

`dict` with `version` plus a block per model — `lgbm_forecasting`,
`genome_resistance`, `trend_forecast`, `rl_agent`, `mutation_timeline` —
carrying `trained`, `model_type` and `description`. Useful as a health check.
The trained models' blocks also have `run_id` and `metrics` (their measured
test numbers); `genome_resistance` says whether it `searches_genes`.

---

## `registry`

Lazy, process-wide predictor cache.

```python
amrpredict.registry.lgbm()          # shared LGBMResistancePredictor
amrpredict.registry.genome()        # shared GenomeModelPredictor (gene model if possible)
amrpredict.registry.genome_kmers()  # the k-mer genome model
amrpredict.registry.trend()         # shared TimelineMLForecaster
amrpredict.registry.rl()            # shared RLAgent
amrpredict.registry.timeline()      # shared MutationTimelinePredictor
amrpredict.registry.reset()         # drop them, freeing memory
```

Passing `model_dir` bypasses the cache and builds a fresh instance.

---

## Classes

For direct control, the underlying classes are exported:

```python
from amrpredict import LGBMResistancePredictor

p = LGBMResistancePredictor()                 # bundled models
p = LGBMResistancePredictor('/custom/dir')    # or your own

p.predict('ciprofloxacin', taxon_id=562)
p.batch_predict([{'antibiotic': 'ciprofloxacin', 'taxon_id': 562}, ...])
p.status          # a property, not a method
```

`GenomeModelPredictor`, `TimelineMLForecaster` and `MutationTimelinePredictor`
follow the same shape: construct with an optional `model_dir`, call
`.predict(...)` (`.forecast(genus, antibiotic)` for the trend model), read
`.status`. `RLAgent(folder).block(antibiotic, n_weeks)` gives the plan.

> `.status` is a **property**. Calling `.status()` raises `TypeError`.

---

## `default_model_dir()`

Absolute path to the bundled artifacts — useful for copying them out as a
starting point for retraining.
