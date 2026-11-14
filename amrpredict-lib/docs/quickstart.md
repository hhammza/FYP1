# Quickstart

Five minutes from install to a prediction.

## 1. Install

```bash
pip install amrpredict
```

Nothing else to download — the trained models ship inside the package. For
the gene model, also install NCBI AMRFinderPlus (`amrfinder` on your PATH);
without it, genome predictions use the k-mer model.

## 2. Check it loaded

```bash
amrpredict status
```

```json
{
  "version": "0.3.0",
  "lgbm_forecasting":  { "trained": true,  "run_id": "D3_forecaster_deploy_v7" },
  "genome_resistance": { "trained": true,  "run_id": "G_kmer_deploy", "searches_genes": false },
  "trend_forecast":    { "trained": true,  "run_id": "TL_timeline_ml" },
  "rl_agent":          { "trained": true,  "drugs": ["ciprofloxacin", "gentamicin", "imipenem"] },
  "mutation_timeline": { "trained": false, "model_type": "Biological Simulation" }
}
```

`mutation_timeline` reporting `false` is expected — it is a simulation, not a
trained model. `searches_genes` is `true` once AMRFinderPlus is installed.

## 3. Your first prediction

You have an *E. coli* isolate (NCBI taxon `562`) with a ciprofloxacin MIC of
4 mg/L. Is it resistant?

```python
import amrpredict

r = amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)

print(r['prediction'])   # Resistant
print(r['probability'])  # 0.7055
```

Same thing from the shell:

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
```

## 4. From a genome instead

If you have a complete genome assembly rather than metadata:

```python
with open('genome.fna') as fh:
    fasta = fh.read()

r = amrpredict.predict_fasta(fasta, 'ciprofloxacin')
print(r['prediction'], r['model_used'])
print(amrpredict.identify_species(fasta)['species'])
```

Always check for an error first — short or empty input (under 100,000 bp)
returns an error dict rather than raising:

```python
if 'error' in r:
    print('bad input:', r['error'])
else:
    print(r['prediction'])
```

## 5. Where is resistance heading?

```python
r = amrpredict.forecast_trend('Salmonella', 'ciprofloxacin', years_ahead=5)
for f in r['forecast']:
    print(f['year'], f['resistant_pct'], f'80%: {f["lo"]}-{f["hi"]}')
```

`amrpredict.trend_series()` lists every genus and antibiotic with enough yearly
history.

## 6. Which drug, week by week?

```python
r = amrpredict.plan_treatment('ciprofloxacin', n_weeks=52)
print(r['best'])
print(r['policies'][0]['policy'][:8])   # the RL agent's first 8 weeks
```

The agent learned on a simulation, not patients: a tool for exploring cycling
strategies.

## 7. Choosing a threshold

`threshold` is the probability at or above which a sample is called
**Resistant**. Each model's default was chosen on validation genomes to keep
very major errors (missed resistance) near 10%.

| Model | Default threshold |
|---|---|
| `forecast()` | 0.15 |
| `predict_fasta()`, k-mer model | 0.43 |
| `predict_fasta()`, gene model | 0.58 |

```python
amrpredict.forecast('ciprofloxacin', taxon_id=562, threshold=0.3)
```

A higher threshold gives fewer false alarms and more missed resistance. The
underlying probability does not change — only the label derived from it.

## 8. Which function do I want?

```
Do you have a complete genome assembly?
├── Yes → predict_fasta()      (identify_species() for the organism)
└── No, organism + antibiotic (maybe an MIC) → forecast()

Want the trend over the years for an organism and drug? → forecast_trend()
Want to compare drug cycling strategies?               → plan_treatment()
Want a week-by-week what-if under treatment?           → simulate_timeline()  (simulation)
```

## Next

- [API reference](api-reference.md) — every argument and return field
- [CLI reference](cli.md)
- [Known issues](known-issues.md) — read before quoting numbers in a report
