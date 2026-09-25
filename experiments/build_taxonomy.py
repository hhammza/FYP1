"""
Map every Taxon ID in the data to its species and genus, using NCBI Taxonomy.

The export's `Taxon ID` is mostly strain level: Escherichia coli alone is
spread over about 1,200 IDs (244319 is O26:H11, 83334 is O157:H7) and the
species ID 562 never appears. A user who types 562 therefore never matches a
resistance rate. This script looks each ID up once and writes a small table
that training and prediction both use to move to species level.

    python experiments/build_taxonomy.py

Writes backend/taxon_species.csv (committed; the backend deploys without
experiments/ and without internet access at prediction time). Re-run only
when new data adds taxon IDs. Takes about a minute.
"""
import glob
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from lib import data_prep  # noqa: E402

OUT = os.path.join(ROOT, 'backend', 'taxon_species.csv')
EFETCH = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
BATCH = 200          # IDs per request
PAUSE = 0.4          # NCBI allows 3 requests a second without an API key

# python.org builds on macOS do not use the system certificate store; certifi
# (installed with requests) supplies the same CA list.
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()


def taxon_ids():
    """Every Taxon ID in amr_output/ and mapped_output/."""
    ids = set()
    for source in ('amr_output', 'mapped_output'):
        for f in glob.glob(os.path.join(data_prep.data_root(), source, '*.csv')):
            try:
                col = pd.read_csv(f, usecols=['Taxon ID'])['Taxon ID']
            except (ValueError, KeyError):
                continue      # mapping_summary.csv has no Taxon ID column
            ids.update(pd.to_numeric(col, errors='coerce').dropna().astype(int))
    return sorted(ids)


def fetch(batch):
    """NCBI Taxonomy records for a batch of IDs, keyed by every ID they answer to."""
    body = urllib.parse.urlencode({'db': 'taxonomy', 'id': ','.join(map(str, batch)),
                                   'retmode': 'xml'}).encode()
    for attempt in range(4):
        try:
            with urllib.request.urlopen(EFETCH, data=body, timeout=60, context=SSL_CONTEXT) as resp:
                root = ET.fromstring(resp.read())
            break
        except Exception as e:  # network hiccup or rate limit
            if attempt == 3:
                raise
            print(f'  retry after {e}')
            time.sleep(2 * (attempt + 1))

    records = {}
    for t in root.findall('Taxon'):
        tid = int(t.findtext('TaxId'))
        lineage = {x.findtext('Rank'): (int(x.findtext('TaxId')), x.findtext('ScientificName'))
                   for x in t.findall('LineageEx/Taxon')}
        rank, name = t.findtext('Rank'), t.findtext('ScientificName')
        lineage[rank] = (tid, name)            # the taxon itself may be the species
        species = lineage.get('species', (None, None))
        genus = lineage.get('genus', (None, None))
        rec = {'name': name, 'rank': rank,
               'species_taxon_id': species[0], 'species_name': species[1],
               'genus_taxon_id': genus[0], 'genus_name': genus[1]}
        # Merged IDs come back under their new ID, listed in AkaTaxIds
        for alias in [tid] + [int(a.text) for a in t.findall('AkaTaxIds/TaxId')]:
            records[alias] = rec
    return records


def main():
    ids = taxon_ids()
    print(f'[taxonomy] {len(ids):,} taxon IDs in the data, looking up in batches of {BATCH}')
    found = {}
    for i in range(0, len(ids), BATCH):
        found.update(fetch(ids[i:i + BATCH]))
        time.sleep(PAUSE)
        print(f'  {min(i + BATCH, len(ids)):,} / {len(ids):,}')

    rows = [{'taxon_id': t, **found[t]} if t in found else {'taxon_id': t} for t in ids]
    table = pd.DataFrame(rows)
    for col in ('species_taxon_id', 'genus_taxon_id'):
        table[col] = table[col].astype('Int64')
    table.to_csv(OUT, index=False)

    missing = table['name'].isna().sum()
    no_species = table['species_taxon_id'].isna().sum()
    print(f'[taxonomy] {len(table):,} rows → {os.path.relpath(OUT, ROOT)}')
    print(f'[taxonomy] {table["species_taxon_id"].nunique():,} species; '
          f'{no_species} IDs above species level (for example "Klebsiella sp."); '
          f'{missing} IDs unknown to NCBI')


if __name__ == '__main__':
    main()
