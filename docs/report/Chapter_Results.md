# Chapter: Results

*Hamza Afzal (models). Every number in this chapter comes from a run saved in `experiments/results/` (configuration in `experiments/configs/`, produced by `experiments/run.py`) or from the scripts named beside it; `notebooks/01`–`04` reproduce the served models and the checks with their outputs.*

## 1. How the models were evaluated

| Choice | What we did | Why |
|---|---|---|
| Data | Complete BV-BRC AMR export, cleaning v7: 7,847,110 rows, 439,542 genomes; 649,944 laboratory-confirmed rows on 87,325 genomes | The first models used a 3,655-file subset |
| Split | **By genome**: no genome is in both training and test (80/20), also for the inner folds and the validation slice | Each genome is tested on about 18 antibiotics; a row split leaks the genome (section 2) |
| Headline rows | All test rows, and **lab-confirmed rows** separately | Most BV-BRC labels were predicted by computer from the genome; genome models could score by re-deriving them |
| Threshold | Chosen on validation genomes, never on test: for the served models, the highest threshold that misses at most 10% of resistant isolates (very major error, VME ≤ 10%) | A missed resistance is the costly error |
| Uncertainty | 95% CI by bootstrap over genomes; 3 split seeds; DeLong and McNemar tests and a paired genome bootstrap between models | A single AUC cannot show that one model beats another |
| Extra tests | Lineage split (related bacteria held out), unseen genus, temporal split (bacteria collected after the training years) | Whether the models generalise beyond the genomes they resemble |

## 2. The first model's AUC was a leak

The July forecaster reported AUC 0.93 from a random row split. Re-tested (`experiments/evaluate_shipped.py`):

| Model | Genomes it trained on | Genomes it never saw |
|---|---|---|
| July forecaster (random row split) | 0.941 | **0.644** |
| July k-mer RandomForest (partial genomes) | 0.981 | **0.695** |
| Served forecaster `D3_forecaster_deploy_v7` | 0.764 | **0.762** |
| Served k-mer model `G_kmer_deploy` (lab rows) | 0.960 | **0.935** |

The served models score about the same on genomes they saw and genomes they did not: their numbers describe new bacteria. Every result below is on genomes never seen in training.

## 3. The resistance forecaster (metadata + MIC)

**Served model `D3_forecaster_deploy_v7`**: LightGBM on 14 features (antibiotic, drug class, organism at species level, MIC value and sign, provenance, out-of-fold resistance rates per drug, organism-drug and genus-drug), a monotone MIC effect, isotonic calibration.

| On 1,569,432 test rows of unseen genomes | All rows | Lab-confirmed rows (129,633) |
|---|---|---|
| AUC-ROC [95% CI] | **0.774** [0.772, 0.775] | **0.908** |
| Recall (resistant caught) | 91.4% | 95.1% |
| Very major error (resistant missed) | 8.6% | 4.9% |
| Major error (susceptible called resistant) | 60.8% | 42.8% |
| Brier score (calibration) | 0.193 → **0.160** after isotonic calibration | 0.109 |

The low specificity is the price of the VME ≤ 10% rule at threshold 0.15.

**What the experiments show** (all on the same split by genome unless stated):

| Experiment | Run | AUC | Finding |
|---|---|---|---|
| Leaky target encoding, random split | A0 | 0.787 | The old pipeline's leakage inflates even here |
| Out-of-fold encoding, random split | A1 | 0.786 | |
| **Out-of-fold encoding, split by genome** | **A2** | **0.785** [0.783, 0.787] | Best all-row model |
| No target encoding | A2b | 0.784 | Encoding adds little once organism is a feature |
| Monotone MIC (A10) / + species taxa (A10s) | A10, A10s | 0.785, 0.774 | The rule costs nothing (A10 vs A2: −0.0004, McNemar p = 0.14) |
| Logistic regression (80k-row sample) | A3 | 0.765 | Tree ensembles win |
| LightGBM / random forest / XGBoost / CatBoost (same sample) | A3b, A4, A5, A5b | 0.780 / 0.777 / 0.779 / 0.780 | The algorithm matters less than the data (within 0.003) |
| Drug only | ablation | 0.657 | |
| Everything but the MIC | ablation | 0.775 | The MIC adds +0.010 on all rows |
| Lab rows only, with / without MIC | A6, A6b | **0.923** / 0.840 | The MIC adds **+0.083** on lab rows (p < 0.0001) |
| A genus never seen (Klebsiella held out) | A12 | 0.618 | The forecaster does not transfer to new organisms |
| Learning curve, 50k → 800k training rows | LC | 0.776 → 0.783 | More of the same rows barely helps |

