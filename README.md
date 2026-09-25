# AMR Intelligence Platform

*A walkthrough of how the whole system fits together, written from the code as it stands on 2026-09-24 (commit `52ae361`).*

> **Updated 2026-09-24.** The training data is now in `data/`, and a model
> experiment harness lives in [`experiments/`](experiments/) (§5.4). The headline
> accuracy figure has been re-measured (see §10).
> Document history: [CHANGES.md](CHANGES.md).
>
> **Updated 2026-09-25.** The deployed models have been re-tested on genomes they
> never trained on (§10), and the web app has two new pages, `/models` and
> `/compare`, that show every model, how the data is split, and what each model
> trained on (§8.1).

This is a companion to `PROJECT_DOCUMENTATION.md`, not a replacement. That file is the long reference (datasets, hyperparameters, CSS classes). This one covers what the system is, what its parts are, how a click becomes a prediction, and what is true about it today. Every claim was checked against the code or reproduced by running it. Where the two documents disagree, sections 10 and 11 say why.

---

## 0. The 60-second version

You built a full-stack antimicrobial-resistance (AMR) prediction system with **four deliverables**:

| # | Deliverable | Where | What it is |
|---|---|---|---|
| 1 | **Django REST API** | `backend/` | 8 endpoints, loads 3 prediction engines into memory at startup |
| 2 | **Flask web app** | `frontend/` | 14 routes, 11 pages, calls the Django API over HTTP |
| 3 | **`amrpredict` Python package** | `amrpredict-lib/` | The same three engines, cleaned up, pip-installable, with a CLI and tests |
| 4 | **Research notebooks** | `*.ipynb` | Where the models were originally designed and trained (Colab) |

And **three prediction engines**, of which only two are machine learning:

| Engine | Type | Input | Output | Trained? |
|---|---|---|---|---|
| LightGBM forecaster | Gradient-boosted trees | Antibiotic + taxonomy + MIC metadata | Resistant / Susceptible + probability | ✅ 217 trees on disk |
| K-mer classifier | RandomForest (100 trees) | Genome FASTA + antibiotic | Resistant / Susceptible + probability | ✅ trained, **but see §11.1, the web app never actually runs it** |
| Mutation timeline | Logistic-growth simulation | Genome FASTA + antibiotic | Week-by-week resistance curve | ❌ not a model, no AUC, by design |

The honesty about engine 3, labelling it a simulation everywhere in the UI rather than dressing it up as deep learning, is one of the stronger points of the project, and worth defending in a viva rather than hiding.

---

## 1. What the project does

**The problem.** Antimicrobial resistance means an antibiotic no longer kills the bacteria it used to. Clinically, you find out by culturing the isolate and measuring its MIC (minimum inhibitory concentration), slow, 24 to 72 hours. The premise here is: given data you already have (species, taxonomy, a partial MIC reading, or the genome sequence itself), predict the resistance call faster.

**The task.** Binary classification, **Resistant (1) vs Susceptible (0)**. `Intermediate` and `Nonsusceptible` phenotypes are folded into Resistant during cleaning (`backend/train_models.py:117-119`), a conservative choice: it is safer to over-call resistance than to miss it.

**The three questions the app answers**, one per page:

1. *"I have lab metadata for this isolate, will it resist drug X?"* → `/forecast` → LightGBM
2. *"I have the genome assembly, will it resist drug X?"* → `/predict` → K-mer RandomForest
3. *"If I treat with drug X, how fast does resistance take over the population?"* → `/timeline` → simulation

---

## 2. Repository map

