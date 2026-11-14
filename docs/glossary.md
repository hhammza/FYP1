# Glossary and reading order

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 12. Glossary

| Term | Meaning |
|---|---|
| **AMR** | Antimicrobial resistance, bacteria surviving a drug that used to kill them |
| **MIC** | Minimum inhibitory concentration (mg/L): lowest drug concentration that stops visible growth. Higher = more resistant |
| **MIC sign** | The comparator recorded with a MIC: `=` exact, `<=` "not detected above this", `>=` "exceeded the measurable range" |
| **Breakpoint** | The MIC threshold above which a clinical lab calls an isolate Resistant (EUCAST/CLSI publish these per drug/species) |
| **R / I / S** | Resistant / Intermediate / Susceptible, the clinical phenotype call. Here I is merged into R |
| **k-mer** | A length-k substring of DNA. 256 possible 4-mers; their frequencies fingerprint a genome without alignment |
| **GC content** | Fraction of G+C bases. Species-characteristic, and a cheap proxy for genome composition |
| **Taxon ID** | NCBI Taxonomy identifier, 562 = *E. coli*, 573 = *K. pneumoniae* |
| **Target encoding** | Replacing a category with the historical mean of the target for that category |
| **AUC-ROC** | Probability the model ranks a random Resistant sample above a random Susceptible one. 0.5 = coin flip, 1.0 = perfect |
| **BV-BRC / PATRIC** | Bacterial and Viral Bioinformatics Resource Center, the source of the AMR phenotype data |
| **Pseudo-labelling** | Adding confidently-predicted unlabeled rows to the training set as if they were labels |

## 13. Reading order for someone new to the repo

1. `frontend/app.py`, 250 lines, and it shows you every feature the system has
2. `backend/api/views.py`: the eight endpoints and their validation rules
3. `backend/ml_models/lgbm_predictor.py`: the cleanest of the three engines
4. `backend/train_models.py`, where the features actually come from
5. `experiments/HANDBOOK.md`: the training setup, data fields and measured results
6. The `/models` and `/compare` pages in the running app: every model's results and training data, with charts
7. `amrpredict-lib/docs/known-issues.md`: the account of what is broken
8. `notebooks/01_forecaster_model.ipynb` to `03_evaluation.ipynb`, the current models step by step; `notebooks/archive/LightGBM_Model_Improved.ipynb` for the July research story
9. `docs/PROJECT_DOCUMENTATION.md`: the deep reference, once you know the shape

If you only have ten minutes before a demo: know that engine 3 is a simulation and say so unprompted, and know that the July model's 0.93 was measured on genomes it had already seen: on new genomes it scored 0.64, which is why every number now comes from a split by genome.
