# Genome model results (Track B)

Last updated 2026-09-29 (k-mer cache for all 24,926 genomes in; B7 and the lineage check at scale added). Every number here is from `experiments/results/registry.csv`; configs in `experiments/configs/`. Cleaning **v5** (`"source": "amr_output"`), as the research plan's rule for paper numbers asks. Genome models are judged on **lab-confirmed rows**: BV-BRC's computational labels were predicted from the genome, so all-row scores are partly circular.

## 1. Gene features on the lab-tested genomes (B6)

Ali's gene matrix covers 24,926 genomes (AMRFinderPlus, 2,733 genes and point mutations). 24,844 of them have v5 labels: **361,881 rows, 201,042 of them lab-confirmed on 22,475 genomes**. Genome-grouped 80/20 split, LightGBM, threshold 0.5. Raw gene columns are genes carried by at least 50 genomes (356 columns, kept small for 8 GB of RAM); the drug-aware features count every gene.

| Run | Features | All rows AUC | **Lab AUC [95% CI]** (40,553 lab test rows) |
|---|---|---|---|
| `B6L_base_drug` | antibiotic | 0.684 | 0.721 [0.716–0.727] |
| `B6L_nogenes` | antibiotic, drug class, genus | 0.824 | 0.838 [0.832–0.845] |
| `B6L_base_taxonomy` | antibiotic, genus, species | 0.837 | 0.852 [0.847–0.859] |
| `B6L_genes_only` | antibiotic, drug class + genes | 0.977 | **0.976 [0.973–0.978]** |
| `B6L_genes` | antibiotic, drug class, genus + genes | 0.980 | **0.978 [0.976–0.980]** |

- Genes add about **0.13 lab AUC** over the best model without them.
- Genus adds almost nothing once genes are in (0.976 → 0.978): the signal is the genes, not the organism.
- Lab and computational rows now score alike (0.978 vs 0.980), so the result does not rest on the circular labels.
- The earlier B6 (`B6_genes_lgbm`, 0.993 lab) rested on 30 lab genomes; this one on thousands.

## 2. Unseen genus (B8)

Train without one genus, test only on it (`split.strategy = "species_holdout"`), with and without gene features (antibiotic and drug class in both; genus cannot help an unseen genus).

| Genus held out | Lab test rows | Lab AUC without genes | **Lab AUC with genes [95% CI]** |
|---|---|---|---|
| *Klebsiella* | 71,188 | 0.623 | **0.890 [0.887–0.893]** |
| *Neisseria* | 28,199 | 0.745 | **0.844 [0.838–0.849]** |
| *Acinetobacter* | 22,431 | 0.636 | **0.838 [0.831–0.845]** |
| *Salmonella* | 22,332 | 0.535 | **0.945 [0.940–0.951]** |
| *Shigella* | 22,088 | 0.536 | **0.915 [0.909–0.920]** |
| *Pseudomonas* | 8,801 | 0.622 | **0.841 [0.829–0.853]** |
| *Campylobacter* | 7,734 | 0.460 | **0.856 [0.844–0.866]** |

Without genes a model is near chance on an organism it never saw; with genes it reaches 0.84–0.95 on every one. Resistance genes carry **mechanism that transfers across species**. For comparison: the tabular forecaster's *Klebsiella* hold-out (A12) scores 0.60, and k-mers on unseen *E. coli* scored 0.545 (lineage check below). This is the "mechanism vs taxonomy" result.

## 3. Per antibiotic (B6, lab rows)

`B6L_genes` against `B6L_nogenes` on the same lab test rows; drugs with at least 200 lab test rows, weakest first. CIs resample genomes.