```
FYP1/
├── backend/                     Django REST API (port 8000)
│   ├── backend/settings.py      Config; no auth/admin/sessions apps installed
│   ├── api/
│   │   ├── urls.py              8 routes under /api/
│   │   ├── views.py             All endpoint logic (266 lines, plain Django Views)
│   │   ├── apps.py              ready() → loads all models at process start
│   │   └── model_registry.py    Module-level singletons for the 3 engines
│   ├── ml_models/               The engines themselves
│   │   ├── lgbm_predictor.py    LightGBM + heuristic fallback
│   │   ├── resistance_predictor.py  K-mer RandomForest + heuristic fallback
│   │   └── mutation_timeline.py Logistic-growth simulation
│   ├── train_models.py          Production trainer: raw CSV/FASTA → artifacts
│   ├── trained_models/          6 committed artifacts (~7 MB) + model_report.json
│   ├── Procfile / railway.toml  Gunicorn deploy config
│   └── db.sqlite3               Exists but unused, there are no Django models
│
├── frontend/                    Flask app (port 5001 by default)
│   ├── app.py                   14 routes; a thin proxy over the Django API
│   ├── templates/               11 Jinja2 pages, all extending base.html
│   └── static/
│       ├── css/                 8 files: tokens → layout → components → … → dark
│       └── js/                  10 files, one per page + main.js + dropdowns.js
│                                + report-charts.js (shared by /models and /compare)
│
├── amrpredict-lib/              The packaged library (see §7)
│   ├── src/amrpredict/          Flat API, CLI, 3 predictors, bundled models
│   ├── tests/                   30 pytest tests
│   ├── docs/                    quickstart, api-reference, cli, known-issues
│   └── dist/                    Built wheel + sdist, v0.1.0
│
├── experiments/                 Model training & comparison harness (§5.4)
│   ├── algorithms/              One file per algorithm + registry
│   ├── lib/                     Cleaning, splitting, encoding, metrics
│   ├── configs/                 One JSON per experiment
│   ├── results/                 Per-run metrics, predictions and saved models
│   ├── run.py / report.py / predict.py
│   ├── evaluate_shipped.py      Re-tests the deployed models on unseen genomes
│   ├── export_report.py         Builds model_report.json for the web pages
│   └── HANDBOOK.md              Full documentation of the training setup
│
├── Data/                        The BV-BRC export (committed, 5 GB)
│   ├── amr_output/              3,655 per-species AMR CSVs
│   ├── mapped_output/           The same rows joined to FASTA paths
│   └── fasta_output/            Genome assemblies (4 GB)
│
├── *.ipynb                      Research notebooks (§6)
├── fasta_amr_map.py             Joins PATRIC CSV rows to GenBank FASTA files
├── start.sh / start.bat         One-command launchers (macOS/Linux, Windows)
├── train_all.bat                Windows training launcher
├── PROJECT_DOCUMENTATION.md     The long reference doc
└── EXPERIMENT_PLAN.md           Staged plan for model experiments
```

**The data is committed.** `Data/` holds 2.99 M raw AMR rows and 4 GB of FASTA, so the project runs from a clone alone; the 101 MB *Klebsiella* CSV is stored with Git LFS. `.gitignore` still excludes the experiment cache, saved experiment models and raw predictions. The artifacts in `backend/trained_models/` are committed binaries dated 10 July, trained before this data layout existed, see §11.2.

---

## 3. Architecture, and one request end-to-end

```
Browser
  │  form POST (multipart or urlencoded)
  ▼
Flask  frontend/app.py                    ← renders HTML, holds no ML code at all
  │  requests.post(BACKEND_URL + 'predict/')
  ▼
Django  backend/api/views.py              ← validates, calls the engine
  │  model_registry.get_kmer().predict(..)
  ▼
Engine  backend/ml_models/*.py            ← loaded once at startup, kept in RAM
  │  dict
  ▲───── JSON back up the same path, rendered into the same template
```

Two things about this shape:

- **The frontend is kept simple.** It never imports numpy, sklearn or lightgbm, only `flask` and `requests` (`frontend/requirements.txt`). That is why it deploys as a separate Railway service with a tiny image, and why the ML stack can be swapped without touching a template.
- **Models load once, not per request.** `api/apps.py` calls `model_registry.init_models()` in `ready()`, so the ~7 MB of artifacts is read at boot, not on every prediction. The registry is a plain module-level global with an idempotence guard (`if _lgbm is not None: return`).

### A worked trace: uploading a genome on `/predict`

