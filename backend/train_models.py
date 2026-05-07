"""
Train all available AMR models.
Run: python train_models.py [--model lgbm|kmer|all]
"""
import os
import sys
import glob
import re
import pickle
import argparse
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)
MODEL_DIR = os.path.join(BASE_DIR, 'trained_models')

sys.path.insert(0, BASE_DIR)

os.makedirs(MODEL_DIR, exist_ok=True)

MIC_SIGN_MAP = {'<=': -1.0, '<': -0.5, '=': 0.0, '==': 0.0, 'exact': 0.0, '>=': 1.0, '>': 0.5, 'unknown': 0.0}

DRUG_CLASS_MAP = {
    'ampicillin': 'beta_lactam', 'amoxicillin': 'beta_lactam',
    'amoxicillin/clavulanic acid': 'beta_lactam', 'piperacillin': 'beta_lactam',
    'piperacillin/tazobactam': 'beta_lactam', 'oxacillin': 'beta_lactam',
    'cefazolin': 'beta_lactam', 'cefoxitin': 'beta_lactam', 'cefotaxime': 'beta_lactam',
    'ceftazidime': 'beta_lactam', 'ceftriaxone': 'beta_lactam', 'cefepime': 'beta_lactam',
    'cefuroxime': 'beta_lactam', 'cephalothin': 'beta_lactam',
    'imipenem': 'carbapenem', 'meropenem': 'carbapenem', 'ertapenem': 'carbapenem', 'doripenem': 'carbapenem',
    'aztreonam': 'monobactam',
    'ciprofloxacin': 'fluoroquinolone', 'levofloxacin': 'fluoroquinolone',
    'norfloxacin': 'fluoroquinolone', 'nalidixic acid': 'fluoroquinolone', 'ofloxacin': 'fluoroquinolone',
    'gentamicin': 'aminoglycoside', 'tobramycin': 'aminoglycoside', 'amikacin': 'aminoglycoside',
    'streptomycin': 'aminoglycoside', 'neomycin': 'aminoglycoside', 'kanamycin': 'aminoglycoside',
    'tetracycline': 'tetracycline', 'doxycycline': 'tetracycline',
    'minocycline': 'tetracycline', 'tigecycline': 'tetracycline',
    'sulfamethoxazole': 'sulfonamide', 'trimethoprim': 'sulfonamide',
    'trimethoprim/sulfamethoxazole': 'sulfonamide', 'chloramphenicol': 'phenicol',
    'azithromycin': 'macrolide', 'erythromycin': 'macrolide',
    'colistin': 'polymyxin', 'polymyxin b': 'polymyxin',
    'vancomycin': 'glycopeptide', 'teicoplanin': 'glycopeptide',
    'clindamycin': 'lincosamide', 'nitrofurantoin': 'nitrofuran',
    'rifampicin': 'rifamycin', 'rifampin': 'rifamycin',
}


def load_amr_data(data_dir, max_files=500):
    """Load and combine AMR output CSV files."""
    amr_dir = os.path.join(data_dir, 'amr_output')
    if not os.path.exists(amr_dir):
        print(f"[Data] amr_output not found at {amr_dir}")
        return None

    csv_files = glob.glob(os.path.join(amr_dir, '*.csv'))
    csv_files = [f for f in csv_files if not f.endswith('.tmp')]
    print(f"[Data] Found {len(csv_files)} AMR CSV files. Loading up to {max_files}...")

    frames = []
    for i, f in enumerate(csv_files[:max_files]):
        try:
            df = pd.read_csv(f, low_memory=False)
            frames.append(df)
        except Exception:
            continue
        if (i + 1) % 100 == 0:
            print(f"  Loaded {i+1} files...")

    if not frames:
        return None
    combined = pd.concat(frames, ignore_index=True)
    print(f"[Data] Combined shape: {combined.shape}")
    return combined


def parse_mic_sign(val):
    if pd.isna(val): return 'unknown'
    val = str(val).strip()
    for op in ['<=', '>=', '==', '<', '>', '=']:
        if val.startswith(op): return op
    return 'exact'


def parse_mic_numeric(val):
    if pd.isna(val): return np.nan
    m = re.search(r'(\d+\.?\d*)', str(val))
    return float(m.group(1)) if m else np.nan


