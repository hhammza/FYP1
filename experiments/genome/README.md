# Genome features

Resistance genes and point mutations for every genome, found with NCBI AMRFinderPlus. They become the gene matrix (one row per `Genome ID`, one 0/1 column per gene or mutation) for the B6 and B7 experiments.

## Why the genomes are downloaded again

The FASTA files in `Data/fasta_output/` are truncated. An *E. coli* file holds about 0.8 MB of a 5 MB genome (1090929.3 has 25 of its 120 contigs), and 1000561.3 (*P. aeruginosa*) is 74 KB of 6.3 MB. Most *S. aureus* files are whole. A gene outside the saved part cannot be found, so AMRFinderPlus runs on complete assemblies downloaded from the BV-BRC API. The K-mer model was trained on the truncated files, which is worth a sentence in the report.

## Setup (once)

AMRFinderPlus has a native Apple Silicon build on bioconda. Keep it in its own conda environment, apart from the project's `.venv`:

```bash
conda create -n amrfinder -c conda-forge -c bioconda --strict-channel-priority --override-channels ncbi-amrfinderplus=4.2.7
conda activate amrfinder
amrfinder -u                 # downloads the database, about 3 minutes
amrfinder --list_organisms
conda deactivate
```

## Run

Both scripts use the project's Python (`.venv`), not the conda environment. They skip finished genomes, so they are safe to stop and re-run.

```bash
# 1. Complete assemblies from BV-BRC: about 3 hours with 12 workers
caffeinate -i python experiments/genome/features/download_genomes.py --workers 12

# 2. AMRFinderPlus on every downloaded genome: 10 to 45 seconds per genome
caffeinate -i python experiments/genome/features/run_amrfinder.py --jobs 4 --threads 2

# 3. Gene matrix from the AMRFinderPlus output: seconds (needs pyarrow)
python experiments/genome/features/build_gene_matrix.py             # every searched genome
python experiments/genome/features/build_gene_matrix.py --sample 20 # into sample/

# 4. Summary for the /genes web page: seconds
python experiments/genome/features/export_gene_report.py
```

Test on a few genomes first with `--limit 5` on either script.

| Output (gitignored) | What it holds |
| --- | --- |
| `Data/genomes_full/<genome_id>.fna` | complete assembly, about 12 GB in total |
| `Data/genomes_full/manifest.csv` | taxon, local and full length, contigs per genome |
| `Data/genomes_full/failures.csv` | downloads that failed or came back short |
| `Data/amrfinder_output/<genome_id>.tsv` | AMRFinderPlus hits for one genome |
| `Data/amrfinder_output/run_summary.csv` | organism used, hits, seconds, error, tool and database version |

| Output (committed) | What it holds |
| --- | --- |
| `experiments/genome/features/gene_matrix.parquet` | genome x gene 0/1 matrix, format in `progress/formats/README.md` section 3 |
| `experiments/genome/features/gene_info.csv` | symbol, type, class, subclass and genome count for each column |
| `experiments/genome/features/sample/` | the same two files for a fixed 20-genome sample |
| `backend/trained_models/gene_report.json`, `gene_hits.json` | run summary and per-genome genes for the `/genes` page |

A download is kept only when its length is within 1% of the length BV-BRC reports.

## Organism choice

`--organism` turns on point-mutation detection (for example `gyrA_S83L`). Each genome's NCBI species comes from `backend/taxon_species.csv`:

| Species in the data | Genomes | `--organism` |
| --- | --- | --- |
| *Escherichia coli*, *Escherichia* sp., *Shigella flexneri* | 991 | `Escherichia` |
| *Salmonella enterica* | 913 | `Salmonella` |
| *Staphylococcus aureus* | 227 | `Staphylococcus_aureus` |
| *Enterococcus faecium* | 201 | `Enterococcus_faecium` |
| *Streptococcus pneumoniae* | 53 | `Streptococcus_pneumoniae` |
| *Klebsiella pneumoniae* | 52 | `Klebsiella_pneumoniae` |
| *Acinetobacter baumannii* | 43 | `Acinetobacter_baumannii` |
| *Pseudomonas aeruginosa* | 37 | `Pseudomonas_aeruginosa` |
| *Campylobacter jejuni* | 8 | `Campylobacter` |
| *Enterobacter cloacae* | 5 | `Enterobacter_cloacae` |
| *Corynebacterium diphtheriae* | 2 | `Corynebacterium_diphtheriae` |
| *Clostridioides difficile* | 1 | `Clostridioides_difficile` |
| *Klebsiella michiganensis* (26), *Mycobacterium tuberculosis* (22), *Acinetobacter nosocomialis* (4), *Enterococcus hirae* (1), *Acinetobacter schindleri* (1) | 54 | none: genes only, no point mutations |

*M. tuberculosis* resistance is mostly point mutations, which AMRFinderPlus does not report for it, so expect few hits there.

Versions used: AMRFinderPlus 4.2.7, database 2026-08-07.1.
