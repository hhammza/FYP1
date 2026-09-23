# CLI reference

```
amrpredict [--compact] [--model-dir DIR] <command> [options]
```

Every command prints JSON to stdout. Diagnostics go to stderr via `logging`,
so output always pipes cleanly.

## Global options

| Option | Meaning |
|---|---|
| `--version` | Print version and exit |
| `--compact` | Single-line JSON instead of indented |
| `--model-dir DIR` | Use artifacts from `DIR` instead of the bundled ones |

## `forecast`

```
amrpredict forecast ANTIBIOTIC [--taxon-id N] [--mic-value F] [--mic-sign S]
                               [--genus G] [--species S] [--threshold F]
```

```bash
amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4
```

```json
{
  "prediction": "Susceptible",
  "probability": 0.1005,
  "confidence": 89.9,
  "antibiotic": "ciprofloxacin",
  "drug_class": "fluoroquinolone",
  "model_used": "LightGBM (trained)",
  "threshold": 0.4
}
```

Default threshold `0.40`.

## `predict`

```
amrpredict predict FASTA ANTIBIOTIC [--threshold F]
```

`FASTA` is a path, or `-` to read stdin.

```bash
amrpredict predict genome.fasta ciprofloxacin
cat genome.fasta | amrpredict predict - ciprofloxacin --threshold 0.6
```

Default threshold `0.50`.

## `timeline`

```
amrpredict timeline FASTA ANTIBIOTIC [--weeks N]
```

```bash
amrpredict timeline genome.fasta ciprofloxacin --weeks 12
```

Returns `weeks + 1` entries — week 0 is the baseline. Output is a simulation,
not a prediction.

## `antibiotics`

```bash
amrpredict antibiotics
```

JSON array of the 62 names the k-mer model knows.

## `status`

```bash
amrpredict status
```

Which models loaded, and the library version.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Invalid value (bad argument, unusable input) |
| `2` | File not found |

Note that a FASTA which is too short is **not** an error exit — it returns `0`
with an `error` key in the JSON, matching the Python API. Check the payload:

```bash
amrpredict --compact predict tiny.fasta ciprofloxacin | jq -e '.error // empty'
```

## Recipes

Just the call:

```bash
amrpredict --compact forecast meropenem --taxon-id 287 | jq -r .prediction
```

Sweep a panel of antibiotics for one isolate:

```bash
for ab in ciprofloxacin meropenem gentamicin colistin; do
  printf '%-16s %s\n' "$ab" \
    "$(amrpredict --compact forecast "$ab" --taxon-id 562 | jq -r .prediction)"
done
```

Flag only resistant results across a directory of genomes:

```bash
for f in genomes/*.fasta; do
  r=$(amrpredict --compact predict "$f" ciprofloxacin)
  [ "$(echo "$r" | jq -r .prediction)" = "Resistant" ] && echo "$f: $(echo "$r" | jq -r .probability)"
done
```

Turn a timeline into CSV:

```bash
amrpredict timeline genome.fasta ciprofloxacin --weeks 8 \
  | jq -r '.timeline[] | [.week, .resistant_fraction, .mic_fold_change] | @csv'
```

See diagnostics while debugging:

```bash
PYTHONWARNINGS=default amrpredict status 2>&1 >/dev/null
```
