# Experiment results

| Run | Data | Split | Encoding | Model | AUC-ROC [95% CI] | Lab AUC (n) | AUPRC | F1 | VME | ME | Brier | Thr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `A6_lab_only` | v5 | grouped | oof | lightgbm | 0.9675 [0.9647-0.9704] | n/a | 0.9692 | 0.8858 | 8.4% | 14.9% | 0.0722 | 0.40 |
| `L_broad_genes` | v5 | lineage | none | lightgbm | 0.9898 [0.9032-0.9935] | 0.9949 (810) | 0.9478 | 0.8866 | 6.8% | 2.8% | 0.0284 | 0.50 |
| `B6_genes_lgbm` | v5 | grouped | none | lightgbm | 0.9812 [0.9758-0.9866] | 0.9930 (384) | 0.9393 | 0.8588 | 10.4% | 3.7% | 0.0394 | 0.50 |
| `L_clone_genes` | v5 | lineage | none | lightgbm | 0.9770 [0.9693-0.9829] | 0.9956 (363) | 0.9277 | 0.8541 | 12.7% | 3.4% | 0.0409 | 0.50 |
| `L_close_genes` | v5 | lineage | none | lightgbm | 0.9597 [0.9219-0.9838] | 0.9931 (347) | 0.8822 | 0.8407 | 19.0% | 2.3% | 0.0539 | 0.50 |
| `A6b_lab_only_no_mic` | v5 | grouped | oof | lightgbm | 0.8764 [0.8706-0.8819] | n/a | 0.8693 | 0.7939 | 9.4% | 36.8% | 0.1428 | 0.40 |
| `L_clone_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9569 [0.9395-0.9670] | 0.9928 (363) | 0.8631 | 0.7860 | 24.4% | 3.3% | 0.0524 | 0.50 |
| `B4_kmer4_lgbm` | v5 | grouped | none | lightgbm | 0.9559 [0.9422-0.9667] | 0.9962 (384) | 0.8614 | 0.7854 | 21.3% | 4.3% | 0.0537 | 0.50 |
| `L_broad_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9495 [0.8204-0.9508] | 0.9762 (810) | 0.7966 | 0.7408 | 25.9% | 4.2% | 0.0543 | 0.50 |
| `B2_kmer3_rf` | v5 | grouped | none | random_forest | 0.9021 [0.8796-0.9214] | 0.9497 (384) | 0.7428 | 0.6791 | 30.4% | 7.0% | 0.1036 | 0.50 |
| `A0_baseline_leaky` | v5 | random | leaky | lightgbm | 0.8244 [0.8226-0.8265] | n/a | 0.7402 | 0.6639 | 9.3% | 47.3% | 0.1712 | 0.40 |
| `A1_oof_random` | v5 | random | oof | lightgbm | 0.8225 [0.8208-0.8246] | n/a | 0.7379 | 0.6617 | 8.9% | 48.3% | 0.1720 | 0.40 |
| `A2_oof_grouped` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | n/a | 0.7373 | 0.6638 | 9.3% | 47.4% | 0.1718 | 0.40 |
| `A9_threshold_f1` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | n/a | 0.7373 | 0.6704 | 20.1% | 33.5% | 0.1718 | 0.47 |
| `LC_800k` | v5 | grouped | oof | lightgbm | 0.8205 [0.8173-0.8240] | n/a | 0.7370 | 0.6618 | 9.8% | 47.3% | 0.1726 | 0.40 |
| `A2b_no_encoding` | v5 | grouped | none | lightgbm | 0.8214 [0.8181-0.8250] | n/a | 0.7351 | 0.6626 | 8.9% | 48.1% | 0.1722 | 0.40 |
| `A10_monotonic_mic` | v5 | grouped | oof | lightgbm | 0.8215 [0.8183-0.8249] | n/a | 0.7346 | 0.6652 | 10.7% | 45.4% | 0.1725 | 0.40 |
| `LC_200k` | v5 | grouped | oof | lightgbm | 0.8174 [0.8112-0.8223] | n/a | 0.7325 | 0.6604 | 9.3% | 48.3% | 0.1737 | 0.40 |
| `A3b_lgbm_same_sample` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | n/a | 0.7310 | 0.6658 | 21.1% | 33.5% | 0.1738 | 0.46 |
| `LC_400k` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | n/a | 0.7310 | 0.6623 | 11.1% | 45.8% | 0.1738 | 0.40 |
| `A5_xgboost` | v5 | grouped | oof | xgboost | 0.8167 [0.8125-0.8207] | n/a | 0.7307 | 0.6640 | 21.8% | 33.0% | 0.1744 | 0.47 |
| `LC_100k` | v5 | grouped | oof | lightgbm | 0.8158 [0.8096-0.8217] | n/a | 0.7303 | 0.6612 | 11.0% | 46.2% | 0.1754 | 0.40 |
| `A5b_catboost` | v5 | grouped | oof | catboost | 0.8170 [0.8125-0.8211] | n/a | 0.7303 | 0.6660 | 19.9% | 34.8% | 0.1741 | 0.47 |
| `A5c_catboost_native` | v5 | grouped | none | catboost | 0.8155 [0.8111-0.8197] | n/a | 0.7282 | 0.6644 | 20.5% | 34.5% | 0.1746 | 0.47 |
| `A4_random_forest` | v5 | grouped | oof | random_forest | 0.8140 [0.8097-0.8183] | n/a | 0.7236 | 0.6630 | 21.9% | 33.1% | 0.1754 | 0.47 |
| `B1_kmer4_rf_grouped` | v5 | grouped | none | random_forest | 0.9037 [0.8828-0.9204] | 0.9765 (384) | 0.7225 | 0.6351 | 31.1% | 9.5% | 0.1075 | 0.50 |
| `A10s_monotonic_species` | v5 | grouped | oof | lightgbm | 0.8040 [0.8002-0.8077] | n/a | 0.7176 | 0.6493 | 13.0% | 46.4% | 0.1795 | 0.40 |
| `B0_kmer4_rf_random` | v5 | random | none | random_forest | 0.9107 [0.9014-0.9187] | 0.9624 (361) | 0.7168 | 0.6008 | 17.4% | 18.2% | 0.1154 | 0.50 |
| `D2_forecaster_deploy` | v4 | grouped | oof | lightgbm | 0.8044 [0.8010-0.8080] | n/a | 0.7163 | 0.6419 | 9.0% | 53.0% | 0.1678 | 0.25 |
| `D1_forecaster_deploy` | v3 | grouped | oof | lightgbm | 0.8043 [0.8010-0.8080] | n/a | 0.7161 | 0.6420 | 9.1% | 52.9% | 0.1678 | 0.24 |
| `D3_forecaster_deploy` | v5 | grouped | oof | lightgbm | 0.8039 [0.8001-0.8076] | n/a | 0.7135 | 0.6397 | 8.2% | 54.6% | 0.1683 | 0.23 |
| `LC_50k` | v5 | grouped | oof | lightgbm | 0.8038 [0.7951-0.8148] | n/a | 0.7110 | 0.6525 | 10.1% | 49.6% | 0.1800 | 0.40 |
| `A3_logistic` | v5 | grouped | oof | logistic | 0.7979 [0.7935-0.8021] | n/a | 0.7013 | 0.6542 | 18.4% | 39.0% | 0.1828 | 0.41 |
| `L_close_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9083 [0.8676-0.9346] | 0.9455 (347) | 0.6962 | 0.6438 | 38.7% | 5.7% | 0.0817 | 0.50 |
| `A_ablation_no_mic` | v5 | grouped | oof | lightgbm | 0.8030 [0.8001-0.8069] | n/a | 0.6953 | 0.6517 | 9.1% | 50.5% | 0.1822 | 0.40 |
| `B2_kmer5_rf` | v5 | grouped | none | random_forest | 0.8875 [0.8652-0.9045] | 0.9640 (384) | 0.6749 | 0.5926 | 35.6% | 10.5% | 0.1158 | 0.50 |
| `B2_kmer6_rf` | v5 | grouped | none | random_forest | 0.8829 [0.8625-0.9010] | 0.9566 (384) | 0.6574 | 0.5791 | 37.7% | 10.4% | 0.1189 | 0.50 |
| `A12_species_holdout` | v5 | species_holdout | oof | lightgbm | 0.6041 [0.6012-0.6076] | n/a | 0.6070 | 0.4999 | 51.7% | 35.7% | 0.2253 | 0.40 |
| `B_base_taxonomy` | v5 | grouped | none | lightgbm | 0.8229 [0.8037-0.8442] | 0.7104 (384) | 0.5491 | 0.4823 | 26.7% | 25.8% | 0.1631 | 0.50 |
| `B_base_taxonomy_rf` | v5 | grouped | none | random_forest | 0.8214 [0.8013-0.8422] | 0.7146 (384) | 0.5485 | 0.5024 | 42.9% | 13.8% | 0.1664 | 0.50 |
| `L_clone_nogenes` | v5 | lineage | none | lightgbm | 0.8098 [0.7660-0.8449] | 0.6889 (363) | 0.5464 | 0.4820 | 32.2% | 22.3% | 0.1653 | 0.50 |
| `L_clone_taxonomy` | v5 | lineage | none | lightgbm | 0.8185 [0.7770-0.8508] | 0.7019 (363) | 0.5457 | 0.4717 | 31.4% | 24.0% | 0.1635 | 0.50 |
| `B6_base_nogenes` | v5 | grouped | none | lightgbm | 0.8132 [0.7950-0.8339] | 0.6963 (384) | 0.5429 | 0.4844 | 29.3% | 23.9% | 0.1658 | 0.50 |
| `A_ablation_drug_only` | v5 | grouped | none | lightgbm | 0.6535 [0.6510-0.6566] | n/a | 0.4852 | 0.5744 | 10.0% | 70.8% | 0.2308 | 0.40 |
| `L_close_taxonomy` | v5 | lineage | none | lightgbm | 0.7878 [0.7210-0.8534] | 0.6448 (347) | 0.4471 | 0.4524 | 33.4% | 24.8% | 0.1611 | 0.50 |
| `B_base_drug` | v5 | grouped | none | lightgbm | 0.7521 [0.7321-0.7736] | 0.5611 (384) | 0.4425 | 0.4218 | 38.8% | 25.4% | 0.1798 | 0.50 |
| `B_base_drug_rf` | v5 | grouped | none | random_forest | 0.7471 [0.7283-0.7675] | 0.5668 (384) | 0.4363 | 0.4195 | 55.5% | 13.3% | 0.2041 | 0.50 |
| `L_close_nogenes` | v5 | lineage | none | lightgbm | 0.7704 [0.7115-0.8311] | 0.6671 (347) | 0.4235 | 0.4618 | 34.7% | 22.8% | 0.1650 | 0.50 |
| `L_broad_nogenes` | v5 | lineage | none | lightgbm | 0.7152 [0.6897-0.8053] | 0.6863 (810) | 0.3534 | 0.3477 | 67.1% | 9.1% | 0.1455 | 0.50 |
| `L_broad_taxonomy` | v5 | lineage | none | lightgbm | 0.7241 [0.5979-0.7350] | 0.7137 (810) | 0.3248 | 0.0000 | 100.0% | 0.0% | 0.1272 | 0.50 |
| `L_species_genes` | v5 | lineage | none | lightgbm | 0.7080 [0.7080-0.7080] | n/a | 0.2925 | 0.3326 | 41.2% | 28.2% | 0.2051 | 0.50 |
| `L_species_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.5446 [0.5446-0.5446] | n/a | 0.1718 | 0.2575 | 61.5% | 23.3% | 0.1839 | 0.50 |
| `L_species_nogenes` | v5 | lineage | none | lightgbm | 0.5440 [0.5440-0.5440] | n/a | 0.1622 | 0.2317 | 61.9% | 27.7% | 0.2068 | 0.50 |
| `L_species_taxonomy` | v5 | lineage | none | lightgbm | 0.5000 [0.5000-0.5000] | n/a | 0.1267 | 0.0000 | 100.0% | 0.0% | 0.2062 | 0.50 |

