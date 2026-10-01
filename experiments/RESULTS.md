# Experiment results

| Run | Data | Split | Encoding | Model | AUC-ROC [95% CI] | Lab AUC (n) | AUPRC | F1 | Accuracy | Recall | Specificity | VME | ME | Brier | Thr |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `B7L_genes_kmers_v6` | v6 | grouped | none | lightgbm | 0.9829 [0.9817-0.9840] | 0.9809 (40,356) | 0.9783 | 0.9250 | 93.7% | 92.8% | 94.3% | 7.2% | 5.7% | 0.0478 | 0.50 |
| `B7L_genes_kmers_v7` | v7 | grouped | none | lightgbm | 0.9829 [0.9817-0.9840] | 0.9809 (40,356) | 0.9783 | 0.9250 | 93.7% | 92.8% | 94.3% | 7.2% | 5.7% | 0.0478 | 0.50 |
| `B6L_genes_v7_s2` | v7 | grouped | none | lightgbm | 0.9826 [0.9813-0.9837] | 0.9792 (40,525) | 0.9778 | 0.9249 | 93.7% | 92.8% | 94.3% | 7.2% | 5.7% | 0.0478 | 0.50 |
| `B6L_genes_v6` | v6 | grouped | none | lightgbm | 0.9816 [0.9803-0.9827] | 0.9790 (40,356) | 0.9772 | 0.9214 | 93.4% | 92.2% | 94.3% | 7.8% | 5.7% | 0.0494 | 0.50 |
| `B6L_genes_v7` | v7 | grouped | none | lightgbm | 0.9816 [0.9803-0.9827] | 0.9790 (40,356) | 0.9772 | 0.9214 | 93.4% | 92.2% | 94.3% | 7.8% | 5.7% | 0.0494 | 0.50 |
| `B6L_genes_v6_withplasmids` | v6 | grouped | none | lightgbm | 0.9817 [0.9802-0.9829] | 0.9813 (39,582) | 0.9771 | 0.9222 | 93.5% | 92.4% | 94.2% | 7.5% | 5.8% | 0.0493 | 0.50 |
| `LL_clone_genes_v6` | v6 | lineage | none | lightgbm | 0.9816 [0.9800-0.9829] | 0.9794 (40,384) | 0.9769 | 0.9221 | 93.5% | 92.1% | 94.4% | 7.8% | 5.6% | 0.0492 | 0.50 |
| `LL_clone_genes_v7` | v7 | lineage | none | lightgbm | 0.9816 [0.9800-0.9829] | 0.9794 (40,384) | 0.9769 | 0.9221 | 93.5% | 92.2% | 94.4% | 7.8% | 5.6% | 0.0492 | 0.50 |
| `B6L_genes_v7_s1` | v7 | grouped | none | lightgbm | 0.9817 [0.9804-0.9830] | 0.9785 (40,085) | 0.9768 | 0.9217 | 93.4% | 92.3% | 94.2% | 7.7% | 5.8% | 0.0495 | 0.50 |
| `B7L_genes_kmers` | v5 | grouped | none | lightgbm | 0.9818 [0.9804-0.9835] | 0.9798 (40,553) | 0.9763 | 0.9236 | 93.6% | 92.7% | 94.3% | 7.3% | 5.8% | 0.0484 | 0.50 |
| `LL_clone_genes` | v5 | lineage | none | lightgbm | 0.9808 [0.9793-0.9821] | 0.9788 (40,998) | 0.9755 | 0.9210 | 93.4% | 92.1% | 94.3% | 7.9% | 5.7% | 0.0503 | 0.50 |
| `LL_close_genes_v7` | v7 | lineage | none | lightgbm | 0.9801 [0.9782-0.9819] | 0.9786 (40,471) | 0.9753 | 0.9156 | 93.0% | 91.2% | 94.2% | 8.8% | 5.8% | 0.0516 | 0.50 |
| `B6L_genes_only_v7` | v7 | grouped | none | lightgbm | 0.9796 [0.9779-0.9809] | 0.9772 (40,356) | 0.9753 | 0.9184 | 93.2% | 91.7% | 94.2% | 8.3% | 5.8% | 0.0516 | 0.50 |
| `G_genes_deploy` | v7 | grouped | none | lightgbm | 0.9796 [0.9779-0.9809] | 0.9772 (40,356) | 0.9753 | 0.9181 | 93.3% | 90.1% | 95.6% | 9.9% | 4.4% | 0.0516 | 0.58 |
| `LL_close_genes_v6` | v6 | lineage | none | lightgbm | 0.9801 [0.9782-0.9819] | 0.9786 (40,471) | 0.9753 | 0.9156 | 92.9% | 91.2% | 94.2% | 8.8% | 5.8% | 0.0516 | 0.50 |
| `B6L_genes_only_v6` | v6 | grouped | none | lightgbm | 0.9796 [0.9779-0.9809] | 0.9772 (40,356) | 0.9753 | 0.9184 | 93.2% | 91.7% | 94.2% | 8.3% | 5.8% | 0.0516 | 0.50 |
| `B6L_genes` | v5 | grouped | none | lightgbm | 0.9795 [0.9779-0.9813] | 0.9784 (40,553) | 0.9746 | 0.9197 | 93.3% | 91.8% | 94.4% | 8.2% | 5.6% | 0.0509 | 0.50 |
| `LL_close_genes` | v5 | lineage | none | lightgbm | 0.9787 [0.9764-0.9807] | 0.9769 (40,023) | 0.9732 | 0.9117 | 92.7% | 90.4% | 94.3% | 9.6% | 5.7% | 0.0534 | 0.50 |
| `B6L_genes_only` | v5 | grouped | none | lightgbm | 0.9766 [0.9750-0.9784] | 0.9758 (40,553) | 0.9719 | 0.9145 | 92.9% | 91.0% | 94.2% | 9.0% | 5.8% | 0.0539 | 0.50 |
| `A6_lab_only` | v5 | grouped | oof | lightgbm | 0.9675 [0.9647-0.9704] | n/a | 0.9692 | 0.8858 | 88.3% | 91.6% | 85.1% | 8.4% | 14.9% | 0.0722 | 0.40 |
| `LL_broad_genes_v7` | v7 | lineage | none | lightgbm | 0.9681 [0.9435-0.9791] | 0.9651 (31,564) | 0.9599 | 0.8914 | 91.0% | 88.2% | 93.1% | 11.8% | 6.9% | 0.0658 | 0.50 |
| `LL_broad_genes_v6` | v6 | lineage | none | lightgbm | 0.9681 [0.9435-0.9791] | 0.9651 (31,564) | 0.9599 | 0.8914 | 91.0% | 88.2% | 93.1% | 11.8% | 6.9% | 0.0658 | 0.50 |
| `L_broad_genes` | v5 | lineage | none | lightgbm | 0.9898 [0.9032-0.9935] | 0.9949 (810) | 0.9478 | 0.8866 | 96.7% | 93.2% | 97.2% | 6.8% | 2.8% | 0.0284 | 0.50 |
| `B8_acinetobacter_genes` | v5 | species_holdout | none | lightgbm | 0.8411 [0.8349-0.8467] | 0.8381 (22,431) | 0.9430 | 0.8307 | 75.8% | 75.8% | 75.7% | 24.2% | 24.3% | 0.1655 | 0.50 |
| `LL_broad_genes` | v5 | lineage | none | lightgbm | 0.9537 [0.8951-0.9765] | 0.9558 (31,091) | 0.9406 | 0.8614 | 88.3% | 87.5% | 88.9% | 12.5% | 11.1% | 0.0832 | 0.50 |
| `B6_genes_lgbm` | v5 | grouped | none | lightgbm | 0.9812 [0.9758-0.9866] | 0.9930 (384) | 0.9393 | 0.8588 | 95.2% | 89.6% | 96.3% | 10.4% | 3.7% | 0.0394 | 0.50 |
| `B8_acinetobacter_genes_v6` | v6 | species_holdout | none | lightgbm | 0.8231 [0.8158-0.8308] | 0.8226 (22,263) | 0.9381 | 0.8555 | 78.4% | 80.8% | 69.5% | 19.2% | 30.5% | 0.1492 | 0.50 |
| `B8_acinetobacter_genes_v7` | v7 | species_holdout | none | lightgbm | 0.8231 [0.8158-0.8308] | 0.8226 (22,263) | 0.9381 | 0.8555 | 78.4% | 80.8% | 69.5% | 19.2% | 30.5% | 0.1492 | 0.50 |
| `L_clone_genes` | v5 | lineage | none | lightgbm | 0.9770 [0.9693-0.9829] | 0.9956 (363) | 0.9277 | 0.8541 | 95.1% | 87.3% | 96.6% | 12.7% | 3.4% | 0.0409 | 0.50 |
| `B4L_kmer4_lgbm_v6` | v6 | grouped | none | lightgbm | 0.9371 [0.9340-0.9402] | 0.9345 (40,356) | 0.9170 | 0.8351 | 85.6% | 87.1% | 84.4% | 12.9% | 15.6% | 0.1017 | 0.50 |
| `B4L_kmer4_lgbm_v7` | v7 | grouped | none | lightgbm | 0.9371 [0.9340-0.9402] | 0.9345 (40,356) | 0.9170 | 0.8351 | 85.6% | 87.1% | 84.4% | 12.9% | 15.6% | 0.1017 | 0.50 |
| `G_kmer_deploy` | v6 | grouped | none | lightgbm | 0.9371 [0.9340-0.9402] | 0.9345 (40,356) | 0.9170 | 0.8320 | 84.7% | 90.4% | 80.5% | 9.6% | 19.5% | 0.1017 | 0.43 |
| `LT_A2_close_v7` | v7 | lineage | oof | lightgbm | 0.9300 [0.9210-0.9375] | 0.9670 (40,471) | 0.9143 | 0.8046 | 81.5% | 91.1% | 74.5% | 8.9% | 25.5% | 0.1063 | 0.40 |
| `LL_clone_kmer4_v6` | v6 | lineage | none | lightgbm | 0.9347 [0.9284-0.9398] | 0.9327 (40,384) | 0.9139 | 0.8327 | 85.5% | 86.2% | 85.0% | 13.8% | 15.0% | 0.1026 | 0.50 |
| `LL_clone_kmer4_v7` | v7 | lineage | none | lightgbm | 0.9347 [0.9284-0.9398] | 0.9327 (40,384) | 0.9139 | 0.8327 | 85.5% | 86.2% | 85.0% | 13.8% | 15.0% | 0.1026 | 0.50 |
| `LT_A2_grouped_v7` | v7 | grouped | oof | lightgbm | 0.9289 [0.9252-0.9332] | 0.9676 (40,356) | 0.9134 | 0.8010 | 80.9% | 91.7% | 73.1% | 8.3% | 26.9% | 0.1086 | 0.40 |
| `B8_shigella_genes` | v5 | species_holdout | none | lightgbm | 0.9057 [0.9017-0.9092] | 0.9154 (22,088) | 0.9125 | 0.8132 | 84.7% | 73.9% | 93.6% | 26.1% | 6.4% | 0.1171 | 0.50 |
| `LL_clone_kmer4` | v5 | lineage | none | lightgbm | 0.9334 [0.9286-0.9383] | 0.9296 (40,998) | 0.9117 | 0.8299 | 85.2% | 86.1% | 84.6% | 13.9% | 15.4% | 0.1040 | 0.50 |
| `B4L_kmer4_lgbm` | v5 | grouped | none | lightgbm | 0.9326 [0.9297-0.9359] | 0.9283 (40,553) | 0.9110 | 0.8330 | 85.5% | 86.4% | 84.8% | 13.6% | 15.2% | 0.1042 | 0.50 |
| `B8_shigella_genes_v6` | v6 | species_holdout | none | lightgbm | 0.9021 [0.8985-0.9057] | 0.9090 (22,088) | 0.9093 | 0.8195 | 85.0% | 75.6% | 92.7% | 24.4% | 7.3% | 0.1184 | 0.50 |
| `B8_shigella_genes_v7` | v7 | species_holdout | none | lightgbm | 0.9021 [0.8985-0.9057] | 0.9090 (22,088) | 0.9093 | 0.8195 | 85.0% | 75.6% | 92.7% | 24.4% | 7.3% | 0.1184 | 0.50 |
| `LL_close_kmer4_v7` | v7 | lineage | none | lightgbm | 0.9291 [0.9216-0.9369] | 0.9260 (40,471) | 0.9061 | 0.8230 | 84.7% | 85.0% | 84.4% | 14.9% | 15.6% | 0.1069 | 0.50 |
| `LL_close_kmer4_v6` | v6 | lineage | none | lightgbm | 0.9291 [0.9216-0.9369] | 0.9260 (40,471) | 0.9061 | 0.8230 | 84.7% | 85.1% | 84.4% | 14.9% | 15.6% | 0.1069 | 0.50 |
| `LL_close_kmer4` | v5 | lineage | none | lightgbm | 0.9289 [0.9202-0.9367] | 0.9252 (40,023) | 0.9053 | 0.8229 | 84.7% | 85.1% | 84.3% | 14.9% | 15.7% | 0.1072 | 0.50 |
| `LT_D3_close_v7` | v7 | lineage | oof | lightgbm | 0.9206 [0.9100-0.9300] | 0.9619 (40,471) | 0.8977 | 0.7641 | 75.2% | 95.9% | 60.2% | 4.1% | 39.8% | 0.1111 | 0.25 |
| `LT_D3_grouped_v7` | v7 | grouped | oof | lightgbm | 0.9159 [0.9120-0.9204] | 0.9622 (40,356) | 0.8967 | 0.7845 | 79.2% | 90.4% | 71.1% | 9.6% | 28.9% | 0.1142 | 0.30 |
| `T0_grouped_withyear_v7` | v7 | grouped | oof | lightgbm | 0.9280 [0.9254-0.9306] | 0.9280 (114,241) | 0.8913 | 0.7609 | 80.9% | 88.8% | 76.8% | 11.2% | 23.2% | 0.1072 | 0.40 |
| `B8_klebsiella_genes` | v5 | species_holdout | none | lightgbm | 0.8624 [0.8590-0.8654] | 0.8903 (71,188) | 0.8857 | 0.8235 | 76.9% | 93.0% | 54.7% | 7.0% | 45.3% | 0.1713 | 0.50 |
| `LT_A2_broad_v7` | v7 | lineage | oof | lightgbm | 0.9032 [0.8457-0.9483] | 0.9607 (31,564) | 0.8836 | 0.7842 | 80.3% | 86.0% | 76.2% | 14.0% | 23.8% | 0.1243 | 0.40 |
| `A6_lab_only_v7` | v7 | grouped | oof | lightgbm | 0.9227 [0.9197-0.9256] | 0.9227 (129,992) | 0.8829 | 0.7511 | 80.4% | 87.6% | 76.8% | 12.4% | 23.2% | 0.1105 | 0.40 |
| `L_close_genes` | v5 | lineage | none | lightgbm | 0.9597 [0.9219-0.9838] | 0.9931 (347) | 0.8822 | 0.8407 | 95.0% | 81.0% | 97.7% | 19.0% | 2.3% | 0.0539 | 0.50 |
| `A6_lab_only_v7_s1` | v7 | grouped | oof | lightgbm | 0.9211 [0.9181-0.9245] | 0.9211 (129,994) | 0.8807 | 0.7485 | 80.1% | 87.9% | 76.0% | 12.0% | 23.9% | 0.1119 | 0.40 |
| `A6_lab_only_v7_s2` | v7 | grouped | oof | lightgbm | 0.9203 [0.9181-0.9234] | 0.9203 (129,987) | 0.8799 | 0.7474 | 80.0% | 87.7% | 76.1% | 12.3% | 23.9% | 0.1123 | 0.40 |
| `B8_klebsiella_genes_v7` | v7 | species_holdout | none | lightgbm | 0.8570 [0.8538-0.8599] | 0.8832 (71,327) | 0.8793 | 0.8190 | 76.2% | 92.7% | 53.5% | 7.3% | 46.5% | 0.1738 | 0.50 |
| `B8_klebsiella_genes_v6` | v6 | species_holdout | none | lightgbm | 0.8570 [0.8538-0.8599] | 0.8832 (71,327) | 0.8793 | 0.8190 | 76.2% | 92.7% | 53.5% | 7.3% | 46.5% | 0.1738 | 0.50 |
| `A6b_lab_only_no_mic` | v5 | grouped | oof | lightgbm | 0.8764 [0.8706-0.8819] | n/a | 0.8693 | 0.7939 | 76.7% | 90.5% | 63.2% | 9.4% | 36.8% | 0.1428 | 0.40 |
| `LT_D3_broad_v7` | v7 | lineage | oof | lightgbm | 0.9028 [0.8454-0.9473] | 0.9612 (31,564) | 0.8675 | 0.7435 | 72.2% | 96.6% | 54.9% | 3.4% | 45.1% | 0.1274 | 0.20 |
| `LL_broad_kmer4_v7` | v7 | lineage | none | lightgbm | 0.8948 [0.8510-0.9257] | 0.8998 (31,564) | 0.8658 | 0.7747 | 81.2% | 77.5% | 83.9% | 22.5% | 16.1% | 0.1292 | 0.50 |
| `LL_broad_kmer4_v6` | v6 | lineage | none | lightgbm | 0.8948 [0.8510-0.9257] | 0.8998 (31,564) | 0.8658 | 0.7747 | 81.2% | 77.5% | 83.9% | 22.5% | 16.1% | 0.1292 | 0.50 |
| `L_clone_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9569 [0.9395-0.9670] | 0.9928 (363) | 0.8631 | 0.7860 | 93.2% | 75.6% | 96.7% | 24.4% | 3.3% | 0.0524 | 0.50 |
| `B4_kmer4_lgbm` | v5 | grouped | none | lightgbm | 0.9559 [0.9422-0.9667] | 0.9962 (384) | 0.8614 | 0.7854 | 92.9% | 78.7% | 95.7% | 21.3% | 4.3% | 0.0537 | 0.50 |
| `B8_acinetobacter_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.6304 [0.6241-0.6363] | 0.6318 (22,263) | 0.8471 | 0.7016 | 59.9% | 59.8% | 60.3% | 40.2% | 39.7% | 0.2442 | 0.50 |
| `B8_acinetobacter_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.6304 [0.6241-0.6363] | 0.6318 (22,263) | 0.8471 | 0.7016 | 59.9% | 59.8% | 60.3% | 40.2% | 39.7% | 0.2442 | 0.50 |
| `B8_acinetobacter_nogenes` | v5 | species_holdout | none | lightgbm | 0.6285 [0.6212-0.6343] | 0.6355 (22,431) | 0.8456 | 0.7465 | 64.3% | 67.2% | 53.7% | 32.8% | 46.3% | 0.2269 | 0.50 |
| `B8_pseudomonas_genes_v6` | v6 | species_holdout | none | lightgbm | 0.8283 [0.8194-0.8353] | 0.8384 (8,801) | 0.8352 | 0.7443 | 71.4% | 84.4% | 58.8% | 15.6% | 41.2% | 0.1904 | 0.50 |
| `B8_pseudomonas_genes_v7` | v7 | species_holdout | none | lightgbm | 0.8283 [0.8194-0.8353] | 0.8384 (8,801) | 0.8352 | 0.7443 | 71.4% | 84.5% | 58.8% | 15.6% | 41.2% | 0.1904 | 0.50 |
| `B8_pseudomonas_genes` | v5 | species_holdout | none | lightgbm | 0.8292 [0.8204-0.8363] | 0.8414 (8,801) | 0.8300 | 0.7578 | 73.6% | 83.8% | 63.8% | 16.2% | 36.2% | 0.1852 | 0.50 |
| `B1L_kmer4_rf_v6` | v6 | grouped | none | random_forest | 0.8715 [0.8669-0.8761] | 0.8665 (40,356) | 0.8280 | 0.7541 | 77.8% | 81.3% | 75.2% | 18.7% | 24.8% | 0.1511 | 0.50 |
| `B1L_kmer4_rf_v7` | v7 | grouped | none | random_forest | 0.8708 [0.8659-0.8757] | 0.8657 (40,356) | 0.8278 | 0.7517 | 77.6% | 80.8% | 75.4% | 19.2% | 24.6% | 0.1510 | 0.50 |
| `T1_temporal_2012_v7` | v7 | temporal | oof | lightgbm | 0.8780 [0.8754-0.8805] | 0.8780 (318,713) | 0.8240 | 0.7080 | 77.6% | 80.9% | 75.9% | 19.1% | 24.1% | 0.1505 | 0.40 |
| `B1L_kmer4_rf` | v5 | grouped | none | random_forest | 0.8668 [0.8622-0.8716] | 0.8599 (40,553) | 0.8199 | 0.7512 | 77.5% | 81.0% | 75.1% | 19.0% | 24.9% | 0.1525 | 0.50 |
| `LL_broad_kmer4` | v5 | lineage | none | lightgbm | 0.8645 [0.7689-0.9183] | 0.8780 (31,091) | 0.8159 | 0.7544 | 78.4% | 80.0% | 77.3% | 20.0% | 22.7% | 0.1510 | 0.50 |
| `LL_close_taxonomy_v7` | v7 | lineage | none | lightgbm | 0.8463 [0.8262-0.8702] | 0.8530 (40,471) | 0.7987 | 0.7322 | 75.2% | 81.0% | 71.0% | 19.0% | 29.0% | 0.1599 | 0.50 |
| `LL_close_taxonomy_v6` | v6 | lineage | none | lightgbm | 0.8463 [0.8262-0.8702] | 0.8530 (40,471) | 0.7987 | 0.7322 | 75.2% | 81.0% | 71.0% | 19.0% | 29.0% | 0.1599 | 0.50 |
| `L_broad_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9495 [0.8204-0.9508] | 0.9762 (810) | 0.7966 | 0.7408 | 92.8% | 74.2% | 95.8% | 25.9% | 4.2% | 0.0543 | 0.50 |
| `LL_clone_taxonomy_v6` | v6 | lineage | none | lightgbm | 0.8387 [0.8292-0.8508] | 0.8509 (40,384) | 0.7928 | 0.7214 | 74.6% | 78.5% | 71.8% | 21.5% | 28.2% | 0.1639 | 0.50 |
| `LL_clone_taxonomy_v7` | v7 | lineage | none | lightgbm | 0.8387 [0.8292-0.8508] | 0.8509 (40,384) | 0.7928 | 0.7214 | 74.6% | 78.5% | 71.8% | 21.5% | 28.2% | 0.1639 | 0.50 |
| `LL_close_taxonomy` | v5 | lineage | none | lightgbm | 0.8399 [0.8209-0.8636] | 0.8492 (40,023) | 0.7903 | 0.7198 | 74.4% | 78.7% | 71.2% | 21.3% | 28.8% | 0.1637 | 0.50 |
| `B6L_base_taxonomy` | v5 | grouped | none | lightgbm | 0.8366 [0.8316-0.8422] | 0.8523 (40,553) | 0.7899 | 0.7212 | 74.2% | 79.6% | 70.4% | 20.4% | 29.6% | 0.1651 | 0.50 |
| `LL_clone_taxonomy` | v5 | lineage | none | lightgbm | 0.8361 [0.8263-0.8472] | 0.8513 (40,998) | 0.7883 | 0.7184 | 74.5% | 77.9% | 72.0% | 22.1% | 28.0% | 0.1652 | 0.50 |
| `B6L_base_taxonomy_v6` | v6 | grouped | none | lightgbm | 0.8358 [0.8298-0.8419] | 0.8487 (40,356) | 0.7880 | 0.7199 | 73.9% | 79.8% | 69.7% | 20.2% | 30.3% | 0.1662 | 0.50 |
| `B6L_base_taxonomy_v7` | v7 | grouped | none | lightgbm | 0.8358 [0.8298-0.8419] | 0.8487 (40,356) | 0.7880 | 0.7199 | 74.0% | 79.8% | 69.7% | 20.2% | 30.3% | 0.1662 | 0.50 |
| `B6L_nogenes` | v5 | grouped | none | lightgbm | 0.8243 [0.8189-0.8304] | 0.8375 (40,553) | 0.7714 | 0.7103 | 73.6% | 77.4% | 70.9% | 22.6% | 29.1% | 0.1713 | 0.50 |
| `B6L_nogenes_v7` | v7 | grouped | none | lightgbm | 0.8236 [0.8167-0.8299] | 0.8343 (40,356) | 0.7697 | 0.7098 | 73.4% | 77.5% | 70.5% | 22.5% | 29.5% | 0.1723 | 0.50 |
| `B6L_nogenes_v6` | v6 | grouped | none | lightgbm | 0.8236 [0.8167-0.8299] | 0.8343 (40,356) | 0.7697 | 0.7098 | 73.4% | 77.5% | 70.5% | 22.5% | 29.5% | 0.1723 | 0.50 |
| `LL_broad_taxonomy_v6` | v6 | lineage | none | lightgbm | 0.8245 [0.7237-0.8817] | 0.8155 (31,564) | 0.7687 | 0.6984 | 73.6% | 73.4% | 73.7% | 26.6% | 26.3% | 0.1701 | 0.50 |
| `LL_broad_taxonomy_v7` | v7 | lineage | none | lightgbm | 0.8245 [0.7237-0.8817] | 0.8155 (31,564) | 0.7687 | 0.6984 | 73.6% | 73.4% | 73.7% | 26.6% | 26.3% | 0.1701 | 0.50 |
| `T1_temporal_2014_v7` | v7 | temporal | oof | lightgbm | 0.8573 [0.8546-0.8602] | 0.8573 (226,045) | 0.7670 | 0.6695 | 76.9% | 77.0% | 76.8% | 23.0% | 23.2% | 0.1539 | 0.40 |
| `B8_salmonella_genes` | v5 | species_holdout | none | lightgbm | 0.9306 [0.9262-0.9348] | 0.9452 (22,332) | 0.7593 | 0.7631 | 91.1% | 85.4% | 92.2% | 14.6% | 7.8% | 0.0790 | 0.50 |
| `LL_broad_taxonomy` | v5 | lineage | none | lightgbm | 0.8230 [0.6942-0.8849] | 0.8231 (31,091) | 0.7591 | 0.6994 | 73.8% | 73.7% | 73.8% | 26.3% | 26.2% | 0.1711 | 0.50 |
| `B8_salmonella_genes_v6` | v6 | species_holdout | none | lightgbm | 0.9314 [0.9274-0.9358] | 0.9406 (22,332) | 0.7547 | 0.7462 | 90.8% | 81.1% | 92.7% | 18.9% | 7.3% | 0.0754 | 0.50 |
| `B8_salmonella_genes_v7` | v7 | species_holdout | none | lightgbm | 0.9314 [0.9274-0.9358] | 0.9406 (22,332) | 0.7547 | 0.7462 | 90.8% | 81.0% | 92.7% | 18.9% | 7.3% | 0.0754 | 0.50 |
| `A6b_lab_only_no_mic_v7` | v7 | grouped | oof | lightgbm | 0.8400 [0.8365-0.8438] | 0.8400 (129,992) | 0.7517 | 0.6590 | 70.7% | 83.9% | 64.0% | 16.1% | 36.0% | 0.1626 | 0.40 |
| `A6b_lab_only_no_mic_v7_s1` | v7 | grouped | oof | lightgbm | 0.8374 [0.8332-0.8423] | 0.8374 (129,994) | 0.7473 | 0.6584 | 70.7% | 83.8% | 64.0% | 16.2% | 36.0% | 0.1639 | 0.40 |
| `T1_temporal_2015_v7` | v7 | temporal | oof | lightgbm | 0.8569 [0.8537-0.8602] | 0.8569 (169,597) | 0.7468 | 0.6483 | 75.8% | 79.8% | 74.2% | 20.2% | 25.8% | 0.1530 | 0.40 |
| `A6b_lab_only_no_mic_v7_s2` | v7 | grouped | oof | lightgbm | 0.8353 [0.8317-0.8395] | 0.8353 (129,987) | 0.7451 | 0.6560 | 70.4% | 83.7% | 63.6% | 16.3% | 36.4% | 0.1651 | 0.40 |
| `B2_kmer3_rf` | v5 | grouped | none | random_forest | 0.9021 [0.8796-0.9214] | 0.9497 (384) | 0.7428 | 0.6791 | 89.2% | 69.6% | 93.0% | 30.4% | 7.0% | 0.1036 | 0.50 |
| `A0_baseline_leaky` | v5 | random | leaky | lightgbm | 0.8244 [0.8226-0.8265] | n/a | 0.7402 | 0.6639 | 66.5% | 90.7% | 52.7% | 9.3% | 47.3% | 0.1712 | 0.40 |
| `A1_oof_random` | v5 | random | oof | lightgbm | 0.8225 [0.8208-0.8246] | n/a | 0.7379 | 0.6617 | 66.0% | 91.1% | 51.7% | 8.9% | 48.3% | 0.1720 | 0.40 |
| `A2_oof_grouped` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | n/a | 0.7373 | 0.6638 | 66.5% | 90.7% | 52.6% | 9.3% | 47.4% | 0.1718 | 0.40 |
| `A9_threshold_f1` | v5 | grouped | oof | lightgbm | 0.8227 [0.8197-0.8264] | n/a | 0.7373 | 0.6704 | 71.4% | 79.9% | 66.5% | 20.1% | 33.5% | 0.1718 | 0.47 |
| `LC_800k` | v5 | grouped | oof | lightgbm | 0.8205 [0.8173-0.8240] | n/a | 0.7370 | 0.6618 | 66.4% | 90.2% | 52.7% | 9.8% | 47.3% | 0.1726 | 0.40 |
| `A2b_no_encoding` | v5 | grouped | none | lightgbm | 0.8214 [0.8181-0.8250] | n/a | 0.7351 | 0.6626 | 66.2% | 91.1% | 51.9% | 8.9% | 48.1% | 0.1722 | 0.40 |
| `A10_monotonic_mic` | v5 | grouped | oof | lightgbm | 0.8215 [0.8183-0.8249] | n/a | 0.7346 | 0.6652 | 67.2% | 89.3% | 54.6% | 10.7% | 45.4% | 0.1725 | 0.40 |
| `LC_200k` | v5 | grouped | oof | lightgbm | 0.8174 [0.8112-0.8223] | n/a | 0.7325 | 0.6604 | 65.9% | 90.7% | 51.7% | 9.3% | 48.3% | 0.1737 | 0.40 |
| `LC_400k` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | n/a | 0.7310 | 0.6623 | 66.9% | 88.9% | 54.2% | 11.1% | 45.8% | 0.1738 | 0.40 |
| `A3b_lgbm_same_sample` | v5 | grouped | oof | lightgbm | 0.8176 [0.8132-0.8217] | n/a | 0.7310 | 0.6658 | 71.1% | 78.9% | 66.5% | 21.1% | 33.5% | 0.1738 | 0.46 |
| `A5_xgboost` | v5 | grouped | oof | xgboost | 0.8167 [0.8125-0.8207] | n/a | 0.7307 | 0.6640 | 71.1% | 78.2% | 67.0% | 21.8% | 33.0% | 0.1744 | 0.47 |
| `A5b_catboost` | v5 | grouped | oof | catboost | 0.8170 [0.8125-0.8211] | n/a | 0.7303 | 0.6660 | 70.6% | 80.1% | 65.2% | 19.9% | 34.8% | 0.1741 | 0.47 |
| `LC_100k` | v5 | grouped | oof | lightgbm | 0.8158 [0.8096-0.8217] | n/a | 0.7303 | 0.6612 | 66.6% | 89.0% | 53.8% | 11.0% | 46.2% | 0.1754 | 0.40 |
| `A5c_catboost_native` | v5 | grouped | none | catboost | 0.8155 [0.8111-0.8197] | n/a | 0.7282 | 0.6644 | 70.6% | 79.5% | 65.5% | 20.5% | 34.5% | 0.1746 | 0.47 |
| `A4_random_forest` | v5 | grouped | oof | random_forest | 0.8140 [0.8097-0.8183] | n/a | 0.7236 | 0.6630 | 71.0% | 78.1% | 66.9% | 21.9% | 33.1% | 0.1754 | 0.47 |
| `B1_kmer4_rf_grouped` | v5 | grouped | none | random_forest | 0.9037 [0.8828-0.9204] | 0.9765 (384) | 0.7225 | 0.6351 | 87.0% | 68.9% | 90.5% | 31.1% | 9.5% | 0.1075 | 0.50 |
| `A10s_monotonic_species` | v5 | grouped | oof | lightgbm | 0.8040 [0.8002-0.8077] | n/a | 0.7176 | 0.6493 | 65.7% | 87.0% | 53.6% | 13.0% | 46.4% | 0.1795 | 0.40 |
| `B0_kmer4_rf_random` | v5 | random | none | random_forest | 0.9107 [0.9014-0.9187] | 0.9624 (361) | 0.7168 | 0.6008 | 82.0% | 82.6% | 81.8% | 17.4% | 18.2% | 0.1154 | 0.50 |
| `D2_forecaster_deploy` | v4 | grouped | oof | lightgbm | 0.8044 [0.8010-0.8080] | n/a | 0.7163 | 0.6419 | 63.0% | 91.0% | 47.0% | 9.0% | 53.0% | 0.1678 | 0.25 |
| `D1_forecaster_deploy` | v3 | grouped | oof | lightgbm | 0.8043 [0.8010-0.8080] | n/a | 0.7161 | 0.6420 | 63.0% | 90.9% | 47.1% | 9.1% | 52.9% | 0.1678 | 0.24 |
| `D3_forecaster_deploy` | v5 | grouped | oof | lightgbm | 0.8039 [0.8001-0.8076] | n/a | 0.7135 | 0.6397 | 62.3% | 91.8% | 45.4% | 8.2% | 54.6% | 0.1683 | 0.23 |
| `LC_50k` | v5 | grouped | oof | lightgbm | 0.8038 [0.7951-0.8148] | n/a | 0.7110 | 0.6525 | 64.9% | 90.0% | 50.4% | 10.1% | 49.6% | 0.1800 | 0.40 |
| `A3_logistic` | v5 | grouped | oof | logistic | 0.7979 [0.7935-0.8021] | n/a | 0.7013 | 0.6542 | 68.5% | 81.6% | 61.0% | 18.4% | 39.0% | 0.1828 | 0.41 |
| `L_close_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.9083 [0.8676-0.9346] | 0.9455 (347) | 0.6962 | 0.6438 | 89.0% | 61.3% | 94.4% | 38.7% | 5.7% | 0.0817 | 0.50 |
| `A_ablation_no_mic` | v5 | grouped | oof | lightgbm | 0.8030 [0.8001-0.8069] | n/a | 0.6953 | 0.6517 | 64.6% | 90.9% | 49.5% | 9.1% | 50.5% | 0.1822 | 0.40 |
| `B2_kmer5_rf` | v5 | grouped | none | random_forest | 0.8875 [0.8652-0.9045] | 0.9640 (384) | 0.6749 | 0.5926 | 85.4% | 64.4% | 89.5% | 35.6% | 10.5% | 0.1158 | 0.50 |
| `B8_klebsiella_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.5860 [0.5830-0.5888] | 0.6223 (71,327) | 0.6603 | 0.6683 | 58.6% | 72.0% | 40.1% | 28.0% | 59.9% | 0.2476 | 0.50 |
| `B8_klebsiella_nogenes` | v5 | species_holdout | none | lightgbm | 0.5847 [0.5821-0.5875] | 0.6226 (71,188) | 0.6603 | 0.6686 | 58.6% | 72.1% | 40.1% | 27.9% | 59.9% | 0.2470 | 0.50 |
| `B8_klebsiella_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.5860 [0.5830-0.5888] | 0.6223 (71,327) | 0.6603 | 0.6683 | 58.6% | 72.0% | 40.1% | 28.0% | 59.9% | 0.2476 | 0.50 |
| `B2_kmer6_rf` | v5 | grouped | none | random_forest | 0.8829 [0.8625-0.9010] | 0.9566 (384) | 0.6574 | 0.5791 | 85.1% | 62.3% | 89.6% | 37.7% | 10.4% | 0.1189 | 0.50 |
| `B8_campylobacter_genes_v6` | v6 | species_holdout | none | lightgbm | 0.8444 [0.8313-0.8584] | 0.8495 (7,734) | 0.6538 | 0.5383 | 81.1% | 59.1% | 86.1% | 40.9% | 13.9% | 0.1521 | 0.50 |
| `B8_campylobacter_genes_v7` | v7 | species_holdout | none | lightgbm | 0.8444 [0.8313-0.8584] | 0.8495 (7,734) | 0.6538 | 0.5383 | 81.1% | 59.1% | 86.1% | 40.9% | 13.9% | 0.1521 | 0.50 |
| `B8_neisseria_genes_v7` | v7 | species_holdout | none | lightgbm | 0.8605 [0.8564-0.8639] | 0.8433 (28,183) | 0.6420 | 0.5610 | 68.2% | 89.6% | 61.9% | 10.4% | 38.1% | 0.2223 | 0.50 |
| `B8_neisseria_genes_v6` | v6 | species_holdout | none | lightgbm | 0.8605 [0.8564-0.8639] | 0.8433 (28,183) | 0.6420 | 0.5610 | 68.2% | 89.6% | 61.9% | 10.4% | 38.1% | 0.2223 | 0.50 |
| `B8_neisseria_genes` | v5 | species_holdout | none | lightgbm | 0.8548 [0.8505-0.8585] | 0.8439 (28,199) | 0.6349 | 0.5845 | 71.3% | 88.9% | 66.1% | 11.1% | 33.9% | 0.2038 | 0.50 |
| `A12_species_holdout_v7` | v7 | species_holdout | oof | lightgbm | 0.6183 [0.6158-0.6210] | 0.9454 (78,708) | 0.6257 | 0.5835 | 56.8% | 63.9% | 50.4% | 36.1% | 49.6% | 0.2403 | 0.40 |
| `B8_campylobacter_genes` | v5 | species_holdout | none | lightgbm | 0.8512 [0.8390-0.8642] | 0.8558 (7,734) | 0.6226 | 0.5399 | 81.2% | 59.2% | 86.2% | 40.8% | 13.8% | 0.1532 | 0.50 |
| `A0_baseline_leaky_v7` | v7 | random | leaky | lightgbm | 0.7870 [0.7860-0.7880] | 0.9220 (129,328) | 0.6157 | 0.5569 | 61.8% | 85.6% | 52.5% | 14.4% | 47.5% | 0.1879 | 0.40 |
| `A1_oof_random_v7` | v7 | random | oof | lightgbm | 0.7862 [0.7852-0.7872] | 0.9212 (129,328) | 0.6145 | 0.5585 | 62.5% | 84.7% | 53.8% | 15.3% | 46.2% | 0.1882 | 0.40 |
| `A2_oof_grouped_v7_s1` | v7 | grouped | oof | lightgbm | 0.7853 [0.7837-0.7871] | 0.9226 (129,328) | 0.6134 | 0.5555 | 61.6% | 85.6% | 52.2% | 14.4% | 47.8% | 0.1886 | 0.40 |
| `A10_monotonic_mic_v7_s1` | v7 | grouped | oof | lightgbm | 0.7850 [0.7834-0.7867] | 0.9197 (129,328) | 0.6124 | 0.5553 | 61.6% | 85.6% | 52.2% | 14.4% | 47.8% | 0.1889 | 0.40 |
| `A2_oof_grouped_v7` | v7 | grouped | oof | lightgbm | 0.7850 [0.7833-0.7868] | 0.9195 (129,633) | 0.6120 | 0.5555 | 61.6% | 85.5% | 52.3% | 14.4% | 47.7% | 0.1888 | 0.40 |
| `A9_threshold_f1_v7` | v7 | grouped | oof | lightgbm | 0.7850 [0.7833-0.7868] | 0.9195 (129,633) | 0.6120 | 0.5745 | 70.0% | 72.3% | 69.0% | 27.7% | 31.0% | 0.1888 | 0.49 |
| `A2_oof_grouped_v7_s2` | v7 | grouped | oof | lightgbm | 0.7844 [0.7830-0.7861] | 0.9196 (129,849) | 0.6116 | 0.5553 | 61.6% | 85.5% | 52.3% | 14.5% | 47.7% | 0.1888 | 0.40 |
| `A10_monotonic_mic_v7` | v7 | grouped | oof | lightgbm | 0.7846 [0.7830-0.7865] | 0.9169 (129,633) | 0.6112 | 0.5554 | 61.6% | 85.5% | 52.3% | 14.5% | 47.7% | 0.1889 | 0.40 |
| `A10_monotonic_mic_v7_s2` | v7 | grouped | oof | lightgbm | 0.7840 [0.7826-0.7856] | 0.9167 (129,849) | 0.6105 | 0.5571 | 62.3% | 84.5% | 53.7% | 15.5% | 46.3% | 0.1890 | 0.40 |
| `A2b_no_encoding_v7` | v7 | grouped | none | lightgbm | 0.7839 [0.7821-0.7856] | 0.9194 (129,633) | 0.6098 | 0.5570 | 62.3% | 84.5% | 53.6% | 15.5% | 46.4% | 0.1891 | 0.40 |
| `LC_200k_v7` | v7 | grouped | oof | lightgbm | 0.7807 [0.7759-0.7862] | 0.9013 (3,300) | 0.6085 | 0.5564 | 62.4% | 83.8% | 54.0% | 16.2% | 46.0% | 0.1904 | 0.40 |
| `LC_800k_v7` | v7 | grouped | oof | lightgbm | 0.7825 [0.7800-0.7853] | 0.9205 (12,994) | 0.6075 | 0.5592 | 62.8% | 84.0% | 54.4% | 16.0% | 45.6% | 0.1892 | 0.40 |
| `A12_species_holdout` | v5 | species_holdout | oof | lightgbm | 0.6041 [0.6012-0.6076] | n/a | 0.6070 | 0.4999 | 57.3% | 48.3% | 64.3% | 51.7% | 35.7% | 0.2253 | 0.40 |
| `A3b_lgbm_same_sample_v7` | v7 | grouped | oof | lightgbm | 0.7804 [0.7766-0.7842] | 0.9076 (6,522) | 0.6057 | 0.5709 | 70.8% | 69.2% | 71.4% | 30.8% | 28.6% | 0.1904 | 0.52 |
| `LC_400k_v7` | v7 | grouped | oof | lightgbm | 0.7804 [0.7766-0.7842] | 0.9076 (6,522) | 0.6057 | 0.5534 | 61.4% | 85.1% | 52.2% | 14.9% | 47.8% | 0.1904 | 0.40 |
| `A5_xgboost_v7` | v7 | grouped | oof | xgboost | 0.7792 [0.7752-0.7829] | 0.9073 (6,522) | 0.6033 | 0.5698 | 70.5% | 69.5% | 70.9% | 30.4% | 29.1% | 0.1910 | 0.50 |
| `LC_50k_v7` | v7 | grouped | oof | lightgbm | 0.7761 [0.7656-0.7860] | 0.8589 (835) | 0.6030 | 0.5579 | 62.2% | 84.2% | 53.5% | 15.8% | 46.5% | 0.1909 | 0.40 |
| `A5b_catboost_v7` | v7 | grouped | oof | catboost | 0.7795 [0.7756-0.7831] | 0.9028 (6,522) | 0.6029 | 0.5694 | 69.4% | 72.1% | 68.3% | 27.9% | 31.7% | 0.1908 | 0.49 |
| `A5c_catboost_native_v7` | v7 | grouped | none | catboost | 0.7788 [0.7750-0.7829] | 0.9032 (6,522) | 0.6025 | 0.5695 | 69.3% | 72.2% | 68.2% | 27.8% | 31.8% | 0.1915 | 0.49 |
| `A4_random_forest_v7` | v7 | grouped | oof | random_forest | 0.7772 [0.7734-0.7808] | 0.8995 (6,522) | 0.5977 | 0.5694 | 70.2% | 70.2% | 70.1% | 29.8% | 29.9% | 0.1914 | 0.51 |
| `A10s_monotonic_species_v7` | v7 | grouped | oof | lightgbm | 0.7737 [0.7720-0.7754] | 0.9082 (129,633) | 0.5953 | 0.5496 | 61.4% | 83.9% | 52.7% | 16.1% | 47.3% | 0.1931 | 0.40 |
| `LC_100k_v7` | v7 | grouped | oof | lightgbm | 0.7764 [0.7697-0.7841] | 0.8838 (1,688) | 0.5945 | 0.5573 | 62.7% | 83.4% | 54.6% | 16.7% | 45.4% | 0.1902 | 0.40 |
| `D3_forecaster_deploy_v7` | v7 | grouped | oof | lightgbm | 0.7737 [0.7720-0.7754] | 0.9081 (129,633) | 0.5919 | 0.5259 | 53.8% | 91.4% | 39.2% | 8.6% | 60.8% | 0.1604 | 0.15 |
| `D4_forecaster_deploy` | v6 | grouped | oof | lightgbm | 0.7735 [0.7718-0.7752] | 0.9067 (129,633) | 0.5916 | 0.5305 | 55.2% | 90.2% | 41.6% | 9.8% | 58.4% | 0.1605 | 0.16 |
| `B6L_base_drug` | v5 | grouped | none | lightgbm | 0.6840 [0.6795-0.6883] | 0.7210 (40,553) | 0.5900 | 0.5734 | 63.5% | 58.6% | 67.0% | 41.4% | 33.0% | 0.2222 | 0.50 |
| `A_ablation_no_mic_v7` | v7 | grouped | oof | lightgbm | 0.7753 [0.7737-0.7772] | 0.8358 (129,633) | 0.5891 | 0.5514 | 61.5% | 84.4% | 52.6% | 15.6% | 47.4% | 0.1932 | 0.40 |
| `B6L_base_drug_v6` | v6 | grouped | none | lightgbm | 0.6815 [0.6773-0.6859] | 0.7147 (40,356) | 0.5863 | 0.5966 | 62.1% | 66.8% | 58.7% | 33.2% | 41.3% | 0.2233 | 0.50 |
| `B6L_base_drug_v7` | v7 | grouped | none | lightgbm | 0.6815 [0.6773-0.6859] | 0.7147 (40,356) | 0.5863 | 0.5966 | 62.1% | 66.8% | 58.7% | 33.2% | 41.3% | 0.2233 | 0.50 |
| `A3_logistic_v7` | v7 | grouped | oof | logistic | 0.7654 [0.7617-0.7689] | 0.8433 (6,522) | 0.5756 | 0.5620 | 68.7% | 71.6% | 67.5% | 28.4% | 32.5% | 0.1968 | 0.47 |
| `B6R_gene_rule_class_v7` | v7 | grouped | none | gene_rule | 0.7268 [0.7204-0.7326] | 0.7109 (40,356) | 0.5721 | 0.7207 | 69.1% | 95.2% | 50.2% | 4.8% | 49.8% | 0.3095 | 0.50 |
| `B8_pseudomonas_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.5768 [0.5719-0.5835] | 0.6189 (8,801) | 0.5557 | 0.5791 | 53.9% | 64.4% | 43.7% | 35.6% | 56.3% | 0.2516 | 0.50 |
| `B8_pseudomonas_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.5768 [0.5719-0.5835] | 0.6189 (8,801) | 0.5557 | 0.5791 | 53.9% | 64.4% | 43.7% | 35.6% | 56.3% | 0.2516 | 0.50 |
| `B8_pseudomonas_nogenes` | v5 | species_holdout | none | lightgbm | 0.5741 [0.5691-0.5807] | 0.6221 (8,801) | 0.5528 | 0.5790 | 53.9% | 64.4% | 43.7% | 35.6% | 56.3% | 0.2532 | 0.50 |
| `B_base_taxonomy` | v5 | grouped | none | lightgbm | 0.8229 [0.8037-0.8442] | 0.7104 (384) | 0.5491 | 0.4823 | 74.1% | 73.3% | 74.2% | 26.7% | 25.8% | 0.1631 | 0.50 |
| `B_base_taxonomy_rf` | v5 | grouped | none | random_forest | 0.8214 [0.8013-0.8422] | 0.7146 (384) | 0.5485 | 0.5024 | 81.4% | 57.1% | 86.2% | 42.9% | 13.8% | 0.1664 | 0.50 |
| `L_clone_nogenes` | v5 | lineage | none | lightgbm | 0.8098 [0.7660-0.8449] | 0.6889 (363) | 0.5464 | 0.4820 | 76.0% | 67.8% | 77.7% | 32.2% | 22.3% | 0.1653 | 0.50 |
| `L_clone_taxonomy` | v5 | lineage | none | lightgbm | 0.8185 [0.7770-0.8508] | 0.7019 (363) | 0.5457 | 0.4717 | 74.8% | 68.6% | 76.0% | 31.4% | 24.0% | 0.1635 | 0.50 |
| `B6_base_nogenes` | v5 | grouped | none | lightgbm | 0.8132 [0.7950-0.8339] | 0.6963 (384) | 0.5429 | 0.4844 | 75.2% | 70.7% | 76.1% | 29.3% | 23.9% | 0.1658 | 0.50 |
| `B6R_gene_rule_key_v7` | v7 | grouped | none | gene_rule | 0.5965 [0.5942-0.5987] | 0.5981 (40,356) | 0.5141 | 0.3521 | 65.7% | 22.2% | 97.1% | 77.8% | 2.9% | 0.3431 | 0.50 |
| `B8_shigella_nogenes` | v5 | species_holdout | none | lightgbm | 0.5472 [0.5427-0.5512] | 0.5355 (22,088) | 0.5056 | 0.4480 | 52.8% | 42.5% | 61.2% | 57.5% | 38.8% | 0.2667 | 0.50 |
| `B8_shigella_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.5413 [0.5371-0.5456] | 0.5311 (22,088) | 0.4909 | 0.4480 | 52.8% | 42.5% | 61.2% | 57.5% | 38.8% | 0.2561 | 0.50 |
| `B8_shigella_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.5413 [0.5371-0.5456] | 0.5311 (22,088) | 0.4909 | 0.4480 | 52.8% | 42.5% | 61.2% | 57.5% | 38.8% | 0.2561 | 0.50 |
| `A_ablation_drug_only` | v5 | grouped | none | lightgbm | 0.6535 [0.6510-0.6566] | n/a | 0.4852 | 0.5744 | 51.4% | 90.0% | 29.2% | 10.0% | 70.8% | 0.2308 | 0.40 |
| `L_close_taxonomy` | v5 | lineage | none | lightgbm | 0.7878 [0.7210-0.8534] | 0.6448 (347) | 0.4471 | 0.4524 | 73.8% | 66.6% | 75.2% | 33.4% | 24.8% | 0.1611 | 0.50 |
| `B_base_drug` | v5 | grouped | none | lightgbm | 0.7521 [0.7321-0.7736] | 0.5611 (384) | 0.4425 | 0.4218 | 72.4% | 61.2% | 74.6% | 38.8% | 25.4% | 0.1798 | 0.50 |
| `B_base_drug_rf` | v5 | grouped | none | random_forest | 0.7471 [0.7283-0.7675] | 0.5668 (384) | 0.4363 | 0.4195 | 79.7% | 44.5% | 86.7% | 55.5% | 13.3% | 0.2041 | 0.50 |
| `A_ablation_drug_only_v7` | v7 | grouped | none | lightgbm | 0.6572 [0.6560-0.6585] | 0.6084 (129,633) | 0.4249 | 0.4708 | 44.8% | 87.6% | 28.1% | 12.3% | 72.0% | 0.2301 | 0.40 |
| `A_ablation_drug_only_v7_s1` | v7 | grouped | none | lightgbm | 0.6569 [0.6558-0.6583] | 0.6082 (129,328) | 0.4241 | 0.4779 | 54.1% | 75.0% | 46.0% | 25.1% | 54.0% | 0.2153 | 0.40 |
| `L_close_nogenes` | v5 | lineage | none | lightgbm | 0.7704 [0.7115-0.8311] | 0.6671 (347) | 0.4235 | 0.4618 | 75.2% | 65.3% | 77.2% | 34.7% | 22.8% | 0.1650 | 0.50 |
| `A_ablation_drug_only_v7_s2` | v7 | grouped | none | lightgbm | 0.6565 [0.6553-0.6577] | 0.6069 (129,849) | 0.4231 | 0.4735 | 47.9% | 83.5% | 34.1% | 16.5% | 65.9% | 0.2238 | 0.40 |
| `B8_neisseria_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.7251 [0.7209-0.7300] | 0.7453 (28,183) | 0.3999 | 0.5276 | 64.7% | 86.7% | 58.3% | 13.3% | 41.7% | 0.2100 | 0.50 |
| `B8_neisseria_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.7251 [0.7209-0.7300] | 0.7453 (28,183) | 0.3999 | 0.5276 | 64.7% | 86.7% | 58.3% | 13.3% | 41.7% | 0.2100 | 0.50 |
| `B8_neisseria_nogenes` | v5 | species_holdout | none | lightgbm | 0.7246 [0.7204-0.7294] | 0.7447 (28,199) | 0.3998 | 0.4558 | 52.7% | 87.1% | 42.6% | 12.9% | 57.4% | 0.2152 | 0.50 |
| `L_broad_nogenes` | v5 | lineage | none | lightgbm | 0.7152 [0.6897-0.8053] | 0.6863 (810) | 0.3534 | 0.3477 | 82.9% | 32.9% | 90.9% | 67.1% | 9.1% | 0.1455 | 0.50 |
| `L_broad_taxonomy` | v5 | lineage | none | lightgbm | 0.7241 [0.5979-0.7350] | 0.7137 (810) | 0.3248 | 0.0000 | 86.1% | 0.0% | 100.0% | 100.0% | 0.0% | 0.1272 | 0.50 |
| `L_species_genes` | v5 | lineage | none | lightgbm | 0.7080 [0.7080-0.7080] | n/a | 0.2925 | 0.3326 | 70.1% | 58.7% | 71.8% | 41.2% | 28.2% | 0.2051 | 0.50 |
| `B8_salmonella_nogenes` | v5 | species_holdout | none | lightgbm | 0.5491 [0.5459-0.5528] | 0.5352 (22,332) | 0.1980 | 0.2655 | 47.2% | 56.6% | 45.3% | 43.4% | 54.7% | 0.2882 | 0.50 |
| `B8_salmonella_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.5487 [0.5447-0.5529] | 0.5355 (22,332) | 0.1976 | 0.2598 | 43.2% | 59.5% | 40.0% | 40.6% | 60.0% | 0.2955 | 0.50 |
| `B8_salmonella_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.5487 [0.5447-0.5529] | 0.5355 (22,332) | 0.1976 | 0.2598 | 43.2% | 59.5% | 40.0% | 40.6% | 60.0% | 0.2955 | 0.50 |
| `B8_campylobacter_nogenes_v6` | v6 | species_holdout | none | lightgbm | 0.4559 [0.4502-0.4617] | 0.4594 (7,734) | 0.1830 | 0.1670 | 47.8% | 28.0% | 52.3% | 72.0% | 47.7% | 0.2403 | 0.50 |
| `B8_campylobacter_nogenes` | v5 | species_holdout | none | lightgbm | 0.4562 [0.4503-0.4621] | 0.4597 (7,734) | 0.1830 | 0.1670 | 47.8% | 28.0% | 52.3% | 72.0% | 47.6% | 0.2631 | 0.50 |
| `B8_campylobacter_nogenes_v7` | v7 | species_holdout | none | lightgbm | 0.4559 [0.4502-0.4617] | 0.4594 (7,734) | 0.1830 | 0.1670 | 47.8% | 28.0% | 52.3% | 72.0% | 47.7% | 0.2403 | 0.50 |
| `L_species_kmer4_lgbm` | v5 | lineage | none | lightgbm | 0.5446 [0.5446-0.5446] | n/a | 0.1718 | 0.2575 | 71.8% | 38.6% | 76.7% | 61.5% | 23.3% | 0.1839 | 0.50 |
| `L_species_nogenes` | v5 | lineage | none | lightgbm | 0.5440 [0.5440-0.5440] | n/a | 0.1622 | 0.2317 | 68.0% | 38.1% | 72.3% | 61.9% | 27.7% | 0.2068 | 0.50 |
| `L_species_taxonomy` | v5 | lineage | none | lightgbm | 0.5000 [0.5000-0.5000] | n/a | 0.1267 | 0.0000 | 87.3% | 0.0% | 100.0% | 100.0% | 0.0% | 0.2062 | 0.50 |

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
- `B6L_genes` - B6 on the lab-tested genome set: genes (in >= 50 genomes) + drug-aware features + antibiotic, drug class, genus
- `B6L_base_drug` - Lab-tested genome set (v5, 24,844 genomes): antibiotic only
- `B6L_base_taxonomy` - Lab-tested genome set: antibiotic + genus + species, no genome features
- `B6L_nogenes` - Lab-tested genome set: antibiotic + drug class + genus (B6 without genes)
- `B6L_genes_only` - Genes and drug-aware features + antibiotic and drug class only, no genus: does the gene signal stand alone?
- `B8_acinetobacter_genes` - B8: train without Acinetobacter, test only on it (with gene features)
- `B8_acinetobacter_nogenes` - B8: train without Acinetobacter, test only on it (without gene features)
- `B8_campylobacter_genes` - B8: train without Campylobacter, test only on it (with gene features)
- `B8_campylobacter_nogenes` - B8: train without Campylobacter, test only on it (without gene features)
- `B8_klebsiella_genes` - B8: train without Klebsiella, test only on it (with gene features)
- `B8_klebsiella_nogenes` - B8: train without Klebsiella, test only on it (without gene features)
- `B8_neisseria_genes` - B8: train without Neisseria, test only on it (with gene features)
- `B8_neisseria_nogenes` - B8: train without Neisseria, test only on it (without gene features)
- `B8_pseudomonas_genes` - B8: train without Pseudomonas, test only on it (with gene features)
- `B8_pseudomonas_nogenes` - B8: train without Pseudomonas, test only on it (without gene features)
- `B8_salmonella_genes` - B8: train without Salmonella, test only on it (with gene features)
- `B8_salmonella_nogenes` - B8: train without Salmonella, test only on it (without gene features)
- `B8_shigella_genes` - B8: train without Shigella, test only on it (with gene features)
- `B8_shigella_nogenes` - B8: train without Shigella, test only on it (without gene features)
- `B4L_kmer4_lgbm` - B4 on the 24,926 genomes (v5): LightGBM on 4-mers + antibiotic + GC/length
- `B7L_genes_kmers` - B7 on the 24,926 genomes (v5): genes + 4-mers + antibiotic, drug class, genus
- `LL_clone_taxonomy` - Lineage check at scale, near-identical isolates held out: antibiotic + genus + species
- `LL_clone_kmer4` - Lineage check at scale, near-identical isolates held out: LightGBM on 4-mers
- `LL_clone_genes` - Lineage check at scale, near-identical isolates held out: genes + antibiotic, drug class, genus
- `LL_close_taxonomy` - Lineage check at scale, close lineages held out: antibiotic + genus + species
- `LL_close_kmer4` - Lineage check at scale, close lineages held out: LightGBM on 4-mers
- `LL_close_genes` - Lineage check at scale, close lineages held out: genes + antibiotic, drug class, genus
- `LL_broad_taxonomy` - Lineage check at scale, broad lineages held out: antibiotic + genus + species
- `LL_broad_kmer4` - Lineage check at scale, broad lineages held out: LightGBM on 4-mers
- `LL_broad_genes` - Lineage check at scale, broad lineages held out: genes + antibiotic, drug class, genus
- `B1L_kmer4_rf` - B1 on the 24,926 genomes (v5): RF on 4-mers + antibiotic + GC/length, genome-grouped
- `G_kmer_deploy` - Deploy candidate for /predict: LightGBM on 4-mers of the complete genome (v6, no plasmid records), threshold for VME <= 10% on validation
- `B4L_kmer4_lgbm_v6` - B4 on the 24,926 genomes : LightGBM on 4-mers + antibiotic + GC/length [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_base_drug_v6` - Lab-tested genome set : antibiotic only [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_base_taxonomy_v6` - Lab-tested genome set: antibiotic + genus + species, no genome features [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_only_v6` - Genes and drug-aware features + antibiotic and drug class only, no genus: does the gene signal stand alone? [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_v6` - B6 on the lab-tested genome set: genes (in >= 50 genomes) + drug-aware features + antibiotic, drug class, genus [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_nogenes_v6` - Lab-tested genome set: antibiotic + drug class + genus (B6 without genes) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B7L_genes_kmers_v6` - B7 on the 24,926 genomes : genes + 4-mers + antibiotic, drug class, genus [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_acinetobacter_genes_v6` - B8: train without Acinetobacter, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_acinetobacter_nogenes_v6` - B8: train without Acinetobacter, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_campylobacter_genes_v6` - B8: train without Campylobacter, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_campylobacter_nogenes_v6` - B8: train without Campylobacter, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_klebsiella_genes_v6` - B8: train without Klebsiella, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_klebsiella_nogenes_v6` - B8: train without Klebsiella, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_neisseria_genes_v6` - B8: train without Neisseria, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_neisseria_nogenes_v6` - B8: train without Neisseria, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_pseudomonas_genes_v6` - B8: train without Pseudomonas, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_pseudomonas_nogenes_v6` - B8: train without Pseudomonas, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_salmonella_genes_v6` - B8: train without Salmonella, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_salmonella_nogenes_v6` - B8: train without Salmonella, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_shigella_genes_v6` - B8: train without Shigella, test only on it (with gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B8_shigella_nogenes_v6` - B8: train without Shigella, test only on it (without gene features) [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_broad_genes_v6` - Lineage check at scale, broad lineages held out: genes + antibiotic, drug class, genus [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_broad_kmer4_v6` - Lineage check at scale, broad lineages held out: LightGBM on 4-mers [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_broad_taxonomy_v6` - Lineage check at scale, broad lineages held out: antibiotic + genus + species [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_clone_genes_v6` - Lineage check at scale, near-identical isolates held out: genes + antibiotic, drug class, genus [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_clone_kmer4_v6` - Lineage check at scale, near-identical isolates held out: LightGBM on 4-mers [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_clone_taxonomy_v6` - Lineage check at scale, near-identical isolates held out: antibiotic + genus + species [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_close_genes_v6` - Lineage check at scale, close lineages held out: genes + antibiotic, drug class, genus [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_close_kmer4_v6` - Lineage check at scale, close lineages held out: LightGBM on 4-mers [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `LL_close_taxonomy_v6` - Lineage check at scale, close lineages held out: antibiotic + genus + species [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_v6_withplasmids` - B6 on cleaning v6 keeping the plasmid-only records: measures what excluding them changes
- `B1L_kmer4_rf_v6` - B1 on the 24,926 genomes : RF on 4-mers + antibiotic + GC/length, genome-grouped [cleaning v6, plasmid-only records (< 500 kb) excluded]
- `D4_forecaster_deploy` - D3 on cleaning v6: the complete BV-BRC export (7.8 M rows, 439,542 genomes)
- `A12_species_holdout_v7` - A12_species_holdout on cleaning v7 (the complete BV-BRC export); compare with the v5 run A12_species_holdout
- `D3_forecaster_deploy_v7` - D3_forecaster_deploy on cleaning v7 (the complete BV-BRC export); compare with the v5 run D3_forecaster_deploy
- `A1_oof_random_v7` - A1_oof_random on cleaning v7 (the complete BV-BRC export); compare with the v5 run A1_oof_random
- `A0_baseline_leaky_v7` - A0_baseline_leaky on cleaning v7 (the complete BV-BRC export); compare with the v5 run A0_baseline_leaky
- `B6R_gene_rule_class_v7` - Gene-lookup rule, nothing learned: resistant when the genome carries an AMRFinderPlus gene or point mutation of the drug's class. Same genomes and split as B6L_genes_v6 [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6R_gene_rule_key_v7` - Gene-lookup rule, nothing learned: resistant when the genome carries a named key determinant for the drug (genes.py KEY_DETERMINANTS, 16 drugs; other drugs score 0). Same genomes and split as B6L_genes_v6 [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_v7` - B6 on the lab-tested genome set: genes (in >= 50 genomes) + drug-aware features + antibiotic, drug class, genus [cleaning v7, plasmid-only records (< 500 kb) excluded]; same run as B6L_genes_v6 on v7, for the per-drug comparison with the gene-lookup rules (B6R)
- `A_ablation_no_mic_v7` - A_ablation_no_mic on cleaning v7 (the complete BV-BRC export); compare with the v5 run A_ablation_no_mic
- `A10s_monotonic_species_v7` - A10s_monotonic_species on cleaning v7 (the complete BV-BRC export); compare with the v5 run A10s_monotonic_species
- `A2b_no_encoding_v7` - A2b_no_encoding on cleaning v7 (the complete BV-BRC export); compare with the v5 run A2b_no_encoding
- `A3_logistic_v7` - A3_logistic on cleaning v7 (the complete BV-BRC export); compare with the v5 run A3_logistic
- `A3b_lgbm_same_sample_v7` - A3b_lgbm_same_sample on cleaning v7 (the complete BV-BRC export); compare with the v5 run A3b_lgbm_same_sample
- `A4_random_forest_v7` - A4_random_forest on cleaning v7 (the complete BV-BRC export); compare with the v5 run A4_random_forest
- `A5_xgboost_v7` - A5_xgboost on cleaning v7 (the complete BV-BRC export); compare with the v5 run A5_xgboost
- `A5b_catboost_v7` - A5b_catboost on cleaning v7 (the complete BV-BRC export); compare with the v5 run A5b_catboost
- `A5c_catboost_native_v7` - A5c_catboost_native on cleaning v7 (the complete BV-BRC export); compare with the v5 run A5c_catboost_native
- `A9_threshold_f1_v7` - A9_threshold_f1 on cleaning v7 (the complete BV-BRC export); compare with the v5 run A9_threshold_f1
- `LC_100k_v7` - LC_100k on cleaning v7 (the complete BV-BRC export); compare with the v5 run LC_100k
- `LC_200k_v7` - LC_200k on cleaning v7 (the complete BV-BRC export); compare with the v5 run LC_200k
- `LC_400k_v7` - LC_400k on cleaning v7 (the complete BV-BRC export); compare with the v5 run LC_400k
- `LC_50k_v7` - LC_50k on cleaning v7 (the complete BV-BRC export); compare with the v5 run LC_50k
- `LC_800k_v7` - LC_800k on cleaning v7 (the complete BV-BRC export); compare with the v5 run LC_800k
- `T0_grouped_withyear_v7` - Grouped twin of the T1 temporal runs: A6 on the same rows (lab, genomes with a collection year), random genome-grouped split [cleaning v7]
- `T1_temporal_2014_v7` - Temporal test (RESEARCH_PLAN section 8): A6 (lab rows, OOF rate features) trained on genomes collected up to 2014, tested on genomes collected after 2014; genomes without a collection year dropped [cleaning v7]
- `T1_temporal_2012_v7` - Temporal test (RESEARCH_PLAN section 8): A6 (lab rows, OOF rate features) trained on genomes collected up to 2012, tested on genomes collected after 2012; genomes without a collection year dropped [cleaning v7]
- `T1_temporal_2015_v7` - Temporal test (RESEARCH_PLAN section 8): A6 (lab rows, OOF rate features) trained on genomes collected up to 2015, tested on genomes collected after 2015; genomes without a collection year dropped [cleaning v7]
- `B1L_kmer4_rf_v7` - B1 on the 24,926 genomes : RF on 4-mers + antibiotic + GC/length, genome-grouped [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B4L_kmer4_lgbm_v7` - B4 on the 24,926 genomes : LightGBM on 4-mers + antibiotic + GC/length [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_base_drug_v7` - Lab-tested genome set : antibiotic only [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_base_taxonomy_v7` - Lab-tested genome set: antibiotic + genus + species, no genome features [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_only_v7` - Genes and drug-aware features + antibiotic and drug class only, no genus: does the gene signal stand alone? [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_nogenes_v7` - Lab-tested genome set: antibiotic + drug class + genus (B6 without genes) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B7L_genes_kmers_v7` - B7 on the 24,926 genomes : genes + 4-mers + antibiotic, drug class, genus [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_acinetobacter_genes_v7` - B8: train without Acinetobacter, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_acinetobacter_nogenes_v7` - B8: train without Acinetobacter, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_campylobacter_genes_v7` - B8: train without Campylobacter, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_campylobacter_nogenes_v7` - B8: train without Campylobacter, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_klebsiella_genes_v7` - B8: train without Klebsiella, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_klebsiella_nogenes_v7` - B8: train without Klebsiella, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_neisseria_genes_v7` - B8: train without Neisseria, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_neisseria_nogenes_v7` - B8: train without Neisseria, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_pseudomonas_genes_v7` - B8: train without Pseudomonas, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_pseudomonas_nogenes_v7` - B8: train without Pseudomonas, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_salmonella_genes_v7` - B8: train without Salmonella, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_salmonella_nogenes_v7` - B8: train without Salmonella, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_shigella_genes_v7` - B8: train without Shigella, test only on it (with gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B8_shigella_nogenes_v7` - B8: train without Shigella, test only on it (without gene features) [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_broad_kmer4_v7` - Lineage check at scale, broad lineages held out: LightGBM on 4-mers [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_broad_taxonomy_v7` - Lineage check at scale, broad lineages held out: antibiotic + genus + species [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_clone_genes_v7` - Lineage check at scale, near-identical isolates held out: genes + antibiotic, drug class, genus [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_clone_kmer4_v7` - Lineage check at scale, near-identical isolates held out: LightGBM on 4-mers [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_clone_taxonomy_v7` - Lineage check at scale, near-identical isolates held out: antibiotic + genus + species [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_close_genes_v7` - Lineage check at scale, close lineages held out: genes + antibiotic, drug class, genus [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_close_kmer4_v7` - Lineage check at scale, close lineages held out: LightGBM on 4-mers [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `LL_close_taxonomy_v7` - Lineage check at scale, close lineages held out: antibiotic + genus + species [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `B6L_genes_v7_s1` - B6L_genes_v7 with split seed 1 (seed 42 is B6L_genes_v7): seed variation for T2.5
- `B6L_genes_v7_s2` - B6L_genes_v7 with split seed 2 (seed 42 is B6L_genes_v7): seed variation for T2.5
- `A6_lab_only_v7` - A6_lab_only on cleaning v7 (the complete BV-BRC export); compare with the v5 run A6_lab_only
- `A6b_lab_only_no_mic_v7` - A6b_lab_only_no_mic on cleaning v7 (the complete BV-BRC export); compare with the v5 run A6b_lab_only_no_mic
- `A6_lab_only_v7_s1` - A6_lab_only_v7 with split seed 1 (seed 42 is A6_lab_only_v7): seed variation for T2.5
- `A6_lab_only_v7_s2` - A6_lab_only_v7 with split seed 2 (seed 42 is A6_lab_only_v7): seed variation for T2.5
- `A6b_lab_only_no_mic_v7_s1` - A6b_lab_only_no_mic_v7 with split seed 1 (seed 42 is A6b_lab_only_no_mic_v7): seed variation for T2.5
- `A6b_lab_only_no_mic_v7_s2` - A6b_lab_only_no_mic_v7 with split seed 2 (seed 42 is A6b_lab_only_no_mic_v7): seed variation for T2.5
- `A_ablation_drug_only_v7` - A_ablation_drug_only on cleaning v7 (the complete BV-BRC export); compare with the v5 run A_ablation_drug_only
- `A_ablation_drug_only_v7_s1` - A_ablation_drug_only_v7 with split seed 1 (seed 42 is A_ablation_drug_only_v7): seed variation for T2.5
- `A_ablation_drug_only_v7_s2` - A_ablation_drug_only_v7 with split seed 2 (seed 42 is A_ablation_drug_only_v7): seed variation for T2.5
- `A2_oof_grouped_v7` - A2_oof_grouped on cleaning v7 (the complete BV-BRC export); compare with the v5 run A2_oof_grouped
- `A2_oof_grouped_v7_s1` - A2_oof_grouped_v7 with split seed 1 (seed 42 is A2_oof_grouped_v7): seed variation for T2.5
- `A2_oof_grouped_v7_s2` - A2_oof_grouped_v7 with split seed 2 (seed 42 is A2_oof_grouped_v7): seed variation for T2.5
- `A10_monotonic_mic_v7` - A10_monotonic_mic on cleaning v7 (the complete BV-BRC export); compare with the v5 run A10_monotonic_mic
- `A10_monotonic_mic_v7_s1` - A10_monotonic_mic_v7 with split seed 1 (seed 42 is A10_monotonic_mic_v7): seed variation for T2.5
- `A10_monotonic_mic_v7_s2` - A10_monotonic_mic_v7 with split seed 2 (seed 42 is A10_monotonic_mic_v7): seed variation for T2.5
- `LL_broad_genes_v7` - Lineage check at scale, broad lineages held out: genes + antibiotic, drug class, genus [cleaning v7, plasmid-only records (< 500 kb) excluded]
- `G_genes_deploy` - Deploy candidate for /predict: LightGBM on AMRFinderPlus genes and drug-aware gene features + antibiotic and drug class (no genus: an upload does not come with one), cleaning v7, no plasmid records, threshold for VME <= 10% on validation
- `LT_A2_grouped_v7` - Lineage check for the tabular model A2_oof_grouped_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), genome-grouped split (the twin of the lineage runs, same rows) [cleaning v7]
- `LT_A2_close_v7` - Lineage check for the tabular model A2_oof_grouped_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), lineage split, close cut: no close-lineage cluster on both sides [cleaning v7]
- `LT_A2_broad_v7` - Lineage check for the tabular model A2_oof_grouped_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), lineage split, broad cut: no broad-lineage cluster on both sides [cleaning v7]
- `LT_D3_grouped_v7` - Lineage check for the tabular model D3_forecaster_deploy_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), genome-grouped split (the twin of the lineage runs, same rows) [cleaning v7]
- `LT_D3_close_v7` - Lineage check for the tabular model D3_forecaster_deploy_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), lineage split, close cut: no close-lineage cluster on both sides [cleaning v7]
- `LT_D3_broad_v7` - Lineage check for the tabular model D3_forecaster_deploy_v7 (Research track): its config on the 24,926 genomes with lineage clusters (no plasmid records), lineage split, broad cut: no broad-lineage cluster on both sides [cleaning v7]

