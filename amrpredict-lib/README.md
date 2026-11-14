# amrpredict

Antimicrobial resistance prediction from bacterial genomes and MIC metadata.

The models of the AMR Intelligence Platform (a final-year project) behind one
flat Python API and a command-line tool: the same models, and the same answers,
as the project's web app. The trained artifacts ship inside the package, so
there is nothing to download and it works offline.

```python
import amrpredict

amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
# {'prediction': 'Resistant', 'probability': 0.7055, 'confidence': 70.6,
#  'drug_class': 'fluoroquinolone', 'model_run': 'D3_forecaster_deploy_v7', ...}
```

## Install

```bash
pip install amrpredict
```

Requires Python 3.9+. Dependencies: LightGBM, pandas, NumPy, joblib. The
download is about 6 MB because the model artifacts are bundled.

For the gene model (the most accurate genome model), also install NCBI
[AMRFinderPlus](https://github.com/ncbi/amr) so the `amrfinder` program is on
your PATH (e.g. `conda install -c bioconda ncbi-amrfinderplus`). Without it,
`predict_fasta()` uses the k-mer model.

From a checkout:

```bash
pip install -e ".[dev]"
```

## The models

| Function | Model | Input | Measured on data it never saw |
|---|---|---|---|
| `forecast()` | LightGBM, calibrated | Antibiotic + organism + MIC | AUC 0.774 (lab-confirmed rows 0.908) |
| `predict_fasta()` | Gene model: LightGBM on AMRFinderPlus genes and mutations | Complete genome FASTA | Lab AUC 0.977 [0.975–0.979] |
| `predict_fasta()` without AMRFinderPlus | k-mer model: LightGBM on 4-mer frequencies | Complete genome FASTA | Lab AUC 0.935 [0.931–0.939] |
| `forecast_trend()` | Timeline ML model: LightGBM on yearly resistant shares | Genus + antibiotic | 13.98 percentage points mean error on 2017–2022 |
| `plan_treatment()` | RL agent (PPO), trained on the simulation | One of 3 antibiotics | Beats every fixed schedule in the simulation |
| `simulate_timeline()` | Biological simulation | Genome FASTA + antibiotic | **Not a trained model** |

Every trained model was tested on genomes (or years) it never saw in training.
`simulate_timeline()` is a deterministic simulation, not a learned model: it
has no accuracy score, and its output is illustrative rather than predictive.
`status()` reports `trained: False` for it, deliberately.

## Usage

### Resistance from metadata and an MIC

```python
r = amrpredict.forecast(
    'ciprofloxacin',
    taxon_id=562,           # NCBI taxonomy ID — 562 is E. coli
    mic_value=4,            # mg/L
    mic_sign='=',           # '=', '>', '<=' ...
    genus='Escherichia',
    species='coli',
    # threshold=None: the model's own (0.15, chosen to keep very major
    # errors <= 10% on validation genomes); pass a number to override
)

print(r['prediction'])         # 'Resistant'
print(r['probability'])        # calibrated
print(r['evidence']['label'])  # which inputs counted
```

On 1,569,432 test rows from genomes it never saw: AUC 0.774 [0.772–0.775],
recall 91.4%, very major error 8.6%, major error 60.8% at that threshold
(`status()['lgbm_forecasting']['metrics']` has the full set). Every argument
except `antibiotic` is optional; with fewer inputs the model falls back to
population-level resistance rates.

### Resistance from a complete genome

```python
with open('genome.fna') as fh:
    fasta = fh.read()

r = amrpredict.predict_fasta(fasta, 'ciprofloxacin')

print(r['prediction'], r['probability'])
print(r['model_used'])        # 'LightGBM on AMRFinderPlus resistance genes (G_genes_deploy)'
print(r['genes_found'][:3])   # gene model: the resistance genes and mutations found
print(r['species_detected'])  # gene model: the species, from the genome
print(r.get('top_kmers'))     # k-mer model: the most frequent 4-mers
```

- Upload a **complete assembly** (at least 100,000 bp); every contig is read.
- `use_genes=None` (default) picks the gene model when AMRFinderPlus is
  installed, else the k-mer model; `use_genes=False` always uses the k-mer
  model; `use_genes=True` requires the gene model. If AMRFinderPlus fails on
  one genome, the k-mer model answers and the result has a `warning`.
- `threshold=None` uses each model's own threshold, chosen on validation
  genomes for very major error near 10%.
- Bad input (too short, empty) returns a dict with `error`; it never raises.

```python
amrpredict.identify_species(fasta)
# {'species': 'Pseudomonas aeruginosa', 'genus': 'Pseudomonas', 'distance': 0.00028}
```

### Yearly resistance trend and its forecast

```python
r = amrpredict.forecast_trend('Salmonella', 'ciprofloxacin', years_ahead=5)

for h in r['history']:     # observed: BV-BRC laboratory results per year
    print(h['year'], h['resistant_pct'], h['n'])
for f in r['forecast']:    # the model's forecast with an 80% band
    print(f['year'], f['resistant_pct'], f['lo'], f['hi'])
print(r['metrics'])        # its held-out error against simple baselines

amrpredict.trend_series()  # {genus: [antibiotics]} with enough history
```

Trained on 553,223 dated laboratory results (2000–2022; a year counts with at
least 20 results), it predicts each year from the years before it and was
tested on 2017–2022: mean absolute error 13.98 percentage points, against
14.33 for "same as last year", 16.75 for a linear trend and 17.25 for the
average. The forecast is made one year at a time; the band widens with each.

### Which drug to give each week

```python
r = amrpredict.plan_treatment('ciprofloxacin', n_weeks=52)

print(r['best'])                  # the policy that keeps drugs working longest
for p in r['policies']:           # the RL agent, then fixed schedules
    print(p['label'], p['failure_week'], p['total_reward'])
print(r['policies'][0]['policy'][:8])   # the agent's drug for weeks 1-8
```

A PPO agent chooses ciprofloxacin, gentamicin or imipenem each week in the
project's cycling simulation; the policies are compared on the same simulated
episode. It learned from simulated episodes only, not patient data: use it to
explore cycling strategies, not to treat patients.

### Week-by-week simulation (not a trained model)

```python
r = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8)

for week in r['timeline']:
    print(week['week'], week['resistant_fraction'], week['mic_fold_change'])
print(r['failure_week'])
```

`n_weeks=8` returns **9** entries — week 0 is the untreated baseline. Despite
the name, `resistant_fraction` and its siblings are **percentages (0–100)**.
See [Known issues](docs/known-issues.md).

### Inspect what loaded

```python
amrpredict.status()
# {'version': '0.3.0',
#  'lgbm_forecasting':  {'trained': True, 'run_id': 'D3_forecaster_deploy_v7', 'metrics': {...}},
#  'genome_resistance': {'trained': True, 'run_id': 'G_kmer_deploy', 'searches_genes': False, ...},
#  'trend_forecast':    {'trained': True, 'run_id': 'TL_timeline_ml', ...},
#  'rl_agent':          {'trained': True, 'drugs': ['ciprofloxacin', 'gentamicin', 'imipenem'], ...},
#  'mutation_timeline': {'trained': False, ...}}

amrpredict.antibiotics()            # the genome models' 111 antibiotics
amrpredict.antibiotics('forecast')  # also 'trend' and 'rl'
```

## Command line

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
amrpredict predict genome.fna ciprofloxacin            # --kmers or --genes to choose
amrpredict species genome.fna
amrpredict trend Salmonella ciprofloxacin --years 5
amrpredict plan ciprofloxacin --weeks 52
amrpredict timeline genome.fna ciprofloxacin --weeks 12
amrpredict antibiotics --model trend
amrpredict status
```

Output is JSON on stdout, so it composes. Unusable input (a short FASTA, a
drug the RL agent does not know) exits 0 with an `error` key, as the Python
API returns it:

```bash
amrpredict --compact forecast meropenem --taxon-id 287 | jq -r .prediction
cat genome.fna | amrpredict predict - ciprofloxacin
```

Diagnostics go through `logging` to stderr, never stdout. To see them:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Using your own models

Every entry point takes `model_dir`, a folder laid out like the bundled one
(`amrpredict.default_model_dir()`): the forecaster's files at the top
(`amr_lgbm_final_model.txt`, the `*.joblib` rate tables, `lgbm_metrics.json`),
and the folders `genome/`, `genome_genes/`, `timeline_ml/` and `rl_agent/`.
They are produced by the main project's `experiments/promote.py`.

```python
amrpredict.forecast('ciprofloxacin', taxon_id=562, model_dir='/path/to/models')
```

## Performance notes

Models load lazily on first use and are cached process-wide, so the first call
pays about 1–2 s and later calls are fast. A complete genome takes about a
second with the k-mer model; the gene model adds AMRFinderPlus's 10–45 s.
To release the memory: `amrpredict.registry.reset()`.

## Changes in 0.3.0

- `predict_fasta()` uses the web app's genome models: the gene model (lab AUC
  0.977) with AMRFinderPlus, else the k-mer LightGBM (0.935). The July k-mer
  RandomForest (0.695 on genomes it never saw) is removed, and with it the
  scikit-learn dependency. `predict_fasta()` now needs a complete genome
  (100,000 bp or more) and reads all of it.
- New: `forecast_trend()` and `trend_series()` (timeline ML model),
  `plan_treatment()` (RL agent), `identify_species()`; CLI commands `trend`,
  `plan` and `species`.
- `status()` reports `genome_resistance`, `trend_forecast` and `rl_agent`
  (`kmer_resistance` is gone); `antibiotics()` takes the model to ask.

## Development

```bash
pip install -e ".[dev]"
pytest
python -m build && twine check dist/*
```

## Documentation

- [Quickstart](docs/quickstart.md)
- [API reference](docs/api-reference.md)
- [CLI reference](docs/cli.md)
- [Known issues](docs/known-issues.md)

## License

MIT — see [LICENSE](LICENSE).
