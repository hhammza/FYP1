# Plan: instructor requirements for the AMR dashboard

*Written 2026-10-28, before any code. It covers the 12 instructor requirements and the technical requirements, from an inspection of the current code and data. Nothing here is built yet.*

## 1. What the codebase has today

| Area | Current state | What it means for this work |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite in `web/`, Bootstrap 5, Plotly (`plotly.js-dist-min` 2.26, lazy-loaded through `web/src/components/Plot.tsx`), react-router 7, 12 pages | New views reuse `Plot.tsx`, the Bootstrap styles in `web/src/styles/` and the theme in `lib/theme.ts`. Plotly already supports choropleth maps |
| Backend | Django REST API (`backend/api/views.py`, 18 routes), models loaded from files in `backend/trained_models/` | New endpoints follow the same pattern |
| **Database** | **None:** the settings have `DATABASES = {}` in `backend/backend/settings.py`; the Docker image ships only `backend/` | The "tables" in the brief have no database to live in. See decision D1 |
| Antibiotics | 126 drugs after cleaning; one flat class each in `backend/amr_constants.py` (`DRUG_CLASS_MAP`: 23 classes, `beta_lactam` alone covers 50 drugs) | Family, subfamily and chemical group are new data |
| Organisms | 40 genera, 247 species-level taxa; genus → species tree in `backend/api/organisms.py` | Gram stain is new data, at genus level |
| Resistance data | Cleaned table v7: 7,847,110 rows; **649,944 laboratory rows** on 87,325 genomes (`experiments/cache/clean_v7_amr_full_norm.pkl`, not deployed) | Too large to query per request; it must be pre-aggregated (section 3) |
| Country | `isolation_country` in `Data/genome_meta/genome_meta.csv` | 596,013 of the lab rows (91.7%) have a country: 165 countries, 122 with at least 30 lab rows |
| Infection site | Free-text `isolation_source` ("urine" 29,314 lab rows, "blood" 21,371, "wound" 9,296, "sputum" 7,466, "csf" 1,380, "feces" ...) | 239,776 lab rows (36.9%) have one; mapped to infection types by keyword |
| Disease | Not downloaded yet. BV-BRC's genome records also hold `disease`, `host_health` (e.g. "cystic fibrosis") and `body_sample_site` (checked on the live API) | Add these 3 fields to `scripts/bvbrc_download/download_genome_meta.py` and re-run it (about 2 minutes); coverage measured then |
| Year | 571,202 lab rows have a collection year | Trends in the drug-wise view (point 8) |
| Intermediate results | Cleaning folds Intermediate into Resistant | To exclude them by default (technical requirement), the aggregate keeps Intermediate as its own count |

## 2. Decisions needed from you before coding

| # | Decision | Options | Recommendation |
|---|---|---|---|
| **D1** | Where the lookup tables live (the brief says "tables"; there is no database) | (a) **CSV files** in a new `backend/reference/` folder, loaded at startup, edited in any spreadsheet; (b) add **SQLite** and Django models with migrations | **(a) CSV.** No schema change, nothing destructive, reviewable in git, editable without code. (b) changes the architecture and the deploy, so it needs your go-ahead |
| **D2** | Which rows count as "tested" | Lab rows only; or lab plus BV-BRC's computational predictions | **Lab rows only.** Computational labels are predictions, not tests. A toggle can add them later |
| **D3** | Gram stain for genera that have none | *Mycobacterium* (acid-fast), and any genus not Gram-stainable | A third group, **"Other (acid-fast / not Gram-classified)"**, rather than forcing it into one of two |
| **D4** | Resistance types for the heat map (point 10) | Standard definitions from organism + drug | MRSA = *S. aureus* resistant to oxacillin, methicillin or cefoxitin; VRE = *Enterococcus* resistant to vancomycin; CRE = Enterobacterales resistant to any carbapenem; CRAB = *A. baumannii* resistant to a carbapenem; CRPA = *P. aeruginosa* resistant to a carbapenem; **ESBL (proxy)** = Enterobacterales resistant to a 3rd-generation cephalosporin. ESBL is a mechanism the data does not record directly, so it is labelled "proxy" |
| **D5** | PubChem calls | At request time on the server; or once, by a build script, cached in a JSON file | **Build script + cache.** No network dependency in the deployed app, and PubChem's rate limits are respected. A "refresh" re-runs the script |
| **D6** | Team ownership | The frontend and `views.py` are Suleman's files | Agree with Suleman before starting; new code goes into new files where possible, and the shared files get a few lines each (logged in his Handovers) |

