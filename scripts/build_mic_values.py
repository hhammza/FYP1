"""MIC values recorded in BV-BRC, per species, genus and antibiotic, for the
/forecast form's MIC suggestions (backend/api/mic_values.json).

    python scripts/build_mic_values.py [--data Data/amr_output]

Reads every CSV in the AMR folder (BV-BRC columns `Taxon ID`, `Antibiotic`,
`Measurement Value`, `Measurement Unit`), keeps MICs in mg/L, maps each Taxon
ID to its species and genus with backend/taxon_species.csv, and keeps the most
common values per (species, antibiotic), (genus, antibiotic) and antibiotic.
These are suggestions for the form only; the model never reads this file.
"""
import argparse
import collections
import csv
import glob
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ml_models.common import normalize_antibiotic  # noqa: E402

TOP = 12          # values kept per key, the most common ones
MIN_ROWS = 3      # a value must be seen this often to be suggested


def taxon_table():
    out = {}
    with open(os.path.join(ROOT, 'backend', 'taxon_species.csv'), encoding='utf-8') as fh:
        for r in csv.DictReader(fh):
            if r['species_name'] and r['genus_name']:
                out[int(r['taxon_id'])] = (r['species_name'].lower(), r['genus_name'].lower())
    return out


def fmt(v):
    return float(f'{v:.4g}')


def top_values(counter):
    common = [v for v, n in counter.most_common(TOP) if n >= MIN_ROWS]
    return sorted(fmt(v) for v in common)


def main(data_dir, out_path):
    taxa = taxon_table()
    by_sp, by_ge, by_ab = (collections.defaultdict(collections.Counter) for _ in range(3))
    files = sorted(glob.glob(os.path.join(data_dir, '*.csv')))
    if not files:
        sys.exit(f'no CSV files in {data_dir}')
    rows = used = 0
    for i, path in enumerate(files, 1):
        df = pd.read_csv(path, usecols=['Taxon ID', 'Antibiotic', 'Measurement Value', 'Measurement Unit'],
                         dtype=str, on_bad_lines='skip')
        rows += len(df)
        df = df[df['Measurement Unit'].str.strip().str.lower().eq('mg/l')]
        values = pd.to_numeric(df['Measurement Value'], errors='coerce')
        df = df.assign(v=values)[values.gt(0) & values.lt(10_000)]
        for tid, ab, v in zip(df['Taxon ID'], df['Antibiotic'], df['v']):
            ab = normalize_antibiotic(ab)
            if not ab:
                continue
            by_ab[ab][v] += 1
            try:
                names = taxa.get(int(float(tid)))
            except (TypeError, ValueError):
                names = None
            if names:
                by_sp[f'{names[0]}|{ab}'][v] += 1
                by_ge[f'{names[1]}|{ab}'][v] += 1
            used += 1
        if i % 500 == 0:
            print(f'  {i}/{len(files)} files', flush=True)
    result = {
        'source': 'BV-BRC MIC measurements in mg/L, ' + os.path.relpath(data_dir, ROOT).replace(os.sep, '/'),
        'note': 'Suggestions for the /forecast form; the model does not read this file',
        'rows_read': rows, 'mic_rows': used,
        'by_species': {k: top_values(c) for k, c in by_sp.items() if top_values(c)},
        'by_genus': {k: top_values(c) for k, c in by_ge.items() if top_values(c)},
        'by_antibiotic': {k: top_values(c) for k, c in by_ab.items() if top_values(c)},
    }
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, separators=(',', ':'), sort_keys=True)
    print(f'{rows:,} rows read, {used:,} MICs in mg/L; {len(result["by_species"])} species, '
          f'{len(result["by_genus"])} genus and {len(result["by_antibiotic"])} antibiotic keys; '
          f'{os.path.getsize(out_path) / 1e3:.0f} kB -> {os.path.relpath(out_path, ROOT)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default=os.path.join(ROOT, 'Data', 'amr_output'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'backend', 'api', 'mic_values.json'))
    a = ap.parse_args()
    main(a.data, a.out)
