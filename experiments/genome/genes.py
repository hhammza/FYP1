"""Resistance-gene features from Ali's gene matrix (Track B6/B7).

The matrix (experiments/genome/features/gene_matrix.parquet, format in
progress/formats/README.md §3) has one row per genome. A training row is a
(genome, antibiotic) pair, so besides the raw 0/1 gene columns this builds
features that depend on which drug is being asked about:

    gene_class_n      resistance genes whose AMRFinderPlus class covers this drug
    mutation_class_n  point mutations whose class covers this drug
    gene_class_any    either of the above is non-zero
    key_determinant   a named, well-known determinant for this drug is present
    amr_genes_total   every AMR gene and mutation in the genome (multidrug load)
    efflux_n          EFFLUX / MULTIDRUG elements, which act on many drugs

Evaluate on lab-confirmed rows (test_by_label_source['lab'] in metrics.json):
BV-BRC's computational labels were themselves predicted from the genome, so a
gene model can score well on them by re-deriving that prediction.
"""
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FEATURES_DIR = os.path.join(HERE, 'features')
MATRIX = os.path.join(FEATURES_DIR, 'gene_matrix.parquet')
INFO = os.path.join(FEATURES_DIR, 'gene_info.csv')

# Project drug class (backend/amr_constants.py DRUG_CLASS_MAP) -> the
# AMRFinderPlus classes whose genes confer resistance to it. A gene listed
# under several classes ('PHENICOL/QUINOLONE') counts for each of them.
# TODO(Hamza): refine with subclasses. 'carbapenem' currently takes every
# BETA-LACTAM gene; gene_info.csv's `subclass` column (CARBAPENEM,
# CEPHALOSPORIN, ...) would let carbapenems count only carbapenemases.
CLASS_TO_AMRFINDER = {
    'beta_lactam': {'BETA-LACTAM'},
    'carbapenem': {'BETA-LACTAM'},
    'monobactam': {'BETA-LACTAM'},
    'fluoroquinolone': {'QUINOLONE'},
    'aminoglycoside': {'AMINOGLYCOSIDE'},
    'tetracycline': {'TETRACYCLINE'},
    'sulfonamide': {'SULFONAMIDE', 'TRIMETHOPRIM'},
    'phenicol': {'PHENICOL'},
    'macrolide': {'MACROLIDE'},
    'lincosamide': {'LINCOSAMIDE'},
    'streptogramin': {'STREPTOGRAMIN'},
    'glycopeptide': {'GLYCOPEPTIDE'},
    'polymyxin': {'COLISTIN'},
    'rifamycin': {'RIFAMYCIN'},
    'oxazolidinone': {'OXAZOLIDINONE'},
    'nitrofuran': {'NITROFURAN'},
    'phosphonic_acid': {'FOSFOMYCIN'},
    'fusidane': {'FUSIDIC ACID', 'FUSIDIC_ACID'},
    'lipopeptide': {'LIPOPEPTIDE'},
    'pseudomonic_acid': {'MUPIROCIN'},
    'orthosomycin': {'AVILAMYCIN'},
    # antitubercular: AMRFinderPlus reports few M. tuberculosis mutations
}

# Antibiotic -> symbol prefixes of well-known determinants. A genome carries
# the determinant if any matrix column starts with one of the prefixes.
# TODO(Hamza): extend this list (your suggestion "key determinants").
#   - carbapenems beyond meropenem/imipenem (ertapenem, doripenem)
#   - 3rd/4th-generation cephalosporins: ceftazidime, cefepime (blaCTX-M, blaCMY)
#   - aminoglycosides: aac(6')-Ib for amikacin/tobramycin, armA/rmtB for all
#   - trimethoprim/sulfamethoxazole needs BOTH a sul and a dfr gene; that is
#     an AND, not a prefix match, so handle it in drug_aware_features() below
KEY_DETERMINANTS = {
    'oxacillin': ['mecA', 'mecC'],
    'methicillin': ['mecA', 'mecC'],
    'cefoxitin': ['mecA', 'mecC'],
    'vancomycin': ['vanA', 'vanB'],
    'colistin': ['mcr-'],
    'ciprofloxacin': ['gyrA_S83', 'gyrA_D87', 'parC_S80', 'qnr'],
    'levofloxacin': ['gyrA_S83', 'gyrA_D87', 'parC_S80', 'qnr'],
    'nalidixic acid': ['gyrA_S83', 'gyrA_D87'],
    'cefotaxime': ['blaCTX-M'],
    'ceftriaxone': ['blaCTX-M'],
    'meropenem': ['blaKPC', 'blaNDM', 'blaOXA-48', 'blaVIM', 'blaIMP'],
    'imipenem': ['blaKPC', 'blaNDM', 'blaOXA-48', 'blaVIM', 'blaIMP'],
    'tetracycline': ['tet('],
    'chloramphenicol': ['cat', 'cmlA', 'floR'],
    'gentamicin': ['aac(3)', 'ant(2'],
    'trimethoprim': ['dfr'],
}


