"""
Evaluate the models the web app serves (backend/trained_models/) on genomes
they never trained on.

The shipped artifacts carry no record of their training data, but it can be
reconstructed: train_models.py read the first N files of a directory listing,
which on the Windows machine that trained them was alphabetical. The first 500
amr_output CSVs reproduce the LightGBM's 76 antibiotics, 9 genera and stored
global resistance rate exactly; the first 200 mapped CSVs reproduce the K-mer
model's 62 antibiotics exactly. Every genome outside those files is unseen.

    python experiments/evaluate_shipped.py

Writes experiments/results/shipped_eval.json. Takes about 3 minutes, most of it
reading 4 GB of FASTA.
"""
import glob
import json
import os
import pickle
import sys
import warnings
from multiprocessing import Pool

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib import data_prep, metrics  # noqa: E402
from lib.profile import profile  # noqa: E402

MODEL_DIR = os.path.join(ROOT, 'backend', 'trained_models')
OUT = os.path.join(HERE, 'results', 'shipped_eval.json')
LGBM_TRAIN_FILES = 500   # load_amr_data(max_files=500)
KMER_TRAIN_FILES = 200   # train_kmer: csv_files[:200]
CAT_COLS = ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign']


def roc_points(y, s, n=101):
    """ROC curve resampled onto a fixed FPR grid, small enough to ship."""
    fpr, tpr, _ = roc_curve(y, s)
    grid = np.linspace(0, 1, n)
    return {'fpr': grid.round(4).tolist(), 'tpr': np.interp(grid, fpr, tpr).round(4).tolist()}


def summarise(name, y, s, groups, threshold, roc=False):
    r = metrics.evaluate(y, s, threshold)
    lo, hi = metrics.bootstrap_ci(y, s, groups, n_boot=200)
    row = {
        'subset': name, 'rows': int(len(y)), 'genomes': int(pd.Series(groups).nunique()),
        'prevalence': round(float(np.mean(y)), 4), 'threshold': threshold,
        'auc_roc': round(r['auc_roc'], 4), 'auc_ci': [round(lo, 4), round(hi, 4)],
        'auc_pr': round(r['auc_pr'], 4), 'f1': round(r['f1'], 4),
        'very_major_error': round(r['very_major_error'], 4),
        'major_error': round(r['major_error'], 4), 'brier': round(r['brier'], 4),
        'tp': r['tp'], 'fp': r['fp'], 'tn': r['tn'], 'fn': r['fn'],
    }
    if roc:
        row['roc'] = roc_points(y, s)
    print(f"  {name:<52} AUC {row['auc_roc']:.4f} [{lo:.4f}-{hi:.4f}]  n={len(y):,}")
    return row


# ── LightGBM forecaster ──────────────────────────────────────────────────

