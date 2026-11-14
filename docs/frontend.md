# The web application

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 8. The frontend in detail

### Routes (`frontend/app.py`)

| Route | Methods | Backend call | Page |
|---|---|---|---|
| `/` | GET | `health/` | `index.html`, landing, live model status |
| `/forecast` | GET, POST | `forecast/` | `resistance_forecast.html`, one isolate or an uploaded CSV |
| `/forecast/batch` | POST | `forecast/batch/` | the same page with a batch summary, chart and row table |
| `/forecast/template.csv` | GET | n/a | sample file for the batch upload |
| `/export/<page>.csv`, `.pdf` | POST | n/a | download of the result on `/forecast`, `/predict`, `/timeline` (batch: CSV only) |
| `/predict` | GET, POST | `predict/` | `resistance_prediction.html`, with the resistance-genes panel |
| `/predict/sample` | GET | n/a | local runs only: `/predict` filled with `progress/formats/genome_response.sample.json`, to preview the genes panel |
| `/timeline/sample` | GET | n/a | local runs only: `/timeline` filled with `progress/formats/timeline_response.sample.json`, to preview the RL panel ("Simulation + RL policy (not trained on patient data)"), shown only when a response has `rl` |
| `/timeline` | GET, POST | `timeline/` | `mutation_timeline.html` |
| `/train` | GET, POST | `train/` | `train.html` |
| `/datasets` | GET | n/a | `datasets.html`, the five datasets explained |
| `/about` | GET | n/a | `about.html`, methodology, team, metrics |
| `/library` | GET | n/a | `library.html` - `amrpredict` docs |
| `/models` | GET | `models/` | `models.html`, every model, the split, charts (§8.1) |
| `/compare` | GET | `models/` | `compare.html`, deployed vs experimental models and their data (§8.1) |
| `/genes` | GET | `genes/` | `genes.html`, AMRFinderPlus resistance genes (§8.2) |
| `/api/genes/<genome_id>` | GET | `genes/<genome_id>/` | JSON, one genome's genes for the lookup |
| `/genes/matrix.csv`, `/genes/info.csv` | GET | `genes/matrix.csv`, `genes/info.csv` | CSV downloads of the gene matrix and its columns |
| `/reload` | POST | `reload/` | JSON, re-reads artifacts without a restart |
| `/api/health` | GET | `health/` | JSON passthrough |
| `/api/antibiotics` | GET | n/a | JSON, 48 names (hardcoded list) |
| `/api/organisms` | GET | n/a | JSON, 15 species |
| `/api/vocabulary` | GET | `vocabulary/` | JSON, what each model can tell apart; `lgbm.organisms` is the genus → species → taxon ID tree for `/forecast` |
| `/api/mic-values` | GET | `mic-values/` | JSON, MIC suggestions for an antibiotic and organism (`?antibiotic=&genus=&species=`), with the `level` they came from |
| `/api/genome/<genome_id>` | GET | `genome/<genome_id>/` | JSON for `/forecast`'s "Fill from Genome ID": the organism to fill, the genome's lab results (`?antibiotic=` picks one drug's), and whether each served model trained on it |

### How the pages are built

- **One base template.** `base.html` holds the nav, footer, toast container, theme bootstrap and the libraries (Bootstrap 5.3, Bootstrap Icons and Plotly 2.26 from `static/vendor/`, so the site works offline; only the Inter and JetBrains Mono fonts come from Google). Every page extends it and fills `{% block content %}` + `{% block scripts %}`.
- **CSS is layered, not monolithic:** `tokens` (colour/spacing variables) → `layout` → `components` → `utilities` → `charts` → `animations` → `dark`. Dark mode is a `data-theme="dark"` attribute on `<html>`, set before first paint by an inline script so there's no flash, and persisted in `localStorage`.
- **JS is one file per page** plus `main.js` (the global `window.AMR` helper: Plotly theme fragment, toasts) and `dropdowns.js`.
- **Dropdowns populate themselves.** Any `<select data-populate="antibiotics">` is filled by `dropdowns.js` from `/api/antibiotics`, cached in `sessionStorage` for the tab, with `data-selected="…"` restoring the choice after a POST. That's why the antibiotic list lives in exactly one place per source.
- **Organism lists on `/forecast` are linked.** Genus, species and taxon ID are dropdowns of what the forecaster was trained on: choosing a genus fills the species list with that genus's species only (from `backend/taxon_species.csv`, so "coli" is offered under both *Escherichia* and *Campylobacter*), and the taxon ID list with that species' IDs (the whole genus's when no species is chosen). The MIC field suggests the values recorded in BV-BRC for the drug and organism, at the most specific level with data (species, then genus, then all organisms), from `backend/api/mic_values.json`, built by `python scripts/build_mic_values.py`; any value can still be typed.
- **"Fill from Genome ID" on `/forecast`.** A BV-BRC Genome ID starts with its taxon ID (`562.1234` is taxon 562), so the helper fills genus, species and taxon ID from it (only values the model knows). It shows the genome's **laboratory** result for the chosen drug (never BV-BRC's computer-predicted labels; `backend/api/genome_lab_results.json.gz`, 37,573 genomes, built by `python scripts/build_genome_lab_results.py`), offers "Use this MIC" when it is a single value in mg/L, links the genome's genes on `/genes`, and says whether the forecaster trained on it (Hamza's `ml_models/training_genomes.py`, format [§7](library.md)): a training genome gets a caution, because its prediction looks better than a new genome's would. After a prediction it says whether the model agrees with the lab. **The Genome ID is never sent to the model**: it is the key of the genome-grouped split, so as an input it could only memorise known genomes.
- **Charts are server-data → inline JSON → Plotly.** The template writes `<script type="application/json" id="kmer-chart-data">{{ result.top_kmers | tojson }}</script>` and the page script parses it. No API call, no template-inlined JavaScript data.

