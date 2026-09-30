# Research plan: what we did, what is left, and why

**Added:** 2026-09-28 by Ali

**Last updated:** 2026-09-29

This adds a research track (papers) to the existing plan. Nothing in the weekly plan is dropped: the FYP deliverables (models, website, library, timeline, RL, CTGAN, report) stay as they are in the three trackers. The research tasks sit beside them, and each person's tracker has a row pointing here.

**How to read it:** sections 1 to 3 explain the project and what we found. Sections 4 and 5 explain why we are writing papers and which ones. Sections 6 and 7 list the rules and who does what next. Words that may be new are explained in section 9.

The full literature review (with DOIs and links) is Ali's `PAPER_RESEARCH.md`, kept outside the repo; ask Ali for a copy.

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked

---

## 1. The project in one paragraph

Some bacteria survive antibiotics. This is called antimicrobial resistance (AMR). Today a hospital finds out whether a drug will work with a lab test that takes one to three days. AMRPredict tries to answer that question earlier with machine learning. It has three parts:

| Part | What it does | Page on the website |
| --- | --- | --- |
| Metadata model (LightGBM) | Guesses "resistant or not" from the drug, the species and the MIC value | `/forecast` |
| Genome model | Guesses the same from the bacterium's DNA | `/predict` |
| Timeline | Shows how resistance might grow week by week if one drug keeps being used (a simulation, not a trained model) | `/timeline` |

All data comes from BV-BRC, a free public database of bacteria and their test results.

## 2. What we have done so far

### Data (Ali)

- Cleaned the BV-BRC resistance table: all **17.6 M** records. Cleaning v7 has **7,847,110 rows, 439,542 genomes, 649,944 lab rows on 87,325 genomes**. Along the way we found and fixed real problems in the data (section 3).
- Downloaded the complete DNA of **24,926 genomes**, 22,475 of them with a real lab result. The complete export has 87,325 lab-tested genomes; the DNA of the other 64,850 is not downloaded yet (team decision).
- Ran AMRFinderPlus (a US government tool that finds resistance genes) on every genome. The result is a **gene table of 24,926 genomes x 2,733 genes and mutations**.
- Built the **k-mer file** (`kmer6_counts.npz`): a count of every 6-letter DNA pattern in each genome, for Hamza's models.

### Models (Hamza)

- Rebuilt the metadata model honestly. The served model **D3 scores AUC 0.80** (95% range 0.800 to 0.808) on genomes it never saw.
- Tested many algorithms and data sizes: they all land near 0.82. More data or a fancier algorithm does not help; better features do.
- First genome models: **genes 0.98, k-mers 0.96**. But these were tested on only 30 lab-tested genomes, so they cannot be quoted yet. On a species the model never saw, **genes held 0.71 while k-mers fell to 0.55**.

### Platform (Suleman)

- Removed every hardcoded accuracy number from the website; the pages now read the real numbers from the models.
- Security fixes, antibiotic dropdowns, warnings when a model falls back or does not know a drug.

### Timeline (Ali)

- Fixed a bug where percentages added up to more than 100.
- **Sensitivity analysis:** tested 8,232 input combinations. Main finding: the answer depends too much on how many weeks the user asks for.
- **Calibration:** fitted the timeline's curve to 15 published resistance curves (lab experiments and European hospital data). The curve shape fits well (median R² 0.91), but lab days and hospital years do not convert into the timeline's weeks, so the page now says the weeks are illustrative.

## 3. What we found (the interesting part)

These findings matter more than any single accuracy number, and they are why we can write papers.

1. **The first model looked great but was not.** The model shipped in July scored **0.94** on the genomes it had seen but **0.64** on 128,825 genomes it had not seen. It had trained on only 1.6% of the data, picked in alphabetical file order, and never saw *Klebsiella*.
2. **The database has hidden errors** (complete export, 2026-09-28):
   - Genome IDs like `195.304` and `195.3040` look like numbers; reading them as numbers merges **16,531 genomes** (32,744 IDs collide).
   - 196 spellings of antibiotic names become 126 drugs after clean-up; 10 "drug" names are not drugs (drug classes, `instrument`).
   - 45% of lab records have a measurement but no resistant or susceptible call; 8,380 lab rows give disk sizes in mm where an MIC is expected; testing standards appear as both "CLSI" and "clsi".
   - 4,313 genome and drug pairs have conflicting lab results.
   - Most taxon IDs are strains or serotypes, but 89% of rows sit under a species-rank ID.
3. **Most labels are not real lab results.** About 92% of the cleaned labels were predicted by BV-BRC's own models (SIR XGBoost, AdaBoost); only 8% are lab tests. Where both exist, the prediction disagrees with the lab 9.6% of the time, and for daptomycin (lipopeptides) the predictions say 95% resistant against 11% in the lab. A model trained on them partly learns to copy another model.
4. **The metadata model mostly learns "this species is usually resistant to this drug."** When a whole species is hidden from training, it falls to about 0.60. The DNA models are needed to go beyond that.

