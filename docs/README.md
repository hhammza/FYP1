# Project documentation

The detailed guides for the AMR Intelligence Platform. The top-level [README](../README.md) is the short version; start there if you are new.

## Guides

| Guide | What it covers |
|---|---|
| [Overview](overview.md) | The 60-second version, the problem, the three questions the platform answers, and the dated update notes |
| [Architecture](architecture.md) | Repository map, the layers, and one genome upload traced from the browser to the model and back |
| [The prediction engines](models.md) | The LightGBM forecaster, the genome models (genes and k-mers), and the mutation timeline: inputs, outputs, fallbacks |
| [Data and training](data-and-training.md) | BV-BRC data, cleaning, the production trainer, the experiment harness, and the notebooks the models came from |
| [The amrpredict library](library.md) | The pip-installable package and its command line |
| [The web application](frontend.md) | Every page, downloads and batch upload, the report pages, the genes page and the Resistance Explorer |
| [Running and deployment](running-and-deployment.md) | `./start.sh` and `start.bat`, training, CI, Docker and Railway |
| [Results](results.md) | Every headline number and the run or script it comes from |
| [Verified issues and fixes](known-issues.md) | Problems found in the code, how each was fixed, and what is still open |
| [Glossary and reading order](glossary.md) | Terms (AUC, VME, MIC, k-mer and so on) and the order to read the code in |

## Plans and references

| Document | What it is |
|---|---|
| [INSTRUCTOR_REQUIREMENTS_PLAN.md](INSTRUCTOR_REQUIREMENTS_PLAN.md) | The instructor's twelve dashboard requirements, the decisions taken and their progress |
| [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | The experiments behind every model choice, with their run IDs |
| [E2E_CHECKLIST.md](E2E_CHECKLIST.md) | The browser walk-through used to check every page end to end |
| [DATA_LINKS.md](DATA_LINKS.md) | Where the shared data lives |
| [how_to_make_python_library.md](how_to_make_python_library.md) | How the `amrpredict` package was built and published |
| [FYP_Completion_Roadmap.md](FYP_Completion_Roadmap.md) | The FYP-II roadmap |
| [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | The older long reference (May 2026, before the FYP-II rebuild). Kept for history; where it disagrees with the guides above, the guides are current |

The FYP-II report (LaTeX sources, figures and build scripts) is kept outside the repository.
