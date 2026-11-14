"""Build the dashboard's summary table ("cube") from the laboratory rows.

For the views in docs/INSTRUCTOR_REQUIREMENTS_PLAN.md. Every filter and view
is a sum over this table, so the deployed backend never needs the 1.5 GB
cleaned table. Laboratory rows only (decision D2): computational labels are
predictions, not tests.

Reads
    experiments/cache/clean_v7_amr_full_norm.pkl     the cleaned table (lab rows)
    Data/amr_full/lab/*.csv                          raw lab records, to tell Intermediate apart
    Data/genome_meta/genome_meta.csv                 country, year, disease, body site
    backend/reference/*.csv                          infection rules, diseases, organisms
Writes
    backend/trained_models/explorer/cube.csv.gz      one row per combination of
        country, genus, species, antibiotic, infection_type, disease, year,
        with tested, resistant and intermediate counts
    backend/trained_models/explorer/cube_meta.json   build date, totals, coverage

The cleaned table counts Intermediate as Resistant (1). Here a genome-drug
pair is "intermediate" when its laboratory records include Intermediate and
no Resistant or Nonsusceptible call. Resistance % excludes those pairs by
default: resistant / (resistant + susceptible).

    .venv/bin/python scripts/build_explorer_data.py
"""
import glob
import json
import os
import sys
import time

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from amr_constants import ANTIBIOTIC_ALIASES  # noqa: E402

REF = os.path.join(ROOT, 'backend', 'reference')
OUT = os.path.join(ROOT, 'backend', 'trained_models', 'explorer')
META_FIELDS = ['disease', 'host_health', 'body_sample_site', 'isolation_source']


def norm_drug(s):
    s = s.astype(str).str.strip().str.lower()
    return s.replace({k: v for k, v in ANTIBIOTIC_ALIASES.items() if v is not None})


def intermediate_pairs():
    files = sorted(glob.glob(os.path.join(ROOT, 'Data', 'amr_full', 'lab', '**', '*.csv'), recursive=True))
    raw = pd.concat([pd.read_csv(f, usecols=['Genome ID', 'Antibiotic', 'Resistant Phenotype'], dtype=str)
                     for f in files], ignore_index=True).dropna(subset=['Resistant Phenotype'])
    raw['Antibiotic'] = norm_drug(raw['Antibiotic'])
    raw['Genome ID'] = raw['Genome ID'].str.strip()
    calls = raw.groupby(['Genome ID', 'Antibiotic'])['Resistant Phenotype'].agg(set)
    inter = calls.map(lambda s: 'Intermediate' in s and not ({'Resistant', 'Nonsusceptible'} & s))
    return set(inter[inter].index)


def infection_types(meta):
    """Apply backend/reference/infection_types.csv: the lowest priority number wins."""
    rules = pd.read_csv(os.path.join(REF, 'infection_types.csv')).sort_values('priority', ascending=False)
    text = {f: meta[f].astype(str).str.lower().str.strip("[]' ").replace({'nan': ''}) for f in META_FIELDS}
    out = pd.Series('Unknown', index=meta.index)
    for _, r in rules.iterrows():
        out[text[r.field].str.contains(r.pattern, regex=True, na=False)] = r.infection_type
    return out


def main():
    t0 = time.time()
    df = pd.read_pickle(os.path.join(ROOT, 'experiments', 'cache', 'clean_v7_amr_full_norm.pkl'))
    lab = df[df['label_source'] == 'lab'][['Genome ID', 'Antibiotic', 'genus', 'species', 'target']].copy()
    print(f'[lab] {len(lab):,} laboratory rows', flush=True)

    inter = intermediate_pairs()
    lab['intermediate'] = [(g, a) in inter for g, a in zip(lab['Genome ID'], lab['Antibiotic'])]
    print(f'[lab] {int(lab.intermediate.sum()):,} pairs intermediate only', flush=True)

    meta = pd.read_csv(os.path.join(ROOT, 'Data', 'genome_meta', 'genome_meta.csv'), dtype={'genome_id': str},
                       usecols=['genome_id', 'isolation_country', 'year'] + META_FIELDS, low_memory=False)
    meta['infection_type'] = infection_types(meta)
    dis = pd.read_csv(os.path.join(REF, 'diseases.csv'), dtype=str)
    raw_d = meta['disease'].astype(str).str.lower().str.strip("[]' ").str.replace(r"'\s*,\s*'", '; ', regex=True)
    meta['disease_norm'] = raw_d.map(dict(zip(dis.disease_raw, dis.disease))).fillna('')
    meta['country'] = meta['isolation_country'].fillna('').astype(str).str.strip()
    meta = meta[['genome_id', 'country', 'year', 'infection_type', 'disease_norm']]

    lab = lab.merge(meta, left_on='Genome ID', right_on='genome_id', how='left')
    lab['country'] = lab['country'].fillna('')
    lab['infection_type'] = lab['infection_type'].fillna('Unknown')
    lab['disease_norm'] = lab['disease_norm'].fillna('')
    lab['year'] = pd.to_numeric(lab['year'], errors='coerce').astype('Int64')
    lab['resistant'] = ((lab.target == 1) & ~lab.intermediate).astype(int)
    lab['intermediate'] = lab['intermediate'].astype(int)

    keys = ['country', 'genus', 'species', 'Antibiotic', 'infection_type', 'disease_norm', 'year']
    cube = (lab.groupby(keys, dropna=False)
               .agg(tested=('target', 'size'), resistant=('resistant', 'sum'), intermediate=('intermediate', 'sum'))
               .reset_index()
               .rename(columns={'Antibiotic': 'antibiotic', 'disease_norm': 'disease'}))
    os.makedirs(OUT, exist_ok=True)
    # CSV, not parquet: the backend image has no pyarrow
    cube.to_csv(os.path.join(OUT, 'cube.csv.gz'), index=False)

    info = {
        'built': time.strftime('%Y-%m-%d'), 'source': 'cleaning v7, laboratory rows only',
        'rows_in_cube': len(cube), 'lab_rows': int(cube.tested.sum()),
        'resistant': int(cube.resistant.sum()), 'intermediate': int(cube.intermediate.sum()),
        'with_country': int(cube.loc[cube.country != '', 'tested'].sum()),
        'with_infection_type': int(cube.loc[cube.infection_type != 'Unknown', 'tested'].sum()),
        'with_disease': int(cube.loc[cube.disease != '', 'tested'].sum()),
        'with_year': int(cube.loc[cube.year.notna(), 'tested'].sum()),
        'countries': int((cube.country != '').groupby(cube.country).any().sum()),
    }
    with open(os.path.join(OUT, 'cube_meta.json'), 'w') as fh:
        json.dump(info, fh, indent=1)
    size = os.path.getsize(os.path.join(OUT, 'cube.csv.gz')) / 1e6
    print(json.dumps(info, indent=1))
    print(f'[done] cube.csv.gz {len(cube):,} rows, {size:.1f} MB, {time.time() - t0:.0f} s')


if __name__ == '__main__':
    main()
