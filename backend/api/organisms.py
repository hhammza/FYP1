"""Which species and taxon IDs belong to which genus, and the MIC values
recorded for an organism and drug: the /forecast form's linked dropdowns.

The tree holds only what the served forecaster can use: a genus and species
it has a category for, and taxon IDs it has a rate for. backend/taxon_species.csv
says which species belongs to which genus, so a species name shared by two
genera ('coli': Escherichia and Campylobacter) is offered under each genus
where that pair really exists.
"""
import csv
import json
import os

from django.conf import settings

_cache = {}

# NCBI has renamed these genera since the BV-BRC genome names the model learned
OLD_GENUS_NAMES = {'aliarcobacter': 'arcobacter', 'stutzerimonas': 'pseudomonas'}


def _taxon_rows():
    if 'taxa' not in _cache:
        path = os.path.join(str(settings.BASE_DIR), 'taxon_species.csv')
        rows = []
        if os.path.exists(path):
            with open(path, encoding='utf-8') as fh:
                rows = list(csv.DictReader(fh))
        _cache['taxa'] = rows
    return _cache['taxa']


def organism_tree(vocab):
    """[{genus, species: [{name, label, taxon_ids}], other_taxon_ids: [{id, label}]}]
    from the model's vocabulary (`genera`, `species`, `taxon_ids`). `other_taxon_ids`
    are IDs of the genus the model knows but that name no single species of it
    (the genus itself, a species complex, an unnamed strain)."""
    genera = {g.lower(): g for g in vocab.get('genera') or []}
    species = {s.lower() for s in vocab.get('species') or []}
    taxa = set(vocab.get('taxon_ids') or [])
    tree = {g: {} for g in genera}
    placed, rows_by_id = set(), {}
    for r in _taxon_rows():
        try:
            rows_by_id[int(r['taxon_id'])] = r
        except (TypeError, ValueError):
            pass
        ncbi_genus = (r.get('genus_name') or '').strip().lower()
        genus = OLD_GENUS_NAMES.get(ncbi_genus, ncbi_genus)
        full = (r.get('species_name') or '').strip()
        if not ncbi_genus or not full:
            continue                                 # a genus-level ID: see other_taxon_ids below
        if genus not in tree or not full.lower().startswith(ncbi_genus + ' '):
            continue
        epithet = full.split(' ', 1)[1].lower()
        if epithet not in species:
            continue
        label = f'{genera[genus]} {epithet}'
        entry = tree[genus].setdefault(epithet, {'name': epithet, 'label': label, 'taxon_ids': set()})
        try:
            sid = int(r['species_taxon_id'])
        except (TypeError, ValueError):
            continue
        if sid in taxa:
            entry['taxon_ids'].add(sid)
            placed.add(sid)
    other = {g: [] for g in tree}
    for tid in sorted(taxa - placed):
        r = rows_by_id.get(tid)
        if not r:
            continue
        genus = OLD_GENUS_NAMES.get((r.get('genus_name') or '').strip().lower(), '')
        genus = genus or (r.get('genus_name') or '').strip().lower()
        if genus in other:
            other[genus].append({'id': tid, 'label': r['name']})
    return [{'genus': genera[g],
             'species': [dict(e, taxon_ids=sorted(e['taxon_ids'])) for _, e in sorted(tree[g].items())],
             'other_taxon_ids': other[g]}
            for g in sorted(tree)]


def _mic_table():
    if 'mic' not in _cache:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mic_values.json')
        _cache['mic'] = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    return _cache['mic']


def mic_values(antibiotic, genus='', species=''):
    """(values, level) for the most specific match: species, then genus, then
    every organism for the drug; ([], None) when nothing was recorded."""
    table = _mic_table()
    ab, genus, species = (antibiotic or '').lower(), (genus or '').lower(), (species or '').lower()
    for level, key in (('species', f'{genus} {species}|{ab}' if genus and species else ''),
                       ('genus', f'{genus}|{ab}' if genus else ''),
                       ('antibiotic', ab)):
        values = key and table.get(f'by_{level}', {}).get(key)
        if values:
            return values, level
    return [], None
