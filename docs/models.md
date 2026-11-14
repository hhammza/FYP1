# The prediction engines

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 4. The three prediction engines

All three share one design: a class with `_load()`, `predict()` and a `status` property; if the artifact is missing, `is_trained` stays `False` and a **heuristic fallback** answers instead. That fallback is what keeps the app demo-able on a fresh clone, and also what hides failures ([§11.1](known-issues.md)).

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