def clean_amr_data(df_raw):
    """Replicate the LightGBM notebook cleaning pipeline."""
    df = df_raw.copy()

    df['mic_sign'] = df['Measurement'].apply(parse_mic_sign)
    df['mic_value'] = df['Measurement'].apply(parse_mic_numeric)
    mask = df['mic_value'].isna()
    df.loc[mask, 'mic_value'] = df.loc[mask, 'Measurement Value'].astype(str).apply(parse_mic_numeric)
    df['has_mic'] = df['mic_value'].notna().astype(int)
    df['mic_log'] = np.log1p(df['mic_value'].clip(lower=0))

    def extract_parts(name):
        if pd.isna(name): return pd.Series({'genus': 'unknown', 'species': 'unknown'})
        parts = str(name).strip().split(None, 2)
        genus = parts[0].capitalize() if parts else 'unknown'
        species = parts[1].lower() if len(parts) > 1 else 'unknown'
        return pd.Series({'genus': genus, 'species': species})

    genome_parts = df['Genome Name'].apply(extract_parts)
    df = pd.concat([df, genome_parts], axis=1)

    merge_map = {'Susceptible': 'Susceptible', 'Resistant': 'Resistant',
                 'Intermediate': 'Resistant', 'Nonsusceptible': 'Resistant'}
    df_labeled = df[df['Resistant Phenotype'].notna()].copy()
    df_labeled['Resistant Phenotype'] = df_labeled['Resistant Phenotype'].map(merge_map)
    df_labeled = df_labeled[df_labeled['Resistant Phenotype'].notna()]
    df_labeled['target'] = (df_labeled['Resistant Phenotype'] == 'Resistant').astype(int)

    df_labeled['Antibiotic'] = df_labeled['Antibiotic'].str.strip().str.lower()
    df_labeled['drug_class'] = df_labeled['Antibiotic'].map(DRUG_CLASS_MAP).fillna('other')
    df_labeled['is_lab_confirmed'] = (df_labeled.get('Evidence', '') == 'Laboratory Method').astype(int)

    def extract_f1(text):
        if pd.isna(text): return np.nan
        m = re.search(r'F1 score:\s*([\d.]+)', str(text))
        return float(m.group(1)) if m else np.nan

    df_labeled['computational_f1'] = df_labeled['Computational Method Performance'].apply(extract_f1)
    df_labeled.loc[df_labeled['is_lab_confirmed'] == 1, 'computational_f1'] = 1.0
    median_f1 = df_labeled['computational_f1'].median()
    df_labeled['computational_f1'] = df_labeled['computational_f1'].fillna(0.85 if pd.isna(median_f1) else median_f1)

    # Deduplicate
    df_labeled = (df_labeled
                  .sort_values(['Genome ID', 'Antibiotic', 'is_lab_confirmed'], ascending=[True, True, False])
                  .drop_duplicates(subset=['Genome ID', 'Antibiotic'], keep='first')
                  .reset_index(drop=True))

    print(f"[Clean] Cleaned shape: {df_labeled.shape}")
    vc = df_labeled['target'].value_counts()
    print(f"[Clean] Target: Susceptible={vc.get(0,0):,} | Resistant={vc.get(1,0):,}")
    return df_labeled


