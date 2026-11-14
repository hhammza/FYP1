# The amrpredict library

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 7. The `amrpredict` package

The project's models as a standalone library and command line, the proposal's main deliverable. It started as the three July engines taken out of Django (commit `52ae361`, September); since 0.3.0 it carries every model the website serves.

**Version 0.3.0** (built 2026-11-14, `amrpredict-lib/dist/`) is ready for the real PyPI; once uploaded:

```bash
pip install amrpredict
```

0.2.0 is on TestPyPI (https://test.pypi.org/project/amrpredict/0.2.0/, 2026-10-13); it bundled the served forecaster but still the July k-mer RandomForest for genomes.

| Function | Model (the website's) | Measured on data it never saw |
|---|---|---|
| `forecast()` | Forecaster `D3_forecaster_deploy_v7` (`/forecast`) | AUC 0.774, lab rows 0.908 |
| `predict_fasta()` | Gene model `G_genes_deploy` with AMRFinderPlus, else k-mer model `G_kmer_deploy` (`/predict`) | Lab AUC 0.977 / 0.935 |
| `identify_species()` | 6-mer species profiles (the gene model's) | Right species 98.0%, genus 99.8% |
| `forecast_trend()`, `trend_series()` | Timeline ML model `TL_timeline_ml` (`/timeline`, ML trend forecast) | 13.98 pp mean error, 2017–2022 |
| `plan_treatment()` | RL agent, PPO (`/timeline`, RL panel) | Beats every fixed schedule in the simulation |
| `simulate_timeline()` | Biological simulation (`/timeline`, what-if) | Not a trained model |

```python
import amrpredict
amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
amrpredict.predict_fasta(open('genome.fna').read(), 'ampicillin')
amrpredict.forecast_trend('Salmonella', 'ciprofloxacin', years_ahead=5)
amrpredict.plan_treatment('ciprofloxacin', n_weeks=52)
amrpredict.simulate_timeline(fasta, 'imipenem', n_weeks=12)
amrpredict.status()        # which models loaded, with their metrics
```

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
amrpredict predict genome.fna ampicillin
amrpredict trend Salmonella ciprofloxacin --years 5
amrpredict plan ciprofloxacin --weeks 52
amrpredict antibiotics --model trend --compact | jq
```

**What differs from the backend copy**, these are the things worth listing in a report:

| | Backend | Library |
|---|---|---|
| Model loading | At Django startup | Lazy + thread-locked singleton (`registry.py`), nothing read until first call |
| Diagnostics | `print()` | `logging`, so `amrpredict antibiotics \| jq` isn't corrupted by stray output |
| Model dir | Required constructor arg | Defaults to models bundled inside the wheel (`_paths.py` via `importlib.resources`) |
| Predictor code | `ml_models/lgbm_predictor.py`, `genome_predictor.py`, `timeline_ml.py`, `rl_agent.py` | Ported from them (imports and logging only), same outputs: `backend/tests/test_library_parity.py` checks the forecaster, the k-mer genome model, the timeline ML model and the RL agent |
| Dependencies | scikit-learn among them | LightGBM, pandas, NumPy, joblib only (the July RandomForest, the one pickled scikit-learn model, was removed in 0.3.0) |
| Import cost | numpy/pandas/lightgbm at import | Deferred via module `__getattr__` |
| Tests | `unittest`, in CI | 55 pytest tests, in CI; pass on Python 3.9 and 3.13 |

The bundled files are the served ones: `experiments/promote.py --library` copies the forecaster, and `experiments/sync_library.py` the genome, timeline ML and RL models (`--check` reports any that differ). After promoting a new model, run them, bump the version in `amrpredict-lib/pyproject.toml` and rebuild (`python -m build`).

`amrpredict-lib/docs/known-issues.md` is required reading before you quote any number from this project. It is unusually candid and it is where the July k-mer bug is documented.
