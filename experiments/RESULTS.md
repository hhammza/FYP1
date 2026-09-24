# Experiment results

| Run | Split | Encoding | Model | AUC-ROC [95% CI] | AUPRC | F1 | VME | ME | Brier | Thr |
|---|---|---|---|---|---|---|---|---|---|---|
| `A6_lab_only` | grouped | oof | lightgbm | 0.9654 [0.9620-0.9685] | 0.9678 | 0.8829 | 8.2% | 16.1% | 0.0748 | 0.40 |
| `A6b_lab_only_no_mic` | grouped | oof | lightgbm | 0.8703 [0.8644-0.8764] | 0.8642 | 0.7934 | 11.4% | 34.6% | 0.1464 | 0.40 |
| `A0_baseline_leaky` | random | leaky | lightgbm | 0.8243 [0.8227-0.8264] | 0.7409 | 0.6662 | 10.6% | 45.4% | 0.1711 | 0.40 |
| `A9_threshold_f1` | grouped | oof | lightgbm | 0.8232 [0.8200-0.8269] | 0.7394 | 0.6703 | 20.2% | 33.6% | 0.1716 | 0.47 |
| `A2_oof_grouped` | grouped | oof | lightgbm | 0.8232 [0.8200-0.8269] | 0.7394 | 0.6645 | 10.1% | 46.4% | 0.1716 | 0.40 |
| `A1_oof_random` | random | oof | lightgbm | 0.8225 [0.8210-0.8247] | 0.7387 | 0.6648 | 10.9% | 45.4% | 0.1719 | 0.40 |
| `A2b_no_encoding` | grouped | none | lightgbm | 0.8221 [0.8188-0.8255] | 0.7376 | 0.6644 | 10.4% | 46.1% | 0.1720 | 0.40 |
| `A10_monotonic_mic` | grouped | oof | lightgbm | 0.8222 [0.8192-0.8257] | 0.7372 | 0.6640 | 10.1% | 46.5% | 0.1722 | 0.40 |
| `LC_800k` | grouped | oof | lightgbm | 0.8200 [0.8162-0.8245] | 0.7372 | 0.6599 | 9.8% | 47.7% | 0.1728 | 0.40 |
| `LC_100k` | grouped | oof | lightgbm | 0.8195 [0.8123-0.8263] | 0.7349 | 0.6589 | 10.0% | 47.6% | 0.1735 | 0.40 |
| `LC_400k` | grouped | oof | lightgbm | 0.8201 [0.8163-0.8245] | 0.7348 | 0.6575 | 8.8% | 49.3% | 0.1733 | 0.40 |
| `A3b_lgbm_same_sample` | grouped | oof | lightgbm | 0.8201 [0.8163-0.8245] | 0.7348 | 0.6683 | 20.4% | 33.5% | 0.1733 | 0.47 |
| `A5_xgboost` | grouped | oof | xgboost | 0.8195 [0.8158-0.8238] | 0.7343 | 0.6675 | 20.8% | 33.2% | 0.1737 | 0.49 |
| `A5b_catboost` | grouped | oof | catboost | 0.8191 [0.8154-0.8234] | 0.7329 | 0.6674 | 20.6% | 33.5% | 0.1736 | 0.47 |
| `A5c_catboost_native` | grouped | none | catboost | 0.8186 [0.8146-0.8226] | 0.7323 | 0.6671 | 20.8% | 33.3% | 0.1739 | 0.47 |
| `LC_50k` | grouped | oof | lightgbm | 0.8157 [0.8060-0.8233] | 0.7307 | 0.6595 | 12.5% | 44.9% | 0.1759 | 0.40 |
| `LC_200k` | grouped | oof | lightgbm | 0.8174 [0.8115-0.8223] | 0.7307 | 0.6581 | 11.2% | 46.2% | 0.1740 | 0.40 |
| `A4_random_forest` | grouped | oof | random_forest | 0.8173 [0.8136-0.8214] | 0.7282 | 0.6657 | 21.4% | 32.9% | 0.1748 | 0.48 |
| `A3_logistic` | grouped | oof | logistic | 0.8024 [0.7985-0.8063] | 0.7083 | 0.6557 | 21.0% | 35.4% | 0.1811 | 0.45 |
| `A_ablation_no_mic` | grouped | oof | lightgbm | 0.8033 [0.7999-0.8068] | 0.6974 | 0.6518 | 9.1% | 50.6% | 0.1820 | 0.40 |
| `A12_species_holdout` | species_holdout | oof | lightgbm | 0.5971 [0.5935-0.6012] | 0.5990 | 0.6045 | 11.4% | 82.9% | 0.2467 | 0.40 |
| `A_ablation_drug_only` | grouped | none | lightgbm | 0.6545 [0.6516-0.6570] | 0.4906 | 0.5743 | 9.8% | 71.2% | 0.2277 | 0.40 |

## Runs

- `A0_baseline_leaky` - Reproduces backend/train_models.py: random split, encodings fitted on all data
- `A1_oof_random` - A0 with out-of-fold encoding, isolates the cost of target leakage
- `A2b_no_encoding` - A2 without any rate features, what the model learns unaided
- `A9_threshold_f1` - A2 with the threshold tuned on validation instead of fixed at 0.40
- `A10_monotonic_mic` - A2 constrained so P(resistant) cannot fall as the MIC rises
- `A_ablation_no_mic` - A2 without any MIC input, the value of a measured MIC
- `A_ablation_drug_only` - Antibiotic and drug class only, the floor the UI calls a population-level estimate
- `A6_lab_only` - A2 restricted to wet-lab labels, removes computational-caller noise
- `A12_species_holdout` - Train without Klebsiella, test only on it, generalisation to an unseen genus
- `A6b_lab_only_no_mic` - A6 without MIC features, tests whether lab-label performance is just the breakpoint rule
- `A3_logistic` - Logistic regression baseline, is boosting earning its complexity?
- `A3b_lgbm_same_sample` - LightGBM on the identical 400k sample, the like-for-like comparison against A3_logistic
- `LC_50k` - Learning curve: LightGBM on a 50k-row sample
- `LC_100k` - Learning curve: LightGBM on a 100k-row sample
- `LC_200k` - Learning curve: LightGBM on a 200k-row sample
- `LC_400k` - Learning curve: LightGBM on a 400k-row sample
- `LC_800k` - Learning curve: LightGBM on a 800k-row sample
- `A2_oof_grouped` - A1 with genome-grouped split, the corrected baseline
- `A4_random_forest` - Random forest on the same 400k sample, bagged trees vs boosted trees
- `A5_xgboost` - XGBoost on the same 400k sample, library comparison against LightGBM
- `A5b_catboost` - CatBoost with the hand-built rate encodings, same 400k sample
- `A5c_catboost_native` - CatBoost with no rate features, its ordered target statistics instead of the hand-built encoding

