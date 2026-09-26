"""Run one experiment from a JSON config.

    python experiments/run.py experiments/configs/A1_oof_grouped.json
    python experiments/run.py --all

Everything a run needs is in its config, and everything a run produces lands
in experiments/results/<id>/, models included. Nothing here writes to
backend/trained_models/, so the served models are never disturbed by an
experiment.
"""
import argparse
import glob
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import algorithms  # noqa: E402
from lib import data_prep, encoders, metrics, splits  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(HERE, 'results')
REGISTRY = os.path.join(RESULTS_DIR, 'registry.csv')

BASE_FEATURES = ['Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign',
                 'is_lab_confirmed', 'computational_f1', 'mic_value', 'mic_log', 'has_mic']


def load_config(path):
    with open(path) as fh:
        cfg = json.load(fh)
    cfg.setdefault('id', os.path.splitext(os.path.basename(path))[0])
    cfg.setdefault('description', '')
    cfg.setdefault('data', {})
    cfg.setdefault('split', {})
    cfg.setdefault('features', {})
    cfg.setdefault('model', {'type': 'lightgbm'})
    cfg.setdefault('threshold', {'strategy': 'fixed', 'fixed': 0.5})
    cfg.setdefault('evaluation', {})
    return cfg


def select_rows(df, data_cfg, verbose=True):
    """Apply the row filters a config asks for."""
    out = df
    sources = data_cfg.get('label_sources')
    if sources:
        out = out[out['label_source'].isin(sources)]
    drop_drugs = data_cfg.get('drop_antibiotics')
    if drop_drugs:
        out = out[~out['Antibiotic'].isin(drop_drugs)]
    min_rows = data_cfg.get('min_rows_per_antibiotic')
    if min_rows:
        counts = out['Antibiotic'].value_counts()
        out = out[out['Antibiotic'].isin(counts[counts >= min_rows].index)]
    sample = data_cfg.get('sample_rows')
    if sample and len(out) > sample:
        out = out.sample(sample, random_state=data_cfg.get('seed', 42))
    out = out.reset_index(drop=True)
    if verbose and len(out) != len(df):
        print(f'[rows] {len(df):,} → {len(out):,} after filters')
    return out