def train_lgbm(data_dir, model_dir):
    """Train LightGBM resistance forecasting model."""
    import joblib
    try:
        import lightgbm as lgb
    except ImportError:
        print("[LightGBM] lightgbm not installed. Run: pip install lightgbm")
        return False

    from sklearn.model_selection import train_test_split
    from sklearn.metrics import roc_auc_score, classification_report

    print("\n" + "="*60)
    print("  TRAINING LIGHTGBM AMR RESISTANCE FORECASTING MODEL")
    print("="*60)

    df_raw = load_amr_data(data_dir)
    if df_raw is None or len(df_raw) < 100:
        print("[LightGBM] Insufficient data for training.")
        return False

    df = clean_amr_data(df_raw)
    if len(df) < 50:
        print("[LightGBM] Too few labeled samples.")
        return False

    BASE_FEATURES = ['Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species',
                     'mic_sign', 'is_lab_confirmed', 'computational_f1',
                     'mic_value', 'mic_log', 'has_mic']
    TARGET = 'target'

    for feat in BASE_FEATURES:
        if feat not in df.columns:
            df[feat] = 0 if feat not in ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign'] else 'unknown'

    global_mean = df[TARGET].mean()
    print(f"[LightGBM] Global resistance rate: {global_mean:.4f}")

    # Target encoding
    ab_rate = df.groupby('Antibiotic')[TARGET].mean()
    taxon_ab = df.groupby(['Taxon ID', 'Antibiotic'])[TARGET].agg(['sum', 'count'])
    taxon_ab = taxon_ab[taxon_ab['count'] >= 3].assign(rate=lambda x: x['sum']/x['count'])['rate'].reset_index()
    taxon_ab.columns = ['Taxon ID', 'Antibiotic', 'taxon_ab_resistance_rate']
    genus_ab = df.groupby(['genus', 'Antibiotic'])[TARGET].agg(['sum', 'count'])
    genus_ab = genus_ab[genus_ab['count'] >= 3].assign(rate=lambda x: x['sum']/x['count'])['rate'].reset_index()
    genus_ab.columns = ['genus', 'Antibiotic', 'genus_ab_resistance_rate']

    df['ab_resistance_rate'] = df['Antibiotic'].map(ab_rate).fillna(global_mean)
    df = df.merge(taxon_ab, on=['Taxon ID', 'Antibiotic'], how='left')
    df['taxon_ab_resistance_rate'] = df.get('taxon_ab_resistance_rate', pd.Series(global_mean, index=df.index)).fillna(df['ab_resistance_rate'])
    df = df.merge(genus_ab, on=['genus', 'Antibiotic'], how='left')
    df['genus_ab_resistance_rate'] = df.get('genus_ab_resistance_rate', pd.Series(global_mean, index=df.index)).fillna(df['ab_resistance_rate'])

    FINAL_FEATURES = BASE_FEATURES + ['ab_resistance_rate', 'taxon_ab_resistance_rate', 'genus_ab_resistance_rate']
    CAT_FEATURES = ['Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign']

    for col in CAT_FEATURES:
        df[col] = df[col].astype('category')

    X = df[FINAL_FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)

    X_tr, X_val, y_tr, y_val = train_test_split(X_train, y_train, test_size=0.15, stratify=y_train, random_state=42)

    lgb_train = lgb.Dataset(X_tr, label=y_tr, categorical_feature=CAT_FEATURES)
    lgb_val = lgb.Dataset(X_val, label=y_val, categorical_feature=CAT_FEATURES, reference=lgb_train)

    params = {
        'objective': 'binary', 'metric': 'auc', 'boosting_type': 'gbdt',
        'verbose': -1, 'random_state': 42, 'n_jobs': -1,
        'num_leaves': 63, 'learning_rate': 0.05, 'n_estimators': 500,
        'subsample': 0.8, 'colsample_bytree': 0.8,
        'reg_alpha': 0.1, 'reg_lambda': 1.0, 'is_unbalance': True,
        'cat_smooth': 10, 'max_cat_threshold': 32,
    }

    print("[LightGBM] Training...")
    model = lgb.train(
        params, lgb_train, valid_sets=[lgb_val],
        callbacks=[lgb.early_stopping(30, verbose=False), lgb.log_evaluation(100)]
    )

    y_pred_proba = model.predict(X_test[FINAL_FEATURES])
    y_pred = (y_pred_proba >= 0.40).astype(int)
    auc = roc_auc_score(y_test, y_pred_proba)
    print(f"\n[LightGBM] Test AUC-ROC: {auc:.4f}")
    print(classification_report(y_test, y_pred, target_names=['Susceptible', 'Resistant']))

    model_path = os.path.join(model_dir, 'amr_lgbm_final_model.txt')
    model.save_model(model_path)
    joblib.dump(ab_rate, os.path.join(model_dir, 'ab_rate_full.joblib'))
    joblib.dump(taxon_ab, os.path.join(model_dir, 'taxon_ab_rate_full.joblib'))
    joblib.dump(genus_ab, os.path.join(model_dir, 'genus_ab_rate_full.joblib'))
    joblib.dump({'global_mean': global_mean}, os.path.join(model_dir, 'lgbm_meta.joblib'))

    print(f"[LightGBM] Model saved to {model_path}")
    return True


