# Results and where each number comes from

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 10. The numbers, and where each one comes from

There are several AUC figures in circulation in this project. They are not contradictory, they come from different runs on different data, but you should know which is which before a viva.

**Current figures (2026-10-22; forecaster cleaning v7; genome models v6, identical on v7).** Quote these; the tables below are the history that led to them.

| Model | Served on | Test | AUC [95% CI] |
|---|---|---|---|
| `D3_forecaster_deploy_v7` (LightGBM, metadata + MIC) | `/forecast` | 1.57 M rows of unseen genomes | **0.774** [0.772–0.775]; lab-confirmed rows 0.908; 0.762 as `/forecast` scores it (form inputs) |
| `G_kmer_deploy` (LightGBM, 4-mers of the complete genome) | `/predict` without AMRFinderPlus | 40,356 lab rows, 4,481 unseen genomes | **0.935** [0.931–0.939] |
| `TL_timeline_ml` (LightGBM, yearly resistance series) | `/timeline` (`ml_forecast`) | 411 forecasts of 2017–2022 | mean absolute error **13.98 pp** [11.84–16.33]; last value 14.33, trend 16.75, mean 17.25 |
| `G_genes_deploy` (LightGBM, AMRFinderPlus genes, no genus) | `/predict` where AMRFinderPlus runs (Docker image) | same | **0.977** [0.975–0.979] |
| `B6L_genes_v6` (genes + genus, the best experiment) | experiment | same | **0.979** [0.977–0.981]; 0.9789 ± 0.0004 over 3 split seeds |
| `B8_*_v6` (genes, one genus held out) | experiment | 7 genera | 0.82–0.94 with genes, 0.46–0.75 without |

Genome models are judged on lab-confirmed rows (computational labels were predicted from the genome). Details: `experiments/GENOME_RESULTS.md`, `experiments/RESULTS.md`, and the "Currently served" note in `experiments/README.md`.

| Number | Source | What it measures |
|---|---|---|
| **0.8881** | `LightGBM_Model_Improved.ipynb`, cell 5 output | Test AUC of the notebook model, 18,166 held-out rows from the single BV-BRC CSV |
| **0.8815 ± 0.0003** | same notebook, 5-fold CV | Stability check, very tight, so no fold-luck |
| **0.8872** | same notebook, after pseudo-labelling | Final notebook model. Pseudo-labelling added 25,214 rows and *did not* improve test AUC |
| **0.9255** | `docs/PROJECT_DOCUMENTATION.md:2088`, a `train_models.py` console log | The shipped backend artifact, trained on the per-species `amr_output/` CSVs |
| **0.9290** | `docs/PROJECT_DOCUMENTATION.md:1928` | Claimed K-mer RF test AUC, see the caveat below |
| **0.93** | UI badges throughout | Rounded, for both models |

**Superseded as of 2026-09-24.** The `experiments/` harness re-measured this on the
full export (1.56 M rows on cleaning v5) under a grouped split with out-of-fold encoding:
**AUC 0.8227 [0.8197-0.8264]** (0.8232 on the pre-v5 data). The 0.9255 is not directly comparable, it came
from a seventh of the data under a protocol that fitted encodings on the test
rows. Quote 0.823 and explain the difference; see
[experiments/HANDBOOK.md [§11](known-issues.md)](../experiments/HANDBOOK.md).

**Re-tested on unseen genomes, 2026-09-25.** `experiments/evaluate_shipped.py`
worked out exactly what the shipped artifacts trained on: `train_models.py` reads
the first N files of a directory listing, which on the Windows machine that
trained them was alphabetical. The first 500 `amr_output` CSVs reproduce the
LightGBM's 76 antibiotics, 9 genera and stored resistance rate (0.1662) exactly,
and the first 200 mapped CSVs reproduce the K-mer model's 62 antibiotics exactly.
Every genome outside those files is unseen:

| Model | Trained on | AUC on genomes it trained on | AUC on genomes it never saw |
|---|---|---|---|
| Shipped LightGBM | 24,983 rows, 1,007 genomes, 9 genera | 0.941 | **0.644** [0.642-0.645] |
| Shipped K-mer RF | 6,002 rows, 218 genomes, 6 genera | 0.981 | **0.695** [0.679-0.714] |
| Experiment A2 | 1,220,637 rows, 102,578 genomes, 37 genera | n/a | **0.823** [0.820-0.827] |

On the same 297,197 rows that neither model trained on, the shipped LightGBM
scores 0.644 and A2 scores 0.820. The shipped LightGBM trained on 1.6% of the
available rows, not a seventh as stated above: 500 of 3,655 files, but those
files are small. It never saw *Klebsiella* (30% of the data) and its training
data is 16.6% resistant against 36.5% overall. The K-mer model does no better
than guessing from the antibiotic alone (0.703). Both pages in [§8.1](frontend.md) show these
numbers.

Two caveats:

1. **No metrics ship with the artifacts.** `train_models.py` prints AUC and throws it away; nothing is written into the model files. So every number in the UI and the docs is hand-transcribed from a console log of a run whose data is no longer in the repo. If anyone retrains, the badges will silently go stale. The fix is small: write a `metrics.json` next to the models and read it in `status()`.
2. **The K-mer AUC is measured on the training-time path, not the serving path.** Training computes it correctly. Serving never reaches the model at all ([§11.1](known-issues.md)), so the 0.93 badge on `/predict` does not describe what that page is doing.

Other counts to keep straight:

| Thing | Count | Where |
|---|---|---|
| Antibiotics offered in the UI dropdowns | 82 | `backend/amr_constants.py:UI_ANTIBIOTICS` (fallback; each page shows the names its model knows) |
| Antibiotics the K-mer model knows | 62 | `ab_list` inside the pickle |
| Antibiotics with a LightGBM rate table | 76 | `ab_rate_full.joblib` |
| Drug classes mapped | 24 | `backend/amr_constants.py:DRUG_CLASS_MAP` (138 entries) |
| Organisms in the quick-select | 15 | `frontend/app.py:BACTERIA_LIST` |
| LightGBM trees / leaves | 217 / 63 | the `.txt` model file |
| K-mer forest | 100 trees, depth 15, 321 features | the pickle |

The 48-vs-62 gap means 14 antibiotics the k-mer model was trained on can never be selected in the web UI. Not a bug, but a rough edge.
