# Research track: papers from AMRPredict

**Added:** 2026-09-28 by Ali

**Last updated:** 2026-09-28

This adds a research track to the existing plan. Nothing in the weekly plan is dropped: the FYP deliverables (models, website, library, timeline, RL, CTGAN, report) stay as they are in the three trackers. The research tasks below sit beside them, and each person's tracker has a row pointing here.

The full literature review (with DOIs and links) is Ali's `PAPER_RESEARCH.md`, kept outside the repo; ask Ali for a copy. This file keeps only what we need to act on.

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

---

## 1. What the literature says, in short

- **Predicting resistance from BV-BRC genomes is old news.** Davis et al. 2016 (Sci Rep) and Nguyen et al. 2018 to 2020 did it with k-mers and XGBoost at 88 to 99% accuracy. "We predicted AMR from BV-BRC" is not a paper on its own.
- **"Random splits inflate accuracy" is already measured.** Lüftinger et al. 2021, Hu et al. 2024 (Brief Bioinform, 78 PATRIC datasets), Yu et al. 2025 (PLOS Biol) and, closest to us, Kervancı 2026 (Bioinformatics Advances): BV-BRC, AUROC 0.93 random, 0.87 clade-aware, 0.81 external. Our 0.94 to 0.64 story has the same shape, so we present it as a replication on a deployed system, not as a discovery.
- **A simple gene lookup is a strong competitor.** In Hu et al. 2024, rule-based ResFinder was the best method on 44 to 50% of datasets under phylogeny-aware splits. Any genome model we publish must be compared with a lookup rule.
- **Nobody has counted BV-BRC's data defects.** No paper found reports Genome IDs merged by number parsing, strain-level taxon sprawl, drug-name duplicates, truncated genome downloads, or the effect of mixing 87% computational labels with 13% lab labels. This is our strongest novelty.
- **Nobody found compares AMRFinderPlus gene presence with genome k-mers on the same BV-BRC lab-tested genomes under a clade split.** That is our second opening.
- **RL for antibiotic cycling is taken** (Weaver et al. 2024, PNAS). The timeline, RL and CTGAN stay FYP deliverables; at most they make a workshop poster.

## 2. The papers

| Paper | Claim | Main evidence we have | Target venue |
| --- | --- | --- | --- |
| **A (main)** | An audit of BV-BRC AMR data and of a deployed predictor: silent data defects, label provenance, and why a shipped model's AUC did not survive unseen genomes | Cleaning v1 to v5 counts; shipped model 0.94 seen vs 0.64 unseen; D3 0.80 with CI; lab-only vs computational labels; VME and ME at the chosen threshold | *Microbial Genomics*, fallback *PLOS ONE* |
| **B** | AMRFinderPlus genes vs k-mers vs a gene-lookup rule, on 22,475 lab-tested genomes, under lineage and species hold-out | Gene matrix 24,926 x 2,733; `kmer6_counts.npz`; first lineage runs (genes 0.708 vs k-mers 0.545 at species level, old 2,505 genomes) | *BMC Bioinformatics* or *PeerJ*, or folded into A |
| **C (later)** | The `amrpredict` library and web app | Library, tests, docs | *JOSS* (needs about 6 months of public history) |

Order: Paper A first (most of its evidence exists), Paper B in parallel as the genome runs finish, Paper C once the repo has been public long enough.

## 3. Rules for any number we put in a paper

1. Only from cleaning v5 runs (Genome ID read as text).
2. Every headline number has a 95% CI, and every "A beats B" or "no difference" has a DeLong (AUC) or McNemar (threshold) test.
3. Three seeds for headline runs; report mean and sd.
4. Genome models: quote the **lab** AUC only. BV-BRC's computational labels come from its own genome classifiers, so all-row scores are partly circular.
5. Do not call the tabular model a "forecaster" in a paper: it predicts resistance now from drug, species and MIC. Call it a metadata model or a population-level prior. (The FYP title keeps "forecasting"; see 5.)
6. Methods written against the DOME checklist (Walsh et al. 2021, Nat Methods).

