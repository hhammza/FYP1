# web/: the React + TypeScript frontend (in progress)

The new frontend, replacing the Flask one in `frontend/` page by page. Until
every page is moved, `frontend/` stays the site that is deployed and tested;
pages not yet moved here show a link to the Flask version.

Built with React 18, TypeScript, Vite and React Router; Bootstrap 5.3.2,
Bootstrap Icons 1.11.3 and Plotly 2.26.0 are the same versions the Flask site
vendors, and the stylesheets are the Flask site's own (`src/styles/`), so the
pages look the same.

## Run it

```bash
cd web
npm install          # once
npm run dev          # http://127.0.0.1:5173 (the Django backend must run on port 8000)
npm test             # unit tests (Vitest)
npm run build        # type-check, then build to web/dist/
```

In development `/api` is passed through to Django on port 8000. A deployed
build calls `VITE_API_URL` (the backend's `/api` address); the backend must
then list this site in `CORS_ALLOWED_ORIGINS`.

## Moved so far

| Page | Status |
|---|---|
| Layout (navbar, footer, theme, toasts) | done |
| `/` Dashboard | done |
| `/about`, `/datasets`, `/library` | done |
| `/forecast` (one isolate, Genome ID helper, batch CSV, downloads) | done |
| `/predict` (upload or paste, gene model's species and genes, downloads; `/predict/sample` on a dev run) | done |
| `/timeline` (simulation, RL panel, weekly table, downloads; `/timeline/sample` on a dev run) | done |
| `/models`, `/compare`, `/genes`, `/train` | to do |
| CSV/PDF downloads: `POST /api/export/<page>.<fmt>` in Django (`backend/api/exports.py`) | done |

Each moved page is checked against the Flask one in a browser: same text,
same page height, no console errors, light and dark theme; on the tool pages
the same inputs give the same result. 58 unit tests (`npm test`).
