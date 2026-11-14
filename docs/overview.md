# Overview

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## Update notes

*A walkthrough of how the whole system fits together, written from the code as it stands on 2026-09-24 (commit `52ae361`).*

> **Updated 2026-09-24.** The training data is now in `data/`, and a model
> experiment harness lives in [`experiments/`](../experiments/) ([§5.4](data-and-training.md)). The headline
> accuracy figure has been re-measured (see [§10](results.md)).
> Document history: [CHANGES.md](../CHANGES.md).
>
> **Updated 2026-09-25.** The deployed models have been re-tested on genomes they
> never trained on ([§10](results.md)), and the web app has two new pages, `/models` and
> `/compare`, that show every model, how the data is split, and what each model
> trained on ([§8.1](frontend.md)).
>
> **Updated 2026-09-26.** The backend has been hardened ([§11.4](known-issues.md)): no default
> secrets, a password on Train and Reload, upload and rate limits, and no
> database. Local runs need `DEBUG=True`, which `start.sh` and `start.bat` set ([§9](running-and-deployment.md)).
>
> **Updated 2026-09-27.** `/forecast`, `/predict` and `/timeline` download their
> result as CSV, a PDF report or a PNG chart, and `/forecast` takes a CSV of up
> to 10,000 isolates ([§8](frontend.md), "Downloads and batch upload").
>
> **Updated 2026-09-28.** `/predict` has a resistance-genes panel, ready for the
> genome model's `genes_found`; the k-mer model served today does not search for
> genes, and the page says so ([§8](frontend.md), "Resistance genes on /predict").

This is a companion to `docs/PROJECT_DOCUMENTATION.md`, not a replacement. That file is the long reference (datasets, hyperparameters, CSS classes). This one covers what the system is, what its parts are, how a click becomes a prediction, and what is true about it today. Every claim was checked against the code or reproduced by running it. Where the two documents disagree, sections 10 and 11 say why.

## 0. The 60-second version

You built a full-stack antimicrobial-resistance (AMR) prediction system with **four deliverables**:

| # | Deliverable | Where | What it is |
|---|---|---|---|
| 1 | **Django REST API** | `backend/` | 14 endpoints, loads 3 prediction engines into memory at startup |
| 2 | **Flask web app** | `frontend/` | 22 routes, 11 pages, calls the Django API over HTTP |
| 2b | **React + TypeScript web app** | `web/` | The same 11 pages as the Flask app, calling the Django API straight from the browser; the frontend to deploy, with Flask kept as the fallback ([web/README.md](../web/README.md)) |
| 3 | **`amrpredict` Python package** | `amrpredict-lib/` | The same three engines, cleaned up, pip-installable, with a CLI and tests |
| 4 | **Research notebooks** | `*.ipynb` | Where the models were originally designed and trained (Colab) |

And **three prediction engines**, of which only two are machine learning:

| Engine | Type | Input | Output | Trained? |
|---|---|---|---|---|
| LightGBM forecaster | Gradient-boosted trees | Antibiotic + taxonomy + MIC metadata | Resistant / Susceptible + probability | ✅ `D3_forecaster_deploy_v7`, cleaning v7, calibrated; AUC 0.774 on unseen genomes (lab rows 0.908) |
| Genome models | LightGBM on AMRFinderPlus resistance genes (where AMRFinderPlus runs) or on 4-mers of the complete genome | Genome FASTA + antibiotic | Resistant / Susceptible + probability (+ the genes found) | ✅ gene model `G_genes_deploy`, lab AUC 0.977 on unseen genomes, served by the Docker image (checked by CI); k-mer model `G_kmer_deploy`, lab AUC 0.935, where AMRFinderPlus is not installed. Replaced a RandomForest on partial genomes (0.695) |
| Mutation timeline | Logistic-growth simulation | Genome FASTA + antibiotic | Week-by-week resistance curve | ❌ not a model, no AUC, by design |
| Timeline ML model | LightGBM regression on yearly resistance series | Organism (given, or identified from the genome) + antibiotic | Observed yearly % resistant and a 5-year forecast with an 80% band | ✅ `TL_timeline_ml` (2026-10-22): trained on 467 series from 553,223 dated lab results; error 13.98 pp on 2017–2022, beating last value, trend and mean; shown beside the simulation |

The honesty about engine 3, labelling it a simulation everywhere in the UI rather than dressing it up as deep learning, is one of the stronger points of the project, and worth defending in a viva rather than hiding.

## 1. What the project does

**The problem.** Antimicrobial resistance means an antibiotic no longer kills the bacteria it used to. Clinically, you find out by culturing the isolate and measuring its MIC (minimum inhibitory concentration), slow, 24 to 72 hours. The premise here is: given data you already have (species, taxonomy, a partial MIC reading, or the genome sequence itself), predict the resistance call faster.

**The task.** Binary classification, **Resistant (1) vs Susceptible (0)**. `Intermediate` and `Nonsusceptible` phenotypes are folded into Resistant during cleaning (`backend/train_models.py:117-119`), a conservative choice: it is safer to over-call resistance than to miss it.

**The three questions the app answers**, one per page:

1. *"I have lab metadata for this isolate, will it resist drug X?"* → `/forecast` → LightGBM
2. *"I have the genome assembly, will it resist drug X?"* → `/predict` → k-mer LightGBM on the complete genome
3. *"If I treat with drug X, how fast does resistance take over the population?"* → `/timeline` → simulation
