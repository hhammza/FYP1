# Quickstart

Five minutes from install to a prediction.

## 1. Install

```bash
pip install amrpredict
```

Nothing else to download — the trained models ship inside the package.

## 2. Check it loaded

```bash
amrpredict status
```

```json
{
  "version": "0.1.0",
  "lgbm_forecasting":  { "trained": true,  "model_type": "LightGBM Gradient Boosting" },
  "kmer_resistance":   { "trained": true,  "antibiotics_known": 62 },
  "mutation_timeline": { "trained": false, "model_type": "Biological Simulation" }
}
```

`mutation_timeline` reporting `false` is expected — it is a simulation, not a
trained model.

## 3. Your first prediction

You have an *E. coli* isolate (NCBI taxon `562`) with a ciprofloxacin MIC of
4 mg/L. Is it resistant?

```python
import amrpredict

r = amrpredict.forecast('ciprofloxacin', taxon_id=562, mic_value=4)

print(r['prediction'])   # Susceptible
print(r['confidence'])   # 89.9
```

Same thing from the shell:

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
```

## 4. From a genome instead

If you have sequence rather than metadata:

```python
with open('genome.fasta') as fh:
    r = amrpredict.predict_fasta(fh.read(), 'ciprofloxacin')

print(r['prediction'], r['gc_content'])
```

Always check for an error first — short or empty input returns an error dict
rather than raising:

```python
if 'error' in r:
    print('bad input:', r['error'])
else:
    print(r['prediction'])
```

## 5. Choosing a threshold

`threshold` is the probability at or above which a sample is called
**Resistant**. It is the main knob you have.

| Threshold | Effect | Use when |
|---|---|---|
| 0.3 | More resistance calls; higher sensitivity | Missing resistance is costly |
| 0.4 | Default for `forecast()` | General use |
| 0.5 | Default for `predict_fasta()` | Balanced |
| 0.7 | Fewer, higher-confidence calls | False alarms are costly |

```python
amrpredict.forecast('ciprofloxacin', taxon_id=562, threshold=0.3)
```

The underlying probability does not change — only the label derived from it.

## 6. Which function do I want?

```
Do you have the genome sequence?
├── Yes → predict_fasta()
│         └── want resistance evolution over time? → simulate_timeline()
└── No, just organism + antibiotic (maybe an MIC)
          └── forecast()
```

`forecast()` is the strongest model and the one to prefer when you have an MIC
value. `predict_fasta()` is for when sequence is all you have.

## Next

- [API reference](api-reference.md) — every argument and return field
- [CLI reference](cli.md)
- [Known issues](known-issues.md) — read before quoting numbers in a report
