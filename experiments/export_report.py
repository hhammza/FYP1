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
    'D3_forecaster_deploy': 'special',
}
ROC_RUNS = ['A2_oof_grouped', 'A3_logistic', 'A6_lab_only',
            'A12_species_holdout', 'A_ablation_drug_only', 'D3_forecaster_deploy']
BEST = 'A2_oof_grouped'
V7 = '_v7'


def folder(run_id):
    """The results folder behind a run name on the page: its cleaning v7 run."""
    return run_id + V7 if os.path.isdir(os.path.join(RESULTS, run_id + V7)) else run_id


# Page wording where a config's description names an earlier cleaning version
PAGE_DESCRIPTIONS = {
    'D3_forecaster_deploy': 'The /forecast recipe: grouped split, out-of-fold encoding, isotonic '
                            'calibration, threshold with very major error within budget',
}


def config_description(run_id, fallback):
    if run_id in PAGE_DESCRIPTIONS:
        return PAGE_DESCRIPTIONS[run_id]
    path = os.path.join(HERE, 'configs', f'{run_id}.json')
    return load_json(path).get('description', fallback) if os.path.exists(path) else fallback


def load_json(*parts):
    with open(os.path.join(*parts)) as fh:
        return json.load(fh)


def roc_points(y, s, n=101):
    fpr, tpr, _ = roc_curve(y, s)
    grid = np.linspace(0, 1, n)
    return {'fpr': grid.round(4).tolist(), 'tpr': np.interp(grid, fpr, tpr).round(4).tolist()}


def is_genome_run(run_id):
    """Track B runs (B*, L_*, B6L_*, B8_*): configs that use genome data."""
    path = os.path.join(RESULTS, run_id, 'config.snapshot.json')
    if not os.path.exists(path):
        return run_id.startswith(('B', 'L_'))
    cfg = load_json(path)
    feats = cfg.get('features', {})
    return bool(cfg.get('data', {}).get('genomes') or feats.get('kmers') or feats.get('genes'))


def genome_runs():
    """Track B runs for the separate Genome models section of /models
    (progress/formats/README.md §6). Judged by lab-confirmed rows: BV-BRC's
    computational labels were predicted from the genome."""
    reg = pd.read_csv(os.path.join(RESULTS, 'registry.csv'))
    reg = reg.sort_values('finished_at').drop_duplicates('id', keep='last')
    out = []
    for r in reg.itertuples():
        if not is_genome_run(r.id):
            continue
        m = load_json(RESULTS, r.id, 'metrics.json')
        cfg = m['config']
        lab = m.get('test_by_label_source', {}).get('lab') or {}
        feats = cfg.get('features', {})
        split = cfg.get('split', {})
        cv = m['dataset'].get('clean_version')
        out.append({
            'id': r.id, 'description': r.description,
            'clean_version': cv,
            # v7 changed only MIC values, which genome runs do not use, so
            # their rows and labels are v6's: one section shows both.
            'label_version': 'v6' if cv in ('v6', 'v7') else cv,
            'model': r.model,
            'features': ('gene lookup rule, nothing learned' if r.model == 'gene_rule' else
                         'genes + k-mers' if feats.get('genes') and feats.get('kmers') else
                         'genes' if feats.get('genes') else 'k-mers' if feats.get('kmers') else
                         'no genome features'),
            'split': split.get('strategy', 'grouped') + (f" ({split['lineage_cut']})" if split.get('lineage_cut') else '')
                     + (f" ({split['holdout_genus']} held out)" if split.get('holdout_genus') else ''),
            'plasmids_excluded': bool(cfg.get('data', {}).get('min_genome_bp')),
            'auc_roc': round(float(r.auc_roc), 4),
            'auc_roc_lab': round(float(lab['auc_roc']), 4) if lab else None,
            'auc_roc_lab_ci': [round(float(x), 4) for x in lab['auc_roc_ci']] if lab else None,
            'n_lab': int(lab.get('n', 0)) if lab else 0,
            'lab_genomes': lab.get('genomes') if lab else None,
        })
    # The site shows the complete data only: v6 and v7 (same rows and labels)
    out = [r for r in out if r['label_version'] == 'v6']
    return sorted(out, key=lambda x: (x['clean_version'] or '', x['id']))


