# The prediction engines

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 4. The prediction engines: five trained models and one simulation

| Engine | Kind | Page | Section |
|---|---|---|---|
| Forecaster `D3_forecaster_deploy_v7` | LightGBM, trained | `/forecast` | 4.1 |
| Gene model `G_genes_deploy` and k-mer model `G_kmer_deploy` | LightGBM, trained (two models) | `/predict` | 4.2 |
| Mutation timeline | Logistic-growth simulation, **not trained** | `/timeline`, what-if simulation | 4.3 |
| Timeline ML model `TL_timeline_ml` | LightGBM, trained | `/timeline`, ML trend forecast (the default tab) | 4.4 |
| RL agent | PPO, trained **on the simulation** | `/timeline`, panel under the what-if simulation | 4.5 |

Since 2026-11-15 the two `/timeline` tabs call separate endpoints: `/api/timeline/` is the timeline ML model only (the organism given or identified from a genome) and `/api/timeline/simulate/` is the simulation with the RL block. The simulation's response no longer carries `ml_forecast`.

The forecaster, the genome models and the simulation share one design: a class with `_load()`, `predict()` and a `status` property; if the artifact is missing, `is_trained` stays `False` and a **heuristic fallback** answers instead. That fallback is what keeps the app demo-able on a fresh clone, and also what hides failures ([§11.1](known-issues.md)).

### 4.1 LightGBM resistance forecaster - `ml_models/lgbm_predictor.py`

**Input:** antibiotic (required), plus optional taxon ID, MIC value, MIC sign, genus, species.

**The 14 features** (`FINAL_FEATURES`, line 74):

| Group | Features | Notes |
|---|---|---|
| Identity | `Taxon ID`, `Antibiotic`, `drug_class`, `genus`, `species` | 4 of these are LightGBM native categoricals |
| MIC | `mic_sign`, `mic_value`, `mic_log`, `has_mic` | NaN is left as NaN. LightGBM learns a branch for it |
| Provenance | `is_lab_confirmed`, `computational_f1` | how trustworthy the source label was |
| **Target encodings** | `ab_resistance_rate`, `taxon_ab_resistance_rate`, `genus_ab_resistance_rate` | historical resistance rate for this drug / this organism+drug / this genus+drug |

The target encodings are the interesting part and the most likely viva question. They are lookups computed during training and saved as `.joblib` side-tables: 76 antibiotic rates, 553 taxon×antibiotic rates, 138 genus×antibiotic rates (only groups with ≥3 observations qualify, `train_models.py:171-177`). At inference the predictor looks up the pair and falls back, taxon rate → antibiotic rate → global mean (0.1662, from `lgbm_meta.joblib`). This is what lets the model say something sensible about *E. coli* + ciprofloxacin even when you give it no MIC.

**Taxon IDs are now species level in the trainer (2026-09-25).** The export's `Taxon ID` is mostly strain level: *E. coli* is spread over about 1,200 IDs and the species ID 562 never appears, so the shipped taxon table never matches what a user types. `backend/taxon_species.csv` (built from NCBI by `experiments/build_taxonomy.py`) maps every ID to its species, and `train_models.py` now trains and builds the taxon table on species IDs: a model retrained this way recognises 562 on `/forecast`. The deployed model still uses strain IDs until it is retrained, and the predictor should map a user's strain ID to its species at the same time (`load_species_map()` in `train_models.py`). The trainer's own random-split AUC falls from 0.825 to 0.805 with species IDs, because strain IDs let it partly recognise individual genomes; a genome-grouped comparison is still to be run.

**Threshold:** the served model's own, chosen on validation genomes so that at most 10% of resistant isolates are missed (0.15 for `D3_forecaster_deploy_v7`, after isotonic calibration), read from `lgbm_metrics.json`. The first version used a fixed 0.40.

**Served model (2026-09-30): `D3_forecaster_deploy_v7`**, promoted by `experiments/promote.py` (also bundled in `amrpredict` 0.2.0): trained on cleaning v7 (7.85 M rows; v7 = v6 with disk-diffusion mm values no longer read as MICs) with species-level taxa, a monotone MIC effect and isotonic calibration. Deterministic; taxon 562 matches. History and numbers: `experiments/README.md` ("Currently served").