def run(cfg, verbose=True):
    t0 = time.time()
    run_dir = os.path.join(RESULTS_DIR, cfg['id'])
    os.makedirs(os.path.join(run_dir, 'model'), exist_ok=True)

    print(f'\n{"=" * 68}\n  {cfg["id"]} - {cfg["description"]}\n{"=" * 68}')

    # ── Data ─────────────────────────────────────────────────────────────
    dcfg = cfg['data']
    df = data_prep.get_clean(
        source=dcfg.get('source', 'amr_output'),
        normalize_antibiotics=dcfg.get('normalize_antibiotics', True),
        verbose=verbose)
    df = select_rows(df, dcfg, verbose)
    df = apply_taxon_level(df, dcfg.get('taxon_level', 'strain'), verbose)

    # ── Split ────────────────────────────────────────────────────────────
    scfg = cfg['split']
    train_mask, test_mask = splits.make_split(
        df,
        strategy=scfg.get('strategy', 'grouped'),
        test_size=scfg.get('test_size', 0.2),
        seed=scfg.get('seed', 42),
        holdout_genus=scfg.get('holdout_genus'),
        verbose=verbose)

    # ── Features ─────────────────────────────────────────────────────────
    fcfg = cfg['features']
    enc_mode = fcfg.get('target_encoding', 'oof')
    folds = None
    if enc_mode == 'oof':
        folds = splits.inner_folds(df.loc[train_mask], n_splits=fcfg.get('encoding_folds', 5),
                                   seed=scfg.get('seed', 42))
    df, rate_features = encoders.add_rate_features(df, train_mask, enc_mode, folds, verbose)

    features = list(fcfg.get('base', BASE_FEATURES)) + rate_features
    for drop in fcfg.get('drop', []):
        if drop in features:
            features.remove(drop)
    cat_features = [c for c in algorithms.CAT_FEATURES if c in features]

    X = df[features]
    y = df['target'].to_numpy()

    X_train_all, X_test = algorithms.align_categories(
        X.loc[train_mask], X.loc[test_mask], columns=cat_features)
    y_train_all, y_test = y[train_mask.to_numpy() if hasattr(train_mask, 'to_numpy') else train_mask], y[test_mask]

    # Validation slice for early stopping and threshold choice, grouped so the
    # same genome cannot sit in both halves of the training data either.
    train_df = df.loc[train_mask].reset_index(drop=True)
    inner = splits.inner_folds(train_df, n_splits=6, seed=scfg.get('seed', 42))
    fit_pos, val_pos = inner[0]
    X_fit, X_val = X_train_all.iloc[fit_pos], X_train_all.iloc[val_pos]
    y_fit, y_val = y_train_all[fit_pos], y_train_all[val_pos]

    print(f'[data] features={len(features)} fit={len(X_fit):,} '
          f'val={len(X_val):,} test={len(X_test):,}')

    # ── Train ────────────────────────────────────────────────────────────
    model = algorithms.build_model(cfg['model'])
    t_fit = time.time()
    model.fit(X_fit, y_fit, X_val, y_val, cat_features)
    fit_seconds = time.time() - t_fit

    # ── Calibration and threshold on validation, never on test ───────────
    # With calibration on, the validation genomes are split in two: the
    # calibrator is fitted on one half and the threshold chosen on the other,
    # so neither choice is made on rows it is then judged by.
    val_raw = model.predict_proba(X_val)
    ccfg = cfg.get('calibration')
    calibrator = None
    thr_pos = np.arange(len(y_val))
    if ccfg:
        val_df = train_df.iloc[val_pos].reset_index(drop=True)
        cal_pos, thr_pos = splits.inner_folds(val_df, n_splits=2, seed=scfg.get('seed', 42))[0]
        calibrator = metrics.fit_calibrator(y_val[cal_pos], val_raw[cal_pos],
                                            ccfg.get('method', 'isotonic'))
    val_score = metrics.apply_calibrator(calibrator, val_raw)

    tcfg = cfg['threshold']
    threshold = metrics.pick_threshold(
        y_val[thr_pos], val_score[thr_pos],
        strategy=tcfg.get('strategy', 'fixed'),
        fixed=tcfg.get('fixed', 0.5),
        vme_budget=tcfg.get('vme_budget', 0.03))

    # ── Evaluate ─────────────────────────────────────────────────────────
    test_raw = model.predict_proba(X_test)
    test_score = metrics.apply_calibrator(calibrator, test_raw)
    result = metrics.evaluate(y_test, test_score, threshold)
    val_result = metrics.evaluate(y_val, val_score, threshold)

    calibration = None
    if calibrator:
        raw = metrics.evaluate(y_test, test_raw, threshold)
        calibration = {
            'method': calibrator['method'],
            'fitted_on_rows': int(len(cal_pos)),
            'threshold_chosen_on_rows': int(len(thr_pos)),
            'test_brier_before': raw['brier'], 'test_brier_after': result['brier'],
            'test_auc_before': raw['auc_roc'], 'test_auc_after': result['auc_roc'],
            'reliability_before': metrics.calibration_curve_points(y_test, test_raw),
            'reliability_after': metrics.calibration_curve_points(y_test, test_score),
        }
        print(f'[calibrate] {calibrator["method"]}: Brier {raw["brier"]:.4f} → '
              f'{result["brier"]:.4f}, AUC {raw["auc_roc"]:.4f} → {result["auc_roc"]:.4f}')

    ecfg = cfg['evaluation']
    test_rows = df.loc[test_mask]
    lo, hi = metrics.bootstrap_ci(y_test, test_score, test_rows['Genome ID'].to_numpy(),
                                  n_boot=ecfg.get('n_boot', 200))
    result['auc_roc_ci'] = [lo, hi]
    by_drug = metrics.per_group(y_test, test_score, test_rows['Antibiotic'].to_numpy(),
                                threshold, min_n=ecfg.get('min_n_per_group', 50))

    print(f'\n[result] AUC {result["auc_roc"]:.4f} [{lo:.4f}-{hi:.4f}]  '
          f'AUPRC {result["auc_pr"]:.4f}  F1 {result["f1"]:.4f}')
    print(f'[result] threshold {threshold:.3f} | VME {result["very_major_error"]:.1%} '
          f'| ME {result["major_error"]:.1%} | Brier {result["brier"]:.4f}')
    if by_drug:
        print('[result] weakest antibiotics:')
        for r in by_drug[:5]:
            print(f'           {r["group"][:34]:34s} n={r["n"]:6,} AUC={r["auc_roc"]:.3f}')

    # ── Persist ──────────────────────────────────────────────────────────
    payload = {
        'id': cfg['id'],
        'description': cfg['description'],
        'finished_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'runtime_seconds': round(time.time() - t0, 1),
        'fit_seconds': round(fit_seconds, 1),
        'environment': {'python': platform.python_version(),
                        'platform': platform.platform()},
        'dataset': {
            'rows': int(len(df)), 'genomes': int(df['Genome ID'].nunique()),
            'antibiotics': int(df['Antibiotic'].nunique()),
            'prevalence': float(df['target'].mean()),
            'train_rows': int(train_mask.sum()), 'test_rows': int(test_mask.sum()),
        },
        'features': features,
        'model_info': model.info,
        'test': result,
        'validation': val_result,
        'calibration': calibration,
        'per_antibiotic': by_drug,
        'config': cfg,
    }
    with open(os.path.join(run_dir, 'metrics.json'), 'w') as fh:
        json.dump(payload, fh, indent=2)

    pred = pd.DataFrame({
        'genome_id': test_rows['Genome ID'].to_numpy(),
        'antibiotic': test_rows['Antibiotic'].to_numpy(),
        'genus': test_rows['genus'].to_numpy(),
        'y_true': y_test,
        'y_score': test_score,
    })
    if calibrator:
        pred['y_score_raw'] = test_raw
    pred.to_csv(os.path.join(run_dir, 'predictions.csv'), index=False)

    model.save(os.path.join(run_dir, 'model', 'model'))
    export_inference_bundle(run_dir, df, train_mask, features, cat_features,
                            X_train_all, threshold, cfg, enc_mode, calibrator)
    with open(os.path.join(run_dir, 'config.snapshot.json'), 'w') as fh:
        json.dump(cfg, fh, indent=2)

    append_registry(payload)
    print(f'[saved] {os.path.relpath(run_dir, os.path.dirname(HERE))}  '
          f'({payload["runtime_seconds"]:.0f}s)')
    return payload