## 3. Architecture

```
Data/ + cache (not deployed)                     backend/ (deployed)                     web/ (deployed)
───────────────────────────                      ───────────────────                     ───────────────
clean_v7 table (lab rows) ─┐                     reference/*.csv  (editable lookups)     /explore page
genome_meta.csv (country, ─┼─ build script ──►   trained_models/explorer/                  filters in the URL
  source, year, disease)   │                       cube.parquet   (counts)                 map, heat map, bars,
reference/*.csv ───────────┘                       drugs.json     (PubChem cache)          drug and chemistry panels
                                                   structures/*.png
                                                 api/explorer.py ──── /api/explore/* ──►
```

**The aggregate ("cube").** A new script, `scripts/build_explorer_data.py`, joins the lab rows to the genome metadata and the lookup tables, then counts per **country × species × antibiotic × infection type × disease × year**: rows tested, resistant, intermediate. The script needs the raw phenotype to keep Intermediate separate, so it reads `Data/amr_full/` through the same cleaning code with one extra column. The cube is small (estimated well under 20 MB as parquet), ships in `backend/trained_models/explorer/`, and answers every view by filtering and summing in pandas, in milliseconds.

**Resistance %** = resistant ÷ (resistant + susceptible) for the active filters; with "include intermediate" on, intermediate counts in both.

## 4. Lookup tables (D1: CSV, editable, seeded)

All in `backend/reference/`, loaded and validated at startup; a test fails if a drug, genus or source in the data has no row.

| File | Columns | Seeded from |
|---|---|---|
| `antibiotics.csv` | `antibiotic` (canonical name, as in the data), `family`, `subfamily` (e.g. Cephalosporins 3rd gen), `chemical_group` (structural class), `atc_code`, `aware` (Access / Watch / Reserve / Not classified), `mechanism`, `target`, `resistance_mechanism`, `pubchem_cid` | WHO ATC/DDD index (family and subfamily from ATC levels J01C, J01D...), WHO AWaRe 2023 list, standard pharmacology references; one row per drug, 126 rows. Veterinary-only drugs (ceftiofur, florfenicol, tylosin...) get AWaRe "Not classified" |
| `families.csv` | `family`, `subfamily`, `display_order` | The hierarchy in the brief (Beta-lactams > Penicillins, Cephalosporins 1st to 5th gen, Carbapenems, Monobactams; Aminoglycosides; Fluoroquinolones; ...; Nitrofurans, Fosfomycin, Others) |
| `chemical_groups.csv` | `chemical_group`, `core_structure`, `mechanism`, `resistance_mechanisms` | Curated: beta-lactam ring, aminoglycoside/aminocyclitol, quinolone core, macrolide lactone ring, glycopeptide, tetracycline four-ring, polypeptide, oxazolidinone, sulfonamide, and so on |
| `organisms.csv` | `genus`, `gram_stain` (positive / negative / other) | Standard microbiology, 40 genera |
| `infection_types.csv` | `pattern` (keyword or exact source), `infection_type` (UTI, bloodstream, pneumonia / respiratory, skin and wound, meningitis, GI, other clinical, non-clinical) | The most frequent `isolation_source` values (urine → UTI, blood → bloodstream, sputum / respiratory / nasopharynx → respiratory, wound / pus / tissue → skin and wound, csf → meningitis, feces / stool / diarrhea → GI; food and environment → non-clinical) |
| `diseases.csv` | `disease` (normalised), `infection_type` | Values found in BV-BRC's `disease` and `host_health` fields after the re-download, mapped by hand |
| `resistance_types.csv` | `resistance_type`, `organism_rule`, `drugs` | D4 |

