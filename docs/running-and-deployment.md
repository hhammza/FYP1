# Running and deployment

*Part of the [project documentation](README.md). Moved from the top-level README on 2026-11-14; section numbers (§) are kept, so older references still match.*

## 9. Running, training, deploying

### Local (macOS/Linux)

```bash
./start.sh            # backend + React app (web/) on http://127.0.0.1:5173
./start.sh --flask    # backend + the older Flask app (frontend/) on http://127.0.0.1:5001
./start.sh --update   # also reinstall or upgrade the dependencies (needs internet)
```

Creates `.venv` if missing, installs both requirement sets, checks for **libomp** (LightGBM's OpenMP dependency, without it `import lightgbm` fails on macOS and the forecaster silently degrades to heuristics), starts Django on 8000 and waits for `/api/health/` to answer. It then starts the React app with Vite on **5173**, which passes `/api` through to the backend; the first run installs its packages with `npm ci`. The React app needs Node.js 18 or newer; without Node, or with `--flask`, the launcher starts Flask on **5001** instead (`app.py`'s default; not 5000, which macOS AirPlay Receiver owns). If port 8000 already has this project's backend (an earlier `./start.sh` still running), the launcher uses it and leaves it running on exit; if another program holds 8000, the backend moves to the next free port and the frontend is pointed there. It opens the browser and tears down what it started on Ctrl-C. Only the React app has the Resistance Explorer.

Windows: `start.bat`, with the same options (`--flask`, `--update`), in two `cmd` windows: ports 8000 and 5173, or 5001 with `--flask`. It creates `.venv` if missing and runs everything with the venv's Python, so no activation is needed.

Both launchers start the backend with `DEBUG=True`, local development mode, so no `SECRET_KEY` or `ALLOWED_HOSTS` is needed (Django makes a random key per process). Starting the backend by hand needs the same: `DEBUG=True python manage.py runserver`, or `set DEBUG=True` first on Windows. There is no `migrate` step: the API uses no database.

Train and Reload on `/train` need a password you choose when you start:

```bash
ADMIN_TOKEN=some-password ./start.sh          # macOS / Linux
```

```bat
set ADMIN_TOKEN=some-password
start.bat
```

(Windows: both lines in the same Command Prompt window; in PowerShell the first is `$env:ADMIN_TOKEN="some-password"`)

then type the same password on the Train page. Without `ADMIN_TOKEN` every other page works and those two buttons are switched off.

### Training

```bash
cd backend && python train_models.py --model all     # or lgbm / kmer
python train_models.py --model lgbm --max-files 500  # seeded random subset of files
python train_models.py --model lgbm --model-dir /tmp/out   # write somewhere else
```
Windows: `scripts\train_all.bat`. The trainer finds the data in `Data/` itself. With all files, the LightGBM trains in about 4 minutes on 1.56 M rows (cleaning v5); the K-mer model takes about an hour, because it computes GC content row by row. Training writes to `backend/trained_models/candidates/<model>/` (the same place `/api/train/` uses) and never touches the deployed models; a model is served only after `experiments/promote.py`, which also writes its `metrics.json`.

### Continuous integration (GitHub Actions)

[`.github/workflows/ci.yml`](../.github/workflows/ci.yml) runs on every push and pull request:

| Job | When | What |
|---|---|---|
| `tests` | every push and PR | Python 3.12, scikit-learn 1.6.1 (as the image and the library pin): backend, frontend and RL-converter tests (`unittest`), and the `amrpredict` library (`pytest`). No PyTorch: no test uses stable-baselines3 |
| `docker` | pushes to `main`, or by hand | Builds `backend/Dockerfile` (AMRFinderPlus with its pinned database; the conda layer is cached between runs), starts it with production settings, and runs [`scripts/ci_docker_smoke.py`](../scripts/ci_docker_smoke.py): `/api/health/` must say `searches_genes: true`, and one complete genome from the gene model's **test** list, downloaded from BV-BRC, must come back from `/api/predict/` with `genes_found` and `species_detected` within the page's 120 s |

The same commands locally: `python -m unittest discover -s backend/tests` (and `-s frontend/tests`, `-s experiments/evolution -p "test_*.py"`), and `PYTHONPATH=src python -m pytest -q` in `amrpredict-lib/`.

**End to end, in a real browser:** `python scripts/e2e_check.py --start` opens every page, submits every form and checks every download (23 steps; needs `python -m pip install playwright`). The same steps by hand, and how to run it against the deployed site: [docs/E2E_CHECKLIST.md](E2E_CHECKLIST.md).

### Docker (backend)

```bash
docker build -f backend/Dockerfile -t amr-backend .      # from the project root
docker run -p 8000:8000 -e SECRET_KEY=... -e ALLOWED_HOSTS=localhost -e ADMIN_TOKEN=... amr-backend
```

The image holds `backend/` only (about 21 MB of code and models, plus AMRFinderPlus from bioconda for the gene model); the root `.dockerignore` keeps `Data/`, `experiments/` and the other folders out. It runs gunicorn on `$PORT` (8000 by default). Training is not available inside it (no `Data/`), so `/api/train/` answers 503 there.

AMRFinderPlus's database is pinned to **2026-08-07.1**, the version the gene model was trained with, instead of the newest one `amrfinder -u` would fetch: `backend/docker/fetch_amrfinder_db.py` downloads exactly that version from NCBI (43 files, about 130 MB) and the build stops if a file is missing or the version differs; `AMRFINDER_DATABASE` points at it. To move to a newer database, change `AMRFINDER_DB_VERSION` in the Dockerfile together with a gene model retrained on it. With AMRFinderPlus in the image, `/predict` serves the gene model; check `/api/health/` → `models.kmer_resistance.searches_genes` is `true`.

### Deployment (Railway, two services)

| | Backend | Frontend |
|---|---|---|
| Start | `gunicorn backend.wsgi:application --workers 2 --timeout 120` | `gunicorn app:app --workers 2 --timeout 120` |
| Health check | `/api/health/` | `/` |
| Required env vars | `SECRET_KEY`, `ALLOWED_HOSTS` (its Railway domain, plus `healthcheck.railway.app` for the health check), `ADMIN_TOKEN` | `BACKEND_URL` |
| Optional env vars | `CORS_ALLOWED_ORIGINS` (not needed for the Flask site, whose browser never calls the API; **needed** for the React site in `web/`, set to its address), `RATELIMIT_ENABLE=False` | `PORT` (Railway sets it), `LIB_VERSION`, `SECRET_KEY` (unused: no sessions) |

Leave `DEBUG` unset in production. Without `SECRET_KEY` or `ALLOWED_HOSTS` the backend refuses to start and says which is missing. Generate a key with `python -c "import secrets; print(secrets.token_urlsafe(50))"`.

`frontend/app.py` infers its mode from `PORT`: if Railway sets it, `debug=False`; locally with no `PORT`, debug is on and the server listens on 127.0.0.1 only, since the debugger can run code.

**The React frontend instead of Flask** (`web/`): a service with root directory `web/` (`web/railway.toml`). Nixpacks builds it; `npm start` runs `web/server.mjs`, a plain Node static server. Set `VITE_API_URL` (the backend's `/api` address, read at build time) on it, and `CORS_ALLOWED_ORIGINS` (its address) on the backend. Check it with `python scripts/e2e_check.py --site react --base <web> --api <backend>/api`.
