"""
Collect every model result into one JSON file for the web app's /models page.

    python experiments/evaluate_shipped.py   # once, or after retraining the app
    python experiments/export_report.py      # after any experiment run

Reads results/registry.csv, each run's metrics.json and predictions.csv, and
results/shipped_eval.json. Writes backend/trained_models/model_report.json,
which is committed so the deployed backend can serve it without the 5 GB of
data or the experiment outputs, neither of which ship.
"""
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib import data_prep, splits  # noqa: E402
from lib.profile import profile  # noqa: E402
from run import select_rows  # noqa: E402

RESULTS = os.path.join(HERE, 'results')
OUT = os.path.join(ROOT, 'backend', 'trained_models', 'model_report.json')

# How each run is grouped on the page. Anything unlisted lands in 'other'.
GROUPS = {
    'A2_oof_grouped': 'baseline', 'A9_threshold_f1': 'baseline',
    'A0_baseline_leaky': 'protocol', 'A1_oof_random': 'protocol',
    'A2b_no_encoding': 'protocol', 'A10_monotonic_mic': 'protocol',
    'A3_logistic': 'algorithm', 'A3b_lgbm_same_sample': 'algorithm',
    'A4_random_forest': 'algorithm', 'A5_xgboost': 'algorithm',
    'A5b_catboost': 'algorithm', 'A5c_catboost_native': 'algorithm',
    'A6_lab_only': 'special', 'A6b_lab_only_no_mic': 'special',
    'A12_species_holdout': 'special',
    'A_ablation_no_mic': 'ablation', 'A_ablation_drug_only': 'ablation',
    'A10s_monotonic_species': 'protocol', 'D1_forecaster_deploy': 'special',
    'D2_forecaster_deploy': 'special',
}
ROC_RUNS = ['A2_oof_grouped', 'A3_logistic', 'A6_lab_only',
            'A12_species_holdout', 'A_ablation_drug_only', 'D2_forecaster_deploy']
BEST = 'A2_oof_grouped'


def load_json(*parts):
    with open(os.path.join(*parts)) as fh:
        return json.load(fh)


def roc_points(y, s, n=101):
    fpr, tpr, _ = roc_curve(y, s)
    grid = np.linspace(0, 1, n)
    return {'fpr': grid.round(4).tolist(), 'tpr': np.interp(grid, fpr, tpr).round(4).tolist()}


def runs_table():
    reg = pd.read_csv(os.path.join(RESULTS, 'registry.csv'))
    reg = reg.sort_values('finished_at').drop_duplicates('id', keep='last')
    out = []
    for r in reg.itertuples():
        cfg = load_json(RESULTS, r.id, 'config.snapshot.json')
        out.append({
            'id': r.id, 'description': r.description,
            'group': GROUPS.get(r.id, 'learning_curve' if r.id.startswith('LC_') else 'other'),
            'split': r.split, 'encoding': r.encoding, 'model': r.model,
            'rows': int(r.rows), 'test_rows': int(r.test_rows),
            'sample_rows': cfg.get('data', {}).get('sample_rows'),
            'label_sources': cfg.get('data', {}).get('label_sources'),
            'auc_roc': r.auc_roc, 'auc_ci': [r.auc_ci_low, r.auc_ci_high],
            'auc_pr': r.auc_pr, 'f1': r.f1, 'brier': r.brier,
            'very_major_error': r.very_major_error, 'major_error': r.major_error,
            'threshold': r.threshold, 'runtime_seconds': r.runtime_seconds,
        })
    return sorted(out, key=lambda x: -x['auc_roc'])


def split_summary():
    """Real counts for the default split, and what a random split would leak."""
    m = load_json(RESULTS, BEST, 'metrics.json')
    df = data_prep.get_clean(verbose=False)
    out = {'strategies': {}}
    for strategy in ('grouped', 'random'):
        tr, te = splits.make_split(df, strategy=strategy, test_size=0.2, seed=42, verbose=False)
        train_g = set(df.loc[tr, 'Genome ID'])
        test_g = set(df.loc[te, 'Genome ID'])
        shared = train_g & test_g
        leaked_rows = int(df.loc[te, 'Genome ID'].isin(train_g).sum())
        out['strategies'][strategy] = {
            'train_rows': int(tr.sum()), 'test_rows': int(te.sum()),
            'train_genomes': len(train_g), 'test_genomes': len(test_g),
            'shared_genomes': len(shared),
            'test_genomes_seen_in_train': round(len(shared) / len(test_g), 4),
            'test_rows_from_seen_genomes': round(leaked_rows / int(te.sum()), 4),
            'train_prevalence': round(float(df.loc[tr, 'target'].mean()), 4),
            'test_prevalence': round(float(df.loc[te, 'target'].mean()), 4),
        }
    g = out['strategies']['grouped']
    val_rows = int(m['validation']['n'])
    out.update({
        'total_rows': int(len(df)), 'total_genomes': int(df['Genome ID'].nunique()),
        'rows_per_genome': round(len(df) / df['Genome ID'].nunique(), 1),
        'fit_rows': g['train_rows'] - val_rows, 'validation_rows': val_rows,
        'test_rows': g['test_rows'], 'encoding_folds': 5, 'validation_folds': 6,
    })
    return out


