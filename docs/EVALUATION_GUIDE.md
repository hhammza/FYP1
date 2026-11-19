# Evaluation guide: the code behind every number

*For the evaluation. Where the preprocessing and model code is, which notebook reproduces each reported number, and how to install the `amrpredict` library on any laptop. Answers to the ML and data science questions: [EVALUATION_QA.md](EVALUATION_QA.md).*

## 1. The notebooks, in the order to show them

Every notebook runs the project's **own code** (the same functions that trained the served models; each one prints that code where it is first used) and was saved **with its outputs**, so it can be shown without running it. Each one checks its results against the published run. They are in [`notebooks/`](../notebooks/).

| # | Notebook | What it shows | Reported number it reproduces |
|---|---|---|---|
| 00 | [00_preprocessing.ipynb](../notebooks/00_preprocessing.ipynb) | Raw BV-BRC records → the modelling table, one cleaning step at a time (labels, MIC, organism, antibiotic names, lab vs computational, one row per genome and drug); a genome turned into model inputs | **7,847,110** rows, **649,944** laboratory rows, 439,542 genomes, 28.0% resistant, 126 antibiotics, 23 classes, 40 genera: 13 figures, all ✓ (section 9) |
| 01 | [01_forecaster_model.ipynb](../notebooks/01_forecaster_model.ipynb) | The forecaster (`/forecast`): split by genome, out-of-fold resistance rates, LightGBM, calibration, threshold, ROC curve (section 7) | AUC **0.774** (0.7737) on unseen genomes, **0.908** on laboratory rows; threshold 0.15 (section 7) |
| 02 | [02_genome_models.ipynb](../notebooks/02_genome_models.ipynb) | The gene model and the k-mer model (`/predict`); how the website builds features from an uploaded genome; ROC curves of both models (section 5) | Lab AUC **0.977** (gene) and **0.935** (k-mer), "same as published" (section 5) |
| 03 | [03_evaluation.ipynb](../notebooks/03_evaluation.ipynb) | Why the numbers can be trusted: seen vs never-seen genomes, seeds, significance tests, lineage split, temporal test | The first model's 0.93 falling to **0.64** on unseen genomes (section 1) |
| 04 | [04_timeline_ml_and_gan.ipynb](../notebooks/04_timeline_ml_and_gan.ipynb) | The timeline ML model (`/timeline`): yearly series, features, two tests, the forecast; the GAN experiment | **13.98** pp on 2017–2022 (temporal test) and **9.86** pp on 20% of the series held out (80/20 test); GAN AUC −0.008 on rare classes |
| 05 | [05_rl_agent.ipynb](../notebooks/05_rl_agent.ipynb) | The RL agent: environment, fixed schedules, training code, the served agent evaluated | Served agent **92.5** effective weeks, first failure **77.14**: identical to training; report figures 95.0 and 81.3 (3 seeds pooled) |
| 06 | [06_library_demo.ipynb](../notebooks/06_library_demo.ipynb) | The library from PyPI, in a clean environment: every function, one genome no model trained on | Forecast **Resistant 0.7055**, as on the website; 11 of 14 lab results right on the test genome |

**A 10-minute walkthrough:** 00 section 9 (the data matches), 01 section 7 (forecaster on unseen genomes), 02 section 5 (genome models), 03 section 1 (why the first 0.93 was wrong), 04 section A3 (timeline), 05 section 4 (RL agent), then the library live on the teacher's laptop (section 3 below).

