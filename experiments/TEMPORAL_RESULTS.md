# Temporal test: does the forecaster work on bacteria collected later?

RESEARCH_PLAN section 8. Train on genomes collected up to a cut-off year, test on genomes collected after it. A random genome-grouped split mixes years on both sides, so it can't show whether a model still works on bacteria from after its training data. This test can.

**Setup.** Model A6 (LightGBM on lab-confirmed rows, out-of-fold rate features, threshold 0.40), cleaning v7. Collection years come from Ali's `Data/genome_meta/genome_meta.csv` (`collection_year`, or else the year in `collection_date`), joined on Genome ID as text. 75,284 of the 87,325 lab-tested genomes have a year (571,202 of 649,944 lab rows; 1922–2022, median 2013). Genomes without a year are left out of both sides. The grouped twin `T0` runs on the same rows with a random genome-grouped split. Configs: `experiments/configs/T0_*`, `T1_*`; split code: `split.strategy = "temporal"` in `experiments/lib/splits.py`.

## Overall

| Run | Train: genomes up to | Train rows | Test rows | AUC [95% CI] | AUPRC | VME | ME | Brier |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `T0_grouped_withyear_v7` | any year (random genome split) | 456,961 | 114,241 | **0.928** [0.925–0.931] | 0.891 | 11.2% | 23.2% | 0.107 |
| `T1_temporal_2012_v7` | 2012 | 252,489 | 318,713 | **0.878** [0.875–0.881] | 0.824 | 19.1% | 24.1% | 0.151 |
| `T1_temporal_2014_v7` | 2014 | 345,157 | 226,045 | **0.857** [0.855–0.860] | 0.767 | 23.0% | 23.2% | 0.154 |
| `T1_temporal_2015_v7` | 2015 | 401,605 | 169,597 | **0.857** [0.854–0.860] | 0.747 | 20.2% | 25.8% | 0.153 |

On later bacteria AUC falls by 0.05–0.07, and at the same threshold the share of resistant isolates missed (VME) roughly doubles. More training years don't close the gap: the 2015 cut-off trains on 60% more rows than 2012 and scores lower, because its test set is the harder later years.

## By test year (AUC, years with at least 1,000 test rows)

| Test year | Cut-off 2012 | Cut-off 2014 | Cut-off 2015 | Grouped split |
| --- | --- | --- | --- | --- |
| 2013 | 0.938 | | | 0.955 |
| 2014 | 0.936 | | | 0.961 |
| 2015 | 0.847 | 0.868 | | 0.926 |
| 2016 | 0.864 | 0.876 | 0.885 | 0.942 |
| 2017 | 0.816 | 0.820 | 0.823 | 0.962 |
| 2018 | 0.817 | 0.820 | 0.817 | 0.952 |
| 2019 | 0.942 | 0.957 | 0.964 | 0.980 |
| 2020 | 0.796 | 0.823 | 0.865 | 0.964 |
| 2021 | 0.904 | 0.909 | 0.918 | 0.948 |
| 2022 | 0.966 | 0.966 | 0.961 | |

The loss doesn't grow steadily with distance from the cut-off. It is concentrated in particular years: 2017 and 2018 score about 0.82 whatever the cut-off, while the same years score 0.95–0.96 when the model has seen genomes from them.

## Where it fails: within-genus drift

2017–2018 test rows, cut-off 2014, against the grouped split's AUC for the same genus (all years):

| Year | Genus | Test rows | Temporal | Grouped |
| --- | --- | --- | --- | --- |
| 2017 | *Shigella* | 3,439 | 0.507 | 0.854 |
| 2017 | *Neisseria* | 14,177 | 0.744 | 0.911 |
| 2017 | *Escherichia* | 6,901 | 0.782 | 0.858 |
| 2017 | *Salmonella* | 5,321 | 0.816 | 0.920 |
| 2018 | *Salmonella* | 14,628 | 0.771 | 0.920 |
| 2018 | *Klebsiella* | 4,999 | 0.790 | 0.971 |
| 2018 | *Staphylococcus* | 7,839 | 0.808 | 0.870 |
| 2017 | *Klebsiella* | 5,368 | 0.976 | 0.971 |
| 2018 | *Mycobacterium* | 11,676 | 0.929 | 0.883 |

The failures are in the genera where resistance spread after the training years (e.g. *Shigella* and *Neisseria* in the late 2010s). The metadata model learns each organism's and drug's historical resistance rate, so when that rate shifts it has nothing to go on. Genera with stable resistance (*Mycobacterium*, *Streptococcus*, *Klebsiella* in 2017) hold up.

## What to quote

- A random genome-grouped split overstates performance on future bacteria: 0.928 vs 0.857–0.878 for the same model on the same genomes.
- The served forecaster's headline (0.774 on all rows) comes from a grouped split. It should be read as "unseen genomes from the same period", not "the future".
- The genome models (k-mers, genes) read the resistance mechanism, not a historical rate, so they may transfer better over time. That is the next temporal test, on the 24,926 genomes that have k-mers and genes (Paper B).

Caveats: years are BV-BRC metadata, empty for 14% of lab-tested genomes; DeLong and the bootstrap don't apply between runs with different test sets, so the comparison above rests on the per-run CIs (which don't overlap).
