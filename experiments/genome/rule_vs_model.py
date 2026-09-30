"""Gene-lookup rules vs the learned genes model, on the same lab test rows.

Reads the predictions of three runs made with the same genomes and split:
    B6R_gene_rule_class_v7   resistant when a gene or mutation of the drug's class is present
    B6R_gene_rule_key_v7     resistant when a named key determinant is present (16 drugs)
    B6L_genes_v7             LightGBM on the gene matrix (B6)
and writes experiments/genome/results/rule_vs_model.md: overall and per-drug
AUC, very major and major errors on lab rows, and a paired bootstrap over
genomes for the AUC gap. For Paper B in progress/RESEARCH_PLAN.md.

Run from the project root, after the three runs:
    .venv/bin/python experiments/genome/rule_vs_model.py
"""
import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(os.path.dirname(HERE), 'results')
OUT = os.path.join(HERE, 'results', 'rule_vs_model.md')
RUNS = {'class rule': 'B6R_gene_rule_class_v7', 'key rule': 'B6R_gene_rule_key_v7',
        'genes model': 'B6L_genes_v7'}
CONTEXT = {'B6L_base_drug_v6': 'antibiotic only',
           'B6L_nogenes_v6': 'antibiotic, drug class, genus',
           'B6L_base_taxonomy_v6': 'antibiotic, genus, species',
           'B6L_genes_v7': 'the genes model: antibiotic, drug class, genus, genes'}
N_BOOT = 1000
MIN_N = 100          # lab test rows per drug, with at least 10 of each class


def load():
    frames = []
    for name, run in RUNS.items():
        p = pd.read_csv(os.path.join(RESULTS, run, 'predictions.csv'), dtype={'genome_id': str})
        p = p[p['label_source'] == 'lab'].set_index(['genome_id', 'antibiotic'])
        frames.append(p['y_score'].rename(name))
        truth = p['y_true']
    df = pd.concat(frames + [truth], axis=1, join='inner').reset_index()
    return df


def errors(y, s, thr=0.5):
    call = s >= thr
    res, sus = y == 1, y == 0
    vme = (~call & res).sum() / max(res.sum(), 1)       # resistant called susceptible
    me = (call & sus).sum() / max(sus.sum(), 1)         # susceptible called resistant
    return vme, me


def paired_gap(df, a, b, seed=42):
    """AUC(b) - AUC(a) with a 95% interval, resampling genomes."""
    blocks = [g.index.to_numpy() for _, g in df.groupby('genome_id')]
    y, sa, sb = df['y_true'].to_numpy(), df[a].to_numpy(), df[b].to_numpy()
    rng = np.random.default_rng(seed)
    gaps = []
    for _ in range(N_BOOT):
        idx = np.concatenate([blocks[i] for i in rng.integers(0, len(blocks), len(blocks))])
        if len(np.unique(y[idx])) == 2:
            gaps.append(roc_auc_score(y[idx], sb[idx]) - roc_auc_score(y[idx], sa[idx]))
    gap = roc_auc_score(y, sb) - roc_auc_score(y, sa)
    lo, hi = np.percentile(gaps, [2.5, 97.5])
    return gap, lo, hi, float(np.mean(np.asarray(gaps) <= 0))


