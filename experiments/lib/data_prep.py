"""Load and clean the raw BV-BRC AMR exports into a modelling table.

One cleaned frame serves every experiment, so cleaning happens once and is
cached. The cache key includes CLEAN_VERSION, bump it whenever the cleaning
logic changes, or old runs become incomparable to new ones without anyone
noticing.

Differences from backend/train_models.py, all deliberate and all recorded on
the frame so an experiment can opt out:
  * the full export is loaded (train_models.py also does now; until
    2026-09-25 it read only the first 500 files)
  * antibiotic spellings are normalised (optional, see normalize_antibiotics)
  * every row keeps a `label_source` so MIC-rule labels can be excluded
"""
import glob
import os
import pickle
import re
import time

import numpy as np
import pandas as pd

CLEAN_VERSION = 'v4'  # v2: extended ANTIBIOTIC_ALIASES; v3: species_taxon_id (2026-09-25); v4: 54 drugs added to DRUG_CLASS_MAP (2026-09-26)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
# Taxon ID -> species, from NCBI; built by experiments/build_taxonomy.py and
# shared with backend/train_models.py
TAXON_SPECIES_PATH = os.path.join(ROOT, 'backend', 'taxon_species.csv')

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

# Spelling variants, typos and non-drugs found in the raw Antibiotic column.
# Left-hand side is what appears in the export; right-hand side is canonical.
# None means "drop these rows", a drug class is not a drug.
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
    # Separator variants of combination drugs
    'tazobactam_piperacillin': 'piperacillin/tazobactam',
    'ceftazidime_avibactam': 'ceftazidime/avibactam',
    'ceftolozane_tazobactam': 'ceftolozane/tazobactam',
    'ticarcillin_clavulanate': 'ticarcillin/clavulanic acid',
    'cefpodoxime_clavulanic_acid': 'cefpodoxime/clavulanic acid',
    'trimethoprim_sulfobactam': 'trimethoprim/sulfobactam',
    'para_aminosalicylic_acid': 'para-aminosalicylic acid',
    # Typos and a broken character encoding
    'amipicillin_sulbactam': 'ampicillin/sulbactam',
    'tgecycline': 'tigecycline',
    'cefuroxim\u00e2': 'cefuroxime',
    'pristimycin': 'pristinamycin',
    # Shigella panel; never on the same genome as nitrofurantoin
    'strofurantoin': 'nitrofurantoin',
    # Alternative names for the same drug
    'cefuroxime_sodium': 'cefuroxime',
    'cefalotin': 'cephalothin',
    'cefalexin': 'cephalexin',
    'synercid': 'quinupristin/dalfopristin',
    # Not a single drug: drug classes, a phenotype, and a lost drug name
    # ('instrument' is 593 C. difficile lab rows with the drug name missing)
    'carbapenem': None,
    'beta-lactam': None,
    'cephalosporin': None,
    'fluoroquinolones': None,
    'aminogycosides': None,
    'macrolides': None,
    'sulfonamides': None,
    'extended spectrum beta lactamase': None,
    'instrument': None,
}

PHENOTYPE_MAP = {
    'Susceptible': 0,
    'Susceptible-dose dependent': 0,
    'Resistant': 1,
    'Intermediate': 1,
    'Nonsusceptible': 1,
    'Reduced Susceptibility': 1,
}

MIC_SIGN_RE = re.compile(r'^\s*(<=|>=|==|<|>|=)')


def species_taxon_ids(taxon_ids):
    """Species-level Taxon IDs. Taxon ID itself is mostly strain level.

    IDs not in the table, or above species level, keep their own value.
    """
    if not os.path.exists(TAXON_SPECIES_PATH):
        print(f'[clean] {TAXON_SPECIES_PATH} missing, species_taxon_id = Taxon ID; '
              f'run experiments/build_taxonomy.py')
        return taxon_ids.copy()
    table = pd.read_csv(TAXON_SPECIES_PATH)
    species = table['species_taxon_id'].fillna(table['taxon_id']).astype('int64')
    mapping = dict(zip(table['taxon_id'].astype('int64'), species))
    return taxon_ids.map(mapping).fillna(taxon_ids).astype('int64')


def _cache_path(source, normalize):
    tag = 'norm' if normalize else 'raw'
    return os.path.join(CACHE_DIR, f'clean_{CLEAN_VERSION}_{source}_{tag}.pkl')


def data_root():
    """The data directory, whatever its capitalisation.

    macOS is case-insensitive so `data/` and `Data/` are interchangeable here,
    but Linux is not, resolving it explicitly keeps the harness portable.
    """
    for name in ('data', 'Data', 'DATA'):
        candidate = os.path.join(ROOT, name)
        if os.path.isdir(candidate):
            return candidate
    return os.path.join(ROOT, 'data')


def load_raw(source='amr_output', max_files=None, verbose=True):
    """Concatenate every AMR CSV under <data root>/<source>/."""
    pattern = os.path.join(data_root(), source, '*.csv')
    files = sorted(f for f in glob.glob(pattern) if not f.endswith('.tmp'))
    if max_files:
        files = files[:max_files]
    if not files:
        raise FileNotFoundError(f'No CSVs matched {pattern}')

    if verbose:
        print(f'[data] reading {len(files):,} files from '
              f'{os.path.relpath(data_root(), ROOT)}/{source}/')
    t0 = time.time()
    frames = []
    for f in files:
        try:
            frames.append(pd.read_csv(f, low_memory=False))
        except Exception:
            continue
    df = pd.concat(frames, ignore_index=True)
    if verbose:
        print(f'[data] {len(df):,} raw rows in {time.time() - t0:.0f}s')
    return df


