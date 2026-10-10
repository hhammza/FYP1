# Changes

What changed, why, and which documents were affected. Newest first.

Baseline is commit **`52ae361`** *(Add amrpredict library and macOS launcher, 2026-09-23)*, the last committed state before this work.

## Documents tracked here

| File | What it is | Status |
|---|---|---|
| [README.md](README.md) | How the whole system fits together | Created, then revised |
| [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md) | Staged plan for model experiments | Created, then corrected against measurements |
| [experiments/HANDBOOK.md](experiments/HANDBOOK.md) | Full reference for the training setup | Created, then revised |
| [experiments/README.md](experiments/README.md) | Usage card for the harness | Created, then revised |
| [experiments/RESULTS.md](experiments/RESULTS.md) | Generated comparison table | Regenerated after every run |
| [progress/formats/README.md](progress/formats/README.md) | Data handed between Ali, Hamza and Suleman | Created 2026-09-25, extended 2026-09-26 |
| [PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md) | The original long reference | **Unchanged**. Superseding facts are recorded in [README.md](README.md) instead |

---

## RL panel on /timeline (2026-10-10, Suleman)

| File | Change |
|---|---|
| [frontend/templates/_rl_panel.html](frontend/templates/_rl_panel.html), [mutation_timeline.html](frontend/templates/mutation_timeline.html) | New panel "Simulation + RL policy (not trained on patient data)", shown only when the response has `rl` (format §4): agent, drugs and the 50% rule; comparison table (first failed week or "Never in N weeks", `effective_weeks` and `mean_burden` when sent, reward, the `best` row marked) |
| [frontend/static/js/timeline.js](frontend/static/js/timeline.js), [static/css/components.css](frontend/static/css/components.css) | A chart of every policy (resistance of the drug given each week, end of week, with the 50% line); for the chosen policy, week chips with the drug given and a chart of every drug's resistance |
| [frontend/app.py](frontend/app.py) | `/timeline/sample`: the page filled with `progress/formats/timeline_response.sample.json`, local runs only |
| [frontend/tests/test_rl_panel.py](frontend/tests/test_rl_panel.py) | New: 8 tests |

Checked in Edge at 1366 px and 390 px (no page-wide scroll). Live data comes when Ali's agent fills `rl` in `/api/timeline/`; one open question for him, in his tracker: whether a week fails on resistance at the start or the end of the week.

---

## Every endpoint and page tested (2026-10-10, Suleman, T2.7)

| File | Change |
|---|---|
| [backend/tests/test_endpoints.py](backend/tests/test_endpoints.py) | New, 9 tests: the API routes no other file covered: `/api/antibiotics/`, `/api/models/` (and 404 when the report is missing), `/api/genes/` (and its 404), `/api/genes/matrix.csv` (24,926 rows × 2,733 0/1 columns, checked against `gene_hits.json`), `/api/genes/info.csv`, `/api/genes/<id>/` |
| [frontend/tests/test_pages.py](frontend/tests/test_pages.py) | New, 18 tests: all 11 pages with the backend up and down, the batch result page, `/reload`, favicon, `/api/antibiotics`, `/api/vocabulary`, `/api/organisms`, the gene CSV and lookup passthroughs, and the Content-Type and file name of every CSV and PDF export |

All 18 API routes and 25 frontend routes now have at least one test; 84 backend and 66 frontend tests, run by CI on every push.

---

## Continuous integration (2026-10-06, Suleman, T2.7)

