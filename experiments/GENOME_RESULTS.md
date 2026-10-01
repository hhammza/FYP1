# Genome model results (Track B)

Last updated 2026-09-30. Every number is from `experiments/results/registry.csv` (configs in `experiments/configs/`, run ids below). Data: **cleaning v6** (the complete BV-BRC export), with **plasmid-only records excluded** (`data.min_genome_bp = 500000`), runs named `*_v6`. Genome models are judged on **lab-confirmed rows**: BV-BRC's computational labels were predicted from the genome, so all-row scores are partly circular.

**Rows:** Ali's gene matrix and k-mer cache cover 24,926 complete genomes. With v6 labels and without the 207 plasmid-only records (all under 500 kb, `genome_status = Plasmid`), that is **359,712 rows on 24,719 genomes**, about 200,000 of them lab-confirmed. Genome-grouped 80/20 split: **40,356 lab test rows from 4,481 genomes**. LightGBM unless stated; threshold 0.5 unless stated.

**Cleaning v7 (2026-09-30).** Every run below was repeated on v7 as `*_v7` (same configs). The results are identical: all 28 finished runs give the same lab AUC to 4 decimals. The one exception is the RandomForest (`B1L`), 0.8657 vs 0.8665, which is forest randomness. v7 changes only MIC values, which genome runs don't use. So the v6 tables stand for v7, and the papers can cite either id. (`LL_broad_genes_v7` is still to re-run: Windows blocked a SciPy file for that one run.)

**Seed check.** `B6L_genes_v7` with split seeds 42, 1 and 2: lab AUC **0.9789 ± 0.0004** (sd over seeds), VME 7.6% ± 0.3%, ME 5.7% ± 0.1%. The headline doesn't depend on the split.

**Significance.** Genes vs k-mers on the same 40,356 lab rows: +0.0445, DeLong 95% CI [+0.043, +0.046], p < 0.0001; paired genome bootstrap [+0.041, +0.048]; McNemar 4,054 rows only the gene model gets right vs 1,069 only the k-mer model gets right, p < 0.0001 (`experiments/compare.py`; all pairs in `results/significance.md`). Genes beat taxonomy by +0.130 and the drug-only baseline by +0.264 (both p < 0.0001). Adding k-mers to genes (B7) is a real but small gain: +0.0019, genome bootstrap [+0.0012, +0.0026]. That is statistically clear and practically negligible, so B6 stays the model to serve: it needs only AMRFinderPlus, not k-mer counting as well.

## 1. Gene features (B6) against the baselines

| Run | Features | All rows AUC | **Lab AUC [95% CI]** |
|---|---|---|---|
| `B6L_base_drug_v6` | antibiotic | 0.682 | 0.715 [0.708–0.720] |
| `B6L_nogenes_v6` | antibiotic, drug class, genus | 0.824 | 0.834 [0.828–0.841] |
| `B6L_base_taxonomy_v6` | antibiotic, genus, species | 0.836 | 0.849 [0.842–0.855] |
| `B1L_kmer4_rf_v6` | RandomForest on 4-mers (the old design) | 0.872 | 0.867 [0.861–0.873] |
| `B4L_kmer4_lgbm_v6` | LightGBM on 4-mers | 0.937 | 0.935 [0.931–0.939] |
| `B6L_genes_only_v6` | genes, antibiotic, drug class | 0.980 | 0.977 [0.975–0.979] |
| **`B6L_genes_v6`** | genes, antibiotic, drug class, genus | 0.982 | **0.979 [0.977–0.981]** |
| `B7L_genes_kmers_v6` | genes + 4-mers | 0.983 | 0.981 [0.979–0.982] |

- **Genes add 0.13 lab AUC** over the best model without genome features, and beat k-mers by 0.04.
- **B7 (genes + k-mers) adds 0.002** with overlapping intervals: no real gain, so the simpler gene model (B6) is the best genome model.
- Genus adds almost nothing once genes are in (0.977 → 0.979).
- Lab and computational rows score alike (0.979 vs 0.982), so the result does not rest on circular labels.
- **Plasmid records:** keeping them (`B6L_genes_v6_withplasmids`) gives 0.981 [0.979–0.983]: excluding them changes nothing material, but the cleaner set is the one to quote.
- **v5 vs v6:** the v5 runs (`B6L_*`, `B4L_*`, ... without `_v6`) score within 0.007 of these: the 24,926 genomes gain only 172 lab rows in v6.