def evaluate_lgbm():
    import lightgbm as lgb
    print('[lgbm] loading shipped artifacts')
    booster = lgb.Booster(model_file=os.path.join(MODEL_DIR, 'amr_lgbm_final_model.txt'))
    ab_rate = joblib.load(os.path.join(MODEL_DIR, 'ab_rate_full.joblib'))
    tax = joblib.load(os.path.join(MODEL_DIR, 'taxon_ab_rate_full.joblib'))
    gen = joblib.load(os.path.join(MODEL_DIR, 'genus_ab_rate_full.joblib'))
    gm = float(joblib.load(os.path.join(MODEL_DIR, 'lgbm_meta.joblib'))['global_mean'])
    cats = booster.pandas_categorical
    known_ab, known_genus = set(cats[0]), set(cats[2])

    files = sorted(glob.glob(os.path.join(data_prep.data_root(), 'amr_output', '*.csv')))
    frames = []
    for i, f in enumerate(files):
        try:
            d = pd.read_csv(f, low_memory=False)
        except Exception:
            continue
        d['_train_file'] = i < LGBM_TRAIN_FILES
        frames.append(d)
    raw = pd.concat(frames, ignore_index=True)
    seen = set(raw.loc[raw['_train_file'], 'Genome ID'])

    # Shipped model uses raw antibiotic names, so no alias normalisation here
    df = data_prep.clean(raw, normalize_antibiotics=False, verbose=False)
    df['unseen'] = ~df['Genome ID'].isin(seen)

    check = df[~df.unseen]
    reconstruction = {
        'training_files': LGBM_TRAIN_FILES,
        'antibiotics_match': set(check.Antibiotic) >= known_ab,
        'genera_match': set(check.genus) == known_genus,
        'global_mean_stored': round(gm, 4),
        'global_mean_reconstructed': round(float(check.target.mean()), 4),
    }
    print(f'[lgbm] reconstruction {reconstruction}')

    def features(d, served=False):
        X = pd.DataFrame(index=d.index)
        X['Taxon ID'] = d['Taxon ID']
        for c in CAT_COLS[:4]:
            X[c] = d[c]
        X['mic_sign'] = d['mic_sign']
        # The web app always sends is_lab_confirmed=0 and computational_f1=0.85
        X['is_lab_confirmed'] = 0 if served else d['is_lab_confirmed']
        X['computational_f1'] = 0.85 if served else d['computational_f1']
        for c in ('mic_value', 'mic_log', 'has_mic'):
            X[c] = d[c]
        X['ab_resistance_rate'] = d['Antibiotic'].map(ab_rate).fillna(gm).astype(float)
        t = d[['Taxon ID', 'Antibiotic']].merge(tax, on=['Taxon ID', 'Antibiotic'], how='left')
        X['taxon_ab_resistance_rate'] = t['taxon_ab_resistance_rate'].to_numpy()
        X['taxon_ab_resistance_rate'] = X['taxon_ab_resistance_rate'].fillna(X['ab_resistance_rate'])
        g = d[['genus', 'Antibiotic']].merge(gen, on=['genus', 'Antibiotic'], how='left')
        X['genus_ab_resistance_rate'] = g['genus_ab_resistance_rate'].to_numpy()
        X['genus_ab_resistance_rate'] = X['genus_ab_resistance_rate'].fillna(X['ab_resistance_rate'])
        X = X[['Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign',
               'is_lab_confirmed', 'computational_f1', 'mic_value', 'mic_log', 'has_mic',
               'ab_resistance_rate', 'taxon_ab_resistance_rate', 'genus_ab_resistance_rate']]
        for c, levels in zip(CAT_COLS, cats):
            X[c] = pd.Categorical(X[c].astype(str), categories=levels)
        return X

    def run(name, d, served=True, roc=False):
        s = booster.predict(features(d, served))
        return summarise(name, d.target.to_numpy(), s, d['Genome ID'].to_numpy(), 0.40, roc), s

    seen_df, un = df[~df.unseen], df[df.unseen]
    un_known = un[un.genus.isin(known_genus) & un.Antibiotic.isin(known_ab)]
    rows = [
        run('Genomes it trained on', seen_df, roc=True)[0],
        run('Genomes it never saw', un, roc=True)[0],
        run('Never seen, organisms and drugs it knows', un_known)[0],
    ]

    # Head to head with A2 on rows neither model trained on
    head = None
    pred_path = os.path.join(HERE, 'results', 'A2_oof_grouped', 'predictions.csv')
    if os.path.exists(pred_path):
        pred = pd.read_csv(pred_path)
        h = un.merge(pred[['genome_id', 'antibiotic', 'y_true', 'y_score']],
                     left_on=['Genome ID', 'Antibiotic'], right_on=['genome_id', 'antibiotic'])
        h = h[h.y_true == h.target]
        s = booster.predict(features(h))
        known = (h.genus.isin(known_genus) & h.Antibiotic.isin(known_ab)).to_numpy()
        head = {
            'rows': int(len(h)), 'genomes': int(h['Genome ID'].nunique()),
            'shipped_auc': round(roc_auc_score(h.target, s), 4),
            'a2_auc': round(roc_auc_score(h.target, h.y_score), 4),
            'known_rows': int(known.sum()),
            'shipped_auc_known': round(roc_auc_score(h.target[known], s[known]), 4),
            'a2_auc_known': round(roc_auc_score(h.target[known], h.y_score[known]), 4),
        }
        print(f'[lgbm] head to head {head}')

    return {
        'name': 'LightGBM forecaster', 'page': '/forecast',
        'artifact': 'backend/trained_models/amr_lgbm_final_model.txt',
        'trees': booster.num_trees(), 'known_antibiotics': len(known_ab),
        'known_genera': sorted(known_genus),
        'train_rows': int(len(seen_df)), 'train_genomes': int(seen_df['Genome ID'].nunique()),
        'source': 'amr_output', 'files_used': LGBM_TRAIN_FILES, 'files_total': len(files),
        'train_profile': profile(seen_df),
        'claimed_auc': 0.9255, 'split': 'random row-level 80/20, stratified',
        'reconstruction': reconstruction, 'results': rows, 'head_to_head_a2': head,
    }


