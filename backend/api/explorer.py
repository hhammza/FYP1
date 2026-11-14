"""The dashboard's queries over the laboratory summary table (/api/explore/*).

docs/INSTRUCTOR_REQUIREMENTS_PLAN.md. Every view is a sum over
trained_models/explorer/cube.csv.gz (built by scripts/build_explorer_data.py:
tested, resistant and intermediate counts per country, organism, antibiotic,
infection type, disease and year), joined at load time to the editable lookup
tables in backend/reference/. Nothing here reads the cleaned table.

Resistance % = resistant / (resistant + susceptible). Intermediate results
are left out unless include_intermediate is on; then they count as resistant
and as tested.
"""
import json
import os

import pandas as pd
from django.conf import settings

REF = os.path.join(settings.BASE_DIR, 'reference')
MIN_N_DEFAULT = 30

# Filters: request parameter -> cube column; values are comma-separated
LIST_FILTERS = {
    'gram': 'gram_stain', 'genus': 'genus', 'species': 'organism', 'family': 'family',
    'subfamily': 'subfamily', 'antibiotic': 'antibiotic', 'chemical_group': 'chemical_group',
    'country': 'iso3', 'infection_type': 'infection_type', 'disease': 'disease', 'aware': 'aware',
}
# Dimensions a summary can be broken down by
DIMENSIONS = {
    'country': 'iso3', 'family': 'family', 'subfamily': 'subfamily', 'antibiotic': 'antibiotic',
    'chemical_group': 'chemical_group', 'gram': 'gram_stain', 'genus': 'genus', 'species': 'organism',
    'infection_type': 'infection_type', 'disease': 'disease', 'year': 'year', 'aware': 'aware',
}

_cache = {}


def _table(name):
    return pd.read_csv(os.path.join(REF, name), dtype=str).fillna('')


def data():
    """The cube with every lookup column joined, and the lookup tables; loaded once."""
    if 'cube' in _cache:
        return _cache
    folder = os.path.join(str(settings.TRAINED_MODELS_DIR), 'explorer')
    cube = pd.read_csv(os.path.join(folder, 'cube.csv.gz'), dtype={'year': 'Int64'},
                       keep_default_na=False, na_values={'year': ['']})
    drugs = _table('antibiotics.csv')
    # A spelling variant the cleaning missed is grouped with the drug it names
    canon = {r.antibiotic: (r.alias_of or r.antibiotic) for r in drugs.itertuples()}
    cube['antibiotic'] = cube['antibiotic'].map(canon).fillna(cube['antibiotic'])
    info = drugs[drugs.alias_of == ''].set_index('antibiotic')
    for col in ('family', 'subfamily', 'chemical_group', 'aware'):
        cube[col] = cube['antibiotic'].map(info[col]).fillna('')
    orgs = _table('organisms.csv').set_index('genus')
    cube['gram_stain'] = cube['genus'].map(orgs['gram_stain']).fillna('negative')
    cube['order_group'] = cube['genus'].map(orgs['order_group']).fillna('')
    cube['organism'] = cube['genus'] + ' ' + cube['species'].astype(str)
    countries = _table('countries.csv')
    cube['iso3'] = cube['country'].map(dict(zip(countries.country, countries.iso3))).fillna('')
    # One display name per ISO-3 code: the spelling with the most rows
    countries['lab_rows'] = pd.to_numeric(countries.lab_rows)
    names = (countries[countries.iso3 != ''].sort_values('lab_rows', ascending=False)
             .drop_duplicates('iso3').set_index('iso3')['country'])
    cube['disease'] = cube['disease'].fillna('')
    cube = cube.groupby([c for c in cube.columns if c not in ('tested', 'resistant', 'intermediate')],
                        dropna=False, as_index=False)[['tested', 'resistant', 'intermediate']].sum()
    with open(os.path.join(folder, 'drugs.json')) as fh:
        pubchem = json.load(fh)
    meta_path = os.path.join(folder, 'cube_meta.json')
    _cache.update(cube=cube, drugs=drugs, info=info, families=_table('families.csv'),
                  chemistry=_table('chemical_groups.csv').set_index('chemical_group'),
                  types=_table('resistance_types.csv'), country_names=names.to_dict(),
                  infection_types=_table('infection_types.csv'), diseases=_table('diseases.csv'),
                  pubchem=pubchem, folder=folder,
                  build=json.load(open(meta_path)) if os.path.exists(meta_path) else {})
    return _cache


