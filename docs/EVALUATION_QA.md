# Evaluation answers: ML and data science questions

*For the FYP-II evaluation. Each answer: what to say, the exact numbers, and what to show. All numbers are from the code and the saved runs; [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) says which notebook reproduces each one.*

---

## Part A. The questions on the evaluator's sheet

### A1. Preprocessing: show the code

**Say:** The raw BV-BRC export (17,585,506 records) is cleaned by one function, `clean()` in `experiments/lib/data_prep.py`, in six steps:
1. Keep records with a resistance call; label Resistant, Intermediate, Nonsusceptible and Reduced Susceptibility as 1, and Susceptible as 0.
2. Split the MIC into a sign and a value, and add log(1 + MIC). Disk-diffusion zone sizes (mm) get no MIC.
3. Take genus and species from the genome name; map strain-level taxon IDs to species level (NCBI).
4. Normalise antibiotic names (40 spellings renamed, 10 non-drugs dropped) and map each drug to its class.
5. Record whether each label came from a lab or was predicted by BV-BRC's computational tools.
6. Keep one row per genome and antibiotic, preferring a lab result.

**Result:** 7,847,110 rows (649,944 lab-confirmed), 439,542 genomes, 126 antibiotics, 23 drug classes, 40 genera.

**Show:** `notebooks/00_preprocessing.ipynb`: §2–7 show each step on 1.5 million real raw records, §8 the function, and §9 the 13 report figures recomputed, all ✓.

### A2. Patches?

**Say:** We have no images, so no patches. The DNA equivalent of patches is **k-mers**: a sliding window of 4 bases over every contig of the genome. That gives 4⁴ = 256 possible 4-mers, whose frequencies form the k-mer model's input vector. The gene model uses whole genes instead, found by NCBI AMRFinderPlus.

**Show:** `00_preprocessing.ipynb` §10 (a 4.9 Mb genome → 259 features), and `experiments/genome/kmers.py`.

### A3. Feature engineering: vectorisation? Separate, or inside the model?

**Say:** It is a **separate step before the model**: the features are designed by hand, not learned by the model. The model then learns how the features interact.