The chemistry and nomenclature fields that come from PubChem (IUPAC name, formula, weight, SMILES, synonyms for brand names) go to `trained_models/explorer/drugs.json`, written by `scripts/fetch_pubchem.py` (PUG REST by name, then by CID; missing fields stay null and the UI shows "not available"). The 2D structure images are PubChem's PNG for each CID, saved once to `trained_models/explorer/structures/`.

## 5. The 12 requirements: how each is built

| # | Requirement | How | Where |
|---|---|---|---|
| 1 | Organism, Gram+ / Gram- | Organism dropdown with group headers Gram-positive, Gram-negative, Other (D3), genus → species; "all Gram-positive" and "all Gram-negative" as selectable entries | `organisms.csv`; `web/src/pages/explore/filters/OrganismFilter.tsx` |
| 2 | Antibiotic group | Group filter; choosing a group selects all its drugs in the antibiotic filter | `antibiotics.csv`, `families.csv`; `filters/AntibioticFilter.tsx` |
| 3 | Country | Multi-select with search (Bootstrap dropdown with a search box, no new library) | `filters/CountryFilter.tsx` |
| 4 | Disease / infection type | Two linked filters: an infection type narrows the disease list, and a disease selects its infection type | `infection_types.csv`, `diseases.csv`; `filters/InfectionFilter.tsx` |
| 5 | Chemical group | Separate filter on `chemical_group`, independent of family | `filters/ChemicalGroupFilter.tsx` |
| 6 | Map by antibiotic group | Plotly choropleth: pick a group, see resistance % per country | `views/GroupMap.tsx` |
| 7 | Group-wise comparison | Horizontal bars of resistance % per antibiotic group, sorted descending; split by Gram, organism, country or infection type (grouped bars, small multiples past 3 series) | `views/GroupComparison.tsx` |
| 8 | Drug-wise comparison | Pick a group, compare its drugs: resistance %, isolates tested (n), and yearly trend lines where years exist | `views/DrugComparison.tsx` |
| 9 | Chemistry (important) | Chemistry panel per drug: chemical group and core structure, 2D structure image, formula and weight, mechanism and target, resistance mechanism tied to the chemistry; plus resistance % compared across chemical groups | `views/ChemistryView.tsx`, `chemical_groups.csv`, `drugs.json` |
| 10 | Country heat map | Choropleth coloured by resistance % in bins 0-20 ... 80-100; toggle "dominant resistance type" (D4); tooltip with country, %, n, top 3 resistance types, top organism; no data grey; n < 30 (configurable) faded with a "low sample" note; clicking a country sets the Country filter | `views/CountryHeatMap.tsx` |
| 11 | Family in the antibiotic dropdown | A grouped dropdown (family > subfamily > drug) built from `antibiotics.csv` through the API, never hard-coded in the UI; also used on `/forecast` and `/timeline` | `web/src/components/AntibioticSelect.tsx`; small edits to the forecast and timeline forms |
| 12 | Nomenclature | Drug detail panel (Bootstrap offcanvas), opened from any dropdown or chart click: generic name, brand names, IUPAC name, ATC code, family / subfamily / chemical group, AWaRe category, PubChem CID with a link | `views/DrugDetail.tsx`, `drugs.json` |

**Every filter applies to every view:** the views read one filter object; the API takes the same filter set on every endpoint.

**Filters in the URL:** one `useExploreFilters()` hook built on react-router's `useSearchParams`, so any view can be shared as a link (`/explore?gram=negative&group=carbapenems&country=PK,IN&view=heatmap`).

## 6. API

