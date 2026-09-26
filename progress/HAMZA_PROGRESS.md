# Progress: Hamza Afzal (SP23-BCS-086, leader)

**Role:** models
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-26 (Day 1 + Week 1, drug classes and D2)

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

---

## Summary

| Week | Dates (planned) | Focus | Status |
|---|---|---|---|
| 1 | 28 Sep to 2 Oct | K-mer fix, promote the best model, threshold, calibration, `metrics.json` | Done 2026-09-25 (UI side waits on Suleman) |
| 2 | 5 Oct to 9 Oct | Genome experiments B0 to B4 (k-mers) | Not started |
| 3 | 12 Oct to 16 Oct | Gene-feature models B6/B7, deploy the best genome model | Not started |
| 4 | 19 Oct to 23 Oct | Library v0.2.0, statistics and seeds | Not started |
| 5 | 26 Oct to 30 Oct | Results chapters | Not started |

**Files I own:** `experiments/` (except `lib/data_prep.py`, `genome/features/`, `evolution/`), `backend/ml_models/lgbm_predictor.py`, `backend/ml_models/resistance_predictor.py`, `backend/trained_models/`, `amrpredict-lib/`.
Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: leader tasks and handover formats

- [x] **Scope email to the supervisor:** drug design and images descoped, GAN run as an experiment, RL built as a small agent on the simulation. Keep the reply. *Sent 2026-09-25; waiting for the reply (paste its date and any scope changes here)*
- [x] **`metrics.json` format** agreed with Suleman: run id, date, AUC with CI, AUPRC, F1, accuracy, recall, VME, ME, threshold, train rows, test rows, genera, git commit. Give Suleman a sample file. *Sample is the real file: [`progress/formats/lgbm_metrics.sample.json`](formats/lgbm_metrics.sample.json)*
- [x] **Genome prediction response** agreed with Suleman: today's response plus `genes_found: [{gene, drug_class}]`. *Sample: [`progress/formats/genome_response.sample.json`](formats/genome_response.sample.json)*
- [~] **Gene matrix format** agreed with Ali: parquet, one row per `Genome ID`, one 0/1 column per gene. *Proposed with a `gene_info.csv` sidecar and a string `Genome ID` index; waiting for Ali*
- [x] Formats written down in the team channel or below

> Agreed formats: **[progress/formats/README.md](formats/README.md)** (metrics files, genome response, gene matrix). Suleman and Ali: edit that file if anything doesn't suit your side.

---

## Week 1: honest deployed models

### T1.1 K-mer scaler fix `[x]`
- [x] `backend/ml_models/resistance_predictor.py:158`: scale only the first 256 columns, as in `amrpredict-lib/src/amrpredict/kmer.py:166`
- [x] In the `except` branch set `model_used` to `'Heuristic fallback'`, so a failure can never be shown as the trained model
- **Done when:** the same FASTA on `/predict` gives the same probability twice. **Met:** `1001988.3` + ciprofloxacin → 0.8569 twice, `model_used: RandomForest K-mer (trained)`

### Antibiotic names at prediction time (from Ali's T1.5) `[x]`
- [x] Apply the `ANTIBIOTIC_ALIASES` map (in `backend/train_models.py`) to the user's input in `lgbm_predictor.py` and `resistance_predictor.py`, so `rifampin` matches `rifampicin`. *Shared helper `backend/ml_models/common.py`; the k-mer model maps canonical names back to its own training spelling (`rifampin`)*
- [x] Note: all 22 existing runs used the old (v1) names. Re-run before promoting. *A10 re-run on v3; the other 21 rows in the registry are still v1, so compare them with care*

