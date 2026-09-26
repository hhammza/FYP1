# Experiment Handbook

*The training setup in `experiments/`: where the data comes from, what every field means, what happens during a run, which algorithms are available, how results are measured, and what the 22 runs have shown.*

Last updated 2026-09-24 against the code in this folder. [README.md](README.md) is the short usage card; this is the full reference. [CHANGES.md](../CHANGES.md) records how both got here.

---

## Contents

1. [What this folder is](#1-what-this-folder-is)
2. [The pipeline, end to end](#2-the-pipeline-end-to-end)
3. [The data](#3-the-data)
4. [Field reference](#4-field-reference)
5. [The feature set](#5-the-feature-set)
6. [What happens during a run](#6-what-happens-during-a-run)
7. [Algorithms](#7-algorithms)
8. [Metrics](#8-metrics)
9. [Config reference](#9-config-reference)
10. [Results so far](#10-results-so-far)
11. [What the results mean](#11-what-the-results-mean)
12. [File reference](#12-file-reference)
13. [Limitations of this harness](#13-limitations-of-this-harness)

---

## 1. What this folder is

A separate training ground for the **tabular resistance forecaster**, the model behind the `/forecast` page. It exists so that new models can be trained and compared without touching `backend/trained_models/`, which is what the running app serves.

Three properties it guarantees, none of which the original `backend/train_models.py` provides:

- **Every run is fully described by a JSON config.** Change one field, get one comparable result. No editing training code per experiment.
- **The evaluation protocol is fixed and enforced.** Test data is split once and never used for fitting, early stopping or threshold choice. Encodings are fitted on training folds only. Genomes never straddle the split.
- **Every run leaves an audit trail.** Metrics, raw predictions, the config that produced them, and the model artifact all land in one folder, plus a row in a registry that forms the comparison table.

It does **not** cover the k-mer genome model or the timeline simulation. Those are Tracks B and C in [EXPERIMENT_PLAN.md](../EXPERIMENT_PLAN.md) and not built yet.

---

## 2. The pipeline, end to end

```
data/amr_output/*.csv                 3,655 files, 2,986,755 rows
        │
        │  lib/data_prep.py, parse MIC, split organism name, normalise drug
        │  names, map phenotype to 0/1, tag provenance, deduplicate
        ▼
cache/clean_v1_amr_output_norm.pkl    1,525,796 rows × 14 columns
        │
        │  lib/splits.py, grouped / random / species-holdout
        ▼
   train (80%)                                    test (20%)
        │                                              │
        │  lib/encoders.py, out-of-fold rate features │  (mapped from train)
        ▼                                              │
   fit (83%) ── val (17%)                              │
        │          │                                   │
        │          │ early stopping + threshold        │
        ▼          ▼                                   ▼
   algorithms/<algo>.py ────────────────────► lib/metrics.py
        │                                              │
        ▼                                              ▼
 results/<id>/model/                    results/<id>/metrics.json
                                        results/<id>/predictions.csv
                                        results/registry.csv
```

---

## 3. The data

### 3.1 Source

| Path | What it is |
|---|---|
| `data/amr_output/*.csv` | 3,655 per-species AMR phenotype exports from **BV-BRC** (formerly PATRIC), one file per taxon, e.g. `amr_taxon_562_Escherichia_coli.csv`. **This is what the harness reads.** |
| `data/BVBRC_genome_amr.csv` | A single 30 MB export, the source used by `LightGBM_Model_Improved.ipynb`. Not used here. |
| `data/mapped_output/*.csv` | The same rows joined to FASTA paths by `fasta_amr_map.py`. For the genome model (Track B). |
| `data/fasta_output/taxon_*/` | 4 GB of genome assemblies. Track B. |
| `data/sample_*` | Small fixtures for notebook development. **Not a representative sample**, do not train on them. |

### 3.2 Cleaning, step by step

Implemented in [`lib/data_prep.py`](lib/data_prep.py) `clean()`. Row counts are from the current run:

| # | Step | Effect |
|---|---|---|
| 1 | Concatenate all 3,655 CSVs | 2,986,755 rows |
| 2 | Parse `Measurement` into `mic_sign` + `mic_value`; fall back to `Measurement Value` | adds 3 columns |
| 3 | Split `Genome Name` into `genus` + `species` | adds 2 columns |
| 4 | Lower/strip `Antibiotic`, apply alias map, drop non-drugs | removes `carbapenem` etc. |
| 5 | Map `Resistant Phenotype` to a binary target; drop rows with no usable phenotype | 2,986,755 → 1,704,339 |
| 6 | Tag `label_source` (lab vs computational), extract `computational_f1` | adds 2 columns |
| 7 | Deduplicate on (`Genome ID`, `Antibiotic`), lab result wins | −178,543 rows |
| 8 | Keep the 14 modelling columns | **1,525,796 rows** |

The cleaned frame is cached; later runs load it in under a second. Bump `CLEAN_VERSION` in `data_prep.py` whenever cleaning changes, or old and new runs become silently incomparable.

**Label mapping** (step 5):

| Raw phenotype | Target | Reason |
|---|---|---|
| `Susceptible` | 0 | |
| `Susceptible-dose dependent` | 0 | effective at higher dosing |
| `Resistant` | 1 | |
| `Intermediate` | 1 | conservative, safer to over-call resistance |
| `Nonsusceptible` | 1 | |
| `Reduced Susceptibility` | 1 | |
| `Not defined`, missing | dropped | 1.27 M rows, ~42% of the raw export |

### 3.3 What the cleaned dataset looks like

| | |
|---|---|
| Rows (one per genome × antibiotic) | 1,525,796 (cleaning v1; v2 gives 1,521,644, see §3.4) |
| Unique genomes | 128,317 |
| Rows per genome | ~11.9 |
| Unique taxon IDs | 3,549 |
| Antibiotics | 152 (v1; 130 after the v2 name clean-up) |
| Drug classes | 20 |
| Genera | 41 (40 from v3, where a stray quote no longer makes `"neisseria` a genus) |
| Species | 94 |
| **Resistant** | **36.5%** |
| Label provenance | 87% computational caller, 13% wet lab |
| Rows carrying an MIC value | **6.8%** |

**Top genera:** Klebsiella 452,770 · Salmonella 344,201 · Pseudomonas 184,595 · Acinetobacter 171,078 · Neisseria 90,146 · Campylobacter 88,605 · Shigella 74,473 · Escherichia 74,066.

**Top antibiotics:** ciprofloxacin 119,359 · tetracycline 104,985 · gentamicin 89,720 · tobramycin 65,912 · trimethoprim/sulfamethoxazole 65,196 · meropenem 64,357.

**Resistance rate by drug class** (classes over 10,000 rows):

| Class | n | Resistant |
|---|---|---|
| tetracycline | 110,449 | 46.3% |
| monobactam | 48,406 | 45.6% |
| fluoroquinolone | 253,314 | 40.1% |
| carbapenem | 164,936 | 39.5% |
| sulfonamide | 124,668 | 36.4% |
| beta_lactam | 390,166 | 36.3% |
| aminoglycoside | 282,061 | 33.3% |
| macrolide | 73,413 | 20.6% |
| phenicol | 21,619 | 14.7% |

### 3.4 Known data-quality issues

- **93% of rows have no MIC.** `mic_value` is present for only 104,205 rows, and `mic_sign` is `unknown` for 96.3%. The MIC features are mostly missing data. LightGBM handles that natively, but it means the strongest clinical signal is absent from most training rows.
- **Label provenance is confounded with MIC availability.** Lab rows carry an MIC 47% of the time; computational rows 0.6%. Any comparison between the two subsets is partly a comparison of "has MIC" versus "doesn't".
- **Antibiotic names were messy; fixed in cleaning v2 (2026-09-25).** `CLEAN_VERSION = 'v2'` extends `ANTIBIOTIC_ALIASES`: 16 renames (underscore variants such as `ceftazidime_avibactam`, typos such as `amipicillin_sulbactam`, `tgecycline` and `strofurantoin`, the mis-encoded `cefuroximâ`, and alternative names such as `synercid` and `cefalotin`) and 8 drops (drug classes such as `fluoroquinolones`, the phenotype `extended spectrum beta lactamase`, and `instrument`, 593 *C. difficile* rows whose drug name was lost). Names go from 152 to 130 and rows from 1,525,796 to 1,521,644. `trimethoprim/sulfobactam` is kept as it is: every one of its genomes also has a separate trimethoprim/sulfamethoxazole row, so it is not a duplicate. **All 22 runs in §10 used v1**; re-run a config to get v2 numbers. Since 2026-09-26 the map lives only in `backend/amr_constants.py`, which the cleaning, trainer, predictors and web app all read.
- **13 more aliases and one more drop (2026-09-26), still v4.** Hyphen and underscore variants (`ceftazidime-avibactam`, `imipenem-relebactam`, `polymyxin_b`, `cefepime_taniborbactam`), the mis-encoded `cefotaxime/clavulanic acidâ`, `phosphomycin` → fosfomycin, `benzylpenicillin` → penicillin, other-language spellings Suleman found in `BVBRC_genome_amr.csv` (`tigecyklin`, `tetracyklin`, `cefpirom`, `amoxicillin_clavulanat`), and `sulfa` dropped as a drug group. None of the genomes has both spellings. Every row they touch in `amr_output/` has no usable phenotype, so the cleaned table is unchanged and `CLEAN_VERSION` stays `v4`; the map matters at prediction time and for other exports. `trimethoprim/sulfonamide` (38 rows) is left alone: a sulfonamide is not necessarily sulfamethoxazole.
- **Taxon IDs are strain-level.** 3,549 distinct IDs in a dataset of 41 genera, these are BV-BRC strain identifiers, not the species IDs a user would type (562 for *E. coli*). This is why the `/forecast` page's Taxon ID field never matches a lookup.
- **`computational_f1` is self-reported** by whichever caller produced the row, parsed out of a free-text field, and forced to 1.0 for lab rows. Treat it as a provenance hint, not a calibrated quality score.

---

## 4. Field reference

### 4.1 Raw columns (21) and what happens to each

| Column | Used? | How |
|---|---|---|
| `Taxon ID` | ✅ feature | numeric feature + key for taxon rate encoding |
| `Genome ID` | ✅ grouping | **never a feature**, used to group the split so a genome cannot straddle it |
| `Genome Name` | ✅ derived | split into `genus` + `species` |
| `Antibiotic` | ✅ feature | normalised, categorical feature, key for all rate encodings |
| `Resistant Phenotype` | ✅ label | mapped to `target` |
| `Measurement` | ✅ derived | parsed into `mic_sign` and `mic_value` |
| `Measurement Value` | ✅ derived | fallback when `Measurement` has no number |
| `Measurement Sign` | ❌ | redundant, the sign is parsed from `Measurement` |
| `Measurement Unit` | ❌ | almost always mg/L; not validated |
| `Evidence` | ✅ derived | drives `is_lab_confirmed` and `label_source` |
| `Computational Method Performance` | ✅ derived | F1 score regex-extracted into `computational_f1` |
| `Computational Method`, `… Version` | ❌ | high missingness |
| `Laboratory Typing Method`, `… Version`, `… Platform` | ❌ | >95% missing |
| `Vendor`, `Testing Standard`, `Testing Standard Year` | ❌ | >96% missing. `Testing Standard Year` would enable a temporal split if it were populated |
| `Source`, `PubMed` | ❌ | >99% missing |

### 4.2 Cleaned columns (15 from cleaning v3)

| Column | Type | Coverage | Distinct | Meaning |
|---|---|---|---|---|
| `Genome ID` | float64 | 100% | 128,317 | Assembly identifier. **Grouping key, not a feature.** |
| `Taxon ID` | int64 | 100% | 3,549 | BV-BRC taxonomy ID, mostly strain level (3,224 of 3,655 are strains or serotypes) |
| `species_taxon_id` | int64 | 100% | 124 | Species-level NCBI Taxon ID (v3). *E. coli* is 562, spread over about 1,200 `Taxon ID`s. From `backend/taxon_species.csv`, built by `build_taxonomy.py` |
| `Antibiotic` | str | 100% | 152 | Normalised drug name, lowercase |
| `drug_class` | str | 100% | 20 | Mapped from `Antibiotic`; `other` when unmapped |
| `genus` | str | 100% | 41 | First token of `Genome Name`, capitalised |
| `species` | str | 100% | 94 | Second token, lowercase |
| `mic_sign` | str | 100% | 7 | `<`, `<=`, `=`, `==`, `>`, `>=`, `unknown` (96.3%) |
| `mic_value` | float64 | **6.8%** | 121 | MIC in mg/L. Median 8, range 0 to 16,384 |
| `mic_log` | float64 | 6.8% | 121 | `log1p(mic_value)`. MIC is log-distributed by design (doubling dilutions) |
| `has_mic` | int64 | 100% | 2 | Explicit missingness flag |
| `is_lab_confirmed` | int64 | 100% | 2 | 1 when `Evidence == 'Laboratory Method'` |
| `computational_f1` | float64 | 100% | 71 | Caller's self-reported F1; 1.0 for lab rows; median 0.93 |
| `label_source` | str | 100% | 2 | `lab` or `computational`. **Filter, not a feature** |
| `target` | int64 | 100% | 2 | 1 = Resistant, 0 = Susceptible |

---

## 5. The feature set

Fourteen features reach the model. Eleven come straight from cleaning; three are computed per-run because they depend on the split.

### 5.1 Base features (11)

| Feature | Kind | Note |
|---|---|---|
| `Taxon ID` | numeric | Treated as a number, so the model can only split on ranges of it |
| `Antibiotic` | categorical | 152 levels, LightGBM native categorical |
| `drug_class` | categorical | 20 levels, lets rare drugs borrow from their class |
| `genus` | categorical | 41 levels |
| `species` | categorical | 94 levels |
| `mic_sign` | categorical | 7 levels |
| `mic_value` | numeric | NaN left as NaN; LightGBM learns a default direction |
| `mic_log` | numeric | log-scaled MIC |
| `has_mic` | binary | missingness as signal |
| `is_lab_confirmed` | binary | provenance |
| `computational_f1` | numeric | provenance quality |

### 5.2 The three rate features

These are **target (mean) encodings**, each replaces a category with the historical resistance rate for that group, computed from training data only:

| Feature | Grouped by | Min group size |
|---|---|---|
| `ab_resistance_rate` | Antibiotic | 1 |
| `taxon_ab_resistance_rate` | Taxon ID × Antibiotic | 3 |
| `genus_ab_resistance_rate` | genus × Antibiotic | 3 |

Groups below the minimum, or unseen at prediction time, fall back: taxon rate → antibiotic rate → global mean (0.3652 on the current training split).

**Three encoding modes**, selected per config:

- **`oof`** (default, correct), each training row's encoding is computed from the *other* four folds, so a row never sees its own label. Test rows use the full training map.
- **`leaky`**, fitted on the entire dataset before splitting. Reproduces [train_models.py:186-209](../backend/train_models.py#L186-L209). Kept only so the cost of the bug can be measured.
- **`none`**, no rate features.

### 5.3 What the model actually uses

Feature importance from `A2_oof_grouped` (share of total gain):

| Feature | Gain | Splits |
|---|---|---|
| `taxon_ab_resistance_rate` | **61.2%** | 4,392 |
| `genus_ab_resistance_rate` | 11.7% | 3,930 |
| `mic_value` | 6.4% | 3,847 |
| `mic_sign` | 5.7% | 536 |
| `Taxon ID` | 3.8% | 6,876 |
| `Antibiotic` | 3.7% | 3,597 |
| `species` | 2.4% | 1,138 |
| `mic_log` | 1.6% | 851 |
| `genus` | 1.0% | 688 |
| `ab_resistance_rate` | 0.9% | 3,132 |
| `drug_class` | 0.6% | 353 |
| `computational_f1` | 0.5% | 1,092 |
| `is_lab_confirmed` | 0.4% | 553 |
| `has_mic` | 0.0% | 15 |

The three rate features account for **73.8% of total gain**. But removing them entirely (`A2b_no_encoding`) costs only 0.001 AUC, because `Taxon ID` and `Antibiotic` carry the same information in raw form, and the trees simply rebuild it. The encodings make the model *converge faster*, not *know more*.

---

## 6. What happens during a run

`run.py` executes these steps in order. Each is one function so it can be audited independently.

**1. Load config**. JSON, with defaults filled for anything absent.

**2. Load data**, cached clean frame, then apply the config's row filters (`label_sources`, `drop_antibiotics`, `min_rows_per_antibiotic`, `sample_rows`).

**3. Split** - `lib/splits.py`:
- `grouped` (default): `StratifiedGroupKFold(n_splits=5)` on `Genome ID`, first fold is the test set. Preserves class balance while keeping genomes whole.
- `random`: plain stratified row split, reproduces the old pipeline.
- `species_holdout`: one genus becomes the entire test set.

The run prints how many genomes appear on both sides. Under `grouped` this is always 0; seeing anything else means something is wrong.

**4. Encode** - `lib/encoders.py` adds the rate features per the chosen mode. Under `oof`, inner folds are themselves grouped by genome.

**5. Align categories**, train and test are given identical category levels, so the same string maps to the same integer on both sides. Without this, LightGBM can silently interpret category codes differently across the split.

**6. Carve a validation slice**, a 6-fold grouped split of the training set; fold 0 is validation (~17% of train). Used for early stopping and threshold choice, never for final metrics. Typical sizes on the full dataset: fit 1,017,201 · val 203,436 · test 305,159.

**7. Fit**, the model from `model.type`, with early stopping on validation AUC (patience 30).

**8. Pick a threshold**, on **validation** scores, never test:
- `fixed`, use the configured number (0.40 matches production)
- `maximize_f1`, the threshold maximising F1 on the precision-recall curve
- `vme_constrained`, the highest threshold whose very-major-error rate still fits `vme_budget`

**9. Evaluate on test**, full metric set, plus a bootstrap CI that **resamples genomes rather than rows** (rows from one genome are correlated; resampling rows would give a falsely tight interval), plus a per-antibiotic breakdown sorted worst-first.

**10. Persist** - `metrics.json`, `predictions.csv`, `config.snapshot.json`: the **model bundle** (below), and one row appended to `results/registry.csv`. Re-running an id replaces its registry row rather than duplicating it.

### 6.1 The saved model bundle

Every run writes three files to `results/<id>/model/`, and all three are needed
to predict:

| File | What it holds |
|---|---|
| `model.txt` / `model.joblib` | the trained booster or sklearn pipeline |
| `rate_tables.joblib` | the three resistance-rate lookup tables **built from this run's training rows**, plus that run's global mean |
| `feature_meta.json` | feature order, categorical levels, encoding mode, chosen threshold, and what it was trained on |

The booster alone is not a usable model. Three of its features are rates looked
up per antibiotic / taxon / genus, so predicting without the matching tables
would feed it numbers it was never trained against, the same mismatch that
makes promotion to the backend risky if the tables are not carried across.

Load and predict with [`predict.py`](predict.py):

```python
from experiments.predict import load

model = load('A2_oof_grouped')
model.predict({'antibiotic': 'ciprofloxacin', 'genus': 'Escherichia',
               'species': 'coli', 'mic_value': 8, 'mic_sign': '>'})
# {'probability': 0.9996, 'prediction': 'Resistant', 'threshold': 0.4, ..}
```

```bash
python experiments/predict.py --list          # every loadable saved model
python experiments/predict.py A2_oof_grouped --antibiotic ciprofloxacin --mic 8
```

**Verified faithful:** reloading a bundle and re-predicting 300 test rows
reproduces that run's stored scores to within 5e-5 (the rounding in
`predictions.csv`) for both the LightGBM and scikit-learn paths.

Runs trained before this existed were backfilled with
`python experiments/backfill_bundles.py`, which rebuilds each run's training
split from its config snapshot, the splits are seeded, so the rows are
identical, and recomputes the tables without retraining.

---

## 7. Algorithms

**One file per algorithm**, in [`algorithms/`](algorithms/). All five implement the
same `fit` / `predict_proba` / `save` / `info` contract, so swapping `model.type`
changes the algorithm and nothing else in the pipeline.

| File | `model.type` | Algorithm |
|---|---|---|
| [`algorithms/lightgbm_model.py`](algorithms/lightgbm_model.py) | `lightgbm` | LightGBM GBDT |
| [`algorithms/logistic_model.py`](algorithms/logistic_model.py) | `logistic` | Logistic regression |
| [`algorithms/random_forest_model.py`](algorithms/random_forest_model.py) | `random_forest` | Random forest |
| [`algorithms/xgboost_model.py`](algorithms/xgboost_model.py) | `xgboost` | XGBoost |
| [`algorithms/catboost_model.py`](algorithms/catboost_model.py) | `catboost` | CatBoost |
| [`algorithms/base.py`](algorithms/base.py) | n/a | the contract, `align_categories()`, shared sklearn preprocessing |
| [`algorithms/__init__.py`](algorithms/__init__.py) | n/a | `REGISTRY` + `build_model()` dispatcher |

Each file carries its own defaults and the reasoning for them, so the training
recipe for an algorithm is readable in one place without wading through the
others.

**To add an algorithm:** write a class with the four methods (see `base.py`),
add one line to `REGISTRY` in `__init__.py`. `run.py` needs no change, and
existing results stay comparable because nothing else in the pipeline moves.

### LightGBM - `"type": "lightgbm"`

Gradient-boosted decision trees. The default and the only one used in the runs so far.

```python
objective='binary', metric='auc', boosting_type='gbdt',
num_leaves=63, learning_rate=0.05, n_estimators=500,
subsample=0.8, colsample_bytree=0.8,
reg_alpha=0.1, reg_lambda=1.0,
is_unbalance=True, cat_smooth=10, max_cat_threshold=32,
early_stopping_rounds=30
```

Handles categoricals natively (no one-hot) and NaN natively (learns a default direction), which suits this dataset, 93% of MIC values are missing. Supports `monotone_on`, which forces a feature's effect to be non-decreasing: `["mic_value","mic_log"]` makes it impossible for the model to predict *less* resistance at a higher MIC.

### Logistic regression - `"type": "logistic"`

Sparse one-hot for categoricals (`min_frequency=20`) + median imputation and scaling for numerics, then `LogisticRegression(solver='saga', class_weight='balanced', max_iter=200)`. The interpretable floor: if boosting can't beat this by much, the signal is linear.

### Random forest - `"type": "random_forest"`

`RandomForestClassifier(n_estimators=200, max_depth=18, class_weight='balanced')` on the same one-hot pipeline. Wired and working; no config written yet.

### XGBoost - `"type": "xgboost"` *(needs `pip install xgboost`)*

`hist` tree method, `enable_categorical=True`, `scale_pos_weight` computed from the training class balance, early stopping at 30.

### CatBoost - `"type": "catboost"` *(needs `pip install catboost`)*

Ordered target statistics, a principled built-in replacement for the hand-rolled rate encoding, and the natural comparison against it. `auto_class_weights='Balanced'`, early stopping at 50.

Missing libraries exit with an install hint rather than a traceback.

---

## 8. Metrics

Every run reports all of these. Pooled AUC alone would hide too much.

| Metric | What it answers | Why it's here |
|---|---|---|
| **AUC-ROC** | Ranking quality across all thresholds | Comparable to the literature, but flattering under imbalance |
| **AUPRC** | Ranking quality weighted to the positive class | Honest at 36.5% prevalence; **the table sorts by this** |
| **F1** | Balance of precision and recall at the chosen threshold | |
| **Balanced accuracy** | Mean of sensitivity and specificity | Threshold-dependent, imbalance-reliable |
| **Brier score** | Squared error of the predicted probability | The UI prints "54.3%" as a probability, this says whether that means anything. Lower is better |
| **Sensitivity / specificity** | Standard rates | |
| **Very major error (VME)** | Resistant isolate called Susceptible | **The dangerous error.** Clinical guidance asks for ≤1.5 to 3% |
| **Major error (ME)** | Susceptible isolate called Resistant | Wasteful, drives broader-spectrum prescribing. ≤3% |
| **Bootstrap CI** | Uncertainty on AUC | Resamples genomes; two overlapping intervals are not different |
| **Per-antibiotic table** | Where the model fails | A pooled 0.82 can hide a drug at 0.50 |

VME and ME are the clinically meaningful pair and the reason the production threshold is 0.40 rather than 0.50: lowering the threshold trades ME for VME.

---

## 9. Config reference

```json
{
  "id": "unique_run_name",
  "description": "one line, appears in the comparison table",

  "data": {
    "source": "amr_output",
    "normalize_antibiotics": true,
    "label_sources": ["lab"],
    "drop_antibiotics": ["furazolidone"],
    "min_rows_per_antibiotic": 200,
    "sample_rows": 400000,
    "seed": 42
  },

  "split": {
    "strategy": "grouped",
    "test_size": 0.2,
    "seed": 42,
    "holdout_genus": "Klebsiella"
  },

  "features": {
    "target_encoding": "oof",
    "encoding_folds": 5,
    "base": ["Antibiotic", "drug_class"],
    "drop": ["mic_value", "mic_log", "has_mic", "mic_sign"]
  },

  "model": {
    "type": "lightgbm",
    "params": { "num_leaves": 127, "learning_rate": 0.03 },
    "monotone_on": ["mic_value", "mic_log"]
  },

  "threshold": { "strategy": "vme_constrained", "vme_budget": 0.03, "fixed": 0.4 },

  "evaluation": { "n_boot": 200, "min_n_per_group": 50 }
}
```

| Key | Values | Default |
|---|---|---|
| `data.source` | folder under `data/` | `amr_output` |
| `data.normalize_antibiotics` | `true` / `false` | `true` |
| `data.label_sources` | `["lab"]`, `["computational"]`, both | all |
| `data.sample_rows` | int | all rows |
| `split.strategy` | `grouped`, `random`, `species_holdout` | `grouped` |
| `features.target_encoding` | `oof`, `leaky`, `none` | `oof` |
| `features.base` | explicit feature list | the 11 base features |
| `features.drop` | features to remove, this is how ablations are written | `[]` |
| `model.type` | `lightgbm`, `logistic`, `random_forest`, `xgboost`, `catboost` | `lightgbm` |
| `model.monotone_on` | feature names (LightGBM only) | none |
| `threshold.strategy` | `fixed`, `maximize_f1`, `vme_constrained` | `fixed` |
| `evaluation.n_boot` | bootstrap resamples | 200 |

---

## 10. Results so far

22 runs, identical protocol unless stated. Sorted by AUC.

| Run | Algo | AUC-ROC [95% CI] | AUPRC | F1 | VME | ME | Brier | Thr | Rows |
|---|---|---|---|---|---|---|---|---|---|
| `A6_lab_only` | lightgbm | 0.9654 [0.9620-0.9685] | 0.9678 | 0.8829 | 8.2% | 16.1% | 0.0748 | 0.40 | 203,824 |
| `A6b_lab_only_no_mic` | lightgbm | 0.8703 [0.8644-0.8764] | 0.8642 | 0.7934 | 11.4% | 34.6% | 0.1464 | 0.40 | 203,824 |
| `A0_baseline_leaky` | lightgbm | 0.8243 [0.8227-0.8264] | 0.7409 | 0.6662 | 10.6% | 45.4% | 0.1711 | 0.40 | 1,525,796 |
| `A9_threshold_f1` | lightgbm | 0.8232 [0.8200-0.8269] | 0.7394 | 0.6703 | 20.2% | 33.6% | 0.1716 | 0.47 | 1,525,796 |
| `A2_oof_grouped` | lightgbm | 0.8232 [0.8200-0.8269] | 0.7394 | 0.6645 | 10.1% | 46.4% | 0.1716 | 0.40 | 1,525,796 |
| `A1_oof_random` | lightgbm | 0.8225 [0.8210-0.8247] | 0.7387 | 0.6648 | 10.9% | 45.4% | 0.1719 | 0.40 | 1,525,796 |
| `A10_monotonic_mic` | lightgbm | 0.8222 [0.8192-0.8257] | 0.7372 | 0.6640 | 10.1% | 46.5% | 0.1722 | 0.40 | 1,525,796 |
| `A2b_no_encoding` | lightgbm | 0.8221 [0.8188-0.8255] | 0.7376 | 0.6644 | 10.4% | 46.1% | 0.1720 | 0.40 | 1,525,796 |
| `A3b_lgbm_same_sample` | lightgbm | 0.8201 [0.8163-0.8245] | 0.7348 | 0.6683 | 20.4% | 33.5% | 0.1733 | 0.47 | 400,000 |
| `LC_400k` | lightgbm | 0.8201 [0.8163-0.8245] | 0.7348 | 0.6575 | 8.8% | 49.3% | 0.1733 | 0.40 | 400,000 |
| `LC_800k` | lightgbm | 0.8200 [0.8162-0.8245] | 0.7372 | 0.6599 | 9.8% | 47.7% | 0.1728 | 0.40 | 800,000 |
| `LC_100k` | lightgbm | 0.8195 [0.8123-0.8263] | 0.7349 | 0.6589 | 10.0% | 47.6% | 0.1735 | 0.40 | 100,000 |
| `A5_xgboost` | xgboost | 0.8195 [0.8158-0.8238] | 0.7343 | 0.6675 | 20.8% | 33.2% | 0.1737 | 0.49 | 400,000 |
| `A5b_catboost` | catboost | 0.8191 [0.8154-0.8234] | 0.7329 | 0.6674 | 20.6% | 33.5% | 0.1736 | 0.47 | 400,000 |
| `A5c_catboost_native` | catboost | 0.8186 [0.8146-0.8226] | 0.7323 | 0.6671 | 20.8% | 33.3% | 0.1739 | 0.47 | 400,000 |
| `LC_200k` | lightgbm | 0.8174 [0.8115-0.8223] | 0.7307 | 0.6581 | 11.2% | 46.2% | 0.1740 | 0.40 | 200,000 |
| `A4_random_forest` | random_forest | 0.8173 [0.8136-0.8214] | 0.7282 | 0.6657 | 21.4% | 32.9% | 0.1748 | 0.48 | 400,000 |
| `LC_50k` | lightgbm | 0.8157 [0.8060-0.8233] | 0.7307 | 0.6595 | 12.5% | 44.9% | 0.1759 | 0.40 | 50,000 |
| `A_ablation_no_mic` | lightgbm | 0.8033 [0.7999-0.8068] | 0.6974 | 0.6518 | 9.1% | 50.6% | 0.1820 | 0.40 | 1,525,796 |
| `A3_logistic` | logistic | 0.8024 [0.7985-0.8063] | 0.7083 | 0.6557 | 21.0% | 35.4% | 0.1811 | 0.45 | 400,000 |
| `A_ablation_drug_only` | lightgbm | 0.6545 [0.6516-0.6570] | 0.4906 | 0.5743 | 9.8% | 71.2% | 0.2277 | 0.40 | 1,525,796 |
| `A12_species_holdout` | lightgbm | 0.5971 [0.5935-0.6012] | 0.5990 | 0.6045 | 11.4% | 82.9% | 0.2467 | 0.40 | 1,525,796 |

Regenerate with `python experiments/report.py`.

---

## 11. What the results mean

**The corrected baseline is AUC 0.823** (`A2_oof_grouped`): full data, out-of-fold encoding, zero genome overlap, threshold 0.40.

**Target leakage costs 0.002, not the large correction expected.** `A0_baseline_leaky` 0.8243 vs `A1_oof_random` 0.8225, overlapping intervals. At 1.5 M rows each encoded group is estimated from many rows, so one test row's own label barely shifts its group mean. It would matter on the 25 k rows the shipped model used; it does not here. Fix it anyway (it is free), but do not claim a large correction.

**Genome grouping also costs nothing here.** `A1_oof_random` has 106,815 genomes on both sides and scores 0.8225; `A2_oof_grouped` has zero overlap and scores 0.8232. With 128 k genomes there is not enough per-genome signal to memorise. It is very different for small training sets and for the k-mer model, where one genome's feature vector is *identical* across its rows; see the next paragraph.

**The threshold matters more than any model choice.** Every algorithmic variant sits inside ±0.002 AUC. Meanwhile moving the threshold from 0.40 to 0.47 moves VME from 10.1% to 20.2% and ME from 46.4% to 33.6%. **At the production threshold, 46% of susceptible isolates are called resistant.** That is the single most important number in this table and it is a policy decision, not a modelling one.

**Algorithm choice barely matters; model family does.** All five run on the identical 400 k sample, same split, same seed:

| Algorithm | AUC [95% CI] | AUPRC | Brier |
|---|---|---|---|
| LightGBM | 0.8201 [0.8163-0.8245] | 0.7348 | 0.1733 |
| XGBoost | 0.8195 [0.8158-0.8238] | 0.7343 | 0.1737 |
| CatBoost | 0.8191 [0.8154-0.8234] | 0.7329 | 0.1736 |
| Random forest | 0.8173 [0.8136-0.8214] | 0.7282 | 0.1748 |
| Logistic regression | 0.8024 [0.7985-0.8063] | 0.7083 | 0.1811 |

The three boosting libraries are within 0.001 of each other. Boosting over bagging is 0.003, overlapping intervals, not a real difference. Either tree method over linear is ~0.018 with non-overlapping intervals, so that one is real but modest. Most of the signal is in the features, not in non-linear interactions.

**MIC is worth about 0.02 AUC pooled** (`A_ablation_no_mic` 0.8033 vs 0.8232), smaller than expected because 93% of rows have no MIC. On the lab subset where MIC is present 47% of the time, it is worth **0.095** (`A6` 0.9654 vs `A6b` 0.8703).

**The lab-only result is partly circular.** 0.9654 looks spectacular, but a lab's S/R call *is* the MIC put through clinical breakpoints, and lab rows carry an MIC 78× more often. Remove MIC and it falls to 0.8703, still well above the pooled baseline, so lab labels are cleaner, but 0.9654 is not a number to quote as model performance.

**Drug identity alone gives 0.6545.** This is the measured floor that the `/forecast` page labels a "Population-level estimate", what a user gets when they fill in nothing but the antibiotic.

**Generalisation across genera collapses.** `A12_species_holdout`, train without *Klebsiella*, test only on it, gives 0.5971 with 82.9% ME, barely above chance. The model substantially encodes "this organism is usually resistant to this drug" rather than resistance mechanism.

**The deployed models score far lower on genomes they never saw.** `evaluate_shipped.py` rebuilt which files each shipped artifact trained on (the first 500 `amr_output` and first 200 `mapped_output` files, confirmed by identical antibiotic sets, genera and stored resistance rate) and scored both on every other genome:

| Model | Training data | Seen genomes | Unseen genomes |
|---|---|---|---|
| Shipped LightGBM | 24,983 rows, 1,007 genomes, 9 genera, 16.6% resistant | 0.941 | 0.644 [0.642-0.645] |
| Shipped K-mer RF | 6,002 rows, 218 genomes, 6 genera, no lab labels | 0.981 | 0.695 [0.679-0.714] |

On the 297,197 rows neither trained on, the shipped LightGBM scores 0.644 and `A2_oof_grouped` 0.820, with the same algorithm. The gap is the data: 1.6% of the rows, no *Klebsiella*, *Neisseria*, *Campylobacter* or *Shigella*, and half the resistant share of the full export. The K-mer model does no better than the antibiotic's resistance rate alone (0.703), and within a single antibiotic its AUC averages 0.62. At the shipped thresholds the two models miss 46% and 70% of resistant isolates.

**The learning curve is flat from 50 k rows.** 50 k → 1.5 M moves AUC 0.8157 → 0.8232, all intervals overlapping. What full data does buy is precision (CI width 0.017 → 0.007) and tail coverage (36 → 90 antibiotics with enough test rows to evaluate). **More rows will not help; better features will**, which is the argument for AMR gene presence features (Track B6 in the plan) over further tuning.

---

## 12. File reference

**Entry points**

| File | Purpose |
|---|---|
| `run.py` | Runs one config end to end; `--all` for every config |
| `report.py` | `registry.csv` → Markdown; `--per-antibiotic <id>` for one run's weak spots |
| `predict.py` | Loads a saved run and predicts with it; `--list` shows every loadable model |
| `backfill_bundles.py` | Adds inference bundles to runs trained before the exporter existed |
| `evaluate_shipped.py` | Re-tests the models in `backend/trained_models/` on genomes outside their training files; writes `results/shipped_eval.json` |
| `export_report.py` | Collects runs, split counts, ROC curves, per-antibiotic results and training-data profiles into `backend/trained_models/model_report.json` for the app's `/models` and `/compare` pages |

**Algorithms, one file each**

| File | `model.type` | What it is |
|---|---|---|
| `algorithms/base.py` | n/a | The `fit`/`predict_proba`/`save`/`info` contract, `align_categories()`, and the shared one-hot + impute + scale preprocessing the sklearn estimators use |
| `algorithms/__init__.py` | n/a | `REGISTRY` mapping type names to classes, plus `build_model()` |
| `algorithms/lightgbm_model.py` | `lightgbm` | Gradient-boosted trees; native categoricals and native NaN handling |
| `algorithms/logistic_model.py` | `logistic` | The interpretable linear baseline |
| `algorithms/random_forest_model.py` | `random_forest` | Bagged trees; the non-boosted tree contrast |
| `algorithms/xgboost_model.py` | `xgboost` | Needs `pip install xgboost` |
| `algorithms/catboost_model.py` | `catboost` | Ordered target statistics; needs `pip install catboost` |

**Pipeline stages**

| File | Purpose |
|---|---|
| `lib/data_prep.py` | Raw CSVs → cleaned frame. Holds `CLEAN_VERSION`; imports `DRUG_CLASS_MAP`, `ANTIBIOTIC_ALIASES`, `PHENOTYPE_MAP` from `backend/amr_constants.py` |
| `lib/splits.py` | `make_split()` (grouped/random/species) and `inner_folds()` |
| `lib/encoders.py` | `add_rate_features()`, the `oof`/`leaky`/`none` logic |
| `lib/metrics.py` | `evaluate()`, `pick_threshold()`, `per_group()`, `bootstrap_ci()` |
| `lib/profile.py` | `profile()`: rows, genomes, genera, antibiotics, resistant share, lab share and genus mix of a training set |

**Data in and out**

| Path | Purpose |
|---|---|
| `configs/*.json` | One per experiment, the complete description of a run |
| `cache/` | Cleaned-data cache; safe to delete, costs ~20 s to rebuild |
| `results/<id>/metrics.json` | Every metric + per-antibiotic breakdown + the config |
| `results/<id>/predictions.csv` | Raw test scores, what statistical comparisons need |
| `results/<id>/config.snapshot.json` | Exactly what produced this run |
| `results/<id>/model/` | `model.*` + `rate_tables.joblib` + `feature_meta.json` (§6.1) |
| `results/registry.csv` | One row per run, the comparison table |
| `results/shipped_eval.json` | The deployed models' re-test, from `evaluate_shipped.py` |
| `RESULTS.md` | Generated comparison table |

Not committed (see `.gitignore`): `cache/` (189 MB), `results/*/predictions.csv`
(184 MB) and `results/*/model/` (44 MB). Everything needed to regenerate them is, any model rebuilds from its config in about a minute.

---

## 13. Limitations of this harness

- **Tabular model only.** The k-mer genome model and the timeline simulation have no equivalent training harness yet. The shipped k-mer model can be re-tested (`evaluate_shipped.py`), but not retrained here.
- **No hyperparameter search.** Configs are hand-written; there is no sweep or Bayesian search loop. Add one by generating configs programmatically.
- **No statistical test between runs.** Bootstrap CIs are computed per run, but DeLong and McNemar tests across two runs are not implemented. `predictions.csv` holds everything needed to add them.
- **No calibration curve.** Brier score is reported, but reliability plots are not produced (matplotlib is not installed).
- **Promotion to the app is manual.** The rate tables are now exported per run, so a promoted model can carry its own lookups, but the backend expects them under different filenames (`ab_rate_full.joblib` etc.) and as pandas objects, so a small conversion step is still needed. Nothing writes to `backend/trained_models/` automatically.
- **Single seed.** Every run uses `seed=42`. Variance across seeds is unmeasured; for a headline claim, re-run with 3 to 5 seeds and report the spread.