def apply_taxon_level(df, level='strain', verbose=True):
    """Use species-level Taxon IDs in place of the export's strain-level ones.

    The export spreads one species over many strain IDs (E. coli over ~1,200,
    never 562), so a taxon a user can actually type never matches a strain
    rate. 'species' swaps in species_taxon_id (cleaning v3) for the feature
    and for the taxon x antibiotic rate table.
    """
    if level == 'strain':
        return df
    if level != 'species':
        raise ValueError(f'unknown taxon_level {level!r}')
    out = df.copy()
    out['Taxon ID'] = out['species_taxon_id']
    if verbose:
        print(f'[taxon] species level: {df["Taxon ID"].nunique():,} strain IDs → '
              f'{out["Taxon ID"].nunique():,} species IDs')
    return out


def export_inference_bundle(run_dir, df, train_mask, features, cat_features,
                            X_train, threshold, cfg, enc_mode, calibrator=None):
    """Everything needed to predict with this model later.

    A saved booster alone is not enough: three of its features are resistance
    rates looked up per (antibiotic / taxon / genus), and those tables must come
    from *this run's training rows* or the model sees inputs it was never
    trained against. The lookup tables, the category levels, the feature order
    and the chosen threshold are all part of the model.
    """
    import joblib
    from lib import encoders

    model_dir = os.path.join(run_dir, 'model')
    train_rows = df.loc[train_mask]
    global_mean = float(train_rows['target'].mean())

    tables = {}
    if enc_mode != 'none':
        for keys, name, min_count in encoders.SPECS:
            agg = train_rows.groupby(keys, observed=True)['target'].agg(['sum', 'count'])
            agg = agg[agg['count'] >= min_count]
            rate = (agg['sum'] / agg['count'])
            tables[name] = {tuple(k) if isinstance(k, tuple) else (k,): float(v)
                            for k, v in rate.items()}

    joblib.dump({'global_mean': global_mean, 'tables': tables},
                os.path.join(model_dir, 'rate_tables.joblib'))

    levels = {c: sorted(X_train[c].astype(str).unique()) for c in cat_features}
    with open(os.path.join(model_dir, 'feature_meta.json'), 'w') as fh:
        json.dump({
            'model_type': cfg['model'].get('type', 'lightgbm'),
            'model_file': 'model.txt' if cfg['model'].get('type', 'lightgbm') == 'lightgbm'
                          else 'model.joblib',
            'features': features,
            'categorical_features': cat_features,
            'category_levels': levels,
            'encoding_mode': enc_mode,
            'global_mean': global_mean,
            'threshold': float(threshold),
            'calibration': calibrator,
            'taxon_level': cfg['data'].get('taxon_level', 'strain'),
            # What produced the categorical inputs, so inference can rebuild
            # them exactly as training did.
            'drug_class_map': data_prep.DRUG_CLASS_MAP,
            'antibiotics_normalized': cfg['data'].get('normalize_antibiotics', True),
            'trained_on': {
                'rows': int(train_mask.sum()),
                'genomes': int(train_rows['Genome ID'].nunique()),
                'prevalence': global_mean,
            },
        }, fh, indent=2)