### Downloads and batch upload

Each tool page has a **Download this result** bar under its result. The page posts back the result it rendered, and `frontend/exports.py` builds the file. The same code also runs in the backend as `POST /api/export/<page>.<fmt>` (`backend/api/exports.py`, 30 per minute per IP), which the React frontend in `web/` uses, since it has no server of its own:

| Format | Contents |
|---|---|
| CSV | One row per result (the timeline: one row per week, each labelled "Simulation, not a trained model"). Cells that would start a spreadsheet formula get a leading apostrophe |
| PDF | ReportLab: inputs, result, the model's name, run, AUC with its interval and threshold rule, the chart, the detail table, a timestamp, and "Research tool, not a clinical diagnostic" |
| PNG | The chart, redrawn on white by `static/js/export.js` |

The model details come from the metrics files on the server, never from the page, so a download cannot carry numbers the server did not produce. Only a real PNG is embedded in a PDF.

**Batch upload** (`/forecast`, "Upload CSV" tab): columns `antibiotic` (required), `genus`, `species`, `taxon_id`, `mic_value`, `mic_sign`; up to 10,000 rows and 2 MB. `POST /api/forecast/batch/` checks every row, predicts the valid ones in one call (the same probabilities as the single form) and returns one result row per input row, with `error` set on the rows it could not use. The page shows the R/S counts, a chart per antibiotic and the first 200 rows; the results CSV has all of them.

### Genome models on /models (Section 5)