# ── K-mer RandomForest ───────────────────────────────────────────────────

_LUT = np.full(256, 255, dtype=np.uint8)
for _i, _c in enumerate(b'ATCG'):        # itertools.product('ATCG') order
    _LUT[_c] = _i


def _genome_features(path):
    """Same numbers as train_models.kmer_freq + GC + length, vectorised."""
    try:
        with open(path, 'rb') as fh:
            seq = b''.join(line.strip() for line in fh if not line.startswith(b'>')).upper()
    except OSError:
        return path, None
    s = _LUT[np.frombuffer(seq, dtype=np.uint8)]
    s = s[s != 255][:500_000]
    if len(s) < 9:
        return path, None
    idx = s[:-3].astype(np.int32) * 64 + s[1:-2] * 16 + s[2:-1] * 4 + s[3:]
    counts = np.bincount(idx, minlength=256).astype(np.float32)
    gc = float(np.isin(s, [2, 3]).mean())
    return path, (counts / counts.sum(), np.array([gc, 1 - gc, len(s) / 500000.0], np.float32))


def evaluate_kmer():
    print('[kmer] loading shipped artifacts')
    with open(os.path.join(MODEL_DIR, 'kmer_resistance_model.pkl'), 'rb') as fh:
        art = pickle.load(fh)
    model, scaler, ab_list = art['model'], art['scaler'], art['ab_list']
    ab_idx = {a: i for i, a in enumerate(ab_list)}
    fasta_root = os.path.join(data_prep.data_root(), 'fasta_output')

    def resolve(p):
        parts = str(p).replace('\\', '/').split('/')
        return os.path.join(fasta_root, *parts[parts.index('fasta_output') + 1:])

    files = sorted(glob.glob(os.path.join(data_prep.data_root(), 'mapped_output', '*_mapped.csv')))
    frames = []
    for i, f in enumerate(files):
        d = pd.read_csv(f, low_memory=False)
        d['_train_file'] = i < KMER_TRAIN_FILES
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=['Antibiotic', 'Resistant Phenotype', 'fasta_path'])
    df = df[df['Resistant Phenotype'].isin(['Susceptible', 'Intermediate', 'Resistant'])].copy()
    df['label'] = (df['Resistant Phenotype'] != 'Susceptible').astype(int)
    df['ab'] = df['Antibiotic'].astype(str).str.lower().str.strip()
    df['path'] = df['fasta_path'].map(resolve)
    seen = set(df.loc[df._train_file, 'Genome ID'])
    df['unseen'] = ~df['Genome ID'].isin(seen)

    train_rows = df[~df.unseen]
    train_profile = profile(train_rows.assign(
        genus=train_rows['Genome Name'].astype(str).str.split().str[0].str.capitalize(),
        Antibiotic=train_rows['ab'], target=train_rows['label'],
        is_lab_confirmed=(train_rows['Evidence'].astype(str) == 'Laboratory Method').astype(int)))
    all_genomes = int(df['Genome ID'].nunique())
    reconstruction = {
        'training_files': KMER_TRAIN_FILES,
        'antibiotics_match': set(df.loc[df._train_file, 'Antibiotic']) == set(ab_list),
    }
    print(f'[kmer] reconstruction {reconstruction}')

    print(f'[kmer] reading {df.path.nunique():,} genomes')
    with Pool(min(8, os.cpu_count() or 1)) as pool:
        feats = dict(pool.imap_unordered(_genome_features, df['path'].unique().tolist(), chunksize=8))
    df = df[df['path'].map(lambda p: feats.get(p) is not None)].copy()

    K = np.stack([feats[p][0] for p in df['path']])
    E = np.stack([feats[p][1] for p in df['path']])
    A = np.zeros((len(df), len(ab_list)), np.float32)
    for r, a in enumerate(df['ab']):
        if a in ab_idx:
            A[r, ab_idx[a]] = 1
    # Scaler on the 256 k-mer columns only, as in training
    df['score'] = model.predict_proba(np.hstack([scaler.transform(K), A, E]))[:, 1]

    # Baseline that ignores the genome: the drug's resistance rate in training rows
    rate = df[~df.unseen].groupby('ab')['label'].mean()
    df['drug_only'] = df['ab'].map(rate).fillna(df.loc[~df.unseen, 'label'].mean())

    def run(name, d, col='score', roc=False):
        return summarise(name, d.label.to_numpy(), d[col].to_numpy(),
                         d['Genome ID'].to_numpy(), 0.5, roc)

    seen_df, un = df[~df.unseen], df[df.unseen & df.ab.isin(ab_idx)]
    rows = [
        run('Genomes it trained on', seen_df, roc=True),
        run('Genomes it never saw', un, roc=True),
        run('Drug-only baseline, genome ignored', un, col='drug_only', roc=True),
    ]

    per = []
    for a, g in un.groupby('ab'):
        if g.label.nunique() == 2 and len(g) >= 50:
            per.append({'antibiotic': a, 'rows': int(len(g)),
                        'auc_roc': round(roc_auc_score(g.label, g.score), 4)})
    per.sort(key=lambda r: -r['rows'])
    within = float(np.average([p['auc_roc'] for p in per], weights=[p['rows'] for p in per]))
    print(f'[kmer] within-antibiotic AUC {within:.4f} over {len(per)} drugs')

    # What /predict actually returns: the backend predictor, as deployed
    sys.path.insert(0, os.path.join(ROOT, 'backend'))
    import contextlib
    import io
    from ml_models.resistance_predictor import KmerResistancePredictor
    with contextlib.redirect_stdout(io.StringIO()):
        served = KmerResistancePredictor(MODEL_DIR)
    sample = un.sample(100, random_state=0)
    fallbacks = 0
    for _, r in sample.iterrows():
        buf = io.StringIO()
        with open(r.path) as fh, contextlib.redirect_stdout(buf):
            served.predict(fh.read(), r.ab)
        fallbacks += 'Prediction error' in buf.getvalue()
    print(f'[kmer] /predict fell back to the heuristic on {fallbacks}/100 calls')

    return {
        'name': 'K-mer RandomForest', 'page': '/predict',
        'artifact': 'backend/trained_models/kmer_resistance_model.pkl',
        'trees': len(model.estimators_), 'known_antibiotics': len(ab_list),
        'train_rows': int(len(seen_df)), 'train_genomes': int(seen_df['Genome ID'].nunique()),
        'source': 'mapped_output + fasta_output', 'files_used': KMER_TRAIN_FILES,
        'files_total': len(files), 'genomes_with_fasta': all_genomes,
        'train_profile': train_profile,
        'claimed_auc': 0.929, 'split': 'random row-level 80/20, stratified',
        'reconstruction': reconstruction, 'results': rows,
        'within_antibiotic_auc': round(within, 4), 'per_antibiotic': per[:15],
        'served_fallback_rate': fallbacks / 100,
    }


if __name__ == '__main__':
    report = {'lightgbm': evaluate_lgbm(), 'kmer': evaluate_kmer()}
    with open(OUT, 'w') as fh:
        json.dump(report, fh, indent=1)
    print(f'wrote {os.path.relpath(OUT, ROOT)}')
