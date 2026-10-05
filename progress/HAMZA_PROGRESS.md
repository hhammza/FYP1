# Progress: Hamza Afzal (SP23-BCS-086, leader)

**Role:** models
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../docs/FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-30 (v7 forecaster served; library v0.2.0 built; T2.5 tools; temporal split; code review)

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
|---|---|---|---|
| 1 | 28 Sep to 2 Oct | K-mer fix, promote the best model, threshold, calibration, `metrics.json` | Done 2026-09-25 (UI side waits on Suleman) |
| 2 | 5 Oct to 9 Oct | Genome experiments B0 to B4 (k-mers) | Done 2026-09-27 (plus a first B6) |
| 3 | 12 Oct to 16 Oct | Gene-feature models B6/B7, deploy the best genome model | Done 2026-09-29 on v6: B6 0.979, B8 0.82–0.94 on unseen genera, k-mer model live on `/predict` (0.935). 2026-09-30: gene-model path done (`genes_found`, species detection, k-mer fallback); live on the deployed site with Suleman's Docker image |
| 4 | 19 Oct to 23 Oct | Library v0.2.0, statistics and seeds | In progress (started early, 2026-09-30): library 0.2.0 built and tested; DeLong/McNemar, calibration plot and accuracy columns done; seed runs queued |
| 5 | 26 Oct to 30 Oct | Results chapters | Not started |
| Research | alongside weeks 3 to 5 | Lab-genome runs B6 to B8, lineage split for all models, seeds and tests, calibration plot, temporal split ([Research track](#research-track-added-by-ali-2026-09-28), added by Ali) | Not started |

**Files I own:** `experiments/` (except `lib/data_prep.py`, `genome/features/`, `evolution/`), `backend/ml_models/lgbm_predictor.py`, `backend/ml_models/resistance_predictor.py`, `backend/trained_models/`, `amrpredict-lib/`.
Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: leader tasks and handover formats

- [x] **Scope email to the supervisor:** drug design and images descoped, GAN run as an experiment, RL built as a small agent on the simulation. Keep the reply. *Sent 2026-09-25; waiting for the reply (paste its date and any scope changes here)*
- [x] **`metrics.json` format** agreed with Suleman: run id, date, AUC with CI, AUPRC, F1, accuracy, recall, VME, ME, threshold, train rows, test rows, genera, git commit. Give Suleman a sample file. *Sample is the real file: [`progress/formats/lgbm_metrics.sample.json`](formats/lgbm_metrics.sample.json)*
- [x] **Genome prediction response** agreed with Suleman: today's response plus `genes_found: [{gene, drug_class}]`. *Sample: [`progress/formats/genome_response.sample.json`](formats/genome_response.sample.json)*
- [x] **Gene matrix format** agreed with Ali: parquet, one row per `Genome ID`, one 0/1 column per gene. *Proposed with a `gene_info.csv` sidecar and a string `Genome ID` index; agreed by Ali 2026-09-26 with notes in formats §3 (filter `core` + `Type = AMR`, no plus file)*
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
| `D2_forecaster_deploy` (served 2026-09-26, replaced by D3) | **0.8044 [0.8010–0.8080]** harness | D1 on cleaning v4: 54 drugs moved out of drug class `other`. Threshold 0.25: VME 9.0%, ME 53.0%. On the 5,106 test rows of those drugs AUC 0.8648 → 0.8652: the model already knew them by name; the gain is for drugs it never saw (e.g. ceftobiprole), which now get their real class |
| **`D3_forecaster_deploy`** (served) | **0.8039 [0.8001–0.8076]** harness · **0.7997 [0.7959–0.8036]** as `/forecast` scores it | D2 on cleaning v5 (Genome ID as text: 1,558,494 rows, 131,385 genomes, test = 311,712 rows of 26,324 genomes). Threshold 0.23: VME 8.2%, ME 54.6%, recall 91.8%, accuracy 62.3%. The ID bug barely moved the model (D2 0.8044) |
| K-mer RF (unchanged, now actually runs) | 0.695 [0.679–0.714] | 0/100 heuristic fallbacks (was every call); no better than the drug alone (0.703) |

Threshold trade-off on D3's test set, for the report (the threshold itself was chosen on validation):

| Threshold | 0.20 | **0.23** | 0.30 | 0.35 | 0.40 | 0.50 |
|---|---|---|---|---|---|---|
| VME | 7.2% | **8.2%** | 15.7% | 24.5% | 30.9% | 50.4% |
| ME | 56.9% | **54.6%** | 42.5% | 31.9% | 26.1% | 12.3% |

### T1.6 Metrics beside each deployed model `[x]`
- [x] `lgbm_metrics.json` written by `promote.py`; `kmer_metrics.json` written by `evaluate_shipped.py`
- [x] Each predictor's `status` returns its metrics file (`/api/health/` → `models.*.metrics`, plus `default_threshold`)
- **Done when:** Suleman's UI shows numbers read from these files, with nothing typed in by hand. **Met** (Suleman, `d5044a7`): the site shows 0.804 and 0.695 from the metrics files; the old 0.93 survives only in the `/about` sentence explaining why it was wrong

---

## Week 2: genome experiments on k-mers (no gene matrix needed)

New folder `experiments/genome/`, reusing `lib/splits.py` and `lib/metrics.py`.

- [x] **K-mer features from the complete genomes:** `experiments/genome/kmers.py` counts 6-mers once per genome in `Data/genomes_full/` (within contigs, ACGT only; 13 min for 2,587 genomes) and derives k = 3–5 from them. Cached in `experiments/cache/kmer6_counts.npz`
- [x] **Harness:** `data.genomes`, `features.kmers` and `features.genes` in `run.py`; every run now reports **lab-only** metrics (`test_by_label_source`, `Lab AUC` in `RESULTS.md`), because BV-BRC's computational labels were predicted from the genome
- [x] **Baselines on the same rows:** antibiotic only 0.752 (lab 0.561); antibiotic + genus + species 0.823 (lab 0.710)
- [x] **B0** fixed k-mer RF, random split (what was shipped): 0.911 (lab 0.962)
- [x] **B1** same, genome-grouped split (how much was memorisation): 0.904 [0.883–0.920] (lab 0.977): almost none
- [x] **B2** k = 3, 4, 5, 6 (RF): 0.902, 0.904, 0.888, 0.883: k = 4 is best for the forest
- [x] **B4** LightGBM on k-mers: **0.956 [0.942–0.967]** (lab 0.996)
- [x] Load Ali's gene matrix and write the B6 code against it: `experiments/genome/genes.py` (raw 0/1 genes in ≥ 10 genomes + drug-aware features). First run `B6_genes_lgbm`: **0.981 [0.976–0.987]** (lab 0.993) vs 0.813 (lab 0.696) without genes
- **Done when:** B0 to B4 are in the registry with grouped-split AUCs and confidence intervals. **Met**

**Read these numbers with care before quoting them:**
- Only 384 lab test rows from **30 genomes** (84% *Salmonella*). Lab AUCs above 0.95 rest on those 30.
- 97% of rows carry computational labels that BV-BRC derived from the genome, so all-row AUCs of genome models are partly circular (B6 on computational rows: 0.981).
- ~~A genome-grouped split can still put near-identical isolates on both sides.~~ **Checked 2026-09-27 with a lineage-grouped split** (`experiments/genome/lineage.py`, `split.strategy = "lineage"`; 16 `L_*` runs):

  | Split | Taxonomy | K-mers (B4) | Genes (B6) |
  |---|---|---|---|
  | Genome-grouped | 0.823 | 0.956 | 0.981 |
  | Clones held out (398 test lineages) | 0.819 | 0.957 | 0.977 |
  | Close lineages held out (225) | 0.788 | 0.908 | 0.960 |
  | Broad lineages held out (26; 810 lab rows) | 0.724 | 0.950 | 0.990 |
  | *E. coli* held out (species cut: one test cluster, no CI) | 0.500 | 0.545 | 0.708 |

  The k-mer gain is not clone memorisation; part of it is lineage (close cut 0.908) but most survives. K-mers do not transfer to an unseen species, genes partly do: **genes carry mechanism, k-mers composition**. The species row is a first look at B8.
- B-track runs are kept off `/models` (different, smaller dataset); they are in `RESULTS.md`.

---

## Week 3: gene-feature models and deployment

All figures on **cleaning v6**, plasmid-only records excluded (`*_v6` runs; the v5 runs stay in the registry as history). Full tables: [GENOME_RESULTS.md](../experiments/GENOME_RESULTS.md).

### A. Preparation
- [x] **`lineage.py` scaled to 24,926 genomes:** clusters within each species (E. coli and Shigella as one), memory follows the largest species (~0.3 GB) instead of all genomes (~5 GB); same clusters as the all-pairs version on the 2,587 (clone cut identical, others ARI ≥ 0.997). Full run: 99 species, 23,113 / 17,666 / 1,345 / 279 clusters
- [x] **Served model decided (2026-09-29): k-mers now, genes later.** The gene model (lab AUC 0.979) needs AMRFinderPlus on the server (10–45 s per genome) and so a Docker image; the k-mer model (0.935) needs nothing extra. `/predict` switches to genes when Suleman's image is ready. Told Suleman (handover)
- [x] **Served predictor without the 500 kb cut:** `backend/ml_models/genome_predictor.py` reads the whole genome, counts k-mers per contig exactly as `kmers.py` (frequencies equal to 1e-9, predictions equal to the harness to 4 decimals), refuses uploads under 100 kb; same response fields as the old predictor (`gc_content`, `top_kmers`, `ab_list`, `status`) so the page works unchanged
- [x] **Promotion path:** `promote.py <run> --genome` → `backend/trained_models/genome/` with `genome_metrics.json` (lab AUC as headline, threshold rule recorded)
- [x] **Plasmid-only records:** new `data.min_genome_bp` drops assemblies under 500 kb (207 genomes, 2,390 rows). Keeping them changes B6 by 0.002 (0.981 vs 0.979), so nothing depended on them; done here, no flag needed from Ali
- [x] **Memory:** `run.py` stores text columns as categories (`compact()`): v6 takes 0.42 GB instead of 1.5 GB, results unchanged (checked on a v6 run: identical AUC, Brier and confusion counts). Without it the v6 forecaster swapped for 10+ minutes before training

### B. Experiments on the lab-tested genomes (v6, 24,719 genomes, 40,356 lab test rows)
- [x] **B6** genes: **lab AUC 0.979 [0.977–0.981]** vs taxonomy 0.849, antibiotic only 0.715; genes alone 0.977
- [x] **K-mers:** LightGBM 0.935 [0.931–0.939], RandomForest (the old design) 0.867
- [x] **B7** genes + k-mers: 0.981 [0.979–0.982], no real gain over genes → B6 is the best genome model
- [x] **B8** unseen genus, 7 genera: with genes **0.82–0.94**, without 0.46–0.75
- [x] **Lineage check:** clone / close / broad cuts: genes 0.979 / 0.979 / 0.965, k-mers 0.933 / 0.926 / 0.900, taxonomy 0.851 / 0.853 / 0.816
- [x] Per-antibiotic table (B6, 35 drugs): every drug gains (smallest +0.02); weakest tigecycline 0.79
- [x] `genome_runs` in `model_report.json` for Suleman's Genome models section (formats §6)

### C. Deploy
- [x] **`G_kmer_deploy` on `/predict`** (2026-09-29): LightGBM on 4-mers of the complete genome, v6 without plasmids, threshold 0.43 chosen on validation for VME ≤ 10%: **lab AUC 0.935 [0.931–0.939]**, VME 9.6%, ME 19.5%. `backend/api/model_registry.py` serves it when `trained_models/genome/` exists, else the old RandomForest. Checked end to end: API, the `/predict` form, every page
- [x] Page text for the new model: home, `/predict` and `/about` (Suleman's templates, listed in his tracker); `/models` and `/compare` read the model's name from the report
- [x] `evaluate_shipped.py` re-tests the served genome model (lab rows, the run's own split, the promoted booster reproduces the run's scores) and keeps the old RandomForest as `kmer_previous`; `export_report.py` refreshed
- [x] **Gene model on `/predict` with `genes_found`** (format §2). *Done on my side 2026-09-30: `genome_predictor.py` serves the gene model (`trained_models/genome_genes/`) whenever AMRFinderPlus is on the server, else the k-mer model as now. It identifies the upload's species from its 6-mer profile (right species 98.0%, right genus 99.8% of held-out genomes), runs AMRFinderPlus with that `--organism` as training did, builds the gene features (identical to training on 3,600 real genome-drug rows) and returns `genes_found`, `species_detected`; if AMRFinderPlus fails, the k-mer model answers with a `warning`. `promote.py --genome` takes gene runs; deploy model **`G_genes_deploy` promoted 2026-10-01: lab AUC 0.977 [0.975–0.979]** on 40,356 lab rows of 4,481 unseen genomes, threshold 0.58 (VME 10.2%, ME 5.1%; k-mers: 9.6%, 19.5%); served probabilities equal the run's on 400 test rows. 9 tests (`backend/tests/test_gene_model.py`). Live on Railway once Suleman's Docker image is built (it already installs AMRFinderPlus 4.2.7, the training version)*
- [x] Tell Suleman it is deployed, so `/datasets` marks Dataset 2 (partial FASTAs) "Superseded by Dataset 3, kept to reproduce the original K-mer model" (handover row added; message to send) *Done: Suleman labelled Dataset 2 on 2026-09-29*
- **Done when:** `/predict` names the genes it found, and its AUC comes from a lineage- or genome-grouped split on lab rows. *Met 2026-09-30: the gene model names its genes (`genes_found`) wherever AMRFinderPlus runs; lab AUC from a genome-grouped split*

### D. Optional improvements (the suggestions; each is marked in the code)
- [ ] Canonical k-mers (B3): `TODO(Hamza, B3)` in `kmer_matrix()`, `experiments/genome/kmers.py`
- [ ] More key determinants, carbapenem subclasses and the co-trimoxazole "`sul` and `dfr`" rule: `KEY_DETERMINANTS` / `CLASS_TO_AMRFINDER` in `experiments/genome/genes.py`
- [ ] MIC ÷ clinical breakpoint (EUCAST/CLSI) as a forecaster feature: `experiments/lib/encoders.py`, then an A-track config

---

## Week 4: library and statistics

### T2.6 Library v0.2.0
- [x] New models and `metrics.json` in `amrpredict-lib/src/amrpredict/models/`. *2026-09-30: `amrpredict/lgbm.py` ported from the backend predictor (calibration, species-level taxa with a bundled `taxon_species.csv`, the run's threshold and drug-class map, `evidence`); `promote.py D3_forecaster_deploy_v7 --library`. Same probabilities and calls as the backend on the same inputs*
- [x] Library copy of the antibiotic names. *`amrpredict/amr_constants.py`, a copy of the data in `backend/amr_constants.py`; `backend/tests/test_amr_constants.py` fails if it goes stale*
- [x] Sync the timeline fix into `amrpredict/timeline.py` (fractions sum to 100, seeded), then remove the strict `xfail` at `amrpredict-lib/tests/test_fasta.py:122`. *Ali is doing this himself (agreed 2026-09-29)* Done by Ali 2026-09-29 at your request: also a `seed` argument on `simulate_timeline()`, `model_used` always Biological Simulation, `calibration` from the bundled `timeline_calibration.json`; 31 tests pass
- [ ] Backend imports `amrpredict` instead of its own copies in `backend/ml_models/` (agree the switch-over with Suleman, who owns `backend/api/`)
- [x] `amrpredict.status()` returns the metrics (`lgbm_forecasting.metrics`, the promoted run's `lgbm_metrics.json`)
- [x] Version `0.1.0` → `0.2.0` in `amrpredict-lib/pyproject.toml`; `README.md`, `docs/` and `known-issues.md` updated; `forecast()` threshold defaults to the model's own (0.15) instead of 0.40
- [x] Pin `scikit-learn` to the version used for training. *Library: `>=1.6.1,<1.7` (the k-mer pickle is 1.6.1). Backend left at `>=1.3`: its forecaster has no pickled scikit-learn object (calibration is stored as numbers), and the k-mer RandomForest is no longer served*
- [~] `python -m build`, then `twine upload --repository testpypi dist/*`. *Built 2026-09-30 (`twine check` passes); the wheel installs in a clean venv (scikit-learn 1.6.1) and gives the backend's numbers; 34 tests pass. Upload needs Hamza's TestPyPI token*
- **Done when:** `pip install` from TestPyPI works in a clean venv

### T2.5 Evaluation completeness
- [x] Accuracy, recall and specificity columns in `experiments/lib/metrics.py` and `RESULTS.md`. *2026-09-30: `report.py` columns (from the registry, or each run's `metrics.json` for older rows); `run.py` writes them to `registry.csv`*
- [x] Calibration plot for the deployed model. *`experiments/calibration_plot.py` → `experiments/results/figures/calibration_D3_forecaster_deploy_v7.png`: isotonic brings the served forecaster onto the diagonal (Brier 0.193 → 0.160)*
- [x] DeLong test between A2/A10 and alternatives; McNemar at the chosen threshold. *Done 2026-10-01: `experiments/results/significance.md` (7 pairs; DeLong, McNemar, paired genome bootstrap). Genes vs k-mers +0.0445, genes vs taxonomy +0.130, genes vs drug only +0.264, A2 vs drug only +0.128, MIC on lab rows (A6 vs A6b) +0.083: all p < 0.0001. Genes + k-mers vs genes +0.002 (real, negligible). A10 vs A2 −0.0004: McNemar p = 0.14, practically none, so the monotone MIC rule costs nothing*
- [x] 3 seeds for A2, A10 and the best genome run; mean ± sd. *Done 2026-10-01 (split seeds 42, 1, 2; `report.py --seeds`): A2 0.7849 ± 0.0005 (lab 0.9206 ± 0.0018), A10 0.7845 ± 0.0005 (lab 0.9178 ± 0.0017), A6 0.9214 ± 0.0012, A6b 0.8376 ± 0.0024, drug-only 0.6569 ± 0.0004, B6 genes lab 0.9789 ± 0.0004. Every sd is under 0.0025: no result depends on the split*
- **Done when:** every headline number in the report has a CI or a significance test

---

## Week 5: report

- [ ] **Results chapters:** comparison table, ablations, learning curve, species hold-out, threshold trade-off, calibration, genome B-track
- [ ] **Deployed-system evaluation:** shipped vs new re-test
- [ ] Update `CHANGES.md` for my work
- [ ] Final version bump and release of the library once everyone's work is merged

---

## Research track (added by Ali 2026-09-28)

Alongside weeks 3 to 5, not instead of them. What the papers are and why: [RESEARCH_PLAN.md](RESEARCH_PLAN.md). Most items are already in weeks 3 and 4 above; they are listed here because Paper A (BV-BRC data audit and deployed-model evaluation) and Paper B (genes vs k-mers vs a lookup rule) depend on them.

- [ ] **B6, B7, B8 on the 22,475 lab-tested genomes:** lab AUC with CI, per drug and per genus (Paper B). *Why:* the current 0.98 and 0.96 rest on 30 lab genomes

- [x] **Lineage split scaled to 24,926 genomes**, and the same lineage groups applied to the tabular A2 and D3 configs (Papers A and B). *Genome models: Week 3. Tabular, done 2026-10-01 (`LT_*_v7`, the 24,926 genomes with lineage clusters): lab AUC grouped / close / broad: A2 0.968 / 0.967 / 0.961, D3 0.962 / 0.962 / 0.961. Holding related bacteria out costs at most 0.007, so the genome-grouped numbers are not inflated by relatives*

- [x] **Three seeds, DeLong and McNemar** for A2, A6, A6b, A10, the drug-only baseline and the best genome run (T2.5). *Why:* without them we cannot say one model beats another *Done 2026-10-01: see T2.5*

- [x] **Calibration plot for D3** (T2.5): `calibration_plot.py`, served `D3_forecaster_deploy_v7`

- [x] **Temporal split run:** train on genomes collected up to a cut-off year, test on later ones, once Ali's collection years are in (RESEARCH_PLAN section 8). *Why:* a real forecast, and the honest answer to "why is it called forecasting" *Done 2026-09-30 on the tabular model (A6, lab rows, v7): random genome split 0.928 vs trained up to 2012 / 2014 / 2015 and tested after: 0.878 / 0.857 / 0.857; VME roughly doubles. The loss is within-genus drift in particular years (2017–2018: Shigella 0.51, Neisseria 0.74, Salmonella 0.77), not steady decay. [TEMPORAL_RESULTS.md](../experiments/TEMPORAL_RESULTS.md). Next: the same test for the genome models*

- [x] Ali's gene-lookup rule baseline goes in `registry.csv` next to B6 (Ali, `74bccd8`; checked 2026-09-30), on the same rows and split: agree the config with Ali

- **Rules for paper numbers:** cleaning v5 only, lab AUC for genome models, a CI or a significance test on every claim (RESEARCH_PLAN section 6)

- **Done when:** every number Papers A and B quote from the models has a v5 run, a CI and, where it compares, a test

---

## Handovers

| From / to | What | Needed by | Status |
|---|---|---|---|
| From Ali | Clean antibiotic names (T1.5) | Week 1, day 2 | [x] merged 2026-09-25 (`0ba94cd`) |
| From Ali | Trainer data path fixed (T1.2): `train_models.py` finds `Data/`, reads all files by default, `--max-files N` for a seeded subset, `--model-dir` to avoid overwriting `trained_models/`. LightGBM on all files: about 4 min. K-mer on all files: about 1 hour, because GC content is computed per row (worth caching per genome) | Week 1 | [x] merged |
| From Ali | Species-level taxon grouping | Week 1 | [x] 2026-09-25. `backend/taxon_species.csv` maps every Taxon ID to its NCBI species; `train_models.load_species_map()` / `to_species_taxon()`; `species_taxon_id` column in cleaning v3. **To do (Hamza):** in `lgbm_predictor.py` map the user's `taxon_id` through `load_species_map()` before the rate lookup, and ship it with the retrained model (the deployed model is still strain level). Also worth a grouped-split run comparing `Taxon ID` and `species_taxon_id` (random-split AUC fell 0.825 → 0.805, expected) |
| From Ali | FYI: the FASTAs in `Data/fasta_output/` are truncated (E. coli about 0.8 of 5 MB), so the shipped K-mer model and any k-mer run on them saw partial genomes. Complete assemblies are being downloaded to `Data/genomes_full/<genome_id>.fna` (gitignored; see `experiments/genome/README.md`). Consider running B0 to B4 on those | Week 2 | [x] download and AMRFinderPlus finished 2026-09-26: 2,587 genomes, 0 failures. Ali shared the folder as `genomes_full.zip` on 2026-09-27 ([genomes folder](https://drive.google.com/drive/folders/1rmt0JKfObvDBlCAs9nZ4Wh57qdDXmHl3?usp=sharing)): extract inside `Data/`. The `.fna` files are plain FASTA, so look for the `.fna` extension (see `experiments/genome/README.md`). **Update 2026-09-28:** Dataset 3 is now 24,926 complete genomes (all 22,475 lab-tested), 98 GB on Ali's Mac; the Drive zip still holds the first 2,587. You get the rest as `kmer6_counts.npz` (Drive) and `gene_matrix.parquet` (git), no genome download needed |
| From Ali | 20-genome sample gene matrix | Week 2, day 2 | [x] 2026-09-26, `experiments/genome/features/sample/` (20 genomes, 7 genera, all join to their labels) |
| From Ali | Full gene matrix | End of week 2 | [x] 2026-09-26 (`53ee20a`): `experiments/genome/features/gene_matrix.parquet` + `gene_info.csv`, 2,587 genomes × 536 symbols (227 point mutations); every `Genome ID` in `Data/mapped_output/` has a row (2,567 of 2,567); summary in `gene_summary.md` |
| From Ali | **Cleaning v5** (`77bc855`): `Genome ID` is now read as text in `data_prep.py` and `train_models.py`. As a number it merged 3,312 genomes into others and dropped 36,850 labelled rows (2.4%); v5 has 1,558,494 rows and 131,385 genomes. **To do (Hamza):** retrain and promote the forecaster on v5, rerun `evaluate_shipped.py`, re-run the registry configs you quote, and read `genome_id` with `dtype=str` in `promote.py:150` (its test-genome count merges IDs the same way) | Week 2 | [x] 2026-09-26: `D3_forecaster_deploy` trained on v5 and promoted; `evaluate_shipped.py` re-run; `dtype=str` added in `promote.py` **and** in `evaluate_shipped.py` (the AMR CSVs, the mapped CSVs and `predictions.csv` had the same bug, so a re-run alone would have merged the IDs again); every run now records its `clean_version`. **All 23 registry configs re-run on v5** (D1, D2 kept on v3/v4 as history): every AUC within 0.012 of before, overlapping intervals; A2 0.8227, A10 0.8215. `RESULTS.md`, `/models`, HANDBOOK §10–11, EXPERIMENT_PLAN §8b, README §10 and the roadmap updated |
| From Ali | `Data/mapped_output/` Genome IDs fixed (`b05d718`): 68 genomes had lost a trailing zero (e.g. `1055537.10` → `1055537.1`; `1038927.40` had merged with `1038927.4`); 888 misattributed rows of 20 genomes corrected later in `77bc855`. **To do (Hamza):** rerun `experiments/evaluate_shipped.py` so `kmer_metrics.json` uses the fixed IDs | Week 2 | [x] 2026-09-26: re-run with IDs read as text; 2,505 genomes join (was 2,485), unseen-genome AUC 0.6949 (was 0.6951) |
| From Ali | **Two genome datasets, one to retire.** Dataset 2 (`Data/fasta_output/`, 2,587 partial FASTAs, median about 31% of each genome) is what the served K-mer model was trained on; Dataset 3 (`Data/genomes_full/`, 24,926 complete genomes) is what the new genome models use. Keep Dataset 2 and `Data/mapped_output/` until your genome model replaces the K-mer model on `/predict`, so the old model stays reproducible and the report can show 0.70 (partial) vs 0.90 (complete). **When you deploy it, tell Suleman** so `/datasets` can mark Dataset 2 as superseded | Week 3 (at deploy) | [x] Suleman labelled Dataset 2 superseded on 2026-09-29 |
| From Ali | **Research track** (2026-09-28): the papers in [RESEARCH_PLAN.md](RESEARCH_PLAN.md) rely on work already in this tracker: B6 to B8 on the lab-tested genomes (Paper B), and T2.5 seeds, DeLong/McNemar and the D3 calibration plot (Paper A). Two additions: apply the scaled lineage groups to the tabular A2 and D3 configs too ("grouped by genome" is not phylogeny-aware), and a temporal-split run once my collection years are in. I add a gene-lookup rule baseline on B6's rows and split, so it lands in `registry.csv` next to B6. Rule for paper numbers: v5 only, lab AUC for genome models, CI or test on every claim | Weeks 4 to 5 | [ ] |
| From Ali | **Cleaning v6: the complete BV-BRC export** (`9a1e1c8`, 2026-09-29). **Update, same day: use cleaning v7.** The audit found 8,380 lab rows measured in mm (disk-diffusion zone sizes) that were read as MICs; v7 keeps their labels and gives them no MIC. Same 7,847,110 rows and labels; 8,256 fewer MIC values. Take `clean_v7_amr_full_norm.pkl` from Drive instead of the v6 file (`data_prep` looks for the v7 name now). v5 still rebuilds identically, so D3 and the registry are unaffected. `Data/amr_full/` has every BV-BRC record (17,585,506) (checked against BV-BRC's count, 0 duplicates). v6: 7,847,110 rows, 439,542 genomes, 649,944 lab rows on 87,325 genomes, 28.0% resistant (lab rows 33.7%), 247 species. `data_prep.get_clean()` now reads `amr_full` by default. (1) Done by Ali on request: `run.py` now reads the current export (v6) and records the version it actually read; `backfill_bundles.py`, `evaluate_shipped.py` and `export_report.py` rebuild each run on the export its `clean_version` names (`data_prep.source_of`), so D3's split still rebuilds exactly (311,712 test rows). **To do (Hamza):** (2) get the data: run `scripts/bvbrc_download/download_amr_full.py` (about 35 min, 5.3 GB) or take `clean_v6_amr_full_norm.pkl` (1.5 GB) from the [genomes Drive folder](https://drive.google.com/drive/folders/1rmt0JKfObvDBlCAs9nZ4Wh57qdDXmHl3) into `experiments/cache/`; (3) retrain and promote D3 on v6, rerun the registry configs you quote, and re-pick thresholds (the resistant share changed). Genome runs: the 24,926 genomes gain only 172 lab rows, so B-track numbers barely move; the 64,850 new lab-tested genomes need their DNA downloaded first (team decision, about 350 GB) | Week 4 | [~] 2026-09-29: data in `experiments/cache/`; **D4_forecaster_deploy** (D3 on v6) trained and promoted: all rows AUC 0.774 [0.772–0.775], lab rows 0.907, threshold re-picked 0.16 (VME 9.8%, ME 58.4%); genome runs re-done on v6 (`*_v6`). Genome runs on v6 stand for v7 (v7 changes only MIC values, which they do not use). The 23 registry configs: Ali re-runs them on v7 (`*_v7`), so my v6 re-run was stopped. **To do:** take `clean_v7_amr_full_norm.pkl` from Drive; when Ali's `D3_forecaster_deploy_v7` finishes, promote it (`promote.py D3_forecaster_deploy_v7`) in place of D4, then `evaluate_shipped.py` + `export_report.py`. **[x] 2026-09-30:** `D3_forecaster_deploy_v7` promoted (backend and library): AUC 0.774 [0.772–0.775], lab rows 0.908, threshold 0.15 (VME 8.6%, ME 60.8%); re-test through the backend 0.762; split reproduced exactly (1,569,432 rows). Genome runs re-run on v7 as `*_v7` (queued) |
| From Ali | **Collection years are in (2026-09-30), for your temporal split run.** Run `scripts/bvbrc_download/download_genome_meta.py` (about 2 min, no key needed) to get `Data/genome_meta/genome_meta.csv`: one row per Genome ID with `year` (`collection_year`, or else the year in `collection_date`), `isolation_country`, `host_common_name`, `isolation_source`. Join on Genome ID read as text. Coverage in `experiments/audit/results/genome_meta_coverage.md`. On cleaned v7 lab rows, 75,284 of 87,325 genomes have a year; possible cut-offs (train up to the year, test after): 2012 gives 43,439 / 31,845 genomes (252,489 / 318,713 lab rows), 2014 gives 54,204 / 21,080 (345,157 / 226,045), 2015 gives 59,564 / 15,720 (401,605 / 169,597). Genomes without a year stay out of both sides. **Also:** the D3 model on v7, `D3_forecaster_deploy_v7`, has finished (AUC 0.774, lab rows 0.908); its model folder is `D3_forecaster_deploy_v7_model.zip` on the genomes Drive folder: unzip into `experiments/results/`, then `promote.py D3_forecaster_deploy_v7` | Week 4 | [x] 2026-09-30: model promoted (see the v6/v7 row); `genome_meta.csv` taken from Drive; `temporal` split in the harness (`split.cutoff_year`), runs `T1_temporal_{2012,2014,2015}_v7` (A6 on lab rows) and the grouped twin `T0_grouped_withyear_v7` queued |
| From Ali | **Gene-lookup rule baseline is in `registry.csv` next to B6 (2026-09-30, `74bccd8`).** New model type `gene_rule` (`experiments/algorithms/rule_model.py`) learns nothing and reads your `genes.py` drug-aware columns: `B6R_gene_rule_class_v7` uses `gene_class_any`, `B6R_gene_rule_key_v7` uses `key_determinant`. Same data block and split as `B6L_genes_v6`, and I re-ran that as `B6L_genes_v7` for its predictions (lab AUC 0.979 [0.977–0.981], same as yours). On the 40,356 lab test rows the class rule scores 0.711 and your model 0.979 (+0.268 [+0.261, +0.274], paired genome bootstrap); per-drug table and your no-genes runs as context in `experiments/genome/results/rule_vs_model.md`. Please check the configs are the comparison you want. Next I add a subclass-aware rule; your TODO on subclasses in `CLASS_TO_AMRFINDER` would improve the model's features the same way | Week 4 | [x] checked 2026-09-30: same data block and split as `B6L_genes_v6` (40,356 lab rows, 4,481 genomes); it is the comparison we want |
| From Ali | **All 87,325 lab-tested genomes (1 Oct):** Ali downloads the other 64,850 in Colab to Drive (`My Drive/FYP/genomes_lab_v7/`, about 76 GB gzipped, 1 to 2 days), then builds `gene_matrix.parquet` and `kmer6_counts.npz` for all 89,776 genomes in the same formats. Answered in his Handovers: k-mer runs in Colab, per-genome length / contigs / status / assembly accession, same AMRFinderPlus 4.2.7 + database 2026-08-07.1. **To do (Hamza) when his files arrive:** rebuild the lineage clusters (`lineage.py`) and the served gene model's `species_profiles.npz`, retrain B6/B7/B8, `G_genes_deploy` and `G_kmer_deploy` on all lab-tested genomes (in Colab), re-promote, and tell Suleman the new Dataset 3 numbers come from Ali | After Ali's download | [~] 2026-10-01 (Ali): download done (64,812 of 64,850; 38 refused by the length check, `genomes_lab_v7/failures.csv`). k-mers ready: `My Drive/FYP/kmer6_counts_all.npz`, 89,738 genomes × 4,096, 715 MB, same fields as `kmer6_counts.npz` (genome_id, counts, length, gc). Your question, why 6 and not 4: 4-mers are only 256 features and each appears about 20,000 times in a 5 Mb genome, so they show little beyond species and GC; 6 bases are two codons, so 6-mers catch codon-pair usage and short coding patterns with only 4,096 features; 8-mers (65,536) and 10-mers (about 1 million) need sparse or hashed storage; and the old file and models use 6. Even 6-mers mostly capture lineage, so keep the grouped split. Ali can build 4-mers from the same genomes for a comparison if wanted. Gene matrix: AMRFinderPlus running in Colab (Mycobacterium skipped). **2026-10-04 (Hamza):** answered in Ali's Handovers: storing 6-mers is right and no 4-mer build is needed (4-mers are sums of 6-mer counts; the served model and every scaled run use 4-mers made that way); next, in Colab: LightGBM on 4-mers vs 6-mers on lab rows with the lineage split; with the merged gene matrix, retrain B6 and both deploy models and rebuild lineage clusters and species profiles. Asked Ali to search the new *Mycobacterium* genomes as before (without `--organism`) rather than skip them, so the matrix treats them alike |
| To Suleman | Sample `metrics.json` | Day 1 | [x] 2026-09-25: `progress/formats/lgbm_metrics.sample.json` (the real file) |
| To Suleman | Real `metrics.json` for both models | End of week 1 | [x] 2026-09-25: `backend/trained_models/lgbm_metrics.json`, `kmer_metrics.json`; also in `/api/health/` → `models.*.metrics` |
| To Suleman | **Threshold default: the slider and API must start at `default_threshold` (now 0.25), not 0.40.** Hardcoded in `resistance_forecast.html:137-145`, `frontend/app.py:109`, `backend/api/views.py:53`. At 0.40 the calibrated model misses 30.2% of resistant isolates instead of 9.0%. `/predict` likewise: `default_threshold` from `kmer_metrics.json`, 0.5 | Week 1 | [x] 2026-09-26 (`d5044a7`): the slider starts at `metrics.lgbm.threshold` and the API uses the model's own when none is sent, so it follows each promotion (0.25 for D2) |
| To Suleman | New response fields: `/forecast` has `model_run`, `calibrated`; both pages can return `model_used: "Heuristic fallback"` (show a warning); `/predict` has `antibiotic_known` | Week 1 | [x] 2026-09-26: Suleman's T1.3 shows warnings for `Heuristic fallback` and for an antibiotic the k-mer model never saw (CHANGES.md) |
| To Suleman | Genome response with `genes_found` | Week 3 | [x] 2026-09-30: real `genes_found` from the gene model whenever AMRFinderPlus is on the server; format §2 updated (new: `species_detected`, `warning`, `model_run`, `subclass`, `name`); his row in SULEMAN_PROGRESS.md has the steps |
| To Suleman | **Code review (2026-09-30)**, rows in his Handovers: bad input gives 500 instead of 400 in `views.py` (malformed JSON, non-numeric threshold or `n_weeks`, `antibiotic: null`; checked) and `frontend/app.py:265`; stale July pipeline text in `about.html` / `index.html`; per-process rate-limit cache. FYI: the reload bug fixed on my side | Week 4 | [x] Suleman 2026-10-01: bad input is a 400 with a plain message on forecast, predict, timeline and train, `app.py` passes threshold and weeks on as typed (12 tests); `/about`, home and `/datasets` describe today's models. [ ] per-process rate-limit cache (optional, after the demo) |
| From Suleman | **To discuss (2026-10-02): a Genome ID field on `/forecast`?** Your forecaster does not use Genome ID (it is the split key, so as an input it could only memorise known genomes), so not as a model input. Proposed: a "fill from Genome ID" helper (fills genus, species, taxon ID; shows the genome's real lab result; links `/genes`), plus **whether the model saw that genome in training**, which needs your list of the served model's test genomes. Is that list easy to export? FYI: `/forecast`'s genus, species and taxon ID are now linked dropdowns of your model's vocabulary (`backend/api/organisms.py`) | Week 4 | [x] answered 2026-10-04: yes to the helper, never as a model input. `promote.py` now writes each served model's train/test genome lists (`lgbm_split_genomes.json.gz`, `genome*/split_genomes.json.gz`, formats §7), rebuilt from the run and checked against its test-row count; `backend/ml_models/training_genomes.py` `genome_status()` answers train / test / not in data per model; 4 tests. Suleman builds the helper. **Built by Suleman 2026-10-05** (`GET /api/genome/<id>/`): a training genome gets the caution "The forecaster was trained on this genome, so its prediction will look better than on a new genome" |
| To Ali | **Code review (2026-09-30)**, row in his Handovers: `v7_runs.py` uses `pgrep`/`ps` (fails on Windows); `mutation_timeline.py` would report `trained` if a `.pkl` appeared. FYI: library timeline now uses the shared names | Week 4 | [ ] |
| To Ali | **Plasmid-only records in the genome set:** 109 of the first 2,587 assemblies are under 500 kb and the manifest says `genome_status = Plasmid` (e.g. `1001989.12`, 3,319 bp). They are in the gene matrix and k-mer cache as if they were genomes. Please count them in the 24,926 and add a flag (or drop them) in `gene_matrix.parquet` / the k-mer cache, so B6–B8 can be re-run without them. [GENOME_RESULTS.md §5](../experiments/GENOME_RESULTS.md) | Week 3 | [x] 2026-09-29: done here instead: `data.min_genome_bp = 500000` drops them (207 genomes); no flag needed |
| To Suleman | **Which genome model `/predict` will serve** (k-mers: no extra install; genes: AMRFinderPlus in his Docker image). Decide early in Week 3 so the Dockerfile is only built if needed | Week 3, day 1 | [x] 2026-09-29: **k-mers now** (`G_kmer_deploy`, live), **genes later** once the Docker image with AMRFinderPlus is ready: keep AMRFinderPlus in the Dockerfile. AMRFinderPlus takes 10–45 s per genome (Ali), so the site's 30 s wait needs to grow or become a background job |
| To Suleman | A genome-models section on `/models`: B-track runs are excluded from `model_report.json` for now (`export_report.py`), because their dataset and labels differ from the tabular runs. Show them separately, with lab AUC and its n | Week 3 | [x] 2026-09-29: `genome_runs` in `model_report.json`, format in formats §6 (show the `*_v6` runs, lab AUC + `n_lab`) |
| To Ali | **Download + AMRFinderPlus for lab-tested genomes.** Only 30 lab-tested genomes are in the test set today; the export has 22,475 lab-tested genomes (201,042 rows, 107 drugs, 49.5% resistant). A stratified sample of ~5,000 would make the lab AUCs quotable. `kmers.py` and `genes.py` pick new genomes up with no code change | Week 3 | [x] 2026-09-28 (Ali): all 22,475 lab-tested genomes downloaded and searched, 24,926 in total, 0 failures. New `gene_matrix.parquet` / `gene_info.csv` (24,926 × 2,733) pushed; `kmer6_counts.npz` for all 24,926 built, Ali shares it on Drive; put it in `experiments/cache/`
| To Suleman | **The k-mer genome model is live on `/predict`** (2026-09-29): please mark Dataset 2 on `/datasets` "Superseded by Dataset 3, kept to reproduce the original K-mer model" (Ali's wording; don't remove it). FYI, your files I edited for the new model: `backend/api/model_registry.py` (serves `GenomeModelPredictor` when `trained_models/genome/` exists), `index.html`, `resistance_prediction.html`, `about.html` (model text), `models.html`, `compare.html`, `models.js`, `compare.js` (the model's name read from the report). Formats §5 batch CSV checked against `features_frame()`: consistent | Week 3 | [x] Suleman labelled Dataset 2 on 2026-09-29 |
| To Ali | **Answers (2026-09-29):** (1) yes, please sync your timeline fix into `amrpredict/timeline.py` yourself and remove the strict xfail; (2) lab AUC on your genomes (v6, plasmids excluded): **genes 0.979 [0.977–0.981] on 40,356 lab test rows from 4,481 genomes; training used 24,719 genomes** (about 200,000 lab rows); k-mers 0.935; (3) Dataset 2 kept, Suleman told to mark it superseded | Week 3 | [x] |
| To Ali | Proposed gene-matrix format in `progress/formats/README.md` §3 (string `Genome ID` index, zero rows for searched genomes, `gene_info.csv`); `pyarrow` needed | Day 1 | [x] agreed by Ali 2026-09-26, formats §3; `pyarrow` in `experiments/requirements.txt` |
| To supervisor | Scope email | Day 1 | [x] sent 2026-09-25; reply pending |

---

## Already done (before this plan)

From the git history:

- [x] Initial project upload: backend, frontend, notebooks, trained models (May 2026)
- [x] Project setup documentation (2026-09-23)
- [x] Google Drive link for the data (`Data_Drive`, now `docs/DATA_LINKS.md`, 2026-09-24)
- [x] Completion roadmap (`docs/FYP_Completion_Roadmap.md`, 2026-09-25)

---

## Log

Newest first. One line per work session: date, what I did, what is next, anything blocking.

| Date | Done | Next | Blockers |
|---|---|---|---|
| 2026-10-04 | Answered the team's messages in their Handovers. Suleman: gene model pushed (test it in Docker on a `'test'` genome), Dataset 2 stays "Superseded", CI needs no AMRFinderPlus. Ali: storing 6-mers is right, the models use 4-mers summed from them, a 4-vs-6 LightGBM comparison planned in Colab, counts as int32 to save memory, search the new *Mycobacterium* genomes as before | Colab notebook for the 89,738-genome k-mer runs | Ali's merged gene matrix |
| 2026-10-04 | Answered Suleman's Genome ID question: `promote.py` exports the served models' train/test genome lists (forecaster 351,442 / 88,100; genome models 19,804 / 4,915; test list equal to the run's predictions), `training_genomes.py` lookup for the page, formats §7, 4 tests (backend 69 pass). Noticed the genome used for yesterday's `/predict` demo was a training genome: demo on a `'test'` genome from now on | Suleman builds the helper | None |
| 2026-10-01 | Pulled Suleman's 17 commits (bad input → 400, gene-model display, page text, AMRFinderPlus database pin); tests pass. Night jobs were cut by a shutdown; resumed: **gene model `G_genes_deploy` trained and promoted (lab AUC 0.977)** after fixing a `promote.py` indexing bug; `.gitignore` now lets `trained_models/genome_genes/` be committed; **seeds done** (every sd < 0.0025); **significance table** (7 pairs); **lineage check for A2 and D3** (lab AUC drops at most 0.007); `export_report.py` taught the temporal split. Ran the site end to end (forecast, a real 4.96 MB genome on /predict, timeline, all pages) | Push the gene model for Suleman's Docker test and Ali's Mac check | Suleman: Docker build; Ali: one real AMRFinderPlus run |
| 2026-09-30 | **Unblocked Suleman:** gene-model path in `genome_predictor.py` (species from 6-mers 98.0% / genus 99.8%, AMRFinderPlus with `--organism`, features identical to training on 3,600 rows, `genes_found`, `species_detected`, k-mer fallback with `warning`), `promote.py --genome` for gene runs, `G_genes_deploy` config, 9 tests, format §2 and sample updated; answered the library switch-over (after the demo); Dataset 2 ticked. Lineage check configs for A2 and D3 (`LT_*_v7`) | `G_genes_deploy` and `LT_*` train after the seed runs; promote the gene model; push | Suleman: Docker image; Ali: one real AMRFinderPlus run on the Mac |
| 2026-09-30 | **v7 forecaster served** (`D3_forecaster_deploy_v7`, 0.774, lab 0.908, threshold 0.15) and re-tested (0.762 through the backend); **library 0.2.0** (backend loader ported, served model bundled, names shared, metrics in `status()`, scikit-learn pinned; built, 35 tests, clean-venv install checked); **T2.5 tools**: `compare.py` (DeLong, McNemar, genome bootstrap: genes vs k-mers +0.0445, p < 0.0001), `calibration_plot.py`, accuracy/recall/specificity columns, `report.py --seeds`; **temporal split** (`TEMPORAL_RESULTS.md`: 0.928 random vs 0.857–0.878 on later genomes); genome runs on v7 (identical to v6); seed runs. **Code review:** fixed in my files: reload kept the old run's metrics (test added), Windows crash when experiment output is redirected (`experiments/lib/__init__.py`), pandas deprecation in `genome_predictor.py`, random noise in the heuristic fallbacks, library k-mer/timeline names; backend–library parity test added. Others' findings sent as Handovers (Suleman: 500s on bad input, stale page text; Ali: `v7_runs.py` on Windows) | A2/A10 seeds finish → significance table, `RESULTS.md`, `/models` report; TestPyPI upload; next temporal test on the genome models | TestPyPI token (Hamza). Windows Smart App Control blocked scikit-learn 1.9.1 and one SciPy file today (venv now scikit-learn 1.8.0); WSL or Colab if it spreads |
| 2026-09-29 | Week 3 finished on v6 (Hamza's choice: v6 figures, k-mers now): plasmid filter (`min_genome_bp`), memory fix (`compact()`, identical results), 33 genome runs on v6 (B6 0.979, B8 0.82–0.94, k-mers 0.935, lineage check), `G_kmer_deploy` promoted and served on `/predict` (0.935, threshold 0.43), `evaluate_shipped.py` re-tests the genome model, page text updated, `genome_runs` for Suleman, **D4 on v6** promoted (all rows 0.774, lab 0.907, threshold 0.16) | Tabular configs: Ali re-runs them on v7 (my v6 re-run stopped); promote his `D3_forecaster_deploy_v7` when it finishes | Gene model on `/predict` waits on Suleman's Docker |
| 2026-09-29 | Ali's `kmer6_counts.npz` (24,926 genomes) and `clean_v6_amr_full_norm.pkl` in `experiments/cache/`. `lineage.py` at full scale; 12 runs at scale: k-mers LightGBM lab 0.928 (forest 0.860), **B7 genes + k-mers 0.980 vs genes 0.978 (no real gain)**, lineage check: genes hold 0.956 at the broad cut, k-mers 0.878. Recommend serving the gene model | Model decision; deploy with Suleman | Docker with AMRFinderPlus (Suleman) if genes are chosen |
| 2026-09-29 | Week 3 on what was available: `run.py` gene-only runs on the full gene matrix; **B6 on 22,475 lab-tested genomes: lab AUC 0.978** (taxonomy 0.852); **B8 on 7 unseen genera: 0.84–0.95 with genes, 0.46–0.75 without**; per-drug table; `lineage.py` per species (scales to 24,926); `genome_predictor.py` (whole genome, matches training) and `promote.py --genome`; `export_report.py` skips every genome run (the `L_*` runs broke it). Results in `experiments/GENOME_RESULTS.md`. Found 109 plasmid-only records among the genomes | Download the k-mer cache; B7; k-mer and lineage re-runs at scale; choose the served model | k-mer cache download (you); plasmid flag (Ali); model decision (you); API wiring and Docker (Suleman) |
| 2026-09-27 | Updated all three trackers: a shared "before each work session" checklist; my Week 3 split into A (now) / B (needs Ali's files) / C (deploy) / D (suggestions), with the model-choice decision and the 500 kb cap on `/predict`; Week 4 library items for the names and the timeline sync; Ali's lab-genome steps; Suleman's genome section, Docker dependency and batch-format note | Week 3 part A | None |
| 2026-09-27 | Answered Ali: labels come from `Data/amr_output/` (joined by Genome ID), not `mapped_output/`, so the lab-tested genomes join once they are in the k-mer cache and gene matrix. Asked for the k-mer cache + gene matrix instead of 90 GB of genomes, and an early batch | Rework `lineage.py` for ~25k genomes; test on the early batch | Disk: ~27 GB free. The project is inside OneDrive: keep `Data/` out of OneDrive sync |
| 2026-09-27 | Lineage check: `lineage.py` clusters the 2,587 genomes by 6-mer cosine distance at 4 cuts; `lineage` split in `splits.py`/`run.py` (inner folds and CIs grouped by lineage too); 16 runs. K-mer and gene gains survive held-out lineages; with *E. coli* held out k-mers collapse (0.545), genes hold 0.708 | B7, B8 proper (several held-out species with CIs) | Species cut gives a single test cluster, so no CI |
| 2026-09-27 | Week 2: k-mer cache from complete genomes, genome/gene support and lab-only metrics in the harness, 12 B-track runs (baselines, B0, B1, B2 ×3, B4, B6 + its baseline). K-mers on complete genomes beat taxonomy (B4 0.956 vs 0.823), genes more so (B6 0.981), but lab evidence is 30 genomes | Ask Ali for lab genomes; lineage-grouped split; B7, B8 | Lab test set too small to quote; possible lineage leakage |
| 2026-09-26 | Registry re-run on v5 finished: 23 runs, no failures. Two conclusions changed: the learning curve flattens after ~100 k rows, not 50 k (`LC_50k` 0.8157 → 0.8038); `A12_species_holdout` error rates swapped at 0.40 (VME 11% → 52%), so quote only its AUC (0.6041). Docs and CHANGES.md updated | Week 2: B0–B4 on `Data/genomes_full/`, B6 on the gene matrix | None |
| 2026-09-26 | Week 1 closed on cleaning v5 (Ali's `77bc855`, `b05d718`): `dtype=str` for Genome ID in `promote.py` and `evaluate_shipped.py`; runs record `clean_version`; trained, promoted and re-tested `D3_forecaster_deploy` (0.8039, served 0.7997, threshold 0.23); K-mer re-test on fixed IDs (0.6949); all 23 registry configs re-run on v5 (D1, D2 kept as the v3/v4 history of what was served). Installed xgboost and catboost; pyarrow reads the full gene matrix | Week 2: B0–B4 on `Data/genomes_full/`, B6 on the gene matrix | Windows Smart App Control briefly blocked pyarrow and a SciPy DLL right after `pip install`; both import fine a minute later. If it recurs, wait and retry |
| 2026-09-26 | T1.6 met: Suleman's UI reads every score from the metrics files and the threshold from the model; checked it follows D2 (0.25), not a typed-in 0.24. `/train` now writes to `trained_models/candidates/`; the command-line trainer still defaults to `trained_models/` (Ali to fix) | Don't run `train_models.py` without `--model-dir` | None |
| 2026-09-26 | Drug classes for 54 drugs that were `other` (cleaning v4, `data_prep.py` and `train_models.py`; `lgbm_predictor.py` now imports the trainer's map instead of its own copy). Every dropdown drug has a class. Trained and promoted `D2_forecaster_deploy`, re-tested, report refreshed | Same as below | `data_prep.py` is Ali's file: tell him about v4 |
| 2026-09-25 | Day 1 formats written (`progress/formats/`); scope email drafted. Week 1: k-mer scaler fix; antibiotic aliases at prediction time (`ml_models/common.py`); harness gains `taxon_level`, calibration and accuracy; ran A10 (v3), A10s, D1; `promote.py`; D1 promoted; July genus-rate lookup bug fixed in passing (table stored `Escherichia`, lookup used `escherichia`); `evaluate_shipped.py` re-tests promoted models through the backend's own `features_frame()` and writes `kmer_metrics.json`; `export_report.py` keeps ROC curves whose `predictions.csv` is missing | Send scope email; Suleman: threshold default + metrics in UI; Ali: confirm gene-matrix format; Week 2 k-mer runs | Library not updated (T2.6): promoting with `--library` before its loader applies calibration would make `amrpredict.forecast()` disagree with the web app. The other 21 registry rows are still cleaning v1 |
| 2026-09-25 | Tracker created | Scope email, agree formats | None |
