"""Fetch each antibiotic's nomenclature and chemistry from PubChem and cache it.

For the drug detail and chemistry panels (docs/INSTRUCTOR_REQUIREMENTS_PLAN.md,
points 9 and 12). Reads backend/reference/antibiotics.csv and writes:

    backend/trained_models/explorer/drugs.json       one entry per drug
    backend/trained_models/explorer/structures/<cid>.png   2D structure images

Uses PubChem PUG REST (https://pubchem.ncbi.nlm.nih.gov/rest/pug), at most
4 requests a second as PubChem asks. A combination (amoxicillin/clavulanic
acid) is fetched component by component. Fields PubChem does not have stay
null; the panel shows "not available". Re-running skips drugs already cached;
--refresh fetches them all again.

    .venv/bin/python scripts/fetch_pubchem.py
"""
import argparse
import json
import os
import re
import time

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, 'backend', 'reference', 'antibiotics.csv')
OUT = os.path.join(ROOT, 'backend', 'trained_models', 'explorer')
PUG = 'https://pubchem.ncbi.nlm.nih.gov/rest/pug'
PROPS = 'IUPACName,MolecularFormula,MolecularWeight,SMILES,Title'

# Names PubChem knows under another name
LOOKUP_NAME = {'penicillin': 'benzylpenicillin', 'polymyxin b': 'polymyxin B1', 'spiramycin': 'spiramycin I', 'cephalothin': 'cefalotin',
               'sulfisoxazole': 'sulfafurazole', 'sulfamethazine': 'sulfadimidine', 'sulphadimethoxine': 'sulfadimethoxine',
               'imipenem': 'imipenem', 'colomycin': 'colistin', 'timentin': 'ticarcillin',
               'azidothymidine': 'zidovudine'}

_last = [0.0]


def get(url, binary=False):
    wait = max(0.0, 0.26 - (time.time() - _last[0]))
    time.sleep(wait)
    for attempt in range(4):
        _last[0] = time.time()
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return r.content if binary else r.json()
            if r.status_code == 404:
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def brand_like(synonyms, name):
    """Likely trade names among PubChem's synonyms: one capitalised word of
    letters, not the generic name or a code. A heuristic; marked as such."""
    out = []
    for s in synonyms[:80]:
        stem = name.lower().replace(' ', '')[:5]
        if (re.fullmatch(r'[A-Z][a-z]{3,14}', s) and not s.lower().startswith(stem)
                and s.lower() not in name.lower() and s not in out):
            out.append(s)
    return out[:6]


def component(name):
    q = requests.utils.quote(LOOKUP_NAME.get(name, name))
    cids = get(f'{PUG}/compound/name/{q}/cids/JSON')
    if not cids:
        return None
    cid = cids['IdentifierList']['CID'][0]
    props = (get(f'{PUG}/compound/cid/{cid}/property/{PROPS}/JSON') or {}).get('PropertyTable', {}).get('Properties', [{}])[0]
    syn = get(f'{PUG}/compound/cid/{cid}/synonyms/JSON')
    synonyms = syn['InformationList']['Information'][0].get('Synonym', []) if syn else []
    png = os.path.join(OUT, 'structures', f'{cid}.png')
    if not os.path.exists(png):
        img = get(f'{PUG}/compound/cid/{cid}/PNG?image_size=400x300', binary=True)
        if img:
            with open(png, 'wb') as fh:
                fh.write(img)
    return {'name': name, 'pubchem_cid': cid, 'pubchem_title': props.get('Title'),
            'iupac_name': props.get('IUPACName'), 'molecular_formula': props.get('MolecularFormula'),
            'molecular_weight': float(props['MolecularWeight']) if props.get('MolecularWeight') else None,
            'smiles': props.get('SMILES'), 'structure_image': f'structures/{cid}.png' if os.path.exists(png) else None,
            'brand_names_guess': brand_like(synonyms, name),
            'pubchem_url': f'https://pubchem.ncbi.nlm.nih.gov/compound/{cid}'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refresh', action='store_true')
    args = ap.parse_args()
    os.makedirs(os.path.join(OUT, 'structures'), exist_ok=True)
    path = os.path.join(OUT, 'drugs.json')
    cache = {} if args.refresh or not os.path.exists(path) else json.load(open(path))
    drugs = pd.read_csv(REF, dtype=str).fillna('')
    for _, d in drugs.iterrows():
        name = d.antibiotic
        if name in cache:
            continue
        parts = [p.strip() for p in (d.alias_of or name).split('/')]
        comps = [component(p) for p in parts]
        cache[name] = {'antibiotic': name, 'components': [c for c in comps if c],
                       'missing_components': [p for p, c in zip(parts, comps) if not c],
                       'fetched': time.strftime('%Y-%m-%d')}
        print(f'{name:35s} ' + ', '.join(f"{c['name']}={c['pubchem_cid']}" for c in cache[name]['components'])
              + (f"  MISSING {cache[name]['missing_components']}" if cache[name]['missing_components'] else ''), flush=True)
        with open(path, 'w') as fh:
            json.dump(cache, fh, indent=1)
    found = sum(1 for v in cache.values() if v['components'] and not v['missing_components'])
    print(f'\n{found} of {len(cache)} drugs fully found; {len(os.listdir(os.path.join(OUT, "structures")))} structure images')


if __name__ == '__main__':
    main()