**Seeds** (split seeds 42, 1, 2): A2 0.7849 ± 0.0005, A10 0.7845 ± 0.0005, A6 0.9214 ± 0.0012, A6b 0.8376 ± 0.0024, drug only 0.6569 ± 0.0004. No result depends on the split.

## 4. The genome models (complete genomes)

Data: 24,926 complete genomes downloaded from BV-BRC (24,719 after removing plasmid-only records); 40,356 lab test rows from 4,481 unseen genomes.

| Model | Features | Lab AUC [95% CI] |
|---|---|---|
| Antibiotic only | | 0.715 [0.708, 0.720] |
| Gene-lookup rule (resistant if a gene of the drug's class is present) | AMRFinderPlus | 0.711 |
| Antibiotic, genus, species | | 0.849 [0.842, 0.855] |
| Old design: RandomForest on 4-mers | k-mers | 0.867 [0.861, 0.873] |
| **k-mer model**, LightGBM on 4-mers (served without AMRFinderPlus) | k-mers | **0.935** [0.931, 0.939] |
| **Gene model** `G_genes_deploy` (served with AMRFinderPlus) | genes, no genus | **0.977** [0.975, 0.979] |
| Genes + genus (B6, best experiment) | genes | 0.979 [0.977, 0.981]; 0.9789 ± 0.0004 over 3 seeds |
| Genes + k-mers (B7) | both | 0.981 [0.979, 0.982] |

- **Genes beat k-mers** by +0.0445 (DeLong 95% CI [+0.043, +0.046], p < 0.0001; genome bootstrap [+0.041, +0.048]; McNemar: 4,054 rows only the gene model gets right, 1,069 only the k-mer model). Genes beat taxonomy by +0.130 and the drug alone by +0.264.
- **Adding k-mers to genes** gains +0.002 (genome bootstrap [+0.001, +0.003]): real, negligible.
- **The rule vs the model:** the learned gene model beats the lookup rule on 45 of 46 drugs; knowing which genes matter for which drug is what the model learns.
- **Served gene model:** threshold 0.58, VME 10.2%, major error 5.1% (k-mer model: 9.6% and 19.5%). The website's feature code reproduces the training run's features exactly (3,600 genome-drug rows) and its probabilities (400 rows); verified with real AMRFinderPlus in the Docker image by CI.

**Generalisation.** A genus never seen in training (7 genera held out in turn): 0.82–0.94 with genes, 0.46–0.75 without. Related bacteria held out (lineage clusters by 6-mer distance), lab AUC by genome / close lineages / broad lineages: genes 0.979 / 0.979 / 0.965, k-mers 0.933 / 0.926 / 0.900, taxonomy 0.851 / 0.853 / 0.816. Gene features carry the resistance mechanism; k-mers carry composition, which partly identifies the lineage.

## 5. Generalisation of the forecaster

| Test | Lab AUC (A2 design / served D3 design) |
|---|---|
| Split by genome (24,926 genomes with lineage clusters) | 0.968 / 0.962 |
| Close lineages held out | 0.967 / 0.962 |
| Broad lineages held out | 0.961 / 0.961 |

Holding related bacteria out costs at most 0.007: the split by genome does not flatter the forecaster through relatives.

**Bacteria collected after the training years** (A6 on lab rows with a collection year; `experiments/TEMPORAL_RESULTS.md`):

| Training data | Test | AUC [95% CI] | VME |
|---|---|---|---|
| Random split, same genomes | mixed years | 0.928 [0.925, 0.931] | 11.2% |
| Collected up to 2012 | after 2012 | 0.878 [0.875, 0.880] | 19.1% |
| Up to 2014 | after 2014 | 0.857 [0.855, 0.860] | 23.0% |
| Up to 2015 | after 2015 | 0.857 [0.854, 0.860] | 20.2% |

AUC falls by 0.05–0.07 on future bacteria and the missed resistances double. The loss sits in 2017–2018 and inside genera where resistance spread after the training years (*Shigella* 0.51, *Neisseria* 0.74, *Salmonella* 0.77 in those years): a forecaster that learns historical rates cannot see a new resistance coming.

## 6. The timeline ML model

The supervisor asked for the timeline as a trained model rather than the simulation's equations. `experiments/timeline_ml/timeline_model.py` builds, from the 553,223 lab results with a collection year (2000–2022), the yearly resistant share of each genus and antibiotic (a year counts with at least 20 results): **2,619 year points in 467 series**. LightGBM predicts a year's share from the years before it only (last values, recent slope, gap, history length, the number of results, genus, antibiotic, drug class), as a change from the last value. Trained on years up to 2016, tested on 2017–2022 (411 forecasts, 191 series).

| Method | Mean absolute error, percentage points [95% CI, resampling series] |
|---|---|
| **Timeline ML model** | **13.98** [11.84, 16.33] |
| Last value | 14.33 [12.16, 16.73] |
| Linear trend | 16.75 [14.32, 19.30] |
| Historical mean | 17.25 [15.07, 19.67] |

The model beats all three baselines: by 0.35 pp over the last value (95% CI [+0.03, +0.67]), 2.77 pp over the trend and 3.28 pp over the mean. The absolute error is large because a year of BV-BRC data is a small, uneven sample. On the ECDC European series of *K. pneumoniae* and carbapenems (30 countries, 231 forecasts, never seen in training) the model (2.32 pp) is slightly worse than the last value (1.89 pp): smooth, well-sampled surveillance data favour persistence. The website shows the forecast beside the simulation, with an 80% band from the held-out errors (`/api/timeline/` → `ml_forecast`).

## 7. The GAN experiment

The proposal asked whether GAN-generated data helps. CTGAN (a GAN for tabular data) was fitted on the **training rows** of A6's split for the rare classes: 62 antibiotics and 21 genera with fewer than 1,000 training rows each (21,030 rows, 60 epochs; `experiments/gan/ctgan_augment.py`). 21,030 synthetic rows were added to the training side of A13; the test set is real and identical to A6's, so the two compare row by row (`experiments/gan/results/GAN_RESULTS.md`).

| Test rows | Rows | AUC without GAN rows (A6) | AUC with GAN rows (A13) | Difference [genome bootstrap 95% CI] | DeLong p |
|---|---|---|---|---|---|
| All test rows | 129,992 | 0.9227 | 0.9222 | −0.0005 [−0.0007, −0.0002] | < 0.0001 |
| Rare antibiotics or genera | 5,083 | 0.9402 | 0.9323 | **−0.0080** [−0.0115, −0.0048] | < 0.0001 |

**The synthetic rows did not help; they slightly hurt, most on the rare classes they were made for.** The quality checks explain why: a classifier separates real from synthetic rows almost perfectly (AUC 0.9999); the category distributions differ (total variation 0.26–0.44 per column, except the resistant share, 0.03) and so does the MIC (Kolmogorov–Smirnov 0.29); and only 17% of sampled rows were biologically consistent (the rest paired a drug with another drug's class or a species with another genus). With 21,030 rows spread over 62 drugs and 21 genera, CTGAN cannot learn the joint structure of drug, organism, MIC and phenotype well enough to add information. Conclusion for the report: on this problem, more real data (the 87,325 lab-tested genomes) is the way to help rare classes, not synthetic rows.

## 8. Limitations

- The overall forecaster AUC (0.774) is held down by computational labels; on lab-confirmed rows it is 0.908.
- The forecaster does not transfer to an unseen genus (0.618) or fully to future years (0.857); the genome models transfer better to new genera (0.82–0.94 with genes).
- The genome models were trained on 24,926 genomes; retraining on all 87,325 lab-tested genomes is future work.
- The timeline ML model forecasts noisy yearly samples (about 14 pp error) and does not beat persistence on smooth surveillance data.
- The GAN experiment is negative: CTGAN rows were easy to tell from real ones and lowered the AUC on rare classes.
- The simulation (and the RL agent trained on it) uses hand-set curves; its time scale is illustrative.