| Model | Vectorisation (before the model) |
|---|---|
| Forecaster | 14 features. Categories (antibiotic, drug class, genus, species) stay categorical: LightGBM splits on them natively, so there is no one-hot encoding. MIC as value, sign and log. Three **out-of-fold target encodings** (the resistance rate of the drug, of organism + drug, and of genus + drug), computed with 5 folds so a row never sees its own label |
| k-mer model | 256 4-mer frequencies + GC content + genome length + antibiotic = 259 features |
| Gene model | 0/1 presence of each AMRFinderPlus gene or mutation found in ≥ 50 genomes, plus drug-aware counts (genes of the drug's class, mutations, key determinant, efflux) + antibiotic and drug class = 358 features |
| Timeline ML | Per year, from **earlier years only**: last 3 values, gap, recent slope, historical mean, history length, results behind the last value, genus, antibiotic, drug class = 11 features |

### A4. The 3 models: main architectural differences

| | Forecaster | Genome models (gene / k-mer) | Timeline ML model |
|---|---|---|---|
| Question | Will this isolate resist? | Will this genome resist? | What will the resistant % be next year? |
| Input | Lab metadata + MIC | Complete genome (FASTA) | Yearly series of a genus + drug |
| Task | Binary classification | Binary classification | **Regression** (the change from last year's value) |
| Algorithm | LightGBM, 499 trees, 63 leaves, learning rate 0.05 | LightGBM, 500 trees, same settings | LightGBM, 73 trees, 15 leaves, learning rate 0.03 |
| Loss | Binary log-loss | Binary log-loss | L1 (mean absolute error) |
| Special | Monotone MIC constraint; isotonic calibration | Gene model needs AMRFinderPlus; k-mer model is the fallback | Recursive multi-year forecast; 80% band |
| Threshold | 0.15 | 0.58 (gene) / 0.43 (k-mer) | — |
| Training data | 6,277,678 rows, 351,442 genomes | 287,774 rows, 19,804 genomes | 1,413 year targets (up to 2016) |
| Test result | AUC 0.774; 0.908 on lab rows | Lab AUC 0.977 / 0.935 | MAE 13.98 pp (2017–2022) |

The other two models are different in kind:
- **RL agent:** a neural network (MLP 64-64, tanh) trained with PPO in a simulation.
- **CTGAN:** a generator and a discriminator, used only in the GAN experiment.

### A5. Training: transfer learning? Freezing layers?

**Say:** **No.** Every model is trained from scratch.

Why not:
- **Gradient-boosted trees have no layers.** Each tree is added to correct the previous ones, so there is nothing to freeze.
- **No suitable pretrained model:** there is none for resistance from lab metadata, and none that our data could fine-tune within the project.
- **Expert knowledge comes in differently:** the gene model gets it through AMRFinderPlus's curated database of resistance genes, not through pretrained weights.

**Future work:** fine-tuning a pretrained DNA language model (e.g. DNABERT) on genomes: freeze the lower layers and train a classification head. Our k-mer and gene features would be its baselines.

**Training procedure (all LightGBM models):**
1. Split **by genome**: 80% train, 20% test.
2. One-sixth of the training genomes is a validation set, used for early stopping (30 rounds without AUC gain).
3. For the forecaster, the validation set is halved: one half fits the isotonic calibration, the other chooses the threshold.
4. The test set is used once, at the end.

### A6. Classes: how many?

**Say:** **2 output classes**, Resistant (1) and Susceptible (0).

- BV-BRC has 6 usable phenotype labels. Intermediate, Nonsusceptible and Reduced Susceptibility count as Resistant, because missing a resistance is the worse error.
- One model covers **all 126 antibiotics**: the antibiotic is an input feature, not a separate model per drug.
- The **23 drug classes** are an input feature, not output classes.
- Class balance: 28.0% resistant overall, 33.7% in lab rows.

### A7. DNA or RNA?

**Say:** **DNA**: complete genome assemblies in FASTA format from BV-BRC (24,926 downloaded, 24,719 after removing plasmid-only records). We use no RNA or gene-expression data. Resistance is read from the DNA: acquired genes, point mutations and k-mer composition.

---

## Part B. Your questions

### B1. Why does the timeline show only 2 organisms for oxacillin?

**Say:** The dropdown lists only organisms with **enough dated lab history** for that drug. A year counts when it has **≥ 20 lab results with a collection year**, and a series needs **≥ 2 such years** to be forecast.

For oxacillin only two genera qualify:
- **Staphylococcus**, 11 years (1,611 results). Oxacillin is the standard test for MRSA, so it's tested almost only on staphylococci.
- **Corynebacterium**, 3 years (97 results).

Streptococcus has 264 oxacillin lab rows, but too few per year to count. The pattern is common: 89 antibiotics have a forecastable series across 15 genera, and the median is 2 genera per drug. Gentamicin (13), tetracycline (11), ciprofloxacin (10) and meropenem (10) have the most.

**Rule in code:** `MIN_RESULTS = 20` and `MIN_HISTORY = 2` in `experiments/timeline_ml/timeline_model.py`; the list is built by `timeline_genera()` in `backend/api/views.py`.

### B2. How are the models integrated into the backend?

1. **Train** in `experiments/` (e.g. `python experiments/run.py experiments/configs/D3_forecaster_deploy_v7.json`).
2. **Promote:** `experiments/promote.py` copies the chosen run's model file (`model.txt`), feature metadata and metrics into `backend/trained_models/`. Only promotion changes what the website serves.
3. **Load once at startup:**
   - Django's `ApiConfig.ready()` (`backend/api/apps.py`) calls `model_registry.init_models()`.
   - Each predictor (`backend/ml_models/lgbm_predictor.py`, `genome_predictor.py`, `mutation_timeline.py`) is created once and kept in memory (singletons).
   - `timeline_ml.py` and `rl_agent.py` are loaded on first use.
4. **Serve:** each REST endpoint (`backend/api/views.py`) gets the model from the registry and returns JSON. For example, `POST /api/forecast/` calls `get_lgbm().predict(...)`. The React site calls these endpoints.
5. **Check:**
   - `/api/health/` reports which models loaded.
   - The RL agent is served as a NumPy copy of its network, so the server needs no PyTorch.
   - `backend/tests/test_library_parity.py` checks that the `amrpredict` library gives the same answers as the backend.

### B3. What weights did we choose, and why?

| Weight | Where | Why |
|---|---|---|
| **Class weights**: `is_unbalance=True` | All LightGBM classifiers | Only 28% of rows are resistant. Weighting the classes by their frequency stops the loss being dominated by susceptible rows |
| **Sample weights**: √n | Timeline ML model | A year resting on many lab results counts more, but under a square root, so one huge year can't dominate |
| **Network weights**, RL agent | PPO policy (`policy.npz`, 3 layers) | Initialised orthogonally (stable-baselines3 default), then learned by PPO (Adam, learning rate 3×10⁻⁴) |
| **Network weights**, CTGAN | Generator and discriminator | Learned with Adam, learning rate 2×10⁻⁴ (the method's defaults) |
| **Pretrained weights** | None | Trained from scratch (A5) |

Two more points:
- **Trees have no weights:** a LightGBM model stores split thresholds and leaf values, saved in `model.txt`.
- **Label quality is a feature, not a weight:** BV-BRC's computational F1 score is an input to the forecaster.

### B4. What activation functions did we choose, and why?

| Model | Activation | Why |
|---|---|---|
| LightGBM classifiers | **No hidden activations** (trees). The output log-odds pass through a **sigmoid** to give a probability, then isotonic calibration | The binary log-loss objective uses the logistic link. Calibration makes "70%" mean 70% |
| Timeline ML model | **Identity** output (regression), clipped to 0–100% | It predicts a change in percentage points |
| RL agent | **tanh** in both hidden layers (64, 64). **Softmax** over the 3 drugs for the policy; linear value head | tanh is the PPO default in stable-baselines3: bounded and smooth, stable for small networks with orthogonal initialisation. Softmax gives a probability for each drug; serving takes the most likely one |
| CTGAN generator | **ReLU** with batch norm (residual blocks, 256-256). Outputs: **tanh** for numbers, **Gumbel-softmax** for categories | Gumbel-softmax makes sampling a category differentiable, so the generator can learn categorical columns |
| CTGAN discriminator | **LeakyReLU(0.2)** + dropout 0.5; WGAN-GP gradient penalty | LeakyReLU keeps a gradient for negative inputs, so the critic does not stop learning |

### B5. What augmentation techniques did we use, and why?

**Say:** One: a **CTGAN** (a GAN for tabular data). It generated extra training rows for rare cases: 62 antibiotics and 21 genera with fewer than 1,000 training rows.
- Fitted on training rows only; the test set stayed real.
- Settings: 60 epochs, batch 500; at most 30,000 rows fitted.
- 21,030 synthetic rows were used, after dropping inconsistent ones (e.g. a species of another genus).

**Result: negative.**
- **Detection AUC 0.9999:** a classifier could tell synthetic rows from real ones.
- **Rare rows:** AUC fell from 0.9402 to 0.9323 (−0.008, DeLong p < 0.001).
- **Served models:** none uses synthetic data, and the report says so.

**Not used, and why:**
- **Image augmentation:** we have no images; the image input was descoped.
- **SMOTE:** too memory-hungry on 6 million rows, and class weighting does the same job.
- **Reverse-complement k-mer merging:** planned (experiment B3), not run.

**Class imbalance is handled instead by:**
- class weighting (`is_unbalance`);
- a threshold chosen so that at most 10% of resistant isolates are missed.

**RL agent:** each training episode starts from random resistance levels (2–10%), and the growth rate varies ±10% each week (domain randomisation). It is evaluated on 100 episodes never used in training.

### B6. Why LightGBM?

1. **Measured, not assumed:** on the same split, LightGBM 0.780, random forest 0.777, XGBoost 0.779, CatBoost 0.780, logistic regression **0.765**. Tree ensembles win, and the algorithm matters less than the data (within 0.003).
2. **Tabular data:** every input is a table row (metadata, gene presence, k-mer frequencies). Gradient-boosted trees are the strongest standard method for tables.
3. **Native categorical features:** 126 antibiotics and many species, without one-hot encoding.
4. **Native missing values:** 97.3% of rows have no MIC. LightGBM learns which branch a missing value goes to, so nothing has to be imputed.
5. **Monotone constraint:** we force "higher MIC → never lower resistance", which an ordinary neural network cannot guarantee. It costs no accuracy (−0.0004, McNemar p = 0.14).
6. **Speed and size:** it trains on 6.3 million rows on a CPU, and the model file is a few MB, so it serves fast on the website.
7. **Deep learning was tried:** a Keras k-mer network and a CNN-LSTM timeline (July). Neither was kept (Deviations chapter).

On genomes, LightGBM on 4-mers (0.935) beat the earlier random forest on 4-mers (0.867).

### B7. Why not deep learning?

**Say:** "Our data is tabular, so we chose by measurement. Deep learning was tried and not kept. We do use neural networks where they fit: the RL agent and the GAN."

1. **Tables, not images or text:** each input is a table row. On tables, gradient-boosted trees usually match or beat neural networks, with far less tuning.
2. **The algorithm hardly mattered:** the four tree ensembles were within 0.003 AUC of each other. The gains came from the data: the split by genome, out-of-fold rates and MIC.
3. **Missing values:** 97.3% of rows have no MIC. A neural network needs these filled in; LightGBM handles them itself.
4. **Safety rule:** "higher MIC never lowers resistance" is guaranteed by LightGBM's monotone constraint. An ordinary network cannot guarantee it.
5. **Genomes are huge:** about 5 million bases each. A CNN on raw DNA needs a GPU and many more labelled genomes. The 256 k-mer counts or 358 gene features carry the signal in a small vector.
6. **Explainable and cheap:** you can see which genes and features a tree model used. It trains on a CPU, and the model files are a few MB.
7. **What was tried:** in July, a Keras two-branch network on k-mers and a CNN-LSTM for the timeline (`notebooks/archive/`). The network's notebook was saved without results, and the CNN-LSTM's training was stopped early. Neither was deployed.

**If she asks "what AUC did the deep model get?":** "It has no finished, comparable result, so we don't claim it lost. We claim the tree models were measured and agree within 0.003."

### B8. Which LightGBM model exactly?

**GBDT** (gradient-boosted decision trees, `boosting_type='gbdt'`), from Microsoft's LightGBM library (version ≥ 4.0). It is trained with `lgb.train` and early stopping in `experiments/algorithms/lightgbm_model.py`.

- **Boosting:** each new tree corrects the errors of the trees before it.
- **Leaf-wise growth:** each step splits the leaf that reduces the loss most.
- **Histogram-based splits:** fast on millions of rows.

| Served model | Task (objective) | Trees | Leaves per tree | Learning rate |
|---|---|---|---|---|
| Forecaster | binary classification (log-loss) | 499 | 63 | 0.05 |
| Gene model | binary classification | 500 | 63 | 0.05 |
| k-mer model | binary classification | 500 | 63 | 0.05 |
| Timeline ML | regression (L1, mean absolute error) | 73 | 15 | 0.03 |

The three classifiers share the same settings:
- 80% row and feature sampling per tree;
- L1 regularisation 0.1 and L2 regularisation 1.0;
- `is_unbalance` class weighting;
- early stopping after 30 rounds without improvement in AUC.

The forecaster also has the monotone constraint on MIC and isotonic calibration. The tree counts come from the served files in `backend/trained_models/`.

### B9. How does LightGBM handle missing values?

A missing MIC is stored as NaN. At every split on MIC, training tries sending all the NaN rows **left** and then **right**, and keeps the direction with the larger gain. That "default direction" is saved in the tree. At prediction time, a missing value follows it.

**Proof from the served forecaster** (`amr_lgbm_final_model.txt`): `mic_value` is used in 4,574 splits. NaN is sent left in 2,398 of them and right in 2,176, so the model learned the direction split by split. It never treats a missing MIC as a value such as 0.

`has_mic` (0 or 1) also tells the model directly whether an MIC was measured. For categorical features, LightGBM sends missing or unseen categories to the "other" side of the split.

### B10. Why these learning rates?

They were **not grid-searched**. They are standard conservative values, and early stopping on validation data chooses the number of trees.

- **0.05 for the three classifiers:** half of LightGBM's default (0.1). A smaller rate means each tree corrects only part of the error, which overfits less but needs more trees. The cap is 500 trees, with early stopping after 30 rounds without AUC gain.
- **0.03 for the timeline:** it trains on a small table of yearly points, so it uses an even slower rate, small trees (15 leaves, 20 points per leaf) and early stopping after 100 rounds. Early stopping chose **73** trees.
- **Why not tune them:** the four tree algorithms were within 0.003 AUC, so tuning was unlikely to move results much. The effort went into the data, the split and the threshold.
- **If asked "the classifiers used 499–500 trees, the cap?":** yes. AUC was still rising slowly at the cap, so more trees or a higher rate might add a little; this is a limitation.

---

## Part C. Other ML concepts she may ask

| Question | Answer |
|---|---|
| **Train / validation / test?** | 80/20 split **by genome** (no genome on both sides). Validation = 1/6 of the training genomes, for early stopping, calibration and the threshold. Test used once. Timeline: trained on years ≤ 2016, tested on 2017–2022 |
| **Overfitting: how prevented?** | Early stopping (30 rounds); row and feature subsampling (0.8 / 0.8); L1 and L2 regularisation (0.1 / 1.0); limited leaves (63); out-of-fold target encoding; the split by genome |
| **Data leakage?** | The first model split rows at random, so a genome's rows were in train and test: AUC 0.93, but **0.64** on unseen genomes. Fixed by splitting by genome, then checked with a lineage split, a temporal split and a genus held out |
| **Cross-validation?** | 5-fold out-of-fold target encoding; 3 split seeds (42, 1, 2: forecaster experiment A2 0.7849 ± 0.0005, gene model 0.9789 ± 0.0004); lineage and temporal splits as extra tests |
| **Hyperparameters?** | Forecaster and genome models: 63 leaves, learning rate 0.05, up to 500 trees with early stopping, subsample 0.8, colsample 0.8. Timeline: 15 leaves, learning rate 0.03, 73 rounds chosen on validation years 2014–2016 |
| **Loss function?** | Classifiers: binary cross-entropy (log-loss). Timeline: L1. RL: PPO's clipped objective. CTGAN: Wasserstein loss with gradient penalty |
| **Why AUC, not accuracy?** | The threshold is set for safety (miss ≤ 10% of resistant), which lowers accuracy (forecaster 0.54) while recall is 0.91. AUC measures ranking at every threshold. We also report F1, AUPRC, Brier score and the clinical errors VME/ME |
| **Confusion matrix (forecaster test)?** | TP 402,050, FP 686,871, TN 442,519, FN 37,992 (1,569,432 rows) |
| **VME and ME?** | VME = a resistant isolate called susceptible (dangerous): 8.6%. ME = a susceptible isolate called resistant: 60.8% at the safety threshold |
| **Calibration?** | Isotonic regression on validation genomes: Brier score 0.193 → 0.160, so a predicted 70% means about 70% |
| **Statistical significance?** | DeLong test for AUC differences, McNemar for paired errors, bootstrap by genome for intervals (e.g. genes beat k-mers by +0.0445, p < 0.0001) |
| **Bias in the data?** | Mostly US/EU isolates; *Escherichia* is 3.56M of 7.85M rows. The forecaster does not transfer to an unseen genus (0.618); the gene model does (0.82–0.94) |
| **Is the simulation ML?** | No: a logistic-growth simulation with hand-set constants, labelled "not a trained model" everywhere. The trained timeline model is the yearly forecast |
| **Contribution?** | Five trained models, each tested on data it never saw against baselines; one web platform; a published library (`pip install amrpredict`); the Resistance Explorer |
