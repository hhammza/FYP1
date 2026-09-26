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
import sys
import time

import numpy as np
import pandas as pd

CLEAN_VERSION = 'v5'  # v2: extended ANTIBIOTIC_ALIASES; v3: species_taxon_id (2026-09-25); v4: 54 drugs added to DRUG_CLASS_MAP (2026-09-26); v5: Genome ID read as text (2026-09-26)
# v5: read as a number, Genome IDs that differ only by trailing zeros
# (195.304, 195.3040) became one genome; 3,312 genomes merged and the
# per-genome dedup dropped 36,850 of their rows. The 13 aliases and 'sulfa'
# added in v4 change nothing: every row they touch has no usable phenotype.
GENOME_ID_TEXT = {'Genome ID': str}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache')
# Taxon ID -> species, from NCBI; built by experiments/build_taxonomy.py and
# shared with backend/train_models.py
TAXON_SPECIES_PATH = os.path.join(ROOT, 'backend', 'taxon_species.csv')

# Antibiotic names, drug classes and phenotype labels live in
# backend/amr_constants.py, shared with the trainer, predictors and web app
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from amr_constants import ANTIBIOTIC_ALIASES, DRUG_CLASS_MAP, PHENOTYPE_MAP  # noqa: E402,F401

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
            # Genome ID as text: as a number, 195.3040 and 195.304 are one genome
            frames.append(pd.read_csv(f, low_memory=False, dtype=GENOME_ID_TEXT))
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
