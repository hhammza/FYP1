"""GAN experiment (A13): does CTGAN-made training data help the rare drugs and organisms?

    python experiments/gan/ctgan_augment.py generate   # fit CTGAN, sample, check quality
    python experiments/run.py experiments/configs/A13_ctgan_v7.json
    python experiments/gan/ctgan_augment.py evaluate   # A13 vs A6, overall and on the rare rows

The base model is A6 (lab-confirmed rows, the forecaster's features). The split
is rebuilt exactly as A6 made it (same data, filters and seed), and CTGAN
(Xu et al. 2019, a GAN for tabular data) is fitted on TRAINING rows only: the
rows of rare antibiotics or rare genera (under RARE_ROWS training rows each).
Its synthetic rows go to A13's training side only (`data.synthetic`, run.py);
the test set stays real and identical to A6's, so the two compare row by row.

Quality of the synthetic rows: per-column distance from the real rows (total
variation for categories, Kolmogorov-Smirnov for the MIC) and a detection test
(a classifier told to separate real from synthetic; AUC 0.5 = indistinguishable).
Synthetic rows that break real relations (a drug with another drug's class, a
species of another genus) are dropped before use. The synthetic file stays in
experiments/cache/ and is never committed.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(HERE)
ROOT = os.path.dirname(EXPERIMENTS)
sys.path.insert(0, EXPERIMENTS)

BASE_CONFIG = os.path.join(EXPERIMENTS, 'configs', 'A6_lab_only_v7.json')
SYNTHETIC = os.path.join(EXPERIMENTS, 'cache', 'ctgan_synthetic_A13.parquet')
SYNTHETIC_REL = 'experiments/cache/ctgan_synthetic_A13.parquet'
QUALITY = os.path.join(HERE, 'results', 'ctgan_quality.json')
RESULTS_MD = os.path.join(HERE, 'results', 'GAN_RESULTS.md')

RARE_ROWS = 1000          # an antibiotic or genus with fewer training rows is rare
MAX_FIT_ROWS = 30000      # CTGAN fits on at most this many rows (CPU time)
EPOCHS = 60
SEED = 42

DISCRETE = ['Antibiotic', 'drug_class', 'genus', 'species', 'taxon', 'mic_sign', 'has_mic', 'target']
COLUMNS = DISCRETE + ['mic_log']


def a6_split(verbose=True):
    """A6's data and train/test masks, rebuilt as run.py builds them."""
    import run as pipeline
    from lib import data_prep, splits
    cfg = pipeline.load_config(BASE_CONFIG)
    dcfg, scfg = cfg['data'], cfg['split']
    df = data_prep.get_clean(source=dcfg.get('source'), verbose=False)
    df = pipeline.compact(df, verbose=False)
    df = pipeline.select_rows(df, dcfg, verbose=False)
    df = pipeline.apply_taxon_level(df, dcfg.get('taxon_level', 'strain'), verbose=False)
    tr, te = splits.make_split(df, strategy=scfg['strategy'], test_size=scfg['test_size'],
                               seed=scfg['seed'], verbose=verbose)
    return df, tr, te


def rare_sets(train):
    ab = train['Antibiotic'].value_counts()
    ge = train['genus'].value_counts()
    return sorted(map(str, ab[(ab > 0) & (ab < RARE_ROWS)].index)), sorted(map(str, ge[(ge > 0) & (ge < RARE_ROWS)].index))


def to_table(rows):
    t = pd.DataFrame({
        'Antibiotic': rows['Antibiotic'].astype(str), 'drug_class': rows['drug_class'].astype(str),
        'genus': rows['genus'].astype(str), 'species': rows['species'].astype(str),
        'taxon': rows['Taxon ID'].astype(str), 'mic_sign': rows['mic_sign'].astype(str),
        'has_mic': rows['has_mic'].astype(int).astype(str), 'target': rows['target'].astype(int).astype(str),
        'mic_log': rows['mic_log'].astype(float).fillna(0.0).to_numpy()})
    return t.reset_index(drop=True)


def from_table(t):
    has = t['has_mic'].astype(int)
    mic_log = np.where(has == 1, t['mic_log'].clip(lower=0), np.nan)
    return pd.DataFrame({
        'Antibiotic': t['Antibiotic'], 'drug_class': t['drug_class'], 'genus': t['genus'],
        'species': t['species'], 'Taxon ID': pd.to_numeric(t['taxon'], errors='coerce'),
        'mic_sign': t['mic_sign'], 'has_mic': has, 'mic_log': mic_log,
        'mic_value': np.where(has == 1, np.expm1(mic_log), np.nan),
        'target': t['target'].astype(int), 'is_lab_confirmed': 1, 'computational_f1': 1.0})


