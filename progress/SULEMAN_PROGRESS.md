# Progress: Malik Muhammad Suleman Saleh (SP23-BCS-068)

**Role:** platform (web app, API, security, testing, deployment)
**Plan:** the split by skill (Ali: data + evolution, Hamza: models, Suleman: platform), based on [FYP_Completion_Roadmap.md](../FYP_Completion_Roadmap.md)
**Started:** 2026-09-25 · **Last updated:** 2026-09-26

Status key: `[ ]` not started · `[~]` in progress · `[x]` done · `[!]` blocked (say why in the log)

---

## Summary

| Week | Dates (planned) | Focus | Status |
| --- | --- | --- | --- |
| 1 | 28 Sep to 2 Oct | Remove hardcoded AUCs, UI reads `metrics.json`, security | Not started |
| 2 | 5 Oct to 9 Oct | Exports (CSV, PDF, PNG), batch CSV upload | Not started |
| 3 | 12 Oct to 16 Oct | Genome result UI, Dockerfile with AMRFinderPlus | Not started |
| 4 | 19 Oct to 23 Oct | RL panel on `/timeline`, automated tests | Not started |
| 5 | 26 Oct to 30 Oct | Deploy, tag, demo video, system-design chapter | Not started |

**Files I own:** `frontend/`, `backend/api/`, `backend/backend/settings.py`, backend and frontend tests, Dockerfile and Railway config. Other people's files: ask the owner, or comment in their pull request.

---

## Day 1: agree the handover formats

- [x] `metrics.json` **format** agreed with Hamza; get a sample file to build against

- [x] **Genome prediction response** agreed with Hamza: today's response plus `genes_found: [{gene, drug_class}]`

- [x] **Timeline + RL response** agreed with Ali: weekly susceptible, intermediate and resistant fractions, plus a `policy` list

- [x] **Batch CSV template and response** defined by me: columns `antibiotic, genus, species, taxon_id, mic_value, mic_sign`; one result row per input row with an `error` column

- [x] Formats written down in the team channel or below

> Agreed formats:
>
> *(paste here once agreed)*

---

## Week 1: honest numbers and security

### Antibiotic dropdown (from Ali's T1.5)

- [x] `frontend/app.py:ANTIBIOTICS`: replace `rifampin` with `rifampicin`