## 4. Research tasks by person

Weeks follow the existing plan (week 4 = 19 to 23 Oct, week 5 = 26 to 30 Oct). Weeks 6 and later are after the FYP report.

### Ali (data)

- [ ] **Audit script** (`experiments/audit/audit_bvbrc.py`): every defect count from one command on a pinned export date (IDs merged as numbers, trailing zeros lost, strain vs species taxon IDs, drug-name duplicates, rows without a phenotype, missing MIC and testing standard, lab vs computational share, truncated FASTAs). Week 4
- [ ] **v5 statistics table** for the paper: rows, genomes, species, drugs and drug classes, resistant share, lab share, by genus. Reconcile the 94, 124 and 164 species counts (they measure different things). Week 4
- [ ] **Prior acknowledgement check:** BV-BRC release notes, docs and GitHub issues for the ID and taxon problems, so we do not claim something they already announced. Week 4
- [ ] **Gene-lookup rule baseline** for Paper B: call a genome resistant when AMRFinderPlus finds a gene or mutation of the drug's class (`gene_info.csv`), scored on the same lab rows and split as Hamza's B6. Week 4
- [ ] **Collection year and country** for every genome from the BV-BRC genome API, and a coverage report. Feeds the temporal test in 5. Week 4
- [ ] Data and methods chapters of the FYP report written so they double as Paper A's data section. Week 5

### Hamza (models)

Most of these are already in his tracker (week 3 B, week 4 T2.5); they are listed here because the papers depend on them.

- [ ] B6, B7, B8 on the 22,475 lab-tested genomes, lab AUC with CI, per drug and per genus (Paper B). Week 3 to 4
- [ ] Lineage split scaled to 24,926 genomes, and the same lineage groups used for the tabular A2 and D3 configs, since "grouped by genome" is not "phylogeny-aware" (Papers A and B). Week 4
- [ ] Three seeds, DeLong and McNemar for A2, A6, A6b, A10, the drug-only baseline and the best genome run (T2.5). Week 4
- [ ] Calibration plot for D3 (T2.5). Week 4
- [ ] Temporal split run once Ali's collection years are in (5). Week 5 or later

### Suleman (platform)

- [ ] Agree with the team and supervisor on making the repo public, which starts the JOSS clock for Paper C. Week 4
- [ ] CI green on `main` (already T2.7): reviewers and JOSS check it. Week 4
- [ ] Stale numbers: README section 0 and 11.1, endpoint counts, test counts, so nothing we quote contradicts the repo. Week 5

### Everyone

- [ ] Verify the FDA/CLSI error-rate thresholds (VME at most 1.5%, ME at most 3%) against the primary source before quoting them.
- [ ] Paper A draft from the report chapters, then a bioRxiv preprint on submission. Week 6 and later

### Supervisor (to decide)

- [ ] Venue, author order, APC funding (Research4Life Group B discount), HEC HJRS category of the journal.
- [ ] Scope email reply (sent 2026-09-25): confirm RL and CTGAN stay as FYP deliverables, not paper material.

## 5. Where "forecasting" fits

The roadmap (line 140, section 9.2) flags that the title says forecasting while the models classify. The research track answers this without overclaiming:

1. **Temporal validation** (Paper A): train on genomes collected up to a cut-off year and test on later ones. This is a real forecast of future isolates and a direct test of the distribution shift that Paper A argues for.
2. **Resistance-rate trends** (optional, week 6 and later): yearly resistant share per species, drug and region from BV-BRC, checked against the ECDC series already in `Data/evolution_curves/`.

Both depend on how many genomes have a collection year, which Ali's coverage report answers first.

## 6. Log

| Date | Who | What |
| --- | --- | --- |
| 2026-09-28 | Ali | Created this plan from the literature review; research rows added to all three trackers |