def available():
    return os.path.exists(os.path.join(str(settings.TRAINED_MODELS_DIR), 'explorer', 'cube.csv.gz'))


# ---------------------------------------------------------------- filters

class Filters:
    """The query parameters every view shares (points 1 to 5 of the plan)."""

    def __init__(self, params):
        self.lists = {}
        for name in LIST_FILTERS:
            raw = params.get(name, '')
            values = [v.strip() for v in str(raw).split(',') if v.strip()]
            if values:
                self.lists[name] = values
        self.year_from = _int(params.get('year_from'), 'year_from', 1900, 2100)
        self.year_to = _int(params.get('year_to'), 'year_to', 1900, 2100)
        self.include_intermediate = str(params.get('include_intermediate', '')).lower() in ('1', 'true', 'yes', 'on')
        self.min_n = _int(params.get('min_n'), 'min_n', 1, 100000) or MIN_N_DEFAULT

    def apply(self, cube, skip=()):
        mask = pd.Series(True, index=cube.index)
        for name, values in self.lists.items():
            if name not in skip:
                mask &= cube[LIST_FILTERS[name]].isin(values)
        if self.year_from:
            mask &= cube['year'].fillna(0) >= self.year_from
        if self.year_to:
            mask &= cube['year'].fillna(9999) <= self.year_to
        return cube[mask]

    def rate(self, frame):
        """Add resistant_pct and the counts it uses."""
        if self.include_intermediate:
            frame['n'] = frame['tested']
            frame['r'] = frame['resistant'] + frame['intermediate']
        else:
            frame['n'] = frame['tested'] - frame['intermediate']
            frame['r'] = frame['resistant']
        frame['resistant_pct'] = (100 * frame['r'] / frame['n'].where(frame['n'] > 0)).round(1)
        frame['low_sample'] = frame['n'] < self.min_n
        return frame


class FilterError(ValueError):
    pass


def _int(value, name, low, high):
    if value in (None, ''):
        return None
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise FilterError(f'{name} must be a whole number.')
    if not low <= v <= high:
        raise FilterError(f'{name} must be from {low} to {high}.')
    return v


def _rows(frame, cols):
    out = frame[cols].copy()
    out = out.astype(object).where(pd.notna(out), None)
    return out.to_dict('records')


# ---------------------------------------------------------------- views

def summary(params):
    """Resistance per value of `by`, optionally split by a second dimension."""
    d = data()
    f = Filters(params)
    by = params.get('by', 'family')
    split = params.get('split', '')
    if by not in DIMENSIONS or (split and split not in DIMENSIONS):
        raise FilterError(f'by and split must be one of: {", ".join(DIMENSIONS)}.')
    cube = f.apply(d['cube'])
    keys = [DIMENSIONS[by]] + ([DIMENSIONS[split]] if split else [])
    g = cube.groupby(keys, dropna=False)[['tested', 'resistant', 'intermediate']].sum().reset_index()
    g = g[g[keys[0]].notna() & (g[keys[0]].astype(str) != '')]   # no year, no country: left out
    g = f.rate(g)
    # Highest resistance first; groups under min_n go after the rest, whatever their %
    g = g.sort_values(['low_sample', 'resistant_pct'], ascending=[True, False], na_position='last')
    out = g.rename(columns={keys[0]: 'value', **({keys[1]: 'split'} if split else {})})
    if by == 'country':
        out['label'] = out['value'].map(d['country_names'])
    cols = ['value'] + (['split'] if split else []) + (['label'] if by == 'country' else []) + \
           ['tested', 'n', 'r', 'intermediate', 'resistant_pct', 'low_sample']
    return {'by': by, 'split': split or None, 'min_n': f.min_n, 'include_intermediate': f.include_intermediate,
            'total': _totals(cube, f), 'rows': _rows(out, cols)}


