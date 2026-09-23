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
| `threshold` | `float` | `0.40` | Probability at/above which the call is Resistant. |
| `model_dir` | `str` | `None` | Directory of alternative artifacts. |

**Returns** `dict`

| Key | Type | Meaning |
|---|---|---|
| `prediction` | `str` | `'Resistant'` or `'Susceptible'` |
| `probability` | `float` | Probability of resistance, 0–1 |
| `confidence` | `float` | Confidence in the call, **percent** |
| `antibiotic` | `str` | Echoed, lowercased |
| `drug_class` | `str` | e.g. `'fluoroquinolone'`, or `'other'` if unrecognised |
| `model_used` | `str` | `'LightGBM (trained)'` |
| `threshold` | `float` | Echoed |

**Notes**

- Unknown antibiotics do not raise; `drug_class` becomes `'other'` and the
  model falls back to population-level rates.
- Deterministic: identical inputs give identical output.

```python
amrpredict.forecast('meropenem', taxon_id=287, mic_value=8, genus='Pseudomonas')
```

---

## `predict_fasta(fasta_text, antibiotic, *, ...)`

Resistance from genome composition, via RandomForest on 4-mer frequencies.

**Parameters**

| Name | Type | Default | Meaning |
|---|---|---|---|
| `fasta_text` | `str` | — | FASTA contents. Headers optional. |
| `antibiotic` | `str` | — | Antibiotic name, case-insensitive. |
| `threshold` | `float` | `0.5` | Probability at/above which the call is Resistant. |
| `model_dir` | `str` | `None` | Directory of alternative artifacts. |

**Returns** `dict` — on success:

| Key | Type | Meaning |
|---|---|---|
| `prediction` | `str` | `'Resistant'` or `'Susceptible'` |
| `probability` | `float` | 0–1 |
| `confidence` | `float` | Percent |
| `sequence_length` | `int` | Cleaned length in bp, after stripping non-ACGT |
| `gc_content` | `float` | **Percent** |
| `top_kmers` | `list[dict]` | Ten most frequent 4-mers, `{'kmer', 'frequency'}` |
| `model_used` | `str` | `'RandomForest K-mer (trained)'` |

On invalid input it returns `{'error': str, 'sequence_length': int}` instead —
**with no `prediction` key**. Always check:

```python
r = amrpredict.predict_fasta(text, 'ciprofloxacin')
if 'error' in r:
    ...
```

**Input handling**

| Input | Behaviour |
|---|---|
| Lowercase bases | Uppercased |
| `N`, `R`, `Y`, other ambiguity codes | Silently discarded |
| Multiple records | Concatenated |
| No `>` header | Accepted |
| Over 500,000 bp | Truncated |
| Under 100 bp after cleaning | Error dict |

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

Each `timeline` entry:

| Key | Type | Meaning |
|---|---|---|
| `week` | `int` | 0-indexed |
| `resistant_fraction` | `float` | **Percent (0–100)**, despite the name |
| `susceptible_fraction` | `float` | Percent |
| `intermediate_fraction` | `float` | Percent — constant at 25.0 |
| `cumulative_mutations` | `int` | Mutations accumulated |
| `mic_fold_change` | `float` | MIC multiple vs baseline |
| `treatment_effective` | `bool` | Whether treatment still works |

See [Known issues](known-issues.md) for the naming and the >100% sum.

---

## `antibiotics(model_dir=None)`

Sorted `list[str]` of the 62 antibiotics the k-mer model was trained on.
`forecast()` accepts names outside this list; `predict_fasta()` will one-hot
them as all-zero.

---

## `status(model_dir=None)`

`dict` with `version` plus a per-model block carrying `trained`, `model_type`
and `description`. Useful as a health check.

---

## `registry`

Lazy, process-wide predictor cache.

```python
amrpredict.registry.lgbm()       # shared LGBMResistancePredictor
amrpredict.registry.kmer()       # shared KmerResistancePredictor
amrpredict.registry.timeline()   # shared MutationTimelinePredictor
amrpredict.registry.reset()      # drop them, freeing memory
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

`KmerResistancePredictor` and `MutationTimelinePredictor` follow the same
shape: construct with an optional `model_dir`, call `.predict(...)`, read
`.status`.

> `.status` is a **property**. Calling `.status()` raises `TypeError`.

---

## `default_model_dir()`

Absolute path to the bundled artifacts — useful for copying them out as a
starting point for retraining.