def runs_table():
    reg = pd.read_csv(os.path.join(RESULTS, 'registry.csv'))
    reg = reg.sort_values('finished_at').drop_duplicates('id', keep='last')
    # Track B (genome) runs use a different, much smaller dataset (2,505
    # genomes, mostly computational labels), so their AUCs are not comparable
    # with the tabular runs on this page. They stay in RESULTS.md until the
    # page has a genome section of its own.
    reg = reg[~reg['id'].map(is_genome_run)]
    # The site shows the complete data only: every tabular run on cleaning v7,
    # listed under its plain name (A2_oof_grouped), with the folder in run_id.
    reg = reg[reg['id'].str.endswith(V7)]
    out = []
    for r in reg.itertuples():
        base = r.id[:-len(V7)]
        cfg = load_json(RESULTS, r.id, 'config.snapshot.json')
        out.append({
            'id': base, 'run_id': r.id, 'clean_version': 'v7',
            'description': config_description(base, r.description),
            'group': GROUPS.get(base, 'learning_curve' if base.startswith('LC_') else 'other'),
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


_FRAMES = {}


def run_frame(metrics):
    """The cleaned data a run read, from the clean_version in its metrics."""
    source = data_prep.source_of(metrics.get('dataset', {}).get('clean_version'))
    if source not in _FRAMES:
        _FRAMES[source] = data_prep.get_clean(source=source, verbose=False)
    return _FRAMES[source]


def split_summary():
    """Real counts for the default split, and what a random split would leak."""
    m = load_json(RESULTS, folder(BEST), 'metrics.json')
    df = run_frame(m)
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
    out = {'full_data': profile(run_frame(load_json(RESULTS, folder(BEST), 'metrics.json')))}
    cache = {}
    for run_id in run_ids:
        cfg = load_json(RESULTS, folder(run_id), 'config.snapshot.json')
        data_cfg, split_cfg = cfg.get('data', {}), cfg.get('split', {})
        run_metrics = load_json(RESULTS, folder(run_id), 'metrics.json')
        full = run_frame(run_metrics)
        source = data_prep.source_of(run_metrics.get('dataset', {}).get('clean_version'))
        key = json.dumps([source, data_cfg, split_cfg], sort_keys=True)
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
    m = load_json(RESULTS, folder(BEST), 'metrics.json')
    per = [p for p in m['per_antibiotic'] if p['n'] >= 1000 and not np.isnan(p['auc_roc'])]
    per.sort(key=lambda p: p['auc_roc'])
    slim = [{'antibiotic': p['group'], 'rows': p['n'], 'auc_roc': round(p['auc_roc'], 4),
             'prevalence': round(p['prevalence'], 4)} for p in per]
    t = m['test']
    return {
        'id': BEST, 'run_id': folder(BEST), 'model_info': m.get('model_info', {}),
        'features': m.get('features', []),
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
        path = os.path.join(RESULTS, folder(run_id), 'predictions.csv')
        if os.path.exists(path):
            p = pd.read_csv(path, usecols=['y_true', 'y_score'])
            out[run_id] = roc_points(p.y_true.to_numpy(), p.y_score.to_numpy())
        elif previous and run_id in previous.get('roc', {}):
            out[run_id] = previous['roc'][run_id]
            kept.append(run_id)
    if kept:
        print(f'[report] no predictions.csv for {", ".join(kept)}; kept their ROC from the last report')
    return out


def lab_auc(m):
    lab = (m.get('test_by_label_source') or {}).get('lab') or {}
    return round(float(lab['auc_roc']), 4) if lab.get('auc_roc') is not None else None


def insights(report):
    """What the results say, each with the runs behind it. Built from the
    numbers, so a re-run updates the text; a finding whose runs are missing
    is left out rather than written from memory."""
    reg = pd.read_csv(os.path.join(RESULTS, 'registry.csv'))
    reg = reg.sort_values('finished_at').drop_duplicates('id', keep='last').set_index('id')

    def auc(rid):
        return float(reg.loc[rid, 'auc_roc']) if rid in reg.index else None

    def lab(rid):
        path = os.path.join(RESULTS, rid, 'metrics.json')
        return lab_auc(load_json(path)) if os.path.exists(path) else None

    out = []
    sh = (report.get('shipped') or {}).get('lightgbm_previous')
    if sh and len(sh.get('results', [])) > 1:
        seen, unseen = sh['results'][0]['auc_roc'], sh['results'][1]['auc_roc']
        out.append({'icon': 'exclamation-triangle', 'title': 'The first model was tested on genomes it had seen',
                    'text': f'The original forecaster reported AUC {sh["claimed_auc"]:.2f} from a random row split. '
                            f'On genomes it trained on it scores {seen:.2f}; on genomes it never saw, {unseen:.2f}. '
                            'Every result on this site now uses a genome-grouped split, so no genome is on both sides.',
                    'evidence': 'Section 2, lightgbm_previous in shipped_eval.json'})

    a2l = lab(BEST + V7)
    if auc(BEST + V7) and a2l:
        out.append({'icon': 'clipboard2-pulse', 'title': 'Lab-confirmed results are predicted far better',
                    'text': f'The best model scores {auc(BEST + V7):.3f} on all test rows but {a2l:.3f} on the rows with '
                            'a real laboratory result. Most test rows carry labels BV-BRC predicted by computer, which '
                            'these features predict less well. Quote the lab AUC for claims about real isolates.',
                    'evidence': 'A2_oof_grouped_v7, test_by_label_source'})

    algos = {k: auc(k + V7) for k in ('A3b_lgbm_same_sample', 'A4_random_forest', 'A5_xgboost', 'A5b_catboost')}
    if all(algos.values()) and auc('A3_logistic' + V7):
        lo, hi = min(algos.values()), max(algos.values())
        out.append({'icon': 'cpu', 'title': 'The algorithm matters less than the data',
                    'text': f'On the same 400k-row sample, LightGBM, XGBoost, CatBoost and random forest land within '
                            f'{hi - lo:.3f} AUC of each other ({lo:.3f} to {hi:.3f}); logistic regression trails at '
                            f'{auc("A3_logistic" + V7):.3f}. Tree ensembles win, but which one barely matters.',
                    'evidence': 'A3 to A5 on v7'})

    lc = {k: auc(f'LC_{k}{V7}') for k in ('50k', '200k', '800k')}
    if all(lc.values()):
        out.append({'icon': 'graph-up', 'title': 'More rows stopped helping early',
                    'text': f'AUC goes from {lc["50k"]:.3f} with 50k training rows to {lc["200k"]:.3f} with 200k and '
                            f'{lc["800k"]:.3f} with 800k. Better features, not more of the same rows, is the way up.',
                    'evidence': 'Learning curve LC_* on v7'})

    drug, nomic, a2 = auc('A_ablation_drug_only' + V7), auc('A_ablation_no_mic' + V7), auc(BEST + V7)
    if drug and nomic and a2:
        out.append({'icon': 'eyedropper', 'title': 'The MIC and the organism carry the signal',
                    'text': f'Knowing only the antibiotic and its class gives {drug:.3f}. Every feature except the MIC '
                            f'(organism, resistance rates) gives {nomic:.3f}, and adding the MIC lifts it to {a2:.3f}. '
                            'The organism does most of the work; the measured MIC adds the rest.',
                    'evidence': 'Ablations on v7'})

    held = auc('A12_species_holdout' + V7)
    if held:
        out.append({'icon': 'question-diamond', 'title': 'A genus it never saw is still hard',
                    'text': f'With every Klebsiella genome held out of training, AUC on Klebsiella is {held:.3f}. The forecaster '
                            'generalises to new genomes of organisms it knows, not to new organisms.',
                    'evidence': 'A12_species_holdout_v7'})

    rule, genes, nogenes = lab('B6R_gene_rule_class_v7'), lab('B6L_genes_v7'), lab('B6L_nogenes_v6')
    if rule and genes:
        extra = f'; organism and drug alone reach {nogenes:.3f}' if nogenes else ''
        out.append({'icon': 'dna', 'title': 'The genome beats a gene lookup table',
                    'text': f'On the same lab-tested genomes, calling a strain resistant whenever it carries a gene of the '
                            f'drug\'s class scores {rule:.3f}{extra}; the learned genes model scores {genes:.3f}. A lookup '
                            'rule over-calls resistance; learning which genes matter for which drug is what works.',
                    'evidence': 'Section 5; experiments/genome/results/rule_vs_model.md'})
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
        'genome_runs': genome_runs(),
    }
    report['clean_version'] = 'v7'
    # Which cleaning version each served model's run used, from its metrics
    report['shipped_versions'] = {
        k: load_json(RESULTS, v['run_id'], 'metrics.json')['dataset'].get('clean_version')
        for k, v in (shipped or {}).items()
        if isinstance(v, dict) and v.get('run_id')
        and os.path.exists(os.path.join(RESULTS, v['run_id'], 'metrics.json'))}
    report['insights'] = insights(report)
    report['training_profiles'] = training_profiles([r['id'] for r in report['runs']])
    with open(OUT, 'w') as fh:
        json.dump(report, fh, separators=(',', ':'))
    print(f'[report] {len(report["runs"])} runs → {os.path.relpath(OUT, ROOT)} '
          f'({os.path.getsize(OUT) / 1024:.0f} KB)')


if __name__ == '__main__':
    main()