def train_kmer(data_dir, model_dir):
    """Train K-mer RandomForest resistance prediction model."""
    import glob
    from itertools import product
    from collections import Counter
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report, roc_auc_score

    print("\n" + "="*60)
    print("  TRAINING K-MER RESISTANCE PREDICTION MODEL")
    print("="*60)

    NUCLEOTIDES = ['A', 'T', 'C', 'G']
    K = 4
    ALL_KMERS = [''.join(p) for p in product(NUCLEOTIDES, repeat=K)]
    _STRIP = str.maketrans('', '', ''.join(c for c in map(chr, range(256)) if c not in 'ATCG'))

    mapped_dir = os.path.join(data_dir, 'mapped_output')
    fasta_dir = os.path.join(data_dir, 'fasta_output')

    if not os.path.exists(mapped_dir):
        mapped_dir = os.path.join(data_dir, 'sample_mapped_output')
        fasta_dir = os.path.join(data_dir, 'sample_fasta_output')
        print(f"[K-mer] Using sample data from {mapped_dir}")

    csv_files = glob.glob(os.path.join(mapped_dir, '*.csv'))
    if not csv_files:
        print("[K-mer] No mapped CSV files found.")
        return False

    print(f"[K-mer] Found {len(csv_files)} mapped CSV files. Loading...")
    frames = []
    for f in csv_files[:200]:
        try:
            frames.append(pd.read_csv(f, low_memory=False))
        except Exception:
            continue

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=['Antibiotic', 'Resistant Phenotype', 'fasta_path'])
    LABEL_MAP = {'Susceptible': 0, 'Intermediate': 1, 'Resistant': 1}
    df = df[df['Resistant Phenotype'].isin(LABEL_MAP)].copy()
    df['label'] = df['Resistant Phenotype'].map(LABEL_MAP)
    print(f"[K-mer] {len(df)} labeled rows. Loading FASTA sequences...")

    ab_list = sorted(df['Antibiotic'].unique().tolist())
    N_AB = len(ab_list)
    ab_to_idx = {a: i for i, a in enumerate(ab_list)}
    print(f"[K-mer] Antibiotics: {N_AB}")

    def read_fasta(path, max_bp=500_000):
        try:
            with open(path, 'r') as f:
                seq = ''.join(line.strip() for line in f if not line.startswith('>')).upper().translate(_STRIP)
            return seq[:max_bp]
        except Exception:
            return None

    def kmer_freq(seq):
        if not seq or len(seq) < K + 5:
            return None
        counter = Counter(seq[i:i+K] for i in range(len(seq) - K + 1))
        counts = np.array([counter.get(km, 0) for km in ALL_KMERS], dtype=np.float32)
        total = counts.sum()
        return counts / total if total > 0 else None

    X_list, y_list = [], []
    seen_fasta = {}
    skipped = 0

    for _, row in df.iterrows():
        fasta_path = str(row['fasta_path']).replace('\\', os.sep).replace('/', os.sep)
        if not os.path.exists(fasta_path):
            # Try to resolve relative to fasta_dir
            parts = fasta_path.replace('\\', '/').split('/')
            try:
                idx = next(i for i, p in enumerate(parts) if p == 'fasta_output')
                rel = os.path.join(*parts[idx+1:])
                fasta_path = os.path.join(fasta_dir, rel)
            except StopIteration:
                fasta_path = os.path.join(fasta_dir, os.path.basename(fasta_path))

        if fasta_path not in seen_fasta:
            seq = read_fasta(fasta_path)
            seen_fasta[fasta_path] = seq

        seq = seen_fasta[fasta_path]
        if seq is None:
            skipped += 1
            continue

        vec = kmer_freq(seq)
        if vec is None:
            skipped += 1
            continue

        ab_vec = np.zeros(N_AB, dtype=np.float32)
        ab_key = str(row['Antibiotic']).lower().strip()
        if ab_key in ab_to_idx:
            ab_vec[ab_to_idx[ab_key]] = 1.0

        gc = sum(1 for c in seq if c in 'GC') / max(len(seq), 1)
        extra = np.array([gc, 1.0 - gc, len(seq) / 500000.0], dtype=np.float32)
        feat = np.concatenate([vec, ab_vec, extra])

        X_list.append(feat)
        y_list.append(int(row['label']))

    print(f"[K-mer] Built {len(X_list)} samples. Skipped: {skipped}")
    if len(X_list) < 10:
        print("[K-mer] Insufficient FASTA data. Skipping K-mer model training.")
        return False

    X = np.array(X_list)
    y = np.array(y_list)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None)

    scaler = StandardScaler()
    n_kmer = len(ALL_KMERS)
    X_train[:, :n_kmer] = scaler.fit_transform(X_train[:, :n_kmer])
    X_test[:, :n_kmer] = scaler.transform(X_test[:, :n_kmer])

    print(f"[K-mer] Training RandomForest on {len(X_train)} samples...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42, n_jobs=-1, class_weight='balanced')
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    y_prob = clf.predict_proba(X_test)[:, 1]
    print(f"[K-mer] Test samples: {len(y_test)}")
    print(classification_report(y_test, y_pred, target_names=['Susceptible', 'Resistant']))
    if len(np.unique(y_test)) > 1:
        print(f"[K-mer] ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

    model_path = os.path.join(model_dir, 'kmer_resistance_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'model': clf, 'scaler': scaler, 'ab_list': ab_list, 'ALL_KMERS': ALL_KMERS}, f)
    print(f"[K-mer] Model saved to {model_path}")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train AMR models')
    parser.add_argument('--model', default='all', choices=['lgbm', 'kmer', 'all'])
    args = parser.parse_args()

    data_dir = ROOT_DIR

    if args.model in ('lgbm', 'all'):
        train_lgbm(data_dir, MODEL_DIR)

    if args.model in ('kmer', 'all'):
        train_kmer(data_dir, MODEL_DIR)

    print("\n[Training] Complete!")
