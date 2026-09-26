"""
Train all available AMR models.
Run: python train_models.py [--model lgbm|kmer|all]
"""
import os
import sys
import glob
import random
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
# Default output, the same place /api/train/ uses. The served model changes
# only through experiments/promote.py, which also writes its metrics.json.
CANDIDATE_DIR = os.path.join(MODEL_DIR, 'candidates')

sys.path.insert(0, BASE_DIR)

os.makedirs(MODEL_DIR, exist_ok=True)

MIC_SIGN_MAP = {'<=': -1.0, '<': -0.5, '=': 0.0, '==': 0.0, 'exact': 0.0, '>=': 1.0, '>': 0.5, 'unknown': 0.0}

# Keep in step with DRUG_CLASS_MAP in experiments/lib/data_prep.py; the
# backend deploys without experiments/. lgbm_predictor.py imports this one.
DRUG_CLASS_MAP = {
    'ampicillin': 'beta_lactam', 'amoxicillin': 'beta_lactam',
    'amoxicillin/clavulanic acid': 'beta_lactam', 'piperacillin': 'beta_lactam',
    'piperacillin/tazobactam': 'beta_lactam', 'oxacillin': 'beta_lactam',
    'ampicillin/sulbactam': 'beta_lactam', 'penicillin': 'beta_lactam',
    'methicillin': 'beta_lactam', 'carbenicillin': 'beta_lactam',
    'cefazolin': 'beta_lactam', 'cefoxitin': 'beta_lactam', 'cefotaxime': 'beta_lactam',
    'ceftazidime': 'beta_lactam', 'ceftriaxone': 'beta_lactam', 'cefepime': 'beta_lactam',
    'cefuroxime': 'beta_lactam', 'cephalothin': 'beta_lactam', 'cefalothin': 'beta_lactam',
    'ceftazidime/avibactam': 'beta_lactam', 'ceftolozane/tazobactam': 'beta_lactam',
    'ceftiofur': 'beta_lactam', 'cefpodoxime': 'beta_lactam',
    'imipenem': 'carbapenem', 'meropenem': 'carbapenem', 'ertapenem': 'carbapenem',
    'doripenem': 'carbapenem', 'aztreonam': 'monobactam',
    'ciprofloxacin': 'fluoroquinolone', 'levofloxacin': 'fluoroquinolone',
    'norfloxacin': 'fluoroquinolone', 'nalidixic acid': 'fluoroquinolone',
    'ofloxacin': 'fluoroquinolone', 'moxifloxacin': 'fluoroquinolone',
    'pefloxacin': 'fluoroquinolone', 'trovafloxacin': 'fluoroquinolone',
    'gentamicin': 'aminoglycoside', 'tobramycin': 'aminoglycoside',
    'amikacin': 'aminoglycoside', 'streptomycin': 'aminoglycoside',
    'neomycin': 'aminoglycoside', 'kanamycin': 'aminoglycoside',
    'spectinomycin': 'aminoglycoside', 'capreomycin': 'aminoglycoside',
    'tetracycline': 'tetracycline', 'doxycycline': 'tetracycline',
    'minocycline': 'tetracycline', 'tigecycline': 'tetracycline',
    'sulfamethoxazole': 'sulfonamide', 'trimethoprim': 'sulfonamide',
    'trimethoprim/sulfamethoxazole': 'sulfonamide', 'sulfisoxazole': 'sulfonamide',
    'chloramphenicol': 'phenicol',
    'azithromycin': 'macrolide', 'erythromycin': 'macrolide',
    'telithromycin': 'macrolide', 'clarithromycin': 'macrolide',
    'colistin': 'polymyxin', 'polymyxin b': 'polymyxin',
    'vancomycin': 'glycopeptide', 'teicoplanin': 'glycopeptide',
    'clindamycin': 'lincosamide', 'nitrofurantoin': 'nitrofuran',
    'rifampicin': 'rifamycin', 'rifampin': 'rifamycin', 'rifabutin': 'rifamycin',
    'linezolid': 'oxazolidinone', 'daptomycin': 'lipopeptide',
    'fusidic acid': 'fusidane', 'quinupristin/dalfopristin': 'streptogramin',
    'pristinamycin': 'streptogramin', 'cephalexin': 'beta_lactam',
    'cefpodoxime/clavulanic acid': 'beta_lactam', 'ticarcillin/clavulanic acid': 'beta_lactam',
    'isoniazid': 'antitubercular', 'ethambutol': 'antitubercular',
    'pyrazinamide': 'antitubercular', 'ethionamide': 'antitubercular',
    'prothionamide': 'antitubercular', 'cycloserine': 'antitubercular',
    'para-aminosalicylic acid': 'antitubercular', 'clofazimine': 'antitubercular',
    'delamanid': 'antitubercular', 'bedaquiline': 'antitubercular',
    # v4: drugs in the export (or the UI list) that fell into 'other'.
    # Only azidothymidine (an antiviral) is left there on purpose.
    'cefixime': 'beta_lactam', 'cefpirome': 'beta_lactam', 'cefoperazone': 'beta_lactam',
    'cefotetan': 'beta_lactam', 'cefiderocol': 'beta_lactam', 'ceftaroline': 'beta_lactam',
    'cefovecin': 'beta_lactam', 'cefamandole': 'beta_lactam', 'cefaclor': 'beta_lactam',
    'cefmetazole': 'beta_lactam', 'ceftizoxime': 'beta_lactam', 'cefdinir': 'beta_lactam',
    'cefozopran': 'beta_lactam', 'ceftobiprole': 'beta_lactam', 'ceftibuten': 'beta_lactam',
    'ceftriaxone/cefpodoxime': 'beta_lactam', 'cefotaxime/clavulanic acid': 'beta_lactam',
    'ceftazidime/clavulanic acid': 'beta_lactam', 'cefoperazone/sulbactam': 'beta_lactam',
    'cefepime/taniborbactam': 'beta_lactam', 'temocillin': 'beta_lactam',
    'ticarcillin': 'beta_lactam', 'mecillinam': 'beta_lactam', 'sulbactam': 'beta_lactam',
    'imipenem/relebactam': 'carbapenem',
    'netilmicin': 'aminoglycoside', 'plazomicin': 'aminoglycoside', 'apramycin': 'aminoglycoside',
    'gatifloxacin': 'fluoroquinolone', 'enrofloxacin': 'fluoroquinolone',
    'danofloxacin': 'fluoroquinolone', 'sparfloxacin': 'fluoroquinolone',
    'pradofloxacin': 'fluoroquinolone', 'delafloxacin': 'fluoroquinolone',
    'chlortetracycline': 'tetracycline', 'oxytetracycline': 'tetracycline',
    'eravacycline': 'tetracycline', 'omadacycline': 'tetracycline',
    'sulfathiazole': 'sulfonamide', 'sulfamethazine': 'sulfonamide',
    'trimethoprim/sulfobactam': 'sulfonamide',
    'tylosin': 'macrolide', 'tulathromycin': 'macrolide', 'spiramycin': 'macrolide',
    'florfenicol': 'phenicol', 'lincomycin': 'lincosamide', 'virginiamycin': 'streptogramin',
    'furazolidone': 'nitrofuran', 'metronidazole': 'nitroimidazole',
    'fosfomycin': 'phosphonic_acid', 'mupirocin': 'pseudomonic_acid',
    'zoliflodacin': 'spiropyrimidinetrione', 'avilamycin': 'orthosomycin',
    'nicotinamide': 'antitubercular',   # all 229 rows are Mycobacterium
}

