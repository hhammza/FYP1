# Model Experiment Plan

*A staged plan for training AMR models under different strategies and comparing the results. Written against the code at commit `52ae361`, 2026-09-24.*

The goal is a comparison table you can put in a thesis chapter and defend in a viva. Each row differs by one choice, every number comes from the same protocol, and the protocol does not inflate the results.

The current pipeline has two measurement faults that make any comparison meaningless. Fix those first (§1), then run experiments (§4-§6).

---

> **Status:** the harness is built (`experiments/`) and **19 runs are done**, across
> three algorithms. Every saved model is reloadable via `experiments/predict.py`.
> Results: [experiments/RESULTS.md](experiments/RESULTS.md); full documentation of
> the data, fields, training procedure and findings in
> [experiments/HANDBOOK.md](experiments/HANDBOOK.md).
> Document history, including two corrected predictions: [CHANGES.md](CHANGES.md). Two predictions in
> §1.2 and §1.3 below were wrong and have been corrected with measurements.

## 0. Contents

1. [Three blockers before any retraining](#1-three-blockers-before-any-retraining)
2. [The measurement protocol](#2-the-measurement-protocol)
3. [The experiment harness](#3-the-experiment-harness)
4. [Track A, tabular forecaster experiments](#4-track-a--tabular-forecaster-experiments)
5. [Track B, genome model experiments](#5-track-b--genome-model-experiments)
6. [Track C, the timeline simulation](#6-track-c--the-timeline-simulation)
7. [Ablations: which inputs actually earn their place](#7-ablations-which-inputs-actually-earn-their-place)
8. [Comparing runs statistically](#8-comparing-runs-statistically)
9. [Suggested schedule](#9-suggested-schedule)
10. [What goes in the report](#10-what-goes-in-the-report)
11. [Pitfall checklist](#11-pitfall-checklist)

---

## 1. Three blockers before any retraining

### 1.1 Data ✅ resolved

The export now lives under `data/` and the harness reads it directly. Census of
`data/amr_output/` (3,655 CSVs, 2026-09-24):

| | |
|---|---|
| Raw rows | 2,986,755 |
| Rows after cleaning | 1,525,796 |
| Unique genomes | 128,317 |
| Rows per genome | ~11.9 |
| Antibiotics (after normalising spellings) | 152 |
| Genera | 41 |
| Resistant | 36.5% |
| Label provenance | 87% computational caller, 13% wet lab |

That is **17× the ~90,000 rows the shipped model was trained on** - `train_models.py`
caps itself at 500 files ([line 55](backend/train_models.py#L55)), so it has only ever
seen a seventh of the export.

### 1.2 Target encodings leak into the test set 🔴

In [train_models.py:186-209](backend/train_models.py#L186-L209) the three resistance-rate features are computed on the **whole** dataframe, and only then is the test set split off:

```python
ab_rate  = df.groupby('Antibiotic')[TARGET].mean()      # ← sees test labels
taxon_ab = df.groupby(['Taxon ID','Antibiotic'])[TARGET]..
genus_ab = df.groupby(['genus','Antibiotic'])[TARGET]..
df['ab_resistance_rate'] = ..
X_train, X_test = train_test_split(X, y, ..)           # ← too late
```

Those three features are the model's strongest signals - `taxon_ab_resistance_rate` is the root split of tree 0. Every test row therefore carries a feature computed partly from its own label. **This is why the shipped artifact reports 0.9255 while the notebook, which did out-of-fold encoding, reports 0.8881 on the same task.** Treat 0.9255 as invalid, not as a better model.

**Fix, out-of-fold encoding.** Compute the encoding for each training fold from the *other* folds, and the test encoding from the training set only:

```python
from sklearn.model_selection import StratifiedKFold

def oof_target_encode(df_tr, df_te, keys, target, global_mean, min_count=3, n_splits=5):
    """Out-of-fold mean encoding. Train rows get a value computed without
    their own label; test rows get the full-train mapping."""
    col = '_'.join(keys) + '_rate'
    df_tr[col] = np.nan
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    for fit_idx, enc_idx in skf.split(df_tr, df_tr[target]):
        agg = (df_tr.iloc[fit_idx].groupby(keys)[target].agg(['sum', 'count']))
        agg = agg[agg['count'] >= min_count]
        rate = (agg['sum'] / agg['count']).rename(col)
        df_tr.loc[df_tr.index[enc_idx], col] = (
            df_tr.iloc[enc_idx].join(rate, on=keys)[col].to_numpy())
    df_tr[col] = df_tr[col].fillna(global_mean)

    agg = df_tr.groupby(keys)[target].agg(['sum', 'count'])
    agg = agg[agg['count'] >= min_count]
    rate = (agg['sum'] / agg['count']).rename(col)
    df_te[col] = df_te.join(rate, on=keys)[col].fillna(global_mean)
    return df_tr, df_te
```

**Measured on the full dataset (2026-09-24): the leakage is worth ~0.002 AUC, not the large gap I expected.** `A0_baseline_leaky` scores 0.8243 [0.8227-0.8264] and `A1_oof_random` scores 0.8225 [0.8210-0.8247], overlapping intervals, i.e. not a significant difference. The reason is scale: with 1.5 M rows and a `min_count >= 3` floor, each encoded group is estimated from many rows, so one test row's own label barely moves its group mean. The leakage would matter on the ~90 k-row subset the shipped model was trained on; it does not at this size.

Fix it anyway, it costs nothing and removes the objection entirely, but do not claim a large correction that the data does not support. See [experiments/RESULTS.md](experiments/RESULTS.md).

### 1.3 Rows from one genome land on both sides of the split 🟠

Cleaning deduplicates on `(Genome ID, Antibiotic)`, so one genome contributes one row per antibiotic tested. A random row-level split puts *the same genome* in train and test. The model can memorise a genome instead of learning resistance.

**Fix, group-aware splitting** on `Genome ID`:

```python
from sklearn.model_selection import StratifiedGroupKFold
splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
train_idx, test_idx = next(splitter.split(X, y, groups=df['Genome ID']))
```

**Measured: also near zero for Track A.** `A1_oof_random` (106,815 genomes on both sides) scores 0.8225 and `A2_oof_grouped` (zero overlap) scores 0.8232, the grouped split is, if anything, marginally *higher*. With ~12 rows per genome but 128 k genomes, there is not enough per-genome signal for the model to memorise.

Keep the grouped split as the default regardless: it costs nothing, it is the defensible choice, and it matters far more for **Track B**, where one genome's k-mer vector is literally identical across its rows. Re-measure there before assuming the Track A result carries over.

### 1.4 Bonus blocker if you use the notebook lineage 🟠

`LightGBM_Model_Improved.ipynb` cell 3 "rescues" 32,756 unlabeled rows by assigning labels from per-antibiotic MIC quantiles, while `mic_value` remains an input feature. Roughly 36% of that training pool has a label that is a deterministic function of a feature the model can see. Any model will look excellent at recovering a rule it was handed.

**Action:** either drop rescued rows from evaluation, or flag them with `label_source ∈ {lab, computational, mic_rule}` and report metrics per source. Never evaluate on `mic_rule` rows.

---

## 2. The measurement protocol

Fix this once; every experiment below reuses it unchanged.

### 2.1 Splits

| Split | Purpose | How |
|---|---|---|
| **Inner CV** (5-fold, grouped) | Hyperparameters, early stopping | `StratifiedGroupKFold` on train, groups = `Genome ID` |
| **Held-out test** (20%, grouped) | The number you report | Split once, `random_state=42`, never touched during development |
| **Species hold-out** | Generalisation to a new organism | Train with *Klebsiella* (or any genus) entirely removed; test only on it |
| **Temporal hold-out** *(optional)* | Realistic deployment | If `Testing Standard Year` is populated, train ≤2018, test ≥2019 |

The species hold-out is the most interesting one for AMR and almost nobody at FYP level does it. It answers: *does this model work on an organism it has never seen?* Expect a large drop. That is a finding, not a failure.

### 2.2 Metrics, report all of these, every run

```python
# scripts/metrics.py
import numpy as np
from sklearn.metrics import (roc_auc_score, average_precision_score, f1_score,
                             balanced_accuracy_score, brier_score_loss, confusion_matrix)

def evaluate(y_true, y_score, threshold=0.5):
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        'auc_roc':   roc_auc_score(y_true, y_score),
        'auc_pr':    average_precision_score(y_true, y_score),   # honest under imbalance
        'f1':        f1_score(y_true, y_pred),
        'balanced_acc': balanced_accuracy_score(y_true, y_pred),
        'brier':     brier_score_loss(y_true, y_score),          # calibration
        'sensitivity': tp / (tp + fn) if tp + fn else float('nan'),
        'specificity': tn / (tn + fp) if tn + fp else float('nan'),
        # Clinical microbiology error rates (CLSI/FDA convention)
        'very_major_error': fn / (tp + fn) if tp + fn else float('nan'),  # R called S, dangerous
        'major_error':      fp / (tn + fp) if tn + fp else float('nan'),  # S called R, wasteful
        'n': int(len(y_true)), 'prevalence': float(np.mean(y_true)),
        'threshold': threshold,
    }
```

**Why AUPRC and not just AUC:** your global resistance rate is 0.166. ROC-AUC flatters minority-class problems; average precision does not.

**Why VME/ME:** these are the metrics clinical microbiology actually uses. FDA guidance for AST devices asks for **very major error ≤ 1.5 to 3%** and **major error ≤ 3%**. Quoting your models against that standard, even to show you miss it, puts the work in the language of the field, and it directly justifies the 0.40 threshold on the forecast page.

**Why Brier/calibration:** your UI prints "Resistance Probability 54.3%". If the model is uncalibrated, that number is not a probability and the display is misleading. Plot a reliability curve per experiment.

### 2.3 Always report per-antibiotic, not just pooled

A pooled AUC of 0.88 can hide a drug at 0.55. Produce a per-antibiotic table (n, prevalence, AUC, VME) and sort ascending by AUC, the bottom five rows are your honest limitations section.

---

## 3. The experiment harness

Do not edit `train_models.py` per experiment. Build a config-driven runner so runs are reproducible and comparable.

```
experiments/
├── configs/
│   ├── A0_baseline.yaml
│   ├── A1_oof_encoding.yaml
│   └── ..
├── run.py                # loads a config, trains, evaluates, writes results
├── splits.py             # grouped/species/temporal splitters, shared by all runs
├── metrics.py            # §2.2
└── results/
    ├── A0_baseline/
    │   ├── metrics.json          # all metrics, per-antibiotic breakdown
    │   ├── predictions.csv       # y_true, y_score, genome_id, antibiotic
    │   ├── config.snapshot.yaml
    │   └── model/
    └── registry.csv              # one row per run, the comparison table
```

A config is the *entire* description of a run:

```yaml
# experiments/configs/A3_catboost.yaml
id: A3_catboost
track: A
description: CatBoost with ordered target statistics, replacing manual encoding
data:
  source: amr_output
  label_sources: [lab, computational]      # excludes mic_rule rows
split:
  strategy: grouped                        # grouped | random | species_holdout | temporal
  group_col: Genome ID
  test_size: 0.2
  seed: 42
features:
  base: [Taxon ID, Antibiotic, drug_class, genus, species, mic_sign,
         is_lab_confirmed, computational_f1, mic_value, mic_log, has_mic]
  target_encoding: none                    # none | oof | catboost_native
model:
  type: catboost
  params: {depth: 8, learning_rate: 0.05, iterations: 2000, auto_class_weights: Balanced}
threshold:
  strategy: maximize_f1                    # fixed | maximize_f1 | vme_constrained
  vme_budget: 0.03
```

**Non-negotiables for every run:** fixed seeds, the config snapshotted into the results folder, `predictions.csv` saved (you need raw scores for DeLong tests in §8), and one appended row in `registry.csv`.

**Also fix the metrics gap while you are here.** `train_models.py` currently prints AUC and discards it ([§11.5 of PROJECT_GUIDE.md](PROJECT_GUIDE.md)). Have the runner write `metrics.json` **next to the model artifact**, and have `LGBMResistancePredictor.status` read it. Then the UI badges stop being hand-transcribed and can never silently go stale.

---

## 4. Track A, tabular forecaster experiments

Run in this order. Each row changes **one** thing from the row above unless stated.

| ID | Strategy | What it tests | Effort | Expected |
|---|---|---|---|---|
| **A0** | Reproduce current pipeline exactly | Establishes the leaky baseline for comparison | ✅ done | **0.8243** |
| **A1** | A0 + out-of-fold encoding (§1.2) | Cost of removing leakage | ✅ done | **0.8225**, leakage worth 0.002 |
| **A2** | A1 + grouped split (§1.3) | Cost of removing genome leakage | ✅ done | **0.8232**, the corrected baseline |
| **A3** | Logistic regression on the same features | Is gradient boosting earning its complexity? | ✅ done | **0.8024**, boosting worth +0.018 |
| **A4** | Random forest *(XGBoost still pending install)* | Bagged vs boosted trees | ✅ done | **0.8173**, boosting worth +0.003, not significant |
| **A5** | CatBoost with native ordered target statistics | Principled alternative to hand-rolled encoding; best-in-class for high-cardinality categoricals | 3h | often +0.01 to 0.02 |
| **A6** | Class-imbalance sweep: `is_unbalance` vs `scale_pos_weight` vs SMOTE vs focal loss | Which imbalance treatment actually helps AUPRC | 4h | SMOTE usually *hurts* trees. **Note:** `A6_lab_only` in the registry is the label-provenance run, not this |
| **A7** | Per-drug-class models (one per beta-lactam / carbapenem / …) vs one global model | Does specialisation beat shared structure? | 4h | global usually wins on rare drugs |
| **A8** | Multi-task: predict all antibiotics per isolate jointly | Exploits cross-resistance correlation | 6h | promising, harder to serve |
| **A9** | Probability calibration (Platt / isotonic on a validation fold) | Makes the displayed % an actual probability | 2h | AUC unchanged, Brier improves. **Note:** `A9_threshold_f1` in the registry is the threshold run, not this |
| **A10** | Monotonic constraint: P(R) non-decreasing in `mic_value` | Encodes biology, resists nonsense outputs | ✅ done | **0.8222**, costs 0.001, worth taking |
| **A11** | Re-test pseudo-labelling under the fixed protocol | The notebook's gain was 0.8881 → 0.8872, i.e. none | 3h | expect confirmation it doesn't help |

**A5 and A10 are the two I would prioritise** after the hygiene runs. CatBoost's ordered boosting is the textbook answer to exactly the leakage you have, which makes it a natural narrative: *"we replaced a leaky hand-built encoder with a method designed to avoid that failure."* A10 is cheap and directly defensible, a model that predicts *less* resistance at a higher MIC is indefensible, and a monotonic constraint makes that impossible by construction.

**A7 note:** your drug-class distribution is extremely skewed (beta_lactam 30,728 rows vs rifamycin 1). Per-class models will fail on the tail; report that as the reason a global model with `drug_class` as a feature is the right design.

---

## 5. Track B, genome model experiments

### B0. Fix the scaler bug first 🔴

The current k-mer model never runs at inference ([PROJECT_GUIDE.md §11.1](PROJECT_GUIDE.md)); the fix already exists in [amrpredict-lib/src/amrpredict/kmer.py](amrpredict-lib/src/amrpredict/kmer.py). Port it to [backend/ml_models/resistance_predictor.py:158](backend/ml_models/resistance_predictor.py#L158) before measuring anything, or every Track B number describes a random heuristic.

| ID | Strategy | What it tests | Effort | Expected |
|---|---|---|---|---|
| **B0** | Fix scaler + re-measure RandomForest | The true current baseline | 1h | unknown, this is the point |
| **B1** | Grouped-by-genome split | How much of the old AUC was genome memorisation | 2h | likely a large drop |
| **B2** | k sweep: k = 3, 4, 5, 6 (64 / 256 / 1,024 / 4,096 features) | Resolution vs overfitting trade-off | 4h | k=5 or 6 often better |
| **B3** | Frequency normalisation: raw vs CLR vs TF-IDF | Compositional data handled properly | 3h | CLR is the principled choice |
| **B4** | LightGBM / linear SVM instead of RandomForest | Model-family comparison on identical features | 3h | GBM usually +0.02 to 0.04 |
| **B5** | Two-branch MLP from `resistance_prediction_model.ipynb` | Does the deep model you designed beat the RF that replaced it? | 6h | close; report honestly either way |
| **B6** | **AMR gene presence features** (AMRFinderPlus / CARD / ResFinder) | Mechanism-aware features vs blind composition | 10h | **largest expected gain** |
| **B7** | B6 features + k-mers combined | Complementarity | 3h | best overall model |
| **B8** | Species hold-out | Does composition generalise across organisms? | 2h | expect collapse; important finding |

**B6 is the scientifically strongest experiment in this document.** 4-mer composition is mostly a species fingerprint, it tells you *which organism* this is, and the model then predicts that organism's typical resistance. Running a real AMR gene caller and using presence/absence of `blaCTX-M`, `mecA`, `vanA`, `gyrA` mutations etc. as features tests whether the model has learned **mechanism** rather than **taxonomy**. Pairing B6 against B0 gives you the most defensible sentence in your thesis, whichever way it lands.

**B8 makes the same point from the other side.** If a k-mer model trained on *E. coli* + *Staph* collapses on *Pseudomonas*, that is direct evidence that composition ≈ taxonomy. Design the experiment to answer it deliberately rather than leaving it as a caveat.

---

## 6. Track C, the timeline simulation

It has no ground truth, so it cannot be "trained" in the current setup. Three honest options:

| ID | Strategy | Effort | Notes |
|---|---|---|---|
| **C1** | Sensitivity analysis | 3h | Sweep `speed` and `peak` ±30%, plot how `failure_week` moves. Turns a black box into a characterised model |
| **C2** | Literature calibration | 6h | Fit the logistic curve to published resistance-evolution series (e.g. serial-passage MIC data) and report fit error. Upgrades it from "hand-set constants" to "calibrated against N published curves" |
| **C3** | Fix the >100% compartment bug and re-run | 2h | Currently an `xfail` in the library; fixing it changes published numbers, so do it as a versioned change with before/after |

Do **C1 at minimum**, it costs an afternoon and pre-empts the obvious viva question *"where did 0.18 come from and what if it's wrong?"*

---

## 7. Ablations: which inputs actually earn their place

This connects directly to the evidence panel now on `/forecast`. That panel tells a user which inputs the model *used*; these ablations tell you which inputs are *worth* collecting.

Train A2 (the clean baseline) repeatedly, each time dropping one input group:

| Ablation | Drops | Answers |
|---|---|---|
| `no_mic` | `mic_value`, `mic_log`, `has_mic`, `mic_sign` | How much is the model just reading the MIC? |
| `no_taxon` | `Taxon ID`, `taxon_ab_resistance_rate` | Is the broken taxon field costing anything? |
| `no_encodings` | all three rate features | Is the model learning, or just recalling base rates? |
| `no_organism` | genus, species, and their encodings | Value of organism identification |
| `drug_only` | everything but `Antibiotic` + `drug_class` | The floor, matches the "Population-level estimate" path in the UI |

The `drug_only` row is the most useful output of this whole section: it is the numeric answer to *"what does a user get when they fill in nothing?"*, and it belongs in the UI next to the population-level badge.

I already measured the live-model version of this for amoxicillin/clavulanic acid, antibiotic alone p=0.543, adding an MIC of 4 moves it to p=0.103, adding genus/species moves it 1 point. The ablation study generalises that across all drugs with proper metrics.

**Also fix the taxon grouping while you are in there.** `taxon_ab` is grouped on PATRIC strain-level IDs ([train_models.py:187](backend/train_models.py#L187)), which is why species IDs like 562 never match. Re-grouping on species-level taxonomy is a one-line change and its own experiment: does a taxon feature that users can actually supply beat one that silently never matches?

---

## 8. Comparing runs statistically

Two AUCs differing by 0.004 are not different. Say so with a test, not a vibe.

| Comparison | Test | Note |
|---|---|---|
| Two models, same test set, AUC | **DeLong** (`scipy` + implementation, or `fastDeLong`) | Paired, correct for correlated ROC curves |
| Two models, same test set, calls | **McNemar** on the discordant pairs | For a fixed threshold |
| Any metric, confidence interval | **Bootstrap**, 1,000 resamples, grouped by `Genome ID` | Resample *genomes*, not rows |

```python
def bootstrap_ci(y_true, y_score, groups, metric, n=1000, seed=42):
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    stats = []
    for _ in range(n):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([np.flatnonzero(groups == g) for g in pick])
        if len(np.unique(y_true[idx])) < 2:
            continue
        stats.append(metric(y_true[idx], y_score[idx]))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))
```

Report every headline number as `0.881 [0.873-0.889]`. It is a small amount of work that visibly raises the level of the whole project.

---

## 8b. What 19 runs have shown

Measured, not predicted. Full table in [experiments/RESULTS.md](experiments/RESULTS.md),
interpretation in [experiments/HANDBOOK.md §11](experiments/HANDBOOK.md).

| Question | Answer |
|---|---|
| Honest baseline? | **AUC 0.8232 [0.8200-0.8269]**, full data, grouped split, out-of-fold encoding |
| Cost of target leakage? | 0.002, not significant at this scale (§1.2) |
| Cost of genome leakage? | ~0 for the tabular model (§1.3) |
| Best algorithm? | LightGBM 0.8201 > random forest 0.8173 > logistic 0.8024, on an identical 400 k sample. Only the linear gap is significant |
| Value of an MIC? | +0.020 pooled; +0.095 on the lab subset where MICs are actually present |
| Value of the rate encodings? | +0.001, the trees rebuild the same information from `Taxon ID` and `Antibiotic` |
| Floor with drug only? | **0.6545**, the measured value of the UI's "Population-level estimate" |
| Generalise to an unseen genus? | **No.** 0.5971 with 82.9% major error |
| More data? | Curve is flat from 50 k rows. Full data buys precision and tail coverage, not accuracy |
| Biggest lever? | **The threshold.** 0.40 → 0.47 moves ME 46% → 34% and VME 10% → 20%. No model change moved AUC by more than 0.002 |

The flat learning curve is the main finding: the model is **feature-limited,
not data-limited**, which is the argument for Track B6 (AMR gene presence) over any
further tuning.

---

## 9. Suggested schedule

Assuming roughly one focused day per block:

| Block | Runs | Deliverable |
|---|---|---|
| **1. Foundations** | Data census, harness, metrics, splits | `registry.csv` exists; A0 reproduced |
| **2. Honesty pass** | A1, A2, B0, B1 | The real baselines, plus a "cost of leakage" table |
| **3. Model families** | A3, A4, A5, B2, B4 | Which algorithm wins, with CIs |
| **4. Going deeper** | A6, A9, A10, B3, B5 | Imbalance, calibration, constraints |
| **5. The scientific question** | B6, B7, B8, A7 | Mechanism vs composition, your headline result |
| **6. Ablations + timeline** | §7 set, C1 | Input-value table; timeline sensitivity |
| **7. Write-up** | n/a | Comparison table, per-antibiotic appendix, decision on what to ship |

If you only have time for two blocks, do **1 and 2**. A corrected baseline with confidence intervals is worth more than five uncontrolled model variants.

---

## 10. What goes in the report

1. **The leakage correction**, stated plainly: "an earlier version reported 0.9255; that figure was produced with target encodings fitted on the full dataset. Under out-of-fold encoding and grouped splitting the same model scores X." Examiners reward finding this in your own work far more than they reward a high number.
2. **One comparison table**: run ID, strategy, AUC-ROC [CI], AUPRC, VME, ME, Brier, notes. Sorted by AUPRC.
3. **Per-antibiotic appendix**, ascending by AUC, with n and prevalence.
4. **The mechanism-vs-taxonomy result** (B6/B7/B8) as the discussion centrepiece.
5. **The ablation table** as the justification for the UI's evidence panel, you can say the interface was designed from measured feature value, not guesswork.
6. **Calibration plot** for whichever model you ship, justifying the probability shown on screen.
7. **What you chose to deploy and why**, and it does not have to be the highest-AUC model. Choosing a calibrated, monotonic, slightly weaker model for a clinical-facing tool is a defensible engineering decision, and saying so is a stronger finish than a leaderboard.

---

## 11. Pitfall checklist

Run through this before believing any result:

- [ ] Encodings fitted on train folds only (§1.2)
- [ ] Same genome never in both train and test (§1.3)
- [ ] `mic_rule`-labelled rows excluded from evaluation (§1.4)
- [ ] Test set split once and never inspected during development
- [ ] Threshold chosen on validation, never on test
- [ ] Seeds fixed and recorded in the config snapshot
- [ ] Metrics include AUPRC, VME/ME and calibration, not AUC alone
- [ ] Per-antibiotic breakdown checked for a drug near 0.5
- [ ] Confidence intervals bootstrapped by genome, not row
- [ ] Differences tested (DeLong/McNemar), not eyeballed
- [ ] `metrics.json` written beside the artifact so the UI cannot drift
- [ ] Antibiotic name variants normalised before grouping - `trimethoprim/sulfamethoxazole`, `trimethoprim-sulfamethoxazole`, `sulfamethoxazole/trimethoprim` and `co_trimoxazole` are currently four separate categories for one drug, each with its own rate

That last one is worth a dedicated cleaning pass: the vocabulary also contains `geamycin` and `trimotheprim` (typos), and `carbapenem` (a drug class sitting among drug names). Normalising these before training is a small change that shrinks the categorical space and makes every downstream comparison cleaner.