def clean(df_raw, normalize_antibiotics=True, verbose=True):
    """Raw export → modelling table. Vectorised; no per-row apply."""
    df = df_raw.copy()

    # ── MIC: sign and magnitude ──────────────────────────────────────────
    meas = df['Measurement'].astype('string')
    df['mic_sign'] = meas.str.extract(MIC_SIGN_RE, expand=False).fillna('unknown')
    mic = meas.str.extract(r'(\d+\.?\d*)', expand=False).astype('Float64')
    fallback = df['Measurement Value'].astype('string').str.extract(
        r'(\d+\.?\d*)', expand=False).astype('Float64')
    df['mic_value'] = mic.fillna(fallback).astype('float64')
    df['has_mic'] = df['mic_value'].notna().astype(int)
    df['mic_log'] = np.log1p(df['mic_value'].clip(lower=0))

    # ── Organism ─────────────────────────────────────────────────────────
    name = df['Genome Name'].astype('string').str.strip().str.strip('"\'')  # some names start with a stray quote
    parts = name.str.split(n=2, expand=True)
    df['genus'] = parts[0].str.capitalize().fillna('unknown')
    df['species'] = (parts[1].str.lower() if parts.shape[1] > 1 else 'unknown')
    df['species'] = df['species'].fillna('unknown')

    # ── Antibiotic ───────────────────────────────────────────────────────
    df['Antibiotic'] = df['Antibiotic'].astype('string').str.strip().str.lower()
    if normalize_antibiotics:
        drop = {k for k, v in ANTIBIOTIC_ALIASES.items() if v is None}
        rename = {k: v for k, v in ANTIBIOTIC_ALIASES.items() if v is not None}
        df = df[~df['Antibiotic'].isin(drop)]
        df['Antibiotic'] = df['Antibiotic'].replace(rename)
    df['drug_class'] = df['Antibiotic'].map(DRUG_CLASS_MAP).fillna('other')

    # ── Label ────────────────────────────────────────────────────────────
    df = df[df['Resistant Phenotype'].isin(PHENOTYPE_MAP)].copy()
    df['target'] = df['Resistant Phenotype'].map(PHENOTYPE_MAP).astype(int)

    # Provenance: which rows came from a wet lab and which from a caller.
    evidence = df['Evidence'].astype('string').fillna('')
    df['is_lab_confirmed'] = (evidence == 'Laboratory Method').astype(int)
    df['label_source'] = np.where(df['is_lab_confirmed'] == 1, 'lab', 'computational')

    perf = df['Computational Method Performance'].astype('string')
    f1 = perf.str.extract(r'F1 score:\s*([\d.]+)', expand=False).astype('Float64')
    df['computational_f1'] = f1.astype('float64')
    df.loc[df['is_lab_confirmed'] == 1, 'computational_f1'] = 1.0
    median_f1 = df['computational_f1'].median()
    df['computational_f1'] = df['computational_f1'].fillna(
        0.85 if pd.isna(median_f1) else median_f1)

    # ── One row per (genome, antibiotic), lab result wins ────────────────
    before = len(df)
    df = (df.sort_values(['Genome ID', 'Antibiotic', 'is_lab_confirmed'],
                         ascending=[True, True, False])
            .drop_duplicates(subset=['Genome ID', 'Antibiotic'], keep='first')
            .reset_index(drop=True))

    keep = ['Genome ID', 'Taxon ID', 'Antibiotic', 'drug_class', 'genus', 'species',
            'mic_sign', 'mic_value', 'mic_log', 'has_mic', 'is_lab_confirmed',
            'computational_f1', 'label_source', 'target']
    df = df[keep]
    df['Taxon ID'] = pd.to_numeric(df['Taxon ID'], errors='coerce').fillna(0).astype('int64')
    df['species_taxon_id'] = species_taxon_ids(df['Taxon ID'])
    for col in ('Antibiotic', 'drug_class', 'genus', 'species', 'mic_sign', 'label_source'):
        df[col] = df[col].astype(str)

    if verbose:
        vc = df['target'].value_counts()
        print(f'[clean] {len(df):,} rows ({before - len(df):,} duplicates dropped)')
        print(f'[clean] susceptible={vc.get(0, 0):,} resistant={vc.get(1, 0):,} '
              f'({df["target"].mean():.1%} resistant)')
        print(f'[clean] genomes={df["Genome ID"].nunique():,} '
              f'drugs={df["Antibiotic"].nunique()} genera={df["genus"].nunique()}')
    return df


def get_clean(source='amr_output', normalize_antibiotics=True, max_files=None,
              refresh=False, verbose=True):
    """Cleaned frame, from cache when possible."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = _cache_path(source, normalize_antibiotics)
    if os.path.exists(path) and not refresh and max_files is None:
        if verbose:
            print(f'[data] cache hit: {os.path.relpath(path, ROOT)}')
        with open(path, 'rb') as fh:
            return pickle.load(fh)

    df = clean(load_raw(source, max_files, verbose), normalize_antibiotics, verbose)
    if max_files is None:
        with open(path, 'wb') as fh:
            pickle.dump(df, fh, protocol=4)
        if verbose:
            print(f'[data] cached → {os.path.relpath(path, ROOT)}')
    return df


if __name__ == '__main__':
    get_clean(refresh=True)
