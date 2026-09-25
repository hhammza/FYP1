# Progress: Muhammad Ali Mirza (SP23-BCS-082)

**Role:** data and evolution **Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../FYP_Completion_Roadmap.md)**Started:** 2026-09-25 · **Last updated:** 2026-09-25

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

---

## Summary

| Week | Dates (planned) | Focus | Status |
| --- | --- | --- | --- |
| 1 | 28 Sep to 2 Oct | Clean names, data path, taxon grouping, start AMRFinderPlus | In progress (name clean-up merged) |
| 2 | 5 Oct to 9 Oct | Gene matrix | Not started |
| 3 | 12 Oct to 16 Oct | Evolution: fix, sensitivity, calibration | Not started |
| 4 | 19 Oct to 23 Oct | RL agent, CTGAN experiment | Not started |
| 5 | 26 Oct to 30 Oct | Report chapters | Not started |

**Files I own:** `Data/`, `experiments/lib/data_prep.py`, `backend/train_models.py`, `experiments/genome/features/` (new), `backend/ml_models/mutation_timeline.py`, `experiments/evolution/` (new). Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: agree the handover formats

- [ ] **Gene matrix format** agreed with Hamza: parquet, one row per `Genome ID`, one 0/1 column per gene symbol

- [ ] **Timeline + RL response** agreed with Suleman: weekly susceptible, intermediate and resistant fractions, plus a `policy` list (drug used each week)

- [ ] Both formats written down in the team channel or in this file (below)

> Agreed formats:

*> *(paste here once agreed)*

---

## Week 1: data correctness

### T1.5 Antibiotic name clean-up (first two days, Hamza re-promotes after this) `[x]` merged in `75a9875`

- [x] List every antibiotic spelling in the data: 152 names after the v1 clean-up

- [x] Add `ANTIBIOTIC_ALIASES` entries: 16 renames (underscore variants, typos `amipicillin_sulbactam`, `tgecycline`, `strofurantoin`, `pristimycin`, broken `cefuroximâ`, alternative names `synercid`, `cefalotin`, `cefalexin`, `cefuroxime_sodium`)

- [x] Drop non-drugs: `carbapenem`, `beta-lactam`, `cephalosporin`, `fluoroquinolones`, `aminogycosides`, `macrolides`, `sulfonamides`, `extended spectrum beta lactamase`, `instrument` (C. difficile rows with the drug name lost)

- [x] Checked, not merged: `trimethoprim/sulfobactam` (every genome also has a separate trimethoprim/sulfamethoxazole row)

- [x] Drug classes added for the renamed drugs (rows in class `other`: 38,851 → 26,163)

- [x] `CLEAN_VERSION` bumped to `v2` so stale cached data cannot be reused

- [x] Apply the same map in `backend/train_models.py` (`normalize_antibiotics()`, used by both the LightGBM and K-mer trainers; maps checked identical)

- \[\~\] Update the dropdown list in `frontend/app.py:ANTIBIOTICS` (Suleman's file): send him the note below

- [x] Rebuild the cache: `python experiments/lib/data_prep.py` → 130 names, 1,521,644 rows (was 152 and 1,525,796)

- [x] Tell Hamza it is merged, and that the model predictors need the same map at prediction time (`lgbm_predictor.py`, `resistance_predictor.py`), and that all 22 runs used v1 names

- [x] Handbook §3.3 and §3.4 updated

- **Done when:** no two names in the cleaned data mean the same drug. **Checked:** no separator duplicates, no underscores, no non-ASCII names, no alias key left

> **Note for Suleman (dropdown list):** replace `rifampin` with `rifampicin`, the only UI name not in the cleaned data. Consider adding these drugs with 1,000+ rows that the dropdown lacks: spectinomycin, ceftiofur, ampicillin/sulbactam, sulfisoxazole, pefloxacin, penicillin, ceftazidime/avibactam, ceftolozane/tazobactam, cefixime, telithromycin, moxifloxacin, clarithromycin, temocillin, cefpirome, florfenicol.

### T1.2 Training data path

- [ ] `backend/train_models.py:412`: `data_dir = os.path.join(ROOT_DIR, 'Data')`

- [ ] Sort the file lists and remove or seed the caps (`max_files=500` at line 63, `[:200]` at line 290)

- [ ] `/api/train/` returns an error when the data folder is missing, instead of "Training started"

- **Done when:** `cd backend && python train_models.py --model lgbm` finds the data

### Species-level taxon grouping (part of T1.4)

- [ ] Group resistance-rate tables on species-level taxon instead of strain-level PATRIC IDs

- [ ] Hand the grouping function to Hamza for `promote.py`

- **Done when:** taxon 562 (*E. coli*) matches a rate on `/forecast`

### Start AMRFinderPlus (longest job, start by Wednesday)

- [ ] Install in WSL2 or Colab: `conda install -c bioconda -c conda-forge ncbi-amrfinderplus`, then `amrfinder -u`

- [ ] Test on 5 genomes: `amrfinder -n <genome>.fasta --organism Escherichia -o <genome>.tsv`

- [ ] Map each genus to its `--organism` value (skip the flag for unsupported genera)

- [ ] Start the full run over `Data/fasta_output/` (2,484 genomes)

---

## Week 2: gene matrix (T2.1, data side)

- [ ] **Day 2 of the week: commit a 20-genome sample matrix** so Hamza can write model code

- [ ] Full run finished, failures logged and re-run

- [ ] Build the genome × gene 0/1 matrix, include point mutations (for example `gyrA_S83L`)

- [ ] Save as parquet under `experiments/genome/features/`

- [ ] Check the join: every `Genome ID` in `Data/mapped_output/` has a row

- [ ] Short summary: genes found, genes per genome, most common genes per genus

- [ ] Do **not** commit the per-genome TSVs (add them to `.gitignore`)

- **Done when:** Hamza can load the matrix and join it to labels without help

---

## Week 3: evolution component (T3.1)

- [ ] **Fix &gt;100% bug** in `mutation_timeline.py`: susceptible + intermediate + resistant = 100 every week

- [ ] Seed the random parts, so the same inputs give the same output

- [ ] Remove the strict `xfail` in `amrpredict-lib/tests/test_fasta.py:122` so the test must pass

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
| Hamza | Clean antibiotic names merged | Week 1, day 2 | [x] merged 2026-09-25 (`75a9875`); tell Hamza |
| Hamza | Species-level taxon grouping | Week 1 | \[ \] |
| Hamza | 20-genome sample gene matrix | Week 2, day 2 | \[ \] |
| Hamza | Full gene matrix | End of week 2 | \[ \] |
| Suleman | Canonical antibiotic list for dropdowns | Week 1 | [x] in `SULEMAN_PROGRESS.md` week 1 |
| Suleman | Timeline + RL response format | Day 1 | \[ \] |
| Suleman | Working RL output | Week 4 | \[ \] |

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
| 2026-09-25 | T1.5 name clean-up: 24 new aliases, cleaning v2 (152 → 130 names), same map in `train_models.py`, handbook updated | Commit and push, tell Hamza and Suleman, then T1.2 data path | None |
| 2026-09-25 | Created this tracker | Agree formats with Hamza and Suleman | None |
