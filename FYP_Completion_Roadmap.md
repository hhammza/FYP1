# FYP Completion Roadmap: Forecasting Antibiotic Resistance with AI

*Prepared 2026-09-24 against the proposal (`Forecasting Antibiotic Resistance.docx`) and the code at commit `67ed6de`  

**Group:** Hamza Afzal (SP23-BCS-086, leader), Muhammad Ali Mirza (SP23-BCS-082), Malik Muhammad Suleman Saleh (SP23-BCS-068)
**Supervisor:** Mr. Imran Latif · **Co-supervisor:** Mr. Shahid Bhatti

---

## Contents

1. [The short answer](#1-the-short-answer)
2. [What the proposal promised](#2-what-the-proposal-promised)
3. [What the project has today](#3-what-the-project-has-today)
4. [Proposal vs. reality, item by item](#4-proposal-vs-reality-item-by-item)
5. [What is left, ranked](#5-what-is-left-ranked)
6. [Step-by-step plan to complete the project](#6-step-by-step-plan-to-complete-the-project)
7. [Who does what](#7-who-does-what)
8. [Definition of done: final checklist](#8-definition-of-done-final-checklist)
9. [How to improve it after completion](#9-how-to-improve-it-after-completion)
10. [Viva preparation](#10-viva-preparation)
11. [Appendix: file and command reference](#11-appendix-file-and-command-reference)

---

## 1. The short answer

**Where you are.** The core promise of the proposal is *"a well-tested model that predicts antibiotic resistance, packaged as a Python library, with a web interface on top."* Those parts are built: a Django API, a Flask web app, a pip-installable `amrpredict` library with a CLI and tests, and an experiment harness that has run 22 controlled experiments on 1.5 M rows.

**What stops it being finished.** Four problems, in this order:

1. **The web app serves the wrong models.** The deployed LightGBM scores **AUC 0.644** on genomes it never saw. Your own experiment `A2_oof_grouped` scores **0.823** on the same kind of data, but it has never been moved into the app.
2. **The genome page (`/predict`) doesn't use its model.** A scaler bug makes every call fall back to a random heuristic. The fix is one line and already exists in the library.
3. **The UI claims "AUC 0.93" everywhere.** Your own re-test shows that number is wrong. An examiner who opens `/models` will see the contradiction.
4. **Several proposal items don't exist yet:** GAN augmentation, reinforcement learning, generative drug design, image input, and CSV/PDF/image export of results. Each one needs to be either built (minimal but honest) or formally descoped with your supervisor's agreement.

**Rough estimate.** About **70% of the committed scope** and **about 45% of everything the proposal mentions** is done. The remaining must-do work is roughly 3 to 5 focused weeks for three people (plan in §6).

**Timing.** Your Gantt chart puts Testing in July to August 2026 and Documentation in August to September 2026, so by the original plan you are in the final phase now. Confirm the actual submission and viva dates with your supervisor, then compress §6 to fit. §6.0 says what to cut if time is short.

---

## 2. What the proposal promised

Extracted from the proposal's Abstract, Success Criterion, Objectives, Methodology and Tools sections. The proposal separates **committed** items from items it only promised "if time and resources allow". That distinction is your strongest tool for scoping the rest of the work, so it is kept here.

### 2.1 Committed ("the assured key output")

| # | Promise | Proposal wording (paraphrased) |
|---|---|---|
| P1 | A validated resistance-prediction model | "Provide a highly-tested prediction model of antibiotic resistance as the assured key output" |
| P2 | Predict from **genomic sequences** | "forecast the presence of antibiotic resistance in genomic sequences" |
| P3 | Predict from **clinical CSV data** | "clinical data in CSV format" |
| P4 | Standard metrics | accuracy, recall, F1-score, AUC-ROC |
| P5 | Robustness tests | cross-dataset evaluation and ablation studies |
| P6 | **Python library**, the primary deliverable | "well-documented, modular Python library… This library shall be the main delivery" |
| P7 | **Web interface** on top of the library | upload data, real-time predictions, visualisations |
| P8 | **Exports** | "download reports in different formats like PDF, CSV" and images |
| P9 | Secure and scalable | "secure, scalable and user-friendly web interface" |

### 2.2 Conditional ("given additional time")

| # | Promise | Proposal wording |
|---|---|---|
| C1 | Evolution forecasting with **reinforcement learning** | "reinforcement learning to simulate the evolution of resistance… mutation routes" |
| C2 | **GAN data augmentation** | "GANs to sample the small datasets… synthetic samples" |
| C3 | **Generative drug design** | "propose novel antibiotic molecular structures depending on particular resistance profiles" |
| C4 | **Image input** (CNN on bacterial images) | "and hopefully, with sufficient time, the transformed image data" |
| C5 | **Multimodal** model (genome + image + CSV together) | "accommodate various sources of input at the same time" |

### 2.3 Named technologies

TensorFlow, PyTorch, Keras, scikit-learn · GANs, RL · Pandas, OpenCV · **React** frontend, **Django** backend · **PostgreSQL** · NCBI Genomes, DrugBank, chemical prediction APIs.

---

## 3. What the project has today

Verified in the code at `67ed6de`, not just taken from the docs.

### 3.1 Components

| Component | Location | State |
|---|---|---|
| Django REST API | `backend/` | 9 endpoints (`health`, `forecast`, `predict`, `timeline`, `antibiotics`, `vocabulary`, `train`, `models`, `reload`). Loads 3 engines at startup |
| Flask web app | `frontend/` | 11 pages: home, forecast, predict, timeline, train, models, compare, datasets, about, library + JSON helpers. Dark mode, Plotly charts |
| `amrpredict` library | `amrpredict-lib/` | v0.1.0, flat API + CLI, bundled models, 27 test functions, 4 doc pages. **Not published to PyPI** |
| Experiment harness | `experiments/` | 5 algorithms, 22 configs, grouped splits, out-of-fold encoding, bootstrap CIs, VME/ME, registry, report export |
| Data | `Data/` | BV-BRC export: 3,655 AMR CSVs (≈3 M raw rows → 1.53 M clean), ≈2,588 genome FASTAs, mapped CSVs. ≈5 GB, committed |
| Notebooks | root `*.ipynb` | LightGBM development (with outputs), Keras two-branch MLP, CNN-LSTM mutation model, **one empty notebook** |
| Deployment | `Procfile`, `railway.toml` | Two Railway services configured |
| Docs | `README.md`, `PROJECT_DOCUMENTATION.md`, `EXPERIMENT_PLAN.md`, `experiments/HANDBOOK.md`, `CHANGES.md` | Thorough and candid |

### 3.2 The three engines

| Engine | Type | Input | Status |
|---|---|---|---|
| **LightGBM forecaster** | Trained ML (gradient-boosted trees, 14 features) | Antibiotic + organism + optional MIC | ✅ Works. ⚠️ Deployed artifact trained on only 1.6% of the data. **0.644 AUC on unseen genomes** |
| **K-mer RandomForest** | Trained ML (256 4-mer frequencies + antibiotic one-hot) | Genome FASTA + antibiotic | 🔴 **Broken in the web app** (scaler shape bug → random heuristic). Works in the library. **0.695 on unseen genomes**, no better than guessing from the antibiotic alone (0.703) |
| **Mutation timeline** | **Simulation, not ML** (logistic growth, hand-set constants) | Genome FASTA + antibiotic | ✅ Runs. ⚠️ Population shares exceed 100% after the susceptible pool empties. Not validated against data |

### 3.3 The measured results you can defend

| Question | Answer (from `experiments/RESULTS.md`) |
|---|---|
| Honest baseline (full data, genome-grouped split, out-of-fold encoding) | **AUC 0.8232 [0.8200–0.8269]**, F1 0.66 |
| Best overall | `A6_lab_only` **0.9654**: lab-confirmed labels only (but the MIC largely *is* the label here; see A6b = 0.870 without MIC) |
| Algorithm comparison (same 400 k sample) | LightGBM 0.820 ≈ XGBoost 0.820 ≈ CatBoost 0.819 ≈ RF 0.817 > Logistic 0.802 |
| Value of MIC | +0.020 pooled, +0.095 on lab subset |
| Floor (antibiotic only) | 0.6545 |
| Unseen genus (*Klebsiella* held out) | **0.597**: does not generalise across genera |
| More data? | Learning curve flat from 50 k rows: **feature-limited, not data-limited** |
| Biggest lever | **The decision threshold.** 0.40 → 0.47 moves major error 46% → 34% |

---

## 4. Proposal vs. reality, item by item

Legend: ✅ done · 🟡 partial · 🔴 missing / broken · ⚪ intentionally different (a justified deviation)

| # | Proposal item | Status | Evidence / gap |
|---|---|---|---|
| P1 | Validated prediction model | 🟡 | Validated model **exists** (A2, 0.823) but the **app serves a weaker one** (0.644). |
| P2 | Genome-sequence prediction | 🔴 | K-mer model broken in the web app, and weak even when fixed. No AMR-gene features yet. |
| P3 | Clinical CSV prediction | 🟡 | Single-isolate form works. **No batch upload of a CSV file** in the web app. |
| P4 | Accuracy / recall / F1 / AUC | 🟡 | AUC, AUPRC, F1, Brier, VME, ME computed. **Accuracy and recall not shown explicitly** (recall = 1 − VME, but say it in the report). No calibration plot. |
| P5 | Cross-dataset + ablation | ✅ | Ablations (no-MIC, drug-only, no-encoding), species hold-out, lab-only vs computational labels, learning curve. **No DeLong/McNemar significance tests, single seed.** |
| P6 | Python library (primary) | 🟡 | Built, tested, documented. **Carries the old weak models.** Not on PyPI. Backend and library are duplicated code. |
| P7 | Web interface | ✅ | 11 pages, clean ML-vs-simulation separation. |
| P8 | Export CSV / PDF / images | 🔴 | **No export of any kind.** Only Plotly's built-in PNG button on charts. |
| P9 | Secure, scalable | 🔴 | Hardcoded `SECRET_KEY` fallback, `ALLOWED_HOSTS='*'`, `CORS_ALLOW_ALL_ORIGINS`, `csrf_exempt` on all POSTs, **unauthenticated `/api/train/` and `/api/reload/`**. |
| C1 | RL evolution forecasting | 🔴 | Timeline is a logistic-growth **simulation** (honestly labelled). CNN-LSTM exists only in a notebook. No RL anywhere. |
| C2 | GAN augmentation | 🔴 | Not present. (Note: learning curve shows more data doesn't help, which is itself an argument against GAN augmentation. See §6.4.2.) |
| C3 | Generative drug design | 🔴 | Not present. No SMILES, no RDKit. |
| C4 | Image input | 🔴 | Not present. No image dataset collected. |
| C5 | Multimodal model | 🔴 | Tabular and genome models are separate; nothing fuses them. |
| – | React frontend | ⚪ | Flask + Jinja + Bootstrap used instead. Defensible: lighter, server-rendered, no build step. **State it in the report.** |
| – | PostgreSQL | ⚪/🔴 | No database in use (`db.sqlite3` is vestigial). Needed only if you add prediction history or user accounts. |
| – | NCBI / DrugBank APIs | 🟡 | Data came from BV-BRC (which aggregates NCBI). DrugBank unused. |
| – | "Forecasting" in the title | 🟡 | The "forecaster" is a **classifier** (predicts R/S now), not a forecast over time. The only time-based output is the simulation. **Examiners may ask about this**; see §6.4.1 and §9.2. |

---

## 5. What is left, ranked

### Tier 1: Must fix. Correctness and honesty (the project is not defensible without these)

| ID | Task | Why it's critical | Effort |
|---|---|---|---|
| T1.1 | Port the k-mer scaler fix to the backend | `/predict` currently returns **random numbers** labelled as a trained model | 1 h |
| T1.2 | Fix the training data path (`data_dir` → `Data/`) | `/train` says "Training started" then silently fails | 30 min |
| T1.3 | Replace every hardcoded "AUC 0.93" / "0.9255" in the UI with real numbers from `model_report.json` | Contradicts your own `/models` page | 2–3 h |
| T1.4 | **Promote the best experiment model into the app** (A10 monotonic, or A2) with a validated threshold | The app serves a model 0.18 AUC worse than one you already have | 1–2 days |
| T1.5 | Normalise antibiotic names (`trimethoprim/sulfamethoxazole` ×4, typos `geamycin`, `trimotheprim`, `carbapenem`) | Inflates categories, splits rates, confuses users | 3–4 h |
| T1.6 | Write `metrics.json` beside each deployed model and read it in `status()` | Stops UI numbers going stale ever again | 2–3 h |

### Tier 2: Must do. Committed proposal items that are missing

| ID | Task | Proposal item | Effort |
|---|---|---|---|
| T2.1 | Build a **real genome model**: AMR-gene presence features (AMRFinderPlus / ResFinder) + k-mers, genome-grouped evaluation | P2 | 4–6 days |
| T2.2 | **Export results**: CSV + PDF report + PNG charts on forecast, predict and timeline pages | P8 | 2–3 days |
| T2.3 | **Batch CSV upload** on `/forecast` (many isolates at once → downloadable results CSV) | P3, P7 | 1–2 days |
| T2.4 | **Security hardening** (auth on train/reload, env-only secret, CORS/hosts, CSRF, upload size limits) | P9 | 1 day |
| T2.5 | Show **accuracy + recall** explicitly, add **calibration plot**, **DeLong/McNemar** tests, **3 seeds** | P4, P5 | 1–2 days |
| T2.6 | Library v0.2.0 with the new models; backend **imports the library** instead of duplicating it; publish to (Test)PyPI | P6 | 1–2 days |
| T2.7 | Backend + frontend **automated tests**; fix the >100% timeline bug (remove the `xfail`) | Testing phase | 2 days |

### Tier 3: Conditional proposal items. Build a minimal honest version *or* formally descope

Agree this list with your supervisor **in writing** (an email is enough). The proposal made these conditional, so descoping is legitimate, but it has to be a decision on record, not something the examiner notices first.

| ID | Item | Recommendation |
|---|---|---|
| T3.1 | Evolution forecasting / RL (C1) | **Build a small version.** Cheapest defensible option: sensitivity analysis + fix + a small RL drug-cycling agent on top of your simulation (§6.4.1) |
| T3.2 | GAN augmentation (C2) | **Build as an experiment, not a feature.** CTGAN on tabular rows for rare antibiotic/genus groups, measure with/without on real test data only (§6.4.2). A negative result is fine and fits your learning-curve finding |
| T3.3 | Generative drug design (C3) | **Minimal prototype or descope.** If built: small SMILES generator + RDKit validity/novelty/QED, clearly labelled "in-silico candidates, not validated" (§6.4.3) |
| T3.4 | Image input (C4) | **Descope → future work.** No image dataset exists; collecting one is out of scope for the time left |
| T3.5 | Multimodal fusion (C5) | **Light version via T2.1**: one genome model that uses gene features + k-mers + organism metadata is multimodal in the genome+tabular sense. Images excluded |

### Tier 4: Documentation and submission

| ID | Task | Effort |
|---|---|---|
| T4.1 | Final report / thesis (with a **Deviations from Proposal** chapter) | 1–2 weeks (in parallel) |
| T4.2 | Delete or fill `forecasting_formulation.ipynb` (0 bytes) | 10 min |
| T4.3 | Demo script, screenshots, recorded video backup | 1 day |
| T4.4 | Deploy final version to Railway and freeze a git tag `v1.0-submission` | ½ day |

---

## 6. Step-by-step plan to complete the project

### 6.0 Suggested schedule

| Week | Focus | Tasks |
|---|---|---|
| **Week 1** | Correctness and honest numbers | T1.1 → T1.6 |
| **Week 2** | Genome model | T2.1 (and start report chapters 1–3 in parallel) |
| **Week 3** | Platform features | T2.2, T2.3, T2.4, T2.6 |
| **Week 4** | Conditional items (as agreed) + evaluation | T3.1, T3.2, (T3.3), T2.5 |
| **Week 5** | Testing, deployment, write-up, rehearsal | T2.7, T4.1–T4.4 |

**If you only have 2 weeks:** Week 1 as above, then T2.2 (exports), T2.4 (security), T3.1 minimal (sensitivity analysis + fix only), a written descoping of C2–C5, and the report. Skip T2.1 and explain the k-mer model's weakness honestly using your own re-test. That is still a defensible project.

---

### 6.1 Week 1: Correctness and honest numbers

#### Step 1. Create a working branch

```bash
cd FYP1
git checkout -b completion
```

Commit after every step below, one step per commit. It makes the viva question "what did you change and when?" easy to answer.

#### Step 2. Fix the k-mer scaler bug (T1.1)

- **File:** `backend/ml_models/resistance_predictor.py`, line 158
- **Current:** `feat = self.scaler.transform(feat.reshape(1, -1))[0]`
- **Change to** (copy from `amrpredict-lib/src/amrpredict/kmer.py:166`):
  ```python
  feat[:256] = self.scaler.transform(feat[:256].reshape(1, -1))[0]
  ```
- **Also:** when the model raises, the response must **not** say `'RandomForest K-mer (trained)'`. Set `model_used` to `'Heuristic fallback'` in the `except` branch so the UI can never hide a failure again.
- **Verify:** submit the same FASTA twice on `/predict`. The probability must be **identical** both times.

#### Step 3. Fix the training data path (T1.2)

- **File:** `backend/train_models.py`, line 412
- **Change:** `data_dir = ROOT_DIR` → `data_dir = os.path.join(ROOT_DIR, 'Data')`
- **Also:** `csv_files[:max_files]` (line 63) and `csv_files[:200]` (line 290) take the *first N files of a directory listing*. Sort them explicitly (`sorted(...)`), and ideally remove the cap or randomise it with a fixed seed. This cap is exactly why the shipped model never saw *Klebsiella*.
- **Also:** make `/api/train/` return an error if the data folder is missing, instead of "Training started".

#### Step 4. Normalise antibiotic names (T1.5)

- **File:** `experiments/lib/data_prep.py` (and the same mapping in `backend/train_models.py`)
- Add one `ANTIBIOTIC_ALIASES` dict applied right after loading:
  ```python
  ANTIBIOTIC_ALIASES = {
      'trimethoprim-sulfamethoxazole': 'trimethoprim/sulfamethoxazole',
      'sulfamethoxazole/trimethoprim': 'trimethoprim/sulfamethoxazole',
      'co_trimoxazole':                'trimethoprim/sulfamethoxazole',
      'geamycin':                      'gentamicin',
      'trimotheprim':                  'trimethoprim',
      'amipicillin_sulbactam':         'ampicillin/sulbactam',
      # drop non-drugs: 'carbapenem', 'extended spectrum beta lactamase'
  }
  ```
- Apply the same map to the frontend dropdown list (`frontend/app.py:ANTIBIOTICS`) so users can only pick canonical names.
- Re-run `A2`/`A10` afterwards so every later number uses clean vocabulary.

#### Step 5. Choose and promote the deployed tabular model (T1.4)

**Decision to make:** which run to ship. Recommendation: **`A10_monotonic_mic`** (0.8222, only 0.001 below A2, and it *cannot* predict lower resistance at higher MIC). That is a clinical-safety argument an examiner will respect.

**Threshold:** don't keep 0.40 blindly. Pick it on the **validation** set with a stated goal, for example *"keep very major error (VME, missed resistance) ≤ 10% while minimising major error"*. Record the chosen value and its VME/ME in the report.

**Calibration (plan A9, not yet done):** fit isotonic or Platt calibration on a validation fold so the "73% resistant" on screen is a real probability. Report Brier score before and after.

**Promotion steps** (the harness does not do this automatically, see `experiments/HANDBOOK.md §13`):

1. Re-run the chosen config on the cleaned data: `python experiments/run.py experiments/configs/A10_monotonic_mic.json`
2. Write a small script `experiments/promote.py` that:
   - loads the saved LightGBM model and the run's rate tables,
   - converts the rate tables to the filenames/pandas shapes the backend expects (`ab_rate_full.joblib`, `taxon_ab_rate_full.joblib`, `genus_ab_rate_full.joblib`, `lgbm_meta.joblib`),
   - writes `amr_lgbm_final_model.txt`,
   - writes **`metrics.json`** (run ID, date, AUC + CI, AUPRC, F1, accuracy, recall, VME, ME, threshold, n_train, n_test, genera, git commit),
   - copies everything into `backend/trained_models/` **and** `amrpredict-lib/src/amrpredict/models/`.
3. Fix the **taxon grouping**: `taxon_ab` is grouped on strain-level PATRIC IDs, so a user typing 562 (*E. coli*) never matches. Group on species-level taxonomy instead (EXPERIMENT_PLAN §7).
4. Restart the backend. Check `/api/health/` and run 5 known cases through `/forecast`.
5. Re-run `python experiments/evaluate_shipped.py` then `python experiments/export_report.py` so `/models` and `/compare` show the **new** deployed model.

#### Step 6. Make the UI read its numbers (T1.3, T1.6)

- Make `LGBMResistancePredictor.status` (and the k-mer one) return the contents of `metrics.json`.
- Replace every hardcoded figure:
  - `frontend/templates/index.html:39` ("LightGBM AUC 0.93")
  - `frontend/templates/base.html:140` (footer "0.93")
  - `frontend/templates/about.html:34, 155, 174, 503, 507`
  - `frontend/templates/datasets.html:347`
  with values passed from the health/models endpoint.
- Add one sentence on `/about`: *"An earlier version reported AUC 0.9255. That figure came from target encodings fitted on the test rows and a model trained on 1.6% of the data. Under a genome-grouped split with out-of-fold encoding, the model scores 0.82."* Examiners reward finding this yourself.

**End of Week 1 check:** `/predict` is deterministic; `/forecast` uses the new model; no number in the UI is hardcoded; `/train` fails loudly without data.

---

### 6.2 Week 2: A real genome model (T2.1)

The proposal's central claim is prediction *from genomic sequences*. Right now that path is the weakest part of the project. Your own analysis says why: 4-mer frequencies mostly identify the *species*, not the *resistance mechanism*. This week fixes that, and it gives you the strongest scientific result in the thesis.

#### Step 7. Genome experiment harness (EXPERIMENT_PLAN Track B)

Extend `experiments/` with a genome track (e.g. `experiments/genome/`) reusing `lib/splits.py` and `lib/metrics.py`:

| Run | What | Purpose |
|---|---|---|
| **B0** | Current k-mer RF with the fix, random split | True baseline of what you shipped |
| **B1** | Same, **genome-grouped** split | How much was memorisation |
| **B2** | k = 3, 4, 5, 6 | Resolution vs. overfitting |
| **B4** | LightGBM on k-mers | Model family |
| **B6** | **AMR-gene presence/absence features** | Mechanism instead of composition (**headline experiment**) |
| **B7** | B6 + k-mers + genus | Combined ("multimodal") model |
| **B8** | Species hold-out | Does it generalise across organisms? |

#### Step 8. Get AMR-gene features (B6)

- **Tool:** NCBI **AMRFinderPlus** (best choice; outputs gene symbols like `blaCTX-M-15`, `mecA`, `vanA` and point mutations like `gyrA_S83L`). Alternatives: **ResFinder**, or **RGI** (CARD).
- **Windows note:** AMRFinderPlus runs on Linux/macOS. Use **WSL2 + conda** (`conda install -c bioconda ncbi-amrfinderplus`) or a Google Colab notebook.
- **Pipeline:**
  1. Run AMRFinderPlus on every FASTA in `Data/fasta_output/` once, with `--organism` set where supported (E. coli, Salmonella, S. aureus, K. pneumoniae, P. aeruginosa…). Save one TSV per genome.
  2. Build a **genome × gene** binary matrix (≈ a few hundred columns) → cache as parquet.
  3. Join to the mapped AMR labels on `Genome ID`.
  4. Train LightGBM on `[gene features] + [antibiotic] + [drug_class] + [genus]`, grouped split.
- **Expected:** a large jump over k-mers for drugs with known genes (β-lactams, aminoglycosides, fluoroquinolones). Report per-antibiotic AUC.
- **Serving:** the web app can't run AMRFinderPlus on Windows/Railway easily. Options: (a) run it in the backend's Linux container on Railway (install via conda in a Dockerfile), or (b) use a lightweight fallback, such as searching the uploaded genome for a curated set of resistance-gene sequences with a k-mer/minimizer match. Decide based on time. Option (a) is cleaner.

#### Step 9. Deploy the better genome model

Whichever of B4/B6/B7 wins under the grouped split replaces the k-mer RF on `/predict`, with its own `metrics.json`. Show on the page **which resistance genes were found**. That makes the prediction explainable ("predicted Resistant to ceftriaxone because `blaCTX-M-15` was detected"), which is a big usability win.

---

### 6.3 Week 3: Platform features (T2.2, T2.3, T2.4, T2.6)

#### Step 10. Exports: CSV, PDF, PNG (T2.2)

For each of `/forecast`, `/predict`, `/timeline`:

| Format | How |
|---|---|
| **CSV** | New Flask route e.g. `/export/forecast.csv` that takes the last result (keep it in the session or re-post the inputs) and streams it with `Content-Disposition: attachment`. For timeline: one row per week |
| **PNG** | Plotly already supports it: `Plotly.downloadImage(el, {format:'png', filename:'timeline'})` on a "Download chart" button |
| **PDF** | Server-side with **ReportLab** or **WeasyPrint** (WeasyPrint needs GTK on Windows; ReportLab is simpler), or a print-optimised CSS + "Save as PDF" button as the minimum. PDF contents: inputs, prediction, probability, model name + version + AUC from `metrics.json`, charts, timestamp, and a disclaimer ("research tool, not a clinical diagnostic") |

Keep the ML vs. simulation labelling in the exports too: a timeline PDF must say **"Simulation, not a trained model"** on the page.

#### Step 11. Batch CSV upload (T2.3)

- On `/forecast` add a second tab: "Upload CSV".
- Accept a template with columns `antibiotic, genus, species, taxon_id, mic_value, mic_sign`. Provide a downloadable **sample template**.
- Backend: new endpoint `POST /api/forecast/batch/`. Validate each row, predict in one vectorised call, return per-row results + error column.
- Frontend: show a summary table (counts R/S, per-antibiotic breakdown chart) + "Download results CSV".
- Limits: max rows (e.g. 10,000) and max file size, enforced server-side.

#### Step 12. Security hardening (T2.4)

In `backend/backend/settings.py` and `backend/api/views.py`:

- [ ] `SECRET_KEY` from env **only**; crash at startup if missing when `DEBUG=False`
- [ ] `ALLOWED_HOSTS` from env, no `*` default in production
- [ ] Replace `CORS_ALLOW_ALL_ORIGINS=True` with `CORS_ALLOWED_ORIGINS=[<frontend URL>]`
- [ ] Protect `/api/train/` and `/api/reload/` with a token header (`X-Admin-Token` from env) at minimum; hide the Train page behind a password in the frontend
- [ ] `DATA_UPLOAD_MAX_MEMORY_SIZE` / `FILE_UPLOAD_MAX_MEMORY_SIZE` limits; reject FASTA > e.g. 20 MB
- [ ] Rate limiting on predict endpoints (`django-ratelimit`) to avoid abuse of the public deployment
- [ ] Remove the unused `db.sqlite3` and `migrate` release step, **or** start using a database (next step)
- [ ] Pin `scikit-learn==1.6.1` in `backend/requirements.txt` (or retrain and pin whatever you use)

#### Step 13 (optional). Database for prediction history

Only if you want to honour the "PostgreSQL" line: add one Django model `Prediction(created_at, page, inputs JSON, output JSON, model_version)`, use SQLite locally and Railway Postgres in production, and add a "History" page. Otherwise list PostgreSQL as a justified deviation ("stateless API; no user data is stored, which is also a privacy advantage").

#### Step 14. Library v0.2.0 (T2.6)

1. Copy the promoted artifacts + `metrics.json` into `amrpredict-lib/src/amrpredict/models/`.
2. Make the **backend import `amrpredict`** instead of keeping its own copies of the three engines (`backend/ml_models/*`). One source of truth means the k-mer-style bug can't reappear in only one copy.
3. `amrpredict.status()` returns the metrics.
4. Bump to `0.2.0`, update `CITATION.cff`, `docs/`, `known-issues.md` (move fixed items to "Fixed").
5. `python -m build`, then `twine upload --repository testpypi dist/*`. Optionally real PyPI. A `pip install amrpredict` line in the thesis is strong evidence for "the library is the main deliverable".

---

### 6.4 Week 4: Conditional proposal items (T3)

Get supervisor agreement on which of these you build (see §5 Tier 3). Each has a **minimal honest version**.

#### 6.4.1 Evolution forecasting + RL (C1): recommended

Three layers. Do (a) and (b) at minimum; (c) gives you a genuine RL component.

**(a) Fix and characterise the simulation**
- Fix the >100% bug in `mutation_timeline.py`: make susceptible, intermediate and resistant a proper partition (compute S = 100 − R − I and let I shrink when S hits 0). Remove the strict `xfail` in the library tests and add a passing test.
- Seed the random parts (`cumulative_mutations`, hotspot types) so identical inputs give identical output.
- **Sensitivity analysis (C1 in EXPERIMENT_PLAN):** sweep `speed` and `peak` ±30%, plot how `failure_week` moves. One figure answers "where did these constants come from and what if they're wrong?"

**(b) Literature calibration (C2 in EXPERIMENT_PLAN)**
- Collect 5 to 10 published serial-passage / adaptive-laboratory-evolution resistance curves (MIC fold-change over days/weeks) for drugs you support, e.g. ciprofloxacin in *E. coli*.
- Fit the logistic parameters per drug with `scipy.optimize.curve_fit`; report RMSE.
- The simulation becomes "calibrated against N published curves" instead of "hand-set constants".

**(c) A small reinforcement-learning agent**
- Wrap the simulation as a **Gymnasium** environment: *state* = current resistant fractions per drug; *action* = which antibiotic (or drug cycling/combination) to use this week; *reward* = −(infection burden) − (penalty for resistance growth).
- Train **PPO** or **DQN** with `stable-baselines3` for a few thousand episodes.
- Compare against fixed baselines (always drug A; simple cycling A→B→C). Report which policy delays treatment failure longest.
- **Framing:** "RL used to explore treatment strategies *within a simulated evolution model*". It matches the proposal's "reinforcement learning to simulate the evolution of resistance to a variety of selective pressures" without overclaiming.
- UI: a panel on `/timeline` labelled **"Simulation + RL policy (not trained on patient data)"**, per your ML-vs-simulation separation rule.

#### 6.4.2 GAN augmentation (C2): do as an experiment

- Use **CTGAN** (`pip install ctgan` or `sdv`) on the tabular training rows.
- Generate synthetic rows **only for under-represented groups** (rare antibiotics, rare genera, or the minority class).
- Experiment `A13_ctgan`: A2 config + synthetic rows in **train only**; evaluate on the untouched real test set. Also run species hold-out with augmentation.
- Report the synthetic-data quality metrics (SDV's `evaluate_quality`) and the AUC/AUPRC change with CIs.
- **Expected:** little or no gain (your learning curve is flat from 50 k rows). That's a *valid, publishable* negative result that directly answers the proposal's hypothesis. Say so.

#### 6.4.3 Generative drug design (C3): optional prototype or descope

If you build it, keep it small and clearly labelled:

1. **Data:** antibacterial actives from **ChEMBL** (compounds with measured MIC against *E. coli* / *S. aureus* / etc.), a few thousand SMILES.
2. **Model:** a character-level LSTM or small VAE on SMILES (PyTorch), or fine-tune a pretrained SMILES model. Keep it under a day of training on Colab.
3. **Conditioning on resistance profile (the proposal's link):** when the prediction module says an isolate is resistant to class X (e.g. fluoroquinolones), generate from / filter to scaffolds of **other** drug classes known to be active against that organism.
4. **Evaluation with RDKit:** validity %, uniqueness %, novelty % (vs. training set), QED, synthetic accessibility, Lipinski pass rate. Show 2D structure images (these count as the proposal's "images" export).
5. **Label:** "Computationally generated candidates, not synthesised or tested. For research exploration only."

If time is short: **descope** with a paragraph citing the proposal's own condition ("if there is time and resources") and point to refs [2]–[4] as the path forward.

#### 6.4.4 Images (C4) and full multimodal fusion (C5): descope

State: no public, labelled dataset of bacterial images paired with AST phenotypes was available at the needed scale in the project period. Collecting one needs a microbiology lab. The genome + metadata fusion (B7) is the multimodal element delivered. List images as future work (§9).

#### Step 15. Evaluation completeness (T2.5)

- Add **accuracy** and **recall (sensitivity)** and **specificity** columns to `metrics.py` and the RESULTS table. The proposal names accuracy and recall explicitly.
- **Calibration plot** (reliability diagram) for the deployed model, before and after calibration.
- **DeLong test** between A2/A10 and each alternative; **McNemar** at the chosen threshold.
- Re-run the key runs (A2, A10, best genome run) with **3 seeds**; report mean ± sd.
- **Per-antibiotic appendix**: AUC, n, prevalence, sorted ascending. Flag drugs near 0.5.

---

### 6.5 Week 5: Testing, deployment, write-up

#### Step 16. Tests (T2.7)

| Layer | What to test | Tool |
|---|---|---|
| Library | Existing 27 tests + new model loads, `metrics.json` present, timeline partition, determinism | `pytest` |
| Backend | Every endpoint: valid input → 200 + schema; missing fields → 400; oversized upload → 413; train/reload without token → 401 | Django `TestCase` + test client |
| Frontend | Every page renders (200) with backend mocked; export routes return the right `Content-Type` | Flask test client + `unittest.mock` |
| End-to-end | Start both servers, submit each form, download each export | Manual checklist or Playwright |
| Model | Regression test: 10 fixed inputs → fixed outputs (catches silent model changes) | `pytest` |

Optional: a GitHub Actions workflow running the library + backend tests on each push. Cheap, and it looks professional in the viva.

#### Step 17. Deploy and freeze (T4.4)

1. Set Railway env vars: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS` origin, `ADMIN_TOKEN`, `BACKEND_URL`.
2. Deploy both services; run the end-to-end checklist against the live URLs.
3. `git tag v1.0-submission && git push --tags`.
4. Record a 5-minute demo video as a backup in case the live site fails during the viva.

#### Step 18. Clean up the repo

- Fill or delete `forecasting_formulation.ipynb` (0 bytes).
- Update `README.md` §10–§11 and `CHANGES.md` "Still open" (several items will be closed; also the stale "XGBoost and CatBoost not installed" line, since A5/A5b have already run).
- Consider moving `Data/` (5 GB) out of git to Google Drive / DVC with a download script. Examiners cloning the repo will thank you. The `Data_Drive` link already exists.

#### Step 19. Write the report (T4.1)

Suggested chapter structure mapped to your material:

| Chapter | Content | Source material |
|---|---|---|
| 1 Introduction | Problem, motivation, objectives (from proposal) | Proposal |
| 2 Literature review | Tables 1 and 2 from the proposal, updated | Proposal |
| 3 Data | BV-BRC export, cleaning, label provenance (lab vs computational), data-quality issues | `experiments/HANDBOOK.md §3` |
| 4 Methodology | Features, target encoding, **leakage and how you removed it**, splits, metrics, genome features | HANDBOOK, EXPERIMENT_PLAN |
| 5 System design | Architecture diagram (Flask → Django → engines), library design, API table | README §2–§8 |
| 6 Results | Comparison table with CIs, ablations, learning curve, species hold-out, threshold trade-off, calibration, genome B-track, GAN/RL results | RESULTS.md + new runs |
| 7 Evaluation of the deployed system | Shipped-vs-new re-test, tests, security | `evaluate_shipped.py`, test reports |
| 8 **Deviations from proposal** | React→Flask, PostgreSQL→stateless, CNN/transformer→gradient boosting (measured, not guessed), images/drug-design descoped/prototyped, *why* | This document §4 |
| 9 Conclusion and future work | §9 of this document | |

The **honesty narrative** is your best asset: *"We found our own headline figure (0.93) was inflated, measured why, and rebuilt the evaluation."* Put it in the abstract.

---

## 7. Who does what

A suggested split, based on the proposal's roles (Ali: data; Hamza: models; Suleman: front/back-end). Adjust as needed.

| Member | Week 1 | Week 2 | Week 3 | Week 4 | Week 5 |
|---|---|---|---|---|---|
| **Hamza** (models) | T1.4 promote model, calibration, threshold | T2.1 B-track experiments, B6/B7 | T2.6 library v0.2.0 | T2.5 stats/seeds, RL agent | Results chapters |
| **Ali** (data) | T1.5 name normalisation, taxon regrouping, T1.2 | AMRFinderPlus runs, gene matrix | Batch-CSV template + validation | CTGAN experiment; literature curves for timeline calibration | Data + methodology chapters |
| **Suleman** (web) | T1.1, T1.3, T1.6 UI numbers | Genome-result UI (genes found) | T2.2 exports, T2.3 batch UI, T2.4 security | Timeline fix + RL panel UI | T2.7 tests, deploy, demo video, system-design chapter |

---

## 8. Definition of done: final checklist

**Models**
- [ ] Deployed tabular model is the promoted experiment (A10 or A2), not the July artifact
- [ ] `/predict` is deterministic and uses a real model; its number comes from `metrics.json`
- [ ] Genome model evaluated with a genome-grouped split; per-antibiotic results reported
- [ ] Threshold chosen on validation with a stated VME/ME rationale
- [ ] Calibration plot + Brier before/after
- [ ] Accuracy, recall, specificity, F1, AUC-ROC, AUPRC reported with 95% CIs
- [ ] DeLong/McNemar for the key comparisons; 3 seeds for key runs

**Proposal items**
- [ ] Ablations and cross-dataset/species hold-out in the report ✅ (already have)
- [ ] Evolution component: simulation fixed, sensitivity analysis, (calibration), (RL agent)
- [ ] GAN experiment run **or** descoped in writing
- [ ] Drug design prototype **or** descoped in writing
- [ ] Images descoped in writing
- [ ] Supervisor email confirming the scope decisions

**Platform**
- [ ] CSV / PDF / PNG export on all three tool pages
- [ ] Batch CSV upload with template
- [ ] Security checklist (§6.3 Step 12) complete
- [ ] No hardcoded metrics anywhere in templates
- [ ] ML vs. simulation labelling preserved in UI **and** exports
- [ ] Deployed on Railway, live URL works, demo video recorded

**Library**
- [ ] v0.2.0 with new models + metrics; backend imports it
- [ ] Published to TestPyPI (or PyPI); install instructions verified in a clean venv
- [ ] Tests pass; no `xfail` left for the timeline bug

**Documentation**
- [ ] Report with a Deviations chapter
- [ ] README/CHANGES updated; empty notebook resolved
- [ ] Git tag `v1.0-submission`

---

## 9. How to improve it after completion

Ordered roughly by value for effort. Good material for the "Future work" section and for turning the FYP into a paper.

### 9.1 Model quality
1. **Mechanism-aware genome models at scale.** AMR genes + point mutations + plasmid markers (PlasmidFinder), trained per drug class. This is where the literature's 0.90+ AUCs come from.
2. **DNA language models.** Embeddings from DNABERT-2, Nucleotide Transformer or Evo on resistance-gene regions as features; compare against gene presence.
3. **Multi-task learning** (EXPERIMENT_PLAN A8). Predict all antibiotics for an isolate jointly to exploit cross-resistance (e.g. ESBL → all 3rd-gen cephalosporins).
4. **MIC regression** instead of binary R/S. Predict the MIC itself, then apply EUCAST/CLSI breakpoints per species. More informative and breakpoint-version-proof.
5. **Uncertainty.** Conformal prediction so the tool can say "uncertain" instead of guessing, which matters for a clinical-facing tool.
6. **Explainability in the UI.** SHAP values per prediction ("MIC contributed +0.31, genus −0.05"); detected genes for genome predictions.

### 9.2 Making "Forecasting" literal
Your title promises forecasting, but the current models classify. A true forecast predicts **how resistance prevalence will change over time**:
- Fetch **collection year and country** for each Genome ID from the BV-BRC genome metadata API (your AMR CSVs don't carry them; `Testing Standard Year` is >96% missing).
- Build a time series of resistance rate per (organism, antibiotic, region, year).
- Forecast it with Prophet / ARIMA / gradient boosting on lagged features, validated with a **temporal split** (train ≤ 2018, test 2019+).
- Combine with WHO GLASS or ECDC surveillance data for population-level trends.
This would be the natural FYP-II or paper extension, and it answers the "why is it called forecasting?" question head-on.

### 9.3 Evolution and drug design
7. Replace hand-set timeline constants with parameters fitted to experimental-evolution datasets; move to a stochastic (Wright–Fisher / Gillespie) population model.
8. RL for **treatment policies** (cycling, combination, de-escalation) on the calibrated simulator; compare with published stewardship strategies.
9. Drug design: target-aware generation (e.g. against a specific β-lactamase structure), docking with AutoDock Vina, and ADMET filters, still clearly labelled in-silico.

### 9.4 Data
10. Add images (C4) through a collaboration with a microbiology lab: Gram-stain or colony images linked to AST results.
11. Add a local dataset (Pakistani hospital antibiograms) for external validation. Very strong for a thesis and for SDG 3 relevance.
12. Cross-dataset validation on an independent source (e.g. NCBI Pathogen Detection AST data, or the CRyPTIC TB dataset).

### 9.5 Engineering
13. **Docker** images for backend + frontend; `docker compose up` for one-command local runs.
14. **CI/CD** with GitHub Actions: tests + lint on every push, auto-deploy on tag.
15. **MLOps:** MLflow for experiment tracking (replaces `registry.csv`), DVC for data and models instead of committing 5 GB to git.
16. User accounts + PostgreSQL + saved projects/history; role-based access for the training page.
17. Async jobs (Celery/RQ) for long genome analyses and batch uploads, with progress bars.
18. A React (or HTMX) front end if you want richer interactivity. This also matches the original proposal.
19. Accessibility and mobile audit; Urdu translation for local clinical users.

---

## 10. Viva preparation

**Know these numbers cold:**

| Number | Meaning |
|---|---|
| 0.823 [0.820–0.827] | Honest tabular baseline (grouped split, out-of-fold encoding, 1.5 M rows) |
| 0.644 | The July-shipped LightGBM on unseen genomes (why you re-promoted) |
| 0.9255 / 0.93 | The old, inflated figure: explain the leakage + tiny-sample cause |
| 0.6545 | Antibiotic-only floor |
| 0.597 | Unseen genus (*Klebsiella* hold-out): no cross-genus generalisation |
| 0.40 → 0.47 | Threshold change: ME 46% → 34%, VME 10% → 20% |
| Flat learning curve from 50 k | Feature-limited → why gene features (B6), and why GANs likely won't help |
| *(new)* B6/B7 genome AUC | Your mechanism-vs-composition result |

**Questions to expect, and the short answer:**

| Question | Answer |
|---|---|
| "Why not deep learning / CNN / transformer as in the proposal?" | We measured it: boosting vs RF vs logistic differ by ≤0.02 on tabular data, and the notebook MLP / CNN-LSTM didn't beat simpler models. Choice was evidence-based. |
| "Is the timeline machine learning?" | No. It's a labelled simulation; we characterised it with sensitivity analysis (and calibration / RL on top). The UI says so everywhere. |
| "Why is it called forecasting?" | Predicts resistance before AST results exist (24 to 72 h earlier) + simulated evolution over weeks. True temporal forecasting is future work (§9.2), since the data has no collection dates. |
| "Where are GANs / drug design / images?" | Conditional in the proposal; agreed with supervisor on [date]. GAN run as an experiment: [result]. Drug design: [prototype / future work]. Images: no dataset. |
| "What's VME / ME and why do you care?" | VME = resistant isolate called susceptible (dangerous). ME = susceptible called resistant (wasteful). Threshold chosen to cap VME. |
| "How do you know you didn't leak?" | Genome-grouped split, out-of-fold encoding, threshold picked on validation, test set touched once. Pitfall checklist in EXPERIMENT_PLAN §11. |
| "Why Flask + Django instead of React?" | Server-rendered pages, no build step, frontend has zero ML dependencies so it deploys separately and small. |

**Demo order (5 minutes):** Home (live status) → `/forecast` single + batch CSV → download PDF → `/predict` with a FASTA showing detected genes → `/timeline` (say "simulation" first) → `/models` (honest numbers, CIs) → `pip install amrpredict` + one CLI call.

---

## 11. Appendix: file and command reference

### Key files

| Purpose | Path |
|---|---|
| K-mer bug line | `FYP1/backend/ml_models/resistance_predictor.py:158` |
| Correct fix to copy | `FYP1/amrpredict-lib/src/amrpredict/kmer.py:166` |
| Training data path | `FYP1/backend/train_models.py:412` (and caps at `:63`, `:290`) |
| Security settings | `FYP1/backend/backend/settings.py:6, 8, 50–51` |
| API routes | `FYP1/backend/api/urls.py` |
| Frontend routes | `FYP1/frontend/app.py` |
| Hardcoded AUC badges | `index.html:39`, `base.html:140`, `about.html:34,155,174,503,507`, `datasets.html:347` |
| Timeline simulation | `FYP1/backend/ml_models/mutation_timeline.py` |
| Experiment configs | `FYP1/experiments/configs/*.json` |
| Results table | `FYP1/experiments/RESULTS.md` |
| Promotion limitation | `FYP1/experiments/HANDBOOK.md §13` |
| Open-issue list | `FYP1/CHANGES.md` "Still open", `FYP1/amrpredict-lib/docs/known-issues.md` |

### Commands

```bash
# Run the app (Windows)
start.bat                                   # Django :8000 + Flask :5000

# Experiments
python experiments/run.py experiments/configs/A10_monotonic_mic.json
python experiments/report.py                # rebuild RESULTS.md
python experiments/evaluate_shipped.py      # re-test deployed models (~2 min)
python experiments/export_report.py         # refresh /models and /compare data

# Library
cd amrpredict-lib
pip install -e .[dev]
pytest
python -m build
twine upload --repository testpypi dist/*

# Production training (after fixing data_dir)
cd backend && python train_models.py --model all
```
