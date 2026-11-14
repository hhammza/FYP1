# Architecture

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

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
│   ├── amr_constants.py         Antibiotic names, aliases, drug classes, label maps: the one copy
│   ├── train_models.py          Production trainer: raw CSV/FASTA → artifacts
│   ├── trained_models/          6 committed artifacts (~7 MB) + model_report.json
│   ├── Procfile / railway.toml  Gunicorn deploy config
│   └── tests/                   unittest: antibiotic names, security ([§11.4](known-issues.md))
│
├── frontend/                    Flask app (port 5001 by default)
│   ├── app.py                   22 routes; a thin proxy over the Django API
│   ├── exports.py               CSV and PDF downloads of a tool page's result
│   ├── templates/               11 Jinja2 pages, all extending base.html
│   └── static/
│       ├── css/                 8 files: tokens → layout → components → … → dark
│       └── js/                  10 files, one per page + main.js + dropdowns.js
│                                + report-charts.js (shared by /models and /compare)
│
├── web/                         React + TypeScript frontend, replacing frontend/ page by page
│   ├── src/pages/               one folder per tool page (forecast/, predict/, timeline/)
│   ├── src/components/          navbar, footer, charts (Plot), downloads, FASTA input
│   └── src/lib/                 API calls, model numbers, theme; *.test.ts(x) beside the code
│
├── amrpredict-lib/              The packaged library (see [§7](library.md))
│   ├── src/amrpredict/          Flat API, CLI, 3 predictors, bundled models
│   ├── tests/                   30 pytest tests
│   ├── docs/                    quickstart, api-reference, cli, known-issues
│   └── dist/                    Built wheel + sdist, v0.1.0
│
├── experiments/                 Model training & comparison harness ([§5.4](data-and-training.md))
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
│   ├── amr_full/                The complete BV-BRC AMR export, 17.6 M records (not in git; cleaning v6 and later)
│   ├── amr_output/              3,655 per-species AMR CSVs (earlier files, cleaning v1 to v5)
│   ├── mapped_output/           The same rows joined to FASTA paths
│   └── fasta_output/            Genome assemblies (4 GB)
│
├── progress/                    Team trackers, research plan, handover formats
├── notebooks/                   The current models step by step (01–03), Ali's Colab tools, archive/ (July notebooks) ([§6](data-and-training.md))
├── docs/                        Roadmap, experiment plan, the long reference doc, data links
├── scripts/                     fasta_amr_map.py (CSV to FASTA join), train_all.bat,
│                                bvbrc_download/ (the scripts that built Data/)
├── start.sh / start.bat         One-command launchers (macOS/Linux, Windows)
├── README.md / CHANGES.md       This file and the change log
```

**The data is committed, except the complete export.** The folder `Data/` holds earlier AMR files (`amr_output/`) and 4 GB of FASTA, so the project runs from a clone alone. The complete export in `Data/amr_full/` (17.6 M records, 5.3 GB, what the experiments read since cleaning v6) is not in git: fetch it with `scripts/bvbrc_download/download_amr_full.py`, or take the cleaned table from Drive (`docs/DATA_LINKS.md`). The 101 MB *Klebsiella* CSV in `amr_output/` is stored with Git LFS. `.gitignore` still excludes the experiment cache, saved experiment models and raw predictions. The artifacts in `backend/trained_models/` are committed binaries dated 10 July, trained before this data layout existed, see [§11.2](known-issues.md).

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
- **Models load once, not per request.** The file `api/apps.py` calls `model_registry.init_models()` in `ready()`, so the ~7 MB of artifacts is read at boot, not on every prediction. The registry is a plain module-level global with an idempotence guard (`if _lgbm is not None: return`).

### A worked trace: uploading a genome on `/predict`

1. **Browser** - `resistance_prediction.html` posts `antibiotic`, `threshold`, and either `fasta_file` or `fasta_text`. Client-side JS blocks submission if neither is present (`static/js/prediction.js`).
2. **Flask** (`app.py:115-150`), picks the branch: a file goes to Django as `multipart/form-data`; pasted text goes as JSON. If neither, it returns the page with an error rather than calling the backend.
3. **Django** (`api/views.py:95-128`), decodes the upload, rejects empty FASTA or empty antibiotic with HTTP 400, then calls the engine.
4. **Engine** (`ml_models/genome_predictor.py`), reads the whole genome contig by contig, counts 4-mers over A/C/G/T windows only (as in training), adds the antibiotic, GC content and length, asks LightGBM for the probability, and applies the model's threshold (0.43). Genomes under 100,000 bp are refused. (Until 2026-09-29 this was `resistance_predictor.py`: a RandomForest on the first 500,000 bp.)
5. **Back up**, the dict returns as JSON; Flask puts it in `result` and re-renders the same template, which now draws the probability bar and a Plotly bar chart of the top 20 k-mers.

Every page follows this pattern: **POST to itself, render the result inline.** There is no SPA, no client-side routing, no JSON API consumed by JavaScript except the dropdown lists.
