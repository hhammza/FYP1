"""Add the inference bundle to runs trained before run.py exported one.

Rebuilds each run's training split from its own config snapshot, the splits
are seeded, so this reproduces exactly the rows that run trained on, and
writes `rate_tables.joblib` and `feature_meta.json` next to the model. No
retraining; only groupby aggregations, so it takes seconds per run.

    python experiments/backfill_bundles.py [--force]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import algorithms  # noqa: E402
from lib import data_prep, encoders, splits  # noqa: E402
import run as runner  # noqa: E402

RESULTS_DIR = runner.RESULTS_DIR


def backfill(run_id, force=False, verbose=True):
    run_dir = os.path.join(RESULTS_DIR, run_id)
    model_dir = os.path.join(run_dir, 'model')
    snapshot = os.path.join(run_dir, 'config.snapshot.json')
    if not os.path.exists(snapshot):
        return f'{run_id}: no config snapshot, skipped'
    if os.path.exists(os.path.join(model_dir, 'feature_meta.json')) and not force:
        return f'{run_id}: already has a bundle'

    with open(snapshot) as fh:
        cfg = json.load(fh)
    for key, default in (('data', {}), ('split', {}), ('features', {}),
                         ('model', {'type': 'lightgbm'}),
                         ('threshold', {'strategy': 'fixed', 'fixed': 0.5})):
        cfg.setdefault(key, default)

    df = data_prep.get_clean(
        source=cfg['data'].get('source', 'amr_output'),
        normalize_antibiotics=cfg['data'].get('normalize_antibiotics', True),
        verbose=False)
    df = runner.select_rows(df, cfg['data'], verbose=False)

    scfg = cfg['split']
    train_mask, _ = splits.make_split(
        df, strategy=scfg.get('strategy', 'grouped'),
        test_size=scfg.get('test_size', 0.2), seed=scfg.get('seed', 42),
        holdout_genus=scfg.get('holdout_genus'), verbose=False)

    fcfg = cfg['features']
    enc_mode = fcfg.get('target_encoding', 'oof')
    rate_features = [] if enc_mode == 'none' else encoders.RATE_FEATURES
    features = list(fcfg.get('base', runner.BASE_FEATURES)) + rate_features
    for drop in fcfg.get('drop', []):
        if drop in features:
            features.remove(drop)
    cat_features = [c for c in algorithms.CAT_FEATURES if c in features]

    # Category levels come from the training rows, exactly as align_categories did.
    X_train = df.loc[train_mask, [c for c in features if c in df.columns]]

    # The threshold the run actually used is recorded in its metrics.
    threshold = cfg['threshold'].get('fixed', 0.5)
    metrics_path = os.path.join(run_dir, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path) as fh:
            threshold = json.load(fh)['test']['threshold']

    runner.export_inference_bundle(run_dir, df, train_mask, features, cat_features,
                                   X_train, threshold, cfg, enc_mode)
    return f'{run_id}: bundle written ({len(features)} features, thr {threshold:.2f})'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='rewrite existing bundles')
    ap.add_argument('--only', help='one run id')
    args = ap.parse_args()

    ids = [args.only] if args.only else sorted(
        d for d in os.listdir(RESULTS_DIR)
        if os.path.isdir(os.path.join(RESULTS_DIR, d)))
    for run_id in ids:
        try:
            print(backfill(run_id, args.force))
        except Exception as exc:
            print(f'{run_id}: FAILED - {exc}')


if __name__ == '__main__':
    main()
