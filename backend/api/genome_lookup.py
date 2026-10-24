"""The "fill from Genome ID" helper on /forecast.

Genome ID is never a model input (it is the key of the genome-grouped split,
so a model given it could only memorise known genomes). The helper only:

  * fills genus, species and taxon ID: a BV-BRC Genome ID starts with its
    taxon ID ('562.1234' is taxon 562), which backend/taxon_species.csv names;
    only values the forecaster can use are filled (organisms.organism_tree)
  * shows the genome's laboratory results (api/genome_lab_results.json.gz,
    built by scripts/build_genome_lab_results.py), never BV-BRC's
    computer-predicted labels
  * says whether each served model trained on it (Hamza's
    ml_models/training_genomes.genome_status, format §7): a training genome's
    prediction looks better than a new genome's, so the page shows a caution
"""
import gzip
import json
import os
import re

from django.conf import settings

from api import organisms
from ml_models.training_genomes import genome_status

GENOME_ID = re.compile(r'^\d{1,9}\.\d{1,9}$')
_cache = {}


def _number(value):
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def valid(genome_id):
    return bool(GENOME_ID.match(genome_id or ''))


def _lab_table():
    if 'lab' not in _cache:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genome_lab_results.json.gz')
        data = {}
        if os.path.exists(path):
            with gzip.open(path, 'rt', encoding='utf-8') as fh:
                data = json.load(fh)
        _cache['lab'] = data
    return _cache['lab']


def _taxon_row(taxon_id):
    if 'rows' not in _cache:
        _cache['rows'] = {}
        for r in organisms._taxon_rows():
            try:
                _cache['rows'][int(r['taxon_id'])] = r
            except (TypeError, ValueError):
                pass
    return _cache['rows'].get(taxon_id)


def organism_fill(taxon_id, vocab):
    """What the form can fill for this taxon: genus, species and the model's
    taxon ID, each only if the forecaster knows it (None otherwise)."""
    row = _taxon_row(taxon_id) or {}
    tree = {g['genus'].lower(): g for g in organisms.organism_tree(vocab)}
    ncbi_genus = (row.get('genus_name') or '').strip().lower()
    g = tree.get(organisms.OLD_GENUS_NAMES.get(ncbi_genus, ncbi_genus))
    species_name = (row.get('species_name') or '').strip()
    epithet = species_name.split(' ', 1)[1].lower() if ' ' in species_name else ''
    s = next((x for x in g['species'] if x['name'] == epithet), None) if g else None
    try:
        sid = int(row.get('species_taxon_id') or 0)
    except ValueError:
        sid = 0
    known_ids = {t for x in (g['species'] if g else []) for t in x['taxon_ids']}
    known_ids |= {o['id'] for o in (g['other_taxon_ids'] if g else [])}
    model_taxon = next((t for t in (sid, taxon_id) if t in known_ids), None)
    return {
        'name': row.get('name') or None,                      # NCBI name of the genome's taxon
        'species_name': species_name or None,
        'genus': g['genus'] if g else None,
        'species': s['name'] if s else None,
        'taxon_id': model_taxon,
    }


def lookup(genome_id, antibiotic, vocab):
    gid = genome_id.strip()
    taxon_id = int(gid.split('.')[0])
    table = _lab_table()
    cols = table.get('columns') or []
    results = [dict(zip(cols, r)) for r in (table.get('genomes') or {}).get(gid, [])]
    for r in results:
        # a MIC the form can take: mg/L and one number (not a ratio such as
        # trimethoprim/sulfamethoxazole's '1/19', not a disk zone in mm)
        r['is_mic'] = r.get('unit', '').lower() == 'mg/l' and _number(r.get('value'))
    return {
        'genome_id': gid,
        'taxon_id': taxon_id,
        'organism': organism_fill(taxon_id, vocab),
        'lab_results': results,
        'lab_for_antibiotic': [r for r in results if antibiotic and r['antibiotic'] == antibiotic],
        'lab_source': table.get('source'),
        'models': genome_status(settings.TRAINED_MODELS_DIR, gid),
        'genes_url': f'/genes#genome={gid}',
    }
