# Known issues

Read this before quoting numbers from this library in a report or thesis.

---

## Fixed in 0.3.0

### `predict_fasta()` carried the July k-mer model

**Severity: high. Fixed in 0.3.0.**

Up to 0.2.0, `predict_fasta()` was the July RandomForest on 4-mers of a
genome's first 500,000 bp: AUC 0.981 on genomes it trained on but **0.695** on
genomes it never saw. 0.3.0 ships the web app's genome models with the code
ported from `backend/ml_models/genome_predictor.py`: the gene model (lab AUC
0.977 on 4,481 unseen genomes) when AMRFinderPlus is installed, the k-mer
LightGBM (0.935) otherwise. A backend test (`test_library_parity.py`) checks
the library and the web app give identical answers. The RandomForest, its
scaler bug (below) and the scikit-learn pin are gone with it.

### scikit-learn version drift

**Severity: medium. Resolved in 0.3.0.** Only the RandomForest was a pickled
scikit-learn estimator; the bundled models are now LightGBM text files and
NumPy arrays, and scikit-learn is no longer a dependency.

### Model metrics are not shipped

**Severity: low. Fixed.** Every trained model carries its measured test
metrics (`lgbm_metrics.json`, `genome_metrics.json`, `timeline_metrics.json`),
returned by `status()`.

---

## Fixed in 0.2.0

### `forecast()` disagreed with the web app

**Severity: high. Fixed in 0.2.0.**

0.1.0 bundled the July model and its own loader. The web app's loader had
since gained isotonic calibration, species-level Taxon IDs, the promoted run's
threshold and drug-class map, and the shared antibiotic-name table, so the same
input gave a different probability (uncalibrated) and could give a different
call (fixed 0.40 threshold) than `/forecast`. 0.2.0 ships the served model
(`D3_forecaster_deploy_v7`) with `lgbm.py` ported from
`backend/ml_models/lgbm_predictor.py` and the names from a copy of
`backend/amr_constants.py` (a backend test fails if the copy goes stale).
Checked: identical probabilities and calls to the backend on the same inputs.

---

## Fixed during extraction

### The k-mer model never actually ran

**Severity: high. Fixed in 0.1.0.**

`extract_features()` builds a 321-element vector (256 k-mer frequencies + 62
antibiotic one-hot + 3 composition features). But training fitted the
`StandardScaler` on the **k-mer block alone**:

```python
# train_models.py
n_kmer = len(ALL_KMERS)                                      # 256
X_train[:, :n_kmer] = scaler.fit_transform(X_train[:, :n_kmer])
```

Inference passed the whole 321-element vector to that 256-feature scaler:

```python
feat = self.scaler.transform(feat.reshape(1, -1))[0]   # ValueError
```

Every call raised `X has 321 features, but StandardScaler is expecting 256`.
The exception was caught by a broad `except Exception` and silently replaced
with `_heuristic_predict()` — a GC-content formula that adds
`np.random.uniform(-0.04, 0.04)` noise.

Consequences while the bug was live:

- The RandomForest never produced a single prediction.
- Results were **random**: identical input gave different answers each call.
- The response still reported `'model_used': 'RandomForest K-mer (trained)'`,
  because `is_trained` was `True` — only *prediction* failed, not loading.
- Any k-mer accuracy figure measured through this path is meaningless.

The fix scales only the k-mer columns:

```python
feat[:N_KMERS] = self.scaler.transform(feat[:N_KMERS].reshape(1, -1))[0]
```

`test_kmer_model_actually_runs` and `test_predict_is_deterministic` guard it.

The same fix was applied in the backend. (0.3.0 removed this model.)

### Library printed to stdout

**Severity: medium. Fixed in 0.1.0.**

The predictors used `print()` for diagnostics, which corrupted JSON output and
broke `amrpredict antibiotics | jq`. All converted to `logging`; load failures
and prediction errors are now `warning` level.

---

### Timeline compartments could exceed 100% (fixed 2026-09-29)

In `simulate_timeline()` the three population shares stopped partitioning the
population once the susceptible pool emptied (week 8 summed to 106.08, with
intermediate pinned at 25.0). The intermediate share is now capped by the
non-resistant share and susceptible takes the remainder, so every week sums to
exactly 100. The same fix has been in the backend since 2026-09-26. The strict
`xfail` on `test_timeline_compartments_partition_the_population_throughout` is
gone: the test now has to pass. The simulation is also seeded (`seed=42` by
default), so the same inputs give the same output, and `model_used` is always
`Biological Simulation`.

## Open

### `*_fraction` fields are percentages

**Severity: low. Open.**

`resistant_fraction`, `susceptible_fraction` and `intermediate_fraction` are
on a 0–100 scale, not 0–1. Renaming them would break the Django frontend
templates, so the names stand and the docs state the scale.

### The timeline is not validated

**Severity: informational.**

`simulate_timeline()` is a deterministic biological simulation. Its growth
parameters are set by hand; its curve shape has been checked against published
resistance-evolution curves (`calibration` in its output), but its weeks are
illustrative. For a forecast trained on data, use `forecast_trend()`. `status()` reports
`trained: False` for it. Treat its output as illustrative.
