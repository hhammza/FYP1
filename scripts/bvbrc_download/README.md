# BV-BRC download scripts

The scripts that built `Data/amr_output/` and `Data/fasta_output/` in April 2026. They were kept outside the repo until 2026-09-28; they are here so the dataset can be rebuilt and the data audit (Paper A, `progress/RESEARCH_PLAN.md`) can say exactly how it was made.

| Script | What it does | Used for our data |
| --- | --- | --- |
| `download_amr_csv.py` | Downloads the AMR phenotype table from the BV-BRC API, one CSV per taxon (`amr_taxon_<id>_<name>.csv`), resumable through `.progress.json` | Yes: `Data/amr_output/` |
| `download_fasta.py` | Downloads a FASTA for every Genome ID in those CSVs, one folder per taxon | Yes: `Data/fasta_output/` (the partial FASTAs, Dataset 2) |
| `Bv-brc_scrapping.py`, `Bv-brc_scrapping_test.py`, `old_fasta_scrapping.py` | Early versions, capped at 5,000 genomes | No, kept for the record |

Each script writes to a folder relative to where it is run, so run it from inside `Data/`.

Known issue: 597 taxa were never finished in the April run (their `.csv.tmp` files are archived outside the repo). Check with the BV-BRC API whether they hold AMR rows before quoting totals.

The complete genomes (Dataset 3) come from `experiments/genome/features/download_genomes.py` instead, not from these scripts.