## 2. Unseen genus (B8)

Train without one genus, test only on it; antibiotic and drug class in both, with and without gene features.

| Genus held out | Lab test rows | Lab AUC without genes | **Lab AUC with genes [95% CI]** |
|---|---|---|---|
| *Klebsiella* | 71,327 | 0.622 | **0.883 [0.880–0.886]** |
| *Neisseria* | 28,183 | 0.745 | **0.843 [0.837–0.848]** |
| *Acinetobacter* | 22,263 | 0.632 | **0.823 [0.814–0.829]** |
| *Salmonella* | 22,332 | 0.536 | **0.941 [0.934–0.947]** |
| *Shigella* | 22,088 | 0.531 | **0.909 [0.902–0.914]** |
| *Pseudomonas* | 8,801 | 0.619 | **0.838 [0.825–0.851]** |
| *Campylobacter* | 7,734 | 0.459 | **0.850 [0.837–0.861]** |

Without genes a model is near chance on an organism it never saw; with genes it reaches **0.82–0.94** on every one. Resistance genes carry **mechanism that transfers across species**. For comparison, the tabular forecaster's *Klebsiella* hold-out (A12) scores about 0.60.

## 3. Per antibiotic (B6, lab rows)

`B6L_genes_v6` against `B6L_nogenes_v6` on the same lab test rows; drugs with at least 200 lab test rows, weakest first. CIs resample genomes.

| Antibiotic | Lab test rows | Resistant | Lab AUC with genes [95% CI] | Without genes | Gain |
|---|---|---|---|---|---|
| tigecycline | 404 | 26.5% | 0.787 [0.733–0.824] | 0.528 | +0.258 |
| piperacillin/tazobactam | 850 | 72.9% | 0.927 [0.906–0.944] | 0.658 | +0.269 |
| penicillin | 814 | 51.1% | 0.929 [0.909–0.946] | 0.587 | +0.342 |
| aztreonam | 865 | 79.3% | 0.931 [0.912–0.950] | 0.750 | +0.181 |
| colistin | 539 | 17.1% | 0.935 [0.911–0.956] | 0.675 | +0.261 |
| cefixime | 529 | 7.4% | 0.937 [0.912–0.958] | 0.509 | +0.428 |
| amikacin | 1,351 | 33.5% | 0.938 [0.924–0.949] | 0.622 | +0.316 |
| cefepime | 801 | 61.0% | 0.939 [0.922–0.955] | 0.711 | +0.228 |
| tetracycline | 2,084 | 50.9% | 0.945 [0.936–0.954] | 0.753 | +0.193 |
| tobramycin | 1,133 | 60.0% | 0.955 [0.945–0.965] | 0.542 | +0.413 |
| imipenem | 963 | 45.8% | 0.955 [0.943–0.968] | 0.656 | +0.299 |
| cefoxitin | 1,101 | 53.0% | 0.955 [0.944–0.967] | 0.776 | +0.179 |
| ampicillin/sulbactam | 677 | 78.3% | 0.956 [0.940–0.973] | 0.369 | +0.588 |
| clindamycin | 333 | 27.3% | 0.962 [0.927–0.992] | 0.742 | +0.220 |
| streptomycin | 487 | 59.1% | 0.964 [0.944–0.979] | 0.688 | +0.276 |
| ertapenem | 495 | 67.5% | 0.967 [0.949–0.980] | 0.705 | +0.261 |
| meropenem | 1,736 | 36.8% | 0.969 [0.962–0.975] | 0.745 | +0.224 |
| nitrofurantoin | 492 | 80.7% | 0.969 [0.956–0.982] | 0.861 | +0.108 |
| gentamicin | 2,233 | 40.3% | 0.970 [0.964–0.977] | 0.695 | +0.276 |
| ceftazidime | 1,472 | 65.4% | 0.973 [0.965–0.979] | 0.732 | +0.240 |
| trimethoprim/sulfamethoxazole | 1,416 | 61.2% | 0.976 [0.968–0.982] | 0.761 | +0.214 |
| levofloxacin | 972 | 69.5% | 0.981 [0.971–0.988] | 0.686 | +0.295 |
| azithromycin | 1,793 | 20.8% | 0.983 [0.976–0.989] | 0.726 | +0.258 |
| chloramphenicol | 740 | 29.7% | 0.984 [0.975–0.992] | 0.804 | +0.180 |
| trimethoprim | 562 | 60.9% | 0.984 [0.977–0.994] | 0.829 | +0.155 |
| cefazolin | 741 | 86.5% | 0.987 [0.977–0.994] | 0.592 | +0.395 |
| spectinomycin | 823 | 11.2% | 0.988 [0.962–0.999] | 0.968 | +0.020 |
| amoxicillin/clavulanic acid | 545 | 63.1% | 0.989 [0.978–0.995] | 0.840 | +0.149 |
| cefotaxime | 832 | 63.3% | 0.989 [0.982–0.994] | 0.884 | +0.106 |
| ciprofloxacin | 2,989 | 49.4% | 0.990 [0.988–0.993] | 0.753 | +0.237 |
| nalidixic acid | 731 | 35.7% | 0.991 [0.978–0.998] | 0.795 | +0.196 |
| cefuroxime | 481 | 90.2% | 0.992 [0.986–0.998] | 0.719 | +0.274 |
| ampicillin | 1,801 | 77.2% | 0.993 [0.989–0.996] | 0.877 | +0.116 |
| erythromycin | 415 | 52.0% | 0.993 [0.987–0.998] | 0.896 | +0.098 |
| ceftriaxone | 2,456 | 35.6% | 0.998 [0.997–0.999] | 0.909 | +0.089 |

