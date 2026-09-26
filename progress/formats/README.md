# Handover formats

The data that passes between our three areas of work. Proposed by Hamza on 2026-09-25 (Day 1). Suleman and Ali: reply in the team channel or edit this file if something doesn't work for your side, then tick the Day 1 box in your tracker.

| Format | From → to | File |
|---|---|---|
| [1. Model metrics](#1-model-metrics-metricsjson) | Hamza → Suleman | `backend/trained_models/lgbm_metrics.json`, `kmer_metrics.json` |
| [2. Genome prediction response](#2-genome-prediction-response) | Hamza → Suleman | `POST /api/predict/` JSON |
| [3. Gene matrix](#3-gene-matrix) | Ali → Hamza | `experiments/genome/features/gene_matrix.parquet` + `gene_info.csv` |
| [4. Timeline + RL response](#4-timeline--rl-response) | Ali → Suleman | `POST /api/timeline/` JSON |

Samples: [`lgbm_metrics.sample.json`](lgbm_metrics.sample.json), [`genome_response.sample.json`](genome_response.sample.json), [`timeline_response.sample.json`](timeline_response.sample.json).

---

## 1. Model metrics (`metrics.json`)

One file per served model, written **beside the artifact** so the numbers can't drift from the model:

| Model | File | Written by |
|---|---|---|
| LightGBM forecaster (`/forecast`) | `backend/trained_models/lgbm_metrics.json` | `experiments/promote.py <run_id>` |
| K-mer RandomForest (`/predict`) | `backend/trained_models/kmer_metrics.json` | `experiments/evaluate_shipped.py` |

**How the UI gets it:** `GET /api/health/` → `models.lgbm_forecasting.metrics` and `models.kmer_resistance.metrics` hold the file's contents unchanged (`null` if the file is missing, so show "not measured" rather than a number). `default_threshold` sits beside it.

### Fields

| Field | Type | Meaning |
|---|---|---|
| `schema` | string | `"amr-model-metrics/1"`. Bumped if a field changes meaning |
| `model` | string | `lightgbm_forecaster` or `kmer_random_forest` |
| `page` | string | The page it serves: `/forecast`, `/predict` |
| `run_id` | string | Experiment run that produced the model (`experiments/results/<run_id>/`) |
| `description` | string | One line, for a tooltip |
| `algorithm` | string | Human-readable, e.g. `LightGBM, monotone in MIC` |
| `trained_at`, `promoted_at` | ISO 8601 UTC or `null` | When |
| `git_commit`, `git_dirty` | string, bool | Code version that promoted it |
| `evaluation.split` | string | How the test set was chosen, e.g. `genome-grouped 80/20, seed 42` |
| `evaluation.test_genomes_unseen` | bool | Always `true`: no test genome was in training |
| `threshold` | number | Default decision threshold. The UI's threshold slider should start here |
| `threshold_rule` | string | How it was chosen, to show next to it |
| `calibration` | object or `null` | `{method, brier_before, brier_after, auc_before, auc_after}` |
| `test.auc_roc`, `test.auc_roc_ci` | number, `[lo, hi]` | Headline AUC with 95% CI (bootstrap over genomes) |
| `test.auc_pr` | number | Area under precision–recall |
| `test.f1`, `test.accuracy`, `test.recall`, `test.specificity` | number 0–1 | At `threshold` |
| `test.very_major_error` | number 0–1 | Resistant isolates called Susceptible (the dangerous error). `= 1 − recall` |
| `test.major_error` | number 0–1 | Susceptible isolates called Resistant |
| `test.brier` | number | Calibration error; lower is better |
| `test.n`, `test.prevalence`, `test.tp/fp/tn/fn` | numbers | Test-set size, resistant share, confusion matrix |
| `data.train_rows`, `data.test_rows`, `data.train_genomes`, `data.test_genomes` | int | Sizes |
| `data.antibiotics` | int | Antibiotics the model knows |
| `data.genera` | list of strings | Genera it was trained on |
| `data.source` | string | Where the data came from |

**Display rules:** show AUC as `0.823 [0.820–0.827]` (3 decimals), rates as percentages with one decimal. Never round a CI away. If `metrics` is `null`, show "not measured".

### Deprecated numbers

`0.93`, `0.9255` and `0.929` must not appear anywhere in the UI. They came from a leaky evaluation (README §10); `/models` explains them.

---

## 2. Genome prediction response

`POST /api/predict/` (`backend/ml_models/resistance_predictor.py`). Today's fields stay; one is added now and one in Week 3.

| Field | Type | Status | Meaning |
|---|---|---|---|
| `prediction` | `"Resistant"` / `"Susceptible"` | existing | Call at `threshold` |
| `probability` | number 0–1 | existing | P(resistant) |
| `confidence` | number 0–100 | existing | Probability of the returned call |
| `antibiotic` | string | existing, **now canonical** | e.g. `rifampin` comes back as `rifampicin` |
| `sequence_length`, `gc_content`, `top_kmers` | | existing | Unchanged |
| `threshold` | number | existing | Now defaults to `default_threshold` from the metrics when the request doesn't send one |
| `model_used` | string | existing, **values changed** | `RandomForest K-mer (trained)` · `Heuristic fallback` (the model failed on this input, **show a warning**) · `Heuristic (untrained)` (no model file) |
| `antibiotic_known` | bool | **new, Week 1** | `false` = the model never saw this drug, so the call reflects the genome alone. Show a warning |
| `genes_found` | list | **Week 3** | Resistance genes and mutations detected; `[]` = searched, none found; field absent = not searched (the k-mer model does not search) |
| `genes_found[].gene` | string | Week 3 | AMRFinderPlus symbol, e.g. `blaCTX-M-15`, `gyrA_S83L` |
| `genes_found[].drug_class` | string | Week 3 | AMRFinderPlus class, lower-case, e.g. `beta-lactam`, `quinolone` |
| `genes_found[].type` | `"gene"` / `"point_mutation"` | Week 3, optional | For grouping in the panel |
| `genes_found[].relevant` | bool | Week 3, optional | `true` if its class matches the requested antibiotic's class; show these first |

The LightGBM `/api/forecast/` response gains `model_run` (run id), `calibrated` (bool), and `model_used` can now also be `Heuristic fallback`.

---

## 3. Gene matrix

For B6/B7 (Weeks 2–3). Built by Ali from `Data/amrfinder_output/*.tsv`.

**`experiments/genome/features/gene_matrix.parquet`**

- One row per genome. The index is **`Genome ID` as a string**. IDs like `1001989.10` and `1001989.1` are different genomes, and a float column would merge them.
- One column per AMRFinderPlus `Element symbol` (genes **and** point mutations, e.g. `blaCTX-M-15`, `gyrA_S83L`), dtype `uint8`, values 0/1.
- **A genome that was searched and had no hits gets a row of zeros.** A genome that was not searched (download failed) has **no row**. That is how we tell "no genes" from "no data".
- Include only `Scope = core` hits for the main matrix (plus-scope stress/virulence genes are noise here). If that's easy, add a second file `gene_matrix_plus.parquet` with everything.

**`experiments/genome/features/gene_info.csv`**: one row per matrix column:

| Column | Example |
|---|---|
| `symbol` | `blaCTX-M-15` |
| `type` | `gene` or `point_mutation` |
| `class` | `BETA-LACTAM` (AMRFinderPlus `Class`) |
| `subclass` | `CEPHALOSPORIN` |
| `genomes` | how many genomes carry it |

`gene_info.csv` is what turns a matrix column into the `genes_found[].drug_class` in format 2.

**Dependency:** parquet needs `pyarrow`, which is not in the project `.venv` yet. Add `pyarrow` to the experiments requirements when the first matrix is committed.

**Sample first:** the 20-genome sample (Ali, Week 2 day 2) uses the same format, so the B6 code written against it works on the full matrix unchanged.

### Ali's notes (agreed 2026-09-26)

Agreed as above, with these details from the real AMRFinderPlus output:

- **Filter is `Scope = core` and `Type = AMR`.** Core scope also holds a few `STRESS` / `BIOCIDE` hits (5 in the first 184 genomes), so `core` alone would let them in.
- **`type`** comes from AMRFinderPlus `Subtype`: `POINT` and `POINT_DISRUPT` → `point_mutation`, everything else → `gene`.
- **"Searched" means `Data/amrfinder_output/<Genome ID>.tsv` exists.** The runner writes that file only when AMRFinderPlus succeeds, and a searched genome with no hits still gets a header-only file. So far most searched genomes have no core hits (many are *S. pneumoniae*), so expect a lot of zero rows. That is real, not missing data.
- **No `gene_matrix_plus.parquet` for now.** The run did not use `--plus`, so plus-scope genes were never searched. Re-running with `--plus` roughly doubles the run time; say if B6/B7 need it.
- **`pyarrow`** is in the new `experiments/requirements.txt` (`pip install -r experiments/requirements.txt`).
- **Builder and sample:** `experiments/genome/features/build_gene_matrix.py`. The 20-genome sample is in `experiments/genome/features/sample/` with the same two file names, so B6 code only changes the folder.

---

## 4. Timeline + RL response

`POST /api/timeline/` (`backend/ml_models/mutation_timeline.py`). Proposed by Ali on 2026-09-26, waiting for Suleman. Sample: [`timeline_response.sample.json`](timeline_response.sample.json).

Request is unchanged: `fasta_text` or `fasta_file`, `antibiotic`, `n_weeks` (1 to 52).

### Timeline (Week 3, after the T3.1 fix)

Today's fields stay. What changes:

| Field | Type | Status | Meaning |
|---|---|---|---|
| `timeline[].week` | int | existing | 0 to `n_weeks` |
| `timeline[].susceptible_fraction`, `intermediate_fraction`, `resistant_fraction` | number 0–100 | existing, **now a partition** | Percent of the population. The three add up to 100 every week (±0.01 from rounding). Today they can exceed 100 |
| `timeline[].cumulative_mutations`, `mic_fold_change`, `treatment_effective` | | existing | Unchanged |
| `failure_week` | int or `null` | existing | First week with `resistant_fraction` ≥ 50; `null` = never in the window |
| `model_used` | string | existing, **value changed** | Always `Biological Simulation`. The `CNN-LSTM (trained)` label goes, since no trained model exists |
| `simulation` | bool | **new** | Always `true`. Show "Simulation, not a trained model" next to the chart and in exports |
| `seed` | int | **new** | Random seed used. Same inputs and seed give the same response |
| `calibration` | object or `null` | **new, Week 3** | `{curves, drugs, rmse}` once fitted to published curves (T3.1); `null` before that, so show "not calibrated" |

### RL panel (Week 4)

A new `rl` object. **Field absent = RL not run** (Week 1 to 3, or the agent is not trained for this drug); hide the panel then.

| Field | Type | Meaning |
|---|---|---|
| `rl.drugs` | list of strings | Drugs the agent can choose from each week (canonical names, e.g. `rifampicin`) |
| `rl.n_weeks` | int | Same as the top-level `n_weeks` |
| `rl.agent` | string | e.g. `PPO (stable-baselines3)` |
| `rl.best` | string | `name` of the policy with the latest `failure_week` |
| `rl.policies` | list | The RL policy and the fixed baselines, RL first |
| `rl.policies[].name` | string | `rl`, `always_<drug>` or `cycle` |
| `rl.policies[].label` | string | For the legend, e.g. `RL agent`, `Always ciprofloxacin`, `Cycle A → B → C` |
| `rl.policies[].policy` | list of strings, length `n_weeks` | Drug given in weeks 1 to `n_weeks` |
| `rl.policies[].resistant_fraction` | object: drug → list of numbers 0–100, length `n_weeks + 1` | Resistant percent per drug, week 0 to `n_weeks`. One line per drug on the chart |
| `rl.policies[].failure_week` | int or `null` | First week the drug given that week has `resistant_fraction` ≥ 50 |
| `rl.policies[].total_reward` | number | Episode reward (higher is better). For the comparison table only |

**Display rules:** label the panel "Simulation + RL policy (not trained on patient data)". Percentages with one decimal. Show the policy as a row of drug chips per week under the chart.