## 4. What the published work already covers

- **Predicting resistance from BV-BRC DNA was done in 2016.** Davis et al. 2016 (Sci Rep) and Nguyen et al. 2018 to 2020 did it with k-mers and XGBoost at 88 to 99% accuracy. "We predicted AMR from BV-BRC" is not a paper on its own.
- **"Random test splits make models look better than they are" is already published** several times: Lüftinger et al. 2021, Hu et al. 2024 (Brief Bioinform, 78 PATRIC datasets), Yu et al. 2025 (PLOS Biol) and, closest to us, Kervancı 2026 (Bioinformatics Advances): same database, AUROC 0.93 random, 0.87 clade-aware, 0.81 external. Our 0.94 to 0.64 story has the same shape, so we present it as a confirmation on a real deployed system, not as a discovery.
- **A simple gene lookup is a strong competitor.** In Hu et al. 2024, rule-based ResFinder was the best method on 44 to 50% of datasets when related bacteria were kept apart. Any genome model we publish must be compared with a lookup rule.
- **Nobody has counted BV-BRC's data errors** (finding 2) or measured how much the computer-predicted labels change the results (finding 3). **This is new, and it is our strongest paper.**
- **Nobody has compared resistance genes vs k-mers vs a simple gene lookup on the same BV-BRC lab-tested genomes** with related bacteria kept apart. Our 22,475-genome data makes this possible.
- **Using reinforcement learning to pick antibiotic schedules was published in 2024** (Weaver et al., PNAS). The timeline, RL agent and CTGAN stay as FYP work; at most they make a workshop poster.

## 5. The papers

| Paper | In one line | Main evidence we have | Where |
| --- | --- | --- | --- |
| **A (main)** | What is wrong with BV-BRC's resistance data, and how it made our first model look better than it was | Audit counts on the complete export (cleaning v7); shipped model 0.94 seen vs 0.64 unseen; D3 on v7 0.774 (lab rows 0.908) with CI; lab-only vs computational labels; VME and ME at the chosen threshold | *Microbial Genomics*, fallback *PLOS ONE* |
| **B** | Genes vs k-mers vs a simple gene lookup, on 22,475 lab-tested genomes, tested on lineages and species the model never saw | Gene table 24,926 x 2,733; `kmer6_counts.npz`; first lineage runs (genes 0.708 vs k-mers 0.545 at species level, old 2,505 genomes) | *BMC Bioinformatics* or *PeerJ*, or joined with A |
| **C (later)** | Our `amrpredict` software library and web app | Library, tests, docs | *JOSS*, after about 6 months of public code |

Order: Paper A first (most of its evidence exists), Paper B in parallel as the genome runs finish, Paper C once the repo has been public long enough.

## 6. Rules for any number in a paper

1. Only from cleaning v7 runs: the complete export, Genome ID read as text, mm values not read as MICs.
2. Every headline number has a 95% CI, and every "A beats B" or "no difference" has a DeLong (AUC) or McNemar (threshold) test.
3. Three seeds for headline runs; report mean and sd.
4. Genome models: quote the **lab** AUC only. BV-BRC's computational labels come from its own genome classifiers, so all-row scores are partly circular.
5. In a paper the `/forecast` model is called a metadata model or a population-level prior, not a forecaster, because it predicts resistance now, not in the future. (The FYP title keeps "forecasting"; see section 8.)
6. Methods written against the DOME checklist (Walsh et al. 2021, Nat Methods).

## 7. What we need to do, and why

Weeks follow the existing plan (week 4 = 19 to 23 Oct, week 5 = 26 to 30 Oct). Weeks 6 and later are after the FYP report.

### Ali (data)

- [x] **Audit script** (`experiments/audit/audit_bvbrc.py`), week 4 (done 2026-09-29; truncated FASTAs are counted in `experiments/genome/`, not here): every data-error count from one command on a pinned export date (IDs merged as numbers, trailing zeros lost, strain vs species taxon IDs, drug-name duplicates, rows without a phenotype, missing MIC and testing standard, lab vs computational share, truncated FASTAs). *Why:* a reviewer must be able to check our numbers.
- [x] **Statistics table of the cleaned data** (done 2026-09-29, section 8 of `audit.md`; 247 species), week 4: rows, genomes, species, drugs and drug classes, resistant share, lab share, by genus; reconcile the 94, 124 and 164 species counts (they measure different things). *Why:* every data paper needs one.
- [ ] **Prior acknowledgement check**, week 4: BV-BRC release notes, docs and GitHub issues for the ID and taxon problems. *Why:* so we do not claim something they already announced.
- [ ] **Gene-lookup rule baseline**, week 4: resistant when AMRFinderPlus finds a gene or mutation of the drug's class (`gene_info.csv`), scored on the same lab rows and split as Hamza's B6. *Why:* published work shows this simple rule often wins, so our models must be compared with it.
- [ ] **Collection year and country** for every genome from the BV-BRC genome API, with a coverage report, week 4. *Why:* needed for the forecasting test in section 8.
- [ ] Data and methods chapters of the FYP report, written so they double as Paper A's data section, week 5.
- RL agent and CTGAN stay as planned (FYP deliverables).

