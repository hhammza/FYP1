# Progress: Malik Muhammad Suleman Saleh (SP23-BCS-068)

**Role:** platform (web app, API, security, testing, deployment)
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../docs/FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-28 (research track added by Ali; genes panel on `/predict`, UI fixes, Ali's Week 3 handovers)

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

**Before each work session (all three of us)**
1. `git pull` first. Commit small and often, and push the same day, so nobody works on stale files.
2. After a pull: `pip install -r experiments/requirements.txt` (it includes the backend requirements).
3. Edit these trackers in a plain text editor (VS Code's normal editor). A visual Markdown editor re-saved them twice and broke them: merged header lines, `[~]` turned into `\[\~\]`, links lost.
4. Someone else's file: add a row to their **Handovers** table only, and say so in the channel.
5. `Data/` and `experiments/cache/` are not in git. Share big files on Drive, not in commits, and keep `Data/` out of OneDrive sync.
6. Read Genome IDs as text (`dtype=str`). As a number, `195.304` and `195.3040` become one genome (the cleaning v5 bug).
7. Backend by hand: `set DEBUG=True` first; Train and Reload need `ADMIN_TOKEN`. `train_models.py` writes to `trained_models/candidates/`; only `experiments/promote.py` changes the model the website serves.
8. Genome-model numbers: quote the **lab** AUC (`Lab AUC` in `RESULTS.md`). BV-BRC's computational labels were predicted from the genome, so all-row scores are partly circular.

---

## Summary

| Week | Dates (planned) | Focus | Status |
| --- | --- | --- | --- |
| 1 | 28 Sep to 2 Oct | Remove hardcoded AUCs, UI reads `metrics.json`, security | Done (T1.3, T2.4) |
| 2 | 5 Oct to 9 Oct | Exports (CSV, PDF, PNG), batch CSV upload | Done 2026-09-27 (T2.2, T2.3) |
| 3 | 12 Oct to 16 Oct | Genome result UI, genome-models section on `/models`, Dockerfile with AMRFinderPlus | In progress: genes panel built (waits for real `genes_found`); genome section and AMRFinderPlus wait on Hamza |
| 4 | 19 Oct to 23 Oct | RL panel on `/timeline`, automated tests | Not started |
| 5 | 26 Oct to 30 Oct | Deploy, tag, demo video, system-design chapter | Not started |
| Research | alongside weeks 4 to 5 | Repo public, CI green, stale README numbers ([Research track](#research-track-added-by-ali-2026-09-28), added by Ali) | Not started |

**Files I own:** `frontend/`, `backend/api/`, `backend/backend/settings.py`, backend and frontend tests, Dockerfile and Railway config. Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: agree the handover formats

- [x] `metrics.json` **format** agreed with Hamza; get a sample file to build against

- [x] **Genome prediction response** agreed with Hamza: today's response plus `genes_found: [{gene, drug_class}]`

- [x] **Timeline + RL response** agreed with Ali: weekly susceptible, intermediate and resistant fractions, plus a `policy` list. *Agreed 2026-09-26 after checking it against the live response; my three questions (tie rule for `rl.best`, requested drug always in `rl.drugs`, `calibration` types) answered by Ali in formats §4*

- [x] **Batch CSV template and response** defined by me: columns `antibiotic, genus, species, taxon_id, mic_value, mic_sign`; one result row per input row with an `error` column

- [x] Formats written down in the team channel or below

> Agreed formats: **[progress/formats/README.md](formats/README.md)** (Hamza: metrics files, genome response; Ali: gene matrix, timeline + RL in §4 with [`timeline_response.sample.json`](formats/timeline_response.sample.json)). My batch CSV format is section 5.

---

## Week 1: honest numbers and security

### Antibiotic dropdown (from Ali's T1.5)

- [x] `frontend/app.py:ANTIBIOTICS`: replace `rifampin` with `rifampicin`

- [x] Consider adding common drugs the list lacks (1,000+ rows each): spectinomycin, ceftiofur, ampicillin/sulbactam, sulfisoxazole, pefloxacin, penicillin, ceftazidime/avibactam, ceftolozane/tazobactam, cefixime, telithromycin, moxifloxacin, clarithromycin, temocillin, cefpirome, florfenicol

  - All 15 added to `frontend/app.py:ANTIBIOTICS` and the matching list in `backend/api/views.py:AntibioticListView` (47 → 62), grouped by drug class
  - 2026-09-26: 20 more from `BVBRC_genome_amr.csv` (171,000 rows) that the list lacked (62 → 82): cefotetan, fosfomycin, cefpodoxime, cefoperazone/sulbactam, cefmetazole, cefozopran, ceftazidime/clavulanic acid, cefotaxime/clavulanic acid, ceftobiprole, lincomycin, oxytetracycline, cefpodoxime/clavulanic acid, ceftaroline, ticarcillin/clavulanic acid, apramycin, carbenicillin, imipenem/relebactam, delafloxacin, ceftibuten, cefepime/taniborbactam
  - Not added, because they are spellings of drugs already listed (for Ali's `ANTIBIOTIC_ALIASES`): phosphomycin → fosfomycin, tigecyklin → tigecycline, tetracyklin → tetracycline, amoxicillin_clavulanat → amoxicillin/clavulanic acid, cefpirom → cefpirome, cefepime_taniborbactam → cefepime/taniborbactam; `sulfa` is a drug group, drop it like `carbapenem`. *Added by Ali 2026-09-26 (`75f7cb0`), plus 7 more variants; `sulfa` dropped*
  - 2026-09-26 (Ali, `b1b1e67`): the list now lives in `backend/amr_constants.py:UI_ANTIBIOTICS`; `frontend/app.py` reads the generated `frontend/antibiotic_names.json` and `views.py` imports it. `VOCAB_EXCLUDE` is replaced by the alias map. To add a drug: edit `amr_constants.py`, run `python backend/amr_constants.py`, commit both
  - The `/forecast`, `/predict` and `/timeline` dropdowns still show only the names the loaded model knows (`?model=lgbm|kmer`); this static list is the fallback when the backend is down
  - Not in either shipped model yet: cefixime, clarithromycin, temocillin, cefpirome, florfenicol. They appear once Hamza's retrained model lands. *Checked 2026-09-27: the served D3 knows all five (126 drugs)*

### T1.3 Replace every hardcoded AUC (22 places)

Built against the real files (`backend/trained_models/lgbm_metrics.json`, `kmer_metrics.json`), read through `/api/health/`. Done 2026-09-26.

- [x] `base.html:140` (footer), plus the footer's records and antibiotics tiles

- [x] `index.html:39, 40, 59, 67, 217, 255, 294, 435, 497`, plus the training-size figures in the same cards

- [x] `resistance_forecast.html:29, 385, 460`

- [x] `resistance_prediction.html:15, 29, 344` (344 was `0.9290`, which the grep below misses)

- [x] `about.html:34, 155, 174, 503, 507`, plus the threshold and training-size rows

- [x] `datasets.html:347`

- [x] One sentence on `/about` explaining that the earlier 0.93 was inflated and the honest figure is about 0.82. *The served model (D1, species taxa) scores 0.804, so the page says that*

- [x] Also: sliders on `/forecast` and `/predict` start at the model's `default_threshold` (0.24, 0.5) instead of 0.40 and 0.5, with step 0.01 so 0.24 doesn't snap to 0.25; the API no longer forces 0.40 / 0.5 when no threshold is sent; the `/forecast` chart line sits at the model's threshold, not 50%. *Checked 2026-09-27: it follows each promotion; the served D3 starts at 0.23*

- [x] Also: warnings for `model_used: Heuristic fallback` (both pages) and `antibiotic_known: false` (`/predict`), per Hamza's format

- [x] Also: `/datasets` threshold note and the deployed-model points on the `/models` VME/ME chart read the real threshold (0.24), not 0.40

- [x] **Flag for Hamza/Ali:** `train_models.py` (via `/train`) overwrites the served model in `backend/trained_models/` but does not rewrite `lgbm_metrics.json`, and its `lgbm_meta.joblib` drops the threshold and calibration. After a retrain from the web page, every page would show D1's 0.804 for a different model. Until fixed, don't use `/train` on the served models (T2.4 will put it behind a token)
  - [x] My part, 2026-09-26: `/api/train/` now trains into `backend/trained_models/candidates/<model>/` (`CANDIDATE_MODELS_DIR` in `settings.py`) and no longer reloads the served model; tested: served files byte-identical after a train, D1 still loaded
  - [x] Ali, 2026-09-26 (`63a2c99`): `train_models.py` from the command line now defaults to `trained_models/candidates/<model>/`; served files checked byte-identical after a run

- **Met 2026-09-26:** the grep finds only `/about` and `/models`; all 10 pages render 0.804 / 0.695 from the files, and "not measured" when the backend is down

- **Done when:** `grep -rn "0\.93\|0\.9255" frontend/templates` finds nothing except the explanation on `/about` and `/models`

### T2.4 Security hardening

- [x] `settings.py:6`: `SECRET_KEY` from the environment only; stop at startup if missing when `DEBUG=False`. *With `DEBUG=True` and no key, a random one per process (the API keeps no sessions)*

- [x] `settings.py:8`: `ALLOWED_HOSTS` from the environment, no `*` default; stops at startup if empty when `DEBUG=False`

- [x] `settings.py:50`: replace `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOWED_ORIGINS` = the frontend URL. *Set to none by default: browsers never call the API (Flask calls it from its server), so no origin needs access; `CORS_ALLOWED_ORIGINS` env var if that changes*

- [x] `/api/train/` and `/api/reload/` need an `X-Admin-Token` header (value from the environment); the Train page asks for a password. *No `ADMIN_TOKEN` set = both switched off (503); `/api/train/` also accepts only `lgbm` or `kmer`, since the name is now part of a folder path*

- [x] Review the 9 `csrf_exempt` uses in `backend/api/views.py`. *8 decorators (the 9th hit was the import). Removed: no CSRF middleware was installed, so they did nothing, and CSRF does not apply to an API that uses no cookies; reason written at the top of `views.py`*

- [x] Upload size limits (`DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`); reject FASTA over 20 MB. *413 from the backend (file, pasted text, or body size) and from Flask (`MAX_CONTENT_LENGTH`, message shown on the page)*

- [x] Rate limiting on predict endpoints (`django-ratelimit`). *Per visitor IP (Flask forwards it): forecast 60/min, predict and timeline 10/min, JSON 429. Counts are per worker process, and a direct caller can fake the IP header, so it stops casual abuse only*

- [x] Remove the unused `db.sqlite3` and `migrate` step, or add a prediction-history model. *Removed: `DATABASES = {}`, `release: migrate` gone from `Procfile`, `migrate` gone from `run_project.md`*

- [x] Also: Flask's hardcoded `secret_key` removed (it uses no sessions); Flask's debug server listens on 127.0.0.1 only (its debugger can run code); `start.bat`, `start.sh` and `run_project.md` set `DEBUG=True` for local runs

- **Done when:** train/reload without the token return 401, and the app runs with no default secrets. **Met 2026-09-26:** `backend/tests/test_security.py`, 13 tests, all pass (with Ali's 6: 19/19)

---

## Week 2: exports and batch upload

### T2.2 Exports on `/forecast`, `/predict`, `/timeline`

- [x] **CSV:** routes such as `/export/forecast.csv`; timeline gives one row per week. *`POST /export/<page>.csv`: the page posts back the result it showed; formulas in cells are neutralised*

- [x] **PNG:** "Download chart" button using `Plotly.downloadImage`. *`Plotly.toImage` on a light copy of the chart, so it prints well whatever the page theme (`static/js/export.js`)*

- [x] **PDF:** ReportLab report with inputs, prediction, probability, model name, version and AUC from `metrics.json`, charts, timestamp, and "research tool, not a clinical diagnostic". *`frontend/exports.py`; model details come from the metrics files on the server, never from the page; only a real PNG is embedded*

- [x] Timeline exports say **"Simulation, not a trained model"** *(banner and footer of the PDF, every CSV row)*

- **Done when:** each of the three pages downloads all three formats. **Met 2026-09-27** (CSV and PDF checked end to end with the real backend; the PNG button runs in the browser, so try it once by hand)

### T2.3 Batch CSV upload on `/forecast`

- [x] "Upload CSV" tab and a downloadable sample template (`/forecast/template.csv`)

- [x] `POST /api/forecast/batch/`: validate each row, predict in one call, per-row result + `error` column. *Same probabilities as the single `/forecast`; unknown antibiotics are an error, a MIC sign without a value is ignored as on `/forecast`*

- [x] Summary table (R/S counts, per-antibiotic chart) and "Download results CSV" (the page lists the first 200 rows; the CSV has all)

- [x] Limits: 10,000 rows and a maximum file size, checked on the server (2 MB; 5 uploads a minute per visitor)

- [x] Add the batch CSV format (template columns, response, `error` column) to `progress/formats/README.md` as a new section, like the others, so Hamza can check it against `LGBMResistancePredictor.features_frame()` *Done 2026-09-27: section 5*

- **Done when:** a 1,000-row file returns a results CSV with errors marked per row. **Met 2026-09-27:** 1,000 rows in 0.1 s, errors on exactly the 3 bad rows. Tests: `backend/tests/test_batch.py` (7), `frontend/tests/test_exports.py` (9)

---

## Week 3: genome result UI and container

- [x] **Genome-models section on `/models`** (from Hamza): Track B runs (`B*`, `L_*`) are kept out of `model_report.json`, because their dataset (2,505 genomes, mostly computational labels) differs from the tabular runs. Show them separately with each run's **lab AUC and its row count** (`auc_roc_lab`, `n_lab` in `experiments/results/registry.csv`; table in `experiments/RESULTS.md`), and say that computational-label scores are partly circular. The numbers will change when Hamza re-runs on Ali's lab-tested genomes, so read them from the file, don't type them *Note (Ali, 2026-09-28): "2,505 genomes" is out of date. Hamza is re-running on the 22,475 lab-tested genomes (24,926 x 2,733 gene table), so build against his new runs, not the old ones* *Done 2026-09-29: Section 5 on `/models` reads Hamza's `genome_runs` list (formats §6): the runs of the newest cleaning version (v6, 33) with a lab AUC, chart coloured by kind of split, table with `n_lab` beside every score, the served run (`G_kmer_deploy`) starred. 5 tests*
- [~] `/predict` shows `genes_found` (gene, drug class) next to the prediction; build against `progress/formats/genome_response.sample.json` before Hamza's model lands. *Built 2026-09-28 (`templates/_genes_panel.html`): all three states of the format (absent = one "not searched" line; `[]` = searched, none found; a list = genes linked to the drug's class first, with a sentence on whether they support the call), in the CSV and PDF too. Preview at `/predict/sample` on a local run. The heading and k-mer cards follow the model, so a gene model without k-mers shows cleanly. Done once Hamza's model sends real `genes_found`*
- [~] Dockerfile for the backend with AMRFinderPlus installed (conda), so Railway can run it. **Only if Hamza serves the gene model (B6):** he decides on Week 3 day 1 (k-mer model = no extra install). Ask him before starting *Hamza decided 2026-09-29: k-mers now, genes later, so AMRFinderPlus stays in the Dockerfile. Not built yet (no Docker on this laptop)*
- [x] **The 30 s wait on `/predict` must grow before the gene model**: AMRFinderPlus takes 10–45 s per genome (Ali). Raise the Flask → backend timeout and gunicorn's (120 s now), or run the prediction as a background job with a "working…" page. *Needed when Hamza's gene-model path in `genome_predictor.py` lands* *Done 2026-09-29, ready before the gene model: `/predict` waits `PREDICT_TIMEOUT` = 120 s (other pages keep 30 s); gunicorn's `--timeout` is 150 s, above it, so the page gives up first; a timeout shows "The backend did not answer within 120 seconds…" (504) instead of the raw `requests` error. After Predict the button says "Analysing the genome…" with a note that a complete genome can take up to a minute, and stays disabled for the whole wait (it used to come back after 30 s, mid-request, inviting a second click; and it no longer spins when the page stops a submit without a genome). A background job was not needed at this length. 4 tests*

- [x] Dockerfile groundwork, needed whatever Hamza decides: a `.dockerignore` so `COPY . /app` leaves out `Data/` (about 100 GB with Ali's complete genomes) and the experiment caches, and `gunicorn` instead of `manage.py runserver` *Done 2026-09-29: root `.dockerignore` (the image gets `backend/` only), `COPY backend/`, gunicorn on `$PORT`, conda cache cleaned, scikit-learn pinned to 1.6.1 (the version `kmer_resistance_model.pkl` was saved with). Checked by running the backend from a copy of `backend/` alone in production mode. `railway.toml` still says NIXPACKS until the Week 5 deploy*
- [x] **Follow-ups to Hamza's `/predict` switch** (he wired `GenomeModelPredictor` into `model_registry.py` and promoted `G_kmer_deploy`). *Done 2026-09-29: his choice moved into `predict_model()`, so `/api/reload/` makes it again (a model promoted while the server runs takes over without a restart); a refused genome (under 100 kb) is a 400 with the reason; the stats strip reads the served model's metrics (287.8K pairs, 111 antibiotics, threshold 0.43, not the old model's hand-typed 6,002 / 62 / "100 trees"); hints and the Load Sample tip say complete genomes of at least 100,000 bp. 10 tests (`test_genome_wiring.py` 7, `test_predict_model.py` 3)*
- [x] Upload limit check: complete genomes are 2–7 MB, under your 20 MB limit, so no change is needed; Hamza is removing the backend's 500 kb cut so the whole genome is used. *Checked 2026-09-28: no change*
- **Done when:** `/predict` explains a prediction by the genes it found, in the deployed container, and `/models` shows the genome runs separately

---

### From Ali (2026-09-28)

- [x] Test the new `start.bat` once on Windows (Ali could only test on his Mac). *Its offline check works here: with everything installed it skips the online install. Still to do: one full run by hand (both windows open, site loads), and once with Wi-Fi off; then tell Ali* *2026-09-29, first run by hand: "Could not find platform independent libraries" on every step. Cause: `py -3` picked an incomplete copy of Python at `C:\Python314` (no `Lib` folder; it borrows another install's library) and built `.venv` on it. `start.bat` now uses a Python only if it has its own `Lib\os.py`, and rebuilds a `.venv` made from one that doesn't; the banner's dash is a plain hyphen (the console showed "ΓÇö")* *Full run by hand done 2026-09-29 after the fix: `.venv` rebuilt, every dependency installed, both windows open, backend `/api/health/` and the site on 5001 answer 200. Still to do: once with Wi-Fi off; then tell Ali (his Handovers table, as he asked)* *Offline check 2026-09-29 (internet blocked through a dead proxy): `start.bat` step 2 skips the install ("Dependencies already installed; skipping, no internet needed"), and the servers need no network. But every page loads Bootstrap CSS/JS and its icons (cdn.jsdelivr.net), Plotly (cdn.plot.ly) and the fonts (Google Fonts) from the internet (`base.html`), so offline the site opens unstyled and without charts. Fix if the demo must work offline: copy those files into `frontend/static/vendor/` (about 4 MB, mostly Plotly) and load them from there* *Fixed 2026-09-29: Bootstrap 5.3.2 CSS/JS, Bootstrap Icons 1.11.3 (with its fonts) and Plotly 2.26.0 are served from `frontend/static/vendor/` (4.3 MB, same versions, `-text` in `.gitattributes`); only the Google fonts stay remote and fall back offline. Checked in Edge with every non-local request blocked: layout, icons, tooltips and the 7 charts on `/models` all work. 2 tests (`test_offline_assets.py`). Told Ali in his Handovers table*

- [x] After Hamza's genome model is on `/predict`: on `/datasets`, label Dataset 2 *"Superseded by Dataset 3, kept to reproduce the original K-mer model"*. Don't remove it *Done 2026-09-29: the label as a note at the top of the Dataset 2 section and a "Superseded" badge in the overview. Also fixed: Dataset 2's boxes showed the new model's training rows (287,774, from Dataset 3) because `metrics.kmer` is now the served model; they give the original model's 6,002 and AUC 0.695. The `/predict` model card says K-mer LightGBM on Dataset 3. 3 tests (`test_datasets_page.py`)*

---

## Week 4: RL panel and tests

### RL panel on `/timeline`

- [x] Remove the "CNN-LSTM deep-learning model is available for training" claim (`mutation_timeline.html:164`, `train.html:142, 147, 154`): `/train` only trains `lgbm` and `kmer`, and the format drops the CNN-LSTM label *Done 2026-09-27, with the "results are accurate" claims on the same cards*

- [x] **Converter from Ali's RL environment to format §4** (his question 4, 2026-09-30). *Done: `experiments/evolution/rl_output.py` turns `rl_env.py`'s episodes into the `rl` block: percent 0–100, `failure_week` null when never failed, plus optional `effective_weeks` and `mean_burden` (added to §4). His `rl_env.py` untouched. 8 tests (`test_rl_output.py`), matched against his `run_episode`. Questions for Ali in his Handovers table: horizon 104 vs a 1–52 week request; the env's curve vs the main timeline's*
- [ ] Panel labelled **"Simulation + RL policy (not trained on patient data)"**, built against Ali's agreed response format

- [ ] Chart of the RL policy against the fixed baselines

### T2.7 Automated tests

- [ ] Backend (Django test client): every endpoint, valid input 200, missing fields 400, oversized upload 413, train/reload without token 401

- [ ] Frontend (Flask test client, backend mocked): every page renders; export routes return the right `Content-Type`

- [ ] End-to-end checklist: start both servers, submit each form, download each export

- [ ] GitHub Actions: library and backend tests on every push

- **Done when:** CI is green on `main`

---

## Week 5: deploy and write-up

- [ ] Railway environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, CORS origin, `ADMIN_TOKEN`, `BACKEND_URL`. *Backend: `SECRET_KEY`, `ALLOWED_HOSTS` (its Railway domain, plus `healthcheck.railway.app` for the health check), `ADMIN_TOKEN`; `CORS_ALLOWED_ORIGINS` not needed. Frontend: `BACKEND_URL`*

- [ ] Deploy both services; run the end-to-end checklist against the live URLs

- [ ] `git tag v1.0-submission && git push --tags`

- [ ] 5-minute demo video as a backup

- [ ] **System-design chapter:** architecture diagram, API table, library design, security

- [ ] Update `CHANGES.md` for my work

---

## Research track (added by Ali 2026-09-28)

Alongside weeks 4 and 5, not instead of them. What the papers are and why: [RESEARCH_PLAN.md](RESEARCH_PLAN.md). Paper C is the `amrpredict` library for JOSS, and Paper A quotes numbers that must match the repo.

- [ ] **Making the repo public:** agree with the team and supervisor. *Why:* JOSS needs about 6 months of public history before the library paper

- [ ] **CI green on the main branch** (your T2.7). *Why:* reviewers and JOSS check for it

- [ ] **Stale numbers:** README section 0 and 11.1, endpoint counts, test counts (27 test functions found, not 30). *Why:* nothing we publish should contradict our own repo

- **Done when:** the repo is public with a green CI badge, and the README numbers match `RESULTS.md`

---

## Handovers

| From / to | What | Needed by | Status |
| --- | --- | --- | --- |
| From Ali | Antibiotic dropdown note | Week 1 | \[x\] in this file (week 1) |
| From Ali | FYI: `backend/api/views.py` `TrainModelView` now returns 503 when training data is missing (8 lines, T1.2). Optional: set `DATA_DIR = BASE_DIR.parent / 'Data'` in `settings.py` for clarity; the trainer already finds `Data/` itself | Week 1 | \[x\] merged |
| From Hamza | Sample `metrics.json` | Day 1 | \[x\] `progress/formats/lgbm_metrics.sample.json` |
| From Hamza | Real `metrics.json` for both models | End of week 1 | \[x\] used by T1.3 |
| From Hamza | Genome response with `genes_found` | Week 3 | \[ \] |
| From Hamza | **Genome-models section on `/models`** (2026-09-27): Track B runs (`B*`, `L_*`) are kept out of `model_report.json` by `export_report.py`, because their dataset (2,505 genomes, mostly computational labels) differs from the tabular runs, so a 0.98 would mislead next to 0.82. Show them separately, with each run's lab AUC and its row count (`auc_roc_lab`, `n_lab` in `experiments/results/registry.csv`); results in `experiments/RESULTS.md` | Week 3 | \[ \] |
| From Hamza | **Answers to your 4 questions (2026-09-29):** (1) `/predict` serves **k-mers now** (`G_kmer_deploy`, lab AUC 0.935, live), **genes later**: keep AMRFinderPlus in the Dockerfile; it takes 10–45 s per genome (Ali), so the 30 s wait must grow or become a background job; (2) `genes_found` comes with the gene model; until then the k-mer model sends no `genes_found` (your panel shows "Not searched") but still sends `top_kmers`; (3) `genome_runs` is in `model_report.json`, format written as formats §6 (edit it if the page needs more); show the `*_v6` runs, lab AUC with `n_lab`; (4) the model is live: please mark **Dataset 2** on `/datasets` "Superseded by Dataset 3, kept to reproduce the original K-mer model" | Week 3 | \[ \] Dataset 2 label |
| From Hamza | **FYI, your files Hamza edited for the new `/predict` model (2026-09-29):** `backend/api/model_registry.py` (serves `GenomeModelPredictor` when `trained_models/genome/` exists, else the old RandomForest); `index.html`, `resistance_prediction.html`, `about.html` (text describing the model: LightGBM on the complete genome, no 500 kb cut, 100 kb minimum); `models.html`, `compare.html`, `models.js`, `compare.js` (the deployed k-mer model's name comes from the report instead of "K-mer RF"). `/datasets` and `/train` untouched (they describe Dataset 2 and the trainer, which are unchanged). Formats §5 batch CSV checked against `features_frame()`: consistent | Week 3 | \[x\] FYI |
| From Ali | Timeline + RL response format | Day 1 | \[x\] agreed 2026-09-26, formats §4; `/api/timeline/` already returns the §4 timeline fields (`simulation`, `seed`, `calibration: null`, fractions sum to 100) |
| From Ali | FYI, your files touched 2026-09-26: `views.py` and `app.py` read antibiotic names from `amr_constants.py`; `components.css` draws the missing `bi-dna` / `bi-bacteria` icons; favicon in `static/` with a `/favicon.ico` route in `app.py`. Still yours: two templates mention CNN-LSTM (`mutation_timeline.html:164`, `train.html:142, 147, 154`; `datasets.html` no longer does, checked 2026-09-27) | Week 2 | \[ \] CNN-LSTM wording |
| From Ali | FYI, your file touched 2026-09-28: `mutation_timeline.html` shows the new `calibration` object under the result and in the Simulation Model card, and three claims that the constants were "calibrated from published clinical data" now say they are hand-set and checked against published data. Fields in formats §4 | Week 3 | [x] FYI |
| From Ali | FYI, your file touched 2026-09-28: `datasets.html` Dataset 3 (complete genomes) now says 24,926 genomes, 22,475 with a lab result, 102.5 billion bp, 98 GB, 22,949 with a resistance gene (was 2,587) | Week 3 | [x] FYI |
| From Ali | **Mark Dataset 2 as superseded on `/datasets` once Hamza's genome model is on `/predict`.** Dataset 2 (partial FASTAs, `fasta_output/`) only feeds the old K-mer model; Dataset 3 (complete genomes) replaces it. Then label Dataset 2 "Superseded by Dataset 3; kept to reproduce the original K-mer model" (or fold it into Dataset 3 as a note). Do not remove it: the report compares the two (K-mer 0.70 on partial vs 0.90 on complete genomes). Hamza tells you when he deploys | Week 3 (after Hamza's deploy) | [ ] |
| From Ali | FYI, your file touched 2026-09-28: `datasets.html` has a new Dataset 5 section (published resistance curves for the timeline calibration: Maltas et al. 2025 lab evolution and ECDC surveillance, with the ECDC attribution), a fifth row in the source table, and "five source datasets" in the counts | Week 3 | [x] FYI |
| From Ali | Working RL output | Week 4 | \[ \] |
| From Ali | **Research track** (2026-09-28, [RESEARCH_PLAN.md](RESEARCH_PLAN.md)): three platform items for the papers. (1) Agree with the team and supervisor on making the repo public, which starts the roughly six-month clock JOSS needs for the library paper. (2) CI green on `main` (your T2.7), which reviewers check. (3) Stale numbers in README section 0 and 11.1, endpoint and test counts, so nothing we quote contradicts the repo | Weeks 4 to 5 | [ ] |
| From Ali | FYI, your file touched 2026-09-29: `datasets.html` Dataset 1 now describes the complete BV-BRC export (`Data/amr_full/`, 17,585,506 records, 7,847,110 after cleaning, 87,325 lab-tested genomes). **Update 2026-09-30 (Ali):** the earlier-data comparison is removed from `/datasets`; `/models` and `/compare` now show the complete data only (every experiment on cleaning v7, served models named by their run's cleaning version), with a Key findings section on `/models`. Files: `datasets.html`, `models.html`, `models.js`, `compare.html`, `components.css`; 66 tests pass | Week 4 | [x] FYI |
| To Hamza | Agreement on the backend switch to the `amrpredict` library (`backend/api/`) | Week 4 | [x] Hamza 2026-09-30: **after the demo**. The library now matches the backend (a parity test, `backend/tests/test_library_parity.py`, fails if the two forecasters drift), so nothing breaks meanwhile; switching before the demo would only add risk |

| From Hamza | **Code review (2026-09-30): bad input gives 500 instead of 400 in `backend/api/views.py`.** Checked with Django's test client: `/api/forecast/` with malformed JSON, `threshold: "abc"` or `antibiotic: null`, and `/api/timeline/` with `n_weeks: "x"`, all return **500** with the raw Python message (e.g. `'NoneType' object has no attribute 'strip'`). Suggest: catch `json.JSONDecodeError`, `ValueError` and `TypeError` around parsing and return `json_error(..., 400)` with a plain message (e.g. "threshold must be a number between 0 and 1"), and check the threshold range. Same in `frontend/app.py:265`: `float(threshold)` on the pasted-FASTA path raises on a non-number (Flask 500). A test per case in `backend/tests/test_security.py` style | Week 4 | [ ] |
| From Hamza | **FYI, fixed on my side (2026-09-30), no action:** `POST /api/reload/` after a promotion kept the old run's `lgbm_metrics.json` (so `model_run`, `/api/health/` metrics and the slider's default came from the previous run) because the predictor read metrics only at start-up. `lgbm_predictor._load()` now re-reads everything (test `backend/tests/test_lgbm_reload.py`). Also the genome predictor no longer trips a pandas deprecation on an unknown antibiotic, and the heuristic fallbacks are deterministic (no random noise) | Week 4 | [x] FYI |
| From Hamza | **Stale page text** (your templates): `about.html:132-142` and `index.html:479` still describe the July pipeline: an "80/20 stratified train-test split" (the models now use genome-grouped splits, and `/predict` serves LightGBM on complete genomes, not the RandomForest `.pkl`), and "AUC-ROC as the primary metric" (we report AUPRC, VME/ME and lab AUC too). `train.html` is right to describe the RandomForest: `/api/train/` still trains the old designs as candidates. Current numbers: `/forecast` `D3_forecaster_deploy_v7` 0.774 (lab 0.908), `/predict` `G_kmer_deploy` lab 0.935 | Week 4 | [ ] |
| From Hamza | **Small, optional:** rate limits use Django's local-memory cache (`settings.CACHES`), which is per process, so with N gunicorn workers each IP gets N × the limit. Fine for the demo; a shared cache (file or Redis) if it matters | Later | [ ] |
| From Hamza | **The gene model's path is ready: your genes panel gets real `genes_found` (2026-09-30).** `backend/ml_models/genome_predictor.py` now serves the gene model whenever AMRFinderPlus is installed on the server, and the k-mer model otherwise (so local Windows runs are unchanged). Per upload it identifies the species from the 6-mer profile, runs AMRFinderPlus with that `--organism` (as training did), builds the gene features (identical to training) and returns `genes_found` in the agreed §2 shape, plus `species_detected`, `model_run`, and `subclass`/`name` per gene; no `top_kmers` (your page already hides the cards). If AMRFinderPlus fails or times out, the k-mer model answers and the response has a `warning` and no `genes_found`. `api/model_registry.py` and `views.py` need no change. The deploy model `G_genes_deploy` trains tonight after the seed runs and is promoted to `backend/trained_models/genome_genes/` automatically; I push it with the results. **Your part:** (1) build the Docker image (your `backend/Dockerfile` already installs AMRFinderPlus 4.2.7 into the base env, which is on PATH, so it is found as is); **recommended:** training used database `2026-08-07.1`, while `amrfinder -u` fetches the newest, so either keep the image's database and accept small naming drift, or download that version from `https://ftp.ncbi.nlm.nih.gov/pathogen/Antimicrobial_resistance/AMRFinderPlus/database/4.2/2026-08-07.1/` into the image and set `AMRFINDER_DATABASE` to that folder; (2) on `/predict`, show `warning` as a warning (like `Heuristic fallback`) and `species_detected.species` as "Identified as *Escherichia coli*" (it can be `null`); (3) check `/api/health/` → `models.kmer_resistance.searches_genes` is `true` on the deployed site. Optional env: `AMRFINDER_THREADS` (4), `AMRFINDER_TIMEOUT` (100 s, under your 120 s). Format §2 and `genome_response.sample.json` are updated; 9 backend tests (`tests/test_gene_model.py`) cover the path with a stand-in for AMRFinderPlus | Week 3 | [x] Hamza's side; [ ] Suleman: (1)-(3) |
---

## Already done (before this plan)

From the git history:

- [x] Early frontend changes (May 2026)

- [x] Fixed the dataset heading count from 5 to 4 on `/datasets` (2026-09-25)

---

## Log

Newest first. One line per work session: date, what I did, what is next, anything blocking.

| Date | Done | Next | Blockers |
| --- | --- | --- | --- |
| 2026-09-29 | `start.bat` test done: full run and offline both work. The site itself needed the internet (Bootstrap, icons, Plotly from CDNs): now served from `static/vendor/`, checked in Edge with the internet blocked. Ali told in his Handovers table. 2 tests | Gene model when Hamza's path lands | Hamza's gene-model path in `genome_predictor.py` |
| 2026-09-29 | `/predict` ready for the gene model's longer runs: waits 120 s (gunicorn 150 s), a clear timeout message, "Analysing the genome…" button that stays disabled for the whole wait. `start.bat` picks a Python with its own library. 4 tests | `start.bat` full run; gene model when Hamza's path lands | Hamza's gene-model path in `genome_predictor.py` |
| 2026-09-29 | Dataset 2 labelled "Superseded by Dataset 3" on `/datasets` (Hamza's request); its numbers are the original model's again (they had switched to the new model's); the `/predict` model card names K-mer LightGBM on Dataset 3. 3 tests | `/predict` wait for the gene model; `start.bat` by hand | Hamza's gene-model path in `genome_predictor.py` |
| 2026-09-29 | Genome section on `/models` from Hamza's `genome_runs` (v6 runs, served run starred); follow-ups to his `/predict` switch (reload picks up a promotion, refused genome = 400, strip from the metrics); Dockerfile groundwork (`.dockerignore`, gunicorn, scikit-learn 1.6.1 pin); pandas warning fixed in `lgbm_predictor.py`. 15 tests | `/predict` wait for the gene model; `start.bat` by hand | Hamza's gene-model path in `genome_predictor.py` (AMRFinderPlus on the upload) |
| 2026-09-28 | Genes panel on `/predict` (`_genes_panel.html`): the three `genes_found` states, linked genes first, in CSV/PDF, `/predict/sample` preview, 7 tests; the heading and k-mer cards follow the model. UI fixes: navbar items on one line (`424c71a`); numbered steps and tags no longer squeezed or split on `/datasets` (`b0c0a82`); two overclaims on `/timeline` (constants hand-set, speeds illustrative). Checked Ali's pushes: all tests pass, `/genes` lookup under 10 ms after the first, `start.bat` offline check works | Genome section on `/models` (needs Hamza's runs in `model_report.json`), Dockerfile groundwork, full `start.bat` run | Hamza's genome model choice and runs |
| 2026-09-27 | Week 2 done: CSV/PDF/PNG downloads on `/forecast`, `/predict`, `/timeline`; batch CSV upload with template, summary, chart and results CSV; CNN-LSTM text removed; 16 new tests | Genome section on `/models`, `genes_found` UI (Week 3) | Genome section waits on Hamza's report export |
| 2026-09-27 | Pulled Hamza's Week 1 close (D3, threshold 0.23) and Week 2: `/models`, `/compare` show D3, sliders follow 0.23 with no change. Added Hamza's genome-section request | T2.2 exports | Genome section waits on Hamza's report export |
| 2026-09-26 | T2.4 security: env-only secrets and hosts, no CORS, admin token on train/reload + password on `/train`, 20 MB upload limit, rate limits, no database; 13 tests | T2.2 exports | None |
| 2026-09-26 | T1.3: every page reads its AUC from `metrics.json` via `/api/health/`; sliders start at the validated threshold (0.24); fallback and unknown-drug warnings | T2.4 security | None |
| 2026-09-26 | Antibiotic dropdown 47 → 82: Ali's 15 drugs plus 20 more from `BVBRC_genome_amr.csv`; spelling variants listed for Ali | T1.3 hardcoded AUCs | None |
| 2026-09-25 | Tracker created | Agree formats, start T1.3 | None |