def consistent(syn, real):
    """Keep synthetic rows whose drug/class and genus/species/taxon combinations exist."""
    ab_class = set(zip(real['Antibiotic'], real['drug_class']))
    org = set(zip(real['genus'], real['species'], real['taxon']))
    ok = [(a, c) in ab_class and (g, s, x) in org
          for a, c, g, s, x in zip(syn['Antibiotic'], syn['drug_class'], syn['genus'], syn['species'], syn['taxon'])]
    return syn[np.array(ok, bool)].reset_index(drop=True)


def quality(real, syn):
    """Column distances and a detection AUC (0.5 = indistinguishable)."""
    from scipy.stats import ks_2samp
    from sklearn.metrics import roc_auc_score
    import lightgbm as lgb
    tvd = {}
    for c in DISCRETE:
        p = real[c].value_counts(normalize=True)
        q = syn[c].value_counts(normalize=True)
        tvd[c] = round(float(0.5 * p.subtract(q, fill_value=0).abs().sum()), 4)
    r_mic = real.loc[real['has_mic'] == '1', 'mic_log']
    s_mic = syn.loc[syn['has_mic'] == '1', 'mic_log']
    ks = float(ks_2samp(r_mic, s_mic).statistic) if len(r_mic) and len(s_mic) else None
    n = min(len(real), len(syn))
    rng = np.random.default_rng(SEED)
    both = pd.concat([real.sample(n, random_state=SEED), syn.sample(n, random_state=SEED)], ignore_index=True)
    y = np.r_[np.zeros(n), np.ones(n)]
    for c in DISCRETE:
        both[c] = both[c].astype('category')
    idx = rng.permutation(len(both)); half = len(idx) // 2
    clf = lgb.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=31, verbose=-1, random_state=SEED)
    clf.fit(both.iloc[idx[:half]], y[idx[:half]])
    auc = float(roc_auc_score(y[idx[half:]], clf.predict_proba(both.iloc[idx[half:]])[:, 1]))
    return {'tvd_per_column': tvd, 'ks_mic_log': None if ks is None else round(ks, 4),
            'detection_auc': round(auc, 4)}


def generate():
    from ctgan import CTGAN
    import torch
    torch.manual_seed(SEED)
    df, tr, te = a6_split()
    train = df.loc[tr]
    rare_ab, rare_ge = rare_sets(train)
    rare = train[train['Antibiotic'].astype(str).isin(rare_ab) | train['genus'].astype(str).isin(rare_ge)]
    real = to_table(rare)
    fit_rows = real.sample(min(len(real), MAX_FIT_ROWS), random_state=SEED)
    print(f'[gan] A6 training rows {int(tr.sum()):,}; rare: {len(rare_ab)} antibiotics, {len(rare_ge)} genera '
          f'(< {RARE_ROWS} training rows each) -> {len(real):,} rows; CTGAN fits on {len(fit_rows):,}, {EPOCHS} epochs')
    t0 = time.time()
    model = CTGAN(epochs=EPOCHS, batch_size=500, verbose=False)
    model.fit(fit_rows, discrete_columns=DISCRETE)
    print(f'[gan] fitted in {time.time() - t0:.0f} s')
    target_n = len(real)
    kept, drawn = [], 0
    while sum(len(k) for k in kept) < target_n and drawn < 20 * target_n:
        batch = model.sample(max(5000, target_n))
        drawn += len(batch)
        kept.append(consistent(batch, real))
    syn = pd.concat(kept, ignore_index=True).head(target_n)
    print(f'[gan] sampled {drawn:,}, kept {len(syn):,} consistent rows ({len(syn) / max(drawn, 1):.0%} of sampled)')
    q = quality(real, syn)
    q.update({'rare_antibiotics': rare_ab, 'rare_genera': rare_ge, 'real_rare_rows': int(len(real)),
              'fit_rows': int(len(fit_rows)), 'synthetic_rows': int(len(syn)), 'sampled': int(drawn),
              'epochs': EPOCHS, 'rare_threshold_rows': RARE_ROWS})
    os.makedirs(os.path.dirname(QUALITY), exist_ok=True)
    with open(QUALITY, 'w', encoding='utf-8') as fh:
        json.dump(q, fh, indent=2)
    from_table(syn).to_parquet(SYNTHETIC, index=False)
    print(f"[gan] quality: detection AUC {q['detection_auc']} (0.5 = indistinguishable), "
          f"KS(MIC) {q['ks_mic_log']}, TVD {q['tvd_per_column']}")
    print(f'[gan] wrote {os.path.relpath(SYNTHETIC, ROOT)} (not committed) and {os.path.relpath(QUALITY, ROOT)}')