- [x] Consider adding common drugs the list lacks (1,000+ rows each): spectinomycin, ceftiofur, ampicillin/sulbactam, sulfisoxazole, pefloxacin, penicillin, ceftazidime/avibactam, ceftolozane/tazobactam, cefixime, telithromycin, moxifloxacin, clarithromycin, temocillin, cefpirome, florfenicol

  - All 15 added to `frontend/app.py:ANTIBIOTICS` and the matching list in `backend/api/views.py:AntibioticListView` (47 → 62), grouped by drug class
  - 2026-09-26: 20 more from `BVBRC_genome_amr.csv` (171,000 rows) that the list lacked (62 → 82): cefotetan, fosfomycin, cefpodoxime, cefoperazone/sulbactam, cefmetazole, cefozopran, ceftazidime/clavulanic acid, cefotaxime/clavulanic acid, ceftobiprole, lincomycin, oxytetracycline, cefpodoxime/clavulanic acid, ceftaroline, ticarcillin/clavulanic acid, apramycin, carbenicillin, imipenem/relebactam, delafloxacin, ceftibuten, cefepime/taniborbactam
  - Not added, because they are spellings of drugs already listed (for Ali's `ANTIBIOTIC_ALIASES`): phosphomycin → fosfomycin, tigecyklin → tigecycline, tetracyklin → tetracycline, amoxicillin_clavulanat → amoxicillin/clavulanic acid, cefpirom → cefpirome, cefepime_taniborbactam → cefepime/taniborbactam; `sulfa` is a drug group, drop it like `carbapenem`
  - The `/forecast`, `/predict` and `/timeline` dropdowns still show only the names the loaded model knows (`?model=lgbm|kmer`); this static list is the fallback when the backend is down
  - Not in either shipped model yet: cefixime, clarithromycin, temocillin, cefpirome, florfenicol. They appear once Hamza's retrained model lands

### T1.3 Replace every hardcoded AUC (22 places)

Build against Hamza's sample `metrics.json`, then switch to the real files.

- [ ] `base.html:140` (footer)

- [ ] `index.html:39, 40, 59, 67, 217, 255, 294, 435, 497`

- [ ] `resistance_forecast.html:29, 385, 460`

- [ ] `resistance_prediction.html:15, 29, 344`

- [ ] `about.html:34, 155, 174, 503, 507`

- [ ] `datasets.html:347`

- [ ] One sentence on `/about` explaining that the earlier 0.93 was inflated and the honest figure is about 0.82

- **Done when:** `grep -rn "0\.93\|0\.9255" frontend/templates` finds nothing except the explanation on `/about` and `/models`

### T2.4 Security hardening

- [ ] `settings.py:6`: `SECRET_KEY` from the environment only; stop at startup if missing when `DEBUG=False`

- [ ] `settings.py:8`: `ALLOWED_HOSTS` from the environment, no `*` default

- [ ] `settings.py:50`: replace `CORS_ALLOW_ALL_ORIGINS = True` with `CORS_ALLOWED_ORIGINS` = the frontend URL

- [ ] `/api/train/` and `/api/reload/` need an `X-Admin-Token` header (value from the environment); the Train page asks for a password

- [ ] Review the 9 `csrf_exempt` uses in `backend/api/views.py`

- [ ] Upload size limits (`DATA_UPLOAD_MAX_MEMORY_SIZE`, `FILE_UPLOAD_MAX_MEMORY_SIZE`); reject FASTA over 20 MB

- [ ] Rate limiting on predict endpoints (`django-ratelimit`)

- [ ] Remove the unused `db.sqlite3` and `migrate` step, or add a prediction-history model

- **Done when:** train/reload without the token return 401, and the app runs with no default secrets

---

## Week 2: exports and batch upload

### T2.2 Exports on `/forecast`, `/predict`, `/timeline`

- [ ] **CSV:** routes such as `/export/forecast.csv`; timeline gives one row per week

- [ ] **PNG:** "Download chart" button using `Plotly.downloadImage`

- [ ] **PDF:** ReportLab report with inputs, prediction, probability, model name, version and AUC from `metrics.json`, charts, timestamp, and "research tool, not a clinical diagnostic"

- [ ] Timeline exports say **"Simulation, not a trained model"**

- **Done when:** each of the three pages downloads all three formats

### T2.3 Batch CSV upload on `/forecast`

- [ ] "Upload CSV" tab and a downloadable sample template

- [ ] `POST /api/forecast/batch/`: validate each row, predict in one call, per-row result + `error` column

- [ ] Summary table (R/S counts, per-antibiotic chart) and "Download results CSV"

- [ ] Limits: 10,000 rows and a maximum file size, checked on the server

- **Done when:** a 1,000-row file returns a results CSV with errors marked per row

---

## Week 3: genome result UI and container

- [ ] `/predict` shows `genes_found` (gene, drug class) next to the prediction; works against a sample response before Hamza's model lands

- [ ] Dockerfile for the backend with AMRFinderPlus installed (conda), so Railway can run it

- **Done when:** `/predict` explains a prediction by the genes it found, in the deployed container

---

## Week 4: RL panel and tests

### RL panel on `/timeline`

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

- [ ] Railway environment variables: `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, CORS origin, `ADMIN_TOKEN`, `BACKEND_URL`

- [ ] Deploy both services; run the end-to-end checklist against the live URLs

- [ ] `git tag v1.0-submission && git push --tags`

- [ ] 5-minute demo video as a backup

- [ ] **System-design chapter:** architecture diagram, API table, library design, security

- [ ] Update `CHANGES.md` for my work

---

## Handovers

| From / to | What | Needed by | Status |
| --- | --- | --- | --- |
| From Ali | Antibiotic dropdown note | Week 1 | \[x\] in this file (week 1) |
| From Ali | FYI: `backend/api/views.py` `TrainModelView` now returns 503 when training data is missing (8 lines, T1.2). Optional: set `DATA_DIR = BASE_DIR.parent / 'Data'` in `settings.py` for clarity; the trainer already finds `Data/` itself | Week 1 | \[x\] merged |
| From Hamza | Sample `metrics.json` | Day 1 | \[ \] |
| From Hamza | Real `metrics.json` for both models | End of week 1 | \[ \] |
| From Hamza | Genome response with `genes_found` | Week 3 | \[ \] |
| From Ali | Timeline + RL response format | Day 1 | \[ \] |
| From Ali | Working RL output | Week 4 | \[ \] |
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
| 2026-09-26 | Antibiotic dropdown 47 → 82: Ali's 15 drugs plus 20 more from `BVBRC_genome_amr.csv`; spelling variants listed for Ali | T1.3 hardcoded AUCs | None |
| 2026-09-25 | Tracker created | Agree formats, start T1.3 | None |
