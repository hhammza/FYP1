# Progress: Muhammad Ali Mirza (SP23-BCS-082)

**Role:** data and evolution

**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../docs/FYP_Completion_Roadmap.md)

**Started:** 2026-09-25 · **Last updated:** 2026-09-28 (research track added by Ali)

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

**Before each work session (all three of us)**
1. `git pull` first. Commit small and often, and push the same day, so nobody works on stale files.
2. After a pull: `pip install -r experiments/requirements.txt` (it includes the backend requirements).
3. Edit these trackers in a plain text editor (VS Code's normal editor). A visual Markdown editor re-saved them twice and broke them: merged header lines, `[~]` turned into `\[\~\]`, links lost.
4. Someone else's file: add a row to their **Handovers** table only, and say so in the channel.
5. `Data/` and `experiments/cache/` are not in git. Share big files on Drive, not in commits, and keep `Data/` out of OneDrive sync.
6. Read Genome IDs as text (`dtype=str`). As a number, `195.304` and `195.3040` become one genome (the cleaning v5 bug).
7. Backend by hand: `set DEBUG=True` first; Train and Reload need `ADMIN_TOKEN`. `train_models.py` writes to `trained_models/candidates/`; only `experiments/promote.py` changes the model the website serves.
8. Genome-model numbers: quote the **lab** AUC (`Lab AUC` in `RESULTS.md`). BV-BRC's computational labels were predicted from the genome, so all-row scores are partly circular.

---

## Summary

| Week | Dates (planned) | Focus | Status |
| --- | --- | --- | --- |
| 1 | 28 Sep to 2 Oct | Clean names, data path, taxon grouping, start AMRFinderPlus | Done: names, data path, taxon grouping; AMRFinderPlus full run finished 2026-09-26 (2,587 genomes, 0 failures) |
| 2 | 5 Oct to 9 Oct | Gene matrix | Done early 2026-09-26: sample and full gene matrix, join check, summary; two notices open for Hamza (v5 retrain, `mapped_output` IDs) |
| 3 | 12 Oct to 16 Oct | Evolution: fix, sensitivity, calibration; lab-tested genomes for Hamza | Mostly done 2026-09-28: timeline fix, sensitivity analysis, calibration (15 curves) on the site; Dataset 3 = 24,926 complete genomes (22,475 lab-tested), gene matrix and k-mer cache delivered. Open: library xfail (waits on Hamza) |
| 4 | 19 Oct to 23 Oct | RL agent, CTGAN experiment | Started early 2026-09-29 with data: the April export was incomplete, so the complete BV-BRC export was downloaded and became cleaning v6 (7.85 M rows, 87,325 lab-tested genomes); RL and CTGAN not started |
| 5 | 26 Oct to 30 Oct | Report chapters | Not started |
| Research | alongside weeks 4 to 5 | Paper A data audit, rule baseline, collection years ([Research track](#research-track-added-by-ali-2026-09-28); [RESEARCH_PLAN.md](RESEARCH_PLAN.md)) | Not started |

**Files I own:** `Data/`, `experiments/lib/data_prep.py`, `backend/train_models.py`, `experiments/genome/features/` (new), `backend/ml_models/mutation_timeline.py`, `experiments/evolution/` (new). Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: agree the handover formats

- [x] **Gene matrix format** agreed with Hamza: parquet, one row per `Genome ID`, one 0/1 column per gene symbol. *Agreed 2026-09-26 with notes: filter `core` + `Type = AMR`, no plus file (run had no `--plus`)*

- [x] **Timeline + RL response** agreed with Suleman: weekly susceptible, intermediate and resistant fractions, plus a `policy` list (drug used each week). *Agreed 2026-09-26; his three questions answered in formats §4 (tie rule for `rl.best`, requested drug always in `rl.drugs`, `calibration` types)*

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

- [x] Update the dropdown list in `frontend/app.py:ANTIBIOTICS` (Suleman's file): done by Suleman, 47 → 82 drugs

- [x] Suleman's spelling variants, 2026-09-26: 13 aliases (his 6 plus 7 more found in `amr_output/`: hyphen and underscore variants, `cefotaxime/clavulanic acidâ`, `benzylpenicillin`) and `sulfa` dropped, in both maps (checked identical). Their rows all lack a phenotype, so the cleaned table is unchanged: still v4, no retrain needed

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

### Start AMRFinderPlus (longest job, start by Wednesday) `[x]` done 2026-09-26

- [x] Found the local FASTAs are truncated (E. coli about 0.8 of 5 MB; 1000561.3 is 74 KB of 6.3 MB). `download_genomes.py` fetches complete assemblies from the BV-BRC API into `Data/genomes_full/` (gitignored), keeping a file only if its length matches BV-BRC within 1%

- [x] Installed natively on the Mac (no WSL2 or Colab needed): conda env `amrfinder`, AMRFinderPlus 4.2.7, database 2026-08-07.1

- [x] Tested on 5 genomes: P. aeruginosa found `gyrA_T83I`, `blaOXA-904`, `oprD`/`nalC` carbapenem mutations; S. pneumoniae found `pbp1a`/`pbp2b` mutations and `mef(A)`, `msr(D)`

- [x] Species mapped to `--organism` from `backend/taxon_species.csv`, in `run_amrfinder.py`: 2,533 genomes get a flag, 54 run without one (M. tuberculosis, K. michiganensis and 3 small ones). Table in `experiments/genome/README.md`

- [x] Full run over all 2,587 genomes: all downloaded and searched, 0 failures (2026-09-26). The 54 genomes without `--organism` crashed the runner on pandas 3 (NaN organism); fixed in `39b3c11`

- [x] `Data/genomes_full/` and `Data/amrfinder_output/` added to `.gitignore`

> **Note for Hamza:** the K-mer model was trained on the truncated FASTAs. Worth retraining B-track k-mer runs on `Data/genomes_full/` once downloaded.

---

## Week 2: gene matrix (T2.1, data side)

- [x] **Day 2 of the week: commit a 20-genome sample matrix** so Hamza can write model code. *Done early, 2026-09-26: `experiments/genome/features/sample/` (20 genomes, 7 genera, 7 with no core AMR hit; all 20 join to their labels)*

- [x] Full run finished, failures logged and re-run: 0 failures

- [x] Build the genome × gene 0/1 matrix, include point mutations (for example `gyrA_S83L`): 2,587 genomes × 536 symbols (227 point mutations), 914 with no core AMR hit (`53ee20a`)

- [x] Save as parquet under `experiments/genome/features/` (`pyarrow` in the new `experiments/requirements.txt`)

- [x] Check the join: every `Genome ID` in `Data/mapped_output/` has a row: yes, 2,567 of 2,567 (after the trailing-zero fix in `b05d718`). 20 matrix genomes have no mapped rows; their labels were merged into other genomes by the Genome-ID-as-number bug below

- [x] Short summary: genes found, genes per genome, most common genes per genus: `experiments/genome/features/gene_summary.md`, rewritten by `build_gene_matrix.py` on every full build

- [x] Do **not** commit the per-genome TSVs (add them to `.gitignore`): done in week 1

- **Done when:** Hamza can load the matrix and join it to labels without help

---

## Week 3: lab-tested genomes for Hamza (added by Hamza 2026-09-27)

Hamza's genome models (k-mers 0.956, genes 0.981) are tested on only 30 lab-tested genomes, too few to quote. These steps give him ~22,475. The evolution work below does not depend on them, so do it while the download runs.

- [x] Download all 22,475 lab-tested genomes: `select_lab_genomes.py` → `download_genomes.py --genome-list experiments/genome/features/lab_genomes.csv`. *Done 2026-09-28: 24,926 genomes on disk (2,587 original + 22,339 new), 0 failures, about 100 GB*
- [x] AMRFinderPlus on the new genomes (`run_amrfinder.py`, as last time). *Done 2026-09-28: 24,926 searched, 0 errors; 1,139 without `--organism` (no point mutations for them)*
- [x] Rebuild `gene_matrix.parquet` + `gene_info.csv` (+ `gene_summary.md`) with `build_gene_matrix.py` and commit them (small files). *Done 2026-09-28 (`842caac`): 24,926 × 2,733 (1,234 genes, 1,499 point mutations), 1.9 MB. Fixed 22,339 new genomes named genus "unknown"*
- [x] Join check against `Data/amr_output/` (the lab rows), not only `mapped_output/`: the new genomes are not in `mapped_output/`, so the current check reports them as missing even though Hamza's code joins them. *Done 2026-09-28: `build_gene_matrix.py` now checks both and writes it to `gene_summary.md`. 24,844 of 24,926 matrix genomes have labels; all 22,475 lab-tested genomes and all 201,042 lab rows have a matrix row, 0 missing*
- [x] Run `python experiments/genome/kmers.py` on the Mac and share `experiments/cache/kmer6_counts.npz` on Drive. *Built 2026-09-28: 24,926 genomes × 4,096 6-mers, 189 MB, 6 min with 8 workers; uploaded 2026-09-28 to the [genomes Drive folder](https://drive.google.com/drive/folders/1rmt0JKfObvDBlCAs9nZ4Wh57qdDXmHl3) and shared with the team* **Not the genomes:** Hamza's laptop has ~27 GB free. Same for `lineage_clusters.csv` only if Hamza asks (he is reworking `lineage.py` to scale)
- [x] **Early batch:** send the matrix + `kmer6_counts.npz` for whatever is finished, so Hamza can test at scale before the full set. *Not needed: the full set finished within a day*
- [x] Rebuild `/genes` on the new matrix (`export_gene_report.py`). *Done 2026-09-28: 24,926 genomes, gene vs lab result over 22,475 lab-tested genomes; `gene_hits.json` is now 9.8 MB*
- **Done when:** Hamza's runs report a lab AUC on thousands of lab-tested genomes instead of 30

---

## Week 3: evolution component (T3.1)

- [x] **Fix >100% bug** in `mutation_timeline.py`: susceptible + intermediate + resistant = 100 every week. *Done early, 2026-09-26, in the backend: checked on every drug profile at 1 to 52 weeks (20,020 weeks, all exactly 100). Also `simulation`, `seed`, `calibration` fields and `model_used` always `Biological Simulation`, per format §4*

- [x] Seed the random parts, so the same inputs give the same output (`predict(..., seed=42)`, one `numpy` generator)

- [ ] Remove the strict `xfail` in `amrpredict-lib/tests/test_fasta.py:122` so the test must pass. *Waits for Hamza: the library has its own copy in `amrpredict-lib/src/amrpredict/timeline.py`; remove the xfail when he syncs the fix (T2.6)*

- [x] **Sensitivity analysis:** sweep `speed` and `peak` ±30%, plot how `failure_week` moves. *Done 2026-09-28: `experiments/evolution/sensitivity.py`, 8,232 combinations (also weeks asked and GC), checked against the served timeline. Main finding: the midpoint is 0.45 x the weeks asked, so asking for 52 weeks instead of 8 makes the same drug fail 2 to 6 times later; `peak` is a switch at 50% (colistin never fails); speed ±30% moves failure by a median 0.6 weeks. Calibrate a per-drug midpoint and the peak*

- [x] **Literature calibration:** collect 5 to 10 published serial-passage or lab-evolution curves. *Done 2026-09-28: 15 curves fitted by `experiments/evolution/calibrate.py` (median R² 0.91)*

  - [x] Curves collected (table: drug, organism, source, data points). *Sources in `Data/evolution_curves/sources.csv`: Maltas et al. 2025 PLOS Biology lab evolution (5 drugs, E. faecalis, days 0 to 8, 4 replicates) and ECDC EARS-Net carbapenem-resistant K. pneumoniae (10 countries, 2005 to 2024)*

  - [x] Fit logistic parameters per drug (`scipy.optimize.curve_fit`), report RMSE. *Median R² 0.91; parameters with 95% CIs in `results/calibration.csv`. Lab resistance rises within days; hospital plateaus 7% to 66% by country (Greece 66% vs the hand-set imipenem peak 65%). The time scale does not carry over to weeks, so the timeline's weeks stay illustrative and its midpoint should be per drug*

- [x] Work lives in `experiments/evolution/` *(README, `sensitivity.py`, `calibrate.py`, results and figures)*

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

## Research track (added by Ali 2026-09-28)

Alongside weeks 4 and 5, not instead of them. Why and how: [RESEARCH_PLAN.md](RESEARCH_PLAN.md) (Paper A: BV-BRC data audit and deployed-model evaluation; Paper B: genes vs k-mers vs a lookup rule).

- [x] **Complete export and cleaning v6** (found while checking the 597 unfinished April taxa). *Done 2026-09-29: the April export held 2,986,755 of BV-BRC's 17,585,506 records (offset paging, 500,000-row cap). New `download_amr_full.py` fetched all of them (34 min, matches BV-BRC's counts); cleaning v6 = 7,847,110 rows, 649,944 lab rows on 87,325 genomes; species table rebuilt (463 species); runs rebuild on their own export; first audit output is the v5 vs v6 table in experiments/audit/results*

- [x] **Audit script** (`experiments/audit/audit_bvbrc.py`). *Done 2026-09-29 on the complete export: one command, about 2 minutes, results in experiments/audit/results/audit.md and .json*

  Planned scope: every data-defect count from one command on a pinned export date (IDs merged as numbers, trailing zeros lost, strain vs species taxon IDs, drug-name duplicates, rows without a phenotype, missing MIC and testing standard, lab vs computational share, truncated FASTAs)

- [x] **Statistics table** (on v6 instead of v5) for the paper. *Done 2026-09-29: section 8 of the audit, by genus, drug class and drug*

  Planned scope: (rows, genomes, species, drugs, drug classes, resistant share, lab share, by genus); reconcile the 94, 124 and 164 species counts

- [ ] **Prior acknowledgement check:** BV-BRC release notes, docs and GitHub issues for the ID and taxon problems

- [ ] **Gene-lookup rule baseline:** resistant when AMRFinderPlus finds a gene or mutation of the drug's class, scored on the same lab rows and split as Hamza's B6

- [ ] **Collection year and country** for every genome from the BV-BRC genome API, with a coverage report (for the temporal test in RESEARCH_PLAN §5)

- [ ] Week 5 data and methods chapters written so they double as Paper A's data section

- **Done when:** the audit script reproduces every defect count in Paper A, and the rule baseline sits in `registry.csv` next to B6

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
| Hamza | **Cleaning v5**: `Genome ID` is now read as text (it was a float, which merged 3,312 genomes and dropped 36,850 rows, 2.4%). Retrain and promote the forecaster on v5, rerun `evaluate_shipped.py`, and re-run registry configs you quote. Also `promote.py:150` reads `genome_id` without `dtype=str`, so its test-genome count merges IDs the same way | Week 2 | [x] done by Hamza 2026-09-26: `D3_forecaster_deploy` served (0.8039), all 23 registry configs re-run on v5 |
| Hamza | `Data/mapped_output/` Genome IDs fixed (68 genomes had lost a trailing zero, e.g. `1055537.10` → `1055537.1`; `1038927.40` had merged with `1038927.4`). Rerun `experiments/evaluate_shipped.py` for `kmer_metrics.json`, since it groups by these IDs | Week 2 | [x] done by Hamza 2026-09-26: 2,505 genomes join, K-mer AUC 0.6949 |
| Hamza | Complete genomes for the k-mer runs (B0 to B4, k-mer part of B7): `genomes_full.zip` (`Data/genomes_full/`, 11 GB, 2,587 `.fna` files) on Google Drive ([genomes folder](https://drive.google.com/drive/folders/1rmt0JKfObvDBlCAs9nZ4Wh57qdDXmHl3?usp=sharing)); extract inside `Data/`. Not needed for B6, which uses the committed gene matrix | Week 2 | [x] uploaded 2026-09-27, link sent to Hamza. *The zip holds only the original 2,587 genomes. Dataset 3 has since grown to 24,926 (98 GB, on Ali's Mac); Hamza gets those as `kmer6_counts.npz` and the gene matrix instead of the genomes* |
| Hamza | **Lab-tested genomes** (his week 2 request): complete assemblies and AMRFinderPlus for all 22,475 genomes with laboratory AST results (201,042 lab rows, 107 drugs), up from 136. `select_lab_genomes.py` + `download_genomes.py --genome-list`; steps in `experiments/genome/features/README.md` | Week 3 | [x] 2026-09-28: all 24,926 genomes downloaded and searched (0 failures); gene matrix 24,926 × 2,733 (1,499 point mutations) pushed; `kmer6_counts.npz` built for Hamza (Drive, not git) |
| Hamza | **Plasmid-only records (Hamza, 2026-09-29):** 109 of the first 2,587 assemblies are under 500 kb and `manifest.csv` says `genome_status = Plasmid` (e.g. `1001989.12`, 3,319 bp), so they are plasmids, not genomes, but sit in `gene_matrix.parquet` and the k-mer cache as genomes. Please count them in the 24,926, and add a flag column (or drop them) in the gene matrix and k-mer cache so Hamza can re-run B6–B8 without them. Details: `experiments/GENOME_RESULTS.md` §5 | Week 3 | [x] no action needed: Hamza drops them himself with `data.min_genome_bp = 500000` (207 genomes; B6 changes by 0.002) |
| Hamza | **Hamza's request for the lab-tested genomes (2026-09-27):** please send the **k-mer cache** instead of the 90 GB of genomes (his laptop has ~27 GB free): run `python experiments/genome/kmers.py` on the Mac after the download, and share `experiments/cache/kmer6_counts.npz` (a few hundred MB) with the new `gene_matrix.parquet` + `gene_info.csv`. An **early batch** of whatever is finished is welcome. *Answer to your question:* his code reads the labels from `Data/amr_output/` (through `data_prep`) and joins by Genome ID; it does not use `mapped_output/`, so the new genomes join automatically. Your gene-matrix join check compares against `mapped_output/`, so it will report the new genomes as missing rows: harmless for the models, but worth checking against `amr_output/` instead | Week 3 | [x] 2026-09-28: `kmer6_counts.npz` (24,926 genomes, 189 MB) on the genomes Drive folder; the join check now also runs against `amr_output/` (all 22,475 lab-tested genomes join) |
| Hamza | Full gene matrix | End of week 2 | [x] 2026-09-26, `experiments/genome/features/gene_matrix.parquet` + `gene_info.csv` |
| Suleman | Canonical antibiotic list for dropdowns | Week 1 | [x] in `SULEMAN_PROGRESS.md` week 1 |
| Hamza, Suleman | `train_models.py` from the command line no longer writes to the served models: default is `trained_models/candidates/<model>/`, like `/api/train/` | Week 1 | [x] 2026-09-26; checked the served files are byte-identical after a run |
| Hamza | Timeline fix is in the backend only; the library copy (`amrpredict/timeline.py`) still has the >100% bug. Sync it in T2.6, then remove the strict xfail | Week 4 | [ ] |
| Hamza | **Hamza's answers (2026-09-29):** (1) **yes**, sync your timeline fix into `amrpredict/timeline.py` yourself and remove the strict xfail; (2) lab AUC on your genomes, cleaning v6, plasmid-only records excluded: **genes (B6) 0.979 [0.977–0.981] on 40,356 lab test rows from 4,481 genomes; the model trained on 24,719 genomes** (about 200,000 lab rows), k-mers 0.935; unseen genus 0.82–0.94 with genes (`experiments/GENOME_RESULTS.md`); (3) Dataset 2 kept; the k-mer genome model is now on `/predict` and Suleman is asked to mark Dataset 2 superseded | Week 3 | [x] |
| Suleman | Templates still mention CNN-LSTM for the timeline (`mutation_timeline.html:164`, `train.html:142, 147, 154`; `datasets.html` already fixed); the API now says `Biological Simulation` only | Week 2 | [x] in Suleman's tracker 2026-09-26, line numbers updated 2026-09-27; the edit is his |
| Suleman | Timeline + RL response format | Day 1 | [x] agreed 2026-09-26, `progress/formats/README.md` §4 |
| Hamza, Suleman | **Retiring Dataset 2 (partial FASTAs).** Keep `Data/fasta_output/` and `Data/mapped_output/`: the served K-mer model was trained on them and the report compares partial vs complete genomes (K-mer 0.70 vs 0.90). Once Hamza's genome model is on `/predict`, Suleman labels Dataset 2 "superseded by Dataset 3" on `/datasets`. Rows added to both trackers 2026-09-28 | Week 3 (at deploy) | [~] noted |
| Suleman | Working RL output | Week 4 | [ ] |
| Hamza | **Cleaning v6, then v7** (complete BV-BRC export; v7 also stops reading disk-diffusion mm values as MICs): retrain D3 and rerun the quoted configs on it; cleaned table `clean_v7_amr_full_norm.pkl` on the genomes Drive folder (replaces the v6 file). `run.py` already switched (at the team's request) | Week 4 | [x] handed over 2026-09-29, row in Hamza's tracker |
| Hamza, Suleman | **Research track** ([RESEARCH_PLAN.md](RESEARCH_PLAN.md)): the papers need, from Hamza, B6 to B8 on lab rows, the lineage split scaled and applied to the tabular configs, seeds and significance tests, the D3 calibration plot; from Suleman, the repo-public decision, CI and stale README numbers. Rows added to both trackers 2026-09-28 | Weeks 4 to 5 | [~] noted |

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
| 2026-09-29 | Audit script and statistics tables on the complete export (`audit_bvbrc.py`): Genome ID collisions 16,531, 89% of rows under species IDs (the April strain picture was our failed download, claim corrected in RESEARCH_PLAN), computational labels agree with the lab on 90.4% of 463,429 pairs, 8,380 mm rows read as MIC | Collection years; prior-acknowledgement check | None |
| 2026-09-29 | The April AMR export was incomplete (2.99 M of 17.6 M records; no *E. coli*, *S. enterica*, *S. aureus*). Wrote `download_amr_full.py` (record-ID paging, 16 parallel shards, resumable, keeps the Mac awake) and downloaded everything in 34 min. Cleaning v6 on it (7.85 M rows, 87,325 lab-tested genomes), species table for 13,058 taxon IDs, runs rebuild on their own export (D3 split exact), v5 vs v6 comparison, Datasets page, HANDBOOK, README, CHANGES. Cleaned table on Drive for Hamza. Also moved loose root files into `docs/`, `notebooks/`, `scripts/`, and start scripts use relative paths and port 5001 | Audit script and statistics table on v6; collection years | Hamza: retrain on v6. Team: DNA for the 64,850 new lab-tested genomes? |
| 2026-09-28 | Research track added from the literature review: `progress/RESEARCH_PLAN.md` (Paper A audit, Paper B genes vs k-mers vs rule, Paper C library), research tasks in this tracker, rows for Hamza and Suleman. Existing weekly plan unchanged | Audit script and v5 statistics table | Supervisor: venue and scope reply |
| 2026-09-28 | Calibration on the site: `/api/timeline/` fills `calibration` (15 curves, rmse 2.9 points, `parameters_changed: false`) and `/timeline` shows it with its limits; three overstated "calibrated" claims corrected. Constants unchanged, since no source is in weeks. Docs: README §4.3, formats §4, CHANGES.md | RL environment (week 4) | Hamza: library timeline sync before the xfail goes |
| 2026-09-28 | T3.1: sensitivity analysis (8,232 combinations; the weeks asked set the midpoint, so 52 weeks makes the same drug fail 2 to 6 times later) and literature calibration (15 curves: Maltas et al. 2025 lab evolution, 5 drugs; ECDC carbapenem-resistant K. pneumoniae, 10 countries; median R² 0.91). Data in `Data/evolution_curves/` with `sources.csv` | Make the timeline's midpoint per drug and fill its `calibration` field; RL environment (week 4) | None |
| 2026-09-28 | Lab-tested genomes done: 24,926 downloaded (0 failures) and searched by AMRFinderPlus (0 errors), all 22,475 lab-tested genomes included. Gene matrix rebuilt: 24,926 × 2,733 (1,234 genes, 1,499 point mutations), 92.1% with a core AMR gene, `/genes` rebuilt. Fixed the build scripts naming 22,339 new genomes' genus "unknown" (species now from `taxon_species.csv` when there is no `fasta_output/` folder). Built `kmer6_counts.npz` with Hamza's `kmers.py` for him. Also: `run_amrfinder.py` saves every 25 genomes, `progress.sh` auto-restarts and keeps the Mac awake, `start.sh`/`start.bat` start offline | Timeline sensitivity analysis and calibration (T3.1) | None |
| 2026-09-27 | Hamza's week 2 showed only about 30 test genomes have lab results. Listed all 22,475 lab-tested genomes (`select_lab_genomes.py`, round-robin across genera), added `--genome-list` to `download_genomes.py` (tested on 5, resumes), `progress.sh` counts the list, plain-words guide in `features/README.md`. Full download running | AMRFinderPlus on the new genomes, then rebuild the gene matrix | None (about a day of downloading) |
| 2026-09-27 | Uploaded `genomes_full.zip` (complete assemblies, 2,587 genomes) to Google Drive for Hamza's k-mer runs; link in `experiments/genome/README.md`. CNN-LSTM line numbers corrected in my and Suleman's trackers | Sensitivity analysis (T3.1) | None |
| 2026-09-26 | Checked all three trackers after Suleman's T2.4 pull: every week 1 and 2 handover from me is delivered. Marked AMRFinderPlus done; brought Hamza's "From Ali" rows up to date (format agreed, download finished, sample and full matrix) and added the v5 and `mapped_output` notices there | Sensitivity analysis (T3.1) | Hamza to retrain on v5 and rerun `evaluate_shipped.py` |
| 2026-09-26 | Week 2 join check (2,567 of 2,567) and `gene_summary.md`. Found that `data_prep.py` and `train_models.py` read Genome ID as a number: 3,312 genomes merged into others and 36,850 labelled rows (2.4%) dropped | Fixed: cleaning v5 reads Genome ID as text (1,558,494 rows, 131,385 genomes); 888 misattributed rows of 20 genomes corrected in `mapped_output` | Hamza to retrain on v5 | None on my side |
| 2026-09-26 | AMRFinderPlus complete (2,587 genomes, 0 failures); full gene matrix committed; `/genes` rebuilt on every genome. Fixed 68 genomes in `mapped_output` whose Genome ID lost a trailing zero (3,271 rows, 26 files; one had merged with a different genome) and the cause in `fasta_amr_map.py`; every mapped genome now joins the matrix | Sensitivity analysis (T3.1) | None |
| 2026-09-26 | `/genes` page: AMRFinderPlus summary, genes by species, gene vs lab result (lab labels by default), genome lookup; `export_gene_report.py` | Rerun the export when AMRFinderPlus finishes | None |
| 2026-09-26 | Names and label maps centralised in `backend/amr_constants.py` (all files, values unchanged, frontend copy generated and tested); timeline applies the aliases | Full gene matrix; sensitivity analysis | None |
| 2026-09-26 | 13 more antibiotic aliases and `sulfa` dropped (still v4: cleaned table unchanged); dropdown item ticked | Full gene matrix; sensitivity analysis | None |
| 2026-09-26 | Gene-matrix format agreed (§3, with notes) and timeline + RL format proposed (§4). `build_gene_matrix.py` and the 20-genome sample; `pyarrow` in `experiments/requirements.txt`. Trainer defaults to `candidates/`. Timeline partition, seed and honest label. Download and AMRFinderPlus restarted. Seen Hamza's cleaning v4 in `data_prep.py` (54 drug classes) | Full matrix once AMRFinderPlus finishes; Suleman to confirm §4 | None |
| 2026-09-25 | AMRFinderPlus: found truncated FASTAs, download script for full assemblies, installed natively, tested 5 genomes, organism mapping, full run started | Finish the full run, then the 20-genome sample matrix | None (download takes about 3 hours) |
| 2026-09-25 | Species-level taxon grouping: NCBI lookup table, species IDs in trainer and cleaning v3, quote fix, docs | Start AMRFinderPlus | None |
| 2026-09-25 | T1.2 data path: trainer finds `Data/`, reads all files (seeded subset optional), `/api/train/` fails clearly, README updated | Species-level taxon grouping, then AMRFinderPlus | None |
| 2026-09-25 | T1.5 name clean-up: 24 new aliases, cleaning v2 (152 → 130 names), same map in `train_models.py`, handbook updated | T1.2 data path | None |
| 2026-09-25 | Created this tracker | Agree formats with Hamza and Suleman | None |