1. **Browser** - `resistance_prediction.html` posts `antibiotic`, `threshold`, and either `fasta_file` or `fasta_text`. Client-side JS blocks submission if neither is present (`static/js/prediction.js`).
2. **Flask** (`app.py:115-150`), picks the branch: a file goes to Django as `multipart/form-data`; pasted text goes as JSON. If neither, it returns the page with an error rather than calling the backend.
3. **Django** (`api/views.py:95-128`), decodes the upload, rejects empty FASTA or empty antibiotic with HTTP 400, then calls the engine.
4. **Engine** (`ml_models/resistance_predictor.py:145-190`), strips FASTA headers and non-ACGT characters, caps at 500,000 bp, builds a 321-feature vector, asks the RandomForest for `predict_proba`, and applies the threshold.
5. **Back up**, the dict returns as JSON; Flask puts it in `result` and re-renders the same template, which now draws the probability bar and a Plotly bar chart of the top 20 k-mers.

Every page follows this pattern: **POST to itself, render the result inline.** There is no SPA, no client-side routing, no JSON API consumed by JavaScript except the dropdown lists.

---

## 4. The three prediction engines

All three share one design: a class with `_load()`, `predict()` and a `status` property; if the artifact is missing, `is_trained` stays `False` and a **heuristic fallback** answers instead. That fallback is what keeps the app demo-able on a fresh clone, and also what hides failures (§11.1).

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

**Threshold:** default 0.40, not 0.50, tuned toward recall, because a missed resistance call is the costlier error.

**Verified working.** Running the shipped artifacts: `ciprofloxacin`, taxon 562, MIC 4, `>=` → `Susceptible`, p=0.152, and identical on repeat calls (deterministic).

### 4.2 K-mer resistance predictor - `ml_models/resistance_predictor.py`

**Input:** FASTA text + antibiotic. **Model:** RandomForest, 100 trees, max_depth 15, `class_weight='balanced'`.

**The feature vector (321 dimensions):**

```
[ 256 4-mer frequencies ][ 62 antibiotic one-hot ][ GC, 1-GC, length/500000 ]
        AAAA … TTTT          the 62 drugs seen in training
```

A *k-mer* is just a substring of length k. With k=4 over {A,T,C,G} there are 4⁴ = 256 possible words; count each one across the genome and divide by the total, and you get a fixed-size fingerprint of the genome's composition regardless of how long it is. That is the whole trick, it turns a variable-length genome into a vector a classifier can eat, without alignment, gene calling or a reference database.

**Preprocessing:** headers dropped, everything lowercased→uppercased and non-ACGT stripped via a 256-char translation table, truncated at 500 kbp. Sequences under 100 bp are rejected with an error rather than a guess.

**⚠️ This engine is broken in the web app.** It loads, reports `trained: True`, and then every prediction silently falls back to a random heuristic. Full detail in §11.1, this is the most important item in this document.

### 4.3 Mutation timeline - `ml_models/mutation_timeline.py`

Not machine learning, and the code says so. Given a genome and an antibiotic it runs a **logistic growth model** over N weeks:

```
resistant(t) = r₀ + (peak − r₀) / (1 + e^(−k(t − midpoint)))
```

- `r₀`, starting resistant fraction, derived from how far the genome's GC content sits from 0.50, clamped to 2 to 15%
- `peak`, `k`, per-antibiotic constants from `ANTIBIOTIC_MUTATION_PROFILES` (13 drugs + a default). Carbapenems and colistin climb slowly to a low ceiling; ampicillin climbs fast to 95%. These numbers are hand-set from the literature, **not fitted**.
- `midpoint`, fixed at 45% of the simulated span

It also reports "mutation hotspots" (windows scored by GC content and nucleotide repetitiveness), resistance-gene activation weeks (`gyrA`, `blaTEM`, `mcr-1` …), MIC fold-change, and the **failure week**, the first week resistance crosses 50%.

Two caveats to state plainly if you present it: the resistance curve is deterministic, but `cumulative_mutations` (Poisson draw) and the hotspot mutation types (`np.random.choice`) are random, so those columns differ between identical runs. And the three population shares can exceed 100% in later weeks (§11.3).

---

## 5. Data pipeline and training

### The source data

