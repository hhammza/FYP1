# Genome features: running the pipeline

How to download genomes, run AMRFinderPlus on them, watch progress, and rebuild the gene matrix. One-time setup (the `amrfinder` conda environment) and the reasons behind the pipeline are in [../README.md](../README.md).

Run every command from the project root (`FYP1/`) with the project's Python, `.venv/bin/python`.

## In plain words

**What we are doing.** Our models guess whether a bacterium will survive an antibiotic by looking at its DNA. To check whether those guesses are right, we need bacteria that were actually tested in a lab. The database has 22,475 of them, but we only had the DNA for 136. So we download the DNA of all of them, look for resistance genes in each one, and hand the result to Hamza.

**What you need.** A Mac with this project on it, about 100 GB of free disk space, and an internet connection. Nothing to pay for and no login.

Open the Terminal app and go into the project folder first. Every step below starts from there:

```bash
cd ~/Desktop/FYP/FYP1
```

**Step 1. Make the list of bacteria to download.** *(Already done on 2026-09-27. Skip it.)*

This reads our own data and writes down every bacterium that has a real lab result. It takes a few seconds and downloads nothing.

```bash
.venv/bin/python experiments/genome/features/select_lab_genomes.py
```

**Step 2. Download the DNA.** *(Started on 2026-09-27. Check it before starting it again.)*

First, check whether it is already running:

```bash
pgrep -fl download_genomes.py
```

If that prints a line, it is running. Go to step 3. If it prints nothing, start it:

```bash
nohup caffeinate -i .venv/bin/python -u experiments/genome/features/download_genomes.py \
  --genome-list experiments/genome/features/lab_genomes.csv --workers 12 \
  >> Data/genomes_full/download.log 2>&1 &
```

It keeps running if you close the Terminal, and it keeps the Mac awake. The whole download takes about a day. If it stops for any reason (you switch off the Mac, the internet drops), run the same command again: it carries on from where it stopped and never keeps a half-downloaded file.

**Step 3. Watch how far it has got.**

Open a second Terminal window, go into the project folder, and run:

```bash
bash experiments/genome/features/progress.sh
```

You see a bar that fills up, how many are done out of how many, whether it is running, and roughly how long is left. Press Ctrl+C to close the view. This only closes the view; the download keeps going.

**Step 4. Look for resistance genes in the DNA.**

This runs a tool from the US National Center for Biotechnology Information (AMRFinderPlus) on every bacterium downloaded so far. You can start it while step 2 is still going:

```bash
nohup caffeinate -i .venv/bin/python -u experiments/genome/features/run_amrfinder.py \
  --jobs 4 --threads 2 >> Data/amrfinder_output/run.log 2>&1 &
```

It only looks at what has already been downloaded. When the download has finished, run the same command once more to catch the rest. `progress.sh` shows this job too.

**Step 5. Build the final table.** *(Only when steps 2 and 4 are both finished.)*

This turns the results into one table (a row per bacterium, a column per gene) and updates the Resistance Genes page of the website:

```bash
.venv/bin/python experiments/genome/features/build_gene_matrix.py
.venv/bin/python experiments/genome/features/export_gene_report.py
```

Then tell Hamza it is ready, and share a zip on Google Drive as before.

**To pause.** If you need the internet or the Mac for something else:

```bash
pkill -f download_genomes.py
pkill -f run_amrfinder.py
```

Nothing is lost. Run the command from step 2 or step 4 again to continue.

**Rules of thumb.**

- Never start a second copy of the same step while one is running. Check with `pgrep` first.
- Do not delete anything in `Data/genomes_full/` or `Data/amrfinder_output/` while a job is running.
- Do not commit these folders to git. They are too big, and `.gitignore` already leaves them out.

The sections below have the details: what each script does, the numbers, and where the data comes from.

## Scripts