| File | Change |
|---|---|
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | New. `tests` (every push and PR): backend, frontend, RL converter and `amrpredict` library tests on Python 3.12 with scikit-learn 1.6.1. `docker` (pushes to `main`, by hand): builds the backend image with AMRFinderPlus (cached conda layer), starts it, runs the gene-model check |
| [scripts/ci_docker_smoke.py](scripts/ci_docker_smoke.py) | New: Hamza's check in the image: `searches_genes` true, then one complete genome from `G_genes_deploy`'s test list (downloaded from BV-BRC with a project User-Agent; Cloudflare refuses Python's default one) through `/api/predict/`, with `genes_found`, `species_detected`, no `warning`, under 120 s. Standard library only |
| [README.md](README.md) | CI badge, a "Continuous integration" section |

Checked here: the workflow parses, the download fetches test genome `1001744.3` (2.1 MB), and against the local backend (no AMRFinderPlus) the check stops at `searches_genes` as it should. The first run on GitHub is the real test of the image.

---

## "Fill from Genome ID" on /forecast (2026-10-05, Suleman)

Agreed with Hamza and Ali: Genome ID is never a model input, only a helper.

| File | Change |
|---|---|
| [backend/api/genome_lookup.py](backend/api/genome_lookup.py), [views.py](backend/api/views.py), [urls.py](backend/api/urls.py) | New `GET /api/genome/<id>/?antibiotic=`: the organism from the ID's taxon prefix (only values the forecaster knows), the genome's laboratory results (a MIC only if mg/L and one number, so not trimethoprim/sulfamethoxazole's `1/19` or a disk zone), whether each served model trained on it (Hamza's `genome_status`, format §7), and its `/genes` link. A malformed ID is a 400 |
| [scripts/build_genome_lab_results.py](scripts/build_genome_lab_results.py), [backend/api/genome_lab_results.json.gz](backend/api/genome_lab_results.json.gz) | Lab results only (`Evidence = Laboratory Method`) per genome: 417,700 lab rows, 37,573 genomes, 0.6 MB, from `Data/amr_output/` (re-run on the complete export to refresh) |
| [frontend/templates/resistance_forecast.html](frontend/templates/resistance_forecast.html), [static/js/forecast.js](frontend/static/js/forecast.js), [static/css/components.css](frontend/static/css/components.css), [frontend/app.py](frontend/app.py) | The "Fill from Genome ID" box under the antibiotic: fills the lists, shows the lab result for the chosen drug with "Use this MIC", a caution for a training genome ("its prediction will look better than on a new genome"), and after a prediction whether the model agrees with the lab. The ID is kept after a submit but never sent to the model |
| [backend/tests/test_genome_lookup.py](backend/tests/test_genome_lookup.py), [frontend/tests/test_forecast_organisms.py](frontend/tests/test_forecast_organisms.py), [backend/tests/test_security.py](backend/tests/test_security.py) | New: 6 backend and 2 frontend tests. The rate-limit test holds the limiter's clock still, since requests crossing a minute boundary started a fresh count (a rare false failure) |

Checked in Edge: `106654.148` (a test genome) fills Acinetobacter / nosocomialis / 106654, gentamicin lab result Resistant (MIC ≥ 16 mg/L), and after the prediction "The model agrees"; `1001988.3` (a training genome) gets the caution. 6,876 of the forecaster's test genomes have a lab result here, for demos.

---

## Linked organism lists and MIC suggestions on /forecast (2026-10-02, Suleman)

| File | Change |
|---|---|
| [frontend/templates/resistance_forecast.html](frontend/templates/resistance_forecast.html), [static/js/forecast.js](frontend/static/js/forecast.js) | Genus, species and taxon ID are dropdowns in that order: a genus fills the species list with its own species only, and the taxon ID list with that species' IDs (the genus's when no species is chosen). The MIC field suggests recorded values and says from which level; any value can still be typed. Choices are kept after a submit. The antibiotic tooltip reads the model's count (126), not "62" |
| [backend/api/organisms.py](backend/api/organisms.py) | New: the genus → species → taxon ID tree from the forecaster's vocabulary and `backend/taxon_species.csv` (only values the model can use; "coli" under Escherichia and Campylobacter; NCBI's renamed Aliarcobacter and Stutzerimonas mapped back; 69 of 70 taxon IDs placed), and the MIC lookup (species, then genus, then all organisms) |
| [backend/api/views.py](backend/api/views.py), [urls.py](backend/api/urls.py), [frontend/app.py](frontend/app.py) | `/api/vocabulary/` adds `lgbm.organisms`; new `GET /api/mic-values/?antibiotic=&genus=&species=` (and the frontend's `/api/mic-values`) |
| [scripts/build_mic_values.py](scripts/build_mic_values.py), [backend/api/mic_values.json](backend/api/mic_values.json) | The MIC values recorded in BV-BRC (mg/L) per species, genus and antibiotic, the 12 most common seen at least 3 times; 118 kB, from `Data/amr_output/` (re-run on the complete export to refresh). Suggestions only: the model does not read it |
| [backend/tests/test_organisms.py](backend/tests/test_organisms.py), [frontend/tests/test_forecast_organisms.py](frontend/tests/test_forecast_organisms.py) | New: 8 and 4 tests |

Checked in Edge with both servers: Escherichia → coli → 562, Campylobacter → coli, jejuni, MIC suggestions for E. coli + ciprofloxacin, the prediction runs and the choices stay. Documents: [README.md](README.md) (routes, "Organism lists on /forecast are linked"; the libraries are served from `static/vendor/`).

**Open for the team:** a Genome ID field. The forecaster does not use Genome ID (it is the split key, so as an input it would only memorise known genomes); proposed instead as a "fill from Genome ID" helper (organism, the genome's real lab results, its genes on `/genes`, and whether the model saw it in training).

---

## Training genomes of the served models (2026-10-04)

For Suleman's "fill from Genome ID" helper on `/forecast`, so the page can say whether the model saw a genome in training.

| File | Change |
|---|---|
| [promote.py](experiments/promote.py) | Writes each promoted model's train/test Genome IDs (`split_genomes()`), rebuilt from the run's config and checked against its test-row count; `--split-only` for models promoted earlier |
| `backend/trained_models/lgbm_split_genomes.json.gz`, `genome/` and `genome_genes/split_genomes.json.gz` | /forecast: 351,442 train, 88,100 test genomes (all 439,542 of v7); /predict: 19,804 and 4,915 (test list identical to the gene run's predictions) |
| [training_genomes.py](backend/ml_models/training_genomes.py) | `genome_status(model_dir, genome_id)`: `train`, `test` or not in the data, per served model, with a sentence for the page |
| [test_training_genomes.py](backend/tests/test_training_genomes.py) | 4 tests: roles, IDs as text, a re-promoted file is re-read, served lists never overlap |
| [formats/README.md](progress/formats/README.md) §7, [.gitignore](.gitignore) | File format; the forecaster's list is committed |

## Gene model promoted, seeds, significance and lineage results (2026-10-01)

| File | Change |
|---|---|
| `backend/trained_models/genome_genes/` | **`G_genes_deploy` promoted:** lab AUC 0.977 [0.975–0.979] on 40,356 lab test rows of 4,481 unseen genomes, threshold 0.58 for VME ≤ 10% (VME 10.2%, ME 5.1%). Served when AMRFinderPlus is on the server; the website's predictor reproduces the run's probabilities on 400 test rows (largest difference 1e-16) |
| [.gitignore](.gitignore) | `backend/trained_models/genome_genes/` committed like `genome/` (it was ignored, so the gene model would never have reached GitHub) |
| [promote.py](experiments/promote.py) | Fix: the species table was indexed with the column from before de-duplication (`Length mismatch`) |
| [export_report.py](experiments/export_report.py) | Rebuilds temporal runs' splits (collection years and `cutoff_year`) |
| [significance.md](experiments/results/significance.md) | 7 pairs: genes vs k-mers +0.0445, vs taxonomy +0.130, vs drug only +0.264; A2 vs drug only +0.128; MIC on lab rows +0.083 (all p < 0.0001); genes + k-mers +0.002; A10 vs A2 −0.0004 (McNemar p = 0.14) |
| Seeds | Split seeds 42, 1, 2: A2 0.7849 ± 0.0005, A10 0.7845 ± 0.0005, A6 0.9214 ± 0.0012, A6b 0.8376 ± 0.0024, drug-only 0.6569 ± 0.0004, B6 genes lab 0.9789 ± 0.0004 |
| `LT_*_v7` | Lineage check for the tabular models on the 24,926 genomes with clusters, lab AUC grouped / close / broad: A2 0.968 / 0.967 / 0.961, D3 0.962 / 0.962 / 0.961 |
| [RESULTS.md](experiments/RESULTS.md) | Regenerated |

## Gene model path on /predict, lineage check for the tabular models (2026-09-30)

| File | Change |
|---|---|
| [genome_predictor.py](backend/ml_models/genome_predictor.py) | Serves the **gene model** (`trained_models/genome_genes/`) whenever AMRFinderPlus is on the server, the k-mer model otherwise. Per upload: species from the 6-mer profile (nearest of 99 species profiles; right species for 98.0%, right genus for 99.8% of 4,929 held-out genomes), AMRFinderPlus with that `--organism` as in training, core AMR hits turned into the gene features of `genes.py` (identical on 3,600 real genome-drug rows), and `genes_found` / `species_detected` in the response. AMRFinderPlus failure or timeout: the k-mer model answers, with a `warning`. Settings: `AMRFINDER_PATH`, `AMRFINDER_THREADS`, `AMRFINDER_TIMEOUT` (100 s), `AMRFINDER_DATABASE` |
| [promote.py](experiments/promote.py) | `--genome` takes gene runs too (to `genome_genes/`, with the gene rules and `species_profiles.npz`); refuses runs that use genus or species, which an upload does not have |
| [G_genes_deploy.json](experiments/configs/G_genes_deploy.json) | Deploy candidate: genes + antibiotic + drug class (no genus), threshold for VME ≤ 10% on validation, cleaning v7. Trains after the seed runs |
| [test_gene_model.py](backend/tests/test_gene_model.py) | 9 tests with a stand-in for AMRFinderPlus: model choice, `genes_found` (relevant first, empty list when none), species and `--organism`, fallback with `warning`, refusal before AMRFinderPlus runs, report parsing (old and new column names) |
| [formats/README.md](progress/formats/README.md) §2, [genome_response.sample.json](progress/formats/genome_response.sample.json) | New fields `species_detected`, `warning`, `model_run`, `genes_found[].subclass` / `name`; which model answers and how AMRFinderPlus is found |
| `experiments/configs/LT_*_v7.json` | Lineage check for the tabular models: A2 and D3 on the 24,926 genomes with lineage clusters, genome-grouped twin and the close and broad lineage cuts (Research track). Queued |
| Trackers | Hamza: Week 3 gene-model item done, Dataset 2 ticks; Suleman: what is left on his side (Docker build, database pin, show `warning` and the species) and the library switch-over answer (after the demo); Ali: one real AMRFinderPlus check on the Mac |

## Code review fixes (2026-09-30)

A read-through of the backend, frontend, library and experiment harness. Every test suite passes (backend 37, frontend 33, library 35, RL output 8). Fixed in Hamza's files:

| File | Bug | Fix |
|---|---|---|
| [lgbm_predictor.py](backend/ml_models/lgbm_predictor.py), [amrpredict/lgbm.py](amrpredict-lib/src/amrpredict/lgbm.py) | `POST /api/reload/` after a promotion re-read the model but not `lgbm_metrics.json`, so `model_run`, `/api/health/` metrics and the slider default stayed those of the previous run; a reload with the files gone kept the old calibration | `_load()` resets all state and re-reads the metrics. Test: [test_lgbm_reload.py](backend/tests/test_lgbm_reload.py) (fails before the fix) |
| [experiments/lib/__init__.py](experiments/lib/__init__.py) (new), `report.py`, `predict.py`, `calibration_plot.py` | On Windows, output redirected to a file is cp1252, so the first `→` printed killed the script (`run.py ... > log`, `export_report.py`) | stdout/stderr switched to UTF-8 wherever `lib` is imported |
| [genome_predictor.py](backend/ml_models/genome_predictor.py) | An antibiotic the genome model never saw was put into a `Categorical` outside its categories: deprecated in pandas, an error in the next major version | Unknown values go in as missing (what LightGBM already did); stale "not wired into the API" docstring corrected |
| `lgbm_predictor.py`, `resistance_predictor.py`, library `lgbm.py`, `kmer.py` | The heuristic fallbacks (used when a model fails to load) added random noise, so the same input gave different answers | Noise removed |
| [amrpredict/kmer.py](amrpredict-lib/src/amrpredict/kmer.py), [timeline.py](amrpredict-lib/src/amrpredict/timeline.py) | The library matched names by lower-casing only (timeline: rifampin alias only), unlike the backend | Both use the library's `amr_constants`; the timeline echoes the canonical name like the backend. Library test added |
| [test_library_parity.py](backend/tests/test_library_parity.py) (new) | Nothing checked that the library's copy of the forecaster loader still matched the backend's | Same probability, call, threshold and evidence on 5 inputs whenever both hold the same run |

Sent as Handovers, not changed (other owners' files): `backend/api/views.py` returns 500 with the raw Python message on malformed JSON, a non-numeric `threshold` or `n_weeks`, or `antibiotic: null`, and `frontend/app.py:265` on a non-numeric threshold (Suleman); stale July pipeline text in `about.html` and `index.html` (Suleman); per-process rate-limit cache (Suleman, optional); `experiments/v7_runs.py` uses `pgrep`/`ps`, which Windows lacks, and `mutation_timeline.py` would report `trained` if a `.pkl` appeared (Ali).

Environment: `gymnasium` (in `experiments/requirements.txt`) was missing from Hamza's venv, so `experiments/evolution/test_rl_output.py` could not run; installed.

## v7 forecaster served, library 0.2.0, significance tests and a temporal split (2026-09-30)

| File | Change |
|---|---|
| `backend/trained_models/` | `D3_forecaster_deploy_v7` (Ali's run of the D3 config on cleaning v7) promoted in place of D4: AUC 0.774 [0.772–0.775], lab rows 0.908, threshold 0.15 (VME 8.6%, ME 60.8%, recall 91.4%). `evaluate_shipped.py` rebuilt the split exactly (1,569,432 rows); through the backend's form inputs 0.762 [0.760–0.764] |
| [amrpredict-lib](amrpredict-lib/) | **0.2.0.** Bundles the served forecaster; `lgbm.py` ported from the backend predictor (calibration, species-level taxa with a bundled `taxon_species.csv`, the run's threshold and drug-class map, `evidence`), so `forecast()` returns the backend's probabilities and calls (checked); `forecast()` threshold defaults to the model's own (0.15) instead of 0.40; `status()` returns the run's metrics; antibiotic names from `amrpredict/amr_constants.py`, a copy of `backend/amr_constants.py` guarded by a backend test; scikit-learn pinned `>=1.6.1,<1.7` (the k-mer pickle's release). 34 tests pass; the wheel installs in a clean venv. Docs and `known-issues.md` updated |
| [promote.py](experiments/promote.py) | `--library` is no longer held back, and also copies `taxon_species.csv` |
| [significance.py](experiments/lib/significance.py), [compare.py](experiments/compare.py) | New: paired DeLong, McNemar at each run's threshold, and a paired genome bootstrap (rows cluster by genome, so it is the one to quote when they disagree). `compare.py A B [--lab]` or `--pairs` for the report's comparisons |
| [calibration_plot.py](experiments/calibration_plot.py) | New: reliability diagram from a run's `metrics.json` → `experiments/results/figures/` (served forecaster: Brier 0.193 raw → 0.160 isotonic) |
| [report.py](experiments/report.py), [run.py](experiments/run.py) | Accuracy, recall and specificity columns in `RESULTS.md`; new runs write them to `registry.csv`, older rows read them from `metrics.json` |
| [splits.py](experiments/lib/splits.py), [run.py](experiments/run.py) | New `temporal` split (`split.cutoff_year`): train on genomes collected up to the year, test on later ones, years from Ali's `Data/genome_meta/genome_meta.csv` (Genome ID as text; genomes without a year dropped). `data.require_year` gives a grouped twin on the same rows |
| `experiments/configs/` | `T0_grouped_withyear_v7`, `T1_temporal_{2012,2014,2015}_v7` (A6 on lab rows); `*_v7` copies of the 30 genome configs; split seeds 1 and 2 (`*_v7_s1`, `*_v7_s2`) for A2, A6, A6b, A10, drug-only and `B6L_genes_v7` |
| [TEMPORAL_RESULTS.md](experiments/TEMPORAL_RESULTS.md) | New: A6 on lab rows trained up to 2012 / 2014 / 2015 and tested on later genomes scores 0.878 / 0.857 / 0.857 against 0.928 for a random genome split of the same rows; the loss is within-genus drift in 2017–2018 (*Shigella*, *Neisseria*, *Salmonella*), not steady decay |
| Seeds (so far) | AUC mean ± sd over split seeds 42, 1, 2: B6 genes lab 0.9789 ± 0.0004, A6 0.9214 ± 0.0012, A6b 0.8376 ± 0.0024, drug-only 0.6569 ± 0.0004; A2 and A10 running |
| [backend/tests/test_amr_constants.py](backend/tests/test_amr_constants.py) | Fails if the library's copy of the names goes stale |
| READMEs, trackers | Served-model text and figures; Hamza's answers to Ali in his Handovers |

Local environment: Windows Smart App Control started blocking scikit-learn 1.9.1's `_cyutility` DLL on 2026-09-30; the project venv now has scikit-learn 1.8.0 (the release the system Python already runs). Results are unaffected: the served forecaster's calibration is stored as numbers, not a pickled estimator.

## Data audit and cleaning v7 (2026-09-29)

| File | Change |
|---|---|
| [audit_bvbrc.py](experiments/audit/audit_bvbrc.py) | New: the data audit for Paper A in one command (no network, about 2 minutes). Results in [audit.md](experiments/audit/results/audit.md) and `audit.json`: 16,531 genomes merge when Genome ID is read as a number; 89% of rows sit under species-rank taxon IDs; computational labels agree with the lab on 90.4% of 463,429 pairs (daptomycin 95.4% vs 10.9% resistant); 580,200 lab records have a measurement but no call |
| [data_prep.py](experiments/lib/data_prep.py) | Cleaning v7: rows measured in mm (disk diffusion, 8,380 lab rows) no longer count as MICs. Switched on by version, so `amr_output/` is still cleaned as v5 and rebuilds identically |
| [compare_clean_versions.py](experiments/audit/compare_clean_versions.py) | Knows the v7 cache |
| [RESEARCH_PLAN.md](progress/RESEARCH_PLAN.md) | Section 3 findings updated from the audit; the strain-level taxon claim withdrawn |

Hamza takes `clean_v7_amr_full_norm.pkl` from Drive instead of the v6 file.

---

## Week 3 on cleaning v6: genome models, a new /predict model and D4 (2026-09-29)

Hamza. Figures on the complete export (v6), as the team agreed; v5 runs stay in the registry as history.

### Served models
| Page | Model | Result |
|---|---|---|
| `/forecast` | `D4_forecaster_deploy` (D3 on v6) | AUC 0.774 [0.772–0.775] on 1.57 M unseen-genome rows, lab rows 0.907; threshold re-picked 0.16 (VME 9.8%, ME 58.4%) because the resistant share fell to 28.0% |
| `/predict` | `G_kmer_deploy`, LightGBM on 4-mers of the complete genome | lab AUC 0.935 [0.931–0.939]; threshold 0.43 (VME 9.6%, ME 19.5%). Replaces the RandomForest on partial genomes (0.695) |

### Genome experiments (v6, plasmid-only records excluded, 40,356 lab test rows)
Genes (B6) 0.979, k-mers 0.935, genes + k-mers 0.981 (no real gain), taxonomy 0.849; unseen genus 0.82–0.94 with genes vs 0.46–0.75 without; genes hold 0.965 with broad lineages held out, k-mers 0.900. Tables: [experiments/GENOME_RESULTS.md](experiments/GENOME_RESULTS.md).

### Code
| File | Change |
|---|---|
| `backend/ml_models/genome_predictor.py` | New: serves a promoted genome model; whole genome, k-mers per contig as in training, 100 kb minimum; same response fields as the old predictor |
| `backend/api/model_registry.py` | `/predict` uses the genome model when `trained_models/genome/` exists, else the old RandomForest |
| `experiments/promote.py` | `--genome` mode (lab AUC headline, threshold rule recorded); thresholds rounded |
| `experiments/run.py` | `data.genomes = "gene_matrix"`, `data.min_genome_bp` (plasmid filter), `compact()` (v6 in 0.42 GB instead of 1.5 GB, identical results) |
| `experiments/genome/lineage.py` | Clusters within each species, so it scales to 24,926 genomes |
| `experiments/evaluate_shipped.py` | Re-tests the served genome model; keeps the old RandomForest as `kmer_previous`; compacts v6 |
| `experiments/export_report.py` | Skips every genome run on `/models`; adds `genome_runs` for the Genome models section (formats §6) |
| Templates (Suleman's, listed in his tracker) | Home, `/predict`, `/about` describe the new model; `/models`, `/compare` read its name from the report |
| `.gitignore` | Lets `backend/trained_models/genome/` (3.6 MB) be committed |

### Still to come
The 23 tabular registry configs: Ali re-runs them on cleaning v7 (`*_v7`, `experiments/v7_runs.py`), which supersedes v6, so the v6 re-run here was stopped; `RESULTS.md`, the handbook and the plan take their tables from those runs. Ali's `D3_forecaster_deploy_v7` replaces D4 on `/forecast` when it finishes. The genome runs here stand for v7 too: v7 changes only MIC values, which they do not use. The gene model goes on `/predict` with Suleman's Docker image.

---

## Complete BV-BRC export and cleaning v6 (2026-09-29)

Ali. Every AMR record BV-BRC holds (17,585,506) downloaded into `Data/amr_full/` and cleaned as v6.

| File | Change |
|---|---|
| [download_amr_full.py](scripts/bvbrc_download/download_amr_full.py) | New: every record, paged by record ID in 16 parallel shards, resumable, keeps the Mac awake, retries without internet, `--watch` live view. Run 2026-09-29: 17,585,506 rows (1,285,111 lab) in 34 minutes, equal to BV-BRC's counts, 0 duplicates |
| [data_prep.py](experiments/lib/data_prep.py) | Cleaning v6 reads `Data/amr_full/` by default: 7,847,110 rows, 439,542 genomes, 649,944 lab rows on 87,325 genomes (v5: 1,558,494 / 131,385 / 201,042 / 22,475). Loads nine columns only; lists unreadable files instead of skipping them. `version_of` / `source_of` map versions to exports |
| [build_taxonomy.py](experiments/build_taxonomy.py), [taxon_species.csv](backend/taxon_species.csv) | 13,058 taxon IDs, 463 species (was 3,655 IDs); without it v6 had 9,114 "species" |
| [run.py](experiments/run.py), [backfill_bundles.py](experiments/backfill_bundles.py) | New runs read v6 and record the version they read |
| [evaluate_shipped.py](experiments/evaluate_shipped.py), [export_report.py](experiments/export_report.py) | Rebuild each run on the export its `clean_version` names; D3's split still rebuilds exactly (311,712 test rows) |
| [compare_clean_versions.py](experiments/audit/compare_clean_versions.py) | New: [v5_vs_v6.md](experiments/audit/results/v5_vs_v6.md). Compares the two cleaned tables |
| [datasets.html](frontend/templates/datasets.html) | Dataset 1 describes the complete export |

Every registry run and the served D3 are still v5; Hamza retrains on v6 (his tracker). Documents: [HANDBOOK §2, §3](experiments/HANDBOOK.md), [README](README.md), [scripts/bvbrc_download/README.md](scripts/bvbrc_download/README.md), [docs/DATA_LINKS.md](docs/DATA_LINKS.md).

---

## Tidier file layout (2026-09-28)

Loose files moved out of the repo root into folders; nothing was deleted from git. Links and paths updated everywhere they are used.

| Moved | To |
|---|---|
| `FYP_Completion_Roadmap.md`, `EXPERIMENT_PLAN.md`, `PROJECT_DOCUMENTATION.md`, `how_to_make_python_library.md` | [docs/](docs/) |
| `Data_Drive` (two Drive links) | [docs/DATA_LINKS.md](docs/DATA_LINKS.md), as a table |
| The four notebooks | [notebooks/](notebooks/) |
| `fasta_amr_map.py`, `train_all.bat` | [scripts/](scripts/) (`train_all.bat` now changes to `..\backend`) |
| New: the BV-BRC download scripts, until now outside the repo | [scripts/bvbrc_download/](scripts/bvbrc_download/README.md) |

`run_project.md` (manual Windows steps with one person's OneDrive path) was removed: [start.bat](start.bat) now does the same steps, with a `.venv`, relative paths and the frontend on port 5001 (it opened 5000, where nothing was running). [start.sh](start.sh) also moved from 5055 to 5001.

Links updated in README.md (file tree, §6, §11), CHANGES.md, experiments/HANDBOOK.md, experiments/README.md, the three trackers, `datasets.html`, `mutation_timeline.html`, `train.html` and `.gitignore`. Links inside the moved docs now start with `../`.

---

## Timeline sensitivity analysis and calibration (2026-09-28)

Ali's T3.1. Numbers and figures in [experiments/evolution/](experiments/evolution/README.md).

| File | Change |
|---|---|
| [sensitivity.py](experiments/evolution/sensitivity.py) | New: speed and peak scaled 0.7 to 1.3, weeks asked and GC varied, 8,232 combinations run through the served `generate_timeline`. The weeks asked decide the answer (midpoint = 45% of the span: 52 weeks instead of 8 makes failure 2 to 6 times later); peak is a switch at 50%; speed ±30% moves failure by a median 0.6 weeks |
| [calibrate.py](experiments/evolution/calibrate.py) | New: the same curve fitted to 15 published curves, median R² 0.91. Lab: *E. faecalis* under five drugs (Maltas, Huynh & Wood 2025, PLOS Biology). Hospitals: carbapenem-resistant *K. pneumoniae*, 10 countries (ECDC EARS-Net), plateau 7% to 66% by country, still-rising countries flagged. Writes `backend/trained_models/timeline_calibration.json` |
| [Data/evolution_curves/](Data/evolution_curves/sources.csv) | New: the source data with `sources.csv` (DOI, licence, use); re-downloadable zips ignored |
| [mutation_timeline.py](backend/ml_models/mutation_timeline.py) | `calibration` filled from the JSON (15 curves, rmse 2.9 points, `parameters_changed: false`); the hand-set constants are unchanged, since no source is in weeks |
| [mutation_timeline.html](frontend/templates/mutation_timeline.html) | Calibration shown under the result and in the Simulation Model card, with its limits; three claims that the constants were "calibrated from published clinical data" corrected |
| [formats §4](progress/formats/README.md) | Optional `calibration` fields documented |
| `experiments/requirements.txt` | `matplotlib`, `openpyxl` |

---

## Every lab-tested genome downloaded and searched (2026-09-28)

Ali's answer to Hamza's Week 2 finding that only about 30 test genomes had laboratory results.

| File | Change |
|---|---|
| [select_lab_genomes.py](experiments/genome/features/select_lab_genomes.py), [lab_genomes.csv](experiments/genome/features/lab_genomes.csv) | New: the 22,475 genomes with laboratory AST results in cleaning v5, round-robin across genera |
| [download_genomes.py](experiments/genome/features/download_genomes.py) | `--genome-list` downloads any list; 24,926 genomes on disk, 0 failures |
| [run_amrfinder.py](experiments/genome/features/run_amrfinder.py) | Saves its summary every 25 genomes and recovers genomes a stopped run finished; 24,926 searched, 0 errors |
| [build_gene_matrix.py](experiments/genome/features/build_gene_matrix.py), [export_gene_report.py](experiments/genome/features/export_gene_report.py) | Species from `backend/taxon_species.csv` when a genome has no `fasta_output/` folder (22,339 genomes were labelled genus "unknown") |
| [gene_matrix.parquet](experiments/genome/features/gene_matrix.parquet), [gene_info.csv](experiments/genome/features/gene_info.csv), [gene_summary.md](experiments/genome/features/gene_summary.md) | 2,587 × 536 → **24,926 × 2,733** (1,234 genes, 1,499 point mutations); lab-tested genomes 136 → 22,475 |
| `backend/trained_models/gene_report.json`, `gene_hits.json` | `/genes` rebuilt on every genome (`gene_hits.json` grows to 9.8 MB) |
| [progress.sh](experiments/genome/features/progress.sh) | Cores in use, keeps the Mac awake, restarts AMRFinderPlus when it stops |
| [start.sh](start.sh), [start.bat](start.bat) | Check dependencies offline first (`pip --no-index`), so a start with no internet no longer hangs; `--update` forces a full install |

Not in git: the genomes (about 100 GB) and `experiments/cache/kmer6_counts.npz` (k-mer counts for all 24,926 genomes, built with Hamza's `kmers.py`, shared on Drive).

---

## Models retrained and every run re-measured on cleaning v5 (2026-09-26)

Hamza's follow-up to Ali's Genome ID fix (`77bc855`, `b05d718`).

### Code
| File | Change |
|---|---|
| [experiments/promote.py](experiments/promote.py) | Reads `genome_id` as text, so its test-genome count no longer merges IDs |
| [experiments/evaluate_shipped.py](experiments/evaluate_shipped.py) | Reads the AMR CSVs, the mapped CSVs and `predictions.csv` with Genome ID as text. A re-run alone would have merged the corrected IDs again |
| [experiments/run.py](experiments/run.py), [report.py](experiments/report.py) | Every run records `clean_version` in `metrics.json` and the registry; `RESULTS.md` gains a Data column |
| [experiments/export_report.py](experiments/export_report.py) | Registers `D3_forecaster_deploy` |

### Served model
`D3_forecaster_deploy` (D2 on v5) replaces D2: AUC **0.8039 [0.8001-0.8076]** on 311,712 test rows of 26,324 unseen genomes; **0.7997** as `/forecast` scores it; threshold 0.23 (VME 8.2%, ME 54.6%, recall 91.8%). The ID bug had barely affected the model (D2: 0.8044). K-mer re-test on the fixed IDs: 2,505 genomes join (was 2,485), AUC 0.6949 (was 0.6951).

### Registry re-run
All 23 experiment configs re-run on v5; `D1` and `D2` stay on v3 and v4 as the record of what was served. Every AUC moved by less than 0.012 with overlapping intervals (A2 0.8232 → **0.8227**, A10 0.8223 → 0.8215). Two conclusions changed and are corrected in [HANDBOOK §11](experiments/HANDBOOK.md), [EXPERIMENT_PLAN §8b](docs/EXPERIMENT_PLAN.md), [README §10](README.md) and the roadmap:
- **Learning curve:** flattens after about 100 k rows, not 50 k (`LC_50k` 0.8157 → 0.8038).
- **`A12_species_holdout`:** AUC still about 0.60, but its error rates at 0.40 swapped (VME 11% → 52%, ME 83% → 36%). Quote only its AUC.

---

## Genome section, /predict follow-ups and backend image (2026-09-29, Suleman)

On top of Hamza's promotion of `G_kmer_deploy` to `/predict` (his wiring in `model_registry.py` stays).

| File | Change |
|---|---|
| [frontend/templates/models.html](frontend/templates/models.html), [static/js/models.js](frontend/static/js/models.js), [static/css/charts.css](frontend/static/css/charts.css) | Section 5 "Genome models, scored on lab results": chart and table of the `genome_runs` list (newest cleaning version, lab AUC with its row count), the served run starred |
| [backend/api/model_registry.py](backend/api/model_registry.py), [backend/api/views.py](backend/api/views.py) | Hamza's choice of `/predict` model moved into `predict_model()`; `/api/reload/` makes the choice again, so a model promoted while the server runs takes over without a restart. A refused genome (under 100 kb) is a 400 with the reason, not a 200 |
| [frontend/templates/resistance_prediction.html](frontend/templates/resistance_prediction.html), [frontend/exports.py](frontend/exports.py) | The stats strip reads the served model's metrics (the old model's hand-typed 6,002 pairs, 62 antibiotics and "100 trees (RF)" are gone); hints say complete genomes of at least 100,000 bp; PDF shows "not reported" for a missing GC content |
| [backend/ml_models/lgbm_predictor.py](backend/ml_models/lgbm_predictor.py) | `Taxon ID` column built as int64 directly: same values, no pandas `FutureWarning` on every forecast |
| [.dockerignore](.dockerignore), [backend/Dockerfile](backend/Dockerfile) | The backend image gets `backend/` only (not `Data/` or `experiments/`), runs gunicorn on `$PORT` instead of `runserver`, pins scikit-learn 1.6.1 (the version `kmer_resistance_model.pkl` was saved with); AMRFinderPlus stays for the gene model |
| [backend/tests/test_genome_wiring.py](backend/tests/test_genome_wiring.py), [frontend/tests/test_genome_section.py](frontend/tests/test_genome_section.py), [frontend/tests/test_predict_model.py](frontend/tests/test_predict_model.py) | New: 7, 5 and 3 tests |

The Docker image was not built here (no Docker on the machine); the backend was checked running from a copy of `backend/` alone, in production mode. Documents: [README.md](README.md) (Section 5, Docker).

---

## Resistance genes on /predict (2026-09-28)

Suleman's Week 3, first part: the UI for the genome model's `genes_found`, built against the agreed sample before the model sends it.

| File | Change |
|---|---|
| [frontend/templates/_genes_panel.html](frontend/templates/_genes_panel.html) | New. The panel for the three states of `genes_found` (absent, empty, a list), linked genes first, with a sentence on whether they support the call |
| [resistance_prediction.html](frontend/templates/resistance_prediction.html) | Includes the panel; "Not searched" line when the model does not look for genes; heading, k-mer cards and chart follow the model instead of assuming the k-mer one |
| [frontend/static/css/components.css](frontend/static/css/components.css) | Gene chip styles, from the colour tokens so dark mode works |
| [frontend/exports.py](frontend/exports.py) | `resistance_genes` column in the `/predict` CSV, a genes table in its PDF |
| [frontend/app.py](frontend/app.py) | `GET /predict/sample`: the page with the sample response, local runs only |
| [frontend/tests/test_genes_panel.py](frontend/tests/test_genes_panel.py) | New: 7 tests, one per state plus escaping, the k-mer-less layout and the local-only preview |

Nothing changes on the served site until the genome model returns `genes_found`. Documents: [README.md](README.md) (banner, routes, new "Resistance genes on /predict"), [progress/formats/README.md](progress/formats/README.md) §2.

---

## Downloads and batch upload (2026-09-27)

Suleman's Week 2 (T2.2, T2.3).

| File | Change |
|---|---|
| [frontend/exports.py](frontend/exports.py) | New. CSV and PDF (ReportLab) of a tool page's result; model details from the metrics files |
| [frontend/app.py](frontend/app.py) | `POST /export/<page>.<csv|pdf>`, `GET /forecast/template.csv`, `POST /forecast/batch` |
| [frontend/templates/_export_bar.html](frontend/templates/_export_bar.html), [static/js/export.js](frontend/static/js/export.js) | New. The download bar on `/forecast`, `/predict`, `/timeline` and the batch results; PNG and the PDF's chart |
| [resistance_forecast.html](frontend/templates/resistance_forecast.html), [forecast.js](frontend/static/js/forecast.js) | "Upload CSV" tab, batch summary, per-antibiotic chart and row table; the record count and antibiotic count read from the metrics file; the examples no longer quote fixed percentages |
| [backend/api/views.py](backend/api/views.py), [urls.py](backend/api/urls.py), [settings.py](backend/backend/settings.py) | New `POST /api/forecast/batch/`: 10,000 rows, 2 MB, 5 a minute per visitor |
| [mutation_timeline.html](frontend/templates/mutation_timeline.html), [train.html](frontend/templates/train.html) | The CNN-LSTM is no longer offered for training, and "results are accurate" is gone: the timeline is a simulation that is not validated |
| [frontend/requirements.txt](frontend/requirements.txt) | `reportlab` |
| Tests | New [backend/tests/test_batch.py](backend/tests/test_batch.py) (7) and [frontend/tests/test_exports.py](frontend/tests/test_exports.py) (9); [backend/tests/django_setup.py](backend/tests/django_setup.py) shares the Django settings between test files |

**For everyone:** `python -m pip install -r frontend/requirements.txt` after pulling (new: `reportlab`).

---

## Security hardening, honest UI numbers and a safe Train button (2026-09-26)

Suleman's platform work (T1.3, T2.4), plus two fixes found on the way.

### Security (T2.4)
| File | Change |
|---|---|
| [backend/backend/settings.py](backend/backend/settings.py) | `SECRET_KEY` and `ALLOWED_HOSTS` from the environment only, required when `DEBUG` is off (a random key per process when it is on); no CORS origins; `DATABASES = {}`; 20 MB FASTA limit; rate limits; `ADMIN_TOKEN` |
| [backend/api/views.py](backend/api/views.py) | `X-Admin-Token` on `/api/train/` and `/api/reload/` (401, or 503 when no token is set); 413 for oversized FASTA; 429 per visitor IP on forecast, predict, timeline; `/api/train/` takes only `lgbm` or `kmer`; the 8 no-op `csrf_exempt` decorators removed, with the reason at the top |
| [frontend/app.py](frontend/app.py), [train.html](frontend/templates/train.html), [train.js](frontend/static/js/train.js) | Admin password on `/train`, sent with Train and Reload; the browser's IP forwarded for the rate limit; 20 MB upload limit with a message on the page; no hardcoded `secret_key`; debug server on 127.0.0.1 only |
| [start.sh](start.sh), [start.bat](start.bat), `run_project.md` (removed 2026-09-28) | Start the backend with `DEBUG=True`; say how to set `ADMIN_TOKEN`; no `migrate` |
| [backend/Procfile](backend/Procfile), [requirements.txt](backend/requirements.txt) | `release: migrate` removed; `django-ratelimit` added |
| [backend/tests/test_security.py](backend/tests/test_security.py) | New: 13 tests, one per rule above |

**For everyone:** `pip install -r backend/requirements.txt` after pulling. Starting the backend by hand needs `DEBUG=True`. Railway now needs `SECRET_KEY`, `ALLOWED_HOSTS` and `ADMIN_TOKEN` on the backend or it will not start.

### UI numbers read from the metrics files (T1.3)
- Every AUC, interval, threshold, recall and training size on the pages comes from `lgbm_metrics.json` and `kmer_metrics.json` via `/api/health/` (cached in `frontend/app.py`), or reads "not measured". The 22 hardcoded `0.93` / `0.9255` / `0.929` are gone; `/about` explains why the old figure was inflated.
- The `/forecast` and `/predict` sliders start at each model's validated threshold instead of 0.40 and 0.5, and the API no longer forces those values. The forecast chart, `/datasets` and the `/models` error chart use the same threshold.
- Warnings for `model_used: Heuristic fallback` and for an antibiotic the k-mer model never saw.

### Train button writes a candidate
- `/api/train/` writes to `backend/trained_models/candidates/<model>/` and no longer reloads the served model, which it used to replace without its threshold, calibration or `metrics.json` (Ali made the command-line trainer do the same).

### Documents
- [README.md](README.md): update banner, repository map (`tests/`, no `db.sqlite3`), "Training from the web UI", §9 local run and Railway variables, §11.4 rewritten as what the code now does, the `db.sqlite3` item removed from §11.5.

---

## Genome IDs read as numbers: cleaning v5 (2026-09-26)

Found by the week 2 join check. `data_prep.py` and `train_models.py` loaded the AMR CSVs without a type, so `Genome ID` became a float and IDs that differ only by trailing zeros merged: `195.304` and `195.3040` are different genomes but the same number.

| | Before (v4) | After (v5) |
|---|---|---|
| Genomes in the cleaned table | 128,286 | 131,385 |
| Rows after cleaning | 1,521,644 | 1,558,494 (+36,850, 2.4%) |
| Laboratory-measured rows | 199,763 | 201,042 |
| Genomes merged into another | 3,312 | 0 |

- [experiments/lib/data_prep.py](experiments/lib/data_prep.py), [backend/train_models.py](backend/train_models.py): `Genome ID` read as text; `CLEAN_VERSION` is `v5`.
- `Data/mapped_output/`: the same bug in `fasta_amr_map.py` had put 888 rows of 20 genomes (e.g. `1055537.30`) under another genome's ID **and FASTA file** (`1055537.3`), which the earlier trailing-zero fix could not see because ID and file name agreed. Corrected from a rerun of the fixed mapper, changing only those rows. All 2,587 genomes now have their own rows.
- Rebuilt: `gene_report.json` (136 genomes with laboratory results, was 125), and the Datasets page, README and handbook figures.
- **Not yet redone:** every model and experiment run used the merged IDs. D2 and the K-mer re-test need a re-run on v5 (Hamza).

---

## Datasets page: four source datasets, counted once (2026-09-26)

The page said "Five datasets" in its subtitle and stat strip, "All Four Datasets" in its table, and counted the test samples as Dataset 4, although they are small copies of the other data. It now lists **four source datasets** (AMR phenotype records, the partial FASTA genomes, the complete assemblies, and the single `BVBRC_genome_amr.csv` export used by the notebooks) and, separately, the data the project built from them (mapped records, gene matrix, test samples).

Also corrected: 3,655 AMR CSVs (not 4,252) and 1.52M cleaned rows over 128,286 genomes, 130 antibiotics and 40 genera (not "90K+", 62 and "15+"); the FASTA files are partial (median 31% of the genome), not complete; the mapped records are 110,493 rows over 2,567 genomes (not 6,002 and 1,684); training writes to `candidates/` rather than reloading the site, and the K-mer model takes about an hour; no CNN-LSTM exists. The served models' training sizes are read live from their metrics files.

---

## Genome IDs that lost a trailing zero (2026-09-26)

`fasta_amr_map.py` read each CSV with Genome ID as a number, so `1055537.10` became `1055537.1`; its substring search then still found `1055537.10.fasta`, so `fasta_path` was right and the ID wrong. 68 genomes in `Data/mapped_output/` were affected (3,271 rows in 26 files), and `1038927.40` had become `1038927.4`, a different genome, mixing the two genomes' labels.

- [fasta_amr_map.py](scripts/fasta_amr_map.py): reads Genome ID as text.
- `Data/mapped_output/`: each wrong ID replaced by the one in its own `fasta_path`, changing only that field. Every mapped genome now joins the gene matrix.
- `Data/amr_output/` was never affected. The K-mer re-test (`evaluate_shipped.py`, `kmer_metrics.json`) groups by these IDs and should be rerun.

---

## Resistance genes page (2026-09-26)

A new `/genes` page (Insights menu, next to the two model reports, which moved there from ML Models the same day) shows the AMRFinderPlus results: run summary, top genes and mutations, genes per genome, drug classes, a genus × gene heatmap, gene vs lab result, and a genome lookup.

### Findings
- Only 118 of the searched genomes have laboratory results; the other labels on them are BV-BRC predictions made from the genome, so the gene vs lab table uses laboratory results by default and shows the predictions behind a labelled toggle.
- Matching genes to antibiotics by drug class paired genes with drugs they do not act on (`aph(6)-Id`, a streptomycin gene, with gentamicin). Pairs now follow the AMRFinderPlus subclass.
- A gene is not a verdict: `sul2` carriers were 10% resistant to co-trimoxazole (trimethoprim resistance needs a second gene), `blaTEM-1` carriers 6% to cefoxitin.

A later addition the same day: a **gene matrix** section explains the matrix, shows a readable corner of it, and offers the whole matrix and its column list as CSV downloads (`/genes/matrix.csv`, `/genes/info.csv`, built by the backend from `gene_hits.json` and checked equal to `gene_matrix.parquet`).

### Code
| File | Change |
|---|---|
| [experiments/genome/features/export_gene_report.py](experiments/genome/features/export_gene_report.py) | New. Builds `gene_report.json` and `gene_hits.json` |
| [backend/api/views.py](backend/api/views.py), [urls.py](backend/api/urls.py) | `GET /api/genes/` and `GET /api/genes/<genome_id>/` |
| [frontend/app.py](frontend/app.py), [templates/genes.html](frontend/templates/genes.html), [static/js/genes.js](frontend/static/js/genes.js) | The page, a lookup proxy, the menu entry; toggle and meter styles in `charts.css` |
| [.gitignore](.gitignore) | The two JSON files are committed so the deployed backend can serve them |

---

## Antibiotic names and label maps in one file (2026-09-26)

### Findings
- The alias table and drug-class map were kept identical by hand in `data_prep.py` and `train_models.py`, the dropdown list was typed twice (`frontend/app.py`, `views.py`), and the frontend kept its own exclusion list that mirrored the aliases.
- The K-mer dropdown offered `cefalothin`, the old spelling, while every other list said `cephalothin`.

### Code
| File | Change |
|---|---|
| [backend/amr_constants.py](backend/amr_constants.py) | New. `DRUG_CLASS_MAP` (138 entries), `ANTIBIOTIC_ALIASES`, `PHENOTYPE_MAP` with each trainer's subset, `MIC_SIGN_ALIASES`, `UI_ANTIBIOTICS` (82), `normalize_antibiotic()` (now also collapses double spaces). Running it writes the frontend copy |
| [frontend/antibiotic_names.json](frontend/antibiotic_names.json) | New, generated: the frontend deploys without `backend/` |
| [backend/tests/test_amr_constants.py](backend/tests/test_amr_constants.py) | New. Fails if the frontend copy is stale, an alias chains or lacks a class, or a dropdown name is a variant |
| `data_prep.py`, `train_models.py`, `ml_models/common.py`, `lgbm_predictor.py`, `api/views.py`, `frontend/app.py` | Import from it; their own copies removed (and the unused `MIC_SIGN_MAP` in the trainer) |

Every value checked identical before and after; the cleaned table is unchanged (1,521,644 rows, 130 names), so still cleaning v4. `amrpredict-lib` keeps its own copies until the library sync (T2.6).

---

## Handover formats, gene matrix, trainer default and timeline fix (2026-09-26)

### Findings
- The command-line trainer wrote straight into `backend/trained_models/`, replacing the promoted model without its threshold, calibration or `metrics.json`, so the UI would have shown the old model's numbers for a new model.
- The timeline's three population shares reached 106% by week 8, and `model_used` could say `CNN-LSTM (trained)` although no trained model is ever used.
- AMRFinderPlus core scope also reports a few stress and biocide genes, so the gene matrix filters on `Type = AMR` as well as `Scope = core`. The run did not use `--plus`, so there is no plus-scope matrix.

### Code
| File | Change |
|---|---|
| [experiments/genome/features/build_gene_matrix.py](experiments/genome/features/build_gene_matrix.py) | New. AMRFinderPlus output → `gene_matrix.parquet` + `gene_info.csv`; `--sample N` writes a fixed sample to `sample/` |
| [experiments/genome/features/sample/](experiments/genome/features/sample/) | New. 20 genomes, 7 genera, 7 with no core AMR hit, all joining to their labels |
| [experiments/requirements.txt](experiments/requirements.txt) | New. Backend requirements plus `scipy` and `pyarrow` |
| [backend/train_models.py](backend/train_models.py) | Default output is `trained_models/candidates/<model>/`, like `/api/train/` |
| [experiments/lib/data_prep.py](experiments/lib/data_prep.py), [backend/train_models.py](backend/train_models.py) | 13 more antibiotic aliases and `sulfa` dropped; cleaned table unchanged, so still cleaning v4 ([HANDBOOK](experiments/HANDBOOK.md) §3) |
| [backend/ml_models/mutation_timeline.py](backend/ml_models/mutation_timeline.py) | Shares are a partition (exactly 100); one seeded generator; drug names go through `normalize_antibiotic()` like the predictors (`rifampin` and `co-trimoxazole` fell to the generic profile); `model_used` always `Biological Simulation`; new `simulation`, `seed`, `calibration` fields |

### Documents
- [progress/formats/README.md](progress/formats/README.md): §3 gene matrix agreed with notes, new §4 timeline + RL response and [sample](progress/formats/timeline_response.sample.json). §4 agreed with Suleman the same day, with his three questions answered: the tie rule for `rl.best`, the requested drug always first in `rl.drugs`, and the `calibration` field types.
- [README.md](README.md): §4.3 timeline caveats, the deep-learning note, §11.3 marked fixed in the backend, training section.
- [experiments/README.md](experiments/README.md): install line, `genome/` and `requirements.txt` in the layout.
- [experiments/genome/README.md](experiments/genome/README.md): step 3 builds the matrix; committed outputs listed.
- [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md): C3 marked done in the backend.

Not yet changed: the library's copy of the timeline and its `xfail`; three templates that still mention CNN-LSTM (`mutation_timeline.html`, `train.html`, `datasets.html`).

---

## Deployed models re-tested, and two report pages (2026-09-25)

### Findings
- The shipped models' training data was reconstructed: the first 500 `amr_output` files for the LightGBM and the first 200 `mapped_output` files for the K-mer model, confirmed by identical antibiotic sets, genera and stored resistance rate.
- On genomes they never saw, the shipped LightGBM scores **0.644** (0.941 on its own genomes) and the K-mer model **0.695** (0.981), against **0.823** for `A2_oof_grouped`. The K-mer model does no better than the antibiotic's resistance rate alone (0.703).
- The shipped LightGBM trained on 1.6% of the rows, not a seventh: 24,983 rows, 9 genera, no *Klebsiella*, 16.6% resistant against 36.5% overall.
- A random split puts 99.7% of test rows on genomes also in training; the grouped split puts 0%.

### Code
| File | Change |
|---|---|
| [experiments/evaluate_shipped.py](experiments/evaluate_shipped.py) | New. Re-tests the shipped models, writes `results/shipped_eval.json` |
| [experiments/export_report.py](experiments/export_report.py) | New. Builds `backend/trained_models/model_report.json` from every run |
| [experiments/lib/profile.py](experiments/lib/profile.py) | New. Size, organism and label mix of a training set |
| [backend/api/views.py](backend/api/views.py), [urls.py](backend/api/urls.py) | New `GET /api/models/` serving the report |
| [frontend/app.py](frontend/app.py) | New routes `/models` and `/compare` |
| [frontend/templates/models.html](frontend/templates/models.html), [compare.html](frontend/templates/compare.html) | New pages, linked from the ML Models menu and the footer |
| [frontend/static/js/](frontend/static/js/) | New `models.js`, `compare.js` and the shared `report-charts.js`; `main.js` skips the count-up on `.stat-mini-static` tiles |
| [frontend/static/css/](frontend/static/css/) | Chart colour tokens in `tokens.css` and `dark.css`; page styles in `charts.css` |
| [.gitignore](.gitignore) | `backend/trained_models/model_report.json` is committed so the deployed backend can serve it |

### Documents
- [README.md](README.md): update banner, new counts (8 endpoints, 14 routes, 11 pages), repository map (and `Data/` described as committed, which it is), §5.4 report scripts, new §8.1 on the report pages, §10 re-test table, §11.2 corrected (the trainer looks in the project root, the data is in `Data/`), reading order.
- [experiments/README.md](experiments/README.md): quick start, layout, new "The web report" section.
- [experiments/HANDBOOK.md](experiments/HANDBOOK.md): §10 now lists all 22 runs (the XGBoost and CatBoost rows were missing), §11 gained the re-test and the five-algorithm table, §12 and §13 list the new files.
- [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md): status banner.

Not yet changed: the "AUC 0.93" badges on the dashboard, `/predict`, `/about`, `/datasets` and in the footer still quote the original figures. *(Replaced on 2026-09-26: every page now reads these from the metrics files; see the entry above.)*

---

## Plain prose pass (2026-09-24)

Em dashes and en dashes removed from every document and from the experiment code, and phrasing that read as machine-written rewritten.

| Area | Files |
|---|---|
| Documents | [CHANGES.md](CHANGES.md), [README.md](README.md), [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md), [HANDBOOK.md](experiments/HANDBOOK.md), [README.md](experiments/README.md), [RESULTS.md](experiments/RESULTS.md) |
| Code | all 14 files under [experiments/](experiments/), docstrings and comments |
| Stored text | 33 JSON files (configs, config snapshots, metrics) plus [registry.csv](experiments/results/registry.csv), since [report.py](experiments/report.py) regenerates `RESULTS.md` from those descriptions |

Numeric ranges became hyphenated (`0.8200-0.8269`), placeholder table cells became `n/a`, and clause-joining dashes became commas, colons or sentence breaks.

Two repairs during the pass: collapsing `..` sequences had turned relative links such as `](../CHANGES.md)` into `](./CHANGES.md)`, and three docstrings in [algorithms/base.py](experiments/algorithms/base.py) became run-on sentences. Both fixed, and a link check across all five documents reports zero broken links.

---

## Documentation consolidation (2026-09-24)

### [experiments/HANDBOOK.md](experiments/HANDBOOK.md)
- [§7 Algorithms](experiments/HANDBOOK.md#7-algorithms) rewritten for the one-file-per-algorithm layout, with a table mapping each file to its `model.type` and instructions for adding one.
- [§10 Results](experiments/HANDBOOK.md#10-results-so-far) regenerated for all 19 runs, with an algorithm column added.
- [§11](experiments/HANDBOOK.md#11-what-the-results-mean) gained the three-way algorithm comparison.
- [§12 File reference](experiments/HANDBOOK.md#12-file-reference) restructured into four groups (entry points, algorithms, pipeline stages, data in and out) plus a note on what [.gitignore](.gitignore) excludes.
- [§6.1](experiments/HANDBOOK.md#61-the-saved-model-bundle) added, documenting the saved-model bundle.

### [README.md](README.md)
- [Repository map](README.md#2-repository-map) now includes `data/` and [experiments/](experiments/).
- New [§5.4](README.md#54-the-experiment-harness---experiments) describing the experiment harness.
- [§10](README.md#10-the-numbers-and-where-each-one-comes-from) carries a correction: the 0.9255 AUC is superseded by a measured **0.8232 [0.8200-0.8269]**.
- [Reading order](README.md#13-reading-order-for-someone-new-to-the-repo) updated to include the handbook.

### [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md)
- Status banner: 19 runs across three algorithms.
- [Track A](docs/EXPERIMENT_PLAN.md#4-track-a-tabular-forecaster-experiments) rows **A3**, **A4**, **A10** marked done with measured numbers.
- New [§8b](docs/EXPERIMENT_PLAN.md#8b-what-19-runs-have-shown), a summary table answering each question the plan posed with a measurement.
- Notes added where registry run ids collide with planned experiment ids. [`A6_lab_only`](experiments/configs/A6_lab_only.json) is the label-provenance run, not the planned imbalance sweep; [`A9_threshold_f1`](experiments/configs/A9_threshold_f1.json) is the threshold run, not the planned calibration one. The registry ids were left alone because their config snapshots are already saved.

### [experiments/README.md](experiments/README.md)
- [Layout](experiments/README.md#layout) updated for `algorithms/`, new [Adding an algorithm](experiments/README.md#adding-an-algorithm) section, and the three-file model bundle spelled out.

### Code
- [experiments/lib/data_prep.py](experiments/lib/data_prep.py): the data directory is now resolved case-tolerantly (`data/`, `Data/`, `DATA/`). The folder on this machine is `Data/`, which macOS treats as identical to `data/` but Linux would not.
- [.gitignore](.gitignore): the data folder is now excluded outright. Three files inside it, including a 30 MB CSV, were not covered by the existing per-dataset rules.

---

## One file per algorithm (2026-09-24)

**Change:** `experiments/lib/modeling.py` was split into [experiments/algorithms/](experiments/algorithms/), one file per algorithm, with a registry.

| File | `model.type` |
|---|---|
| [base.py](experiments/algorithms/base.py) | the contract plus shared scikit-learn preprocessing |
| [lightgbm_model.py](experiments/algorithms/lightgbm_model.py) | `lightgbm` |
| [logistic_model.py](experiments/algorithms/logistic_model.py) | `logistic` |
| [random_forest_model.py](experiments/algorithms/random_forest_model.py) | `random_forest` |
| [xgboost_model.py](experiments/algorithms/xgboost_model.py) | `xgboost` |
| [catboost_model.py](experiments/algorithms/catboost_model.py) | `catboost` |
| [__init__.py](experiments/algorithms/__init__.py) | `REGISTRY` and `build_model()` |

**Why:** each algorithm's training recipe and the reasoning behind its defaults is readable in one place. Adding an algorithm is a new file plus one registry line. [run.py](experiments/run.py) does not change, so earlier results stay comparable.

**Shared preprocessing** (one-hot, impute, scale) stayed in [base.py](experiments/algorithms/base.py) instead of being duplicated into the logistic and random-forest files, so the two cannot drift apart and stop being comparable.

**Verification:** re-ran [`A2_oof_grouped`](experiments/configs/A2_oof_grouped.json) after the split. AUC 0.8232 [0.8200-0.8269], VME 10.1%, ME 46.4%, identical to before. Then added [`A4_random_forest`](experiments/configs/A4_random_forest.json) as a new-file test; it ran and its saved bundle reloads.

**Result added:** the first like-for-like algorithm comparison, identical 400k sample and seed.

| Algorithm | AUC [95% CI] | AUPRC | Run |
|---|---|---|---|
| LightGBM | 0.8201 [0.8163-0.8245] | 0.7348 | [`A3b_lgbm_same_sample`](experiments/configs/A3b_lgbm_same_sample.json) |
| Random forest | 0.8173 [0.8136-0.8214] | 0.7282 | [`A4_random_forest`](experiments/configs/A4_random_forest.json) |
| Logistic regression | 0.8024 [0.7985-0.8063] | 0.7083 | [`A3_logistic`](experiments/configs/A3_logistic.json) |

**Docs:** [HANDBOOK §7](experiments/HANDBOOK.md#7-algorithms) and [§12](experiments/HANDBOOK.md#12-file-reference), [README layout](experiments/README.md#layout) and [Adding an algorithm](experiments/README.md#adding-an-algorithm).

---

## Saved models made reusable (2026-09-24)

**Problem:** every run saved its model, but a saved booster could not predict. Three of its features are resistance rates looked up per antibiotic, taxon and genus, computed from that run's training rows. Without those tables the model is fed numbers it was never trained against.

**Change:** [run.py](experiments/run.py) now exports a complete bundle to `results/<id>/model/`.

| File | Contents |
|---|---|
| `model.txt` / `model.joblib` / `model.cbm` | the trained artifact |
| `rate_tables.joblib` | the three rate lookups from that run's training rows, plus its global mean |
| `feature_meta.json` | feature order, category levels, encoding mode, threshold, training-set summary |

**Added:** [experiments/predict.py](experiments/predict.py) loads a saved run and predicts with it; [experiments/backfill_bundles.py](experiments/backfill_bundles.py) adds bundles to earlier runs by rebuilding their seeded training split, without retraining.

**Verification:** reloading a bundle and re-predicting 300 stored test rows reproduces that run's scores to within 5e-5 (the rounding in `predictions.csv`) for both the LightGBM and scikit-learn paths. All 18 earlier runs were backfilled.

**[.gitignore](.gitignore):** `experiments/cache/` (189 MB), `results/*/predictions.csv` (184 MB) and `results/*/model/` (44 MB) excluded. Configs, code, `metrics.json`, config snapshots and [registry.csv](experiments/results/registry.csv) are kept, so any model rebuilds from its config in about a minute.

**Docs:** [HANDBOOK §6.1](experiments/HANDBOOK.md#61-the-saved-model-bundle) and [§12](experiments/HANDBOOK.md#12-file-reference), [README promotion section](experiments/README.md#promoting-a-model-to-the-app).

---

## Experiment harness built, 19 runs (2026-09-24)

**Added:** [experiments/](experiments/), a training ground for candidate models that never touches `backend/trained_models/`.

**Why:** [backend/train_models.py](backend/train_models.py) cannot answer "is variant A better than variant B?" correctly. It fits target encodings on the full dataset before splitting ([lines 186-209](backend/train_models.py#L186-L209)), splits rows randomly so one genome lands on both sides, caps itself at 500 of 3,655 CSVs ([line 55](backend/train_models.py#L55)), and prints metrics to a console log that is then discarded.

**Data census** (`data/amr_output/`, 3,655 CSVs), produced by [lib/data_prep.py](experiments/lib/data_prep.py):

| | |
|---|---|
| Raw rows | 2,986,755 |
| After cleaning | 1,525,796 |
| Genomes | 128,317 (~11.9 rows each) |
| Antibiotics / genera | 152 / 41 |
| Resistant | 36.5% |
| Rows with an MIC | 6.8% |

That is **17x the ~90,000 rows** the shipped model was trained on. Full field-by-field account in [HANDBOOK §3](experiments/HANDBOOK.md#3-the-data) and [§4](experiments/HANDBOOK.md#4-field-reference).

### Corrections to earlier claims in this work

Two predictions written into [EXPERIMENT_PLAN.md](docs/EXPERIMENT_PLAN.md) were wrong and were replaced with measurements.

| Claim | Predicted | Measured | Runs |
|---|---|---|---|
| Target leakage inflates the AUC substantially | 0.93 to ~0.88 | **0.002** (0.8243 vs 0.8225), intervals overlap | [`A0_baseline_leaky`](experiments/configs/A0_baseline_leaky.json), [`A1_oof_random`](experiments/configs/A1_oof_random.json) |
| Grouped splitting will cost accuracy | "small further drop" | **None**. Grouped 0.8232 is marginally *higher* | [`A2_oof_grouped`](experiments/configs/A2_oof_grouped.json) |

Both are explained by scale: with 1.5 M rows and a min-count floor, an encoded group is estimated from many rows, so one test row's own label barely shifts its group mean. The leakage would matter on the 90k subset; it does not here. Both fixes were kept regardless, since they cost nothing and remove the objection. Corrected text is in [§1.2](docs/EXPERIMENT_PLAN.md#12-target-encodings-leak-into-the-test-set-) and [§1.3](docs/EXPERIMENT_PLAN.md#13-rows-from-one-genome-land-on-both-sides-of-the-split-).

### Findings recorded

Full table in [RESULTS.md](experiments/RESULTS.md), interpretation in [HANDBOOK §11](experiments/HANDBOOK.md#11-what-the-results-mean).

- Corrected baseline: **AUC 0.8232 [0.8200-0.8269]** ([`A2_oof_grouped`](experiments/configs/A2_oof_grouped.json)).
- **The threshold is the biggest lever.** At the production 0.40, major error is **46%**. Moving to 0.47 trades it to 34% at the cost of VME rising from 10% to 20% ([`A9_threshold_f1`](experiments/configs/A9_threshold_f1.json)). No model change moved AUC by more than 0.002.
- Cross-genus generalisation collapses: **0.5971**, 82.9% ME ([`A12_species_holdout`](experiments/configs/A12_species_holdout.json)).
- Drug identity alone: **0.6545**, the measured value of the UI's "Population-level estimate" ([`A_ablation_drug_only`](experiments/configs/A_ablation_drug_only.json)).
- Lab-only labels score 0.9654 ([`A6_lab_only`](experiments/configs/A6_lab_only.json)), but partly circular: lab rows carry an MIC 78x more often, and a lab's S/R call is the MIC put through breakpoints. Without MIC features it falls to 0.8703 ([`A6b_lab_only_no_mic`](experiments/configs/A6b_lab_only_no_mic.json)).
- Learning curve flat from 50k rows ([`LC_50k`](experiments/configs/LC_50k.json) through [`LC_800k`](experiments/configs/LC_800k.json)). Full data buys precision (CI width 0.017 to 0.007) and tail coverage (36 to 90 evaluable antibiotics), not accuracy. **The model is feature-limited, not data-limited.**

**Docs created:** [HANDBOOK.md](experiments/HANDBOOK.md), [README.md](experiments/README.md), [RESULTS.md](experiments/RESULTS.md).

---

## `/forecast` input ambiguity removed (2026-09-24)

**Problem:** the form accepted values the model cannot use, and the result did not say which inputs mattered. Typing "Klebsiella" or taxon ID 562 changed nothing, indistinguishably from leaving the field blank.

**Root causes**, found by inspecting the model's own vocabulary in [lgbm_predictor.py](backend/ml_models/lgbm_predictor.py):
- The taxon encoding table holds 24 strain-level IDs (106,654 to 1,110,693). None of the eight species IDs in the UI's organism dropdown (562, 573, 287, 1280 and so on) are in it.
- The model knows **9 genera** and 11 species. Klebsiella, Enterococcus, Proteus and Enterobacter are not among them, despite being in the dropdown.
- `>=` is not a category the model saw, so selecting it landed in the unknown bucket.
- 11 of the 48 antibiotics offered were unknown to both models.

**Changes:**
- `GET /api/vocabulary/` ([views.py](backend/api/views.py), [urls.py](backend/api/urls.py)) exposes what each model was trained on. Dropdowns populate from it through [frontend/app.py](frontend/app.py) and [dropdowns.js](frontend/static/js/dropdowns.js): 67 drugs for the forecaster, 62 for the genome model, after filtering 9 junk entries such as `carbapenem`, `geamycin` and `trimotheprim`.
- Genus and species get datalists of recognised values plus a live hint ([forecast.js](frontend/static/js/forecast.js)). The organism quick-select lists only the 9 known organisms and no longer fills a meaningless taxon ID.
- `>=` is normalised to `>` in [lgbm_predictor.py](backend/ml_models/lgbm_predictor.py) instead of being silently dropped.
- Every forecast response carries an `evidence` block, rendered above the result in [resistance_forecast.html](frontend/templates/resistance_forecast.html): per-field used, not recognised or not provided, with a level badge from Population-level to Isolate-level, and a warning when the result would be identical for every isolate.

**Docs:** none at the time. The measured ablation values now in [HANDBOOK §11](experiments/HANDBOOK.md#11-what-the-results-mean) are the justification for the panel's wording.

---

## README.md created (was README.md) (2026-09-24)

A walkthrough of the whole system, verified against the code instead of summarised from the existing documentation. Three findings it recorded:

1. **The k-mer model never runs in the web app.** [train_models.py](backend/train_models.py) fits the scaler on 256 k-mer columns; [resistance_predictor.py:158](backend/ml_models/resistance_predictor.py#L158) passes all 321. The exception is swallowed and a random heuristic answers instead, while the response still reports `'RandomForest K-mer (trained)'`. Reproduced live. The one-line fix already exists at [amrpredict-lib/src/amrpredict/kmer.py:166](amrpredict-lib/src/amrpredict/kmer.py#L166). **Still unfixed in the backend.** Detail in [§11.1](README.md#111-the-k-mer-model-never-runs-in-the-web-app-).
2. **Two AUC lineages.** The notebook model scores 0.8881 on one BV-BRC CSV; the shipped artifact's 0.9255 came from a [train_models.py](backend/train_models.py) run over the per-species exports. Not interchangeable. Detail in [§10](README.md#10-the-numbers-and-where-each-one-comes-from).
3. `forecasting_formulation.ipynb` is a 0-byte file, the UI dropdown offered 48 antibiotics while the k-mer model knows 62, and `db.sqlite3` is vestigial. Detail in [§11.5](README.md#115-smaller-things).

[PROJECT_DOCUMENTATION.md](docs/PROJECT_DOCUMENTATION.md) was left untouched. Its line 726 claim that the k-mer scaler "is applied identically at inference time" is contradicted by finding 1, and that contradiction is recorded in [README.md §11.1](README.md#111-the-k-mer-model-never-runs-in-the-web-app-) instead of by editing the original.

---

## Required input fields enforced (2026-09-24)

**Problem:** the backend rejects a `/predict` or `/timeline` request without a FASTA file or pasted sequence ([views.py](backend/api/views.py)), but [mutation_timeline.html](frontend/templates/mutation_timeline.html) labelled both inputs "(optional)" and neither page checked before submitting.

**Changes:** both FASTA labels on the timeline page marked required; submit handlers in [prediction.js](frontend/static/js/prediction.js) and [timeline.js](frontend/static/js/timeline.js) block submission and show an inline alert; a server-side guard in [frontend/app.py](frontend/app.py) returns the same message when JavaScript is disabled.

A plain HTML `required` attribute does not work here. One of the two inputs is always hidden behind a tab, and a hidden required field blocks submission with no visible message.

---

## Still open

| Item | Detail |
|---|---|
| **K-mer scaler bug**, `/predict` answers from a random heuristic | [README.md §11.1](README.md#111-the-k-mer-model-never-runs-in-the-web-app-) |
| Promotion path: rate tables need renaming and reshaping for the backend | [HANDBOOK §13](experiments/HANDBOOK.md#13-limitations-of-this-harness), [README](experiments/README.md#promoting-a-model-to-the-app) |
| Taxon IDs are strain-level, so the UI's Taxon ID field can never match | [HANDBOOK §3.4](experiments/HANDBOOK.md#34-known-data-quality-issues) |
| Timeline compartments exceed 100% after susceptible exhaustion | [README.md §11.3](README.md#113-timeline-population-shares-exceed-100) |
| No DeLong or McNemar test between runs, no calibration plots, single seed | [HANDBOOK §13](experiments/HANDBOOK.md#13-limitations-of-this-harness) |
| XGBoost and CatBoost written but not installed | [HANDBOOK §7](experiments/HANDBOOK.md#7-algorithms) |
| Junk antibiotic names still in the vocabulary (`amipicillin_sulbactam`, `extended spectrum beta lactamase`) | [HANDBOOK §3.4](experiments/HANDBOOK.md#34-known-data-quality-issues), fix in [data_prep.py](experiments/lib/data_prep.py) |
| Track B (genome model) and Track C (timeline) have no harness | [EXPERIMENT_PLAN.md §5](docs/EXPERIMENT_PLAN.md#5-track-b-genome-model-experiments), [§6](docs/EXPERIMENT_PLAN.md#6-track-c-the-timeline-simulation) |