def load_matrix():
    """(matrix as uint8 DataFrame indexed by Genome ID text, gene_info)."""
    if not os.path.exists(MATRIX):
        raise FileNotFoundError(f'{MATRIX} missing; see experiments/genome/README.md')
    m = pd.read_parquet(MATRIX)
    m.index = m.index.astype(str)
    info = pd.read_csv(INFO).set_index('symbol')
    return m, info


def amr_classes(cls):
    return set() if pd.isna(cls) else {c.strip() for c in str(cls).split('/')}


def raw_gene_columns(m, pos, min_genomes=10):
    """0/1 columns for genes carried by at least `min_genomes` genomes."""
    keep = m.columns[m.sum(axis=0).to_numpy() >= min_genomes]
    arr = m[keep].to_numpy(dtype=np.uint8)[pos]
    return {f'g_{s}': arr[:, i] for i, s in enumerate(keep)}


def drug_aware_features(m, info, pos, antibiotics, drug_classes):
    """Features that depend on the (genome, antibiotic) pair."""
    arr = m.to_numpy(dtype=np.uint8)
    symbols = list(m.columns)
    kinds = info.reindex(symbols)['type'].to_numpy()
    classes = [amr_classes(c) for c in info.reindex(symbols)['class']]
    is_mut = kinds == 'point_mutation'
    n = len(pos)

    gene_n = np.zeros(n, dtype=np.float32)
    mut_n = np.zeros(n, dtype=np.float32)
    for dc in np.unique(drug_classes):
        targets = CLASS_TO_AMRFINDER.get(dc)
        if not targets:
            continue
        cols = np.array([bool(c & targets) for c in classes])
        rows = drug_classes == dc
        g = arr[:, cols & ~is_mut].sum(axis=1)
        mu = arr[:, cols & is_mut].sum(axis=1)
        gene_n[rows] = g[pos[rows]]
        mut_n[rows] = mu[pos[rows]]

    key = np.zeros(n, dtype=np.float32)
    for ab in np.unique(antibiotics):
        prefixes = KEY_DETERMINANTS.get(ab)
        if not prefixes:
            continue
        cols = np.array([any(s.startswith(p) for p in prefixes) for s in symbols])
        rows = antibiotics == ab
        key[rows] = (arr[:, cols].sum(axis=1) > 0)[pos[rows]]

    efflux = np.array([bool(c & {'EFFLUX', 'MULTIDRUG'}) for c in classes])
    return {
        'gene_class_n': gene_n,
        'mutation_class_n': mut_n,
        'gene_class_any': ((gene_n + mut_n) > 0).astype(np.float32),
        'key_determinant': key,
        'amr_genes_total': arr.sum(axis=1)[pos].astype(np.float32),
        'efflux_n': arr[:, efflux].sum(axis=1)[pos].astype(np.float32),
    }


def attach(df, gcfg, verbose=True):
    """Keep rows whose genome is in the matrix and add the gene columns.

    gcfg = {"raw": true, "min_genomes": 10, "drug_aware": true}
    """
    m, info = load_matrix()
    pos = pd.Index(m.index).get_indexer(df['Genome ID'])
    keep = pos >= 0
    if verbose:
        print(f'[genes] {int(keep.sum()):,} of {len(df):,} rows have gene data '
              f'({df.loc[keep, "Genome ID"].nunique():,} genomes)')
    df, pos = df.loc[keep].reset_index(drop=True), pos[keep]
    cols = {}
    if gcfg.get('raw', True):
        cols.update(raw_gene_columns(m, pos, gcfg.get('min_genomes', 10)))
    if gcfg.get('drug_aware', True):
        cols.update(drug_aware_features(m, info, pos, df['Antibiotic'].to_numpy(),
                                        df['drug_class'].to_numpy()))
    extra = pd.DataFrame(cols, index=df.index)
    if verbose:
        print(f'[genes] {extra.shape[1]:,} gene columns')
    return pd.concat([df, extra], axis=1), list(extra.columns)