### T1.4 Promote the best tabular model `[x]`
- [x] Choose the run: `A10_monotonic_mic` (recommended, safe with MIC) or `A2_oof_grouped`. *Chose A10 + species taxa + calibration + VME threshold = `D1_forecaster_deploy`*
- [x] Re-run it on cleaning v2: `python experiments/run.py experiments/configs/A10_monotonic_mic.json`. *Re-run on v3*
- [x] Threshold chosen on the **validation** set with a stated goal: VME ≤ 10%, lowest ME → **0.24**
- [x] Calibration (isotonic) on a validation fold; Brier 0.1795 → **0.1678**, AUC unchanged
- [x] Species-level taxon grouping from Ali used in the rate tables (`"taxon_level": "species"` in the config); taxon 562 now matches on `/forecast`
- [x] Write `experiments/promote.py`. *Copies to `backend/trained_models/` only; `--library` is opt-in until T2.6, because the package loader doesn't apply calibration or species taxa yet*
- [x] Restart the backend, check `/api/health/`, run 5 known cases through `/forecast`
- [x] Re-run `python experiments/evaluate_shipped.py` and `python experiments/export_report.py` so `/models` and `/compare` show the new model
- **Done when:** `/forecast` serves the promoted model and `/compare` shows it. **Met** (local): `/api/health/` reports `D1_forecaster_deploy`; `/models` and `/compare` show 0.800

**Week 1 results**

| Model | Unseen-genome AUC | Notes |
|---|---|---|
| July LightGBM (replaced) | 0.644 [0.642–0.645] | 0.941 on genomes it trained on: it memorised |
| `A10_monotonic_mic`, strain taxa, v3 | 0.8223 [0.8193–0.8258] | same as on v1 (0.8222): the name clean-up cost nothing |
| `A10s_monotonic_species` | 0.8044 [0.8011–0.8081] | species taxa cost 0.018, the price of a Taxon ID users can type |
| `D1_forecaster_deploy` (served 2026-09-25, replaced by D2) | **0.8043 [0.801–0.808]** harness · **0.7998 [0.7965–0.8036]** as `/forecast` scores it | calibrated (Brier 0.1795 → 0.1678), threshold 0.24: VME 9.1%, ME 52.9%, recall 90.9%, accuracy 63.0%. Seen genomes 0.8005 vs unseen 0.7998: no memorisation |
| **`D2_forecaster_deploy`** (served) | **0.8044 [0.8010–0.8080]** harness | D1 on cleaning v4: 54 drugs moved out of drug class `other`. Threshold 0.25: VME 9.0%, ME 53.0%. On the 5,106 test rows of those drugs AUC 0.8648 → 0.8652: the model already knew them by name; the gain is for drugs it never saw (e.g. ceftobiprole), which now get their real class |
| K-mer RF (unchanged, now actually runs) | 0.695 [0.679–0.714] | 0/100 heuristic fallbacks (was every call); no better than the drug alone (0.703) |

Threshold trade-off on D2's test set, for the report (the threshold itself was chosen on validation):

| Threshold | 0.20 | **0.25** | 0.30 | 0.35 | 0.40 | 0.50 |
|---|---|---|---|---|---|---|
| VME | 7.3% | **9.0%** | 17.4% | 24.7% | 30.2% | 54.2% |
| ME | 56.4% | **53.0%** | 40.6% | 31.9% | 26.7% | 10.0% |

### T1.6 Metrics beside each deployed model `[x]`
- [x] `lgbm_metrics.json` written by `promote.py`; `kmer_metrics.json` written by `evaluate_shipped.py`
- [x] Each predictor's `status` returns its metrics file (`/api/health/` → `models.*.metrics`, plus `default_threshold`)
- **Done when:** Suleman's UI shows numbers read from these files, with nothing typed in by hand. **Met** (Suleman, `d5044a7`): the site shows 0.804 and 0.695 from the metrics files; the old 0.93 survives only in the `/about` sentence explaining why it was wrong

---

## Week 2: genome experiments on k-mers (no gene matrix needed)

New folder `experiments/genome/`, reusing `lib/splits.py` and `lib/metrics.py`.

