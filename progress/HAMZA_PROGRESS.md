# Progress: Hamza Afzal (SP23-BCS-086, leader)

**Role:** models
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-25

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

---

## Summary

| Week | Dates (planned) | Focus | Status |
|---|---|---|---|
| 1 | 28 Sep to 2 Oct | K-mer fix, promote the best model, threshold, calibration, `metrics.json` | Not started |
| 2 | 5 Oct to 9 Oct | Genome experiments B0 to B4 (k-mers) | Not started |
| 3 | 12 Oct to 16 Oct | Gene-feature models B6/B7, deploy the best genome model | Not started |
| 4 | 19 Oct to 23 Oct | Library v0.2.0, statistics and seeds | Not started |
| 5 | 26 Oct to 30 Oct | Results chapters | Not started |

**Files I own:** `experiments/` (except `lib/data_prep.py`, `genome/features/`, `evolution/`), `backend/ml_models/lgbm_predictor.py`, `backend/ml_models/resistance_predictor.py`, `backend/trained_models/`, `amrpredict-lib/`.
Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: leader tasks and handover formats

- [ ] **Scope email to the supervisor:** drug design and images descoped, GAN run as an experiment, RL built as a small agent on the simulation. Keep the reply
- [ ] **`metrics.json` format** agreed with Suleman: run id, date, AUC with CI, AUPRC, F1, accuracy, recall, VME, ME, threshold, train rows, test rows, genera, git commit. Give Suleman a sample file
- [ ] **Genome prediction response** agreed with Suleman: today's response plus `genes_found: [{gene, drug_class}]`
- [ ] **Gene matrix format** agreed with Ali: parquet, one row per `Genome ID`, one 0/1 column per gene
- [ ] Formats written down in the team channel or below

> Agreed formats:
>
> *(paste here once agreed)*

---

## Week 1: honest deployed models

### T1.1 K-mer scaler fix
- [ ] `backend/ml_models/resistance_predictor.py:158`: scale only the first 256 columns, as in `amrpredict-lib/src/amrpredict/kmer.py:166`
- [ ] In the `except` branch set `model_used` to `'Heuristic fallback'`, so a failure can never be shown as the trained model
- **Done when:** the same FASTA on `/predict` gives the same probability twice

### Antibiotic names at prediction time (from Ali's T1.5)
- [ ] Apply the `ANTIBIOTIC_ALIASES` map (in `backend/train_models.py`) to the user's input in `lgbm_predictor.py` and `resistance_predictor.py`, so `rifampin` matches `rifampicin`
- [ ] Note: all 22 existing runs used the old (v1) names. Re-run before promoting

### T1.4 Promote the best tabular model
- [ ] Choose the run: `A10_monotonic_mic` (recommended, safe with MIC) or `A2_oof_grouped`
- [ ] Re-run it on cleaning v2: `python experiments/run.py experiments/configs/A10_monotonic_mic.json`
- [ ] Threshold chosen on the **validation** set with a stated goal (for example VME ≤ 10%, lowest ME)
- [ ] Calibration (isotonic or Platt) on a validation fold; Brier before and after
- [ ] Species-level taxon grouping from Ali used in the rate tables
- [ ] Write `experiments/promote.py`: converts the run's rate tables to the backend's file names, writes `amr_lgbm_final_model.txt`, `lgbm_meta.joblib` and `metrics.json`, copies to `backend/trained_models/` and `amrpredict-lib/src/amrpredict/models/`
- [ ] Restart the backend, check `/api/health/`, run 5 known cases through `/forecast`
- [ ] Re-run `python experiments/evaluate_shipped.py` and `python experiments/export_report.py` so `/models` and `/compare` show the new model
- **Done when:** `/forecast` serves the promoted model and `/compare` shows it

### T1.6 Metrics beside each deployed model
- [ ] `metrics.json` written for the LightGBM (by `promote.py`) and for the K-mer model (from `experiments/results/shipped_eval.json`)
- [ ] Each predictor's `status` returns its `metrics.json`
- **Done when:** Suleman's UI shows numbers read from these files, with nothing typed in by hand

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
| From Ali | Clean antibiotic names (T1.5) | Week 1, day 2 | [x] merged 2026-09-25 (`75a9875`) |
| From Ali | Species-level taxon grouping | Week 1 | [ ] |
| From Ali | 20-genome sample gene matrix | Week 2, day 2 | [ ] |
| From Ali | Full gene matrix | End of week 2 | [ ] |
| To Suleman | Sample `metrics.json` | Day 1 | [ ] |
| To Suleman | Real `metrics.json` for both models | End of week 1 | [ ] |
| To Suleman | Genome response with `genes_found` | Week 3 | [ ] |
| To supervisor | Scope email | Day 1 | [ ] |

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
| 2026-09-25 | Tracker created | Scope email, agree formats | None |
