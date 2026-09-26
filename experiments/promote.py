"""Promote an experiment run to the model the web app serves.

    python experiments/promote.py D1_forecaster_deploy            # backend
    python experiments/promote.py D1_forecaster_deploy --dry-run  # check only
    python experiments/promote.py D1_forecaster_deploy --library  # + amrpredict (after T2.6)

A run's saved bundle (results/<id>/model/) holds everything needed to predict,
but not in the shape backend/ml_models/lgbm_predictor.py loads. This script
converts it, refuses runs the backend cannot serve faithfully, and writes
lgbm_metrics.json beside the artifacts so every number the UI shows comes from
the run that produced the model.

Writes, into backend/trained_models/ (and, with --library,
amrpredict-lib/src/amrpredict/models/):
    amr_lgbm_final_model.txt     the booster
    ab_rate_full.joblib          {antibiotic: rate}
    taxon_ab_rate_full.joblib    {(taxon_id, antibiotic): rate}
    genus_ab_rate_full.joblib    {(genus lower-case, antibiotic): rate}
    lgbm_meta.joblib             global mean, threshold, calibration, taxon level,
                                 drug-class map, run id
    lgbm_metrics.json            format in progress/formats/README.md

Afterwards run evaluate_shipped.py and export_report.py so /models and
/compare describe the new model.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

import joblib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib import data_prep  # noqa: E402

RESULTS = os.path.join(HERE, 'results')
BACKEND_DIR = os.path.join(ROOT, 'backend', 'trained_models')
LIBRARY_DIR = os.path.join(ROOT, 'amrpredict-lib', 'src', 'amrpredict', 'models')

METRICS_SCHEMA = 'amr-model-metrics/1'

# What backend/ml_models/lgbm_predictor.py builds, in this order.
SERVED_FEATURES = [
    'Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign',
    'is_lab_confirmed', 'computational_f1', 'mic_value', 'mic_log', 'has_mic',
    'ab_resistance_rate', 'taxon_ab_resistance_rate', 'genus_ab_resistance_rate',
]

THRESHOLD_RULES = {
    'fixed': 'fixed at {fixed}',
    'maximize_f1': 'highest F1 on validation genomes',
    'vme_constrained': 'highest threshold with very major error <= {vme_budget:.0%} '
                       'on validation genomes, i.e. the lowest major error within that budget',
}


def git_state():
    """(commit, dirty) of the working tree, or (None, None) outside git."""
    try:
        commit = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                         cwd=ROOT, text=True).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'],
                                             cwd=ROOT, text=True).strip())
        return commit, dirty
    except (OSError, subprocess.CalledProcessError):
        return None, None


def rnd(v, n=4):
    return None if v is None else round(float(v), n)


def test_block(t, ci=None):
    """The fields every metrics.json carries for its test set."""
    return {
        'n': int(t['n']),
        'prevalence': rnd(t['prevalence']),
        'auc_roc': rnd(t['auc_roc']),
        'auc_roc_ci': [rnd(ci[0]), rnd(ci[1])] if ci else None,
        'auc_pr': rnd(t.get('auc_pr')),
        'f1': rnd(t.get('f1')),
        'accuracy': rnd(t.get('accuracy', (t['tp'] + t['tn']) / t['n'])),
        'recall': rnd(t.get('sensitivity', t['tp'] / (t['tp'] + t['fn']))),
        'specificity': rnd(t.get('specificity', t['tn'] / (t['tn'] + t['fp']))),
        'very_major_error': rnd(t['very_major_error']),
        'major_error': rnd(t['major_error']),
        'brier': rnd(t.get('brier')),
        'tp': int(t['tp']), 'fp': int(t['fp']), 'tn': int(t['tn']), 'fn': int(t['fn']),
    }


def load_run(run_id):
    run_dir = os.path.join(RESULTS, run_id)
    model_dir = os.path.join(run_dir, 'model')
    need = [os.path.join(run_dir, 'metrics.json'), os.path.join(model_dir, 'feature_meta.json'),
            os.path.join(model_dir, 'rate_tables.joblib'), os.path.join(model_dir, 'model.txt')]
    missing = [p for p in need if not os.path.exists(p)]
    if missing:
        sys.exit('missing: ' + ', '.join(os.path.relpath(p, ROOT) for p in missing)
                 + f'\nrun it first: python experiments/run.py experiments/configs/{run_id}.json')
    with open(need[0]) as fh:
        metrics = json.load(fh)
    with open(need[1]) as fh:
        meta = json.load(fh)
    return run_dir, metrics, meta, joblib.load(need[2])


def check_servable(metrics, meta):
    """Refuse anything the backend would score differently from the harness."""
    problems = []
    if meta.get('model_type', 'lightgbm') != 'lightgbm':
        problems.append(f"model type {meta.get('model_type')!r}: the backend serves LightGBM only")
    if meta.get('features') != SERVED_FEATURES:
        problems.append('feature list differs from what lgbm_predictor.py builds:\n'
                        f"  run:     {meta.get('features')}\n  backend: {SERVED_FEATURES}")
    if meta.get('encoding_mode') == 'none':
        problems.append('run has no rate features, but the backend always supplies them')
    if metrics['config'].get('split', {}).get('strategy') != 'grouped':
        problems.append('run was not evaluated on a genome-grouped split, '
                        'so its test numbers would overstate the model')
    if problems:
        sys.exit('cannot promote:\n- ' + '\n- '.join(problems))


def convert_tables(rate_tables):
    """Run bundle tables → the dicts lgbm_predictor.py loads."""
    t = rate_tables['tables']
    ab = {k[0]: v for k, v in t.get('ab_resistance_rate', {}).items()}
    taxon = {(int(k[0]), str(k[1])): v for k, v in t.get('taxon_ab_resistance_rate', {}).items()}
    genus = {(str(k[0]).lower(), str(k[1])): v for k, v in t.get('genus_ab_resistance_rate', {}).items()}
    return ab, taxon, genus


def build_metrics(run_id, run_dir, metrics, meta, promoted_at):
    t = metrics['test']
    cfg = metrics['config']
    commit, dirty = git_state()
    cal = metrics.get('calibration')
    tcfg = cfg.get('threshold', {})
    rule = THRESHOLD_RULES.get(tcfg.get('strategy', 'fixed'), tcfg.get('strategy'))
    rule = rule.format(fixed=tcfg.get('fixed', 0.5), vme_budget=tcfg.get('vme_budget', 0.03))

    pred_path = os.path.join(run_dir, 'predictions.csv')
    test_genomes = (int(pd.read_csv(pred_path, usecols=['genome_id'])['genome_id'].nunique())
                    if os.path.exists(pred_path) else None)
    split = cfg.get('split', {})
    ds = metrics['dataset']

    return {
        'schema': METRICS_SCHEMA,
        'model': 'lightgbm_forecaster',
        'page': '/forecast',
        'run_id': run_id,
        'description': metrics.get('description', ''),
        'algorithm': 'LightGBM' + (', monotone in MIC' if cfg['model'].get('monotone_on') else ''),
        'trained_at': metrics.get('finished_at'),
        'promoted_at': promoted_at,
        'git_commit': commit,
        'git_dirty': dirty,
        'evaluation': {
            'split': f"genome-grouped {int(round((1 - split.get('test_size', 0.2)) * 100))}/"
                     f"{int(round(split.get('test_size', 0.2) * 100))}, seed {split.get('seed', 42)}",
            'test_genomes_unseen': True,
            'target_encoding': cfg.get('features', {}).get('target_encoding', 'oof'),
            'taxon_level': meta.get('taxon_level', 'strain'),
        },
        'threshold': rnd(t['threshold'], 3),
        'threshold_rule': rule,
        'calibration': None if not cal else {
            'method': cal['method'],
            'brier_before': rnd(cal['test_brier_before']),
            'brier_after': rnd(cal['test_brier_after']),
            'auc_before': rnd(cal['test_auc_before']),
            'auc_after': rnd(cal['test_auc_after']),
        },
        'test': test_block(t, t.get('auc_roc_ci')),
        'data': {
            'source': 'BV-BRC AMR phenotypes, Data/amr_output (all files), cleaning '
                      + data_prep.CLEAN_VERSION,
            'train_rows': int(ds['train_rows']),
            'test_rows': int(ds['test_rows']),
            'train_genomes': int(meta['trained_on']['genomes']),
            'test_genomes': test_genomes,
            'prevalence': rnd(ds['prevalence']),
            'antibiotics': len(meta['category_levels'].get('Antibiotic', [])),
            'genera': meta['category_levels'].get('genus', []),
        },
    }


def main():
    ap = argparse.ArgumentParser(description='Promote an experiment run to the served model')
    ap.add_argument('run_id')
    ap.add_argument('--dry-run', action='store_true', help='check and print, write nothing')
    ap.add_argument('--library', action='store_true',
                    help='also copy into the amrpredict package. Off by default: the '
                         'package loader (amrpredict/lgbm.py) does not yet apply '
                         'calibration or species-level taxa, so it would score the new '
                         'model differently from the web app. Enable once T2.6 lands.')
    args = ap.parse_args()

    run_dir, metrics, meta, rate_tables = load_run(args.run_id)
    check_servable(metrics, meta)
    ab, taxon, genus = convert_tables(rate_tables)
    promoted_at = datetime.now(timezone.utc).isoformat(timespec='seconds')
    report = build_metrics(args.run_id, run_dir, metrics, meta, promoted_at)
    lgbm_meta = {
        'run_id': args.run_id,
        'global_mean': float(rate_tables['global_mean']),
        # Thresholds come off a linspace grid (0.2400000000000001); store the
        # value a person would read.
        'threshold': round(float(meta['threshold']), 4),
        'calibration': meta.get('calibration'),
        'taxon_level': meta.get('taxon_level', 'strain'),
        'drug_class_map': meta.get('drug_class_map'),
    }

    t = report['test']
    print(f"[promote] {args.run_id}: AUC {t['auc_roc']} {t['auc_roc_ci']}, threshold "
          f"{report['threshold']} ({report['threshold_rule']})")
    print(f"[promote] VME {t['very_major_error']:.1%}  ME {t['major_error']:.1%}  "
          f"accuracy {t['accuracy']:.1%}  recall {t['recall']:.1%}  Brier {t['brier']}")
    print(f"[promote] tables: {len(ab)} antibiotics, {len(taxon):,} taxon pairs, "
          f"{len(genus):,} genus pairs; taxon level {lgbm_meta['taxon_level']}; "
          f"calibration {(lgbm_meta['calibration'] or {}).get('method', 'none')}")
    if args.dry_run:
        print('[promote] dry run, nothing written')
        return

    targets = [BACKEND_DIR] + ([LIBRARY_DIR] if args.library else [])
    for target in targets:
        os.makedirs(target, exist_ok=True)
        shutil.copyfile(os.path.join(run_dir, 'model', 'model.txt'),
                        os.path.join(target, 'amr_lgbm_final_model.txt'))
        joblib.dump(ab, os.path.join(target, 'ab_rate_full.joblib'))
        joblib.dump(taxon, os.path.join(target, 'taxon_ab_rate_full.joblib'))
        joblib.dump(genus, os.path.join(target, 'genus_ab_rate_full.joblib'))
        joblib.dump(lgbm_meta, os.path.join(target, 'lgbm_meta.joblib'))
        with open(os.path.join(target, 'lgbm_metrics.json'), 'w', encoding='utf-8') as fh:
            json.dump(report, fh, indent=2)
        print(f'[promote] wrote {os.path.relpath(target, ROOT)}')
    print('[promote] next: restart the backend (or POST /api/reload/), then run '
          'experiments/evaluate_shipped.py and experiments/export_report.py')


if __name__ == '__main__':
    main()