# Spelling variants, typos and non-drugs in the raw Antibiotic column.
# None means drop the row. Keep in step with ANTIBIOTIC_ALIASES in
# experiments/lib/data_prep.py; the backend deploys without experiments/.
ANTIBIOTIC_ALIASES = {
    'ampicillin-sulbactam': 'ampicillin/sulbactam',
    'ampicillin_clavulanic_acid': 'amoxicillin/clavulanic acid',
    'amoxicillin-clavulanic acid': 'amoxicillin/clavulanic acid',
    'piperacillin-tazobactam': 'piperacillin/tazobactam',
    'trimethoprim-sulfamethoxazole': 'trimethoprim/sulfamethoxazole',
    'sulfamethoxazole/trimethoprim': 'trimethoprim/sulfamethoxazole',
    'co_trimoxazole': 'trimethoprim/sulfamethoxazole',
    'co-trimoxazole': 'trimethoprim/sulfamethoxazole',
    'geamycin': 'gentamicin',
    'trimotheprim': 'trimethoprim',
    'cefalothin': 'cephalothin',
    'rifampin': 'rifampicin',
    'tazobactam_piperacillin': 'piperacillin/tazobactam',
    'ceftazidime_avibactam': 'ceftazidime/avibactam',
    'ceftolozane_tazobactam': 'ceftolozane/tazobactam',
    'ticarcillin_clavulanate': 'ticarcillin/clavulanic acid',
    'cefpodoxime_clavulanic_acid': 'cefpodoxime/clavulanic acid',
    'trimethoprim_sulfobactam': 'trimethoprim/sulfobactam',
    'para_aminosalicylic_acid': 'para-aminosalicylic acid',
    'cefepime_taniborbactam': 'cefepime/taniborbactam',
    'amoxicillin_clavulanat': 'amoxicillin/clavulanic acid',
    'polymyxin_b': 'polymyxin b',
    'ceftazidime-avibactam': 'ceftazidime/avibactam',
    'ceftolozane-tazobactam': 'ceftolozane/tazobactam',
    'imipenem-relebactam': 'imipenem/relebactam',
    'amipicillin_sulbactam': 'ampicillin/sulbactam',
    'tgecycline': 'tigecycline',
    'cefuroxim\u00e2': 'cefuroxime',
    'pristimycin': 'pristinamycin',
    'cefotaxime/clavulanic acid\u00e2': 'cefotaxime/clavulanic acid',
    'tigecyklin': 'tigecycline',
    'tetracyklin': 'tetracycline',
    'cefpirom': 'cefpirome',
    'strofurantoin': 'nitrofurantoin',
    'cefuroxime_sodium': 'cefuroxime',
    'cefalotin': 'cephalothin',
    'cefalexin': 'cephalexin',
    'synercid': 'quinupristin/dalfopristin',
    'phosphomycin': 'fosfomycin',
    'benzylpenicillin': 'penicillin',
    'carbapenem': None,
    'beta-lactam': None,
    'cephalosporin': None,
    'fluoroquinolones': None,
    'aminogycosides': None,
    'macrolides': None,
    'sulfonamides': None,
    'sulfa': None,
    'extended spectrum beta lactamase': None,
    'instrument': None,
}


