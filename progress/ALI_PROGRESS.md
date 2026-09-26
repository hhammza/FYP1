# Progress: Muhammad Ali Mirza (SP23-BCS-082)

**Role:** data and evolution

**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../FYP_Completion_Roadmap.md)

**Started:** 2026-09-25 · **Last updated:** 2026-09-26

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

---

## Summary

| Week | Dates (planned) | Focus | Status |
| --- | --- | --- | --- |
| 1 | 28 Sep to 2 Oct | Clean names, data path, taxon grouping, start AMRFinderPlus | In progress: names, data path and taxon grouping done; AMRFinderPlus full run going (restarted 2026-09-26) |
| 2 | 5 Oct to 9 Oct | Gene matrix | Started early: builder and 20-genome sample done 2026-09-26 |
| 3 | 12 Oct to 16 Oct | Evolution: fix, sensitivity, calibration | Not started |
| 4 | 19 Oct to 23 Oct | RL agent, CTGAN experiment | Not started |
| 5 | 26 Oct to 30 Oct | Report chapters | Not started |

**Files I own:** `Data/`, `experiments/lib/data_prep.py`, `backend/train_models.py`, `experiments/genome/features/` (new), `backend/ml_models/mutation_timeline.py`, `experiments/evolution/` (new). Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: agree the handover formats

- [x] **Gene matrix format** agreed with Hamza: parquet, one row per `Genome ID`, one 0/1 column per gene symbol. *Agreed 2026-09-26 with notes: filter `core` + `Type = AMR`, no plus file (run had no `--plus`)*

- [~] **Timeline + RL response** agreed with Suleman: weekly susceptible, intermediate and resistant fractions, plus a `policy` list (drug used each week). *Proposed 2026-09-26 with a sample; waiting for Suleman*

- [x] Both formats written down in the team channel or in this file (below)

> Agreed formats: **[progress/formats/README.md](formats/README.md)** §3 gene matrix (with my notes) and §4 timeline + RL (sample: [`timeline_response.sample.json`](formats/timeline_response.sample.json))

---

## Week 1: data correctness

### T1.5 Antibiotic name clean-up (first two days, Hamza re-promotes after this) `[x]` merged in `0ba94cd`

- [x] List every antibiotic spelling in the data: 152 names after the v1 clean-up

- [x] Add `ANTIBIOTIC_ALIASES` entries: 16 renames (underscore variants, typos `amipicillin_sulbactam`, `tgecycline`, `strofurantoin`, `pristimycin`, broken `cefuroximâ`, alternative names `synercid`, `cefalotin`, `cefalexin`, `cefuroxime_sodium`)

- [x] Drop non-drugs: `carbapenem`, `beta-lactam`, `cephalosporin`, `fluoroquinolones`, `aminogycosides`, `macrolides`, `sulfonamides`, `extended spectrum beta lactamase`, `instrument` (C. difficile rows with the drug name lost)

- [x] Checked, not merged: `trimethoprim/sulfobactam` (every genome also has a separate trimethoprim/sulfamethoxazole row)

- [x] Drug classes added for the renamed drugs (rows in class `other`: 38,851 → 26,163)

- [x] `CLEAN_VERSION` bumped to `v2` so stale cached data cannot be reused

- [x] Apply the same map in `backend/train_models.py` (`normalize_antibiotics()`, used by both the LightGBM and K-mer trainers; maps checked identical)

