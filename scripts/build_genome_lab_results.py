"""Laboratory resistance results per BV-BRC genome, for the "fill from Genome
ID" helper on /forecast (backend/api/genome_lab_results.json.gz).

    python scripts/build_genome_lab_results.py [--data Data/amr_output]

Keeps only rows BV-BRC marks `Evidence = Laboratory Method`: computer-predicted
labels were made from the genome and are not a result to compare a prediction
with. Per genome: antibiotic (canonical), phenotype, MIC sign, value, unit and
method. Disk-diffusion results are in mm, not MICs, so the unit is kept and the
page shows a value as a MIC only when it is in mg/L. The model never reads this
file.
"""
import argparse
import collections
import glob
import gzip
import json
import os
import sys

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ml_models.common import normalize_antibiotic  # noqa: E402

COLS = ['Genome ID', 'Antibiotic', 'Resistant Phenotype', 'Measurement Sign', 'Measurement Value',
        'Measurement Unit', 'Laboratory Typing Method', 'Evidence']


def clean(v):
    return '' if pd.isna(v) else str(v).strip()


def main(data_dir, out_path):
    files = sorted(glob.glob(os.path.join(data_dir, '*.csv')))
    if not files:
        sys.exit(f'no CSV files in {data_dir}')
    genomes = collections.defaultdict(set)
    rows = lab = 0
    for i, path in enumerate(files, 1):
        df = pd.read_csv(path, usecols=COLS, dtype=str, on_bad_lines='skip')
        rows += len(df)
        df = df[df['Evidence'].str.strip().eq('Laboratory Method')]
        lab += len(df)
        for gid, ab, ph, sign, val, unit, method, _ in df.itertuples(index=False, name=None):
            ab = normalize_antibiotic(ab)
            gid = clean(gid)
            if not ab or not gid:
                continue
            genomes[gid].add((ab, clean(ph), clean(sign), clean(val), clean(unit), clean(method)))
        if i % 500 == 0:
            print(f'  {i}/{len(files)} files', flush=True)
    out = {
        'source': 'BV-BRC laboratory results (Evidence = Laboratory Method), '
                  + os.path.relpath(data_dir, ROOT).replace(os.sep, '/'),
        'columns': ['antibiotic', 'phenotype', 'sign', 'value', 'unit', 'method'],
        'genomes': {g: sorted(r) for g, r in genomes.items()},
    }
    with gzip.open(out_path, 'wt', encoding='utf-8') as fh:
        json.dump(out, fh, separators=(',', ':'))
    n = sum(len(r) for r in genomes.values())
    print(f'{rows:,} rows read, {lab:,} lab rows; {len(genomes):,} genomes, {n:,} distinct results; '
          f'{os.path.getsize(out_path) / 1e6:.1f} MB -> {os.path.relpath(out_path, ROOT)}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--data', default=os.path.join(ROOT, 'Data', 'amr_output'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'backend', 'api', 'genome_lab_results.json.gz'))
    a = ap.parse_args()
    main(a.data, a.out)