### 4.2 Genome k-mer model - `ml_models/genome_predictor.py`

**Input:** FASTA text (a complete assembly) + antibiotic. **Model:** LightGBM, promoted by `experiments/promote.py <run> --genome`: a gene model into `backend/trained_models/genome_genes/`, a k-mer model into `backend/trained_models/genome/`. `backend/ml_models/genome_predictor.py` serves the gene model when AMRFinderPlus is installed (the Docker image) and the k-mer model otherwise (a laptop without it); if AMRFinderPlus fails on one upload, the k-mer model answers with a `warning`.

**Features (259):** 256 4-mer frequencies of the whole genome, counted inside each contig over A/C/G/T windows only (exactly as `experiments/genome/kmers.py` counted them for training), the antibiotic (a native categorical), GC content and genome length. A *k-mer* is a substring of length k; with k = 4 there are 256 possible words, and their frequencies are a fixed-size fingerprint of the genome, with no alignment or reference needed.

**Served run `G_kmer_deploy`:** trained on 24,719 complete genomes (cleaning v6, plasmid-only records dropped), threshold 0.43 chosen on validation for at most 10% very major error. **Lab AUC 0.935 [0.931–0.939]** on 40,356 lab-confirmed test rows from genomes it never saw. Uploads under 100,000 bp are refused (a partial or plasmid-only file is not a genome).

**Served gene model `G_genes_deploy`** (promoted 2026-10-01): AMRFinderPlus genes and mutations + drug-aware gene counts + antibiotic and drug class, trained on the same 24,719 genomes; threshold 0.58 for at most 10% very major error. **Lab AUC 0.977 [0.975–0.979]** (very major error 10.2%, major error 5.1%, against 9.6% and 19.5% for k-mers), and it names the genes it found (`genes_found`). Per upload it identifies the species from the 6-mer profile (98.0% right species, 99.8% right genus on held-out genomes), runs AMRFinderPlus 4.2.7 (database 2026-08-07.1, as in training) with that `--organism`, and builds the gene features exactly as in training. Verified with real AMRFinderPlus in the Docker image by GitHub Actions on every push to `main` (2026-10-09). All genome results: `experiments/GENOME_RESULTS.md`.

**The old engine** (`resistance_predictor.py`, a 100-tree RandomForest on the first 500 kb of partial FASTAs) stays as the fallback when no genome model is promoted. Re-tested on genomes outside its training files it scored 0.695, no better than the antibiotic alone; its scaler bug ([§11.1](known-issues.md)) is fixed.

### 4.3 Mutation timeline - `ml_models/mutation_timeline.py`

Not machine learning, and the code says so. Given a genome and an antibiotic it runs a **logistic growth model** over N weeks:

```
resistant(t) = r₀ + (peak − r₀) / (1 + e^(−k(t − midpoint)))
```

- `r₀`, starting resistant fraction, derived from how far the genome's GC content sits from 0.50, clamped to 2 to 15%
- `peak`, `k`, per-antibiotic constants from `ANTIBIOTIC_MUTATION_PROFILES` (13 drugs + a default). Carbapenems and colistin climb slowly to a low ceiling; ampicillin climbs fast to 95%. These numbers are hand-set from the literature, **not fitted**.
- `midpoint`, fixed at 45% of the simulated span, so a longer chart moves the failure week later (see below)

It also reports "mutation hotspots" (windows scored by GC content and nucleotide repetitiveness), resistance-gene activation weeks (`gyrA`, `blaTEM`, `mcr-1` …), MIC fold-change, and the **failure week**, the first week resistance crosses 50%.

