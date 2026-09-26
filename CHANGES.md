# Changes

What changed, why, and which documents were affected. Newest first.

Baseline is commit **`52ae361`** *(Add amrpredict library and macOS launcher, 2026-09-23)*, the last committed state before this work.

## Documents tracked here

| File | What it is | Status |
|---|---|---|
| [README.md](README.md) | How the whole system fits together | Created, then revised |
| [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | Staged plan for model experiments | Created, then corrected against measurements |
| [experiments/HANDBOOK.md](experiments/HANDBOOK.md) | Full reference for the training setup | Created, then revised |
| [experiments/README.md](experiments/README.md) | Usage card for the harness | Created, then revised |
| [experiments/RESULTS.md](experiments/RESULTS.md) | Generated comparison table | Regenerated after every run |
| [progress/formats/README.md](progress/formats/README.md) | Data handed between Ali, Hamza and Suleman | Created 2026-09-25, extended 2026-09-26 |
| [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | The original long reference | **Unchanged**. Superseding facts are recorded in [README.md](README.md) instead |

---

## Security hardening, honest UI numbers and a safe Train button (2026-09-26)

Suleman's platform work (T1.3, T2.4), plus two fixes found on the way.

### Security (T2.4)
| File | Change |
|---|---|
| [backend/backend/settings.py](backend/backend/settings.py) | `SECRET_KEY` and `ALLOWED_HOSTS` from the environment only, required when `DEBUG` is off (a random key per process when it is on); no CORS origins; `DATABASES = {}`; 20 MB FASTA limit; rate limits; `ADMIN_TOKEN` |
| [backend/api/views.py](backend/api/views.py) | `X-Admin-Token` on `/api/train/` and `/api/reload/` (401, or 503 when no token is set); 413 for oversized FASTA; 429 per visitor IP on forecast, predict, timeline; `/api/train/` takes only `lgbm` or `kmer`; the 8 no-op `csrf_exempt` decorators removed, with the reason at the top |
| [frontend/app.py](frontend/app.py), [train.html](frontend/templates/train.html), [train.js](frontend/static/js/train.js) | Admin password on `/train`, sent with Train and Reload; the browser's IP forwarded for the rate limit; 20 MB upload limit with a message on the page; no hardcoded `secret_key`; debug server on 127.0.0.1 only |
| [start.sh](start.sh), [start.bat](start.bat), [run_project.md](run_project.md) | Start the backend with `DEBUG=True`; say how to set `ADMIN_TOKEN`; no `migrate` |
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

- [fasta_amr_map.py](fasta_amr_map.py): reads Genome ID as text.
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
- [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md): C3 marked done in the backend.

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
- [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md): status banner.

Not yet changed: the "AUC 0.93" badges on the dashboard, `/predict`, `/about`, `/datasets` and in the footer still quote the original figures. *(Replaced on 2026-09-26: every page now reads these from the metrics files; see the entry above.)*

---

## Plain prose pass (2026-09-24)

Em dashes and en dashes removed from every document and from the experiment code, and phrasing that read as machine-written rewritten.

| Area | Files |
|---|---|
| Documents | [CHANGES.md](CHANGES.md), [README.md](README.md), [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md), [HANDBOOK.md](experiments/HANDBOOK.md), [README.md](experiments/README.md), [RESULTS.md](experiments/RESULTS.md) |
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

### [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md)
- Status banner: 19 runs across three algorithms.
- [Track A](EXPERIMENT_PLAN.md#4-track-a-tabular-forecaster-experiments) rows **A3**, **A4**, **A10** marked done with measured numbers.
- New [§8b](EXPERIMENT_PLAN.md#8b-what-19-runs-have-shown), a summary table answering each question the plan posed with a measurement.
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

Two predictions written into [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) were wrong and were replaced with measurements.

| Claim | Predicted | Measured | Runs |
|---|---|---|---|
| Target leakage inflates the AUC substantially | 0.93 to ~0.88 | **0.002** (0.8243 vs 0.8225), intervals overlap | [`A0_baseline_leaky`](experiments/configs/A0_baseline_leaky.json), [`A1_oof_random`](experiments/configs/A1_oof_random.json) |
| Grouped splitting will cost accuracy | "small further drop" | **None**. Grouped 0.8232 is marginally *higher* | [`A2_oof_grouped`](experiments/configs/A2_oof_grouped.json) |

Both are explained by scale: with 1.5 M rows and a min-count floor, an encoded group is estimated from many rows, so one test row's own label barely shifts its group mean. The leakage would matter on the 90k subset; it does not here. Both fixes were kept regardless, since they cost nothing and remove the objection. Corrected text is in [§1.2](EXPERIMENT_PLAN.md#12-target-encodings-leak-into-the-test-set-) and [§1.3](EXPERIMENT_PLAN.md#13-rows-from-one-genome-land-on-both-sides-of-the-split-).

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

[PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) was left untouched. Its line 726 claim that the k-mer scaler "is applied identically at inference time" is contradicted by finding 1, and that contradiction is recorded in [README.md §11.1](README.md#111-the-k-mer-model-never-runs-in-the-web-app-) instead of by editing the original.

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
| Track B (genome model) and Track C (timeline) have no harness | [EXPERIMENT_PLAN.md §5](EXPERIMENT_PLAN.md#5-track-b-genome-model-experiments), [§6](EXPERIMENT_PLAN.md#6-track-c-the-timeline-simulation) |
