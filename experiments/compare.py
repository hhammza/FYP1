"""Is run A really better than run B? DeLong, McNemar and a paired genome
bootstrap on the test rows the two runs share.

    python experiments/compare.py B6L_genes_v6 B4L_kmer4_lgbm_v6 --lab
    python experiments/compare.py A6_lab_only_v7 A_ablation_drug_only_v7
    python experiments/compare.py --pairs                # the report's pairs
    python experiments/compare.py --pairs --out results/significance.md

Rows are matched on (genome_id, antibiotic), so both runs must have used the
same split; a run's yes/no calls use its own threshold from metrics.json.
--lab keeps lab-confirmed rows only (the number to quote for genome models,
whose computational labels are partly circular). Needs each run's
predictions.csv, which is not in git: re-run a run locally to get it.
"""
import argparse
import json
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from lib import significance  # noqa: E402

RESULTS = os.path.join(HERE, 'results')

# (A, B, lab only): the comparisons the report and the papers quote
PAIRS = [
    ('B6L_genes_v6', 'B4L_kmer4_lgbm_v6', True),          # genes vs k-mers
    ('B7L_genes_kmers_v6', 'B6L_genes_v6', True),         # does adding k-mers help?
    ('B6L_genes_v6', 'B6L_base_taxonomy_v6', True),       # genes vs taxonomy only
    ('B6L_genes_v6', 'B6L_base_drug_v6', True),           # genes vs drug only
    ('A2_oof_grouped_v7', 'A_ablation_drug_only_v7', False),
    ('A6_lab_only_v7', 'A6b_lab_only_no_mic_v7', False),  # what MIC adds
    ('A10_monotonic_mic_v7', 'A2_oof_grouped_v7', False),
]


def load(run_id):
    path = os.path.join(RESULTS, run_id, 'predictions.csv')
    if not os.path.exists(path):
        raise FileNotFoundError(f'{run_id}: no predictions.csv (re-run it: python experiments/run.py '
                                f'experiments/configs/{run_id}.json)')
    df = pd.read_csv(path, dtype={'genome_id': str})
    with open(os.path.join(RESULTS, run_id, 'metrics.json')) as fh:
        threshold = json.load(fh)['test']['threshold']
    return df, threshold


def compare(run_a, run_b, lab=False, n_boot=1000):
    a, thr_a = load(run_a)
    b, thr_b = load(run_b)
    key = ['genome_id', 'antibiotic']
    if a.duplicated(key).any() or b.duplicated(key).any():
        raise ValueError('(genome_id, antibiotic) is not unique in predictions.csv')
    m = a.merge(b[key + ['y_true', 'y_score']], on=key, suffixes=('_a', '_b'))
    if (m['y_true_a'] != m['y_true_b']).any():
        raise ValueError('labels differ on shared rows: the runs used different data')
    shared = len(m) / max(len(a), len(b))
    if shared < 0.95:
        print(f'[compare] warning: only {shared:.0%} of rows shared; different splits?')
    if lab:
        m = m[m['label_source'] == 'lab']
    y = m['y_true_a'].to_numpy()
    out = {
        'a': run_a, 'b': run_b, 'lab_only': lab, 'rows': int(len(m)),
        'genomes': int(m['genome_id'].nunique()),
        'delong': significance.delong(y, m['y_score_a'], m['y_score_b']),
        'mcnemar': significance.mcnemar(y, m['y_score_a'] >= thr_a, m['y_score_b'] >= thr_b),
        'bootstrap': significance.paired_bootstrap(y, m['y_score_a'], m['y_score_b'],
                                                   m['genome_id'], n_boot=n_boot),
        'thresholds': [thr_a, thr_b],
    }
    return out


def p_text(p):
    return '< 0.0001' if p < 1e-4 else f'{p:.4f}'


def table(results):
    lines = ['| A | B | Rows (genomes) | AUC A | AUC B | Diff [DeLong 95% CI] | DeLong p '
             '| Genome bootstrap 95% CI | McNemar: only A right / only B right | McNemar p |',
             '|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        d, mc, bs = r['delong'], r['mcnemar'], r['bootstrap']
        lab = ' (lab)' if r['lab_only'] else ''
        lines.append(
            f"| `{r['a']}`{lab} | `{r['b']}` | {r['rows']:,} ({r['genomes']:,}) "
            f"| {d['auc_a']:.4f} | {d['auc_b']:.4f} "
            f"| {d['diff']:+.4f} [{d['ci'][0]:+.4f}, {d['ci'][1]:+.4f}] | {p_text(d['p'])} "
            f"| [{bs['ci'][0]:+.4f}, {bs['ci'][1]:+.4f}] "
            f"| {mc['only_a_right']:,} / {mc['only_b_right']:,} | {p_text(mc['p'])} |")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='*', help='two run ids: A B')
    ap.add_argument('--lab', action='store_true', help='lab-confirmed rows only')
    ap.add_argument('--pairs', action='store_true', help='every pair in PAIRS')
    ap.add_argument('--n-boot', type=int, default=1000)
    ap.add_argument('--out', help='write the Markdown table here')
    args = ap.parse_args()

    if args.pairs:
        todo = PAIRS
    elif len(args.runs) == 2:
        todo = [(args.runs[0], args.runs[1], args.lab)]
    else:
        ap.error('give two run ids, or --pairs')

    results = []
    for a, b, lab in todo:
        try:
            r = compare(a, b, lab, args.n_boot)
        except (FileNotFoundError, ValueError) as e:
            print(f'[compare] skipped {a} vs {b}: {e}')
            continue
        results.append(r)
        print(f"[compare] {a} vs {b}: AUC diff {r['delong']['diff']:+.4f}, "
              f"DeLong p {p_text(r['delong']['p'])}, McNemar p {p_text(r['mcnemar']['p'])}")

    text = ('# Significance of the main comparisons\n\nBuilt by `experiments/compare.py --pairs`. '
            'DeLong and McNemar treat rows as independent; rows cluster by genome, so the genome '
            'bootstrap interval is the one to quote when they disagree.\n\n' + table(results) + '\n')
    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            fh.write(text)
        with open(os.path.splitext(args.out)[0] + '.json', 'w') as fh:
            json.dump(results, fh, indent=2)
        print(f'[compare] wrote {args.out}')
    else:
        print('\n' + table(results))


if __name__ == '__main__':
    main()