To open them: VS Code (with the Python and Jupyter extensions) or `jupyter notebook`, from the project folder. To re-run one, use the project environment: `.venv\Scripts\python.exe -m pip install -r experiments/requirements.txt jupyter`, then *Run All*. They need the cleaned data cache (`experiments/cache/`, on the team's Google Drive, [DATA_LINKS.md](DATA_LINKS.md)); 05 needs no data.

## 2. Where the code is

| Step | Code | Shown in |
|---|---|---|
| Download from BV-BRC | `scripts/bvbrc_download/download_amr_full.py`, `experiments/genome/features/download_genomes.py` | 00 §1 |
| Cleaning | `experiments/lib/data_prep.py` (`clean()`), `backend/amr_constants.py` (label map, antibiotic aliases, drug classes) | 00 §2–8 |
| Data audit | `experiments/audit/audit_bvbrc.py` → `experiments/audit/results/audit.md` | Data chapter §4 |
| Split by genome, features | `experiments/lib/splits.py`, `experiments/lib/encoders.py` | 01 §3–4 |
| Training harness | `experiments/run.py` with a config from `experiments/configs/` (e.g. `D3_forecaster_deploy_v7.json`) | 01 §1, §5 |
| Genome features | `experiments/genome/kmers.py`, `experiments/genome/genes.py` | 02 §2, 00 §10 |
| Metrics, confidence intervals, tests | `experiments/lib/metrics.py` | 01 §7, 03 |
| Timeline ML model | `experiments/timeline_ml/timeline_model.py` | 04 |
| RL agent | `experiments/evolution/rl_env.py`, `rl_train.py` | 05 |
| GAN | `experiments/gan/ctgan_augment.py` | 04 part B |
| Served models | `backend/ml_models/`, files in `backend/trained_models/` | 02 §7, 05 §4 |
| Library | `amrpredict-lib/src/amrpredict/` | 06 |

## 3. The library on another laptop

Needs Python 3.9 or newer (python.org) and internet. Nothing else from the project.

**Windows (PowerShell):**

```powershell
mkdir amr-demo
cd amr-demo
python -m venv venv
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\python -m pip install --default-timeout=300 --retries 10 amrpredict
.\venv\Scripts\python -c "import amrpredict; print(amrpredict.__version__)"
curl.exe -L -o demo.py https://raw.githubusercontent.com/hhammza/FYP1/main/amrpredict-lib/examples/demo.py
.\venv\Scripts\python demo.py --step
```

If `python` is not found, use `py -3` in the third line. The venv's Python is called directly, so the venv never needs activating (activation scripts are often blocked by the PowerShell execution policy).

**macOS or Linux (Terminal):**

```bash
mkdir amr-demo && cd amr-demo
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install amrpredict
python -c "import amrpredict; print(amrpredict.__version__)"
curl -L -o demo.py https://raw.githubusercontent.com/hhammza/FYP1/main/amrpredict-lib/examples/demo.py
python demo.py --step
```

`demo.py` walks through every model, one section per Enter key (`--step`); `--no-genome` skips the 5 MB genome download. The version line should print `0.3.0`.

**One function at a time** (Windows: put `.\venv\Scripts\` before `python`; macOS/Linux with the venv active, as is):

```bash
python -c "import amrpredict; print(amrpredict.status().keys())"
python -c "import amrpredict; print(amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4))"
python -c "import amrpredict; print(amrpredict.forecast_trend('Streptococcus', 'penicillin', years_ahead=5)['forecast'])"
python -c "import amrpredict; print(amrpredict.plan_treatment('ciprofloxacin', n_weeks=12)['best'])"
python -m amrpredict.cli forecast ciprofloxacin --taxon-id 562 --mic-value 4
python -m amrpredict.cli trend Streptococcus penicillin --years 5
python -m amrpredict.cli antibiotics --model trend
```

**If something goes wrong:**

| Message | Fix |
|---|---|
| `ReadTimeoutError` or `Connection broken` during the install | Run the install line again; `--default-timeout=300 --retries 10` is already there for slow connections |
| `An Application Control policy has blocked this file` | Windows blocks new `.exe` launchers: use `python -m pip ...` and `python -m amrpredict.cli ...` as above, never `pip.exe` or `amrpredict.exe` |
| `OSError ... lib_lightgbm.dll` | Install the Microsoft Visual C++ Redistributable (x64) from Microsoft, then retry |
| `No matching distribution found for amrpredict` | Python is older than 3.9: install a newer one from python.org |

On Windows, `predict_fasta()` uses the k-mer model (lab AUC 0.935). The gene model (0.977) needs NCBI AMRFinderPlus, which runs on Linux or macOS (`conda install -c bioconda ncbi-amrfinderplus`); the project's CI runs the library's gene model with it and checks it gives the website's answer.