def evaluate():
    """A13 against A6 on the same real test rows: all rows and the rare rows."""
    from lib import significance
    with open(QUALITY, encoding='utf-8') as fh:
        q = json.load(fh)
    load = lambda r: pd.read_csv(os.path.join(EXPERIMENTS, 'results', r, 'predictions.csv'), dtype={'genome_id': str})
    a6, a13 = load('A6_lab_only_v7'), load('A13_ctgan_v7')
    key = ['genome_id', 'antibiotic']
    m = a13.merge(a6[key + ['y_score']], on=key, suffixes=('_a13', '_a6'))
    assert len(m) == len(a6) == len(a13), 'A13 and A6 must share their test rows'
    rare = m['antibiotic'].isin(q['rare_antibiotics']) | m['genus'].isin(q['rare_genera'])
    out = {}
    for name, sel in [('all test rows', np.ones(len(m), bool)), ('rare antibiotics or genera', rare.to_numpy())]:
        s = m[sel]
        d = significance.delong(s['y_true'], s['y_score_a13'], s['y_score_a6'])
        b = significance.paired_bootstrap(s['y_true'], s['y_score_a13'], s['y_score_a6'], s['genome_id'], n_boot=500)
        out[name] = {'rows': int(len(s)), 'genomes': int(s['genome_id'].nunique()),
                     'auc_a13': round(d['auc_a'], 4), 'auc_a6': round(d['auc_b'], 4),
                     'diff': round(d['diff'], 4), 'delong_p': d['p'], 'bootstrap_ci': [round(x, 4) for x in b['ci']]}
        print(f"[gan] {name}: {len(s):,} rows, AUC A13 {d['auc_a']:.4f} vs A6 {d['auc_b']:.4f}, "
              f"diff {d['diff']:+.4f}, genome bootstrap [{b['ci'][0]:+.4f}, {b['ci'][1]:+.4f}], DeLong p {d['p']:.3g}")
    q['evaluation'] = out
    with open(QUALITY, 'w', encoding='utf-8') as fh:
        json.dump(q, fh, indent=2)
    write_md(q)


def write_md(q):
    e = q['evaluation']
    p = lambda x: '< 0.0001' if x < 1e-4 else f'{x:.4f}'
    lines = ['# GAN experiment (A13): CTGAN training rows for rare drugs and organisms', '',
             'Built by `experiments/gan/ctgan_augment.py`. Base model A6 (lab-confirmed rows, the forecaster\'s '
             'features, split by genome). CTGAN was fitted on A6\'s **training** rows of rare antibiotics or genera '
             f"(under {q['rare_threshold_rows']:,} training rows each: {len(q['rare_antibiotics'])} antibiotics, "
             f"{len(q['rare_genera'])} genera; {q['real_rare_rows']:,} rows, {q['fit_rows']:,} used to fit, "
             f"{q['epochs']} epochs). {q['synthetic_rows']:,} synthetic rows were added to A13's training side; "
             'the test set is real and identical to A6\'s.', '',
             '## Quality of the synthetic rows', '',
             f"- Detection test: a classifier separating real from synthetic rows reaches AUC **{q['detection_auc']}** "
             '(0.5 = indistinguishable, 1.0 = obvious fakes).',
             f"- MIC distribution, Kolmogorov-Smirnov distance: {q['ks_mic_log']}.",
             f"- Category distributions, total variation distance per column: "
             + ', '.join(f'{k} {v}' for k, v in q['tvd_per_column'].items()) + '.',
             f"- {q['synthetic_rows'] / max(q['sampled'], 1):.0%} of sampled rows kept: the rest paired a drug with "
             'another drug\'s class or a species with another genus.', '',
             '## Effect on the model (same real test rows)', '',
             '| Test rows | Rows (genomes) | AUC A13 (with GAN rows) | AUC A6 (without) | Difference | Genome bootstrap 95% CI | DeLong p |',
             '|---|---|---|---|---|---|---|']
    for name, r in e.items():
        lines.append(f"| {name} | {r['rows']:,} ({r['genomes']:,}) | {r['auc_a13']:.4f} | {r['auc_a6']:.4f} | "
                     f"{r['diff']:+.4f} | [{r['bootstrap_ci'][0]:+.4f}, {r['bootstrap_ci'][1]:+.4f}] | {p(r['delong_p'])} |")
    with open(RESULTS_MD, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    print(f'[gan] wrote {os.path.relpath(RESULTS_MD, ROOT)}')


if __name__ == '__main__':
    import lib  # noqa: F401  (UTF-8 output on Windows)
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    {'generate': generate, 'evaluate': evaluate}.get(cmd, lambda: sys.exit('usage: generate | evaluate'))()