| Script | What it does |
| --- | --- |
| `select_lab_genomes.py` | Lists every genome with a laboratory AST result (22,475 in cleaning v5) in `lab_genomes.csv`, ordered round-robin across genera |
| `download_genomes.py` | Downloads complete assemblies from BV-BRC into `Data/genomes_full/` |
| `run_amrfinder.py` | Runs AMRFinderPlus on every downloaded genome into `Data/amrfinder_output/` |
| `progress.sh` | Live progress bars for the two long jobs |
| `build_gene_matrix.py` | Builds `gene_matrix.parquet` and `gene_info.csv` from the AMRFinderPlus output |
| `export_gene_report.py` | Rebuilds the data behind the `/genes` page |

## Lab-tested genomes: what we have and what is left

Only 136 of the original 2,587 genomes have laboratory AST results, so the genome models could barely be tested against real phenotypes (Hamza, week 2). The download of every lab-tested genome started on 2026-09-27. Numbers below are a snapshot from that day; `progress.sh` shows the live count.

**Finished 2026-09-28:** all 24,926 genomes (2,587 original + 22,339 new) downloaded with 0 failures and searched by AMRFinderPlus with 0 errors, including all 22,475 lab-tested genomes. The rebuilt gene matrix is 24,926 × 2,733 (1,234 genes, 1,499 point mutations); 92.1% of genomes carry at least one core AMR gene. Summary in `gene_summary.md`.

| What | Count | Size |
| --- | --- | --- |
| Genomes with lab results in the cleaned data (v5) | 22,475 (201,042 lab rows, 107 drugs, 49.5% resistant) | 91.7 GB |
| Already on disk at the snapshot | 291 | 1.2 GB |
| Still to download at the snapshot | 22,184 | 90.5 GB |
| Not found on BV-BRC | 0 | |
| Original genomes from `fasta_output/` (already downloaded) | 2,587 | 11 GB |

By genus (top 10 of the lab list):

| Genus | Lab-tested genomes | Already on disk (snapshot) |
| --- | --- | --- |
| *Klebsiella* | 6,121 | 7 |
| *Neisseria* | 5,823 | 6 |
| *Shigella* | 2,379 | 5 |
| *Salmonella* | 1,796 | 115 |
| *Acinetobacter* | 1,557 | 13 |
| *Pseudomonas* | 1,411 | 6 |
| *Campylobacter* | 860 | 6 |
| *Streptococcus* | 613 | 22 |
| *Enterobacter* | 450 | 6 |
| *Staphylococcus* | 313 | 6 |

About 76 GB of disk stays free after the full download (167 GB free at the snapshot).

### Where the data comes from

- **Which genomes:** our own data. `Data/amr_output/` (cleaned as v5 by `experiments/lib/data_prep.py`) marks each row as a laboratory result or a computational prediction. `select_lab_genomes.py` takes every genome with at least one laboratory result. Nothing is downloaded for this step.
- **The DNA:** the public BV-BRC API, the database the AMR data came from. Free, no login. `download_genomes.py` makes two calls:
  1. `https://www.bv-brc.org/api/genome/`: each genome's expected length and contig count, 200 genomes per request, saved in `Data/genomes_full/manifest.csv`
  2. `https://www.bv-brc.org/api/genome_sequence/`: the full assembly as FASTA, one genome per request, saved as `Data/genomes_full/<genome_id>.fna` and kept only when its length matches step 1 within 1%

## Picking up where it stopped

Both long jobs can be stopped at any time (Ctrl+C, `pkill`, a crash, a restart) and started again with the same command:

- `download_genomes.py` skips every genome whose `.fna` file is already there. A file is written under a temporary name and only kept when its length is within 1% of what BV-BRC reports, so a half-finished download is never mistaken for a finished one.
- `run_amrfinder.py` skips every genome that already has a `.tsv`.

Run only one copy of each job at a time. Check with `pgrep -fl download_genomes.py` and `pgrep -fl run_amrfinder.py`.

## 1. Choose the genomes

The default is every genome in `Data/fasta_output/` (2,587). For the lab-tested genomes, make the list first:

