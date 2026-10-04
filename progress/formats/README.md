# Handover formats

The data that passes between our three areas of work. Proposed by Hamza on 2026-09-25 (Day 1). Suleman and Ali: reply in the team channel or edit this file if something doesn't work for your side, then tick the Day 1 box in your tracker.

| Format | From → to | File |
|---|---|---|
| [1. Model metrics](#1-model-metrics-metricsjson) | Hamza → Suleman | `backend/trained_models/lgbm_metrics.json`, `kmer_metrics.json` |
| [2. Genome prediction response](#2-genome-prediction-response) | Hamza → Suleman | `POST /api/predict/` JSON |
| [3. Gene matrix](#3-gene-matrix) | Ali → Hamza | `experiments/genome/features/gene_matrix.parquet` + `gene_info.csv` |
| [4. Timeline + RL response](#4-timeline--rl-response) | Ali → Suleman | `POST /api/timeline/` JSON |
| [5. Batch forecast CSV](#5-batch-forecast-csv) | user → Suleman → Hamza's model | upload to `POST /api/forecast/batch/`, JSON back |
| [6. Genome runs for /models](#6-genome-runs-for-models) | Hamza → Suleman | `genome_runs` in `backend/trained_models/model_report.json` |

Samples: [`lgbm_metrics.sample.json`](lgbm_metrics.sample.json), [`genome_response.sample.json`](genome_response.sample.json), [`timeline_response.sample.json`](timeline_response.sample.json).

---

## 1. Model metrics (`metrics.json`)

One file per served model, written **beside the artifact** so the numbers can't drift from the model:

| Model | File | Written by |
|---|---|---|
| LightGBM forecaster (`/forecast`) | `backend/trained_models/lgbm_metrics.json` | `experiments/promote.py <run_id>` |
| K-mer RandomForest (`/predict`) | `backend/trained_models/kmer_metrics.json` | `experiments/evaluate_shipped.py` |
| **Complete-genome k-mer LightGBM (`/predict`, since 2026-09-29)** | `backend/trained_models/genome/genome_metrics.json` (headline = lab AUC) | `experiments/promote.py <run> --genome` |

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
| `genes_found[].subclass`, `genes_found[].name` | string | **2026-09-30**, optional | AMRFinderPlus subclass (e.g. `cephalosporin`, `carbapenem`) and the element's full name, for a tooltip |
| `model_run` | string | **2026-09-30** | Run id of the genome model that answered |
| `species_detected` | object | **2026-09-30**, gene model only | `species`, `genus` (from the upload's 6-mer profile; `null` when nothing is close), `distance`, `amrfinder_organism` (the `--organism` AMRFinderPlus ran with, or `null`). Show as "Identified as *Escherichia coli*" |
| `warning` | string | **2026-09-30** | Present when AMRFinderPlus failed on this upload and the k-mer model answered instead (then `genes_found` is absent). **Show as a warning** |

**How `/predict` shows it** (Suleman, 2026-09-28, `frontend/templates/_genes_panel.html`): absent → one "Not searched" line and no panel; `[]` → "searched, none found"; a list → chips, `relevant` ones first, and a sentence on whether they support the call. If no entry has `relevant`, the genes are one plain list. If the genome model sends no `top_kmers`, the k-mer cards and chart are hidden, so they can be left out. Preview with the sample above at `/predict/sample` on a local run.

**Which model answers** (2026-09-30): `backend/ml_models/genome_predictor.py` serves the gene model (`trained_models/genome_genes/`, from `promote.py <run> --genome` on a gene run) when AMRFinderPlus is installed on the server, else the k-mer model (`genome/`). The gene model sends `genes_found`, `species_detected` and no `top_kmers`; the k-mer model sends `top_kmers` and no `genes_found`. `/api/health/` → `models.kmer_resistance.searches_genes` says which. AMRFinderPlus is found via `AMRFINDER_PATH`, `PATH` or a conda env named `amrfinder`; `AMRFINDER_THREADS` (default 4) and `AMRFINDER_TIMEOUT` (default 100 s, under the page's 120 s wait) tune it.

**Refusals** (Suleman, 2026-09-29): when the model refuses instead of predicting (the genome model: under 100,000 bp; the old RandomForest: under 100 bp), `/api/predict/` answers **HTTP 400** with `error` (and `sequence_length`), and `/predict` shows the reason. `POST /api/reload/` chooses the `/predict` model again, so a model promoted while the server runs takes over without a restart.

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

`POST /api/timeline/` (`backend/ml_models/mutation_timeline.py`). Proposed by Ali and agreed with Suleman on 2026-09-26 (checked against the live response). Sample: [`timeline_response.sample.json`](timeline_response.sample.json).

Request is unchanged: `fasta_text` or `fasta_file`, `antibiotic`, `n_weeks` (1 to 52).

### Timeline (Week 3, after the T3.1 fix)

Today's fields stay. What changes:

| Field | Type | Status | Meaning |
|---|---|---|---|
| `antibiotic` | string | existing, **now canonical** | Same spelling map as the predictors: `rifampin` comes back as `rifampicin` and gets its profile (before, it fell to the generic one) |
| `timeline[].week` | int | existing | 0 to `n_weeks` |
| `timeline[].susceptible_fraction`, `intermediate_fraction`, `resistant_fraction` | number 0–100 | existing, **now a partition** | Percent of the population. The three add up to 100 every week (±0.01 from rounding). Today they can exceed 100 |
| `timeline[].cumulative_mutations`, `mic_fold_change`, `treatment_effective` | | existing | Unchanged |
| `failure_week` | int or `null` | existing | First week with `resistant_fraction` ≥ 50; `null` = never in the window |
| `model_used` | string | existing, **value changed** | Always `Biological Simulation`. The `CNN-LSTM (trained)` label goes, since no trained model exists |
| `simulation` | bool | **new** | Always `true`. Show "Simulation, not a trained model" next to the chart and in exports |
| `seed` | int | **new** | Random seed used. Same inputs and seed give the same response |
| `calibration` | object or `null` | **new, Week 3** | `{curves, drugs, rmse}` once fitted to published curves (T3.1); `null` before that, so show "not calibrated". Types below. **Filled since 2026-09-28** from `backend/trained_models/timeline_calibration.json` |

### RL panel (Week 4)

A new `rl` object. **Field absent = RL not run** (Week 1 to 3, or the agent is not trained for this drug); hide the panel then.

| Field | Type | Meaning |
|---|---|---|
| `rl.drugs` | list of strings | Drugs the agent can choose from each week (canonical names, e.g. `rifampicin`). **The requested `antibiotic` is always in it, first** |
| `rl.n_weeks` | int | Same as the top-level `n_weeks` |
| `rl.agent` | string | e.g. `PPO (stable-baselines3)` |
| `rl.best` | string | `name` of the policy with the latest `failure_week`; ties broken as below |
| `rl.policies` | list | The RL policy and the fixed baselines, RL first. Always includes `always_<requested antibiotic>` |
| `rl.policies[].name` | string | `rl`, `always_<drug>` or `cycle` |
| `rl.policies[].label` | string | For the legend, e.g. `RL agent`, `Always ciprofloxacin`, `Cycle A → B → C` |
| `rl.policies[].policy` | list of strings, length `n_weeks` | Drug given in weeks 1 to `n_weeks` |
| `rl.policies[].resistant_fraction` | object: drug → list of numbers 0–100, length `n_weeks + 1` | Resistant percent per drug, week 0 to `n_weeks`. One line per drug on the chart |
| `rl.policies[].failure_week` | int or `null` | First week the drug given that week has `resistant_fraction` ≥ 50 |
| `rl.policies[].total_reward` | number | Episode reward (higher is better). For the comparison table only |
| `rl.policies[].effective_weeks` | int, optional | Weeks the drug given was under 50% resistance, out of `n_weeks`. *Added 2026-09-30 (Suleman)*: fairer than `failure_week` alone, since a policy can fail early yet work most weeks |
| `rl.policies[].mean_burden` | number 0–100, optional | Resistant percent of the drug given, averaged over the weeks (lower is better). *Added 2026-09-30 (Suleman)* |

**Built by** `experiments/evolution/rl_output.py` (`rl_block(antibiotic, n_weeks, seed, agent=...)`, Suleman 2026-09-30) from Ali's `rl_env.py`, which keeps its own units (0–1 shares, "never failed" = week `weeks + 1`); the conversion to this format happens only there. Every policy runs on the same seed. Baseline names: `always_<drug>`, `cycle`, `cycle_4`, `lowest_resistance`; the panel shows any name by its `label`. Tests: `experiments/evolution/test_rl_output.py`.

**Display rules:** label the panel "Simulation + RL policy (not trained on patient data)". Percentages with one decimal. Show the policy as a row of drug chips per week under the chart.

### Answers to Suleman's questions (2026-09-26)

1. **Tie for `rl.best`.** Compare `failure_week` with `null` (never fails in the window) as later than any week. If several policies share the latest, the higher `total_reward` wins; if that ties too, the one earlier in `rl.policies` wins, so the RL agent wins a full tie. The backend applies this rule, so the UI can trust `rl.best` without re-deriving it.
2. **Is the requested drug always in `rl.drugs`?** Yes, always first, and `rl.policies` always has an `always_<requested antibiotic>` baseline, which is the same curve as the main timeline. If the agent was not trained for the requested drug, `rl` is absent rather than answering for other drugs.
3. **`calibration` types.**

| Field | Type | Meaning |
|---|---|---|
| `calibration.curves` | int | Published curves used in the fit |
| `calibration.drugs` | list of strings | Canonical names of the drugs fitted; the requested drug may not be one of them |
| `calibration.rmse` | number | Root mean squared error of the fit, in percentage points on the 0–100 `resistant_fraction` scale, averaged over curves |

Show `rmse` with one decimal ("fit error ±4.2 points against 7 published curves").

Added 2026-09-28 (Ali), optional, so a reader of the three fields above is unaffected:

| Field | Type | Meaning |
|---|---|---|
| `calibration.lab_curves`, `calibration.surveillance_curves` | int | The split of `curves`: lab evolution (log2 IC50, days) and hospital surveillance (% resistant, years). `rmse` averages the surveillance curves only, the ones on the 0 to 100 scale |
| `calibration.median_r2` | number | Median R² of the fits |
| `calibration.parameters_changed` | bool | `false`: the fit checks the curve's shape; the hand-set constants are not replaced, because no source is in weeks |
| `calibration.sources` | list of strings | Citations |
| `calibration.note` | string | One sentence for the page: the weeks are illustrative |

`drugs` holds the five lab drugs and `carbapenems` (a class, from the surveillance data), so most requested drugs are not in it; `/timeline` says so under the result.

---

## 5. Batch forecast CSV

`POST /api/forecast/batch/` (`backend/api/views.py`, `BatchForecastView`). Defined by Suleman on 2026-09-27. The `/forecast` page's "Upload CSV" tab sends the file; a sample is at `/forecast/template.csv`.

### Upload

A UTF-8 CSV (a byte-order mark is fine) in the multipart field `file`, one isolate per row. At most **10,000 rows** and **2 MB**, else 413; 5 uploads a minute per visitor, else 429. Header names are case-insensitive; other columns are ignored; blank lines are skipped.

| Column | Required | Rule | Passed to `features_frame()` as |
|---|---|---|---|
| `antibiotic` | yes | Must be in the model's vocabulary after the alias map (`rifampin` → `rifampicin`), else the row gets an error | `antibiotic` |
| `genus`, `species` | no | Free text; empty = `unknown` | `genus`, `species` |
| `taxon_id` | no | Positive whole number (`562.0` is accepted as 562) | `taxon_id`, mapped to species level by the model |
| `mic_value` | no | Number greater than 0, in mg/L | `mic_value` |
| `mic_sign` | no | One of `=`, `==`, `<`, `<=`, `>`, `>=`, `≤`, `≥`, `=<`, `=>`. Ignored when `mic_value` is empty, as on `/forecast` | `mic_sign`, normalised by the model |

Valid rows are predicted in **one** `predict_frame()` call, so a row gets the same probability as the single `/forecast` form.

### Response

| Field | Type | Meaning |
|---|---|---|
| `rows[]` | list, same order and length as the input rows | One result per input row |
| `rows[].row` | int | 1-based row number, counting data rows only (not the header or blank lines) |
| `rows[].antibiotic`, `genus`, `species`, `taxon_id`, `mic_value`, `mic_sign` | string | The input as given; `antibiotic` is canonical on rows without an error |
| `rows[].prediction` | `"Resistant"` / `"Susceptible"` / `""` | At `threshold`; empty on a row with an error |
| `rows[].probability` | number 0–1 or `null` | Calibrated P(resistant); `null` on a row with an error |
| `rows[].error` | string | Empty = predicted. Otherwise why the row was not used, e.g. `unknown antibiotic "x" (the model was not trained on it)` |
| `summary` | object | `rows`, `predicted`, `errors`, `resistant`, `susceptible`, and `by_antibiotic`: `[{antibiotic, n, resistant}]`, most rows first |
| `threshold` | number | The served model's `default_threshold` |
| `model_run`, `calibrated` | string, bool | As in the `/api/forecast/` response |

Errors about the whole file (no `antibiotic` column, not UTF-8, no rows, too many rows, too large) come back as `{"error": "..."}` with 400 or 413 instead.

**Results CSV** (`/export/batch.csv`): columns `row, antibiotic, genus, species, taxon_id, mic_value, mic_sign, prediction, probability_resistant, error`; a cell that would start a spreadsheet formula gets a leading apostrophe.

---

## 6. Genome runs for /models

*Requested by Suleman (2026-09-28) for the Genome models section; written by Hamza 2026-09-29. Suleman: edit this section if the page needs more.*

`experiments/export_report.py` writes `genome_runs` into `backend/trained_models/model_report.json` (served by `GET /api/models/`): every Track B run, kept out of `runs` because its dataset and labels differ from the tabular runs. Sorted by `clean_version`, then `id`.

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Run id (`experiments/results/<id>/`) |
| `description` | string | One line from the config |
| `clean_version` | string | `v5` or `v6`. **Show the v6 runs** (the current figures, `*_v6`); older runs are history |
| `model` | string | `lightgbm` or `random_forest` |
| `features` | string | `genes`, `k-mers`, `genes + k-mers`, or `no genome features` (a baseline on the same rows) |
| `split` | string | `grouped`, `lineage (clone|close|broad|species)`, or `species_holdout (<Genus> held out)` |
| `plasmids_excluded` | bool | `true` for the current runs (plasmid-only records dropped) |
| `auc_roc` | number | All test rows. Partly circular for genome features: show it small, or not at all |
| `auc_roc_lab`, `auc_roc_lab_ci` | number, `[lo, hi]` | **The headline**: lab-confirmed test rows, 95% CI resampling genomes (or lineages under the lineage split) |
| `n_lab`, `lab_genomes` | int | Lab test rows and genomes behind `auc_roc_lab`; always show `n_lab` |

Suggested grouping on the page: the B6 table (`B6L_*_v6`, `B4L_*_v6`, `B1L_*_v6`, `B7L_*_v6`), the unseen-genus table (`B8_*_v6`, genes vs no genes per genus), the lineage table (`LL_*_v6`). The same tables, with commentary, are in `experiments/GENOME_RESULTS.md`.

The model `/predict` serves is not in this list twice: its re-test is `shipped.kmer` (as for the old model), and its metrics file is `backend/trained_models/genome/genome_metrics.json` (format §1), which `/api/health/` returns as `models.kmer_resistance.metrics`.

---

## 7. Training genomes of the served models

**Written by** `experiments/promote.py` whenever a model is promoted (or `promote.py <run> --split-only`, with `--genome` for a genome model); **read by** `backend/ml_models/training_genomes.py`. Added 2026-10-04 for the "fill from Genome ID" helper on `/forecast` (Suleman).

| File | Model | Train genomes | Test genomes |
|---|---|---|---|
| `backend/trained_models/lgbm_split_genomes.json.gz` | `/forecast`, `D3_forecaster_deploy_v7` | 351,442 | 88,100 |
| `backend/trained_models/genome/split_genomes.json.gz` | `/predict` k-mer model, `G_kmer_deploy` | 19,804 | 4,915 |
| `backend/trained_models/genome_genes/split_genomes.json.gz` | `/predict` gene model, `G_genes_deploy` | 19,804 | 4,915 |

Gzipped JSON: `{"run_id", "split", "clean_version", "train": [Genome IDs], "test": [Genome IDs]}`, IDs as text. Rebuilt from the run's config and checked against its test-row count; `train` includes the validation genomes (used to stop training and pick the threshold and calibration, so not a fair test either).

```python
from ml_models.training_genomes import genome_status
genome_status(settings.TRAINED_MODELS_DIR, '562.1234')
# {'forecast': {'run_id': 'D3_forecaster_deploy_v7', 'role': 'test',
#               'detail': 'not used in training: a fair test of the model'},
#  'genome_kmers': {...}, 'genome_genes': {...}}      # a model with no file is left out
```

`role`: `'test'` = a fair test; `'train'` = the model learned from it, so its prediction looks better than on a new genome (show a caution); `None` = not in that model's data (e.g. no lab label, or no complete assembly for the genome models). First call reads the file (0.16 s), later calls take microseconds.