- [~] Update the dropdown list in `frontend/app.py:ANTIBIOTICS` (Suleman's file): note below, also in Suleman's tracker

- [x] Rebuild the cache: `python experiments/lib/data_prep.py` → 130 names, 1,521,644 rows (was 152 and 1,525,796)

- [x] Tell Hamza it is merged, and that the model predictors need the same map at prediction time (`lgbm_predictor.py`, `resistance_predictor.py`), and that all 22 runs used v1 names

- [x] Handbook §3.3 and §3.4 updated

- **Done when:** no two names in the cleaned data mean the same drug. **Checked:** no separator duplicates, no underscores, no non-ASCII names, no alias key left

> **Note for Suleman (dropdown list):** replace `rifampin` with `rifampicin`, the only UI name not in the cleaned data. Consider adding these drugs with 1,000+ rows that the dropdown lacks: spectinomycin, ceftiofur, ampicillin/sulbactam, sulfisoxazole, pefloxacin, penicillin, ceftazidime/avibactam, ceftolozane/tazobactam, cefixime, telithromycin, moxifloxacin, clarithromycin, temocillin, cefpirome, florfenicol.

### T1.2 Training data path `[x]` done 2026-09-25 in `8f47f45`

- [x] `resolve_data_dir()` finds `Data/` from the project root or the data folder, so both the command line and `/api/train/` work (no change needed in `settings.py`)

- [x] `select_files()`: sorted, all files by default; `--max-files N` takes a seeded random subset (500 files: 19 genera instead of 11). New `--model-dir` flag so test runs don't overwrite deployed models

- [x] K-mer trainer reads only `*_mapped.csv` (no longer loads `mapping_summary.csv`)

- [x] `/api/train/` returns HTTP 503 with a message when the data is missing (Suleman's `views.py`, 8 lines; noted in Suleman's tracker)

- [x] Tested: LightGBM on all files, 1,521,618 rows, about 4 min, test AUC 0.825; K-mer on 15 files; deployed models untouched

- [x] README §5, §9, §11.2 updated

- **Done when:** `cd backend && python train_models.py --model lgbm` finds the data

### Species-level taxon grouping (part of T1.4) `[x]` done 2026-09-25

- [x] `experiments/build_taxonomy.py`: all 3,655 Taxon IDs looked up in NCBI → `backend/taxon_species.csv` (164 species, none unknown)

- [x] `train_models.py`: `load_species_map()` / `to_species_taxon()`; trains and builds the taxon table on species IDs (strain ID kept as `strain_taxon_id`)

- [x] `data_prep.py`: new `species_taxon_id` column, cleaning v3 (3,549 IDs → 124 species; `Taxon ID` unchanged so Hamza can compare)

- [x] Fixed stray quotes in genome names (`"neisseria` was a separate genus; 41 → 40 genera)

- [x] Tested: retrained model recognises taxon 562 (ciprofloxacin rate 6.5%); deployed model does not. Trainer's random-split AUC 0.825 → 0.805, because strain IDs let it partly recognise genomes

- [x] Hand the grouping function to Hamza for `promote.py` (in Hamza's tracker)

- **Done when:** taxon 562 (*E. coli*) matches a rate on `/forecast`. **Met for a retrained model;** live once Hamza promotes one

### Start AMRFinderPlus (longest job, start by Wednesday) `[~]` started 2026-09-25

- [x] Found the local FASTAs are truncated (E. coli about 0.8 of 5 MB; 1000561.3 is 74 KB of 6.3 MB). `download_genomes.py` fetches complete assemblies from the BV-BRC API into `Data/genomes_full/` (gitignored), keeping a file only if its length matches BV-BRC within 1%

- [x] Installed natively on the Mac (no WSL2 or Colab needed): conda env `amrfinder`, AMRFinderPlus 4.2.7, database 2026-08-07.1

- [x] Tested on 5 genomes: P. aeruginosa found `gyrA_T83I`, `blaOXA-904`, `oprD`/`nalC` carbapenem mutations; S. pneumoniae found `pbp1a`/`pbp2b` mutations and `mef(A)`, `msr(D)`

- [x] Species mapped to `--organism` from `backend/taxon_species.csv`, in `run_amrfinder.py`: 2,533 genomes get a flag, 54 run without one (M. tuberculosis, K. michiganensis and 3 small ones). Table in `experiments/genome/README.md`

- [~] Full run over all 2,587 genomes: download (12 workers, about 3 hours) and AMRFinderPlus running together in the background

- [x] `Data/genomes_full/` and `Data/amrfinder_output/` added to `.gitignore`

> **Note for Hamza:** the K-mer model was trained on the truncated FASTAs. Worth retraining B-track k-mer runs on `Data/genomes_full/` once downloaded.

---

## Week 2: gene matrix (T2.1, data side)

- [x] **Day 2 of the week: commit a 20-genome sample matrix** so Hamza can write model code. *Done early, 2026-09-26: `experiments/genome/features/sample/` (20 genomes, 7 genera, 7 with no core AMR hit; all 20 join to their labels)*

- [ ] Full run finished, failures logged and re-run

- [~] Build the genome × gene 0/1 matrix, include point mutations (for example `gyrA_S83L`). *`build_gene_matrix.py` written; run it again when AMRFinderPlus finishes*

- [x] Save as parquet under `experiments/genome/features/` (`pyarrow` in the new `experiments/requirements.txt`)

- [ ] Check the join: every `Genome ID` in `Data/mapped_output/` has a row

- [ ] Short summary: genes found, genes per genome, most common genes per genus

- [x] Do **not** commit the per-genome TSVs (add them to `.gitignore`): done in week 1

- **Done when:** Hamza can load the matrix and join it to labels without help

---

## Week 3: evolution component (T3.1)

- [x] **Fix >100% bug** in `mutation_timeline.py`: susceptible + intermediate + resistant = 100 every week. *Done early, 2026-09-26, in the backend: checked on every drug profile at 1 to 52 weeks (20,020 weeks, all exactly 100). Also `simulation`, `seed`, `calibration` fields and `model_used` always `Biological Simulation`, per format §4*

- [x] Seed the random parts, so the same inputs give the same output (`predict(..., seed=42)`, one `numpy` generator)

- [ ] Remove the strict `xfail` in `amrpredict-lib/tests/test_fasta.py:122` so the test must pass. *Waits for Hamza: the library has its own copy in `amrpredict-lib/src/amrpredict/timeline.py`; remove the xfail when he syncs the fix (T2.6)*

- [ ] **Sensitivity analysis:** sweep `speed` and `peak` ±30%, plot how `failure_week` moves

- [ ] **Literature calibration:** collect 5 to 10 published serial-passage or lab-evolution curves

  - [ ] Curves collected (table: drug, organism, source, data points)

  - [ ] Fit logistic parameters per drug (`scipy.optimize.curve_fit`), report RMSE

- [ ] Work lives in `experiments/evolution/`

- **Done when:** the timeline is a partition, repeatable, and "calibrated against N published curves"

---

## Week 4: RL agent and CTGAN

### RL agent (T3.1c)

- [ ] Gymnasium environment around the simulation: state = resistant fractions per drug, action = drug this week, reward = minus infection burden minus resistance growth

- [ ] Train PPO or DQN with `stable-baselines3`

- [ ] Compare with "always drug A" and simple cycling A → B → C

- [ ] Output in the agreed response format for Suleman's panel

- **Done when:** a table shows which policy delays treatment failure longest

### CTGAN experiment (T3.2)

- [ ] Train CTGAN on training rows only (`pip install ctgan` or `sdv`)

- [ ] Generate rows only for rare antibiotics or genera

- [ ] Run `A13_ctgan` (A2 config + synthetic rows in training only), evaluate on the real test set

- [ ] Report synthetic-data quality and the AUC/AUPRC change with confidence intervals

- [ ] Do **not** commit synthetic data files

- **Done when:** result is in `experiments/results/registry.csv`, even if there is no gain

---

## Week 5: report

- [ ] **Data chapter:** BV-BRC export, cleaning, lab vs computational labels, data-quality issues, name clean-up, gene features

- [ ] **Methodology chapter:** features, target encoding and the leakage fix, genome-grouped split, metrics, evolution model and RL

- [ ] Figures: sensitivity analysis, calibration fits, RL comparison, gene summary

- [ ] Update `CHANGES.md` for my work

---

## Handovers

| To | What | Needed by | Status |
| --- | --- | --- | --- |
| Hamza | Clean antibiotic names merged | Week 1, day 2 | [x] merged 2026-09-25 (`0ba94cd`) |
| Hamza | Trainer data path fix (T1.2) | Week 1 | [x] merged 2026-09-25 (`8f47f45`), noted in Hamza's tracker |
| Hamza | Species-level taxon grouping | Week 1 | [x] 2026-09-25, in Hamza's tracker |
| Hamza | 20-genome sample gene matrix | Week 2, day 2 | [x] 2026-09-26, `experiments/genome/features/sample/` |
| Hamza | Full gene matrix | End of week 2 | [ ] |
| Suleman | Canonical antibiotic list for dropdowns | Week 1 | [x] in `SULEMAN_PROGRESS.md` week 1 |
| Hamza, Suleman | `train_models.py` from the command line no longer writes to the served models: default is `trained_models/candidates/<model>/`, like `/api/train/` | Week 1 | [x] 2026-09-26; checked the served files are byte-identical after a run |
| Hamza | Timeline fix is in the backend only; the library copy (`amrpredict/timeline.py`) still has the >100% bug. Sync it in T2.6, then remove the strict xfail | Week 4 | [ ] |
| Suleman | Templates still mention CNN-LSTM for the timeline (`mutation_timeline.html:164`, `train.html:132-137`, `datasets.html:468`); the API now says `Biological Simulation` only | Week 2 | [ ] |
| Suleman | Timeline + RL response format | Day 1 | [~] proposed in `progress/formats/README.md` §4 with a sample; backend already returns the §4 timeline fields |
| Suleman | Working RL output | Week 4 | [ ] |

---

## Already done (before this plan)

- [x] Re-tested the deployed models on unseen genomes (`experiments/evaluate_shipped.py`): LightGBM 0.644, K-mer 0.695

- [x] Report export script (`experiments/export_report.py`) and training-data profiles (`experiments/lib/profile.py`)

- [x] `/models` and `/compare` pages

- [x] Documentation updated (`README.md`, `experiments/README.md`, `experiments/HANDBOOK.md`, `CHANGES.md`)

---

## Log

Newest first. One line per work session: date, what I did, what is next, anything blocking.

| Date | Done | Next | Blockers |
| --- | --- | --- | --- |
| 2026-09-26 | Gene-matrix format agreed (§3, with notes) and timeline + RL format proposed (§4). `build_gene_matrix.py` and the 20-genome sample; `pyarrow` in `experiments/requirements.txt`. Trainer defaults to `candidates/`. Timeline partition, seed and honest label. Download and AMRFinderPlus restarted. Seen Hamza's cleaning v4 in `data_prep.py` (54 drug classes) | Full matrix once AMRFinderPlus finishes; Suleman to confirm §4 | None |
| 2026-09-25 | AMRFinderPlus: found truncated FASTAs, download script for full assemblies, installed natively, tested 5 genomes, organism mapping, full run started | Finish the full run, then the 20-genome sample matrix | None (download takes about 3 hours) |
| 2026-09-25 | Species-level taxon grouping: NCBI lookup table, species IDs in trainer and cleaning v3, quote fix, docs | Start AMRFinderPlus | None |
| 2026-09-25 | T1.2 data path: trainer finds `Data/`, reads all files (seeded subset optional), `/api/train/` fails clearly, README updated | Species-level taxon grouping, then AMRFinderPlus | None |
| 2026-09-25 | T1.5 name clean-up: 24 new aliases, cleaning v2 (152 → 130 names), same map in `train_models.py`, handbook updated | T1.2 data path | None |
| 2026-09-25 | Created this tracker | Agree formats with Hamza and Suleman | None |