def normalize_antibiotics(names):
    """Lower-case, strip and alias antibiotic names. Returns (names, keep_mask)."""
    names = names.astype(str).str.strip().str.lower()
    drop = {k for k, v in ANTIBIOTIC_ALIASES.items() if v is None}
    rename = {k: v for k, v in ANTIBIOTIC_ALIASES.items() if v is not None}
    return names.replace(rename), ~names.isin(drop)


# Taxon ID -> species taxon ID, from NCBI Taxonomy. Built by
# experiments/build_taxonomy.py; the export's Taxon IDs are mostly strain level
# (E. coli is spread over ~1,200 IDs and never appears as 562).
TAXON_SPECIES_PATH = os.path.join(BASE_DIR, 'taxon_species.csv')


def load_species_map(path=TAXON_SPECIES_PATH):
    """{taxon_id: species_taxon_id}; species IDs map to themselves.

    IDs above species level (a bare genus) map to themselves too. Returns an
    empty dict if the table is missing, which leaves Taxon IDs unchanged.
    """
    if not os.path.exists(path):
        print(f"[Taxonomy] {path} not found, Taxon IDs stay strain level")
        return {}
    table = pd.read_csv(path)
    species = table['species_taxon_id'].fillna(table['taxon_id']).astype(int)
    mapping = dict(zip(table['taxon_id'].astype(int), species))
    mapping.update({sid: sid for sid in species.unique()})
    return mapping


def to_species_taxon(taxon_ids, mapping=None):
    """Map a Series of Taxon IDs to species level; unknown IDs pass through."""
    mapping = load_species_map() if mapping is None else mapping
    ids = pd.to_numeric(taxon_ids, errors='coerce')
    return ids.map(mapping).fillna(ids)


DATA_SUBDIRS = ('amr_output', 'mapped_output', 'sample_mapped_output')


def resolve_data_dir(base):
    """The folder holding amr_output/ and mapped_output/, or None.

    Accepts either that folder or the project root, where the data lives in
    Data/ (data/ on a case-sensitive clone). Both the command line and
    /api/train/ pass the project root.
    """
    for candidate in (base, os.path.join(base, 'Data'), os.path.join(base, 'data')):
        if any(os.path.isdir(os.path.join(candidate, d)) for d in DATA_SUBDIRS):
            return candidate
    return None


def select_files(files, max_files=None, seed=42):
    """Sorted file list, optionally a seeded random subset.

    The old code took the first N files of an unsorted directory listing.
    On the machine that trained the shipped models that listing was
    alphabetical by taxon ID, so the LightGBM never saw Klebsiella. A random
    subset keeps every genus in proportion.
    """
    files = sorted(f for f in files if not f.endswith('.tmp'))
    if max_files and len(files) > max_files:
        files = sorted(random.Random(seed).sample(files, max_files))
    return files


def load_amr_data(data_dir, max_files=None):
    """Load and combine AMR output CSV files (all of them unless max_files)."""
    amr_dir = os.path.join(data_dir, 'amr_output')
    if not os.path.exists(amr_dir):
        print(f"[Data] amr_output not found at {amr_dir}")
        return None

    found = glob.glob(os.path.join(amr_dir, '*.csv'))
    csv_files = select_files(found, max_files)
    print(f"[Data] Found {len(found)} AMR CSV files. Loading {len(csv_files)}...")

    frames = []
    for i, f in enumerate(csv_files):
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
        parts = str(name).strip().strip('"\'').split(None, 2)  # stray quotes in some names
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

    df_labeled['Antibiotic'], keep = normalize_antibiotics(df_labeled['Antibiotic'])
    df_labeled = df_labeled[keep].copy()
    # Species level, so a user-supplied 562 means the same as the training data
    df_labeled['strain_taxon_id'] = df_labeled['Taxon ID']
    df_labeled['Taxon ID'] = to_species_taxon(df_labeled['Taxon ID'])
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