def training_profiles(run_ids):
    """What each run trained on and was tested on, rebuilt from its config.

    Runs sharing the same data filters and split share one profile.
    """
    full = data_prep.get_clean(verbose=False)
    out = {'full_data': profile(full)}
    cache = {}
    for run_id in run_ids:
        cfg = load_json(RESULTS, run_id, 'config.snapshot.json')
        data_cfg, split_cfg = cfg.get('data', {}), cfg.get('split', {})
        key = json.dumps([data_cfg, split_cfg], sort_keys=True)
        if key not in cache:
            df = select_rows(full, data_cfg, verbose=False)
            tr, te = splits.make_split(df, strategy=split_cfg.get('strategy', 'grouped'),
                                       test_size=split_cfg.get('test_size', 0.2),
                                       seed=split_cfg.get('seed', 42),
                                       holdout_genus=split_cfg.get('holdout_genus'), verbose=False)
            train = profile(df.loc[tr])
            train.update(test_rows=int(te.sum()),
                         test_genomes=int(df.loc[te, 'Genome ID'].nunique()),
                         shared_genomes=len(set(df.loc[tr, 'Genome ID']) & set(df.loc[te, 'Genome ID'])))
            cache[key] = train
        out[run_id] = cache[key]
    return out


def best_run_detail():
    m = load_json(RESULTS, BEST, 'metrics.json')
    per = [p for p in m['per_antibiotic'] if p['n'] >= 1000 and not np.isnan(p['auc_roc'])]
    per.sort(key=lambda p: p['auc_roc'])
    slim = [{'antibiotic': p['group'], 'rows': p['n'], 'auc_roc': round(p['auc_roc'], 4),
             'prevalence': round(p['prevalence'], 4)} for p in per]
    t = m['test']
    return {
        'id': BEST, 'model_info': m.get('model_info', {}), 'features': m.get('features', []),
        'confusion': {k: t[k] for k in ('tp', 'fp', 'tn', 'fn')},
        'test': {k: round(v, 4) for k, v in t.items() if isinstance(v, float)},
        'per_antibiotic_worst': slim[:10], 'per_antibiotic_best': slim[-10:][::-1],
        'per_antibiotic_count': len(slim),
    }


def roc_curves(previous=None):
    """ROC points per run, from predictions.csv.

    predictions.csv is gitignored, so a clone only has it for runs made on
    that machine. Where it is missing, the curve already in the committed
    report is kept rather than silently dropped.
    """
    out = {}
    kept = []
    for run_id in ROC_RUNS:
        path = os.path.join(RESULTS, run_id, 'predictions.csv')
        if os.path.exists(path):
            p = pd.read_csv(path, usecols=['y_true', 'y_score'])
            out[run_id] = roc_points(p.y_true.to_numpy(), p.y_score.to_numpy())
        elif previous and run_id in previous.get('roc', {}):
            out[run_id] = previous['roc'][run_id]
            kept.append(run_id)
    if kept:
        print(f'[report] no predictions.csv for {", ".join(kept)}; kept their ROC from the last report')
    return out


def main():
    shipped_path = os.path.join(RESULTS, 'shipped_eval.json')
    shipped = load_json(shipped_path) if os.path.exists(shipped_path) else None
    if shipped is None:
        print('[report] no shipped_eval.json, run experiments/evaluate_shipped.py first')

    previous = load_json(OUT) if os.path.exists(OUT) else None
    report = {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'best_run': BEST,
        'runs': runs_table(),
        'split': split_summary(),
        'best': best_run_detail(),
        'roc': roc_curves(previous),
        'shipped': shipped,
    }
    report['training_profiles'] = training_profiles([r['id'] for r in report['runs']])
    with open(OUT, 'w') as fh:
        json.dump(report, fh, separators=(',', ':'))
    print(f'[report] {len(report["runs"])} runs → {os.path.relpath(OUT, ROOT)} '
          f'({os.path.getsize(OUT) / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