| Dataset | Origin | Role |
|---|---|---|
| AMR phenotype CSVs | BV-BRC / PATRIC, one file per species | Labels + MIC + metadata → LightGBM |
| Genome FASTAs | GenBank, `taxon_<id>_<Genus>_<species>/` folders | Sequences → K-mer model |
| Mapped CSVs | Produced by `fasta_amr_map.py` | The join of the two |

### `fasta_amr_map.py`: the join

The two sources share no key directly, so this script builds one. CSV files are named `amr_taxon_108981_Acinetobacter_schindleri.csv` and FASTA folders `taxon_108981_../108981.12345.fasta`. It extracts the **taxon ID** from each filename to pair a CSV with a folder, then matches each row's **Genome ID** to a FASTA filename stem. Output per species: a `_mapped.csv` (original columns + `fasta_path`) and an `_unmatched.csv`, plus a global `mapping_summary.csv` with match percentages. Everything downstream depends on that `fasta_path` column.

### `backend/train_models.py`: the production trainer

Two functions, run with `--model lgbm|kmer|all`.

**`train_lgbm()`**
1. Load up to 500 CSVs from `amr_output/`, concatenate.
2. Clean (`clean_amr_data`): parse `Measurement` into `mic_sign` + `mic_value` with regex; split `Genome Name` into genus/species; map phenotypes to binary; extract the F1 score out of the free-text `Computational Method Performance` column; deduplicate on (Genome ID, Antibiotic), keeping lab-confirmed rows first.
3. Build the three target-encoding tables.
4. Split 80/20 stratified, then carve 15% of train for validation.
5. Train with `is_unbalance=True`, `num_leaves=63`, `lr=0.05`, up to 500 rounds with early stopping at 30. The shipped model stopped at **217 trees**.
6. Print AUC + classification report, dump test predictions to `report_figures/`, save 5 artifacts.

**`train_kmer()`**
1. Load mapped CSVs (falling back to `sample_mapped_output/` if the full set is absent).
2. For each row, read the FASTA at `fasta_path`, with a path-repair step, because the CSVs contain Windows paths written on another machine. Sequences are cached in a dict so a genome referenced by 20 antibiotic rows is read once.
3. Build the 321-vector, fit `StandardScaler` **on the 256 k-mer columns only**, train the forest, report, pickle `{model, scaler, ab_list, ALL_KMERS}`.

That "256 columns only" decision is correct in training and is exactly what inference gets wrong (§11.1).

### Training from the web UI

`/train` → Flask → `POST /api/train/` → Django spawns a **daemon thread** running the trainer, returns `{"status": "Training started"}` immediately, and reloads the model into the registry when it finishes. Progress is only visible through `/api/health/`. There is no authentication on this endpoint.

### 5.4 The experiment harness - `experiments/`

`train_models.py` trains the model the app serves. `experiments/` is a separate
system for training *candidate* models and comparing them, without touching
`backend/trained_models/`.

It exists because the original pipeline cannot answer "is variant A better than
variant B?" honestly, it fits target encodings on the full dataset before
splitting, splits rows randomly so one genome lands on both sides, caps itself
at 500 of the 3,655 CSVs, and prints its metrics to a console log that is then
discarded.

The harness fixes each of those and adds an audit trail:

| | |
|---|---|
| **Input** | all 3,655 CSVs → 1,525,796 clean rows (17× what `train_models.py` reads) |
| **Split** | genome-grouped by default; random and species-holdout available |
| **Encoding** | out-of-fold by default; the leaky version kept only for comparison |
| **Algorithms** | LightGBM, logistic regression, random forest, XGBoost, CatBoost, one file each under `algorithms/` |
| **Metrics** | AUC, AUPRC, F1, Brier, plus clinical VME/ME, with bootstrap CIs resampled by genome |
| **Output** | per-run `metrics.json`, `predictions.csv`, config snapshot, saved model, and a row in `results/registry.csv` |

```bash
python experiments/run.py experiments/configs/A2_oof_grouped.json
python experiments/report.py                    # comparison table
python experiments/predict.py --list            # saved models you can reload
```

Twenty-two runs so far. The headline numbers: the corrected baseline is **AUC 0.823**
(against 0.644 for the shipped artifact on genomes it never saw, see §10),
algorithm choice moves almost nothing, and the **threshold is the
highest-leverage decision in the project**, at the production 0.40, major error is 46%.