### Hamza (models)

Most of these are already in his tracker (week 3 B, week 4 T2.5); they are listed here because the papers depend on them.

- [ ] **B6, B7, B8 on the 22,475 lab-tested genomes**, lab AUC with CI, per drug and per genus, weeks 3 to 4. *Why:* the current 0.98 and 0.96 rest on 30 lab genomes; reviewers will reject that.
- [ ] **Lineage split scaled to 24,926 genomes**, and the same lineage groups used for the tabular A2 and D3 configs, week 4. *Why:* shows whether a model learned biology or just memorised related bacteria; "grouped by genome" is not the same as keeping related bacteria apart.
- [ ] **Three seeds, DeLong and McNemar** for A2, A6, A6b, A10, the drug-only baseline and the best genome run (T2.5), week 4. *Why:* without them we cannot say one model beats another.
- [ ] **Calibration plot for D3** (T2.5), week 4. *Why:* shows whether "70% chance" really means 70%.
- [ ] **Temporal split run** once Ali's collection years are in, week 5 or later. *Why:* the forecasting test in section 8.
- Library v0.2.0 stays as planned (FYP deliverable, and later Paper C).

### Suleman (platform)

- [ ] **Agree on making the repo public** with the team and supervisor, week 4. *Why:* the library paper needs about 6 months of public history.
- [ ] **CI green on the main branch** (already T2.7), week 4. *Why:* reviewers and JOSS check for it.
- [ ] **Stale numbers** in README section 0 and 11.1, endpoint counts, test counts, week 5. *Why:* nothing we publish should contradict our own repo.
- Deployment and the RL panel stay as planned (FYP deliverables).

### Everyone

- [ ] Verify the FDA/CLSI error-rate thresholds (VME at most 1.5%, ME at most 3%) against the primary source before quoting them.
- [ ] Paper A draft from the report chapters, then a bioRxiv preprint on submission, week 6 and later.

### Supervisor (to decide)

- [ ] Which journal, author order, and how to pay the publication fee (Pakistan gets a discount through Research4Life Group B); check the journal's HEC HJRS category.
- [ ] Reply to the scope email (sent 2026-09-25): confirm RL and CTGAN stay as FYP work, not paper material.

## 8. What about "forecasting" in the title?

The roadmap (line 140, section 9.2) flags that the title says forecasting while the models classify. Examiners may ask about it. Our honest answer, and a planned test:

- **Now:** the models predict resistance one to three days before the lab test finishes, and the timeline simulates the weeks after.
- **Temporal validation** (Paper A): train on genomes collected up to a cut-off year and test on later ones. That is a real forecast of future bacteria, and it also checks finding 1 (models fail on data unlike their training data).
- **Resistance-rate trends** (optional, week 6 and later): yearly resistant share per species, drug and region from BV-BRC, checked against the ECDC series already in `Data/evolution_curves/`.

Both depend on how many genomes have a collection year, which Ali's coverage report answers first.

## 9. Words used here

| Word | Meaning |
| --- | --- |
| AUC | A score from 0.5 (coin flip) to 1.0 (perfect) for how well a model separates resistant from susceptible |
| Lab label vs computational label | A real lab test result vs BV-BRC's own computer guess |
| MIC | The lowest drug concentration that stops the bacterium growing; a lab measurement |
| k-mer | A short DNA pattern (here 6 letters); counting them gives a fingerprint of a genome |
| Gene table (gene matrix) | One row per genome, one column per resistance gene or mutation, 1 if found |
| Split | How data is divided into training and test sets; a fair split keeps related bacteria on the same side |
| Lineage / species hold-out | Testing on groups of bacteria the model never saw at all, the hardest fair test |
| Confidence range (CI) | The range the true score probably lies in |
| DeLong / McNemar test | Standard tests for whether one model is really better than another, or just lucky |
| Calibration | Whether predicted probabilities match reality |
| VME / ME | Very major error: calling a resistant bacterium susceptible (dangerous). Major error: the reverse |

## 10. Log

| Date | Who | What |
| --- | --- | --- |
| 2026-09-29 | Ali | Complete BV-BRC export downloaded; cleaning v6; audit script and statistics tables done |
| 2026-09-28 | Ali | Created this plan from the literature review; research rows added to all three trackers; plain-words project overview merged in |
