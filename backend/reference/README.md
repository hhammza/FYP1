# Reference tables

Lookup tables for the dashboard views in `docs/INSTRUCTOR_REQUIREMENTS_PLAN.md`. They are plain CSV, so any spreadsheet program can edit them; the backend reads them at start-up, and `backend/tests/test_reference.py` fails if a drug, genus or column is missing.

| File | One row per | Columns |
|---|---|---|
| `antibiotics.csv` | antibiotic name in the cleaned data (126) | `family`, `subfamily`, `chemical_group`, `atc_code`, `aware` (Access, Watch, Reserve, Not classified), `mechanism`, `target`, `resistance_mechanism`, `alias_of` (a spelling variant the cleaning missed), `use` (Human, Veterinary, TB, Laboratory), `review` (a note to check) |
| `families.csv` | family and subfamily | `display_order` for the grouped dropdown |
| `chemical_groups.csv` | structural chemical group (34) | `core_structure`, `mechanism`, `resistance_mechanisms`, `drugs` |
| `organisms.csv` | genus in the cleaned data (40) | `gram_stain` (positive, negative, other), `order_group` (Enterobacterales for the CRE and ESBL rules), `note` |
| `infection_types.csv` | matching rule | `priority` (lower wins), `field` of the genome metadata, `pattern` (regular expression, lower case), `infection_type` |
| `diseases.csv` | disease value on at least 20 lab rows | `disease_raw` (as in BV-BRC), `disease` (normalised), `infection_type`, `lab_rows` |
| `resistance_types.csv` | resistance type (MRSA, VRE, CRE, ESBL proxy, CRAB, CRPA, ...) | `genera` (or `@Enterobacterales`), `species`, `antibiotics` (resistant to any) |

## Sources

- Family, subfamily and ATC codes: WHO ATC classification (J01, J04; veterinary codes start with Q).
- AWaRe: WHO AWaRe classification of antibiotics (2023). Antituberculars, veterinary and topical drugs are not classified. Rows marked in `review` need a second look.
- Mechanism, target and resistance mechanism: standard pharmacology and the gene families AMRFinderPlus reports.
- Gram stain: standard microbiology; *Mycobacterium* is acid-fast and kept apart as `other`.
- Infection types: the genome metadata fields `disease`, `host_health`, `body_sample_site` and `isolation_source` from BV-BRC (`scripts/bvbrc_download/download_genome_meta.py`). With these rules, 62.4% of laboratory rows get an infection type.

## Editing a mapping

Change the row in the CSV, run `python -m unittest backend.tests.test_reference` (from the project root, or `discover -s backend/tests`), and restart the backend. To add a drug that a new cleaning version introduces, add a row to `antibiotics.csv`; the test lists any drug in the data without one.
