# Progress: Malik Muhammad Suleman Saleh (SP23-BCS-068)

**Role:** platform (web app, API, security, testing, deployment)
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../docs/FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-28 (research track added by Ali)

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
| 3 | 12 Oct to 16 Oct | Genome result UI, genome-models section on `/models`, Dockerfile with AMRFinderPlus | Not started; the Dockerfile depends on Hamza's model choice (Week 3, day 1) |
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

- [ ] **Genome-models section on `/models`** (from Hamza): Track B runs (`B*`, `L_*`) are kept out of `model_report.json`, because their dataset (2,505 genomes, mostly computational labels) differs from the tabular runs. Show them separately with each run's **lab AUC and its row count** (`auc_roc_lab`, `n_lab` in `experiments/results/registry.csv`; table in `experiments/RESULTS.md`), and say that computational-label scores are partly circular. The numbers will change when Hamza re-runs on Ali's lab-tested genomes, so read them from the file, don't type them
- [ ] `/predict` shows `genes_found` (gene, drug class) next to the prediction; build against `progress/formats/genome_response.sample.json` before Hamza's model lands
- [ ] Dockerfile for the backend with AMRFinderPlus installed (conda), so Railway can run it. **Only if Hamza serves the gene model (B6):** he decides on Week 3 day 1 (k-mer model = no extra install). Ask him before starting
- [ ] Upload limit check: complete genomes are 2–7 MB, under your 20 MB limit, so no change is needed; Hamza is removing the backend's 500 kb cut so the whole genome is used
- **Done when:** `/predict` explains a prediction by the genes it found, in the deployed container, and `/models` shows the genome runs separately

---

## Week 4: RL panel and tests

### RL panel on `/timeline`

- [x] Remove the "CNN-LSTM deep-learning model is available for training" claim (`mutation_timeline.html:164`, `train.html:142, 147, 154`): `/train` only trains `lgbm` and `kmer`, and the format drops the CNN-LSTM label *Done 2026-09-27, with the "results are accurate" claims on the same cards*

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
| From Ali | Timeline + RL response format | Day 1 | \[x\] agreed 2026-09-26, formats §4; `/api/timeline/` already returns the §4 timeline fields (`simulation`, `seed`, `calibration: null`, fractions sum to 100) |
| From Ali | FYI, your files touched 2026-09-26: `views.py` and `app.py` read antibiotic names from `amr_constants.py`; `components.css` draws the missing `bi-dna` / `bi-bacteria` icons; favicon in `static/` with a `/favicon.ico` route in `app.py`. Still yours: two templates mention CNN-LSTM (`mutation_timeline.html:164`, `train.html:142, 147, 154`; `datasets.html` no longer does, checked 2026-09-27) | Week 2 | \[ \] CNN-LSTM wording |
| From Ali | FYI, your file touched 2026-09-28: `mutation_timeline.html` shows the new `calibration` object under the result and in the Simulation Model card, and three claims that the constants were "calibrated from published clinical data" now say they are hand-set and checked against published data. Fields in formats §4 | Week 3 | [x] FYI |
| From Ali | FYI, your file touched 2026-09-28: `datasets.html` Dataset 3 (complete genomes) now says 24,926 genomes, 22,475 with a lab result, 102.5 billion bp, 98 GB, 22,949 with a resistance gene (was 2,587) | Week 3 | [x] FYI |
| From Ali | **Mark Dataset 2 as superseded on `/datasets` once Hamza's genome model is on `/predict`.** Dataset 2 (partial FASTAs, `fasta_output/`) only feeds the old K-mer model; Dataset 3 (complete genomes) replaces it. Then label Dataset 2 "Superseded by Dataset 3; kept to reproduce the original K-mer model" (or fold it into Dataset 3 as a note). Do not remove it: the report compares the two (K-mer 0.70 on partial vs 0.90 on complete genomes). Hamza tells you when he deploys | Week 3 (after Hamza's deploy) | [ ] |
| From Ali | FYI, your file touched 2026-09-28: `datasets.html` has a new Dataset 5 section (published resistance curves for the timeline calibration: Maltas et al. 2025 lab evolution and ECDC surveillance, with the ECDC attribution), a fifth row in the source table, and "five source datasets" in the counts | Week 3 | [x] FYI |
| From Ali | Working RL output | Week 4 | \[ \] |
| From Ali | **Research track** (2026-09-28, [RESEARCH_PLAN.md](RESEARCH_PLAN.md)): three platform items for the papers. (1) Agree with the team and supervisor on making the repo public, which starts the roughly six-month clock JOSS needs for the library paper. (2) CI green on `main` (your T2.7), which reviewers check. (3) Stale numbers in README section 0 and 11.1, endpoint and test counts, so nothing we quote contradicts the repo | Weeks 4 to 5 | [ ] |
| To Hamza | Agreement on the backend switch to the `amrpredict` library (`backend/api/`) | Week 4 | \[ \] |

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
| 2026-09-27 | Week 2 done: CSV/PDF/PNG downloads on `/forecast`, `/predict`, `/timeline`; batch CSV upload with template, summary, chart and results CSV; CNN-LSTM text removed; 16 new tests | Genome section on `/models`, `genes_found` UI (Week 3) | Genome section waits on Hamza's report export |
| 2026-09-27 | Pulled Hamza's Week 1 close (D3, threshold 0.23) and Week 2: `/models`, `/compare` show D3, sliders follow 0.23 with no change. Added Hamza's genome-section request | T2.2 exports | Genome section waits on Hamza's report export |
| 2026-09-26 | T2.4 security: env-only secrets and hosts, no CORS, admin token on train/reload + password on `/train`, 20 MB upload limit, rate limits, no database; 13 tests | T2.2 exports | None |
| 2026-09-26 | T1.3: every page reads its AUC from `metrics.json` via `/api/health/`; sliders start at the validated threshold (0.24); fallback and unknown-drug warnings | T2.4 security | None |
| 2026-09-26 | Antibiotic dropdown 47 → 82: Ali's 15 drugs plus 20 more from `BVBRC_genome_amr.csv`; spelling variants listed for Ali | T1.3 hardcoded AUCs | None |
| 2026-09-25 | Tracker created | Agree formats, start T1.3 | None |