Since 2026-09-26 the random parts (`cumulative_mutations`, a Poisson draw, and the hotspot mutation types) come from one seeded generator, so identical inputs give an identical response (`seed`, default 42). The three population shares are a partition and add up to exactly 100 every week ([§11.3](known-issues.md)). The response says `model_used: "Biological Simulation"` and `simulation: true`; its format, agreed between Ali and Suleman, is in [progress/formats/README.md](../progress/formats/README.md) §4. That format also fixes what the week 4 RL agent returns (`rl`: the agent's weekly drug plan against "always the same drug" and cycling, with a set rule for `rl.best`) and what `calibration` holds; `rl` is absent until week 4.

**Checked against published data (2026-09-28, [experiments/evolution/](../experiments/evolution/README.md)).** A sensitivity analysis over 8,232 combinations shows the answer depends most on the number of weeks asked: because the midpoint is 45% of the span, asking for 52 weeks instead of 8 makes the same drug fail 2 to 6 times later; `peak` works as a switch at 50% (colistin never fails), and `speed` ±30% moves failure by a median 0.6 weeks. The same logistic curve fits 15 published resistance curves (median R² 0.91): lab evolution of *E. faecalis* under five drugs (Maltas et al. 2025, PLOS Biology) and carbapenem-resistant *K. pneumoniae* in 10 countries (ECDC EARS-Net, 2005 to 2024), whose plateau ranges from 7% to 66% by country. Lab resistance rises within days and hospital resistance over years, so the timeline's weeks stay illustrative and the constants are unchanged. `/api/timeline/` returns this as `calibration` (15 curves, rmse 2.9 points on the hospital series, `parameters_changed: false`), and `/timeline` shows it under the result.

### 4.4 Timeline ML model - `ml_models/timeline_ml.py`

**Input:** a genus and an antibiotic (or a genome, whose genus is found from its 6-mer profile), and 1 to 10 years ahead. **Output:** the observed yearly resistant share and a forecast with an 80% band (`POST /api/timeline/forecast/`, and the `ml_forecast` block of `/api/timeline/`; format in [progress/formats/README.md](../progress/formats/README.md) §8).

**Data:** the 553,223 laboratory results with a collection year (2000–2022), grouped per genus and antibiotic into yearly resistant shares; a year counts with at least 20 results. That gives 2,619 year points in 467 series (`experiments/timeline_ml/series.csv`).

**Model:** LightGBM regression (L1) on the change from the last observed value, from features of the earlier years only: the last three values, the gap since the last one, the recent slope, the historical mean, the number of past points and results, the genus, the antibiotic and its drug class. The forecast is recursive: each predicted year is fed back as history for the next. The band is the 80th percentile of the held-out absolute errors (25.24 pp), widened by √(years ahead).

**Tests** (`experiments/timeline_ml/timeline_model.py train`):

| Test | Model | Last value | Linear trend | Historical mean |
|---|---|---|---|---|
| Temporal: trained on years up to 2016, tested on 2017–2022 (411 forecasts, 191 series) | **13.98** pp | 14.33 | 16.75 | 17.25 |
| Series split: 20% of the series held out whole, every year (396 forecasts, 53 series) | **9.86** pp | 10.21 | 13.16 | 12.52 |

The temporal test is the headline, since a forecast is always about years the model has not seen. **The served model is trained on every year of every series** (`timeline_model.py promote`), so the website's forecast starts after 2022. Known weakness, open (Suleman's scan, 2026-11-15, in `progress/HAMZA_PROGRESS.md` Handovers): some years are one study's batch of isolates, all at 0% or 100% (e.g. *E. coli* and imipenem in 2019–2020); the page draws years with under 30 results hollow.

### 4.5 RL agent - `ml_models/rl_agent.py`

**Input:** ciprofloxacin, gentamicin or imipenem, and a number of weeks (1–52). **Output:** the `rl` block of `/api/timeline/simulate/` (`/api/timeline/` before 2026-11-15; format §4): which drug to give each week, from the agent and from fixed schedules (always one drug, cycling every week or every 4 weeks, lowest resistance first), all run on the same simulation from the same start.

**Model:** a PPO agent (stable-baselines3, Ali, `experiments/evolution/rl_train.py`) trained in the cycling simulation (`rl_env.py`) for 104 weeks, with a 5% weekly fitness cost; the backend runs a NumPy copy of its policy network (`trained_models/rl_agent/policy.npz`), so no PyTorch is needed to serve it. It learned from simulated episodes only, **not from patient data**, and the page says so.

**Result** (100 held-out episodes, Results chapter §8): effective weeks 95.0 of 104 and first failure at week 81.3, against 79.5 and 32.6 for weekly cycling and 18.2 and 19.2 for always imipenem; the simple "lowest resistance first" rule never fails, so the agent does not beat it. The panel appears only for its three drugs, below the what-if simulation's downloads.