Built from `genome_runs` in `model_report.json`, the list of Track B runs that `experiments/export_report.py` writes (format: [progress/formats/README.md [§6](data-and-training.md)](../progress/formats/README.md#6-genome-runs-for-models)). Only the runs of the newest cleaning version (now v6, 33 runs) with a lab AUC are shown; older versions are history. The section has its own intro saying the scores are on lab results only and on different data from Sections 1–4, a chart of lab AUC by run coloured by kind of split (grouped, lineage, unseen genus), and a table with the lab row count beside every score. The run `/predict` serves (`shipped.kmer.run_id`, now `G_kmer_deploy`) is starred and highlighted. Hidden when the report has no `genome_runs`.

### Resistance genes on /predict

`templates/_genes_panel.html` shows the `genes_found` list of the `/api/predict/` response (format: [progress/formats/README.md [§2](architecture.md)](../progress/formats/README.md#2-genome-prediction-response)) under the result, in its three states:

| `genes_found` | The page shows |
|---|---|
| absent | No panel; one line in Genome Statistics: "Not searched", because the model reads k-mer composition, not genes. This is what the served k-mer model returns today |
| `[]` | The panel says the genome was searched and no known resistance gene or mutation was found |
| a list | One chip per gene or mutation (type and drug class). Those with `relevant: true` (their class matches the requested drug's) come first and are highlighted, with one sentence on whether they support the call: a Susceptible call with a linked gene is flagged "Treat this call with care" |

The heading ("K-mer Genome Analysis" or "Genome Analysis") and the k-mer cards follow the model that answered, so a gene model that sends no k-mers shows cleanly. The CSV gets a `resistance_genes` column and the PDF a genes table. On a local run, `/predict/sample` shows the panel with the sample response under a "Sample response, not a real prediction" banner; with `PORT` set (Railway) it returns 404.

### 8.1 The report pages: `/models` and `/compare`

Both pages are listed under **Insights** in the navbar, the menu for pages that explain results, after Bio-Simulator: Model Report and Deployed vs Experimental under *Model results*, Datasets and Resistance Genes under *Data*. ML Models holds only the two predictors. They read one file,
`backend/trained_models/model_report.json`, which the Django endpoint
`GET /api/models/` serves with a live "is the model loaded" flag added. The file
is committed so the deployed backend can serve it without the data or the
experiment outputs. Rebuild it with the two scripts in [§5.4](data-and-training.md).

| Page | Sections |
|---|---|
| `/models` | Best model; how train and test are split (row counts, the four steps, random vs grouped split drawn per genome); deployed models re-tested on seen vs unseen genomes; all 22 runs with AUC and confidence intervals, ROC curves, learning curve, VME vs ME trade-off, results table; confusion matrix and best and worst antibiotics for the best run |
| `/compare` | Where each model's training data comes from; a side-by-side table of the two deployed models and the best experiment; training set size, reported vs unseen-genome AUC, genus mix heatmap and label mix; a table of all 24 models and their data |

Chart colours are CSS tokens (`--viz-1` to `--viz-5`, `--viz-other`) defined in
`tokens.css` and stepped for the dark surface in `dark.css`, checked for
colour-blind separation. Shared chart code lives in `static/js/report-charts.js`.

### 8.2 The resistance genes page: `/genes`

Also under **Insights**. It shows what NCBI AMRFinderPlus found in the complete
genome of every isolate (core AMR genes and point mutations only), from two
committed files that `experiments/genome/features/export_gene_report.py` builds:
`backend/trained_models/gene_report.json` (served by `GET /api/genes/`) and
`gene_hits.json` (one genome at a time, `GET /api/genes/<genome_id>/`).

| Section | What it shows |
|---|---|
| Headline | Genomes searched (with a banner while the run is incomplete), share with at least one gene, distinct genes and mutations |
| What was found | Top 20 genes and mutations, genes per genome, genomes with a gene for each drug class |
| The gene matrix | What the matrix is, its size, a readable corner of it (real genomes × the most common genes), and CSV downloads of the whole matrix and of what each column means. The backend builds the CSV from `gene_hits.json`; it matches `gene_matrix.parquet` cell for cell |
| Genes by species | Genus × gene heatmap and a table of every genus |
| Gene vs lab result | For a gene and an antibiotic its AMRFinderPlus subclass says it acts on, resistance with and without the gene. Laboratory results by default; BV-BRC's predicted labels behind a toggle, because they come from models that read the genome |
| Look up a genome | Every gene and mutation in one genome; `/genes#genome=<id>` opens with it looked up |

After AMRFinderPlus finishes, rebuild with
`python experiments/genome/features/export_gene_report.py`.
Tiles whose value is not a single number (for example "9 vs 37") carry the
`stat-mini-static` class so the count-up animation in `main.js` skips them.

---

### 8.3 The Resistance Explorer: `/explore/<view>`

Each view is its own page, listed in the navbar's **Insights** menu under Resistance Explorer: `/explore/heatmap`, `/explore/dominant`, `/explore/map`, `/explore/groups`, `/explore/drugs` and `/explore/chemistry`. The filters carry over between them in the URL, and `/explore` opens the heat map.

The instructor's dashboard (plan and decisions: [docs/INSTRUCTOR_REQUIREMENTS_PLAN.md](INSTRUCTOR_REQUIREMENTS_PLAN.md)). It shows laboratory-confirmed resistance in BV-BRC by organism, antibiotic group, country, infection type and drug chemistry. Resistance % is resistant ÷ (resistant + susceptible); intermediate results are left out unless the toggle counts them as resistant. Groups under 30 isolates (configurable) are faded and marked "low sample".

| Part | Where |
|---|---|
| Filters: organism grouped by Gram stain, antibiotic group (selects its drugs), antibiotic, chemical group, country (search), infection type and disease (each narrows the other), years, intermediate toggle, low-sample threshold. All kept in the URL | `web/src/pages/explore/FilterBar.tsx`, `filters.ts`, `web/src/components/MultiSelect.tsx` |
| Views: country heat map (rate or dominant resistance type, click a country to filter), map by antibiotic group, group-wise and drug-wise comparison with yearly trend, chemistry across chemical groups | `web/src/pages/explore/views.tsx`, `charts.ts` |
| Drug panel: nomenclature (generic and likely brand names, IUPAC name, ATC code, family, chemical group, AWaRe, PubChem CID) and chemistry (2D structure, formula, weight, mechanism, target, resistance mechanisms) | `web/src/pages/explore/DrugDetail.tsx` |
| Grouped antibiotic dropdown (family › subfamily) on `/forecast`, `/predict` and `/timeline` | `web/src/components/AntibioticOptions.tsx` |
| API: `GET /api/explore/meta/`, `summary/?by=&split=`, `countries/?mode=`, `drug/<name>/`, `structure/<cid>.png`; every filter is a query parameter | `backend/api/explorer.py`, `backend/api/views.py`, `backend/api/urls.py` |
| Tests | `backend/tests/test_explorer.py`, `backend/tests/test_reference.py`, `web/src/pages/Explore.test.tsx` |

**Data.** The page reads no database and never the cleaned table. `scripts/build_explorer_data.py` counts the 649,944 laboratory rows into `backend/trained_models/explorer/cube.csv.gz` (tested, resistant and intermediate per country, organism, antibiotic, infection type, disease and year; 0.2 MB). `scripts/fetch_pubchem.py` caches each drug's PubChem record and structure image in the same folder, so the site does not call PubChem. The world map's outline is served from `web/public/topojson/`, so the maps work offline.

**Lookup tables** ([backend/reference/](../backend/reference/README.md)), plain CSV that any spreadsheet can edit: `antibiotics.csv` (family, subfamily, chemical group, ATC, AWaRe, mechanism, target, resistance mechanism), `families.csv`, `chemical_groups.csv`, `organisms.csv` (Gram stain), `countries.csv` (ISO-3 codes for the maps), `infection_types.csv` (rules from the genome metadata's disease, host health, body site and isolation source), `diseases.csv`, `resistance_types.csv` (MRSA, VRE, CRE, ESBL proxy, CRAB, CRPA). To change a mapping: edit the CSV, run `python -m unittest discover -s backend/tests`, restart the backend. After a new cleaning or metadata download, rerun `scripts/build_explorer_data.py`.

**Limits, also stated on the page.** BV-BRC holds the isolates labs chose to sequence, not surveillance, so a country's percentage describes its submitted isolates. 62% of laboratory rows have an infection type and 20% a disease. ESBL is a proxy (third-generation cephalosporin resistance in Enterobacterales). Brand names are guesses from PubChem synonyms.