def append_registry(payload):
    row = {
        'id': payload['id'],
        'description': payload['description'],
        'finished_at': payload['finished_at'],
        'split': payload['config']['split'].get('strategy', 'grouped'),
        'encoding': payload['config']['features'].get('target_encoding', 'oof'),
        'model': payload['config']['model'].get('type', 'lightgbm'),
        'rows': payload['dataset']['rows'],
        'test_rows': payload['dataset']['test_rows'],
        'auc_roc': round(payload['test']['auc_roc'], 4),
        'auc_ci_low': round(payload['test']['auc_roc_ci'][0], 4),
        'auc_ci_high': round(payload['test']['auc_roc_ci'][1], 4),
        'auc_pr': round(payload['test']['auc_pr'], 4),
        'f1': round(payload['test']['f1'], 4),
        'balanced_acc': round(payload['test']['balanced_acc'], 4),
        'brier': round(payload['test']['brier'], 4),
        'very_major_error': round(payload['test']['very_major_error'], 4),
        'major_error': round(payload['test']['major_error'], 4),
        'threshold': round(payload['test']['threshold'], 3),
        'runtime_seconds': payload['runtime_seconds'],
    }
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df = pd.DataFrame([row])
    if os.path.exists(REGISTRY):
        prev = pd.read_csv(REGISTRY)
        prev = prev[prev['id'] != row['id']]          # a re-run replaces its row
        df = pd.concat([prev, df], ignore_index=True)
    df.to_csv(REGISTRY, index=False)


def main():
    ap = argparse.ArgumentParser(description='Run an AMR model experiment')
    ap.add_argument('config', nargs='?', help='path to a JSON config')
    ap.add_argument('--all', action='store_true', help='run every config in configs/')
    args = ap.parse_args()

    if args.all:
        paths = sorted(glob.glob(os.path.join(HERE, 'configs', '*.json')))
    elif args.config:
        paths = [args.config]
    else:
        ap.error('give a config path or --all')

    for path in paths:
        run(load_config(path))


if __name__ == '__main__':
    main()