- [ ] **B0** fixed k-mer RF, random split (what was shipped)
- [ ] **B1** same, genome-grouped split (how much was memorisation)
- [ ] **B2** k = 3, 4, 5, 6
- [ ] **B4** LightGBM on k-mers
- [ ] Load Ali's 20-genome sample gene matrix and write the B6 code against it
- **Done when:** B0 to B4 are in the registry with grouped-split AUCs and confidence intervals

---

## Week 3: gene-feature models and deployment

- [ ] **B6** AMR-gene presence features (Ali's full gene matrix) + antibiotic + drug class + genus
- [ ] **B7** B6 + k-mers + genus (the "multimodal" model)
- [ ] **B8** species hold-out
- [ ] Per-antibiotic AUC table for the winning run
- [ ] Deploy the winner on `/predict` with its own `metrics.json`, returning `genes_found`
- **Done when:** `/predict` names the genes it found, and its AUC comes from a grouped split

---

## Week 4: library and statistics

### T2.6 Library v0.2.0
- [ ] New models and `metrics.json` in `amrpredict-lib/src/amrpredict/models/`
- [ ] Backend imports `amrpredict` instead of its own copies in `backend/ml_models/` (agree the switch-over with Suleman, who owns `backend/api/`)
- [ ] `amrpredict.status()` returns the metrics
- [ ] Version `0.1.0` → `0.2.0` in `amrpredict-lib/pyproject.toml`; update `docs/` and `known-issues.md`
- [ ] Pin `scikit-learn` to the version used for training (`backend/requirements.txt` has `>=1.3`)
- [ ] `python -m build`, then `twine upload --repository testpypi dist/*`
- **Done when:** `pip install` from TestPyPI works in a clean venv

### T2.5 Evaluation completeness
- [ ] Accuracy, recall and specificity columns in `experiments/lib/metrics.py` and `RESULTS.md`
- [ ] Calibration plot for the deployed model
- [ ] DeLong test between A2/A10 and alternatives; McNemar at the chosen threshold
- [ ] 3 seeds for A2, A10 and the best genome run; mean ± sd
- **Done when:** every headline number in the report has a CI or a significance test

---

## Week 5: report

- [ ] **Results chapters:** comparison table, ablations, learning curve, species hold-out, threshold trade-off, calibration, genome B-track
- [ ] **Deployed-system evaluation:** shipped vs new re-test
- [ ] Update `CHANGES.md` for my work
- [ ] Final version bump and release of the library once everyone's work is merged

---

## Handovers

| From / to | What | Needed by | Status |
|---|---|---|---|
| From Ali | Clean antibiotic names (T1.5) | Week 1, day 2 | [x] merged 2026-09-25 (`0ba94cd`) |
| From Ali | Trainer data path fixed (T1.2): `train_models.py` finds `Data/`, reads all files by default, `--max-files N` for a seeded subset, `--model-dir` to avoid overwriting `trained_models/`. LightGBM on all files: about 4 min. K-mer on all files: about 1 hour, because GC content is computed per row (worth caching per genome) | Week 1 | [x] merged |
| From Ali | Species-level taxon grouping | Week 1 | [x] 2026-09-25. `backend/taxon_species.csv` maps every Taxon ID to its NCBI species; `train_models.load_species_map()` / `to_species_taxon()`; `species_taxon_id` column in cleaning v3. **To do (Hamza):** in `lgbm_predictor.py` map the user's `taxon_id` through `load_species_map()` before the rate lookup, and ship it with the retrained model (the deployed model is still strain level). Also worth a grouped-split run comparing `Taxon ID` and `species_taxon_id` (random-split AUC fell 0.825 → 0.805, expected) |
| From Ali | FYI: the FASTAs in `Data/fasta_output/` are truncated (E. coli about 0.8 of 5 MB), so the shipped K-mer model and any k-mer run on them saw partial genomes. Complete assemblies are being downloaded to `Data/genomes_full/<genome_id>.fna` (gitignored; see `experiments/genome/README.md`). Consider running B0 to B4 on those | Week 2 | [~] download running 2026-09-25 |
| From Ali | 20-genome sample gene matrix | Week 2, day 2 | [ ] |
| From Ali | Full gene matrix | End of week 2 | [ ] |
| To Suleman | Sample `metrics.json` | Day 1 | [x] 2026-09-25: `progress/formats/lgbm_metrics.sample.json` (the real file) |
| To Suleman | Real `metrics.json` for both models | End of week 1 | [x] 2026-09-25: `backend/trained_models/lgbm_metrics.json`, `kmer_metrics.json`; also in `/api/health/` → `models.*.metrics` |
| To Suleman | **Threshold default: the slider and API must start at `default_threshold` (now 0.25), not 0.40.** Hardcoded in `resistance_forecast.html:137-145`, `frontend/app.py:109`, `backend/api/views.py:53`. At 0.40 the calibrated model misses 30.2% of resistant isolates instead of 9.0%. `/predict` likewise: `default_threshold` from `kmer_metrics.json`, 0.5 | Week 1 | [x] 2026-09-26 (`d5044a7`): the slider starts at `metrics.lgbm.threshold` and the API uses the model's own when none is sent, so it follows each promotion (0.25 for D2) |
| To Suleman | New response fields: `/forecast` has `model_run`, `calibrated`; both pages can return `model_used: "Heuristic fallback"` (show a warning); `/predict` has `antibiotic_known` | Week 1 | [ ] |
| To Suleman | Genome response with `genes_found` | Week 3 | [ ] |
| To Ali | Proposed gene-matrix format in `progress/formats/README.md` §3 (string `Genome ID` index, zero rows for searched genomes, `gene_info.csv`); `pyarrow` needed | Day 1 | [~] waiting for Ali |
| To supervisor | Scope email | Day 1 | [x] sent 2026-09-25; reply pending |

---

## Already done (before this plan)

From the git history:

- [x] Initial project upload: backend, frontend, notebooks, trained models (May 2026)
- [x] Project setup documentation (2026-09-23)
- [x] Google Drive link for the data (`Data_Drive`, 2026-09-24)
- [x] Completion roadmap (`FYP_Completion_Roadmap.md`, 2026-09-25)

---

## Log

Newest first. One line per work session: date, what I did, what is next, anything blocking.

| Date | Done | Next | Blockers |
|---|---|---|---|
| 2026-09-26 | T1.6 met: Suleman's UI reads every score from the metrics files and the threshold from the model; checked it follows D2 (0.25), not a typed-in 0.24. `/train` now writes to `trained_models/candidates/`; the command-line trainer still defaults to `trained_models/` (Ali to fix) | Don't run `train_models.py` without `--model-dir` | None |
| 2026-09-26 | Drug classes for 54 drugs that were `other` (cleaning v4, `data_prep.py` and `train_models.py`; `lgbm_predictor.py` now imports the trainer's map instead of its own copy). Every dropdown drug has a class. Trained and promoted `D2_forecaster_deploy`, re-tested, report refreshed | Same as below | `data_prep.py` is Ali's file: tell him about v4 |
| 2026-09-25 | Day 1 formats written (`progress/formats/`); scope email drafted. Week 1: k-mer scaler fix; antibiotic aliases at prediction time (`ml_models/common.py`); harness gains `taxon_level`, calibration and accuracy; ran A10 (v3), A10s, D1; `promote.py`; D1 promoted; July genus-rate lookup bug fixed in passing (table stored `Escherichia`, lookup used `escherichia`); `evaluate_shipped.py` re-tests promoted models through the backend's own `features_frame()` and writes `kmer_metrics.json`; `export_report.py` keeps ROC curves whose `predictions.csv` is missing | Send scope email; Suleman: threshold default + metrics in UI; Ali: confirm gene-matrix format; Week 2 k-mer runs | Library not updated (T2.6): promoting with `--library` before its loader applies calibration would make `amrpredict.forecast()` disagree with the web app. The other 21 registry rows are still cleaning v1 |
| 2026-09-25 | Tracker created | Scope email, agree formats | None |