| Antibiotic | Lab test rows | Resistant | Lab AUC with genes [95% CI] | Without genes | Gain |
|---|---|---|---|---|---|
| tigecycline | 412 | 21.6% | 0.792 [0.742–0.839] | 0.515 | +0.277 |
| colistin | 498 | 16.5% | 0.903 [0.870–0.939] | 0.694 | +0.209 |
| penicillin | 781 | 52.5% | 0.920 [0.898–0.938] | 0.575 | +0.345 |
| cefepime | 803 | 62.1% | 0.926 [0.907–0.941] | 0.697 | +0.229 |
| piperacillin/tazobactam | 861 | 72.8% | 0.928 [0.906–0.943] | 0.667 | +0.261 |
| amikacin | 1,339 | 34.7% | 0.940 [0.928–0.953] | 0.593 | +0.347 |
| tetracycline | 2,111 | 50.4% | 0.940 [0.930–0.949] | 0.739 | +0.201 |
| cefixime | 583 | 6.5% | 0.946 [0.928–0.966] | 0.497 | +0.449 |
| tobramycin | 1,103 | 61.6% | 0.947 [0.932–0.958] | 0.538 | +0.409 |
| aztreonam | 858 | 81.8% | 0.949 [0.933–0.963] | 0.754 | +0.195 |
| imipenem | 966 | 43.1% | 0.953 [0.932–0.968] | 0.622 | +0.331 |
| cefoxitin | 1,128 | 53.7% | 0.959 [0.949–0.968] | 0.792 | +0.167 |
| ceftazidime | 1,436 | 67.5% | 0.961 [0.951–0.973] | 0.749 | +0.212 |
| streptomycin | 503 | 55.7% | 0.962 [0.943–0.978] | 0.664 | +0.298 |
| ampicillin/sulbactam | 694 | 80.3% | 0.963 [0.949–0.976] | 0.347 | +0.616 |
| nitrofurantoin | 504 | 83.1% | 0.963 [0.938–0.981] | 0.867 | +0.096 |
| meropenem | 1,685 | 36.0% | 0.965 [0.958–0.972] | 0.745 | +0.220 |
| gentamicin | 2,264 | 40.2% | 0.970 [0.964–0.976] | 0.721 | +0.249 |
| ertapenem | 523 | 67.7% | 0.970 [0.954–0.982] | 0.706 | +0.264 |
| levofloxacin | 975 | 68.3% | 0.974 [0.962–0.983] | 0.649 | +0.325 |
| trimethoprim/sulfamethoxazole | 1,425 | 60.8% | 0.977 [0.969–0.985] | 0.770 | +0.207 |
| chloramphenicol | 745 | 26.7% | 0.978 [0.966–0.989] | 0.768 | +0.210 |
| azithromycin | 1,847 | 20.3% | 0.981 [0.973–0.988] | 0.735 | +0.246 |
| cefotaxime | 813 | 65.8% | 0.984 [0.974–0.991] | 0.866 | +0.118 |
| clindamycin | 328 | 26.5% | 0.988 [0.969–0.999] | 0.726 | +0.262 |
| ciprofloxacin | 3,017 | 49.7% | 0.988 [0.984–0.990] | 0.754 | +0.234 |
| trimethoprim | 595 | 60.5% | 0.989 [0.981–0.996] | 0.858 | +0.131 |
| cefazolin | 766 | 88.5% | 0.992 [0.985–0.997] | 0.590 | +0.402 |
| nalidixic acid | 750 | 34.3% | 0.992 [0.985–0.998] | 0.777 | +0.215 |
| cefuroxime | 457 | 92.1% | 0.993 [0.985–0.998] | 0.755 | +0.238 |
| ampicillin | 1,850 | 75.2% | 0.993 [0.988–0.996] | 0.883 | +0.110 |
| amoxicillin/clavulanic acid | 552 | 61.1% | 0.993 [0.988–0.998] | 0.858 | +0.135 |
| spectinomycin | 803 | 10.1% | 0.995 [0.987–0.999] | 0.279 | +0.716 |
| ceftriaxone | 2,542 | 36.2% | 0.996 [0.994–0.998] | 0.942 | +0.054 |
| erythromycin | 406 | 50.5% | 0.996 [0.993–0.999] | 0.883 | +0.113 |

Every drug improves. The weakest, **tigecycline (0.79)** and **colistin (0.90)**, are the ones whose resistance is mostly regulatory (efflux pumps switched on) or chromosomal mutation that AMRFinderPlus does not fully catch, so presence/absence of a gene is a weaker signal for them.

## 4. K-mers, genes + k-mers (B7), and the lineage check at scale

All 24,926 genomes have a k-mer vector now (Ali's `kmer6_counts.npz`), so the k-mer runs use the same 361,881 rows and the same 40,553 lab test rows as B6.

| Run | Model | All rows AUC | **Lab AUC [95% CI]** |
|---|---|---|---|
| `B6L_base_taxonomy` | antibiotic, genus, species | 0.837 | 0.852 [0.847–0.859] |
| `B1L_kmer4_rf` | RandomForest on 4-mers (the shipped design) | 0.867 | 0.860 [0.853–0.867] |
| `B4L_kmer4_lgbm` | LightGBM on 4-mers | 0.933 | 0.928 [0.924–0.933] |
| `B6L_genes` | genes | 0.980 | 0.978 [0.976–0.980] |
| `B7L_genes_kmers` | genes + 4-mers | 0.982 | 0.980 [0.978–0.982] |

- **Genes beat k-mers by 0.05**, and adding k-mers to genes (B7) gains 0.002 with overlapping intervals: no real gain. **The gene model is the one to serve.**
- The k-mer forest is barely above taxonomy at scale (0.860 vs 0.852); on 2,587 genomes it had looked much better (0.904). Boosting is what makes k-mers useful (0.928).

**Lineage check at scale** (`LL_*`; `lineage.py` now clusters per species, 24,926 genomes; lab AUC):

| Held out | Taxonomy | K-mers | Genes |
|---|---|---|---|
| nothing (genome-grouped) | 0.852 | 0.928 | 0.978 |
| near-identical isolates (clone cut) | 0.851 | 0.930 | 0.979 |
| close lineages | 0.849 | 0.925 | 0.977 |
| broad lineages (wide CIs: large lineages move whole) | 0.823 [0.749–0.874] | 0.878 [0.812–0.926] | **0.956 [0.913–0.978]** |

Genes barely move as related bacteria are held out; k-mers lose 0.05 at the broad cut, so part of their signal is lineage. Together with B8 (§2), genes carry resistance mechanism; k-mers mostly carry who the bacterium is.

*Earlier, on the first 2,587 genomes only (30–40 lab genomes, runs `B*`, `L_*` in `RESULTS.md`): k-mers 0.956, genes 0.981 all rows. Superseded by the table above.*

## 5. Known data issue: plasmid records among the "genomes"

109 of the first 2,587 assemblies are under 500 kb, and the download manifest labels them `genome_status = Plasmid`: plasmid-only BV-BRC records, not bacterial genomes. They are in the k-mer and gene runs above. A plasmid carries resistance genes, so its gene features are real, but its k-mer profile is not a genome's. `backend/ml_models/genome_predictor.py` refuses uploads under 100 kb. To do (Ali, data side): count them in the 24,926 and flag or drop them in the gene matrix and k-mer cache; then re-run.

## Reproduce

```bash
python experiments/run.py experiments/configs/B6L_genes.json     # and B6L_*, B8_*
python experiments/report.py --out experiments/RESULTS.md
```