## Runs

- `D1_forecaster_deploy` - Deploy candidate: A10s + isotonic calibration + threshold for VME <= 10% with the lowest ME
- `D2_forecaster_deploy` - D1 on cleaning v4: 54 more drugs get a drug class instead of other
- `D3_forecaster_deploy` - D2 on cleaning v5: Genome ID read as text, so 3,312 merged genomes are separate again
- `A0_baseline_leaky` - Reproduces backend/train_models.py: random split, encodings fitted on all data
- `A10_monotonic_mic` - A2 constrained so P(resistant) cannot fall as the MIC rises
- `A10s_monotonic_species` - A10 with species-level Taxon IDs, so a taxon a user types can match
- `A12_species_holdout` - Train without Klebsiella, test only on it, generalisation to an unseen genus
- `A1_oof_random` - A0 with out-of-fold encoding, isolates the cost of target leakage
- `A2_oof_grouped` - A1 with genome-grouped split, the corrected baseline
- `A2b_no_encoding` - A2 without any rate features, what the model learns unaided
- `A3_logistic` - Logistic regression baseline, is boosting earning its complexity?
- `A3b_lgbm_same_sample` - LightGBM on the identical 400k sample, the like-for-like comparison against A3_logistic
- `A4_random_forest` - Random forest on the same 400k sample, bagged trees vs boosted trees
- `A5_xgboost` - XGBoost on the same 400k sample, library comparison against LightGBM
- `A5b_catboost` - CatBoost with the hand-built rate encodings, same 400k sample
- `A5c_catboost_native` - CatBoost with no rate features, its ordered target statistics instead of the hand-built encoding
- `A6_lab_only` - A2 restricted to wet-lab labels, removes computational-caller noise
- `A6b_lab_only_no_mic` - A6 without MIC features, tests whether lab-label performance is just the breakpoint rule
- `A9_threshold_f1` - A2 with the threshold tuned on validation instead of fixed at 0.40
- `A_ablation_drug_only` - Antibiotic and drug class only, the floor the UI calls a population-level estimate
- `A_ablation_no_mic` - A2 without any MIC input, the value of a measured MIC
- `LC_100k` - Learning curve: LightGBM on a 100k-row sample
- `LC_200k` - Learning curve: LightGBM on a 200k-row sample
- `LC_400k` - Learning curve: LightGBM on a 400k-row sample
- `LC_50k` - Learning curve: LightGBM on a 50k-row sample
- `LC_800k` - Learning curve: LightGBM on a 800k-row sample
- `B_base_drug` - Genomes with an assembly, antibiotic only: the floor for Track B
- `B_base_taxonomy` - Antibiotic + genus + species, no genome: what k-mers must beat to show more than taxonomy
- `B_base_drug_rf` - B_base_drug with the random forest used by B0-B2
- `B_base_taxonomy_rf` - B_base_taxonomy with the random forest used by B0-B2
- `B1_kmer4_rf_grouped` - B0 with a genome-grouped split: how much of B0 was genome memorisation
- `B0_kmer4_rf_random` - Shipped design on complete genomes: RF, 4-mers + antibiotic + GC/length, random row split
- `B4_kmer4_lgbm` - B1 with LightGBM instead of the random forest, same features and split
- `B2_kmer3_rf` - B1 with k=3 (64 k-mer columns)
- `B2_kmer5_rf` - B1 with k=5 (1024 k-mer columns)
- `B2_kmer6_rf` - B1 with k=6 (4096 k-mer columns)
- `B6_base_nogenes` - B6 baseline: antibiotic, drug class, genus only, on the same rows
- `B6_genes_lgbm` - Gene features (raw 0/1 + drug-aware) + antibiotic, drug class, genus: first B6, judge on lab rows
- `L_clone_kmer4_lgbm` - B4_kmer4_lgbm with a lineage-grouped split: near-identical isolates (cut 0.00005)
- `L_broad_genes` - B6_genes_lgbm with a lineage-grouped split: broad lineages (0.0007)
- `L_broad_kmer4_lgbm` - B4_kmer4_lgbm with a lineage-grouped split: broad lineages (0.0007)
- `L_broad_nogenes` - B6_base_nogenes with a lineage-grouped split: broad lineages (0.0007)
- `L_broad_taxonomy` - B_base_taxonomy with a lineage-grouped split: broad lineages (0.0007)
- `L_clone_genes` - B6_genes_lgbm with a lineage-grouped split: near-identical isolates (cut 0.00005)
- `L_clone_nogenes` - B6_base_nogenes with a lineage-grouped split: near-identical isolates (cut 0.00005)
- `L_clone_taxonomy` - B_base_taxonomy with a lineage-grouped split: near-identical isolates (cut 0.00005)
- `L_close_genes` - B6_genes_lgbm with a lineage-grouped split: close lineages (0.0002)
- `L_close_kmer4_lgbm` - B4_kmer4_lgbm with a lineage-grouped split: close lineages (0.0002)
- `L_close_nogenes` - B6_base_nogenes with a lineage-grouped split: close lineages (0.0002)
- `L_close_taxonomy` - B_base_taxonomy with a lineage-grouped split: close lineages (0.0002)
- `L_species_genes` - B6_genes_lgbm with a lineage-grouped split: about species level (0.005)
- `L_species_kmer4_lgbm` - B4_kmer4_lgbm with a lineage-grouped split: about species level (0.005)
- `L_species_nogenes` - B6_base_nogenes with a lineage-grouped split: about species level (0.005)
- `L_species_taxonomy` - B_base_taxonomy with a lineage-grouped split: about species level (0.005)