def train_lgbm(data_dir, model_dir, max_files=None):
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

    data_dir = resolve_data_dir(data_dir)
    if data_dir is None:
        print("[LightGBM] Training data not found (looked for Data/amr_output).")
        return False
    df_raw = load_amr_data(data_dir, max_files)
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

    report_dir = os.path.join(ROOT_DIR, 'report_figures')
    os.makedirs(report_dir, exist_ok=True)
    pd.DataFrame({
        'y_true': y_test.to_numpy(),
        'y_score': y_pred_proba,
    }).to_csv(os.path.join(report_dir, 'lgbm_test_predictions.csv'), index=False)
    print(f"[LightGBM] Test predictions saved to {os.path.join(report_dir, 'lgbm_test_predictions.csv')}")

    model_path = os.path.join(model_dir, 'amr_lgbm_final_model.txt')
    model.save_model(model_path)
    joblib.dump(ab_rate, os.path.join(model_dir, 'ab_rate_full.joblib'))
    joblib.dump(taxon_ab, os.path.join(model_dir, 'taxon_ab_rate_full.joblib'))
    joblib.dump(genus_ab, os.path.join(model_dir, 'genus_ab_rate_full.joblib'))
    joblib.dump({'global_mean': global_mean}, os.path.join(model_dir, 'lgbm_meta.joblib'))

    print(f"[LightGBM] Model saved to {model_path}")
    return True


def train_kmer(data_dir, model_dir, max_files=None):
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

    data_dir = resolve_data_dir(data_dir)
    if data_dir is None:
        print("[K-mer] Training data not found (looked for Data/mapped_output).")
        return False
    mapped_dir = os.path.join(data_dir, 'mapped_output')
    fasta_dir = os.path.join(data_dir, 'fasta_output')

    if not os.path.exists(mapped_dir):
        mapped_dir = os.path.join(data_dir, 'sample_mapped_output')
        fasta_dir = os.path.join(data_dir, 'sample_fasta_output')
        print(f"[K-mer] Using sample data from {mapped_dir}")

    csv_files = select_files(glob.glob(os.path.join(mapped_dir, '*_mapped.csv')), max_files)
    if not csv_files:
        print("[K-mer] No mapped CSV files found.")
        return False

    print(f"[K-mer] Found {len(csv_files)} mapped CSV files. Loading...")
    frames = []
    for f in csv_files:
        try:
            frames.append(pd.read_csv(f, low_memory=False))
        except Exception:
            continue

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=['Antibiotic', 'Resistant Phenotype', 'fasta_path'])
    LABEL_MAP = {'Susceptible': 0, 'Intermediate': 1, 'Resistant': 1}
    df = df[df['Resistant Phenotype'].isin(LABEL_MAP)].copy()
    df['Antibiotic'], keep = normalize_antibiotics(df['Antibiotic'])
    df = df[keep].copy()
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

    report_dir = os.path.join(ROOT_DIR, 'report_figures')
    os.makedirs(report_dir, exist_ok=True)
    pd.DataFrame({
        'y_true': y_test,
        'y_score': y_prob,
    }).to_csv(os.path.join(report_dir, 'kmer_test_predictions.csv'), index=False)
    print(f"[K-mer] Test predictions saved to {os.path.join(report_dir, 'kmer_test_predictions.csv')}")

    model_path = os.path.join(model_dir, 'kmer_resistance_model.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump({'model': clf, 'scaler': scaler, 'ab_list': ab_list, 'ALL_KMERS': ALL_KMERS}, f)
    print(f"[K-mer] Model saved to {model_path}")
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Train AMR models')
    parser.add_argument('--model', default='all', choices=['lgbm', 'kmer', 'all'])
    parser.add_argument('--max-files', type=int, default=None,
                        help='use a seeded random subset of this many CSV files (default: all)')
    parser.add_argument('--model-dir', default=None,
                        help='where to write the artifacts (default: '
                             'backend/trained_models/candidates/<model>, never the served model)')
    args = parser.parse_args()

    data_dir = resolve_data_dir(ROOT_DIR)
    if data_dir is None:
        sys.exit('[Data] Training data not found. Expected Data/amr_output/ in the project root.')
    print(f"[Data] Using {data_dir}")

    for name, train in (('lgbm', train_lgbm), ('kmer', train_kmer)):
        if args.model in (name, 'all'):
            model_dir = args.model_dir or os.path.join(CANDIDATE_DIR, name)
            os.makedirs(model_dir, exist_ok=True)
            train(data_dir, model_dir, args.max_files)

    print("\n[Training] Complete!")
