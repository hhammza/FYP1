# Verified issues and fixes

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 11. Verified issues and gaps

Each of these was reproduced or read directly in the code today, not inferred.

### 11.1 The K-mer model never ran in the web app (fixed 2026-09-25; model replaced 2026-09-29)

*Fixed in `resistance_predictor.py` (the scaler now sees only the 256 k-mer columns), and since 2026-09-29 `/predict` serves the complete-genome model ([§4.2](models.md)). Kept below as the record of what went wrong.*

`train_models.py` fits the scaler on the **256 k-mer columns only**. `resistance_predictor.py:158` hands it the **full 321-element vector**:

```python
feat = self.scaler.transform(feat.reshape(1, -1))[0]   # ValueError
```

Reproduced against the shipped artifacts:

```
[K-mer] Model loaded. Antibiotics: 62
[K-mer] Prediction error: X has 321 features, but StandardScaler is expecting 256 features as input.
prob run1: 0.3363   run2: 0.3552   model_used: 'RandomForest K-mer (trained)'
```

Three consequences:

- The `except Exception` around it swallows the error and calls `_heuristic_predict()`, a GC-content formula with `np.random.uniform(-0.04, 0.04)` noise. The same genome gives a different answer every time.
- The response still says `'model_used': 'RandomForest K-mer (trained)'`, because `is_trained` refers to *loading*, not *predicting*. Nothing in the UI reveals the fallback.
- Any accuracy figure quoted for the `/predict` page is meaningless.

The fix is one line, and it is already written and tested in the library (`amrpredict-lib/src/amrpredict/kmer.py:166`):

```python
feat[:N_KMERS] = self.scaler.transform(feat[:N_KMERS].reshape(1, -1))[0]
```

It was ported to `backend/ml_models/resistance_predictor.py` on 2026-09-25, and on 2026-09-29 `/predict` moved to the genome models, so this model now only answers when no genome model is promoted.

### 11.2 Training could not run from a fresh clone (fixed 2026-09-25)

The trainer looked for `amr_output/`, `mapped_output/` and `fasta_output/` directly inside the project root, but the data lives in `Data/`. So `POST /api/train/` started its thread, printed `[Data] amr_output not found`, and returned `False`, while the UI had already reported "Training started".

Now `resolve_data_dir()` in `train_models.py` accepts the project root or the data folder and finds `Data/` (or `data/`) itself, so both the command line and `/api/train/` work. `/api/train/` returns HTTP 503 with a message when no data is found, instead of starting a thread. The trainer also reads every file by default instead of the first 500 (LightGBM) and 200 (K-mer) of an unsorted listing, which is how the shipped LightGBM missed *Klebsiella*. The committed models in `trained_models/` still date from 10 July; [§10](results.md) shows which files they were trained on.

### 11.3 Timeline population shares exceeded 100% (fixed in the backend 2026-09-26)

Once the susceptible pool emptied (~week 7 at default settings), `susceptible` clamped at 0, `intermediate` pinned at 25.0, and `resistant` kept growing, so the three summed to 106% by week 8. Now `intermediate` can never exceed the non-resistant share and `susceptible` takes the rest, so the three add up to exactly 100 (checked on every drug profile at 1 to 52 weeks). The resistant curve and `failure_week` are unchanged; only late-week `intermediate` and `susceptible` values move.

The library's copy (`amrpredict-lib/src/amrpredict/timeline.py`) was synced by Ali on 2026-09-29 and its strict `xfail` removed, so the test now must pass in both.

### 11.4 Security (hardened 2026-09-26)

Until 2026-09-26: `SECRET_KEY` had a hardcoded fallback, `ALLOWED_HOSTS` defaulted to `*`, `CORS_ALLOW_ALL_ORIGINS = True`, `csrf_exempt` on every POST view, and `/api/train/` and `/api/reload/` were open to anyone who could reach the backend. Now:

| Area | What the code does | Where |
|---|---|---|
| Secrets | `SECRET_KEY` from the environment only; the backend refuses to start without it when `DEBUG` is off. Flask has no secret (it uses no sessions) | `settings.py`, `frontend/app.py` |
| Hosts | `ALLOWED_HOSTS` from the environment, no `*`; required when `DEBUG` is off | `settings.py` |
| CORS | No origins allowed. Browsers never call the API; Flask calls it from its server | `settings.py` |
| CSRF | Not installed, and the no-op `csrf_exempt` decorators removed. CSRF abuses credentials a browser sends by itself (cookies); the API uses none, and the admin token is a header a browser never adds on its own | top of `api/views.py` |
| Train / Reload | `X-Admin-Token` must equal `ADMIN_TOKEN` (constant-time compare), else 401; no `ADMIN_TOKEN` = both off (503). `/api/train/` accepts only `lgbm` or `kmer`, since the name is part of a folder path | `api/views.py` |
| Uploads | FASTA over 20 MB gets 413, whether uploaded, pasted, or an oversized body; Flask refuses it first and shows a message | `settings.py`, `api/views.py`, `frontend/app.py` |
| Rate limits | Per visitor IP: forecast 60 a minute, predict and timeline 10 a minute, then 429 (`django-ratelimit`). Flask forwards the browser's IP in `X-Forwarded-For` | `settings.py`, `api/views.py` |
| Database | None (`DATABASES = {}`), and no `migrate` step: the API stores no user data | `settings.py`, `Procfile` |

`backend/tests/test_security.py` checks each row (`python -m unittest discover -s backend/tests`).

Limits worth saying out loud: rate-limit counts are per worker process, and a direct caller can set `X-Forwarded-For` itself, so the limit stops casual abuse, not a determined attacker. Error responses still include the exception text, which a production service would hide.

### 11.5 Smaller things

- `notebooks/forecasting_formulation.ipynb`, a 0-byte file, was removed on 2026-10-13.
- `*_fraction` fields in the timeline are on a **0 to 100** scale despite the name; renaming would break the templates, so the name stands.
- `kmer_resistance_model.pkl` was pickled with scikit-learn 1.6.1; loading under a different 1.x warns and is not guaranteed identical. The library pins `<2.0` so a 2.x install fails loudly instead of being quietly wrong. The backend has no such pin (`scikit-learn>=1.3`).
- `docs/PROJECT_DOCUMENTATION.md:726` states the scaler "is applied identically at inference time." That was the intent; §11.1 is what the code does.