def _totals(cube, f):
    t = f.rate(pd.DataFrame([cube[['tested', 'resistant', 'intermediate']].sum()]))
    return {k: (None if pd.isna(v) else (bool(v) if k == 'low_sample' else float(v) if k == 'resistant_pct' else int(v)))
            for k, v in t.iloc[0].items()}


def _type_mask(cube, row):
    mask = cube['antibiotic'].isin(row.antibiotics.split(';'))
    genera = row.genera.split(';')
    if genera[0].startswith('@'):
        mask &= cube['order_group'] == genera[0][1:]
    else:
        mask &= cube['genus'].isin(genera)
    if row.species:
        mask &= cube['species'].astype(str) == row.species
    return mask


def countries(params):
    """Point 10: per country the resistance %, n, the top resistance types and the top organism."""
    d = data()
    f = Filters(params)
    cube = f.apply(d['cube'], skip=('country',))
    cube = cube[cube['iso3'] != '']
    base = f.rate(cube.groupby('iso3')[['tested', 'resistant', 'intermediate']].sum().reset_index())
    types = []
    for row in d['types'].itertuples():
        sub = cube[_type_mask(cube, row)]
        if len(sub):
            t = f.rate(sub.groupby('iso3')[['tested', 'resistant', 'intermediate']].sum().reset_index())
            t['type'] = row.resistance_type
            types.append(t)
    types = pd.concat(types) if types else pd.DataFrame(columns=['iso3', 'type', 'n', 'resistant_pct', 'low_sample'])
    res_rows = cube.assign(rr=cube['resistant'] + (cube['intermediate'] if f.include_intermediate else 0))
    top_org = (res_rows.groupby(['iso3', 'organism'])['rr'].sum().reset_index()
               .sort_values('rr', ascending=False).drop_duplicates('iso3').set_index('iso3'))
    out = []
    for r in base.itertuples():
        mine = types[(types.iso3 == r.iso3) & (types.n > 0)].sort_values('resistant_pct', ascending=False)
        enough = mine[~mine.low_sample]
        dominant = enough.iloc[0] if len(enough) else None
        out.append({
            'iso3': r.iso3, 'country': d['country_names'].get(r.iso3, r.iso3),
            'tested': int(r.tested), 'n': int(r.n), 'resistant_pct': None if pd.isna(r.resistant_pct) else float(r.resistant_pct),
            'low_sample': bool(r.low_sample),
            'top_types': [{'type': t.type, 'resistant_pct': float(t.resistant_pct), 'n': int(t.n), 'low_sample': bool(t.low_sample)}
                          for t in mine.head(3).itertuples()],
            'dominant_type': None if dominant is None else dominant['type'],
            'dominant_pct': None if dominant is None else float(dominant['resistant_pct']),
            'top_organism': top_org['organism'].get(r.iso3) if r.iso3 in top_org.index and top_org['rr'][r.iso3] > 0 else None,
        })
    return {'min_n': f.min_n, 'include_intermediate': f.include_intermediate, 'countries': out,
            'resistance_types': d['types'][['resistance_type', 'label', 'note']].to_dict('records')}


