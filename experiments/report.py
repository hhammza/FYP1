"""Turn results/registry.csv into a Markdown comparison table.

    python experiments/report.py                 # print to stdout
    python experiments/report.py --out RESULTS.md
    python experiments/report.py --per-antibiotic A2_oof_grouped
    python experiments/report.py --seeds          # mean +- sd over split seeds

The table is ordered by AUPRC rather than AUC because the classes are
imbalanced; AUC is still shown with its bootstrap interval so overlapping runs
are visibly not different.
"""
import argparse
import json
import os

import pandas as pd
import lib  # noqa: E402,F401  (UTF-8 output on Windows; see lib/__init__.py)

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(HERE, 'results', 'registry.csv')

# Cleaning version of runs made before the registry recorded one. Only the
# two past deployments are kept on older data, as a record of what was served.
PRE_COLUMN_VERSIONS = {'D1_forecaster_deploy': 'v3', 'D2_forecaster_deploy': 'v4'}


def test_metric(run_id, key):
    """One test-set number from a run's metrics.json, for registry rows
    written before the registry had that column."""
    path = os.path.join(HERE, 'results', run_id, 'metrics.json')
    try:
        with open(path) as fh:
            return json.load(fh)['test'].get(key, float('nan'))
    except (OSError, KeyError, ValueError):
        return float('nan')


def pct(v):
    return 'n/a' if pd.isna(v) else f'{v:.1%}'


def comparison_table():
    if not os.path.exists(REGISTRY):
        return '_No runs yet._'
    df = pd.read_csv(REGISTRY).sort_values('auc_pr', ascending=False)
    # Accuracy, recall (sensitivity) and specificity: the registry has them for
    # runs since 2026-09-30; older rows read them from metrics.json
    for key in ('accuracy', 'sensitivity', 'specificity'):
        if key not in df:
            df[key] = float('nan')
        missing = df[key].isna()
        df.loc[missing, key] = [test_metric(i, key) for i in df.loc[missing, 'id']]
    if 'clean_version' not in df:
        df['clean_version'] = None

    if 'auc_roc_lab' not in df:
        df['auc_roc_lab'] = float('nan')
        df['n_lab'] = 0

    lines = [
        '| Run | Data | Split | Encoding | Model | AUC-ROC [95% CI] | Lab AUC (n) | AUPRC | F1 '
        '| Accuracy | Recall | Specificity | VME | ME | Brier | Thr |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|',
    ]
    for _, r in df.iterrows():
        version = r['clean_version']
        if pd.isna(version):
            version = PRE_COLUMN_VERSIONS.get(r['id'], '?')
        lab = ('n/a' if pd.isna(r['auc_roc_lab'])
               else f"{r['auc_roc_lab']:.4f} ({int(r['n_lab']):,})")
        lines.append(
            f"| `{r['id']}` | {version} | {r['split']} | {r['encoding']} | {r['model']} "
            f"| {r['auc_roc']:.4f} [{r['auc_ci_low']:.4f}-{r['auc_ci_high']:.4f}] | {lab} "
            f"| {r['auc_pr']:.4f} | {r['f1']:.4f} "
            f"| {pct(r['accuracy'])} | {pct(r['sensitivity'])} | {pct(r['specificity'])} "
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


def seed_table():
    """Runs repeated with other split seeds (<id>_s1, <id>_s2 beside <id>,
    which used seed 42): mean and sd of each metric across the seeds. The sd
    is the split-to-split spread that a single run's bootstrap CI does not show."""
    if not os.path.exists(REGISTRY):
        return '_No runs yet._'
    df = pd.read_csv(REGISTRY).set_index('id')
    bases = sorted({i.rsplit('_s', 1)[0] for i in df.index if i.rsplit('_s', 1)[-1].isdigit()})
    lines = ['| Run | Seeds | AUC mean ± sd | Lab AUC mean ± sd | AUPRC mean ± sd | VME mean ± sd | ME mean ± sd |',
             '|---|---|---|---|---|---|---|']
    for base in bases:
        ids = [i for i in [base] + [f'{base}_s{k}' for k in range(1, 10)] if i in df.index]
        if len(ids) < 2:
            continue
        rows = df.loc[ids]

        def ms(col, fmt='{:.4f}'):
            v = rows[col].dropna()
            if v.empty:
                return 'n/a'
            return f"{fmt.format(v.mean())} ± {fmt.format(v.std(ddof=1) if len(v) > 1 else 0)}"
        lines.append(f"| `{base}` | {len(ids)} | {ms('auc_roc')} | {ms('auc_roc_lab')} | {ms('auc_pr')} "
                     f"| {ms('very_major_error', '{:.3f}')} | {ms('major_error', '{:.3f}')} |")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', help='write Markdown here instead of stdout')
    ap.add_argument('--per-antibiotic', metavar='RUN_ID',
                    help='weakest antibiotics for one run')
    ap.add_argument('--seeds', action='store_true', help='mean +- sd over split seeds')
    args = ap.parse_args()

    if args.seeds:
        text = '### Seed variation (split seeds 42, 1, 2)\n\n' + seed_table()
    elif args.per_antibiotic:
        text = (f'### Weakest antibiotics - `{args.per_antibiotic}`\n\n'
                + per_antibiotic(args.per_antibiotic))
    else:
        text = ('# Experiment results\n\n' + comparison_table()
                + '\n\n## Runs\n\n' + descriptions() + '\n')

    if args.out:
        with open(args.out, 'w', encoding='utf-8') as fh:
            fh.write(text + '\n')
        print(f'wrote {args.out}')
    else:
        print(text)


if __name__ == '__main__':
    main()
