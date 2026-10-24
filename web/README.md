# web/: the React + TypeScript frontend

Every page of the Flask site in `frontend/`, rebuilt in React 18 and
TypeScript (Vite, React Router). Bootstrap 5.3.2, Bootstrap Icons 1.11.3 and
Plotly 2.26.0 are the versions the Flask site vendors, and the stylesheets are
its own (`src/styles/`), so the pages look the same. The browser calls the
Django API itself; there is no frontend server code.

## Run it

```bash
cd web
npm install          # once
npm run dev          # http://127.0.0.1:5173 (the Django backend must run on port 8000)
npm test             # unit tests (Vitest)
npm run build        # type-check, then build to web/dist/
npm start            # serve web/dist/ (server.mjs), as on Railway
```

In development `/api` is passed through to Django on port 8000. A deployed
build calls `VITE_API_URL` (the backend's `/api` address, read at build time);
the backend must then list this site in `CORS_ALLOWED_ORIGINS`.

## Pages

All 11, with the same routes as Flask: `/`, `/forecast` (one isolate, Genome
ID helper, batch CSV), `/predict` (upload or paste; the gene model's species
and genes), `/timeline` (simulation and the RL panel), `/models`, `/compare`,
`/genes` (with `#genome=<id>` links), `/datasets`, `/library`, `/about`,
`/train`. `/predict/sample` and `/timeline/sample` show the agreed sample
responses on a development run only.

The CSV/PDF downloads come from `POST /api/export/<page>.<fmt>` in Django
(`backend/api/exports.py`).

## How it is checked

- `npm test`: 74 unit tests, the backend's answers mocked.
- `python scripts/e2e_check.py --site react`: the 23 browser steps of
  `docs/E2E_CHECKLIST.md`, the same as for the Flask site.
- Each page was compared with the Flask one in a browser: the same text and
  page height, every chart's Plotly figure identical, no console errors.
- CI (`.github/workflows/ci.yml`, job `web`): type check, tests, build and
  `npm audit` on every push and pull request.

## Deploy (Railway)

A third service with root directory `web/` (`railway.toml`): Nixpacks builds
it, `npm start` runs `server.mjs`, a plain Node static server (no packages)
that answers any page path with `index.html` and a missing file with a 404.
Set `VITE_API_URL` on it and `CORS_ALLOWED_ORIGINS` on the backend.
