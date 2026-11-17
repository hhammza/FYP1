# End-to-end checklist

Every page, every form and every download, checked the way a user meets them. Run it before a demo, after a deploy (Week 5: against the live URLs), and after any change to the website.

## Automatic: one command

```bash
python -m pip install playwright            # once
python -m playwright install chromium       # once (or use --browser msedge on Windows)

python scripts/e2e_check.py --start         # starts both servers, checks, stops them
python scripts/e2e_check.py                 # servers already running (start.bat / start.sh)
python scripts/e2e_check.py --base https://<frontend>.up.railway.app   # the deployed site

# the React frontend (web/): the same steps
python scripts/e2e_check.py --site react --start
python scripts/e2e_check.py --site react --base https://<web>.up.railway.app --api https://<backend>.up.railway.app/api
```

It prints ✓ or ✗ for each step below and exits 0 only if all pass. For `/predict` it downloads one complete genome the served model never trained on (from its test list, BV-BRC); `--no-genome` skips that step when offline.

Last run: **2026-11-17**: React 26 of 26 and Flask 26 of 26 (local, Windows, Edge), after the /timeline split into the ML forecast (`#timelineForm`, `/api/timeline/`) and the what-if simulation (`#simulationForm`, `/api/timeline/simulate/`). Earlier, 2026-10-25: React 24 of 24, Flask 23 of 23.

## By hand: the same steps

**Start:** `start.bat` (Windows) or `./start.sh` (Mac). Both windows open; the site is on http://127.0.0.1:5001.

### 1. Health
- [ ] `/api/health` lists the forecaster and the genome model as `trained: true` (on the deployed image also `searches_genes: true`)

### 2. Every page opens with no errors (browser console clean)
- [ ] `/` · `/forecast` · `/predict` · `/timeline` · `/models` · `/compare` · `/genes` · `/datasets` · `/about` · `/library` · `/train`

### 3. `/forecast`
- [ ] Antibiotic ciprofloxacin → genus *Escherichia* → species list shows only *coli* → taxon ID list shows 562; the MIC field suggests values for *E. coli* + ciprofloxacin
- [ ] Antibiotic gentamicin, **Fill from Genome ID** `106654.148` → *Acinetobacter nosocomialis* filled, "a fair test", lab result Resistant (MIC ≥ 16 mg/L); a training genome (`1001988.3`) shows the caution instead
- [ ] **Predict Resistance** → a result with a probability and the comparison chart; the Genome ID box says whether the model agrees with the lab
- [ ] Download **CSV**, **PDF report**, **Chart (PNG)**: each opens
- [ ] **Upload CSV** tab → download the template → upload it → results table and chart → **CSV** download

### 4. `/predict`
- [ ] Paste tab → **Load Sample** → Predict: refused with "genome too short … upload a complete assembly" (not a prediction)
- [ ] Upload a complete genome (FASTA, 2–7 MB) → a prediction within the wait (button says "Analysing the genome…"); on the gene model: "Identified as …" and the resistance-genes panel
- [ ] Download **CSV**, **PDF report**, **Chart (PNG)** (PNG only when the k-mer chart is shown)

### 5. `/timeline` (two tabs: the ML forecast, then the what-if simulation)
- [ ] **ML trend forecast** tab: ciprofloxacin, organism **Salmonella** → about 21 years of history, a dashed forecast with its 80% band
- [ ] Download **CSV**, **PDF report**, **Chart (PNG)** of the forecast
- [ ] Organism **From a genome**: erythromycin + a complete *S. pneumoniae* genome → "identified as Streptococcus" and its forecast
- [ ] **What-if simulation** tab: Paste tab → **Load Sample** → Generate → the weekly chart; ciprofloxacin, gentamicin or imipenem → the RL panel, its red week chips at the weeks the table gives (preview: `/timeline/sample` on a local run)
- [ ] Download the simulation's **CSV**, **PDF report**, **Chart (PNG)**; each is labelled "Simulation, not a trained model"
- [ ] Every antibiotic field (React): typing narrows the list ("cefi" → cefixime, cefiderocol); Enter or a click chooses

### 6. `/genes`
- [ ] Gene matrix CSV and gene info CSV download
- [ ] Look up a genome (e.g. `1000561.3`) → its genes

### 7. Admin (only with `ADMIN_TOKEN` set)
- [ ] `/train`: without the token → refused; with it → "Training started" (saved to `trained_models/candidates/`, the served model unchanged)

### 8. Offline (before a demo)
- [ ] Wi-Fi off, `start.bat` → "Dependencies already installed; skipping"; pages keep their layout, icons and charts (only the web fonts change)

## Also checked automatically on every push (GitHub Actions)

The unit tests (every API route and page: 84 backend, 74 frontend, the RL converter and the library) and the Docker image serving the gene model on an unseen genome. See README, "Continuous integration".
