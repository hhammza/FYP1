"""
Download the complete assembly of every genome in Data/fasta_output/ from BV-BRC.

The FASTA files in fasta_output/ are truncated: an Escherichia coli file holds
about 0.8 MB of a 5 MB genome (1090929.3 has 25 of its 120 contigs), while
Staphylococcus aureus files are mostly whole. Gene detection on a partial
genome misses genes, so AMRFinderPlus runs on these full copies instead.

    python experiments/genome/features/download_genomes.py            # all
    python experiments/genome/features/download_genomes.py --limit 5  # test

Writes Data/genomes_full/<genome_id>.fna (gitignored, about 12 GB) and
Data/genomes_full/manifest.csv (expected and downloaded length per genome).
Safe to stop and re-run: finished genomes are skipped. A file is only kept
when its length is within 1% of the length BV-BRC reports, so a cut-off
download is retried, never used.
"""
import argparse
import glob
import json
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, EXPERIMENTS)
from lib import data_prep  # noqa: E402

FASTA_DIR = os.path.join(data_prep.data_root(), 'fasta_output')
OUT_DIR = os.path.join(data_prep.data_root(), 'genomes_full')
MANIFEST = os.path.join(OUT_DIR, 'manifest.csv')
FAILURES = os.path.join(OUT_DIR, 'failures.csv')

API = 'https://www.bv-brc.org/api'
META_BATCH = 200
# BV-BRC answers 403 to Python's default User-Agent
USER_AGENT = 'amr-fyp-genome-download/1.0 (COMSATS FYP)'
TOLERANCE = 0.01

try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()


def local_genomes():
    """Genome ID, taxon ID and folder for every FASTA in fasta_output/."""
    rows = []
    for path in sorted(glob.glob(os.path.join(FASTA_DIR, 'taxon_*', '*.fasta'))):
        folder = os.path.basename(os.path.dirname(path))
        rows.append({'genome_id': os.path.basename(path)[:-len('.fasta')],
                     'taxon_id': int(folder.split('_')[1]),
                     'folder': folder,
                     'local_bytes': os.path.getsize(path)})
    return pd.DataFrame(rows)


RETRY_WAITS = [10, 20, 40, 60, 90, 120]   # seconds; rides out a few minutes of lost connection


def get(url, accept, timeout=300):
    req = urllib.request.Request(url, headers={'Accept': accept, 'User-Agent': USER_AGENT})
    for wait in RETRY_WAITS + [None]:
        try:
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as resp:
                return resp.read()
        except Exception as e:
            if wait is None:
                raise
            print(f'  retry in {wait}s {url[:90]}... after {e}')
            time.sleep(wait)


def expected_lengths(genome_ids):
    """genome_length, contigs and status from BV-BRC, 200 genomes per request."""
    rows = []
    for i in range(0, len(genome_ids), META_BATCH):
        batch = genome_ids[i:i + META_BATCH]
        query = (f'in(genome_id,({",".join(batch)}))'
                 f'&select(genome_id,genome_length,contigs,genome_status)&limit({len(batch)})')
        rows += json.loads(get(f'{API}/genome/?{query}', 'application/json'))
        print(f'  metadata {min(i + META_BATCH, len(genome_ids)):,} / {len(genome_ids):,}')
    meta = pd.DataFrame(rows)
    meta['genome_id'] = meta['genome_id'].astype(str)
    return meta


def sequence_length(fasta_bytes):
    return sum(len(line.strip()) for line in fasta_bytes.splitlines() if not line.startswith(b'>'))


def download(genome_id, expected):
    """Fetch one assembly; returns its sequence length, raises if incomplete."""
    query = urllib.parse.quote(f'eq(genome_id,{genome_id})', safe='(),') + '&limit(100000)'
    data = get(f'{API}/genome_sequence/?{query}', 'application/dna+fasta')
    length = sequence_length(data)
    if abs(length - expected) > TOLERANCE * expected:
        raise ValueError(f'got {length:,} bp, expected {expected:,}')
    tmp = os.path.join(OUT_DIR, f'{genome_id}.fna.part')
    with open(tmp, 'wb') as fh:
        fh.write(data)
    os.replace(tmp, os.path.join(OUT_DIR, f'{genome_id}.fna'))
    return length


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--limit', type=int, help='only the first N genomes (for testing)')
    ap.add_argument('--workers', type=int, default=4, help='parallel downloads (default 4)')
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    genomes = local_genomes()
    if args.limit:
        genomes = genomes.head(args.limit)
    print(f'[download] {len(genomes):,} genomes in {os.path.relpath(FASTA_DIR)}')

    if os.path.exists(MANIFEST):
        manifest = pd.read_csv(MANIFEST, dtype={'genome_id': str})
    else:
        manifest = genomes.merge(expected_lengths(genomes['genome_id'].tolist()), on='genome_id', how='left')
        manifest['full_bytes'] = pd.NA
    missing_ids = set(genomes['genome_id']) - set(manifest['genome_id'])
    if missing_ids:  # a larger run after a --limit test
        extra = genomes[genomes['genome_id'].isin(missing_ids)]
        extra = extra.merge(expected_lengths(sorted(missing_ids)), on='genome_id', how='left')
        manifest = pd.concat([manifest, extra], ignore_index=True)
    manifest.to_csv(MANIFEST, index=False)

    todo = manifest[manifest['genome_id'].isin(genomes['genome_id'])]
    unknown = todo[todo['genome_length'].isna()]
    todo = todo[todo['genome_length'].notna()]
    done = todo['genome_id'].map(lambda g: os.path.exists(os.path.join(OUT_DIR, f'{g}.fna')))
    todo = todo[~done]
    print(f'[download] {done.sum():,} already done, {len(todo):,} to fetch, '
          f'{len(unknown):,} not found on BV-BRC')

    failures = [{'genome_id': g, 'error': 'not found on BV-BRC'} for g in unknown['genome_id']]
    lengths = {}
    with ThreadPoolExecutor(args.workers) as pool:
        jobs = {pool.submit(download, r.genome_id, int(r.genome_length)): r.genome_id
                for r in todo.itertuples()}
        for n, job in enumerate(as_completed(jobs), 1):
            gid = jobs[job]
            try:
                lengths[gid] = job.result()
            except Exception as e:
                failures.append({'genome_id': gid, 'error': str(e)})
                print(f'  FAILED {gid}: {e}')
            if n % 25 == 0 or n == len(jobs):
                print(f'  {n:,} / {len(jobs):,}')
                manifest.loc[manifest['genome_id'].isin(list(lengths)), 'full_bytes'] = \
                    manifest['genome_id'].map(lengths)
                manifest.to_csv(MANIFEST, index=False)

    pd.DataFrame(failures, columns=['genome_id', 'error']).to_csv(FAILURES, index=False)
    total = sum(os.path.exists(os.path.join(OUT_DIR, f'{g}.fna')) for g in genomes['genome_id'])
    print(f'[download] {total:,} / {len(genomes):,} complete; {len(failures)} failed '
          f'(listed in {os.path.relpath(FAILURES)}, re-run to retry)')


if __name__ == '__main__':
    main()