Two scripts turn the results into the web app's report pages:

```bash
python experiments/evaluate_shipped.py   # re-test the deployed models (~2 min)
python experiments/export_report.py      # write backend/trained_models/model_report.json
```

Full documentation in [experiments/HANDBOOK.md](experiments/HANDBOOK.md); the plan
behind it in [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md).

---

## 6. The notebooks, where the models came from

| Notebook | Cells | State | What it contains |
|---|---|---|---|
| `LightGBM_Model_Improved.ipynb` | 10 | ✅ with outputs | The real LightGBM development run, audit, cleaning, 5-fold CV, pseudo-labelling, final retrain |
| `resistance_prediction_model.ipynb` | 38 | outputs cleared | A **two-branch Keras MLP** (k-mer branch + antibiotic-embedding branch), the deep-learning design that the production RandomForest replaced |
| `bacterial_mutation_timeline.ipynb` | 43 | partial outputs | A **CNN-LSTM** with three heads (nucleotide, position, mutation probability), trained against per-antibiotic consensus genomes |
| `forecasting_formulation.ipynb` | n/a | **empty file (0 bytes)** | Nothing in it |

Two things follow from this table:

- **The notebooks and the backend are different lineages.** The notebook LightGBM was trained on one `BVBRC_genome_amr.csv` (121,589 raw → 90,826 clean rows, global resistance rate 0.3081). The artifacts actually shipped in `backend/trained_models/` have a global mean of **0.1662** and 76 antibiotic rates, which means they came from a `train_models.py` run over the per-species `amr_output/` CSVs, not from the notebook. Both are legitimate; just don't quote a notebook number for a backend artifact.
- **The deep-learning models were never deployed.** `mutation_timeline.py` looks for `mutation_timeline_model.pkl` and would use a CNN-LSTM if present; it is not present, so the simulation always runs. Similarly the Keras MLP became a RandomForest. The code paths for the neural versions still exist, which is why the UI says "CNN-LSTM available for training", accurate but easy to misread.

---

## 7. The `amrpredict` package

This is the newest layer (commit `52ae361`, September) and the most polished code in the repo. It takes the three engines out of Django and makes them a standalone library.

