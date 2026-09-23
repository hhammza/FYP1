# amrpredict

Antimicrobial resistance prediction from bacterial genomes and MIC metadata.

Three models behind one flat Python API and a command-line tool. The trained
artifacts ship inside the package, so there is nothing to download and it works
offline.

```python
import amrpredict

amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)
# {'prediction': 'Susceptible', 'probability': 0.1005, 'confidence': 89.9,
#  'drug_class': 'fluoroquinolone', 'model_used': 'LightGBM (trained)', ...}
```

## Install

```bash
pip install amrpredict
```

From a checkout:

```bash
pip install -e ".[dev]"
```

Requires Python 3.9+. The package is ~7 MB because the model artifacts are
bundled.

## The three models

| Function | Model | Input | Trained |
|---|---|---|---|
| `forecast()` | LightGBM gradient boosting | Antibiotic + taxonomy + MIC | Yes |
| `predict_fasta()` | RandomForest on 4-mer spectra | Genome FASTA + antibiotic | Yes |
| `simulate_timeline()` | Biological simulation | Genome FASTA + antibiotic | **No** — see below |

`simulate_timeline()` is a deterministic simulation, not a learned model. It has
no AUC or accuracy score, and its output is illustrative rather than predictive.
`status()` reports `trained: False` for it, deliberately.

## Usage

### Forecast from metadata

Use when you have organism metadata and, ideally, an MIC measurement.

```python
import amrpredict

r = amrpredict.forecast(
    'ciprofloxacin',
    taxon_id=562,           # NCBI taxonomy ID — 562 is E. coli
    mic_value=4,            # mg/L
    mic_sign='=',           # '=', '>', '<=' ...
    genus='Escherichia',
    species='coli',
    threshold=0.40,         # probability at/above which the call is Resistant
)

print(r['prediction'])      # 'Susceptible'
print(r['probability'])     # 0.1005
print(r['confidence'])      # 89.9
```

Every argument except `antibiotic` is optional and keyword-only. With fewer
inputs the model falls back to population-level resistance rates, so accuracy
degrades but the call still succeeds.

### Predict from a genome

Use when you have a sequence. The FASTA is parsed to plain ACGT, uppercased,
and capped at 500,000 bp.

```python
with open('genome.fasta') as fh:
    fasta = fh.read()

r = amrpredict.predict_fasta(fasta, 'ciprofloxacin', threshold=0.5)

print(r['prediction'])       # 'Susceptible'
print(r['gc_content'])       # 50.43  (percent)
print(r['sequence_length'])  # 3000
print(r['top_kmers'][0])     # {'kmer': 'CCCA', 'frequency': 0.00667}
```

Sequences under 100 bp return an error dict instead of a prediction:

```python
r = amrpredict.predict_fasta('>x\nACGT\n', 'ciprofloxacin')
# {'error': 'FASTA sequence too short (minimum 100 bp)', 'sequence_length': 4}
```

Check for `'error'` before reading `'prediction'`. The function does not raise
on malformed input.

### Simulate resistance evolution

```python
r = amrpredict.simulate_timeline(fasta, 'ciprofloxacin', n_weeks=8)

for week in r['timeline']:
    print(week['week'], week['resistant_fraction'], week['mic_fold_change'])

print(r['failure_week'])            # week treatment stops being effective
print(r['resistance_genes'])        # gyrA, gyrB, parC ...
print(r['mutation_hotspots'])       # positions and substitution types
```

`n_weeks=8` returns **9** entries — week 0 is the untreated baseline.

Despite the name, `resistant_fraction` and its siblings are **percentages
(0–100)**, not fractions. See [Known issues](docs/known-issues.md).

### Inspect what loaded

```python
amrpredict.status()
# {'version': '0.1.0',
#  'lgbm_forecasting':   {'trained': True,  ...},
#  'kmer_resistance':    {'trained': True,  ...},
#  'mutation_timeline':  {'trained': False, ...}}

amrpredict.antibiotics()   # 62 names the k-mer model knows
```

## Command line

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
amrpredict predict genome.fasta ciprofloxacin --threshold 0.6
amrpredict timeline genome.fasta ciprofloxacin --weeks 12
amrpredict antibiotics
amrpredict status
```

Output is JSON on stdout, so it composes:

```bash
amrpredict --compact forecast meropenem --taxon-id 287 | jq -r .prediction
cat genome.fasta | amrpredict predict - ciprofloxacin
```

Diagnostics go through `logging` to stderr, never stdout, so piping stays clean.
To see them:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Using your own models

Every entry point takes `model_dir`:

```python
amrpredict.forecast('ciprofloxacin', taxon_id=562, model_dir='/path/to/models')
```

```bash
amrpredict --model-dir /path/to/models status
```

The directory must contain `amr_lgbm_final_model.txt`,
`kmer_resistance_model.pkl`, and the `*.joblib` rate tables. Retrain them with
`backend/train_models.py` in the main project.

## Performance notes

Models load lazily on first use and are cached process-wide, so the first call
pays ~1–2 s and later calls are fast. In a worker process, call the function you
need once at startup to move that cost out of the request path.

To release the memory:

```python
amrpredict.registry.reset()
```

## scikit-learn version

The k-mer model is a pickled scikit-learn estimator, so the dependency is
pinned to `>=1.3,<2.0`. Unpickling across a major version is not supported and
would silently produce wrong numbers rather than failing.

The artifacts were built with scikit-learn **1.6.1**. Installing a different
1.x will still work but raises `InconsistentVersionWarning`. To silence it,
pin `scikit-learn==1.6.1`, or retrain the model against your version.

The LightGBM model is unaffected — it uses LightGBM's own version-stable text
format.

## Development

```bash
pip install -e ".[dev]"
pytest                          # 29 passed, 1 xfailed
python -m build && twine check dist/*
```

## Documentation

- [Quickstart](docs/quickstart.md)
- [API reference](docs/api-reference.md)
- [CLI reference](docs/cli.md)
- [Known issues](docs/known-issues.md)

## License

MIT — see [LICENSE](LICENSE).