Every drug improves (smallest gain +0.02). The weakest, **tigecycline (0.79)**, is mostly regulatory resistance (efflux pumps switched on), which presence or absence of a gene does not capture well.

## 4. Lineage check (related bacteria held out)

`lineage.py` clusters the 24,926 genomes by 6-mer distance within each species; the `lineage` split keeps whole clusters on one side. Lab AUC:

| Held out | Taxonomy | K-mers | Genes |
|---|---|---|---|
| nothing (genome-grouped) | 0.849 | 0.935 | 0.979 |
| near-identical isolates (clone cut) | 0.851 | 0.933 | 0.979 |
| close lineages | 0.853 | 0.926 | 0.979 |
| broad lineages (wide CIs: large lineages move whole) | 0.816 [0.769–0.855] | 0.900 [0.868–0.926] | **0.965 [0.941–0.979]** |

Genes barely move as related bacteria are held out; k-mers lose 0.035 at the broad cut, so part of their signal is lineage. With B8, this is the "mechanism vs taxonomy" result.

## 5. The model on /predict

**`G_kmer_deploy`**: `B4L_kmer4_lgbm_v6` with the threshold chosen on validation for at most 10% very major error: **lab AUC 0.935 [0.931–0.939]**, threshold 0.43 (all test rows: VME 9.6%, ME 19.5%). Served by `backend/ml_models/genome_predictor.py` (whole genome, k-mers per contig as in training) since 2026-09-29, replacing the old K-mer RandomForest (0.695 on unseen genomes, trained on partial FASTAs). The gene model (B6, 0.979) is better but needs AMRFinderPlus on the server (10–45 s per genome, Ali's measurement), which needs the Docker image; it replaces the k-mer model once that is ready.

## 6. Earlier results

On the first 2,587 genomes only (30–40 lab genomes; runs `B*`, `L_*` in `RESULTS.md`) the numbers were higher and unreliable (k-mers 0.956, genes 0.981 on all rows); on v5 with the 22,475 lab-tested genomes (`B6L_*`, `B8_*`, `B4L_*`, `B7L_*`, `LL_*` without `_v6`) they are within 0.007 of the v6 tables above.

## Reproduce

```bash
python experiments/run.py experiments/configs/B6L_genes_v6.json    # and the other *_v6 configs
python experiments/promote.py G_kmer_deploy --genome              # what /predict serves
python experiments/report.py --out experiments/RESULTS.md
```
