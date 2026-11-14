# Data and training

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 5. Data pipeline and training

### The source data

| Dataset | Origin | Role |
|---|---|---|
| AMR phenotype CSVs | BV-BRC / PATRIC, one file per species | Labels + MIC + metadata → LightGBM |
| Genome FASTAs | GenBank, `taxon_<id>_<Genus>_<species>/` folders | Sequences → K-mer model |
| Mapped CSVs | Produced by `scripts/fasta_amr_map.py` | The join of the two |

### `scripts/fasta_amr_map.py`: the join

The two sources share no key directly, so this script builds one. CSV files are named `amr_taxon_108981_Acinetobacter_schindleri.csv` and FASTA folders `taxon_108981_../108981.12345.fasta`. It extracts the **taxon ID** from each filename to pair a CSV with a folder, then matches each row's **Genome ID** to a FASTA filename stem. Output per species: a `_mapped.csv` (original columns + `fasta_path`) and an `_unmatched.csv`, plus a global `mapping_summary.csv` with match percentages. Everything downstream depends on that `fasta_path` column.

### `backend/train_models.py`: the production trainer

Two functions, run with `--model lgbm|kmer|all`.

**`train_lgbm()`**
1. Load every CSV in `Data/amr_output/` and concatenate. (Until 2026-09-25 it read only the first 500 files of a directory listing; `--max-files N` now takes a seeded random subset instead.)
2. Clean (`clean_amr_data`): parse `Measurement` into `mic_sign` + `mic_value` with regex; split `Genome Name` into genus/species; map phenotypes to binary; extract the F1 score out of the free-text `Computational Method Performance` column; deduplicate on (Genome ID, Antibiotic), keeping lab-confirmed rows first.
3. Build the three target-encoding tables.
4. Split 80/20 stratified, then carve 15% of train for validation.
5. Train with `is_unbalance=True`, `num_leaves=63`, `lr=0.05`, up to 500 rounds with early stopping at 30. The shipped model stopped at **217 trees**.
6. Print AUC + classification report, dump test predictions to `report_figures/`, save 5 artifacts.

**`train_kmer()`**
1. Load every mapped CSV (falling back to `sample_mapped_output/` if the full set is absent). Until 2026-09-25 it read only the first 200.
2. For each row, read the FASTA at `fasta_path`, with a path-repair step, because the CSVs contain Windows paths written on another machine. Sequences are cached in a dict so a genome referenced by 20 antibiotic rows is read once.
3. Build the 321-vector, fit `StandardScaler` **on the 256 k-mer columns only**, train the forest, report, pickle `{model, scaler, ab_list, ALL_KMERS}`.

That "256 columns only" decision is correct in training and is exactly what inference gets wrong ([§11.1](known-issues.md)).

### Training from the web UI

`/train` → Flask → `POST /api/train/` → Django spawns a **daemon thread** running the trainer and returns `{"status": "Training started"}` immediately. The page asks for the admin password, which Flask sends as the `X-Admin-Token` header; without the backend's `ADMIN_TOKEN` the request gets 401 (503 when no token is configured). The new model is written to `backend/trained_models/candidates/<model>/`, never over the served model, and the served model is not reloaded: a candidate goes live only through `experiments/promote.py`. Progress shows only in the backend's console.

### 5.4 The experiment harness - `experiments/`

`train_models.py` trains the model the app serves. `experiments/` is a separate
system for training *candidate* models and comparing them, without touching
`backend/trained_models/`.

It exists because the original pipeline cannot answer "is variant A better than
variant B?" honestly, it fits target encodings on the full dataset before
splitting, splits rows randomly so one genome lands on both sides, caps itself
at 500 of the 3,655 CSVs, and prints its metrics to a console log that is then
discarded.

The harness fixes each of those and adds an audit trail:

| | |
|---|---|
| **Input** | all 3,655 CSVs → 1,525,796 clean rows (17× what `train_models.py` reads) |
| **Split** | genome-grouped by default; random and species-holdout available |
| **Encoding** | out-of-fold by default; the leaky version kept only for comparison |
| **Algorithms** | LightGBM, logistic regression, random forest, XGBoost, CatBoost, one file each under `algorithms/` |
| **Metrics** | AUC, AUPRC, F1, Brier, plus clinical VME/ME, with bootstrap CIs resampled by genome |
| **Output** | per-run `metrics.json`, `predictions.csv`, config snapshot, saved model, and a row in `results/registry.csv` |

```bash
python experiments/run.py experiments/configs/A2_oof_grouped.json
python experiments/report.py                    # comparison table
python experiments/predict.py --list            # saved models you can reload
```

Twenty-two runs so far. The headline numbers: the corrected baseline is **AUC 0.823**
(against 0.644 for the shipped artifact on genomes it never saw, see [§10](results.md)),
algorithm choice moves almost nothing, and the **threshold is the
highest-leverage decision in the project**, at the production 0.40, major error is 46%.

Two scripts turn the results into the web app's report pages:

```bash
python experiments/evaluate_shipped.py   # re-test the deployed models (~2 min)
python experiments/export_report.py      # write backend/trained_models/model_report.json
```

Full documentation in [experiments/HANDBOOK.md](../experiments/HANDBOOK.md); the plan
behind it in [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md).

## 6. The notebooks, where the models came from

**The current models** are in `notebooks/01_forecaster_model.ipynb`, `02_genome_models.ipynb` and `03_evaluation.ipynb` (2026-10-13): each trains or checks a served model with the project's own code, saved with its outputs, and reproduces the published run exactly. `notebooks/README.md` describes them.

The **July notebooks** below, where the first models came from, are kept as history in `notebooks/archive/`.

| Notebook | Cells | State | What it contains |
|---|---|---|---|
| `archive/LightGBM_Model_Improved.ipynb` | 10 | ✅ with outputs | The real LightGBM development run, audit, cleaning, 5-fold CV, pseudo-labelling, final retrain |
| `archive/resistance_prediction_model.ipynb` | 38 | outputs cleared | A **two-branch Keras MLP** (k-mer branch + antibiotic-embedding branch), the deep-learning design that the production RandomForest replaced |
| `archive/bacterial_mutation_timeline.ipynb` | 43 | partial outputs | A **CNN-LSTM** with three heads (nucleotide, position, mutation probability), trained against per-antibiotic consensus genomes |
| `forecasting_formulation.ipynb` | n/a | removed 2026-10-13 | It was an empty file (0 bytes) |

Two things follow from this table:

- **The notebooks and the backend are different lineages.** The notebook LightGBM was trained on one `BVBRC_genome_amr.csv` (121,589 raw → 90,826 clean rows, global resistance rate 0.3081). The artifacts actually shipped in `backend/trained_models/` have a global mean of **0.1662** and 76 antibiotic rates, which means they came from a `train_models.py` run over the per-species `amr_output/` CSVs, not from the notebook. Both are legitimate; just don't quote a notebook number for a backend artifact.
- **The deep-learning models were never deployed.** `mutation_timeline.py` looks for `mutation_timeline_model.pkl` but never uses it: the simulation always runs, and since 2026-09-26 the response and `/api/health/` say so whether or not the file exists. Similarly the Keras MLP became a RandomForest. The code paths for the neural versions still exist, which is why the UI says "CNN-LSTM available for training", accurate but easy to misread.
