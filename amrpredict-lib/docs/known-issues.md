# Known issues

Read this before quoting numbers from this library in a report or thesis.

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

**This bug also exists in the main Django backend**, in
`backend/ml_models/resistance_predictor.py`. Applying the same one-line change
there is required for the web app's `/predict` page to use the real model.

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

### scikit-learn version drift

**Severity: medium. Mitigated.**

`kmer_resistance_model.pkl` was pickled with scikit-learn **1.6.1**. Loading it
under a different 1.x works but emits `InconsistentVersionWarning`, and the
maintainers make no guarantee the numbers are identical.

Mitigated in 0.2.0 by pinning `scikit-learn>=1.6.1,<1.7` (0.1.0 allowed any
1.x). The durable fix is retraining and saving via
[skops](https://skops.readthedocs.io/) or ONNX.

LightGBM is unaffected — its text format is version-stable.

### Model metrics are not shipped

**Severity: low. Fixed in 0.2.0 for the forecaster.** `models/lgbm_metrics.json`
is written by `experiments/promote.py --library` and returned by `status()`.
The k-mer model still has none in the package (the web app's re-test is in
`backend/trained_models/kmer_metrics.json`).

`train_models.py` computes AUC and a classification report, prints them, and
discards them. No metrics are stored in the artifacts, so the library cannot
report the accuracy of the models it carries, and any figure quoted elsewhere
is manually transcribed and can drift silently after a retrain.

Fix: have training write `metrics.json` alongside the models and expose it
through `status()`.

### The timeline is not validated

**Severity: informational.**

`simulate_timeline()` is a deterministic biological simulation. Its growth
parameters are not fitted to data and its output has never been compared
against published resistance-evolution curves. `status()` reports
`trained: False` for it. Treat its output as illustrative.
