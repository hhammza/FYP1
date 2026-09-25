# experiments/

A dedicated training ground for new AMR models. Nothing here writes to
`backend/trained_models/`, so the served models are never disturbed by an
experiment. Promoting a model is a separate copy step, described at the bottom.

Implements the protocol in [EXPERIMENT_PLAN.md](../EXPERIMENT_PLAN.md).

**[HANDBOOK.md](HANDBOOK.md)** is the full account, every data field, every
cleaning step, what happens during a run, all algorithms and metrics, and what
the runs so far have shown. This file is the short usage card, and
[CHANGES.md](../CHANGES.md) is the change history.

## Quick start

```bash
# one experiment
python experiments/run.py experiments/configs/A2_oof_grouped.json

# every config in configs/
python experiments/run.py --all

# comparison table across all runs so far
python experiments/report.py
python experiments/report.py --out experiments/RESULTS.md

# the weakest antibiotics for one run
python experiments/report.py --per-antibiotic A2_oof_grouped

# refresh the web app's /models and /compare pages
python experiments/evaluate_shipped.py   # only after retraining the app's models
python experiments/export_report.py
```

First run reads 3,655 CSVs from `data/amr_output/` (~20 s) and caches the
cleaned frame in `cache/`; later runs start from the cache. A LightGBM run over
the full 1.5 M rows takes about a minute on this machine.

## Layout

```
experiments/
├── configs/            one JSON per experiment, the full description of a run
├── algorithms/         ONE FILE PER ALGORITHM, the training code
│   ├── base.py                 the fit/predict/save contract + shared preprocessing
│   ├── lightgbm_model.py       "type": "lightgbm"
│   ├── logistic_model.py       "type": "logistic"
│   ├── random_forest_model.py  "type": "random_forest"
│   ├── xgboost_model.py        "type": "xgboost"
│   ├── catboost_model.py       "type": "catboost"
│   └── __init__.py             REGISTRY + build_model() dispatcher
├── lib/
│   ├── data_prep.py    raw CSV → clean modelling table (cached)
│   ├── splits.py       random / grouped / species-holdout splitting
│   ├── encoders.py     target encoding: none | leaky | oof
│   ├── metrics.py      AUC, AUPRC, VME/ME, Brier, bootstrap CIs
│   └── profile.py      size, organism and label mix of a training set
├── run.py              runs one config end to end
├── report.py           registry.csv → Markdown
├── predict.py          load a saved model and predict with it
├── evaluate_shipped.py re-test the deployed models on genomes they never saw
├── build_taxonomy.py   Taxon ID → species via NCBI → backend/taxon_species.csv
├── export_report.py    everything above → backend/trained_models/model_report.json
├── backfill_bundles.py adds bundles to runs made before the exporter existed
├── cache/              cleaned-data cache (safe to delete)
└── results/
    ├── registry.csv    one row per run, the comparison table
    ├── shipped_eval.json  deployed models re-tested, written by evaluate_shipped.py
    └── <run_id>/
        ├── metrics.json          every metric, plus per-antibiotic breakdown
        ├── predictions.csv       y_true, y_score, genome_id, antibiotic
        ├── config.snapshot.json  exactly what produced this
        └── model/
            ├── model.txt             the trained artifact
            ├── rate_tables.joblib    rate lookups from THIS run's training rows
            └── feature_meta.json     feature order, category levels, threshold
```

Every trained model is kept under `results/<id>/model/`, and all three files are
needed to predict, the booster alone would look up resistance rates it was
never trained against. Reload one with:

```bash
python experiments/predict.py --list
python experiments/predict.py A2_oof_grouped --antibiotic ciprofloxacin --mic 8
```

## Writing a config

A config is the entire description of a run, change one field, get one
comparable result.

```json
{
  "id": "A5_catboost",
  "description": "CatBoost with ordered target statistics",
  "data": {
    "source": "amr_output",
    "normalize_antibiotics": true,
    "label_sources": ["lab"],
    "min_rows_per_antibiotic": 200,
    "sample_rows": 400000
  },
  "split":    { "strategy": "grouped", "test_size": 0.2, "seed": 42 },
  "features": { "target_encoding": "oof", "drop": ["mic_sign"] },
  "model":    { "type": "catboost", "params": { "depth": 8 } },
  "threshold":{ "strategy": "vme_constrained", "vme_budget": 0.03 }
}
```

