# Significance of the main comparisons

Built by `experiments/compare.py --pairs`. DeLong and McNemar treat rows as independent; rows cluster by genome, so the genome bootstrap interval is the one to quote when they disagree.

| A | B | Rows (genomes) | AUC A | AUC B | Diff [DeLong 95% CI] | DeLong p | Genome bootstrap 95% CI | McNemar: only A right / only B right | McNemar p |
|---|---|---|---|---|---|---|---|---|---|
| `B6L_genes_v6` (lab) | `B4L_kmer4_lgbm_v6` | 40,356 (4,481) | 0.9790 | 0.9345 | +0.0445 [+0.0426, +0.0464] | < 0.0001 | [+0.0413, +0.0476] | 4,054 / 1,069 | < 0.0001 |
| `B7L_genes_kmers_v6` (lab) | `B6L_genes_v6` | 40,356 (4,481) | 0.9809 | 0.9790 | +0.0019 [+0.0014, +0.0023] | < 0.0001 | [+0.0012, +0.0026] | 604 / 382 | < 0.0001 |
| `B6L_genes_v6` (lab) | `B6L_base_taxonomy_v6` | 40,356 (4,481) | 0.9790 | 0.8487 | +0.1303 [+0.1269, +0.1337] | < 0.0001 | [+0.1236, +0.1360] | 8,087 / 1,150 | < 0.0001 |
| `B6L_genes_v6` (lab) | `B6L_base_drug_v6` | 40,356 (4,481) | 0.9790 | 0.7147 | +0.2643 [+0.2594, +0.2692] | < 0.0001 | [+0.2589, +0.2698] | 12,533 / 1,300 | < 0.0001 |
| `A2_oof_grouped_v7` | `A_ablation_drug_only_v7` | 1,569,432 (88,100) | 0.7850 | 0.6572 | +0.1277 [+0.1269, +0.1286] | < 0.0001 | [+0.1260, +0.1296] | 332,379 / 67,930 | < 0.0001 |
| `A6_lab_only_v7` | `A6b_lab_only_no_mic_v7` | 129,992 (17,542) | 0.9227 | 0.8400 | +0.0827 [+0.0812, +0.0843] | < 0.0001 | [+0.0797, +0.0857] | 13,325 / 713 | < 0.0001 |
| `A10_monotonic_mic_v7` | `A2_oof_grouped_v7` | 1,569,432 (88,100) | 0.7846 | 0.7850 | -0.0004 [-0.0004, -0.0003] | < 0.0001 | [-0.0004, -0.0003] | 1,479 / 1,398 | 0.1358 |