```python
import amrpredict
amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
amrpredict.predict_fasta(open('genome.fasta').read(), 'ampicillin')
amrpredict.simulate_timeline(fasta, 'imipenem', n_weeks=12)
amrpredict.antibiotics()   # the 62 the k-mer model knows
amrpredict.status()        # which models loaded
```

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
amrpredict predict genome.fasta ampicillin --threshold 0.6
cat genome.fasta | amrpredict timeline - imipenem --weeks 12
amrpredict antibiotics --compact | jq
```

**What differs from the backend copy**, these are the things worth listing in a report:

| | Backend | Library |
|---|---|---|
| Model loading | Eager, at Django startup | Lazy + thread-locked singleton (`registry.py`), nothing read until first call |
| Diagnostics | `print()` | `logging`, so `amrpredict antibiotics \| jq` isn't corrupted by stray output |
| Model dir | Required constructor arg | Defaults to models bundled inside the wheel (`_paths.py` via `importlib.resources`) |
| K-mer scaling | **Broken** (§11.1) | **Fixed**, scales only `feat[:256]` |
| Import cost | numpy/pandas/lightgbm at import | Deferred via module `__getattr__` |
| Tests | none | 30 pytest tests |

The bundled artifacts are **byte-identical** to `backend/trained_models/` (verified by MD5 on all six files), so the library and the web app carry the same models, they just don't run them the same way.

`docs/known-issues.md` in that folder is required reading before you quote any number from this project. It is unusually candid and it is where the k-mer bug is documented.

---

## 8. The frontend in detail

### Routes (`frontend/app.py`)

| Route | Methods | Backend call | Page |
|---|---|---|---|
| `/` | GET | `health/` | `index.html`, landing, live model status |
| `/forecast` | GET, POST | `forecast/` | `resistance_forecast.html` |
| `/predict` | GET, POST | `predict/` | `resistance_prediction.html` |
| `/timeline` | GET, POST | `timeline/` | `mutation_timeline.html` |
| `/train` | GET, POST | `train/` | `train.html` |
| `/datasets` | GET | n/a | `datasets.html`, the five datasets explained |
| `/about` | GET | n/a | `about.html`, methodology, team, metrics |
| `/library` | GET | n/a | `library.html` - `amrpredict` docs |
| `/models` | GET | `models/` | `models.html`, every model, the split, charts (§8.1) |
| `/compare` | GET | `models/` | `compare.html`, deployed vs experimental models and their data (§8.1) |
| `/reload` | POST | `reload/` | JSON, re-reads artifacts without a restart |
| `/api/health` | GET | `health/` | JSON passthrough |
| `/api/antibiotics` | GET | n/a | JSON, 48 names (hardcoded list) |
| `/api/organisms` | GET | n/a | JSON, 15 species |

### How the pages are built

- **One base template.** `base.html` holds the nav, footer, toast container, theme bootstrap and the CDN links (Bootstrap 5.3, Bootstrap Icons, Inter + JetBrains Mono, Plotly 2.26). Every page extends it and fills `{% block content %}` + `{% block scripts %}`.
- **CSS is layered, not monolithic:** `tokens` (colour/spacing variables) → `layout` → `components` → `utilities` → `charts` → `animations` → `dark`. Dark mode is a `data-theme="dark"` attribute on `<html>`, set before first paint by an inline script so there's no flash, and persisted in `localStorage`.
- **JS is one file per page** plus `main.js` (the global `window.AMR` helper: Plotly theme fragment, toasts) and `dropdowns.js`.
- **Dropdowns populate themselves.** Any `<select data-populate="antibiotics">` is filled by `dropdowns.js` from `/api/antibiotics`, cached in `sessionStorage` for the tab, with `data-selected="…"` restoring the choice after a POST. That's why the antibiotic list lives in exactly one place per source.
- **Charts are server-data → inline JSON → Plotly.** The template writes `<script type="application/json" id="kmer-chart-data">{{ result.top_kmers | tojson }}</script>` and the page script parses it. No API call, no template-inlined JavaScript data.

### 8.1 The report pages: `/models` and `/compare`

Both pages are listed under **ML Models** in the navbar. They read one file,
`backend/trained_models/model_report.json`, which the Django endpoint
`GET /api/models/` serves with a live "is the model loaded" flag added. The file
is committed so the deployed backend can serve it without the data or the
experiment outputs. Rebuild it with the two scripts in §5.4.

| Page | Sections |
|---|---|
| `/models` | Best model; how train and test are split (row counts, the four steps, random vs grouped split drawn per genome); deployed models re-tested on seen vs unseen genomes; all 22 runs with AUC and confidence intervals, ROC curves, learning curve, VME vs ME trade-off, results table; confusion matrix and best and worst antibiotics for the best run |
| `/compare` | Where each model's training data comes from; a side-by-side table of the two deployed models and the best experiment; training set size, reported vs unseen-genome AUC, genus mix heatmap and label mix; a table of all 24 models and their data |

Chart colours are CSS tokens (`--viz-1` to `--viz-5`, `--viz-other`) defined in
`tokens.css` and stepped for the dark surface in `dark.css`, checked for
colour-blind separation. Shared chart code lives in `static/js/report-charts.js`.
Tiles whose value is not a single number (for example "9 vs 37") carry the
`stat-mini-static` class so the count-up animation in `main.js` skips them.

---

## 9. Running, training, deploying

### Local (macOS/Linux)

```bash
./start.sh
```

Creates `.venv` if missing, installs both requirement sets, checks for **libomp** (LightGBM's OpenMP dependency, without it `import lightgbm` fails on macOS and the forecaster silently degrades to heuristics), starts Django on 8000, waits for `/api/health/` to answer, starts Flask on **5055** (not 5000, macOS AirPlay Receiver owns that port), opens the browser, and tears down both process groups on Ctrl-C.

Windows: `start.bat` (ports 8000 + 5000, two `cmd` windows).

### Training

```bash
cd backend && python train_models.py --model all     # or lgbm / kmer
```
Windows: `train_all.bat`. Both need the raw data directories, which are not in the repo.

### Deployment (Railway, two services)

| | Backend | Frontend |
|---|---|---|
| Start | `gunicorn backend.wsgi:application --workers 2 --timeout 120` | `gunicorn app:app --workers 2 --timeout 120` |
| Health check | `/api/health/` | `/` |
| Key env vars | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | `BACKEND_URL`, `PORT`, `LIB_VERSION` |

`frontend/app.py` infers its mode from `PORT`: if Railway sets it, `debug=False`; locally with no `PORT`, debug is on.

---

## 10. The numbers, and where each one comes from

There are several AUC figures in circulation in this project. They are not contradictory, they come from different runs on different data, but you should know which is which before a viva.

| Number | Source | What it measures |
|---|---|---|
| **0.8881** | `LightGBM_Model_Improved.ipynb`, cell 5 output | Test AUC of the notebook model, 18,166 held-out rows from the single BV-BRC CSV |
| **0.8815 ± 0.0003** | same notebook, 5-fold CV | Stability check, very tight, so no fold-luck |
| **0.8872** | same notebook, after pseudo-labelling | Final notebook model. Pseudo-labelling added 25,214 rows and *did not* improve test AUC |
| **0.9255** | `PROJECT_DOCUMENTATION.md:2088`, a `train_models.py` console log | The shipped backend artifact, trained on the per-species `amr_output/` CSVs |
| **0.9290** | `PROJECT_DOCUMENTATION.md:1928` | Claimed K-mer RF test AUC, see the caveat below |
| **0.93** | UI badges throughout | Rounded, for both models |

**Superseded as of 2026-09-24.** The `experiments/` harness re-measured this on the
full export (1.53 M rows) under a grouped split with out-of-fold encoding:
**AUC 0.8232 [0.8200-0.8269]**. The 0.9255 is not directly comparable, it came
from a seventh of the data under a protocol that fitted encodings on the test
rows. Quote 0.823 and explain the difference; see
[experiments/HANDBOOK.md §11](experiments/HANDBOOK.md).

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
than guessing from the antibiotic alone (0.703). Both pages in §8.1 show these
numbers.

Two caveats:

1. **No metrics ship with the artifacts.** `train_models.py` prints AUC and throws it away; nothing is written into the model files. So every number in the UI and the docs is hand-transcribed from a console log of a run whose data is no longer in the repo. If anyone retrains, the badges will silently go stale. The fix is small: write a `metrics.json` next to the models and read it in `status()`.
2. **The K-mer AUC is measured on the training-time path, not the serving path.** Training computes it correctly. Serving never reaches the model at all (§11.1), so the 0.93 badge on `/predict` does not describe what that page is doing.

Other counts to keep straight:

| Thing | Count | Where |
|---|---|---|
| Antibiotics offered in the UI dropdowns | 48 | `frontend/app.py:ANTIBIOTICS` |
| Antibiotics the K-mer model knows | 62 | `ab_list` inside the pickle |
| Antibiotics with a LightGBM rate table | 76 | `ab_rate_full.joblib` |
| Drug classes mapped | 14 | `DRUG_CLASS_MAP` (48 entries) |
| Organisms in the quick-select | 15 | `frontend/app.py:BACTERIA_LIST` |
| LightGBM trees / leaves | 217 / 63 | the `.txt` model file |
| K-mer forest | 100 trees, depth 15, 321 features | the pickle |

The 48-vs-62 gap means 14 antibiotics the k-mer model was trained on can never be selected in the web UI. Not a bug, but a rough edge.

---

## 11. Verified issues and gaps

Each of these was reproduced or read directly in the code today, not inferred.

### 11.1 The K-mer model never runs in the web app 🔴

`train_models.py` fits the scaler on the **256 k-mer columns only**. `resistance_predictor.py:158` hands it the **full 321-element vector**:

```python
feat = self.scaler.transform(feat.reshape(1, -1))[0]   # ValueError
```

Reproduced against the shipped artifacts:

```
[K-mer] Model loaded. Antibiotics: 62
[K-mer] Prediction error: X has 321 features, but StandardScaler is expecting 256 features as input.
prob run1: 0.3363   run2: 0.3552   model_used: 'RandomForest K-mer (trained)'
```

Three consequences:

- The `except Exception` around it swallows the error and calls `_heuristic_predict()`, a GC-content formula with `np.random.uniform(-0.04, 0.04)` noise. The same genome gives a different answer every time.
- The response still says `'model_used': 'RandomForest K-mer (trained)'`, because `is_trained` refers to *loading*, not *predicting*. Nothing in the UI reveals the fallback.
- Any accuracy figure quoted for the `/predict` page is meaningless.

The fix is one line, and it is already written and tested in the library (`amrpredict-lib/src/amrpredict/kmer.py:166`):

```python
feat[:N_KMERS] = self.scaler.transform(feat[:N_KMERS].reshape(1, -1))[0]
```

Porting it to `backend/ml_models/resistance_predictor.py` is the highest-value change available in this repo. It is not applied here because this document was asked to explain the project, not change it, say the word and it is a two-minute edit plus a re-check.

### 11.2 Training cannot run from a fresh clone

The trainer looks for `amr_output/`, `mapped_output/` and `fasta_output/` directly inside the project root (`train_models.py:412`, `data_dir = ROOT_DIR`), but the data lives in `Data/`. So `POST /api/train/` starts its thread, prints `[Data] amr_output not found`, and returns `False`, while the UI has already reported "Training started". The fix is to point `data_dir` at `os.path.join(ROOT_DIR, 'Data')`, or to symlink the three folders into the root. The committed models in `trained_models/` date from 10 July; §10 shows which files they were trained on.

### 11.3 Timeline population shares exceed 100%

Once the susceptible pool empties (~week 7 at default settings), `susceptible` clamps at 0, `intermediate` pins at 25.0, and `resistant` keeps growing, so the three sum to 106% by week 8. Documented as a deliberate `xfail` in the library's test suite (`test_timeline_compartments_partition_the_population_throughout`) so that fixing it can't happen silently. Don't present late weeks as population percentages.

### 11.4 Security posture is demo-grade

Fine for an FYP, worth naming before someone else does: `SECRET_KEY` has a hardcoded fallback; `ALLOWED_HOSTS` defaults to `*`; `CORS_ALLOW_ALL_ORIGINS = True`; `csrf_exempt` on every POST view; and `/api/train/` and `/api/reload/` are unauthenticated, anyone who can reach the deployed backend can kick off training or force a model reload.

### 11.5 Smaller things

- `db.sqlite3` and the `migrate` release command exist, but there are no Django models, no `django.contrib.auth`, no sessions. The database is vestigial.
- `forecasting_formulation.ipynb` is a 0-byte file.
- `*_fraction` fields in the timeline are on a **0 to 100** scale despite the name; renaming would break the templates, so the name stands.
- `kmer_resistance_model.pkl` was pickled with scikit-learn 1.6.1; loading under a different 1.x warns and is not guaranteed identical. The library pins `<2.0` so a 2.x install fails loudly instead of being quietly wrong. The backend has no such pin (`scikit-learn>=1.3`).
- `PROJECT_DOCUMENTATION.md:726` states the scaler "is applied identically at inference time." That was the intent; §11.1 is what the code does.

---

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

---

## 13. Reading order for someone new to the repo

1. `frontend/app.py`, 250 lines, and it shows you every feature the system has
2. `backend/api/views.py`: the eight endpoints and their validation rules
3. `backend/ml_models/lgbm_predictor.py`: the cleanest of the three engines
4. `backend/train_models.py`, where the features actually come from
5. `experiments/HANDBOOK.md`: the training setup, data fields and measured results
6. The `/models` and `/compare` pages in the running app: every model's results and training data, with charts
7. `amrpredict-lib/docs/known-issues.md`: the account of what is broken
8. `LightGBM_Model_Improved.ipynb`, the research story, with outputs intact
9. `PROJECT_DOCUMENTATION.md`: the deep reference, once you know the shape

If you only have ten minutes before a demo: know that engine 3 is a simulation and say so unprompted, and know that `/predict` is currently answering from a fallback heuristic (§11.1).