| Field | Options |
|---|---|
| `split.strategy` | `grouped` (default, no genome on both sides), `random` (reproduces the old pipeline), `species_holdout` (+ `holdout_genus`) |
| `features.target_encoding` | `oof` (correct), `leaky` (reproduces the bug, for comparison), `none` |
| `features.drop` | feature names to remove, this is how ablations are expressed |
| `model.type` | `lightgbm`, `logistic`, `random_forest`, `xgboost`*, `catboost`* |
| `model.monotone_on` | LightGBM only, features whose effect must be non-decreasing |
| `threshold.strategy` | `fixed`, `maximize_f1`, `vme_constrained` |
| `data.label_sources` | `["lab"]`, `["computational"]`, or both |

\* needs `pip install xgboost` / `catboost`; the run exits with that hint if missing.

## Adding an algorithm

Each algorithm is a self-contained file under `algorithms/`. Write a class with
four methods - `fit(X_tr, y_tr, X_val, y_val, cat_features)`, `predict_proba(X)`,
`save(path)` and an `info` property, then add one line to `REGISTRY` in
`algorithms/__init__.py`:

```python
REGISTRY = {
    ..
    'my_model': MyModel,
}
```

It is immediately usable from any config via `{"model": {"type": "my_model"}}`.
`run.py` does not change, so every earlier result stays comparable.

## The web report

The app's `/models` and `/compare` pages read
`backend/trained_models/model_report.json`, which is committed so the deployed
backend can serve it. Two scripts build it:

| Script | Reads | Writes | Time |
|---|---|---|---|
| `evaluate_shipped.py` | `backend/trained_models/`, `data/amr_output/`, `data/mapped_output/`, `data/fasta_output/` | `results/shipped_eval.json` | about 2 min |
| `export_report.py` | `results/registry.csv`, each run's `metrics.json`, `config.snapshot.json` and `predictions.csv`, `results/shipped_eval.json`, the data cache | `backend/trained_models/model_report.json` (about 40 KB) | about 1 min |

`evaluate_shipped.py` reconstructs what the deployed models trained on.
`train_models.py` reads the first 500 `amr_output` files and the first 200
`mapped_output` files of a directory listing, which was alphabetical on the
machine that trained them. The script checks this against the artifacts (same
antibiotics, same genera, same stored resistance rate) and prints the result,
then scores each model on every genome outside those files.

`export_report.py` needs the `predictions.csv` files for ROC curves; they are
not committed, so run it on a machine where the experiments were run. Run
groups on the page (best model, algorithm comparison and so on) come from the
`GROUPS` table at the top of the script; add new run ids there.

## Rules the harness enforces

- **The test set is split once** and never used for fitting, early stopping or
  threshold choice. Thresholds come from a validation fold.
- **Genomes never straddle the split** under `grouped`, the run prints the
  overlap count so it is visible when it is not zero.
- **Encodings are fitted on training folds only** under `oof`.
- **Confidence intervals resample genomes, not rows**, since ~12 rows share a
  genome and row resampling would give a misleadingly tight interval.
- **Categories are aligned** between train and test, so a string means the
  same integer on both sides.
- **Metrics land next to the model** in `metrics.json`, no hand-transcribed
  numbers.

## Promoting a model to the app

Experiments never overwrite the served artifacts. When a run earns deployment:

```bash
cp experiments/results/<run_id>/model/model.txt \
   backend/trained_models/amr_lgbm_final_model.txt
cp experiments/results/<run_id>/metrics.json \
   backend/trained_models/metrics.json
```

The serving predictor also needs the three rate lookup tables
(`ab_rate_full.joblib`, `taxon_ab_rate_full.joblib`, `genus_ab_rate_full.joblib`)
and `lgbm_meta.joblib`. Those lookups now ship with each run in
`model/rate_tables.joblib`, but under different names and in a different shape
than the backend expects, so they need converting before promotion, otherwise
the served model looks up rates that do not match what it was trained on.
Restart the backend or `POST /api/reload/` afterwards.