def main():
    df = load().reset_index(drop=True)
    y = df['y_true'].to_numpy()
    lines = ['# Gene-lookup rules vs the genes model (lab rows)', '',
             'Same genomes, split and lab test rows for all three: the lab-tested genome set, '
             'cleaning v7, plasmid-only records excluded, grouped by genome (seed 42). The rules '
             'learn nothing; they read AMRFinderPlus output the way a lab would. Built by '
             '`experiments/genome/rule_vs_model.py`.', '',
             f'{len(df):,} lab test rows, {df["genome_id"].nunique():,} genomes, '
             f'{df["antibiotic"].nunique()} antibiotics, {100 * y.mean():.1f}% resistant.', '',
             '## Overall', '',
             '| | AUC | Very major error | Major error |', '| --- | --- | --- | --- |']
    for name in RUNS:
        vme, me = errors(y, df[name].to_numpy())
        lines.append(f'| {name} | {roc_auc_score(y, df[name]):.3f} | {100 * vme:.1f}% | {100 * me:.1f}% |')
    gap, lo, hi, p = paired_gap(df, 'class rule', 'genes model')
    lines += ['', f'Genes model minus class rule: AUC {gap:+.3f} [{lo:+.3f} to {hi:+.3f}], '
              f'paired bootstrap over genomes ({N_BOOT} resamples; share of resamples with no '
              f'gain {p:.3f}). The key rule\'s overall AUC is low by construction: drugs without '
              'a named determinant all score 0, so compare it per drug below.', '',
              'Very major error: resistant called susceptible. Major error: susceptible called '
              'resistant. Thresholds: 0.5 for the model, presence for the rules.']

    rows = []
    for ab, g in df.groupby('antibiotic'):
        yy = g['y_true'].to_numpy()
        if len(g) < MIN_N or yy.sum() < 10 or (1 - yy).sum() < 10:
            continue
        r = {'drug': ab, 'n': len(g), 'res': yy.mean()}
        for name in RUNS:
            r[name] = roc_auc_score(yy, g[name])
        r['key_used'] = g['key rule'].max() > 0
        rows.append(r)
    t = pd.DataFrame(rows).sort_values('n', ascending=False)
    lines += ['', f'## By antibiotic (at least {MIN_N} lab test rows and 10 of each class)', '',
              '| Antibiotic | Rows | Resistant | Class rule | Key rule | Genes model |',
              '| --- | --- | --- | --- | --- | --- |']
    for r in t.to_dict('records'):
        key = f'{r["key rule"]:.3f}' if r['key_used'] else '-'
        lines.append(f'| {r["drug"]} | {r["n"]:,} | {100 * r["res"]:.0f}% | '
                     f'{r["class rule"]:.3f} | {key} | {r["genes model"]:.3f} |')
    k = t[t['key_used']]
    lines += ['', f'Genes model above the class rule on {int((t["genes model"] > t["class rule"]).sum())} '
              f'of {len(t)} drugs; above the key rule on {int((k["genes model"] > k["key rule"]).sum())} '
              f'of the {len(k)} drugs that have a named determinant. "-": no named determinant '
              'for that drug in `genes.py`.']
    lines += ['', '## Context: the same lab rows without genes', '',
              'Hamza\'s LightGBM runs on the same genomes and split with no gene columns '
              '(cleaning v6; v7 has the same rows and labels and changes only MIC values, '
              'which these runs do not use).', '',
              '| Run | Inputs | Lab AUC [95% CI] |', '| --- | --- | --- |']
    for run, inputs in CONTEXT.items():
        path = os.path.join(RESULTS, run, 'metrics.json')
        if os.path.exists(path):
            lab = json.load(open(path))['test_by_label_source']['lab']
            lo, hi = lab['auc_roc_ci']
            lines.append(f'| {run} | {inputs} | {lab["auc_roc"]:.3f} [{lo:.3f} to {hi:.3f}] |')
    lines += ['', '## Limits', '',
              '- The class rule counts every gene of the drug\'s AMRFinderPlus class, so any '
              'beta-lactamase counts against carbapenems and cephalosporins. A rule using '
              'AMRFinderPlus subclasses (or ResFinder\'s phenotype table) is the fairer opponent '
              'and is the next run.',
              '- The key rule covers 16 drugs (`genes.py` KEY_DETERMINANTS).',
              '- The model also sees antibiotic, drug class and genus, so part of its lead is '
              'intrinsic resistance by genus, which the context table above measures.',
              '- One split (seed 42), grouped by genome, not by lineage.']
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nwrote {os.path.relpath(OUT)}')


if __name__ == '__main__':
    main()
