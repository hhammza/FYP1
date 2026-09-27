# Experiment results

| Run | Data | Split | Encoding | Model | AUC-ROC [95% CI] | AUPRC | F1 | VME | ME | Brier | Thr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `A6_lab_only` | v5 | grouped | oof | lightgbm | 0.9675 [0.9647-0.9704] | 0.9692 | 0.8858 | 8.4% | 14.9% | 0.0722 | 0.40 |
| `A6b_lab_only_no_mic` | v5 | grouped | oof | lightgbm | 0.8764 [0.8706-0.8819] | 0.8693 | 0.7939 | 9.4% | 36.8% | 0.1428 | 0.40 |
| `A0_baseline_leaky` | v5 | random | leaky | lightgbm | 0.8244 [0.8226-0.8265] | 0.7402 | 0.6639 | 9.3% | 47.3% | 0.1712 | 0.40 |
| `A1_oof_random` | v5 | random | oof | lightgbm | 0.8225 [0.8208-0.8246] | 0.7379 | 0.6617 | 8.9% | 48.3% | 0.1720 | 0.40 |
| `A2_oof_grouped` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | 0.7373 | 0.6638 | 9.3% | 47.4% | 0.1718 | 0.40 |
| `A9_threshold_f1` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | 0.7373 | 0.6704 | 20.1% | 33.5% | 0.1718 | 0.47 |
| `LC_800k` | v5 | grouped | oof | lightgbm | 0.8205 [0.8173-0.8240] | 0.7370 | 0.6618 | 9.8% | 47.3% | 0.1726 | 0.40 |
| `A2b_no_encoding` | v5 | grouped | none | lightgbm | 0.8214 [0.8181-0.8250] | 0.7351 | 0.6626 | 8.9% | 48.1% | 0.1722 | 0.40 |
| `A10_monotonic_mic` | v5 | grouped | oof | lightgbm | 0.8215 [0.8183-0.8249] | 0.7346 | 0.6652 | 10.7% | 45.4% | 0.1725 | 0.40 |
| `LC_200k` | v5 | grouped | oof | lightgbm | 0.8174 [0.8112-0.8223] | 0.7325 | 0.6604 | 9.3% | 48.3% | 0.1737 | 0.40 |
| `A3b_lgbm_same_sample` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | 0.7310 | 0.6658 | 21.1% | 33.5% | 0.1738 | 0.46 |
| `LC_400k` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | 0.7310 | 0.6623 | 11.1% | 45.8% | 0.1738 | 0.40 |
| `A5_xgboost` | v5 | grouped | oof | xgboost | 0.8167 [0.8125-0.8207] | 0.7307 | 0.6640 | 21.8% | 33.0% | 0.1744 | 0.47 |
| `LC_100k` | v5 | grouped | oof | lightgbm | 0.8158 [0.8096-0.8217] | 0.7303 | 0.6612 | 11.0% | 46.2% | 0.1754 | 0.40 |
| `A5b_catboost` | v5 | grouped | oof | catboost | 0.8170 [0.8125-0.8211] | 0.7303 | 0.6660 | 19.9% | 34.8% | 0.1741 | 0.47 |
| `A5c_catboost_native` | v5 | grouped | none | catboost | 0.8155 [0.8111-0.8197] | 0.7282 | 0.6644 | 20.5% | 34.5% | 0.1746 | 0.47 |
| `A4_random_forest` | v5 | grouped | oof | random_forest | 0.8140 [0.8097-0.8183] | 0.7236 | 0.6630 | 21.9% | 33.1% | 0.1754 | 0.47 |
| `A10s_monotonic_species` | v5 | grouped | oof | lightgbm | 0.8040 [0.8002-0.8077] | 0.7176 | 0.6493 | 13.0% | 46.4% | 0.1795 | 0.40 |
| `D2_forecaster_deploy` | v4 | grouped | oof | lightgbm | 0.8044 [0.8010-0.8080] | 0.7163 | 0.6419 | 9.0% | 53.0% | 0.1678 | 0.25 |
| `D1_forecaster_deploy` | v3 | grouped | oof | lightgbm | 0.8043 [0.8010-0.8080] | 0.7161 | 0.6420 | 9.1% | 52.9% | 0.1678 | 0.24 |
| `D3_forecaster_deploy` | v5 | grouped | oof | lightgbm | 0.8039 [0.8001-0.8076] | 0.7135 | 0.6397 | 8.2% | 54.6% | 0.1683 | 0.23 |
| `LC_50k` | v5 | grouped | oof | lightgbm | 0.8038 [0.7951-0.8148] | 0.7110 | 0.6525 | 10.1% | 49.6% | 0.1800 | 0.40 |
| `A3_logistic` | v5 | grouped | oof | logistic | 0.7979 [0.7935-0.8021] | 0.7013 | 0.6542 | 18.4% | 39.0% | 0.1828 | 0.41 |
| `A_ablation_no_mic` | v5 | grouped | oof | lightgbm | 0.8030 [0.8001-0.8069] | 0.6953 | 0.6517 | 9.1% | 50.5% | 0.1822 | 0.40 |
| `A12_species_holdout` | v5 | species_holdout | oof | lightgbm | 0.6041 [0.6012-0.6076] | 0.6070 | 0.4999 | 51.7% | 35.7% | 0.2253 | 0.40 |
| `A_ablation_drug_only` | v5 | grouped | none | lightgbm | 0.6535 [0.6510-0.6566] | 0.4852 | 0.5744 | 10.0% | 70.8% | 0.2308 | 0.40 |

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

