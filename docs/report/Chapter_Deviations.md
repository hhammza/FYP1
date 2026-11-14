# Chapter: Deviations from the Proposal

*Hamza Afzal (leader). What the proposal promised, what was delivered, and why each difference was made. The proposal separates committed items from items promised only "given additional time"; both are listed. Evidence for every result is in the Results chapter and the files named here.*

## 1. Committed items

| # | Proposal | Delivered | Deviation and reason |
|---|---|---|---|
| P1 | A highly tested resistance-prediction model | Forecaster `D3_forecaster_deploy_v7` (AUC 0.774; lab-confirmed rows 0.908) and genome models (gene model lab AUC 0.977; k-mer model 0.935), all tested on genomes never seen in training | None in substance. The first model's reported AUC 0.93 was a leak (random row split); it fell to 0.644 on unseen genomes and was replaced (Results §2) |
| P2 | Predict from genomic sequences | `/predict`: complete-genome upload, gene model with AMRFinderPlus, k-mer model where AMRFinderPlus is not installed | The proposal implied deep learning on raw sequence; gene and k-mer features with gradient boosting were measured instead and won (Results §4) |
| P3 | Predict from clinical CSV data | `/forecast` for one isolate and batch CSV upload with a template | None |
| P4 | Accuracy, recall, F1, AUC-ROC | All reported, plus AUPRC, Brier score, very major and major error, 95% confidence intervals | Extended: the clinical error rates and intervals were added because AUC alone cannot compare models |
| P5 | Cross-dataset evaluation and ablations | Ablations, species and genus hold-out, lineage split, temporal split, 3 seeds, DeLong and McNemar tests | Extended beyond the proposal |
| P6 | A Python library as the main deliverable | `amrpredict` 0.3.0: every model the website serves (forecaster, gene and k-mer genome models, timeline ML model, RL agent) and the simulation, with a command line; 55 tests in CI, passing on Python 3.9 and 3.13; 0.2.0 on TestPyPI | The main-PyPI upload (`pip install amrpredict`) is the last step. The backend keeps its own copy of the predictors, kept identical by parity tests on all four models |
| P7 | Web interface on the library | React + TypeScript site (`web/`) on a Django REST API: forecast, genome prediction, timeline, Resistance Explorer, model reports | See "React" in §3 |
| P8 | Reports in PDF, CSV and images | CSV and PDF export on the three tool pages, PNG download of every chart | None |
| P9 | Secure, scalable interface | Secret key from the environment, restricted hosts and CORS, admin token on training and reload, rate limits, upload size limits, Docker image | Rate limits are per server process; a shared cache is noted for a multi-worker deployment |

## 2. Items promised "given additional time"

| # | Proposal | Delivered | Deviation and reason |
|---|---|---|---|
| C1 | Reinforcement learning to simulate resistance evolution | A biological simulation of resistance under treatment, a **timeline ML model** trained on 553,223 dated lab results, and a **PPO agent** that plans antibiotic cycling on the simulation | The RL agent plans treatment rather than simulating mutation routes: no dataset of mutation routes exists at the needed scale, so the agent learns on the simulation and is labelled as such. The supervisor asked for the timeline as a trained model; the timeline ML model was added for that (Results §6, §8) |
| C2 | GAN data augmentation | CTGAN experiment `A13_ctgan_v7` on the rare antibiotics and genera | Run as planned; the result is negative (AUC −0.008 on rare classes) and reported as such (Results §7). The synthetic rows are not used by any served model |
| C3 | Generative drug design | **Descoped.** The Resistance Explorer shows reference chemistry for existing drugs (from PubChem), not generated molecules | A generator needs validated activity data and chemistry review that the project could not provide; proposing untested molecules in a medical tool would be misleading. Future work |
| C4 | Image input (CNN on bacterial images) | **Descoped** | No public, labelled dataset of bacterial images paired with susceptibility results exists at the needed scale; collecting one needs a microbiology lab. Future work |
| C5 | Multimodal model | Genes + k-mers + organism in one genome model (B7, lab AUC 0.981) | Images excluded (C4). Adding k-mers to genes gains only +0.002, so the genome + metadata fusion is reported, not served |

## 3. Technologies named in the proposal

| Proposal | Used | Reason |
|---|---|---|
| TensorFlow, Keras, CNN / LSTM models | LightGBM (gradient boosting) for the served models; PyTorch for CTGAN; stable-baselines3 for the RL agent | A Keras k-mer network and a CNN-LSTM timeline were tried in July and not kept: the network's notebook was saved without results, and the CNN-LSTM's training was stopped by hand and never deployed (`notebooks/archive/`). On the same split, tree ensembles were within 0.003 AUC of each other and beat logistic regression (Results §3); the choice was measured, not assumed |
| React frontend, Django backend | React + TypeScript (`web/`) on Django | The project first shipped a Flask + Jinja frontend (`frontend/`) for speed, then built the React site the proposal named; both read the same API |
| PostgreSQL | No database | The API is stateless: models and lookup tables are files loaded at start-up (`backend/trained_models/`, `backend/reference/`). A database is needed only for user accounts or prediction history, which are out of scope |
| NCBI Genomes, DrugBank, chemical APIs | BV-BRC (which aggregates NCBI records), NCBI AMRFinderPlus, PubChem, ECDC surveillance data | BV-BRC holds the genomes and their susceptibility results together. DrugBank was not used; drug names, formulas and structures come from PubChem, which is open |
| "Forecasting" in the title | The forecaster predicts resistance of an isolate now; the timeline ML model forecasts the yearly resistant share up to 5 years ahead | The time-based forecast was added in the final sprint at the supervisor's request |

## 4. Scope decisions on record

- **Scope email** to the supervisor, sent 2026-09-25: drug design and images descoped, GAN run as an experiment, RL built as a small agent on the simulation. *Reply: to be added (date and wording) before submission.*
- **Final sprint** (17 to 22 October 2026): the timeline as an ML model, the RL agent and the GAN experiment, at the supervisor's request (`progress/HAMZA_PROGRESS.md`, "Final sprint").
- **Instructor's dashboard requirements** (October to November 2026): twelve requirements for exploring resistance by organism, drug group, country, infection type and chemistry, delivered as the Resistance Explorer (`docs/INSTRUCTOR_REQUIREMENTS_PLAN.md`).

## 5. Moved to future work

- Retraining the genome models on all 87,325 lab-tested genomes (24,926 used).
- Making the backend import `amrpredict` instead of keeping its own copy of the predictors.
- Generative drug design (C3) and image input (C4).
- A reward for the RL agent that penalises failed weeks, and calibration of the simulation's time scale against observed data.
