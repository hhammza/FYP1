"""Turn results/registry.csv into a Markdown comparison table.

    python experiments/report.py                 # print to stdout
    python experiments/report.py --out RESULTS.md
    python experiments/report.py --per-antibiotic A2_oof_grouped

The table is ordered by AUPRC rather than AUC because the classes are
imbalanced; AUC is still shown with its bootstrap interval so overlapping runs
are visibly not different.
"""
import argparse
import json
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, 'results', 'registry.csv')


def comparison_table():
    if not os.path.exists(REGISTRY):
        return '_No runs yet._'
    df = pd.read_csv(REGISTRY).sort_values('auc_pr', ascending=False)

    lines = [
        '| Run | Split | Encoding | Model | AUC-ROC [95% CI] | AUPRC | F1 | VME | ME | Brier | Thr |',
        '|---|---|---|---|---|---|---|---|---|---|---|',
    ]
    for _, r in df.iterrows():
        lines.append(
            f"| `{r['id']}` | {r['split']} | {r['encoding']} | {r['model']} "
            f"| {r['auc_roc']:.4f} [{r['auc_ci_low']:.4f}-{r['auc_ci_high']:.4f}] "
            f"| {r['auc_pr']:.4f} | {r['f1']:.4f} "
            f"| {r['very_major_error']:.1%} | {r['major_error']:.1%} "
            f"| {r['brier']:.4f} | {r['threshold']:.2f} |")
    return '\n'.join(lines)


def descriptions():
    if not os.path.exists(REGISTRY):
        return ''
    df = pd.read_csv(REGISTRY)
    return '\n'.join(f"- `{r['id']}` - {r['description']}" for _, r in df.iterrows())


def per_antibiotic(run_id, limit=15):
    path = os.path.join(HERE, 'results', run_id, 'metrics.json')
    with open(path) as fh:
        payload = json.load(fh)
    rows = payload['per_antibiotic']
    lines = ['| Antibiotic | n | Prevalence | AUC | VME | ME |', '|---|---|---|---|---|---|']
    for r in rows[:limit]:
        lines.append(f"| {r['group']} | {r['n']:,} | {r['prevalence']:.1%} "
                     f"| {r['auc_roc']:.3f} | {r['very_major_error']:.1%} "
                     f"| {r['major_error']:.1%} |")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', help='write Markdown here instead of stdout')
    ap.add_argument('--per-antibiotic', metavar='RUN_ID',
                    help='weakest antibiotics for one run')
    args = ap.parse_args()

    if args.per_antibiotic:
        text = (f'### Weakest antibiotics - `{args.per_antibiotic}`\n\n'
                + per_antibiotic(args.per_antibiotic))
    else:
        text = ('# Experiment results\n\n' + comparison_table()
                + '\n\n## Runs\n\n' + descriptions() + '\n')

    if args.out:
        with open(args.out, 'w') as fh:
            fh.write(text + '\n')
        print(f'wrote {args.out}')
    else:
        print(text)


if __name__ == '__main__':
    main()