| Endpoint | Returns |
|---|---|
| `GET /api/explore/meta/` | Every filter's options with counts: organisms by Gram, the antibiotic hierarchy, chemical groups, countries, infection types and diseases, resistance types, year range |
| `GET /api/explore/summary/?<filters>&by=<dimension>` | Resistant / tested / % per value of `by` (country, family, subfamily, antibiotic, chemical group, Gram, genus, infection type, year, resistance type), with a low-sample flag |
| `GET /api/explore/countries/?<filters>&mode=rate\|dominant` | The heat map's data: per country %, n, top 3 resistance types, top organism |
| `GET /api/drugs/<name>/` | Nomenclature and chemistry for one drug (lookup row + PubChem cache) |

Filter parameters: `gram`, `genus`, `species`, `family`, `subfamily`, `antibiotic`, `chemical_group`, `country`, `infection_type`, `disease`, `year_from`, `year_to`, `include_intermediate`, `min_n` (default 30).

## 7. Files

**New**

| File | What |
|---|---|
| `backend/reference/*.csv` (7 files) | The lookup tables (section 4) |
| `backend/api/reference.py` | Loads and validates the lookup tables |
| `backend/api/explorer.py` | Loads the cube and answers the explore endpoints |
| `backend/tests/test_explorer.py`, `test_reference.py` | Resistance % on hand-made data, filters, intermediate toggle, low-sample flag, every drug and genus has a lookup row |
| `scripts/build_explorer_data.py` | Builds the cube |
| `scripts/fetch_pubchem.py` | Fills `drugs.json` and the structure images |
| `backend/trained_models/explorer/` | The cube, `drugs.json`, structure images (allowed in `.gitignore` like the other served files) |
| `web/src/pages/Explore.tsx` and `web/src/pages/explore/` | The page, filters, views, `useExploreFilters` |
| `web/src/components/AntibioticSelect.tsx` | The grouped drug dropdown |
| Tests beside each in `web/src/` | Vitest, like the existing pages |

**Changed (a few lines each)**

| File | Change | Owner |
|---|---|---|
| `scripts/bvbrc_download/download_genome_meta.py` | Add `disease`, `host_health`, `body_sample_site` | Ali |
| `backend/api/urls.py`, `backend/api/views.py` | Register the 4 endpoints (thin views calling `explorer.py`) | Suleman: agree first |
| `web/src/App.tsx`, `web/src/components/Navbar.tsx` | Route and menu entry for `/explore` | Suleman: agree first |
| `web/src/pages/forecast/ForecastForm.tsx`, the timeline form | Use `AntibioticSelect` | Suleman |
| `.gitignore` | Allow `backend/trained_models/explorer/` | |
| `README.md` | New section: the lookup tables, data sources, how to edit a mapping, how to rebuild the cube and the PubChem cache | |

## 8. Order of work

| Step | Work | Size |
|---|---|---|
| 1 | Re-download genome metadata with the 3 new fields; measure disease coverage | 1 hour |
| 2 | Seed the 7 lookup tables; review them with the team (126 drugs need family, subfamily, chemical group, ATC, AWaRe) | 1 day, the largest manual part |
| 3 | `fetch_pubchem.py`; check every drug resolves | Half a day |
| 4 | `build_explorer_data.py` and the cube; check totals against the cleaned table | Half a day |
| 5 | Backend endpoints and tests | 1 day |
| 6 | Frontend: filters and URL state, then views 6 to 10, then the drug panel and chemistry, then the grouped dropdown | 3 days |
| 7 | README, end-to-end check, the 12-point checklist with file references | Half a day |

About a week of work in all; steps 2 and 6 are the bulk.

## 9. Limitations to state on the page and in the report

- **Infection type is known for about 37% of lab rows**, inferred from free-text sources; disease coverage is unknown until step 1. Views filtered by infection type rest on fewer isolates, and the page shows n everywhere.
- **The data is not surveillance.** BV-BRC holds what labs chose to sequence and submit; country percentages describe the submitted isolates, not a country's population. The page says so beside the map, and small samples are faded.
- **ESBL is a proxy** (3rd-generation cephalosporin resistance), not a measured mechanism.
- **AWaRe covers human medicine;** veterinary drugs in the data are "Not classified".
- **Chemistry is reference information** (PubChem and curated tables), not something the models learn from.
