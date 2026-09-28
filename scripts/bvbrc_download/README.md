# BV-BRC download scripts

The scripts that built `Data/amr_output/` and `Data/fasta_output/` in April 2026. They were kept outside the repo until 2026-09-28; they are here so the dataset can be rebuilt and the data audit (Paper A, `progress/RESEARCH_PLAN.md`) can say exactly how it was made.

| Script | What it does | Used for our data |
| --- | --- | --- |
| `download_amr_full.py` | **Use this one.** Every AMR record, resumable, lab rows first (see below) | Next: `Data/amr_full/` |
| `download_amr_csv.py` | Downloads the AMR phenotype table from the BV-BRC API, one CSV per taxon (`amr_taxon_<id>_<name>.csv`), resumable through `.progress.json` | Yes: `Data/amr_output/` |
| `download_fasta.py` | Downloads a FASTA for every Genome ID in those CSVs, one folder per taxon | Yes: `Data/fasta_output/` (the partial FASTAs, Dataset 2) |
| `Bv-brc_scrapping.py`, `Bv-brc_scrapping_test.py`, `old_fasta_scrapping.py` | Early versions, capped at 5,000 genomes | No, kept for the record |

Each script writes to a folder relative to where it is run, so run it from inside `Data/`.

## The April download is incomplete

`download_amr_csv.py` paged with a growing offset and stopped each taxon at 500,000 rows. Checked against the BV-BRC API on 2026-09-29:

| | BV-BRC | April download (`Data/amr_output/`) |
| --- | --- | --- |
| All AMR rows | 17,585,506 | 2,986,755 |
| Lab rows (`Laboratory Method`) | 1,285,111 | about a quarter of them |
| *E. coli* (taxon 562) | 7,222,070 (243,124 lab) | none: failed at 491,500 rows |
| *K. pneumoniae* (573) | 1,840,793 (85,291 lab) | 500,000: hit the cap |
| *S. enterica* (28901) | 960,890 (63,198 lab) | none: failed at 295,000 rows |
| *S. aureus* (1280) | 533,336 (45,876 lab) | none: failed at 155,000 rows |

597 taxa ended in an error; 586 of them never received a row. Their `.csv.tmp` files are archived outside the repo.

## Full download: `download_amr_full.py`

Downloads every AMR record, lab rows first, paging by record ID (no depth limit, no cap). Resumable after any stop, retries while there is no internet, and keeps the Mac awake. Output in `Data/amr_full/` (not in git): 500,000-row CSV parts with the April columns plus `Record ID`, `Date Inserted`, `Date Modified`, and a `manifest.json` with the counts and dates, which pins the export for the data audit.

```bash
mkdir -p Data/amr_full
nohup .venv/bin/python -u scripts/bvbrc_download/download_amr_full.py \
    >> Data/amr_full/download.log 2>&1 &
.venv/bin/python scripts/bvbrc_download/download_amr_full.py --status   # progress
tail -f Data/amr_full/download.log                                        # live log
pkill -f download_amr_full.py                                             # stop; run again to resume
```

The record IDs are split into 16 shards by their first character and downloaded 8 at a time (`--workers`), about 12,000 rows a second: lab rows in a few minutes, all 17.6 M rows in under an hour, about 6 GB. Only lab rows: add `--streams lab`. Live view: `--watch`.

The complete genomes (Dataset 3) come from `experiments/genome/features/download_genomes.py` instead, not from these scripts.
