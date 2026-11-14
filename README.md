# AMR Intelligence Platform

[![CI](https://github.com/hhammza/FYP1/actions/workflows/ci.yml/badge.svg)](https://github.com/hhammza/FYP1/actions/workflows/ci.yml)

Predicts whether a bacterium resists an antibiotic, from laboratory data or from its genome, shows how resistance could grow under treatment, and maps laboratory resistance across the world. A Final Year Project at COMSATS University Islamabad, Lahore Campus (2026 to 2027).

For the detail behind any part of this page, see the [project documentation](docs/README.md).

## What it does

| Question | Engine | How |
|---|---|---|
| Given the drug, the organism and an MIC reading, will the isolate resist? | **Forecaster** | LightGBM on 14 features, calibrated, threshold set for at most 10% missed resistance |
| Given a genome, will it resist? | **Genome models** | LightGBM on the resistance genes NCBI AMRFinderPlus finds, or on 4-mer frequencies where AMRFinderPlus is not installed |
| If a patient keeps receiving a drug, how fast could resistance take over, and which drug next? | **Timeline** | A logistic simulation checked against 15 published curves, a PPO agent that picks a drug each week, and a yearly forecast from dated lab results |
| Where is resistance highest, for which bacteria, drugs and infections? | **Resistance Explorer** | Maps and comparisons of 649,944 laboratory results by country, organism, drug group, infection type and chemistry |

## Results

Every model is tested on genomes it never saw in training, and genome results are quoted on laboratory-confirmed rows.

| Model | AUC on unseen genomes (lab rows) |
|---|---|
| Forecaster | 0.908 (0.774 on all rows, most of which carry BV-BRC's own computational labels) |
| k-mer genome model | 0.935 |
| Gene model (AMRFinderPlus) | 0.977, and 0.82 to 0.94 on a genus held out of training |

The first version reported 0.93, but scored 0.644 on unseen genomes because its split let a genome appear in training and testing. That finding shaped the project. See [Results](docs/results.md).

**Data.** All 17.6 million AMR records in BV-BRC, cleaned to 7,847,110 rows (649,944 laboratory-confirmed), plus 24,926 complete genomes searched with AMRFinderPlus. See [Data and training](docs/data-and-training.md).

## Quick start

Needs Python 3.9+ and Node.js 18+.

```bash
./start.sh            # macOS / Linux: backend on :8000, web app on http://127.0.0.1:5173
start.bat             # Windows, same options
./start.sh --flask    # the older Flask frontend instead (http://127.0.0.1:5001)
./start.sh --update   # also reinstall or upgrade dependencies
```

The first run creates `.venv` and installs the web app's packages. If port 8000 already runs this backend, it is reused. Training, Docker and deployment are in [Running and deployment](docs/running-and-deployment.md).

## Repository

| Folder | Contents |
|---|---|
| `backend/` | Django REST API, the model registry, trained models and lookup tables (`backend/reference/`) |
| `web/` | React + TypeScript web app (the frontend to use) |
| `frontend/` | The older Flask web app, kept as a fallback |
| `amrpredict-lib/` | The `amrpredict` Python library and command line |
| `experiments/` | Experiment harness: configurations, results of every run, model promotion |
| `scripts/` | Data download, cleaning, audits, genome features, dashboard data |
| `notebooks/` | Colab notebooks that reproduce the served models from shared data |
| `progress/` | Each member's tracker and the formats agreed between components |
| `docs/` | Detailed documentation |

The data and the large genome files are not in the repository; [DATA_LINKS.md](docs/DATA_LINKS.md) says where they are.

## Documentation

- [Overview](docs/overview.md): the system in one page
- [Architecture](docs/architecture.md): layers, repository map, one request end to end
- [The prediction engines](docs/models.md): forecaster, genome models, timeline
- [Data and training](docs/data-and-training.md): BV-BRC data, cleaning, training, experiments
- [The web application](docs/frontend.md): every page, including the Resistance Explorer
- [The amrpredict library](docs/library.md): the package and its command line
- [Running and deployment](docs/running-and-deployment.md): launchers, CI, Docker, Railway
- [Results](docs/results.md) and [verified issues](docs/known-issues.md)
- [Glossary and reading order](docs/glossary.md)

History of changes: [CHANGES.md](CHANGES.md).

## Team

| Member | Role |
|---|---|
| Hamza Afzal (group leader) | Models: experiment harness, forecaster and genome models, evaluation, timeline ML, library |
| Malik Muhammad Suleman Saleh | Platform: Django API and security, React frontend, Docker, CI, deployment |
| Muhammad Ali Mirza | Data and evolution: BV-BRC data and cleaning, genome features, timeline and RL agent, Resistance Explorer |

Supervisor: Mr. Imran Latif. Co-supervisor: Muhammad Shahid Bhatti.

Predictions are for research and teaching, not clinical decisions.
