# The amrpredict library

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 7. The `amrpredict` package

This is the newest layer (commit `52ae361`, September) and the most polished code in the repo. It takes the three engines out of Django and makes them a standalone library.

**Version 0.2.0 is on TestPyPI** (https://test.pypi.org/project/amrpredict/0.2.0/, 2026-10-13) and installs in a clean environment (dependencies from the real PyPI):

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ amrpredict==0.2.0
```

0.2.0 bundles the forecaster the website serves (`D3_forecaster_deploy_v7`) and runs it with the backend's own loader (calibration, species-level taxa, the model's threshold), so `amrpredict.forecast()` gives the website's numbers; `backend/tests/test_library_parity.py` fails if the two drift. `predict_fasta()` still uses the original k-mer RandomForest (the genome models are not in the library yet). The real-PyPI release (`pip install amrpredict`) comes with the final version.

```python
import amrpredict
amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
amrpredict.predict_fasta(open('genome.fasta').read(), 'ampicillin')
amrpredict.simulate_timeline(fasta, 'imipenem', n_weeks=12)
amrpredict.antibiotics()   # the 62 the k-mer model knows
amrpredict.status()        # which models loaded
```

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
amrpredict predict genome.fasta ampicillin --threshold 0.6
cat genome.fasta | amrpredict timeline - imipenem --weeks 12
amrpredict antibiotics --compact | jq
```

**What differs from the backend copy**, these are the things worth listing in a report:

| | Backend | Library |
|---|---|---|
| Model loading | Eager, at Django startup | Lazy + thread-locked singleton (`registry.py`), nothing read until first call |
| Diagnostics | `print()` | `logging`, so `amrpredict antibiotics \| jq` isn't corrupted by stray output |
| Model dir | Required constructor arg | Defaults to models bundled inside the wheel (`_paths.py` via `importlib.resources`) |
| K-mer scaling | Fixed 2026-09-25 ([§11.1](known-issues.md)) | Fixed, scales only `feat[:256]` |
| Forecaster loader | `ml_models/lgbm_predictor.py` | Ported from it in 0.2.0, same outputs (parity test) |
| Import cost | numpy/pandas/lightgbm at import | Deferred via module `__getattr__` |
| Tests | 84 (`unittest`, in CI) | 35 pytest tests (in CI) |

The bundled forecaster files are the ones `experiments/promote.py --library` wrote to `backend/trained_models/` (the same run), so the library and the web app carry the same forecaster and, since 0.2.0, run it the same way.

`docs/known-issues.md` in that folder is required reading before you quote any number from this project. It is unusually candid and it is where the k-mer bug is documented.
