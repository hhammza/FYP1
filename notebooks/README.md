# Notebooks

## The current models (start here)

Run in order, from this folder, with the project's environment. Each one was executed on 2026-10-13 and saved with its outputs, so it can be read without running it.

| Notebook | What it does | Checks against the published run | Run time |
|---|---|---|---|
| [01_forecaster_model.ipynb](01_forecaster_model.ipynb) | Trains the forecaster served on `/forecast` (`D3_forecaster_deploy_v7`) step by step: data, split by genome, out-of-fold resistance rates, LightGBM with a monotone MIC effect, isotonic calibration, threshold for at most 10% missed resistant isolates, evaluation, calibration plot, one prediction through the website's code | AUC 0.7737, the four confusion counts and the threshold: identical | about 25 min |
| [02_genome_models.ipynb](02_genome_models.ipynb) | Trains the two genome models served on `/predict`: the gene model on AMRFinderPlus genes (`G_genes_deploy`) and the k-mer model (`G_kmer_deploy`); a significance test between them; how the website builds the features from an uploaded genome (species from its 6-mer profile, gene features) | Lab AUC 0.9772 and 0.9345: identical; the website's code gives the training run's probability | about 8 min |
| [03_evaluation.ipynb](03_evaluation.ipynb) | The checks behind the reported numbers, from the saved runs: seen vs never-seen genomes (the July 0.93 vs 0.64), seeds, significance tests, lineage split, temporal test, calibration | reads `experiments/results/` | about 10 s |

The notebooks call the project's own code (`experiments/run.py`, `experiments/lib/`, `experiments/genome/`, `backend/ml_models/`) and print each library function's source where it is first used, so the steps can be read in place. They write nothing to `experiments/results/`.

To run them: from the project root, `.venv\Scripts\python.exe -m pip install -r experiments/requirements.txt jupyter`, then open them in Jupyter or VS Code. They need the cleaned data (`experiments/cache/clean_v7_amr_full_norm.pkl`), the k-mer cache (`experiments/cache/kmer6_counts.npz`) and the gene matrix (in git); notebook 03 also needs `Data/genome_meta/genome_meta.csv`. The first two files are on the team's Google Drive (`docs/DATA_LINKS.md`).

## The original notebooks (July 2026, kept as history)

| Notebook | What it was |
|---|---|
| [LightGBM_Model_Improved.ipynb](LightGBM_Model_Improved.ipynb) | The first forecaster (Colab): a random row split, which put the same genomes in training and test. Its AUC 0.93 fell to 0.64 on genomes it had never seen; notebook 03, section 1 |
| [resistance_prediction_model.ipynb](resistance_prediction_model.ipynb) | A deep-learning k-mer model, planned but never run (no outputs) |
| [bacterial_mutation_timeline.ipynb](bacterial_mutation_timeline.ipynb) | The timeline research, including a CNN-LSTM that was explored and not deployed; the timeline is a labelled biological simulation |

## Data pipeline notebooks (Ali, Colab)

| Notebook | What it does |
|---|---|
| [download_genomes_to_drive.ipynb](download_genomes_to_drive.ipynb) | Downloads the lab-tested genomes from BV-BRC straight to Google Drive |
| [build_kmers_on_drive.ipynb](build_kmers_on_drive.ipynb) | Builds the 6-mer counts of every genome |
| [amrfinder_on_drive.ipynb](amrfinder_on_drive.ipynb) | Runs NCBI AMRFinderPlus on the genomes |