def meta():
    """Every filter's options, with laboratory row counts, and the drug hierarchy (point 11)."""
    d = data()
    cube = d['cube']

    def counts(col, label=None):
        g = cube.groupby(col)['tested'].sum().sort_values(ascending=False)
        return [{'value': k, 'label': (label or {}).get(k, k), 'n': int(v)} for k, v in g.items() if str(k) != '']

    orgs = (cube.groupby(['gram_stain', 'genus', 'species'])['tested'].sum().reset_index())
    organisms = []
    for gram in ('positive', 'negative', 'other'):
        genera = []
        for genus, gg in orgs[orgs.gram_stain == gram].groupby('genus'):
            genera.append({'genus': genus, 'n': int(gg.tested.sum()),
                           'species': [{'value': f'{genus} {s}', 'label': f'{genus} {s}', 'n': int(n)}
                                       for s, n in gg.sort_values('tested', ascending=False)[['species', 'tested']].values]})
        organisms.append({'gram': gram, 'genera': sorted(genera, key=lambda g: -g['n'])})

    fam = d['families'].copy()
    fam['display_order'] = pd.to_numeric(fam.display_order)
    n_drug = cube.groupby('antibiotic')['tested'].sum()
    info = d['info']
    hierarchy = []
    for family, ff in fam.sort_values('display_order').groupby('family', sort=False):
        subs = []
        for sub in ff.subfamily:
            names = sorted(info.index[(info.family == family) & (info.subfamily == sub)])
            if names:
                subs.append({'subfamily': sub, 'antibiotics': [{'value': a, 'n': int(n_drug.get(a, 0)), 'aware': info.aware[a]} for a in names]})
        if subs:
            hierarchy.append({'family': family, 'subfamilies': subs})

    inf = d['infection_types']
    dis = d['diseases']
    linked = {t: sorted(set(dis.disease[dis.infection_type == t])) for t in set(inf.infection_type)}
    years = cube['year'].dropna()
    return {
        'organisms': organisms, 'antibiotic_hierarchy': hierarchy,
        'chemical_groups': counts('chemical_group'), 'countries': counts('iso3', d['country_names']),
        'infection_types': counts('infection_type'), 'diseases': counts('disease'),
        'disease_by_infection_type': linked,
        'disease_infection_type': dict(zip(dis.disease, dis.infection_type)),
        'aware': counts('aware'), 'year_range': [int(years.min()), int(years.max())] if len(years) else None,
        'resistance_types': d['types'][['resistance_type', 'label', 'note']].to_dict('records'),
        'min_n_default': MIN_N_DEFAULT, 'build': d['build'],
    }


def drug(name, params=None):
    """Point 12 and point 9: nomenclature and chemistry for one drug, with its laboratory resistance."""
    d = data()
    drugs = d['drugs'].set_index('antibiotic')
    if name not in drugs.index:
        return None
    row = drugs.loc[name]
    canon = row.alias_of or name
    info = drugs.loc[canon]
    chem = d['chemistry'].loc[info.chemical_group] if info.chemical_group in d['chemistry'].index else None
    pub = d['pubchem'].get(canon) or d['pubchem'].get(name) or {}
    f = Filters(params or {})
    cube = f.apply(d['cube'], skip=('antibiotic', 'family', 'subfamily', 'chemical_group', 'aware'))
    mine = cube[cube['antibiotic'] == canon]
    years = f.rate(mine.groupby('year')[['tested', 'resistant', 'intermediate']].sum().reset_index())
    return {
        'antibiotic': canon, 'requested': name, 'alias_of': row.alias_of or None,
        'family': info.family, 'subfamily': info.subfamily, 'chemical_group': info.chemical_group,
        'atc_code': info.atc_code or None, 'aware': info.aware, 'use': info.use, 'review': info.review or None,
        'mechanism': info.mechanism, 'target': info.target, 'resistance_mechanism': info.resistance_mechanism,
        'core_structure': None if chem is None else chem.core_structure,
        'components': [{k: c.get(k) for k in ('name', 'pubchem_cid', 'pubchem_title', 'iupac_name', 'molecular_formula',
                                              'molecular_weight', 'smiles', 'brand_names_guess', 'pubchem_url')}
                       | {'structure_url': f"explore/structure/{c['pubchem_cid']}.png" if c.get('structure_image') else None}
                       for c in pub.get('components', [])],
        'missing_from_pubchem': pub.get('missing_components', [name]) if pub else [name],
        'resistance': _totals(mine, f),
        'by_year': _rows(years.dropna(subset=['year']).sort_values('year'), ['year', 'n', 'r', 'resistant_pct', 'low_sample']),
    }


def structure_path(cid):
    d = data()
    path = os.path.join(d['folder'], 'structures', f'{int(cid)}.png')
    return path if os.path.exists(path) else None