```bash
.venv/bin/python experiments/genome/features/select_lab_genomes.py
```

Because of the round-robin order, a download stopped part way still holds a balanced sample of genera instead of mostly *Klebsiella* and *Neisseria*.

## 2. Download

Test on a few genomes first:

```bash
.venv/bin/python experiments/genome/features/download_genomes.py \
  --genome-list experiments/genome/features/lab_genomes.csv --limit 5
```

Then the full run, in the background:

```bash
nohup caffeinate -i .venv/bin/python -u experiments/genome/features/download_genomes.py \
  --genome-list experiments/genome/features/lab_genomes.csv --workers 12 \
  >> Data/genomes_full/download.log 2>&1 &
```

- `nohup` keeps it running after the terminal or VS Code is closed.
- `caffeinate -i` stops the Mac from sleeping while it runs (macOS only).
- `-u` writes the log line by line, so progress shows up straight away.
- Leave out `--genome-list` to download the `fasta_output/` genomes instead.

It first asks BV-BRC for each genome's length (a few minutes), then downloads. The full lab list is about 90 GB and takes about a day.

## 3. AMRFinderPlus

```bash
nohup caffeinate -i .venv/bin/python -u experiments/genome/features/run_amrfinder.py \
  --jobs 4 --threads 2 >> Data/amrfinder_output/run.log 2>&1 &
```

It can start while the download is still going: it runs on the genomes downloaded so far, and a later re-run picks up the rest. Each genome takes 10 to 45 seconds.

## 4. Watch progress

In a second terminal:

```bash
bash experiments/genome/features/progress.sh
```

It refreshes every 5 seconds and shows, for the download and for AMRFinderPlus:

- a progress bar with done / total and a percentage
- whether the job is `running` or `stopped`
- speed and time left, measured since you opened the view
- disk used by `Data/genomes_full/`
- the number of failures and the last lines of each log
- cores in use by each job, and the `--jobs` / `--threads` AMRFinderPlus was started with

While it is open it also keeps the Mac awake, and restarts AMRFinderPlus when it has stopped and downloaded genomes are still waiting (at most once every 10 minutes). Restarts use 8 jobs x 1 thread; change that, or switch it off:

```bash
AMR_JOBS=10 bash experiments/genome/features/progress.sh      # restart with 10 jobs
bash experiments/genome/features/progress.sh --no-restart     # watch only
```

Ctrl+C closes the view only; the jobs keep running.

Without the live view:

```bash
tail -f Data/genomes_full/download.log           # download log, live
tail -f Data/amrfinder_output/run.log            # AMRFinderPlus log, live
ls Data/genomes_full | grep -c '\.fna$'          # genomes downloaded
ls Data/amrfinder_output | grep -c '\.tsv$'      # genomes searched
```

## 5. Stop, resume, retry

```bash
pkill -f download_genomes.py     # stop the download
pkill -f run_amrfinder.py        # stop AMRFinderPlus
```

To resume, run the command from step 2 or 3 again. Failed genomes are listed in `Data/genomes_full/failures.csv` (download) and in the `error` column of `Data/amrfinder_output/run_summary.csv` (AMRFinderPlus); a re-run retries them.

## 6. Rebuild the gene matrix and the /genes page

When both jobs have finished:

```bash
.venv/bin/python experiments/genome/features/build_gene_matrix.py
.venv/bin/python experiments/genome/features/export_gene_report.py
```

Then commit `gene_matrix.parquet`, `gene_info.csv`, `gene_summary.md` and the two JSON files in `backend/trained_models/`. The genomes and the AMRFinderPlus output stay out of git (`.gitignore`).

## Disk space

| Folder | Size |
| --- | --- |
| `Data/genomes_full/`, 2,587 original genomes | about 11 GB |
| `Data/genomes_full/`, plus the 22,475 lab-tested genomes | about 100 GB in total |
| `Data/amrfinder_output/` | about 5 MB per 1,000 genomes |

Check free space with `df -h ~`.
