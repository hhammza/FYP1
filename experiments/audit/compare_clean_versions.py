"""Compare two cleaned datasets (default v5 and v6) and write
experiments/audit/results/<old>_vs_<new>.md.

Reads the cached cleaned frames in experiments/cache/, so build both first
(data_prep.get_clean). Run from the project root:
    .venv/bin/python experiments/audit/compare_clean_versions.py
"""
import argparse
import os
import pickle

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(os.path.dirname(HERE), 'cache')
CACHES = {'v5': 'clean_v5_amr_output_norm.pkl', 'v6': 'clean_v6_amr_full_norm.pkl',
          'v7': 'clean_v7_amr_full_norm.pkl'}


def load(version):
    with open(os.path.join(CACHE, CACHES[version]), 'rb') as fh:
        return pickle.load(fh)


def summary(df):
    lab = df[df['is_lab_confirmed'] == 1]
    return {
        'Rows': len(df),
        'Genomes': df['Genome ID'].nunique(),
        'Lab rows': len(lab),
        'Lab-tested genomes': lab['Genome ID'].nunique(),
        'Antibiotics': df['Antibiotic'].nunique(),
        'Genera': df['genus'].nunique(),
        'Species taxa': df['species_taxon_id'].nunique(),
        'Resistant share, all rows': df['target'].mean(),
        'Resistant share, lab rows': lab['target'].mean(),
        'Rows with an MIC': df['has_mic'].mean(),
        'Lab share of rows': len(lab) / len(df),
    }


def fmt(v):
    if isinstance(v, float):
        return f'{100 * v:.1f}%'
    return f'{v:,}'


def by_genus(old, new, lab_only, top=15):
    if lab_only:
        old, new = old[old['is_lab_confirmed'] == 1], new[new['is_lab_confirmed'] == 1]
    t = pd.DataFrame({'old': old['genus'].value_counts(), 'new': new['genus'].value_counts()})
    t = t.fillna(0).astype(int).sort_values('new', ascending=False)
    return t.head(top), t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--old', default='v5')
    ap.add_argument('--new', default='v6')
    args = ap.parse_args()
    old, new = load(args.old), load(args.new)
    a, b = summary(old), summary(new)

    lines = [f'# Cleaned data: {args.old} vs {args.new}', '',
             f'{args.old}: built from `Data/amr_output/`. '
             f'{args.new}: built from `Data/amr_full/` (2026-09-29). '
             'Same cleaning code; only the input files differ.', '',
             f'Built by `experiments/audit/compare_clean_versions.py`.', '',
             '## Overall', '',
             f'| | {args.old} | {args.new} | Change |', '| --- | --- | --- | --- |']
    for k in a:
        if isinstance(a[k], float):
            change = f'{100 * (b[k] - a[k]):+.1f} points'
        else:
            change = f'x{b[k] / a[k]:.2f}' if a[k] else 'new'
        lines.append(f'| {k} | {fmt(a[k])} | {fmt(b[k])} | {change} |')

    for lab_only, title in ((False, 'All rows'), (True, 'Lab rows')):
        head, full = by_genus(old, new, lab_only)
        gone = full[(full['old'] > 0) & (full['new'] == 0)]
        lines += ['', f'## {title} by genus (top 15 in {args.new})', '',
                  f'| Genus | {args.old} | {args.new} |', '| --- | --- | --- |']
        lines += [f'| *{g}* | {r.old:,} | {r.new:,} |' for g, r in head.iterrows()]
        if len(gone):
            lines += ['', f'Genera in {args.old} but not in {args.new}: '
                      + ', '.join(f'*{g}* ({r.old:,})' for g, r in gone.iterrows())]

    out = os.path.join(HERE, 'results', f'{args.old}_vs_{args.new}.md')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nwrote {os.path.relpath(out)}')


if __name__ == '__main__':
    main()
