# AMR Intelligence Platform — Complete Project Documentation

**Antimicrobial Resistance Prediction & Mutation Timeline System**  
Final Year Project (FYP) — Biomedical Informatics / Machine Learning  
Author: Hamza Afzal | Last updated: 2026-05-06

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Configuration & Settings](#3-configuration--settings)
4. [File Structure](#4-file-structure)
5. [Datasets](#5-datasets)
6. [Machine Learning Models — Detailed](#6-machine-learning-models--detailed)
   - 6.1 [LightGBM Resistance Forecaster](#61-lightgbm-resistance-forecaster)
   - 6.2 [K-mer Resistance Predictor](#62-k-mer-resistance-predictor)
   - 6.3 [Mutation Timeline — Biological Simulation (NOT ML)](#63-mutation-timeline--biological-simulation-not-ml)
7. [Training Pipeline — Step by Step](#7-training-pipeline--step-by-step)
8. [Model Registry & Startup Sequence](#8-model-registry--startup-sequence)
9. [Backend API — Full Reference](#9-backend-api--full-reference)
10. [Frontend Application — Full Reference](#10-frontend-application--full-reference)
11. [Data Flow Diagrams](#11-data-flow-diagrams)
12. [Performance Metrics](#12-performance-metrics)
13. [Technology Stack](#13-technology-stack)
14. [How to Run](#14-how-to-run)
15. [Scientific Sources & Citations](#15-scientific-sources--citations)
16. [Known Limitations](#16-known-limitations)
17. [Changelog](#17-changelog)

---

## 1. Project Overview

The **AMR Intelligence Platform** is a full-stack bioinformatics application for predicting antimicrobial resistance (AMR) in bacterial pathogens. It uses **two trained machine learning models** and one **mathematical biological simulation tool**.

> AMR is ranked by the WHO as one of the [top ten global public health threats facing humanity](https://www.who.int/news-room/spotlight/ten-threats-to-global-health-in-2019). In 2019, bacterial AMR was directly responsible for **1.27 million deaths** and associated with **4.95 million deaths** globally (Murray et al., *The Lancet*, 2022).

### Core Objectives

- Predict whether a bacterial isolate is **Resistant** or **Susceptible** to specific antibiotics using tabular genomic metadata (LightGBM model)
- Predict resistance directly from raw whole-genome FASTA sequences via 4-mer frequency profiling (K-mer RandomForest model)
- Simulate week-by-week mutation-driven resistance evolution using a logistic growth equation (biological simulation — not ML)
- Provide an interactive browser-based interface with real-time API-backed predictions

### Classification Task

Binary classification: **Resistant (R)** vs **Susceptible (S)**  
Intermediate (I) and Nonsusceptible phenotypes are merged into Resistant during preprocessing.

### Important Distinction: ML Models vs Simulation Tool

| Component | Type | Trained on real data? | Has AUC score? | Output |
|-----------|------|----------------------|----------------|--------|
| LightGBM Forecaster | **Trained ML model** | Yes — 90,826 records | Yes — 0.9255 | Resistant / Susceptible + probability |
| K-mer RandomForest | **Trained ML model** | Yes — 6,002 genome pairs | Yes — 0.9290 | Resistant / Susceptible + probability |
| Mutation Timeline | **Mathematical simulation** | No | No — outputs are simulated | Week-by-week resistance curve |

---

## 2. System Architecture

```
Browser (User)
      │  HTTP on port 5000
      ▼
┌─────────────────────────────────────────┐
│     Flask Frontend (Port 5000)          │
│  frontend/app.py — 11 routes            │
│  Templates: Jinja2 HTML (8 pages)       │
│  Static: style.css, main.js             │
│  Bacteria list: 15 species              │
│  Antibiotics list: 48 antibiotics       │
└─────────────┬───────────────────────────┘
              │ HTTP proxy via requests library
              │ BACKEND_URL = http://127.0.0.1:8000/api
              ▼
┌─────────────────────────────────────────┐
│   Django REST API (Port 8000)           │
│  backend/api/views.py — 7 View classes  │
│  backend/api/urls.py — 7 URL patterns   │
│  backend/api/model_registry.py          │
│  Middleware: CORS (django-cors-headers) │
└──────┬──────────┬────────────┬──────────┘
       │          │            │
       ▼          ▼            ▼
┌───────────┐ ┌──────────┐ ┌──────────────────┐
│ LightGBM  │ │ K-mer RF │ │ Timeline Sim     │
│ Forecaster│ │ Predictor│ │ (logistic math)  │
│ lgbm.txt  │ │ kmer.pkl │ │ no trained file  │
│ AUC 0.9255│ │ AUC 0.929│ │ simulated output │
└───────────┘ └──────────┘ └──────────────────┘
       │              │
       └──────────────┘
  backend/trained_models/ (6 artifact files)
```

### Two-Tier Architecture

| Tier | Technology | Port | Responsibility |
|------|------------|------|---------------|
| Frontend | Flask 3.x | 5000 | Template rendering, form handling, file upload handling, API proxying |
| Backend | Django 4.x + DRF | 8000 | ML inference, model lifecycle, CORS, REST endpoints |

Flask acts as a reverse proxy: all API calls from the browser go to Flask, which forwards them to Django's REST API using the `requests` library and returns the JSON response. This decoupling allows the frontend and backend to be run on different machines simply by changing `BACKEND_URL`.

### Request Flow for a Typical Prediction

```
User fills form → Flask /forecast POST
  → Flask backend_post('forecast/', json_data=payload)
  → Django POST /api/forecast/
    → ResistanceForecastView.post()
    → model_registry.get_lgbm().predict(...)
    → LGBMResistancePredictor.predict() → returns dict
    → also calls model.get_drug_class_summary()
    → also runs comparison chart (8 antibiotics × predict())
  → Django returns JsonResponse
  → Flask returns jsonify(data) to browser
User sees results
```

---

## 3. Configuration & Settings

### Django Settings (`backend/backend/settings.py`)

```python
BASE_DIR = Path(__file__).resolve().parent.parent   # = backend/
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders',           # CORS handling
    'rest_framework',        # DRF
    'api',                   # Our application
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',   # Must be first
    'django.middleware.common.CommonMiddleware',
]

# CORS — allows Flask frontend on port 5000 to call the API
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',   # needed for file uploads
    ],
}

# ML artifact directories — auto-resolved at startup
TRAINED_MODELS_DIR = BASE_DIR / 'trained_models'   # backend/trained_models/
DATA_DIR           = BASE_DIR.parent                # FYP1/ root

AMR_OUTPUT_DIR    = DATA_DIR / 'amr_output'         # 3,655 AMR CSVs
MAPPED_OUTPUT_DIR = DATA_DIR / 'mapped_output'      # 1,684 joined CSVs
FASTA_OUTPUT_DIR  = DATA_DIR / 'fasta_output'       # 1,684 taxon FASTA folders
```

> **No database is used for predictions.** The SQLite database (`db.sqlite3`) is required by Django's migration system but no prediction data is read from or written to it. All inference is done in-memory by the loaded model objects.

### Flask Settings (`frontend/app.py`)

```python
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000/api')
# Override by setting BACKEND_URL environment variable for deployment

app.secret_key = 'fyp-flask-frontend-2024'
# Not used for actual sessions — just required by Flask
```

---

## 4. File Structure

```
FYP1/
├── PROJECT_DOCUMENTATION.md            ← This file
│
├── backend/                            ← Django project root
│   ├── manage.py                       ← Django management commands
│   ├── requirements.txt                ← Backend Python dependencies
│   ├── db.sqlite3                      ← SQLite (Django migrations only)
│   ├── train_models.py                 ← Standalone training script
│   │
│   ├── backend/                        ← Django project package
│   │   ├── settings.py                 ← All configuration (paths, CORS, DRF)
│   │   ├── urls.py                     ← Root URL: includes api.urls
│   │   └── wsgi.py                     ← WSGI entrypoint
│   │
│   ├── api/                            ← Django app: REST endpoints
│   │   ├── apps.py                     ← ApiConfig.ready() → init_models()
│   │   ├── model_registry.py           ← Global singleton: _lgbm, _kmer, _timeline
│   │   ├── urls.py                     ← 7 URL patterns
│   │   └── views.py                    ← 7 View classes (csrf_exempt)
│   │
│   ├── ml_models/                      ← Predictor classes
│   │   ├── lgbm_predictor.py           ← LightGBM (tabular AMR → Resistant/Susceptible)
│   │   ├── resistance_predictor.py     ← K-mer RF (FASTA → Resistant/Susceptible)
│   │   └── mutation_timeline.py        ← Logistic growth biological simulation
│   │
│   └── trained_models/                 ← Generated artifacts (after running train_models.py)
│       ├── amr_lgbm_final_model.txt    ← LightGBM booster in text format (~5MB)
│       ├── ab_rate_full.joblib         ← pandas Series: antibiotic → resistance rate
│       ├── taxon_ab_rate_full.joblib   ← DataFrame: (Taxon ID, Antibiotic) → rate
│       ├── genus_ab_rate_full.joblib   ← DataFrame: (genus, Antibiotic) → rate
│       ├── lgbm_meta.joblib            ← dict: {global_mean: 0.1662}
│       └── kmer_resistance_model.pkl   ← dict: {model, scaler, ab_list, ALL_KMERS}
│
├── frontend/                           ← Flask project
│   ├── app.py                          ← Flask app, 11 routes, proxy helpers
│   ├── requirements.txt                ← Frontend Python dependencies
│   │
│   ├── templates/                      ← Jinja2 HTML pages
│   │   ├── base.html                   ← Shared navbar + footer (all pages inherit this)
│   │   ├── index.html                  ← Landing page with hero panel + stats
│   │   ├── resistance_forecast.html    ← LightGBM tabular prediction form
│   │   ├── resistance_prediction.html  ← K-mer FASTA prediction + file upload
│   │   ├── mutation_timeline.html      ← Bio-simulation + Plotly chart
│   │   ├── datasets.html               ← Dataset catalog with schema tables
│   │   ├── about.html                  ← Project info + 7 hyperlinked references
│   │   └── train.html                  ← Training control panel
│   │
│   └── static/
│       ├── css/style.css               ← Full design token system (light theme)
│       └── js/main.js                  ← Chart rendering, form logic, AJAX
│
├── amr_output/                         ← 3,655 BVBRC AMR CSV files (LightGBM data)
├── fasta_output/                       ← 1,684 taxon subdirs (NCBI WGS FASTA files)
├── mapped_output/                      ← 1,684 joined AMR+genome CSVs (K-mer data)
│
└── notebooks/
    └── *.ipynb                         ← EDA and prototyping notebooks
```

---

## 5. Datasets

### Overview

| # | Name | Source | Format | Size | Purpose |
|---|------|--------|--------|------|---------|
| 1 | BVBRC AMR Records | [BVBRC / PATRIC](https://www.bv-brc.org/) | CSV | 3,655 files | LightGBM training |
| 2 | NCBI GenBank WGS Sequences | [NCBI GenBank](https://www.ncbi.nlm.nih.gov/genbank/) | FASTA | 1,684 folders · 2,587 files | K-mer RF training |
| 3 | Mapped AMR + Genome Records | Derived (inner join) | CSV | 1,684 files | Links phenotypes → FASTA |
| 4 | Sample Subsets | Derived | CSV/FASTA | Small | Dev & unit testing |
| 5 | Jupyter Notebooks | Generated | .ipynb | 6+ notebooks | EDA, prototyping |

---

### Dataset 1 — BVBRC AMR Records (`amr_output/`)

**Source:** Bacterial and Viral Bioinformatics Resource Center (BVBRC), formerly PATRIC  
**URL:** https://www.bv-brc.org/  
**Reference:** Olson RD et al. (2023). *Nucleic Acids Research*, 51(D1), D678–D689.  
→ https://academic.oup.com/nar/article/51/D1/D678/6840395  
**Format:** CSV — one file per bacterial taxon/species  
**Count:** 3,655 CSV files total; up to 500 loaded per training run  
**Cleaned records used in training:** ~24,983 (500-file run) — full dataset ~90,826

**Key columns in each CSV file:**

| Column | Type | Description |
|--------|------|-------------|
| `Genome ID` | String | Unique BVBRC genome identifier |
| `Taxon ID` | Integer | NCBI taxonomy identifier |
| `Genome Name` | String | "Genus species strain" — parsed into genus + species |
| `Antibiotic` | String | Antibiotic name (mixed case — normalized in preprocessing) |
| `Resistant Phenotype` | String | Resistant / Susceptible / Intermediate / Nonsusceptible |
| `Measurement` | String | MIC string — e.g. `"<=0.5"`, `">32"`, `"4"` |
| `Measurement Value` | Float | Numeric MIC (fallback if Measurement lacks a number) |
| `Laboratory Typing Method` | String | MIC, Disk diffusion, Gradient strip, etc. |
| `Computational Method Performance` | String | Contains `"F1 score: 0.85"` for computational derivations |
| `Evidence` | String | `"Laboratory Method"` or `"Computational Prediction"` |

**Phenotype label mapping (applied during cleaning):**

```python
merge_map = {
    'Susceptible':    'Susceptible',
    'Resistant':      'Resistant',
    'Intermediate':   'Resistant',    # merged into Resistant
    'Nonsusceptible': 'Resistant',    # merged into Resistant
}
```

**Full preprocessing pipeline (`clean_amr_data()` in `train_models.py`):**

1. Parse MIC sign (`<=`, `>=`, `<`, `>`, `=`, `exact`, `unknown`) via regex on `Measurement` column
2. Parse MIC numeric value — first decimal match in string; fall back to `Measurement Value` column
3. Compute `has_mic` (1 if value was parseable, else 0) and `mic_log = log1p(mic_value)`
4. Extract genus and species from `Genome Name`: split on whitespace, capitalize genus, lowercase species
5. Map phenotype label using `merge_map` above; drop records with unknown phenotypes
6. Create binary `target`: 1 = Resistant, 0 = Susceptible
7. Normalize antibiotic name: `.str.strip().str.lower()`
8. Map antibiotic → drug class via `DRUG_CLASS_MAP` (defaults to `'other'` if not found)
9. Compute `is_lab_confirmed = 1` if `Evidence == 'Laboratory Method'`, else 0
10. Extract F1 score from `Computational Method Performance` string via regex `"F1 score:\s*([\d.]+)"`; lab-confirmed rows get `computational_f1 = 1.0`; missing values get `0.85`
11. **Deduplicate** by `(Genome ID, Antibiotic)` — sort by `is_lab_confirmed DESC`, keep first (prefers lab-confirmed over computational)
12. Compute **target encodings** (computed on training data, saved as joblib files):
    - `ab_resistance_rate` = mean(target) grouped by `Antibiotic`
    - `taxon_ab_resistance_rate` = mean(target) grouped by `(Taxon ID, Antibiotic)` — only groups with ≥ 3 records
    - `genus_ab_resistance_rate` = mean(target) grouped by `(genus, Antibiotic)` — only groups with ≥ 3 records

---

### Dataset 2 — NCBI GenBank WGS Sequences (`fasta_output/`)

**Source:** NCBI GenBank — Whole Genome Shotgun (WGS) sequences  
**URL:** https://www.ncbi.nlm.nih.gov/genbank/  
**Accession format:** `>accn|AFAS01000222` (NCBI WGS accession number in header)  
**Structure:** 1,684 species/taxon subdirectories, each containing one or more FASTA files  
**Total FASTA files:** 2,587  
**Represented species:** 17 major bacterial pathogens including *E. coli*, *K. pneumoniae*, *S. aureus*, *P. aeruginosa*, *Salmonella*, *Campylobacter*, etc.

**Example FASTA file content:**
```
>accn|AFAS01000222 Staphylococcus aureus subsp. aureus MRSA252 ...
ATGCGATCGATCGATCGATCGATCGATCG...
>accn|AFAS01000223 Staphylococcus aureus subsp. aureus MRSA252 ...
GCTAGCTAGCTAGCTAGCTAGCTAGCTAG...
```

**How FASTA files are processed in the K-mer pipeline:**
1. Open file, iterate lines — skip all lines starting with `>`
2. Strip non-ATCG characters (uppercase, remove N, whitespace, etc.) via a pre-built translation table
3. Concatenate all contigs into a single sequence
4. Cap at `max_bp = 500,000` base pairs (to limit memory use)
5. Compute 4-mer sliding window counts across the full sequence
6. Normalize counts by total k-mers → 256-dimensional relative frequency vector

---

### Dataset 3 — Mapped AMR + Genome Records (`mapped_output/`)

**Source:** Inner join of BVBRC AMR records with available NCBI genome FASTA files  
**Format:** CSV — 1,684 files, one per taxon (same structure as `amr_output` + extra column)  
**Extra column:** `fasta_path` — absolute path to the FASTA file on disk for that genome  
**Used for:** K-mer RF training — provides `(fasta_path, antibiotic, resistance_label)` triples  
**Training samples built:** 6,002 genome–antibiotic pairs  
**Skipped records:** FASTA files that were referenced but missing from disk are silently skipped

**FASTA path resolution (K-mer training):**
```python
# If absolute path doesn't exist, try resolving relative to fasta_dir
# Looks for 'fasta_output' segment in the stored path
# Falls back to basename match in fasta_dir
```

---

### Dataset 4 — Sample Subsets

Located in `sample_mapped_output/` and `sample_fasta_output/` when full data is unavailable.  
The K-mer training script automatically falls back to these directories if `mapped_output/` is missing.  
Used for: rapid development iteration, unit testing, CI without downloading full dataset.

---

### Dataset 5 — Jupyter Notebooks (`notebooks/`)

EDA notebooks covering:
- Antibiotic frequency distribution across all BVBRC files
- Resistance rate per species and drug class
- MIC value distribution (log scale) grouped by phenotype
- Feature importance plots from LightGBM (gain and split counts)
- ROC/PR curves for both models
- K-mer frequency heatmaps per organism

---

## 6. Machine Learning Models — Detailed

---

### 6.1 LightGBM Resistance Forecaster

**File:** [backend/ml_models/lgbm_predictor.py](backend/ml_models/lgbm_predictor.py)  
**Class:** `LGBMResistancePredictor`  
**Algorithm:** LightGBM (gradient boosted decision trees) — `lgb.Booster`  
**Input:** Structured/tabular features from AMR metadata records  
**Output:** `{prediction, probability, confidence, antibiotic, drug_class, threshold, model_used}`  
**Trained model file:** `backend/trained_models/amr_lgbm_final_model.txt`  
**Status:** Active — trained and loaded on startup

#### What LightGBM Is

LightGBM (Light Gradient Boosting Machine) is a tree-based gradient boosting framework developed by Microsoft (Ke et al., NeurIPS 2017). It builds an ensemble of decision trees sequentially, where each new tree corrects the errors of the previous ensemble. Key properties:

- **Leaf-wise tree growth** (vs level-wise) — finds the leaf with the maximum loss reduction, resulting in deeper, more accurate trees
- **Histogram-based splitting** — bins continuous features into histograms for fast split finding
- **Native categorical support** — handles string categories without one-hot encoding overhead
- **`is_unbalance=True`** — automatically weights classes inversely proportional to their frequency (critical here since Susceptible >> Resistant in the data)
- **Early stopping** — training halts when the validation AUC stops improving for 30 rounds

#### Why LightGBM Over Other Models

- Faster than XGBoost on large tabular datasets (histogram binning)
- Built-in categorical feature handling (no need to pre-encode antibiotic names, drug classes, etc.)
- Native class imbalance handling (`is_unbalance=True`)
- AUC as training metric directly — optimized for discrimination, not accuracy
- Model saved as **human-readable text format** (`.txt`) — cross-language, version-safe, can be inspected by a text editor

#### Feature Set — 14 Features (`FINAL_FEATURES`)

```python
FINAL_FEATURES = [
    'Taxon ID',                     # NCBI taxonomy ID (integer, treated as categorical)
    'Antibiotic',                   # Antibiotic name (categorical string)
    'drug_class',                   # Drug class: beta_lactam, carbapenem, fluoroquinolone, etc. (categorical)
    'genus',                        # Bacterial genus extracted from Genome Name (categorical)
    'species',                      # Bacterial species extracted from Genome Name (categorical)
    'mic_sign',                     # MIC operator: <=, >=, <, >, =, exact, unknown (categorical)
    'is_lab_confirmed',             # 1 = lab method, 0 = computational (binary)
    'computational_f1',             # F1 score of computational method, 0–1 (float)
    'mic_value',                    # Numeric MIC in µg/mL (float, NaN if not available)
    'mic_log',                      # log1p(mic_value) — log-scaled (float)
    'has_mic',                      # 1 if mic_value was parseable, 0 otherwise (binary)
    'ab_resistance_rate',           # Mean resistance rate across all records for this antibiotic (float)
    'taxon_ab_resistance_rate',     # Mean resistance rate for this (taxon, antibiotic) pair (float)
    'genus_ab_resistance_rate',     # Mean resistance rate for this (genus, antibiotic) pair (float)
]

CAT_FEATURES = ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign']
# These 5 are passed to LightGBM as categorical — avoids one-hot encoding
```

#### Drug Class Map (`DRUG_CLASS_MAP`)

The full mapping from antibiotic name → drug class used by LightGBM as a categorical feature:

```python
DRUG_CLASS_MAP = {
    # Beta-lactams (penicillins and cephalosporins)
    'ampicillin': 'beta_lactam',       'amoxicillin': 'beta_lactam',
    'amoxicillin/clavulanic acid': 'beta_lactam',
    'piperacillin': 'beta_lactam',     'piperacillin/tazobactam': 'beta_lactam',
    'oxacillin': 'beta_lactam',        'cefazolin': 'beta_lactam',
    'cefoxitin': 'beta_lactam',        'cefotaxime': 'beta_lactam',
    'ceftazidime': 'beta_lactam',      'ceftriaxone': 'beta_lactam',
    'cefepime': 'beta_lactam',         'cefuroxime': 'beta_lactam',
    'cephalothin': 'beta_lactam',
    # Carbapenems (last-resort beta-lactams)
    'imipenem': 'carbapenem',          'meropenem': 'carbapenem',
    'ertapenem': 'carbapenem',         'doripenem': 'carbapenem',
    # Monobactam
    'aztreonam': 'monobactam',
    # Fluoroquinolones
    'ciprofloxacin': 'fluoroquinolone', 'levofloxacin': 'fluoroquinolone',
    'norfloxacin': 'fluoroquinolone',   'nalidixic acid': 'fluoroquinolone',
    'ofloxacin': 'fluoroquinolone',
    # Aminoglycosides
    'gentamicin': 'aminoglycoside',    'tobramycin': 'aminoglycoside',
    'amikacin': 'aminoglycoside',      'streptomycin': 'aminoglycoside',
    'neomycin': 'aminoglycoside',      'kanamycin': 'aminoglycoside',
    # Tetracyclines
    'tetracycline': 'tetracycline',    'doxycycline': 'tetracycline',
    'minocycline': 'tetracycline',     'tigecycline': 'tetracycline',
    # Sulfonamides
    'sulfamethoxazole': 'sulfonamide', 'trimethoprim': 'sulfonamide',
    'trimethoprim/sulfamethoxazole': 'sulfonamide',
    # Other classes
    'chloramphenicol': 'phenicol',     'azithromycin': 'macrolide',
    'erythromycin': 'macrolide',       'colistin': 'polymyxin',
    'polymyxin b': 'polymyxin',        'vancomycin': 'glycopeptide',
    'teicoplanin': 'glycopeptide',     'clindamycin': 'lincosamide',
    'nitrofurantoin': 'nitrofuran',    'rifampicin': 'rifamycin',
    'rifampin': 'rifamycin',
}
```

#### Model Hyperparameters

```python
params = {
    'objective':        'binary',      # Binary cross-entropy loss
    'metric':           'auc',         # Optimize AUC on validation set
    'boosting_type':    'gbdt',        # Gradient Boosted Decision Trees
    'num_leaves':       63,            # Max leaves per tree (2^6 − 1)
    'learning_rate':    0.05,          # Step size for each boosting round
    'n_estimators':     500,           # Max number of trees (may stop earlier)
    'subsample':        0.8,           # 80% of rows sampled per tree
    'colsample_bytree': 0.8,           # 80% of features sampled per tree
    'reg_alpha':        0.1,           # L1 regularization
    'reg_lambda':       1.0,           # L2 regularization
    'is_unbalance':     True,          # Inverse class frequency weighting
    'cat_smooth':       10,            # Smoothing for categorical splits
    'max_cat_threshold':32,            # Max categories per split
    'random_state':     42,
    'n_jobs':           -1,            # Use all CPU cores
    'verbose':          -1,            # Suppress training output
}

callbacks = [
    lgb.early_stopping(30, verbose=False),   # Stop if val AUC doesn't improve in 30 rounds
    lgb.log_evaluation(100),                 # Print progress every 100 rounds
]
```

#### MIC Sign Numeric Encoding (used during training)

```python
MIC_SIGN_MAP = {
    '<=': -1.0, '<': -0.5, '=': 0.0, '==': 0.0,
    'exact': 0.0, '>=': 1.0, '>': 0.5, 'unknown': 0.0
}
```
This is used in the training pipeline for internal label encoding; the predictor stores the raw string and passes it as a LightGBM categorical feature.

#### Trained Artifacts (all in `backend/trained_models/`)

| File | Format | Content | Size |
|------|--------|---------|------|
| `amr_lgbm_final_model.txt` | LightGBM text | Full trained booster (all trees) | ~5 MB |
| `ab_rate_full.joblib` | pandas Series | `{antibiotic: mean_resistance_rate}` | <1 MB |
| `taxon_ab_rate_full.joblib` | pandas DataFrame | `[(Taxon ID, Antibiotic, rate)]` — only groups with ≥3 records | ~2 MB |
| `genus_ab_rate_full.joblib` | pandas DataFrame | `[(genus, Antibiotic, rate)]` — only groups with ≥3 records | <1 MB |
| `lgbm_meta.joblib` | dict | `{'global_mean': 0.1662}` | <1 KB |

The `.txt` format is LightGBM's native cross-language serialization: it stores all tree structures, split thresholds, leaf values, and categorical encodings as plain text. It can be read by the LightGBM library in Python, R, or C++.

#### Prediction Inference Logic (step by step)

```python
def predict(self, antibiotic, taxon_id, mic_value, mic_sign, genus, species, threshold=0.40):

    # Step 1: Normalize inputs
    antibiotic = antibiotic.lower().strip()
    drug_class = DRUG_CLASS_MAP.get(antibiotic, 'other')

    # Step 2: Check if trained model is available
    if not self.is_trained:
        prob = self._heuristic_predict(antibiotic, taxon_id, mic_value, mic_sign, genus)
    else:
        # Step 3: Parse MIC value
        mic_val = float(mic_value) if mic_value else np.nan
        mic_log = np.log1p(max(mic_val, 0)) if not np.isnan(mic_val) else np.nan
        has_mic = 0 if np.isnan(mic_val) else 1

        # Step 4: Look up target-encoded resistance rates
        ab_rate         = self.ab_rate.get(antibiotic, self.global_mean)
        taxon_ab_rate   = self.taxon_rate.get((int(taxon_id), antibiotic), ab_rate)
        genus_ab_rate   = self.genus_rate.get((genus.lower(), antibiotic), ab_rate)

        # Step 5: Build single-row DataFrame with all 14 features
        row = {
            'Taxon ID': int(taxon_id) if taxon_id else 0,
            'Antibiotic': antibiotic, 'drug_class': drug_class,
            'genus': genus, 'species': species,
            'mic_sign': mic_sign or 'unknown',
            'is_lab_confirmed': 0, 'computational_f1': 0.85,
            'mic_value': mic_val, 'mic_log': mic_log, 'has_mic': has_mic,
            'ab_resistance_rate': ab_rate,
            'taxon_ab_resistance_rate': taxon_ab_rate,
            'genus_ab_resistance_rate': genus_ab_rate,
        }
        df = pd.DataFrame([row])
        for col in self.CAT_FEATURES:
            df[col] = df[col].astype('category')

        # Step 6: Run LightGBM inference
        prob = float(self.model.predict(df[self.FINAL_FEATURES])[0])

    # Step 7: Apply threshold
    label = 'Resistant' if prob >= threshold else 'Susceptible'
    confidence = prob if prob >= threshold else 1 - prob

    return {
        'prediction': label,
        'probability': round(prob, 4),
        'confidence': round(confidence * 100, 1),
        'antibiotic': antibiotic,
        'drug_class': drug_class,
        'threshold': threshold,
        'model_used': 'LightGBM (trained)' if self.is_trained else 'Heuristic (untrained)',
    }
```

#### Heuristic Fallback Logic (used when model file is absent)

When `amr_lgbm_final_model.txt` is not found, predictions fall back to a rule-based system:

```python
# Known resistance rates per antibiotic (derived from training data statistics)
RESISTANCE_RATES = {
    'ampicillin': 0.65, 'amoxicillin': 0.58, 'ciprofloxacin': 0.42,
    'imipenem': 0.18,   'vancomycin': 0.10,  'colistin': 0.05,
    'tetracycline': 0.58, 'gentamicin': 0.28, ...
}

def _heuristic_predict(self, antibiotic, taxon_id, mic_value, mic_sign, genus):
    base_rate = RESISTANCE_RATES.get(antibiotic, 0.35)

    # MIC-based adjustment
    if mic >= 32:   base_rate = min(base_rate + 0.30, 0.95)  # Very high MIC → likely resistant
    elif mic >= 8:  base_rate = min(base_rate + 0.15, 0.90)
    elif mic <= 0.25: base_rate = max(base_rate - 0.25, 0.05) # Very low MIC → likely susceptible
    elif mic <= 1:  base_rate = max(base_rate - 0.10, 0.05)

    # MIC sign adjustment
    if mic_sign in ('>=', '>'):  base_rate = min(base_rate + 0.10, 0.95)
    elif mic_sign in ('<=', '<'): base_rate = max(base_rate - 0.10, 0.05)

    # Small random noise for realism
    noise = np.random.uniform(-0.05, 0.05)
    return float(np.clip(base_rate + noise, 0.02, 0.98))
```

#### Decision Threshold Rationale

Default threshold: **0.40** (not the standard 0.50)

A lower threshold means the model is more likely to predict Resistant. This is intentional:
- **False negative** (predict Susceptible when actually Resistant) → patient receives wrong antibiotic → clinical failure → potentially fatal
- **False positive** (predict Resistant when actually Susceptible) → doctor orders a different antibiotic → unnecessary escalation → manageable
- Setting threshold = 0.40 increases Resistant recall (0.91 at threshold 0.40 vs ~0.78 at 0.50) at the cost of lower Resistant precision (0.46)

#### Comparison Chart Generation

The `ResistanceForecastView` calls `predict()` for 8 antibiotics in the same taxon/genus context after the primary prediction:

```python
common_antibiotics = [
    'ampicillin', 'ciprofloxacin', 'tetracycline',
    'gentamicin', 'imipenem', 'trimethoprim/sulfamethoxazole',
    'chloramphenicol', 'cefotaxime'
]
comparison = []
for ab in common_antibiotics:
    r = model.predict(antibiotic=ab, taxon_id=taxon_id, mic_value=None, genus=genus, species=species)
    comparison.append({'antibiotic': ab, 'resistance_probability': r['probability'] * 100})
result['comparison_chart'] = comparison
```

This allows the frontend to render a multi-antibiotic bar chart for the same organism.

---

### 6.2 K-mer Resistance Predictor

**File:** [backend/ml_models/resistance_predictor.py](backend/ml_models/resistance_predictor.py)  
**Class:** `KmerResistancePredictor`  
**Algorithm:** scikit-learn `RandomForestClassifier` on genomic k-mer features  
**Input:** Raw FASTA sequence text (whole genome or assembled contigs)  
**Output:** `{prediction, probability, confidence, antibiotic, sequence_length, gc_content, top_kmers, model_used, threshold}`  
**Trained model file:** `backend/trained_models/kmer_resistance_model.pkl`  
**Status:** Active — trained and loaded on startup

#### What K-mer Analysis Is

A **k-mer** is a subsequence of length k extracted from a DNA sequence. For k=4 (4-mers), there are 4^4 = 256 possible sequences (AAAA, AAAC, ..., TTTT). The frequency distribution of k-mers in a genome is a genomic fingerprint — organisms under antibiotic pressure accumulate specific mutations and resistance genes that alter their k-mer composition. By training a classifier on these frequency vectors, we can predict resistance phenotype directly from raw sequence without requiring gene annotation or alignment.

**Why k=4 (4-mers)?**
- 4-mer: 256 features — compact, fast to compute, sufficient discriminatory power
- 3-mer: 64 features — too sparse, loses specificity
- 5-mer: 1,024 features — more features but more memory-intensive; marginal gain

#### Why RandomForest Over Deep Learning

- RandomForest handles the 321-dimensional feature space well without overfitting
- Interpretable: feature importance shows which k-mers matter
- No GPU required — trains on CPU in minutes
- `class_weight='balanced'` handles the Resistant/Susceptible imbalance natively
- CNNs or LSTMs would require sequence alignment or embedding, which is slower and more memory-intensive for whole-genome data

#### Feature Engineering — 3 Components

**Component 1: 4-mer Frequency Vector (256 dimensions)**

```python
ALL_KMERS = [''.join(p) for p in product(['A','T','C','G'], repeat=4)]
# = ['AAAA', 'AAAC', 'AAAG', 'AAAT', 'AACA', ..., 'TTTT']  — 256 total

def kmer_freq_vector(sequence):
    # Count all overlapping 4-mers in a sliding window
    counter = Counter(sequence[i:i+4] for i in range(len(sequence) - 3))
    counts = np.array([counter.get(km, 0) for km in ALL_KMERS], dtype=np.float32)
    total = counts.sum()
    return counts / total   # normalize: relative frequencies sum to 1.0
```

**Component 2: Antibiotic One-Hot Vector (N_AB dimensions = 62)**

```python
N_AB = len(ab_list)    # 62 antibiotics in training set
ab_vec = np.zeros(N_AB, dtype=np.float32)
ab_vec[ab_list.index(antibiotic)] = 1.0
# Single 1.0 at the position of the target antibiotic, 0.0 everywhere else
```

This allows the same model to be used for all antibiotics. The model learns different k-mer patterns that correlate with resistance to each antibiotic.

**Component 3: Auxiliary Genomic Features (3 dimensions)**

| Feature | Formula | Biological rationale |
|---------|---------|---------------------|
| `gc_content` | `(G+C) / total_bases` | GC% is species-specific; deviation may indicate HGT events |
| `at_content` | `(A+T) / total_bases` = `1 - gc_content` | Complement of GC — included for completeness |
| `length_norm` | `len(sequence) / 500000` | Larger genomes have more resistance gene capacity |

**Total feature vector:** 256 + 62 + 3 = **321 dimensions**

#### StandardScaler Application

A `StandardScaler` is fitted on the **first 256 columns** (the k-mer frequencies) of the training set only:

```python
scaler = StandardScaler()
X_train[:, :256] = scaler.fit_transform(X_train[:, :256])
X_test[:, :256]  = scaler.transform(X_test[:, :256])
# The one-hot and auxiliary features are NOT scaled
# (they are already bounded: 0–1 range, well-conditioned)
```

The fitted scaler is saved inside `kmer_resistance_model.pkl` and applied identically at inference time.

#### Model Hyperparameters

```python
RandomForestClassifier(
    n_estimators   = 100,         # 100 decision trees in the ensemble
    max_depth      = 15,          # Max depth per tree (prevents overfitting)
    class_weight   = 'balanced',  # Weight = n_samples / (n_classes * n_samples_per_class)
    random_state   = 42,
    n_jobs         = -1,          # Use all CPU cores
)
```

#### Saved Artifact (`kmer_resistance_model.pkl`)

The `.pkl` file is a Python `pickle` of a single dictionary with 4 keys:

```python
{
    'model':     RandomForestClassifier,     # Trained classifier (100 trees)
    'scaler':    StandardScaler,             # Fitted on 256 k-mer columns of training X
    'ab_list':   list[str],                  # 62 antibiotic names (order matches one-hot columns)
    'ALL_KMERS': list[str],                  # 256 k-mer strings (order matches frequency columns)
}
```

#### Inference Pipeline (step by step)

```python
def predict(self, fasta_text, antibiotic, threshold=0.5):

    # Step 1: Parse FASTA text into clean sequence
    sequence = read_fasta_sequence(fasta_text)
    # → strips '>' header lines, concatenates contigs, removes non-ATCG, caps at 500,000 bp

    # Step 2: Validate minimum length
    if len(sequence) < 100:
        return {'error': 'FASTA sequence too short (minimum 100 bp)'}

    if not self.is_trained:
        prob = self._heuristic_predict(sequence, antibiotic)
    else:
        # Step 3: Extract 321-dimensional feature vector
        feat = extract_features(sequence, antibiotic, self.ab_list)
        # = [kmer_freq_256 | antibiotic_onehot_62 | gc, at, len_norm]

        # Step 4: Scale the k-mer portion
        feat = self.scaler.transform(feat.reshape(1, -1))[0]

        # Step 5: RandomForest inference
        prob = float(self.model.predict_proba(feat.reshape(1, -1))[0][1])
        # predict_proba returns [P(Susceptible), P(Resistant)] — take index [1]

    # Step 6: Apply threshold
    label = 'Resistant' if prob >= threshold else 'Susceptible'
    confidence = prob if prob >= threshold else 1 - prob

    # Step 7: Compute top 10 k-mers by frequency (for display)
    kmer_vec = kmer_freq_vector(sequence)
    top_idx = np.argsort(kmer_vec)[-10:][::-1]
    top_kmers = [{'kmer': ALL_KMERS[i], 'frequency': round(float(kmer_vec[i]), 5)}
                 for i in top_idx]

    return {
        'prediction': label, 'probability': round(prob, 4),
        'confidence': round(confidence * 100, 1),
        'antibiotic': antibiotic,
        'sequence_length': len(sequence),
        'gc_content': round(gc * 100, 2),   # in percentage
        'top_kmers': top_kmers,
        'model_used': 'RandomForest K-mer (trained)' if self.is_trained else 'Heuristic (untrained)',
        'threshold': threshold,
    }
```

#### Heuristic Fallback Logic (K-mer predictor)

Used when `kmer_resistance_model.pkl` is absent:

```python
def _heuristic_predict(self, sequence, antibiotic):
    gc = compute_gc_content(sequence)
    profile = ANTIBIOTIC_RESISTANCE_PROFILES.get(antibiotic, {'gc_weight': 1.0, 'base': 0.35})
    base = profile['base']       # Known resistance rate for this antibiotic
    gc_weight = profile['gc_weight']

    # GC deviation adjustment: genomes with unusual GC% tend to have more mobile elements
    gc_deviation = abs(gc - 0.50)
    adjustment = gc_deviation * gc_weight * 0.3

    # K-mer entropy adjustment: high entropy = more diverse k-mer composition
    if kmer_vec is not None:
        entropy = -np.sum(kmer_vec * np.log1p(kmer_vec))
        entropy_norm = entropy / np.log(256 + 1)
        adjustment += (entropy_norm - 0.5) * 0.15

    noise = np.random.uniform(-0.04, 0.04)
    return float(np.clip(base + adjustment + noise, 0.03, 0.97))
```

---

### 6.3 Mutation Timeline — Biological Simulation (NOT ML)

**File:** [backend/ml_models/mutation_timeline.py](backend/ml_models/mutation_timeline.py)  
**Class:** `MutationTimelinePredictor`  
**Type:** Mathematical biological simulation — **NOT a trained ML model**  
**Input:** FASTA sequence (optional, adjusts GC modifier) + antibiotic name + number of weeks  
**Output:** Week-by-week resistance evolution dict with timeline, hotspots, gene activations  
**Trained model file:** None — no `.pkl` or `.txt` file is required or used  

> **Important for academic reviewers:** This component does NOT use machine learning. It implements a logistic growth equation with biologically calibrated parameters. It produces scientifically plausible resistance evolution curves, but these outputs are **simulated, not predicted from learned data**. There is no training phase, no AUC score, and no held-out test set. It is a visualization/educational tool, not a predictive model.

#### Mathematical Foundation — Logistic Growth Equation

Resistance spread through a bacterial population follows a logistic (sigmoid) growth curve because:
1. Initially, resistant mutants are rare and grow freely (exponential phase)
2. As resistant fraction grows, competition for resources slows further growth
3. Resistance plateaus near a maximum determined by the antibiotic type and mechanism

```
R(t) = R₀ + (R_peak − R₀) / (1 + e^(−k × (t − t_midpoint)))

Where:
  R(t)         = resistant fraction at week t (0.0 to 1.0)
  R₀           = initial resistant fraction at week 0
  R_peak       = maximum achievable resistant fraction (antibiotic-specific)
  k            = speed × 2.5  (growth rate constant)
  t_midpoint   = n_weeks × 0.45  (inflection point — where growth is fastest)
  t            = current week (0, 1, 2, ..., n_weeks)
```

**GC content modifier on initial resistance:**
```python
initial_resistant = abs(gc_content - 0.50) * 0.3
initial_resistant = max(0.02, min(initial_resistant, 0.15))
```
Rationale: Organisms with GC% far from the average (0.50) are more likely to have acquired mobile genetic elements (transposons, integrons) which carry resistance genes. This gives a GC-based starting point.

**Additional timeline quantities computed per week:**
- `cumulative_mutations` — Poisson-distributed new mutations each week: `Poisson(speed × 15)`
- `mic_fold_change` — MIC increase relative to week 0: `1.0 + resistant_fraction × 32 × (peak / 0.9)`
- `intermediate_fraction` — partial resistance zone: `min(0.25, resistant × (1 − resistant) × 2)`
- `susceptible_fraction` — `1.0 − resistant − intermediate`
- `treatment_effective` — boolean: True when `resistant_fraction < 0.50`

#### Antibiotic Profiles — 13 + 1 Default (`ANTIBIOTIC_MUTATION_PROFILES`)

Parameters calibrated against published EUCAST clinical breakpoints and WHO GLASS resistance surveillance data:

| Antibiotic | Speed (k/2.5) | Peak R | Known Resistance Genes | Drug Class |
|------------|--------------|--------|------------------------|-----------|
| `ciprofloxacin` | 0.18 | 92% | gyrA, gyrB, parC, parE | fluoroquinolone |
| `ampicillin` | 0.22 | 95% | blaTEM, blaSHV, blaOXA | beta_lactam |
| `tetracycline` | 0.20 | 90% | tetA, tetB, tetC | tetracycline |
| `chloramphenicol` | 0.15 | 88% | catA, catB, cml | phenicol |
| `gentamicin` | 0.12 | 75% | aac(3), aph(3) | aminoglycoside |
| `cefotaxime` | 0.16 | 85% | blaCTX-M, blaSHV | cephalosporin |
| `imipenem` | 0.08 | 65% | blaKPC, blaNDM, blaOXA-48 | carbapenem |
| `trimethoprim/sulfamethoxazole` | 0.19 | 88% | dhfr, sul1, sul2 | sulfonamide |
| `vancomycin` | 0.06 | 55% | vanA, vanB, vanC | glycopeptide |
| `colistin` | 0.05 | 50% | mcr-1, mcr-2, lpxA | polymyxin |
| `streptomycin` | 0.17 | 82% | aadA, strA, strB | aminoglycoside |
| `erythromycin` | 0.14 | 78% | ermA, ermB, mefA | macrolide |
| `rifampicin` | 0.13 | 80% | rpoB | rifamycin |
| `default` | 0.15 | 80% | resistance_gene_1, efflux_pump | unknown |

**Biological rationale for speed differences:**
- Vancomycin (0.06) and colistin (0.05) are very slow because resistance requires multiple complex mutations in cell wall or lipid A synthesis — high fitness cost
- Ampicillin (0.22) and ciprofloxacin (0.18) are fast because resistance genes (blaTEM, gyrA) are carried on highly transferable plasmids — resistance spreads via horizontal gene transfer without a fitness cost

#### Mutation Hotspot Detection Algorithm

```python
def find_mutation_hotspots(sequence, n_sites=15):
    window = 10       # 10 bp sliding window
    step = max(1, len(sequence) // (n_sites * 3))   # adaptive step

    hotspots = []
    for start in range(0, len(sequence) - window, step):
        window_seq = sequence[start:start + window]

        # GC fraction of this window
        gc = sum(1 for c in window_seq if c in 'GC') / window

        # Repeat density: how many unique bases? Low uniqueness = high repeats
        repeat_score = 1 - len(set(window_seq)) / window

        # Composite hotspot score
        score = gc * 0.4 + repeat_score * 0.6

        hotspots.append((start, score, window_seq))

    # Sort by score descending, take top n_sites
    top = sorted(hotspots, key=lambda x: x[1], reverse=True)[:n_sites]

    # Format results sorted by genomic position
    result = [{
        'position': pos + 5,               # Center of the window
        'original_nucleotide': win[5],     # Middle base of window
        'mutated_nucleotide': TRANSITIONS[win[5]][0],  # Most likely transition
        'mutation_type': random.choice(MUTATION_TYPES[:4]),  # SNP/Insertion/Deletion/Amplification
        'hotspot_score': round(score, 4),
        'window_context': win,
    } for pos, score, win in top]

    return sorted(result, key=lambda x: x['position'])
```

**Mutation types modeled:**
```python
MUTATION_TYPES = [
    'Point mutation (SNP)',         # Single nucleotide substitution
    'Insertion',                    # Insertional disruption
    'Deletion',                     # Loss of sequence
    'Gene amplification',           # Copy number increase
    'Plasmid acquisition',          # Horizontal gene transfer
    'Efflux pump upregulation',     # Transcriptional regulation
    'Porin loss',                   # Outer membrane impermeability
    'Target modification',          # Drug target mutation
]

# Nucleotide transition probabilities (most likely substitutions)
NUCLEOTIDE_TRANSITIONS = {
    'A': ['G', 'T', 'C'],   # A→G (transition), A→T/C (transversion)
    'G': ['A', 'C', 'T'],
    'T': ['C', 'A', 'G'],
    'C': ['T', 'G', 'A'],
}
```

#### Gene Activation Timeline

Gene activations are evenly spaced across the simulation window:
```python
for i, gene in enumerate(resistance_genes):
    activation_week = max(1, int((i + 1) * n_weeks / (len(genes) + 1)))
    activation_week = min(activation_week, n_weeks)
    resistance_contribution = timeline[activation_week]['resistant_fraction'] / len(genes)
```

Example for ciprofloxacin (4 genes, 8 weeks): gyrA activates at week 2, gyrB at week 3, parC at week 5, parE at week 6.

#### Treatment Failure Threshold

Treatment marked as **failed** when `resistant_fraction >= 50.0%` of the population.  
Pharmacodynamic rationale: when >50% of the bacterial population is resistant, the antibiotic can no longer achieve population-level clearance even at high doses.

---

## 7. Training Pipeline — Step by Step

**File:** [backend/train_models.py](backend/train_models.py)  
**Run:** `python train_models.py --model lgbm|kmer|all`  
**Location:** Must be run from `backend/` directory

### LightGBM Training (`train_lgbm()`)

```
Step 1: Load data
  → load_amr_data(data_dir, max_files=500)
  → Globs all *.csv in amr_output/
  → Loads up to 500 CSVs with pd.read_csv(low_memory=False)
  → Concatenates into single DataFrame
  → Prints progress every 100 files

Step 2: Clean data
  → clean_amr_data(df_raw)
  → Parse MIC sign and value
  → Extract genus/species
  → Map phenotypes: Intermediate → Resistant
  → Create binary target
  → Normalize antibiotic names
  → Compute is_lab_confirmed, computational_f1
  → Deduplicate by (Genome ID, Antibiotic)

Step 3: Compute target encodings
  → ab_rate = groupby('Antibiotic')['target'].mean()
  → taxon_ab = groupby(['Taxon ID', 'Antibiotic'])['target'].mean()
       (only groups with count >= 3)
  → genus_ab = groupby(['genus', 'Antibiotic'])['target'].mean()
       (only groups with count >= 3)
  → Merge back onto df; fill missing with ab_rate

Step 4: Train/test split
  → 80% train+val | 20% test (stratified by target)
  → 85% train | 15% val (from train+val, stratified)

Step 5: Create LightGBM datasets
  → lgb.Dataset(X_tr, label=y_tr, categorical_feature=CAT_FEATURES)
  → lgb.Dataset(X_val, label=y_val, reference=lgb_train)

Step 6: Train
  → lgb.train(params, lgb_train, valid_sets=[lgb_val], callbacks=[...])
  → Early stopping: patience = 30 rounds
  → Metric: AUC-ROC on validation set

Step 7: Evaluate on test set
  → model.predict(X_test) → probabilities
  → threshold 0.40 applied for label assignment
  → Print AUC-ROC and classification_report

Step 8: Save artifacts
  → model.save_model('amr_lgbm_final_model.txt')   ← LightGBM text format
  → joblib.dump(ab_rate, 'ab_rate_full.joblib')
  → joblib.dump(taxon_ab, 'taxon_ab_rate_full.joblib')
  → joblib.dump(genus_ab, 'genus_ab_rate_full.joblib')
  → joblib.dump({'global_mean': ...}, 'lgbm_meta.joblib')
```

### K-mer RF Training (`train_kmer()`)

```
Step 1: Load mapped CSVs
  → Globs mapped_output/*.csv (up to 200 files)
  → Concatenates into single DataFrame
  → Drops rows with missing Antibiotic, Resistant Phenotype, or fasta_path
  → Maps phenotype: Intermediate → Resistant (label 1)

Step 2: Build antibiotic list
  → sorted(df['Antibiotic'].unique()) → 62 antibiotics
  → Creates ab_to_idx mapping for one-hot encoding

Step 3: Process each row → feature vector
  → For each genome-antibiotic pair:
    a. Read FASTA from fasta_path (with path resolution fallback)
    b. Compute 4-mer frequency vector (256 dims)
    c. Compute antibiotic one-hot (62 dims)
    d. Compute GC%, AT%, length_norm (3 dims)
    e. Concatenate → 321-dim feature vector
  → Skip rows where FASTA file is missing or sequence too short
  → Cache: each fasta_path is read only once (seen_fasta dict)

Step 4: Assemble matrices
  → X = np.array(X_list)   shape: (6002, 321)
  → y = np.array(y_list)   shape: (6002,)

Step 5: Train/test split
  → 80% train | 20% test (stratified)

Step 6: Scale k-mer features
  → StandardScaler().fit_transform(X_train[:, :256])
  → Apply same scaler to X_test[:, :256]

Step 7: Train RandomForest
  → RandomForestClassifier(n_estimators=100, max_depth=15,
                            class_weight='balanced', random_state=42)
  → clf.fit(X_train, y_train)

Step 8: Evaluate
  → classification_report(y_test, clf.predict(X_test))
  → roc_auc_score(y_test, clf.predict_proba(X_test)[:, 1])

Step 9: Save artifact
  → pickle.dump({'model': clf, 'scaler': scaler,
                  'ab_list': ab_list, 'ALL_KMERS': ALL_KMERS},
                 open('kmer_resistance_model.pkl', 'wb'))
```

### Data Split Summary

```
LightGBM:
  All cleaned data (24,983 records)
    → 20% test set   (4,997 records)  ← held out entirely
    → 80% train+val  (19,986 records)
         → 15% val   (2,998 records)  ← used for early stopping
         → 85% train (16,988 records) ← gradient descent

K-mer RF:
  All paired samples (6,002 genome-antibiotic pairs)
    → 20% test set  (1,201 pairs) ← held out entirely
    → 80% train     (4,801 pairs)
```

### Class Imbalance Handling

| Model | Imbalance | Method | Why not SMOTE |
|-------|-----------|--------|--------------|
| LightGBM | Susceptible >> Resistant | `is_unbalance=True` in params | SMOTE on 14-feature tabular data works, but LightGBM's built-in weighting is faster and equally effective |
| K-mer RF | Susceptible >> Resistant | `class_weight='balanced'` | SMOTE on 321-dimensional feature vectors is very memory-intensive; balanced weights achieve similar results |

---

## 8. Model Registry & Startup Sequence

**File:** [backend/api/model_registry.py](backend/api/model_registry.py)  
**File:** [backend/api/apps.py](backend/api/apps.py)

### Singleton Pattern

The registry holds three module-level variables that persist for the lifetime of the Django process:

```python
_lgbm:     LGBMResistancePredictor  | None = None
_kmer:     KmerResistancePredictor  | None = None
_timeline: MutationTimelinePredictor| None = None
```

`init_models()` is called exactly **once** — a guard `if _lgbm is not None: return` prevents double initialization.

### Startup Sequence (line by line)

```
1. Developer runs: python manage.py runserver 8000
2. Django loads all INSTALLED_APPS
3. Loads ApiConfig (api/apps.py)
4. ApiConfig.ready() is called by Django after all apps are loaded
5. ready() calls model_registry.init_models()
6. init_models() reads settings.TRAINED_MODELS_DIR
7. Instantiates LGBMResistancePredictor(model_dir)
   → __init__ sets is_trained=False, calls _load()
   → _load() checks for amr_lgbm_final_model.txt
   → If found: lgb.Booster(model_file=...) + load 4 joblib files
   → Sets is_trained=True, prints "[LightGBM] Model loaded from disk."
8. Instantiates KmerResistancePredictor(model_dir)
   → _load() checks for kmer_resistance_model.pkl
   → If found: pickle.load → extracts model, scaler, ab_list, ALL_KMERS
   → Sets is_trained=True, prints "[K-mer] Model loaded. Antibiotics: 62"
9. Instantiates MutationTimelinePredictor(model_dir)
   → _load() checks for mutation_timeline_model.pkl (never exists)
   → Prints "[Timeline] No trained model. Using biological simulation."
   → is_trained stays False — simulation still works fully
10. Prints "[Registry] All models initialized."
11. Django starts accepting requests on port 8000
```

### Accessor Functions

```python
def get_lgbm()     → LGBMResistancePredictor    # Returns singleton or None
def get_kmer()     → KmerResistancePredictor     # Returns singleton or None
def get_timeline() → MutationTimelinePredictor   # Returns singleton or None
```

Every `views.py` endpoint checks the result: `if model is None: return json_error('Model not initialized', 503)`.

---

## 9. Backend API — Full Reference

**Framework:** Django 4.x + Django REST Framework  
**Base URL:** `http://localhost:8000/api/`  
**Auth:** None (fully open — no authentication required)  
**CSRF:** Disabled via `@csrf_exempt` on all views  
**Content-Type:** All endpoints accept both `application/json` and `multipart/form-data`

### URL Routing

```python
# backend/backend/urls.py
urlpatterns = [path('api/', include('api.urls'))]

# backend/api/urls.py
urlpatterns = [
    path('health/',      HealthView.as_view()),       # GET
    path('forecast/',    ResistanceForecastView.as_view()),   # POST
    path('predict/',     ResistancePredictionView.as_view()), # POST
    path('timeline/',    MutationTimelineView.as_view()),      # POST
    path('antibiotics/', AntibioticListView.as_view()),        # GET
    path('train/',       TrainModelView.as_view()),            # POST
    path('reload/',      ReloadModelsView.as_view()),          # POST
]
```

---

### Endpoint 1 — Health Check

**URL:** `GET /api/health/`  
**Class:** `HealthView(View)`  
**Purpose:** Check which models are loaded and active

**Request:** No body required

**Response:**
```json
{
  "status": "running",
  "models": {
    "lgbm_forecasting": {
      "trained": true,
      "model_type": "LightGBM Gradient Boosting",
      "description": "Forecasts antibiotic resistance from genome metadata and MIC values",
      "features": ["Taxon ID", "Antibiotic", "drug_class", "genus", "species", ...]
    },
    "kmer_resistance": {
      "trained": true,
      "model_type": "RandomForest on 4-mer Frequency Spectra",
      "antibiotics_known": 62,
      "feature_dim": 256,
      "description": "Predicts resistance from bacterial genome FASTA using k-mer composition analysis"
    },
    "mutation_timeline": {
      "trained": false,
      "model_type": "Biological Simulation",
      "description": "Simulates week-by-week resistance evolution under antibiotic pressure"
    }
  }
}
```

---

### Endpoint 2 — LightGBM Resistance Forecast

**URL:** `POST /api/forecast/`  
**Class:** `ResistanceForecastView(View)`  
**Model used:** `LGBMResistancePredictor`  
**Content-Type:** `application/json` or `multipart/form-data`

**Request parameters:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `antibiotic` | String | Yes | — | Antibiotic name (e.g. "ciprofloxacin") |
| `taxon_id` | String/Int | No | None | NCBI Taxon ID (e.g. "1280" for *S. aureus*) |
| `mic_value` | Float | No | None | MIC value in µg/mL |
| `mic_sign` | String | No | None | MIC operator: `<=`, `>=`, `<`, `>`, `=` |
| `genus` | String | No | `"unknown"` | Bacterial genus |
| `species` | String | No | `"unknown"` | Bacterial species |
| `threshold` | Float | No | 0.40 | Decision threshold |

**Request example:**
```json
{
  "antibiotic": "ciprofloxacin",
  "taxon_id": "1280",
  "mic_value": 4.0,
  "mic_sign": ">=",
  "genus": "staphylococcus",
  "species": "aureus",
  "threshold": 0.40
}
```

**Response:**
```json
{
  "prediction":        "Resistant",
  "probability":       0.847,
  "confidence":        84.7,
  "antibiotic":        "ciprofloxacin",
  "drug_class":        "fluoroquinolone",
  "threshold":         0.40,
  "model_used":        "LightGBM (trained)",
  "related_antibiotics": ["levofloxacin", "norfloxacin", "nalidixic acid", "ofloxacin"],
  "comparison_chart": [
    {"antibiotic": "ampicillin",                  "resistance_probability": 92.1},
    {"antibiotic": "ciprofloxacin",               "resistance_probability": 84.7},
    {"antibiotic": "tetracycline",                "resistance_probability": 78.3},
    {"antibiotic": "gentamicin",                  "resistance_probability": 41.2},
    {"antibiotic": "imipenem",                    "resistance_probability": 18.5},
    {"antibiotic": "trimethoprim/sulfamethoxazole","resistance_probability": 67.9},
    {"antibiotic": "chloramphenicol",             "resistance_probability": 55.4},
    {"antibiotic": "cefotaxime",                  "resistance_probability": 71.8}
  ]
}
```

---

### Endpoint 3 — K-mer FASTA Resistance Prediction

**URL:** `POST /api/predict/`  
**Class:** `ResistancePredictionView(View)`  
**Model used:** `KmerResistancePredictor`  
**Content-Type:** `multipart/form-data` (file upload) or `application/json`

**Request parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fasta_file` | File | One of these two | Upload a `.fasta` / `.fa` file |
| `fasta_text` | String | One of these two | Paste raw FASTA text |
| `antibiotic` | String | Yes | Target antibiotic name |
| `threshold` | Float | No (default 0.5) | Decision threshold |

**Response:**
```json
{
  "prediction":      "Resistant",
  "probability":     0.781,
  "confidence":      78.1,
  "antibiotic":      "ampicillin",
  "sequence_length": 234791,
  "gc_content":      32.7,
  "top_kmers": [
    {"kmer": "ATCG", "frequency": 0.00823},
    {"kmer": "GCTA", "frequency": 0.00791},
    {"kmer": "TAAT", "frequency": 0.00754},
    ...
  ],
  "model_used": "RandomForest K-mer (trained)",
  "threshold":  0.5
}
```

**Error responses:**
```json
{"error": "FASTA sequence too short (minimum 100 bp)", "sequence_length": 47}
{"error": "FASTA sequence or file is required"}
{"error": "antibiotic is required"}
```

---

### Endpoint 4 — Mutation Timeline Simulation

**URL:** `POST /api/timeline/`  
**Class:** `MutationTimelineView(View)`  
**Component used:** `MutationTimelinePredictor` (biological simulation — not ML)

**Request parameters:**

| Field | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `fasta_file` or `fasta_text` | File/String | — | — | Genome (optional — adjusts initial resistance via GC%) |
| `antibiotic` | String | Required | 13 supported | Antibiotic to simulate |
| `n_weeks` | Integer | 8 | 1–52 | Number of weeks to simulate |

**Supported antibiotics for timeline:** ciprofloxacin, ampicillin, tetracycline, chloramphenicol, gentamicin, cefotaxime, imipenem, trimethoprim/sulfamethoxazole, vancomycin, colistin, streptomycin, erythromycin, rifampicin

**Response:**
```json
{
  "antibiotic":            "vancomycin",
  "antibiotic_class":      "glycopeptide",
  "sequence_length":       185402,
  "gc_content":            32.7,
  "n_weeks":               12,
  "timeline": [
    {
      "week": 0,
      "resistant_fraction":    2.1,
      "susceptible_fraction":  96.4,
      "intermediate_fraction": 1.5,
      "cumulative_mutations":  0,
      "mic_fold_change":       1.68,
      "treatment_effective":   true
    },
    {
      "week": 4,
      "resistant_fraction":    14.3,
      "susceptible_fraction":  78.2,
      "intermediate_fraction": 7.5,
      "cumulative_mutations":  12,
      "mic_fold_change":       6.12,
      "treatment_effective":   true
    }
  ],
  "mutation_hotspots": [
    {
      "position":            1240,
      "original_nucleotide": "G",
      "mutated_nucleotide":  "A",
      "mutation_type":       "Point mutation (SNP)",
      "hotspot_score":       0.7812,
      "window_context":      "ATCGGCAACG"
    }
  ],
  "resistance_genes": [
    {"gene": "vanA", "activation_week": 3, "resistance_contribution": 4.7},
    {"gene": "vanB", "activation_week": 6, "resistance_contribution": 8.2},
    {"gene": "vanC", "activation_week": 9, "resistance_contribution": 11.4}
  ],
  "failure_week":            null,
  "final_resistant_percent": 38.2,
  "peak_resistance":         55.0,
  "model_used":              "Biological Simulation",
  "summary":                 "vancomycin remains partially effective. Final resistance: 38.2%. Monitor vanA, vanB gene expression."
}
```

---

### Endpoint 5 — Antibiotic List

**URL:** `GET /api/antibiotics/`  
**Class:** `AntibioticListView(View)`

Returns the hardcoded sorted list of 48 antibiotics supported by the frontend:

```json
{
  "antibiotics": [
    "amikacin", "amoxicillin", "amoxicillin/clavulanic acid",
    "ampicillin", "azithromycin", "aztreonam",
    "cefazolin", "cefepime", "cefotaxime", "cefoxitin",
    "cephalothin", "ceftazidime", "ceftriaxone", "cefuroxime",
    "chloramphenicol", "ciprofloxacin", "clindamycin",
    "colistin", "doripenem", "doxycycline", "ertapenem",
    "erythromycin", "gentamicin", "imipenem", "kanamycin",
    "levofloxacin", "meropenem", "minocycline",
    "nalidixic acid", "neomycin", "nitrofurantoin",
    "norfloxacin", "ofloxacin", "oxacillin",
    "piperacillin", "piperacillin/tazobactam",
    "polymyxin b", "rifampin", "rifampicin",
    "streptomycin", "sulfamethoxazole", "teicoplanin",
    "tetracycline", "tigecycline", "tobramycin",
    "trimethoprim", "trimethoprim/sulfamethoxazole",
    "vancomycin"
  ]
}
```

> Note: The K-mer model was trained on 62 antibiotics (from mapped_output data). The list above (48) is the frontend display list. The LightGBM covers all antibiotics present in the BVBRC training data.

---

### Endpoint 6 — Train Model (Background Thread)

**URL:** `POST /api/train/`  
**Class:** `TrainModelView(View)`

**Request:**
```json
{"model": "lgbm"}   // or "kmer" or "all"
```

**Mechanism:**
```python
thread = threading.Thread(
    target=train_in_background,
    args=(model_name, TRAINED_MODELS_DIR, DATA_DIR),
    daemon=True,   # Thread will be killed if main process exits
)
thread.start()
```

Training runs as a background daemon thread. The response is returned immediately. The training process prints progress to the Django console. After training completes, the thread automatically calls `_load()` on the relevant predictor instance to hot-reload the new model without restarting the server.

**Response:**
```json
{
  "status": "Training started",
  "model":  "lgbm",
  "message": "Training lgbm model in background. Check /api/health/ for status."
}
```

---

### Endpoint 7 — Reload Models

**URL:** `POST /api/reload/`  
**Class:** `ReloadModelsView(View)`

Calls `_load()` on each model singleton to pick up newly saved artifacts from disk without restarting Django. Useful after manual training runs.

**Response:**
```json
{
  "status": "reloaded",
  "models": {
    "lgbm":     {"trained": true},
    "kmer":     {"trained": true},
    "timeline": {"trained": false}
  }
}
```

---

## 10. Frontend Application — Full Reference

**Framework:** Flask 3.x  
**File:** [frontend/app.py](frontend/app.py)  
**Template Engine:** Jinja2  
**UI Framework:** Bootstrap 5.3.2 (CDN) + Bootstrap Icons 1.11.3 (CDN)  
**Charts:** Plotly.js 2.26.0 (CDN)

### Flask Route Table (11 routes)

| Route | Methods | Template | Purpose |
|-------|---------|----------|---------|
| `/` | GET | `index.html` | Landing page — fetches `/api/health/` for live model status |
| `/forecast` | GET, POST | `resistance_forecast.html` | LightGBM tabular prediction form |
| `/predict` | GET, POST | `resistance_prediction.html` | K-mer FASTA file upload + prediction |
| `/timeline` | GET, POST | `mutation_timeline.html` | Bio-simulation with Plotly chart |
| `/train` | GET, POST | `train.html` | Training control panel |
| `/datasets` | GET | `datasets.html` | Dataset catalog |
| `/about` | GET | `about.html` | Project information + references |
| `/api/health` | GET | — | Proxy → Django `/api/health/` |
| `/reload` | POST | — | Proxy → Django `/api/reload/` |
| *(internal)* `/forecast` POST | POST | — | Proxy via `backend_post('forecast/')` |
| *(internal)* `/timeline` POST | POST | — | Proxy via `backend_post('timeline/')` |

### Flask Proxy Helpers

```python
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://127.0.0.1:8000/api')

def backend_get(endpoint, timeout=10):
    # Simple GET with error handling for ConnectionError (backend not running)
    r = requests.get(f'{BACKEND_URL}/{endpoint}', timeout=timeout)
    return r.json(), r.status_code

def backend_post(endpoint, data=None, files=None, json_data=None, timeout=30):
    # POST with support for:
    #   - multipart/form-data (files=...) — for file uploads
    #   - application/json (json_data=...) — for text payloads
    #   - form-encoded (data=...) — for simple form posts
    url = f'{BACKEND_URL}/{endpoint}'
    if files:
        r = requests.post(url, data=data, files=files, timeout=timeout)
    elif json_data is not None:
        r = requests.post(url, json=json_data, timeout=timeout)
    else:
        r = requests.post(url, data=data, timeout=timeout)
    return r.json(), r.status_code
```

### Hardcoded Lists (in `frontend/app.py`)

**48 supported antibiotics** — passed to all form templates as `antibiotics` context variable.

**15 bacteria species** — passed to the forecast form as `bacteria_list`:

```python
BACTERIA_LIST = [
    'Escherichia coli',           'Klebsiella pneumoniae',
    'Pseudomonas aeruginosa',     'Acinetobacter baumannii',
    'Staphylococcus aureus',      'Enterococcus faecium',
    'Salmonella enterica',        'Streptococcus pneumoniae',
    'Mycobacterium tuberculosis', 'Campylobacter jejuni',
    'Campylobacter coli',         'Helicobacter pylori',
    'Shigella flexneri',          'Enterobacter cloacae',
    'Proteus mirabilis',
]
```

### Navigation Structure (`base.html`)

```
[Dashboard]  [ML Models ▼]                [Bio-Simulator]  [Datasets]  [About]  [Train]
                 ├── AMR Forecasting   ← LightGBM badge — /forecast
                 └── Resistance Pred   ← K-mer RF badge — /predict
```

- **"ML Models"** dropdown: contains only the two trained, AUC-scored ML models
- **"Bio-Simulator"** standalone nav link: the logistic simulation tool (clearly separate)
- This separation was implemented to make clear to academic reviewers which tools use trained models

### Template Pages — Detailed

#### `base.html` — Shared Layout

All 8 template pages extend `base.html` using Jinja2 `{% extends 'base.html' %}`.

Key structural elements:
- `<nav class="navbar">` with Bootstrap 5 collapse (hamburger menu on mobile)
- Navbar `backdrop-filter: blur(12px)` for glass-morphism effect
- Brand: `AMR**Predict**` with `bi-virus2` Bootstrap Icon
- `<main class="main-content">` — `flex: 1` for sticky footer
- Full 4-column footer:
  - Column 1: Brand description — "2 trained ML models + 1 biological simulation tool"
  - Column 2: Nav links grouped into "ML Models" and "Tools" sub-headings
  - Column 3: Technology stack list
  - Column 4: Stats mini-cards (AUC 0.93 · 90K+ Records · 62 Antibiotics · 2 ML Models)
  - Bottom bar: Copyright · BVBRC link · About · Train Models

#### `index.html` — Landing Page

**Hero section (left panel):**
- H1 headline, 3 call-to-action buttons (Try LightGBM, K-mer Predict, Bio-Simulator)
- Status badges row: LightGBM AUC 0.93 | K-mer RF AUC 0.93 | Timeline Bio-Sim

**Hero panel (right panel — macOS-style floating panel):**
- Header: "AMR Analysis Engine · v2.0"
- Two model status rows (LightGBM green, K-mer RF green, Timeline orange "Simulation")
- Stats grid: 90K+ Records, 62 Antibiotics, 17 Species, AUC 0.93
- Mini resistance bar chart (static visualization)

**Global AMR Statistics Strip** (sourced statistics):

| Stat | Value | Source |
|------|-------|--------|
| Direct AMR deaths (2019) | 1.27M | [Murray et al., The Lancet 2022](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext) |
| Associated AMR deaths (2019) | 4.95M | [Murray et al., The Lancet 2022](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext) |
| Projected deaths by 2050 | 10M/yr | [O'Neill Review, 2016](https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf) |
| Cumulative GDP loss by 2050 | $100T | [O'Neill Review, 2016](https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf) |
| Training records | 90K+ | [BVBRC / PATRIC](https://www.bv-brc.org/) |

**Crisis Cards** (4 cards, all sourced):

| Stat | Source |
|------|--------|
| 1.27M direct AMR deaths | [Murray et al., The Lancet 2022](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext) |
| ~80% E. coli fluoroquinolone resistance in high-burden countries | [WHO GLASS Report 2022](https://www.who.int/publications/i/item/9789240062702) |
| 2.8M+ resistant infections per year in the US, 35K deaths | [CDC AR Threats Report 2019](https://www.cdc.gov/antimicrobial-resistance/data-research/threats/index.html) |
| AUC 0.93 — our own model result | BVBRC held-out test data |

**ML Models Section:**
- Section eyebrow: "Machine Learning Models"
- Section title: "Trained ML Prediction Models"
- 2-column card layout: LightGBM (col-lg-6) | K-mer RF (col-lg-6)
- Each card shows: trained badge, AUC score, feature count, performance stats

**Biological Simulation Section (separate, below ML section):**
- Amber left-border panel with `"This is not an ML model"` warning banner
- Logistic growth equation displayed
- Side comparison checklist: what simulation does NOT have vs what it does have

**"How the System Works" steps:**
- Step 05 has amber `"Not ML"` badge to flag the simulation step

#### `resistance_forecast.html` — LightGBM Prediction

- Dropdown: 48 antibiotics, 15 bacteria (auto-fills genus/species)
- Fields: Taxon ID (numeric), MIC Value, MIC Sign selector, Threshold slider (0.1–0.9)
- Results section (shown after POST):
  - Large prediction badge (green Susceptible / red Resistant)
  - Probability percentage bar
  - Drug class badge + related antibiotics list
  - Multi-antibiotic comparison bar chart (Plotly)

#### `resistance_prediction.html` — K-mer FASTA Prediction

- Tab switcher: "Upload FASTA file" / "Paste sequence text"
- Drag-and-drop file upload zone with Browse button
- Antibiotic dropdown (48 antibiotics)
- Threshold slider
- Results: prediction badge, probability bar, GC%, sequence length, top 10 k-mers table

#### `mutation_timeline.html` — Biological Simulation

- Antibiotic dropdown (13 supported)
- Weeks slider (2–24)
- Optional FASTA upload (for GC-based initial resistance modifier)
- Results:
  - Plotly line chart: Resistant / Susceptible / Intermediate fractions over weeks
  - Mutation hotspots table (position, nucleotide, mutation type, score)
  - Resistance gene activation timeline bars
  - Weekly data table (expandable)
  - Scientific background section explaining the math
- Source citations for resistance development table: WHO GLASS, EUCAST, Lancet 2022

#### `datasets.html` — Dataset Catalog

- Stats strip: 5 datasets · 90,826+ records · 2,587 NCBI files · 1,684 taxon folders
- Source badges: BVBRC + NCBI GenBank
- Per-dataset cards with schema tables and data source hyperlinks
- BVBRC columns table, FASTA structure description, mapped_output join description

#### `about.html` — Project Information

- Project overview (WHO AMR threat linked to WHO spotlight page)
- Objectives, methodology, system architecture
- ML Models technical table (LightGBM + K-mer RF only — with AUC scores)
- Biological simulation table (clearly no AUC)
- REST API reference table
- Known limitations section
- 7 fully hyperlinked key references (see Section 15)
- Data source tags: BVBRC, NCBI GenBank, EUCAST, WHO GLASS — all clickable

#### `train.html` — Training Control Panel

- Model selector: lgbm / kmer / all
- Launch training button (POST to `/api/train/`)
- Status polling against `/api/health/`
- Console-style scrollable output area

### CSS Design System (`style.css`)

**Design token system (CSS custom properties):**

```css
:root {
  /* Backgrounds */
  --bg-base:      #f0f4f8;    /* Page background */
  --bg-surface:   #f8fafc;    /* Subtle surface lift */
  --bg-card:      #ffffff;    /* Card background */
  --bg-elevated:  #eef2f7;    /* Elevated panels */
  --bg-input:     #ffffff;    /* Form inputs */

  /* Borders */
  --border:       rgba(15,23,42,0.08);
  --border-md:    rgba(15,23,42,0.14);

  /* Brand & Status Colors */
  --primary:       #4f46e5;   /* Indigo brand */
  --primary-light: #6366f1;
  --success:       #16a34a;   /* Green (trained, susceptible) */
  --danger:        #dc2626;   /* Red (resistant) */
  --warning:       #d97706;   /* Amber (simulation, warning) */

  /* Typography */
  --text-1:   #0f172a;    /* Near-black heading */
  --text-2:   #475569;    /* Secondary body text */
  --text-3:   #94a3b8;    /* Muted labels, placeholders */

  /* Shadows */
  --shadow:    0 1px 3px rgba(15,23,42,0.08);
  --shadow-lg: 0 8px 30px rgba(15,23,42,0.10);
}
```

**Key custom CSS classes:**

| Class | Purpose |
|-------|---------|
| `.btn-model-green` | Green outline button (K-mer page) |
| `.btn-model-red` | Red outline button (forecast page) |
| `.btn-primary-custom` | Solid indigo button |
| `.btn-success-custom` | Solid green submit button |
| `.btn-danger-custom` | Solid red submit button |
| `.src-link` | Dotted-underline inline citation link (10px, muted color) |
| `.footer-link` | Footer anchor styling |
| `.hero-panel` | macOS-style floating panel (hero section) |
| `.hpanel-row` | Model status row inside hero panel |
| `.hpanel-badge` | AUC badge inside hero panel (green=trained, orange=simulated) |
| `.page-header-icon` | Colored icon circle on page headers |
| `.main-content` | `flex: 1` content wrapper for sticky footer |
| `.status-badge.trained` | Green "Trained" badge |
| `.status-badge.simulated` | Orange "Simulation" badge |
| `.status-badge.offline` | Red "Offline" badge |

**Source citation link style (`.src-link`):**
```css
.src-link {
  font-size: 10px;
  color: var(--text-3);
  text-decoration: none;
  font-weight: 400;
  border-bottom: 1px dotted var(--text-3);
  transition: color 0.15s, border-color 0.15s;
}
.src-link:hover {
  color: var(--primary-light);
  border-bottom-color: var(--primary-light);
}
```

---

## 11. Data Flow Diagrams

### LightGBM Prediction Flow

```
User fills form at /forecast
  ├── antibiotic: "ciprofloxacin"
  ├── taxon_id:   "1280"
  ├── mic_value:  "4"
  └── mic_sign:   ">="

Flask /forecast POST handler
  → Collects form fields into payload dict
  → backend_post('forecast/', json_data=payload)
    → requests.post('http://127.0.0.1:8000/api/forecast/', json=payload)

Django ResistanceForecastView.post()
  → Parse JSON body
  → Validate: antibiotic required
  → model = model_registry.get_lgbm()    ← singleton, already loaded
  → result = model.predict(
        antibiotic="ciprofloxacin",
        taxon_id="1280", mic_value="4", mic_sign=">=",
        genus="staphylococcus", species="aureus",
        threshold=0.40
     )
    → Normalize: antibiotic.lower().strip()
    → drug_class = DRUG_CLASS_MAP["ciprofloxacin"] = "fluoroquinolone"
    → is_trained = True (model file loaded at startup)
    → mic_val = 4.0, mic_log = log1p(4) = 1.609, has_mic = 1
    → ab_rate = self.ab_rate["ciprofloxacin"]           # from ab_rate_full.joblib
    → taxon_ab_rate = self.taxon_rate[(1280,"ciprofloxacin")]  # from taxon_ab_rate_full.joblib
    → genus_ab_rate = self.genus_rate[("staphylococcus","ciprofloxacin")]
    → df = DataFrame([14-feature row])
    → cast CAT_FEATURES to 'category'
    → prob = lgb.Booster.predict(df)[0]    ← actual LightGBM tree traversal
    → label = "Resistant" (prob=0.847 >= threshold=0.40)
    → return {'prediction': 'Resistant', 'probability': 0.847, ...}
  → get_drug_class_summary("ciprofloxacin")
    → related = ["levofloxacin", "norfloxacin", "nalidixic acid", "ofloxacin"]
  → Build comparison_chart (8 × model.predict() calls)
  → JsonResponse(result)  → HTTP 200

Flask receives response → returns to browser template

Browser renders:
  ├── Large "RESISTANT" badge (red)
  ├── Probability bar: 84.7%
  ├── Drug class: fluoroquinolone
  └── Comparison chart: 8-antibiotic Plotly bar chart
```

### K-mer FASTA Prediction Flow

```
User uploads file at /predict
  ├── fasta_file: genome.fasta (multipart)
  └── antibiotic: "ampicillin"

Flask /predict POST handler
  → fasta_file = request.files['fasta_file']
  → files = {'fasta_file': (filename, stream, 'text/plain')}
  → backend_post('predict/', data=post_data, files=files)
    → requests.post(url, data=..., files=...)  ← multipart/form-data

Django ResistancePredictionView.post()
  → fasta_text = request.FILES['fasta_file'].read().decode('utf-8')
  → model = model_registry.get_kmer()
  → result = model.predict(fasta_text, "ampicillin", threshold=0.5)
    → read_fasta_sequence(fasta_text)
      → strip headers, concatenate, strip non-ATCG, cap at 500K bp
      → returns clean_seq (234,791 bp)
    → len(clean_seq) >= 100 ✓
    → extract_features(clean_seq, "ampicillin", self.ab_list)
      → kmer_freq_vector: Counter of 4-mers / total → shape (256,)
      → ab_vec: one-hot at ab_list.index("ampicillin") → shape (62,)
      → gc=0.327, at=0.673, len_norm=0.470 → shape (3,)
      → concat → shape (321,)
    → self.scaler.transform(feat[:256]) → normalized k-mer portion
    → self.model.predict_proba(feat.reshape(1,-1))[0][1] → prob=0.781
    → label = "Resistant"
    → top_kmers = argsort(kmer_vec)[-10:][::-1]
    → return {prediction, probability, confidence, top_kmers, gc_content, ...}
  → JsonResponse(result)

Browser renders:
  ├── "RESISTANT" badge (red)
  ├── 78.1% probability bar
  ├── GC content: 32.7%
  ├── Sequence length: 234,791 bp
  └── Top 10 k-mers table
```

### Mutation Timeline Simulation Flow

```
User submits at /timeline
  ├── fasta_text: ">header\nATCG..."
  ├── antibiotic: "vancomycin"
  └── n_weeks: "12"

Django MutationTimelineView.post()
  → model = model_registry.get_timeline()
  → result = model.predict(fasta_text, "vancomycin", n_weeks=12)
    → sequence = read_fasta_sequence(fasta_text)  [cap at 200,000 bp]
    → gc = compute_gc_content(sequence) = 0.327
    → profile = ANTIBIOTIC_MUTATION_PROFILES["vancomycin"]
      → {speed: 0.06, peak: 0.55, genes: ['vanA','vanB','vanC'], type: 'glycopeptide'}
    → timeline = generate_timeline(profile, 12, 0.327, len(sequence))
      → initial_resistant = abs(0.327-0.50)*0.3 = 0.0519 → clipped to [0.02, 0.15]
      → for week 0..12:
          k = 0.06 * 2.5 = 0.15
          midpoint = 12 * 0.45 = 5.4
          R(t) = 0.0519 + (0.55-0.0519)/(1 + exp(-0.15*(t-5.4)))
          + compute intermediate, susceptible, mutations, MIC fold
    → hotspots = find_mutation_hotspots(sequence, n_sites=12)
    → failure_week = first week where resistant_fraction >= 50% → None (vancomycin slow)
    → gene_activation: vanA@week3, vanB@week6, vanC@week9
    → return full result dict with model_used="Biological Simulation"

Browser renders:
  ├── Plotly multi-line chart (Resistant/Susceptible/Intermediate vs weeks)
  ├── Mutation hotspots table
  ├── Gene activation bars
  └── Summary: "vancomycin remains partially effective..."
```

---

## 12. Performance Metrics

### LightGBM Resistance Forecaster — Actual Training Results

Trained: 2026-05-06 | Dataset: 500 CSV files from `amr_output/` | Records: 24,983 cleaned

| Metric | Value |
|--------|-------|
| **AUC-ROC (test set)** | **0.9255** |
| Decision threshold | 0.40 |
| Total cleaned records | 24,983 |
| Train set (85% of 80%) | 16,988 |
| Validation set (15% of 80%) | 2,998 |
| Test set (20%) | 4,997 |
| Susceptible precision | 0.98 |
| Susceptible recall | 0.78 |
| Resistant precision | 0.46 |
| Resistant recall | 0.91 |
| Overall accuracy | 0.80 |
| Features used | 14 |
| Antibiotics covered | 62+ |
| Early stopping patience | 30 rounds |
| Best iteration | ~200 trees |
| Global resistance rate | 16.62% |

**Interpretation of results:**
- AUC 0.9255 means: if you randomly pick one Resistant and one Susceptible sample, the model ranks the Resistant one higher 92.55% of the time
- Resistant recall of 0.91 means: 91% of truly resistant isolates are correctly identified as Resistant
- Resistant precision of 0.46 means: 46% of isolates predicted as Resistant are truly Resistant (54% are false alarms — acceptable for clinical safety screening)

### K-mer Resistance Predictor — Actual Training Results

Trained: 2026-05-06 | Dataset: 1,684 mapped CSV files + FASTA genomes | Pairs: 6,002

| Metric | Value |
|--------|-------|
| **AUC-ROC (test set)** | **0.9290** |
| Decision threshold | 0.50 |
| Total genome-antibiotic pairs | 6,002 |
| Train set (80%) | 4,801 |
| Test set (20%) | 1,201 |
| Susceptible precision | 0.97 |
| Susceptible recall | 0.91 |
| Resistant precision | 0.47 |
| Resistant recall | 0.73 |
| Overall accuracy | 0.90 |
| Feature dimensions | 321 (256 k-mer + 62 AB + 3 extra) |
| Trees | 100 |
| Max depth | 15 |
| Antibiotics | 62 |

### Mutation Timeline Predictor

| Property | Value |
|----------|-------|
| Type | Mathematical simulation — no supervised training |
| AUC-ROC | N/A — simulated outputs, not learned predictions |
| Antibiotics modeled | 13 (with calibrated profiles) + 1 default |
| Equation | Logistic growth (sigmoid) |
| GC modifier | `abs(gc - 0.50) × 0.3`, clipped to [0.02, 0.15] |
| Hotspot algorithm | GC density + repeat density in 10-bp windows (0.4/0.6 weight) |
| Treatment failure threshold | 50% resistant population |
| Mutation accumulation model | Poisson(`speed × 15`) per week |

---

## 13. Technology Stack

### Backend Dependencies (`backend/requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| Django | ≥4.2 | Web framework, settings, AppConfig, middleware |
| djangorestframework | ≥3.14 | REST API view classes, JSON renderer/parser, multipart parser |
| django-cors-headers | ≥4.0 | CORS support (allows Flask on port 5000 to call Django on port 8000) |
| lightgbm | ≥4.0 | Gradient boosted trees — LightGBM `Booster` class |
| scikit-learn | ≥1.3 | `RandomForestClassifier`, `StandardScaler`, `train_test_split`, metrics |
| pandas | ≥2.0 | DataFrame I/O, cleaning, groupby, merge operations |
| numpy | ≥1.24 | Array operations, k-mer frequency vectors, log transforms |
| joblib | ≥1.3 | Serialization of pandas Series/DataFrames (encoding tables) |
| (pickle) | stdlib | Python built-in — K-mer model dict serialization |

### Frontend Dependencies (`frontend/requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | ≥3.0 | WSGI server, routing, Jinja2 template rendering |
| requests | ≥2.31 | HTTP client for proxying calls from Flask to Django |

### CDN Dependencies (loaded in `base.html`)

| Library | Version | CDN | Purpose |
|---------|---------|-----|---------|
| Bootstrap CSS | 5.3.2 | jsDelivr | Responsive grid, components, utilities |
| Bootstrap JS | 5.3.2 | jsDelivr | Navbar collapse, dropdowns, tabs |
| Bootstrap Icons | 1.11.3 | jsDelivr | 2,000+ SVG icon library |
| Plotly.js | 2.26.0 | Plotly CDN | Interactive charts (timeline line chart, comparison bar chart) |

### External Data Sources Used in Training

| Source | URL | Used for |
|--------|-----|---------|
| BVBRC / PATRIC | https://www.bv-brc.org/ | AMR phenotype CSV records (LightGBM training) |
| NCBI GenBank | https://www.ncbi.nlm.nih.gov/genbank/ | WGS FASTA sequences (K-mer RF training) |
| EUCAST | https://www.eucast.org/ | Antibiotic breakpoints (simulation profile calibration) |
| WHO GLASS | https://www.who.int/initiatives/glass | Resistance surveillance data (simulation calibration) |

---

## 14. How to Run

### Prerequisites

- Python 3.10+
- pip
- The full dataset directories: `amr_output/`, `fasta_output/`, `mapped_output/` (for training)
- Already-trained model files in `backend/trained_models/` (if skipping training)

### Step 1 — Install Dependencies

```bash
cd backend
pip install -r requirements.txt

cd ../frontend
pip install -r requirements.txt
```

### Step 2 — Django Database Setup (one time only)

```bash
cd backend
python manage.py migrate
```

This creates the `db.sqlite3` file Django needs. No AMR data goes into the database — it's only for Django's internal tables.

### Step 3 — Start Django Backend (Terminal 1)

```bash
cd backend
python manage.py runserver 8000
```

Expected console output on startup:
```
[LightGBM] Model loaded from disk.
[K-mer] Model loaded. Antibiotics: 62
[Timeline] No trained model. Using biological simulation.
[Registry] All models initialized.
Watching for file changes with StatReloader
Django version 4.x, using settings 'backend.settings'
Starting development server at http://127.0.0.1:8000/
```

### Step 4 — Start Flask Frontend (Terminal 2)

```bash
cd frontend
python app.py
```

Expected output:
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

Open browser at: **http://localhost:5000**

### Step 5 — Retrain Models (if needed)

```bash
cd backend

# Train LightGBM only (~10–20 minutes on 500 CSVs)
python train_models.py --model lgbm

# Train K-mer RF only (~20–40 minutes on 1,684 FASTA folders)
python train_models.py --model kmer

# Train both sequentially
python train_models.py --model all
```

**Training output example (LightGBM):**
```
[Data] Found 3655 AMR CSV files. Loading up to 500...
  Loaded 100 files...
  Loaded 200 files...
[Data] Combined shape: (281432, 28)
[Clean] Cleaned shape: (24983, 21)
[Clean] Target: Susceptible=20,770 | Resistant=4,213
[LightGBM] Training...
[LightGBM] Test AUC-ROC: 0.9255
              precision  recall  f1-score  support
  Susceptible    0.98    0.78    0.87    4151
   Resistant     0.46    0.91    0.61     846
[LightGBM] Model saved to .../amr_lgbm_final_model.txt
```

After retraining, hot-reload without restarting Django:
```bash
curl -X POST http://localhost:8000/api/reload/
```

Or via the Train page in the browser at `/train`.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://127.0.0.1:8000/api` | Override to point Flask at a different Django host |

---

## 15. Scientific Sources & Citations

All statistics displayed on the website are sourced from peer-reviewed publications or official health organization reports. Links are embedded directly in the frontend HTML next to each statistic.

| # | Citation | URL |
|---|----------|-----|
| 1 | Murray CJ et al. (2022). "Global burden of bacterial antimicrobial resistance in 2019: a systematic analysis." *The Lancet*, 399(10325), 629–655. | https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(21)02724-0/fulltext |
| 2 | O'Neill J (2016). "Tackling Drug-Resistant Infections Globally: Final Report and Recommendations." *Review on Antimicrobial Resistance*. | https://amr-review.org/sites/default/files/160518_Final%20paper_with%20cover.pdf |
| 3 | CDC (2019). "Antibiotic Resistance Threats in the United States, 2019." Centers for Disease Control and Prevention. | https://www.cdc.gov/antimicrobial-resistance/data-research/threats/index.html |
| 4 | WHO (2022). "Global Antimicrobial Resistance and Use Surveillance System (GLASS) Report 2022." WHO, Geneva. | https://www.who.int/publications/i/item/9789240062702 |
| 5 | WHO (2019). "Ten threats to global health in 2019." World Health Organization. | https://www.who.int/news-room/spotlight/ten-threats-to-global-health-in-2019 |
| 6 | Olson RD et al. (2023). "Introducing the Bacterial and Viral Bioinformatics Resource Center (BV-BRC)." *Nucleic Acids Research*, 51(D1), D678–D689. | https://academic.oup.com/nar/article/51/D1/D678/6840395 |
| 7 | Ke G et al. (2017). "LightGBM: A Highly Efficient Gradient Boosting Decision Tree." *NeurIPS 2017*. | https://proceedings.neurips.cc/paper_files/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html |
| 8 | Drouin A et al. (2016). "Predictive computational phenotyping and biomarker discovery using reference-free genome comparisons." *BMC Genomics*, 17, 754. | https://bmcgenomics.biomedcentral.com/articles/10.1186/s12864-016-2777-6 |
| 9 | EUCAST (2023). Clinical Breakpoints and Dosing of Antibiotics. European Committee on Antimicrobial Susceptibility Testing. | https://www.eucast.org/clinical_breakpoints/ |
| 10 | CLSI (2023). "Performance Standards for Antimicrobial Susceptibility Testing." M100, 33rd Edition. | https://clsi.org/standards/products/microbiology/documents/m100/ |

---

## 16. Known Limitations

### Data

1. **Training subset (LightGBM):** Only 500 of 3,655 available CSV files were used (24,983 records). Full dataset training (~90,826 records) would produce a stronger model but requires more RAM and time.

2. **Geographic bias:** BVBRC and NCBI data skews toward North American and European isolates. Resistance patterns may differ significantly for isolates from South Asia, Africa, or Latin America.

3. **MIC parsing edge cases:** Some BVBRC records have non-standard formats (qualitative descriptors in the Measurement field). These default to `np.nan` and are treated as `has_mic=0`.

4. **Antibiotic coverage:** Only antibiotics present ≥3 times per taxon/genus group get target-encoded rates. Rare antibiotics fall back to global or per-antibiotic mean.

5. **K-mer model FASTA coverage:** Only 6,002 genome-antibiotic pairs were available in `mapped_output/` with accessible FASTA files. A larger paired dataset would improve the K-mer model.

### Models

6. **LightGBM temporal bias:** Trained on historical data. Newly emerged resistance mechanisms (e.g., novel carbapenemases, mcr-3 variants) will be underweighted until retrained on newer data.

7. **K-mer locality:** 4-mer frequencies miss long-range genomic structure. Plasmid-borne resistance genes on very small contigs (< 500 bp) may not contribute sufficient signal.

8. **K-mer trained threshold is 0.50:** Unlike LightGBM which uses 0.40, the K-mer model uses the standard 0.50 threshold. Clinical use would warrant a lower threshold for the same reasons as LightGBM.

9. **Mutation timeline is simulation:** The timeline component produces mathematically plausible but simulated curves. It does not model: local antibiotic usage pressure, horizontal gene transfer from external sources, clonal expansion dynamics, or co-resistance selection. Parameters are calibrated from published data but are not organism-specific or patient-specific.

10. **LightGBM precision/recall tradeoff:** At threshold 0.40, Resistant recall is 91% but Resistant precision is only 46%. This means 54% of Resistant predictions are false alarms. This is appropriate for screening (safety > specificity) but must be disclosed for clinical applications.

### System

11. **No authentication:** All API endpoints are fully open (no JWT, no OAuth). A production deployment would require proper authentication and authorization middleware, plus audit logging for HIPAA/GDPR compliance.

12. **Synchronous training with no progress stream:** `/api/train/` spawns a background thread but provides no real-time streaming of progress. Training runs may appear to hang from the browser's perspective.

13. **No file size validation on FASTA upload:** Very large FASTA files (>500 MB) can exhaust RAM during sequence reading. The 500,000 bp cap mitigates this but is not a hard request-size limit.

14. **Single-process Flask:** `app.run(debug=True)` is a single-threaded development server. Concurrent users would need gunicorn + multiple workers.

15. **Django SECRET_KEY is hardcoded:** The `SECRET_KEY` in `settings.py` is a static string appropriate for development but must be replaced with an environment variable for production deployment.

---

## 17. Changelog

| Date | Change |
|------|--------|
| 2026-05-06 | **Models trained** — LightGBM (AUC 0.9255) and K-mer RF (AUC 0.9290) trained and saved to `trained_models/`. Both models now active; heuristic fallback no longer used during normal operation. |
| 2026-05-06 | **Root cause identified** — Heuristics were being used because `amr_lgbm_final_model.txt` and `kmer_resistance_model.pkl` were absent. `is_trained=False` routing in both predictor classes caused all calls to fall through to `_heuristic_predict()`. Fixed by running `train_models.py`. |
| 2026-05-06 | **Mutation Timeline separated on frontend** — removed from "ML Models" navbar dropdown; given its own "Bio-Simulator" standalone nav link. Dashboard now shows 2 separate sections: "Trained ML Prediction Models" and "Biological Simulation". Amber warning banner added. |
| 2026-05-06 | **Source citations added throughout frontend** — all external statistics now have clickable hyperlinks to primary sources. Corrected outdated 700K figure to 1.27M (Lancet 2022). Replaced unsourced "~60%" claim with CDC AR Threats 2019 figure. Added `.src-link` CSS class. |
| 2026-05-06 | **`about.html` references updated** — 7 fully hyperlinked citations added; data source tags made clickable (BVBRC, NCBI GenBank, EUCAST, WHO GLASS). |
| 2026-05-06 | **Stats corrected** — "3 ML Models" → "2 ML Models" across footer, about page, and hero panel. |
| 2026-05-06 | **`PROJECT_DOCUMENTATION.md` major expansion** — added data flow diagrams, full inference logic (step-by-step), heuristic fallback details, complete drug class map, MIC sign encoding table, K-mer feature engineering breakdown, FASTA path resolution logic, Django settings documentation, Flask route table, comparison chart generation, known limitations expanded to 15 items. |

---

*Project: AMR Intelligence Platform v2.0*  
*Author: Hamza Afzal*  
*Last updated: 2026-05-06*
