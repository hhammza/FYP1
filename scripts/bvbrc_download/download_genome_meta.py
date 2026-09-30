"""Download collection year, country and host for every genome in the AMR
export (Data/amr_full/), resumable, with the Mac kept awake.

For the temporal test in progress/RESEARCH_PLAN.md: train on genomes
collected up to a year, test on later ones. BV-BRC keeps these fields on the
genome record, not on the AMR record, so they are fetched here by Genome ID,
500 IDs per request, 8 requests at a time.

Output (Data/genome_meta/, not in git):
    batches/batch_00001.csv, ...   one file per 500 IDs (a finished batch is
                                   never fetched again)
    genome_meta.csv                all batches joined, with a "year" column:
                                   collection_year, or else the year written
                                   in collection_date ("year_from" says which)
    download.log                   when started with the command below
Report (in git): experiments/audit/results/genome_meta_coverage.md

Run from the project root:
    nohup .venv/bin/python -u scripts/bvbrc_download/download_genome_meta.py \
        >> Data/genome_meta/download.log 2>&1 &
    .venv/bin/python scripts/bvbrc_download/download_genome_meta.py --watch
    .venv/bin/python scripts/bvbrc_download/download_genome_meta.py --report

Stop with: pkill -f download_genome_meta.py
Run the same command again to resume. With no internet it waits and retries.
"""
import argparse
import concurrent.futures
import glob
import os
import re
import subprocess
import sys
import time
from datetime import datetime

import pandas as pd
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AMR = os.path.join(ROOT, 'Data', 'amr_full')
OUT = os.path.join(ROOT, 'Data', 'genome_meta')
BATCHES = os.path.join(OUT, 'batches')
IDS = os.path.join(OUT, 'genome_ids.csv')
MERGED = os.path.join(OUT, 'genome_meta.csv')
REPORT = os.path.join(ROOT, 'experiments', 'audit', 'results', 'genome_meta_coverage.md')

API = 'https://www.bv-brc.org/api/genome/'
FIELDS = ['genome_id', 'genome_name', 'taxon_id', 'collection_year', 'collection_date',
          'isolation_country', 'geographic_group', 'host_common_name', 'host_name',
          'isolation_source', 'genome_status', 'completion_date', 'date_inserted']
BATCH = 500
WORKERS = 8
YEAR = re.compile(r'(?<!\d)(19[0-9]{2}|20[0-9]{2})(?!\d)')


def genome_ids():
    """Every Genome ID in the export, and whether it has a lab result. Read as
    text: as a float, 1055537.10 and 1055537.1 would merge."""
    if os.path.exists(IDS):
        return pd.read_csv(IDS, dtype={'genome_id': str})
    seen = {}
    files = sorted(glob.glob(os.path.join(AMR, '**', '*.csv'), recursive=True))
    for i, f in enumerate(files, 1):
        lab = f'{os.sep}lab{os.sep}' in f
        col = pd.read_csv(f, usecols=['Genome ID'], dtype=str)['Genome ID'].dropna().str.strip()
        for g in col.unique():
            seen[g] = seen.get(g, False) or lab
        print(f'[ids] {i}/{len(files)} files, {len(seen):,} genomes', flush=True)
    df = pd.DataFrame({'genome_id': list(seen), 'lab_tested': list(seen.values())})
    df = df.sort_values('genome_id').reset_index(drop=True)
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(IDS, index=False)
    return df


def batch_path(n):
    return os.path.join(BATCHES, f'batch_{n:05d}.csv')


def fetch(ids):
    body = (f'in(genome_id,({",".join(ids)}))&select({",".join(FIELDS)})'
            f'&limit({len(ids) + 10})')
    wait = 5
    while True:
        try:
            r = requests.post(API, data=body, timeout=120, headers={
                'Content-Type': 'application/rqlquery+x-www-form-urlencoded',
                'Accept': 'application/json'})
            if r.status_code == 200:
                return r.json()
            print(f'[warn] HTTP {r.status_code}, retry in {wait}s', flush=True)
        except (requests.RequestException, ValueError) as e:
            print(f'[warn] {type(e).__name__}, retry in {wait}s', flush=True)
        time.sleep(wait)
        wait = min(wait * 2, 300)


def do_batch(n, ids):
    rows = fetch(ids)
    df = pd.DataFrame(rows, columns=FIELDS)
    tmp = batch_path(n) + '.tmp'
    df.to_csv(tmp, index=False)
    os.replace(tmp, batch_path(n))     # a batch file exists only when complete
    return n, len(rows)


def download():
    if sys.platform == 'darwin':
        subprocess.Popen(['caffeinate', '-i', '-s', '-w', str(os.getpid())])
    ids = genome_ids()['genome_id'].tolist()
    os.makedirs(BATCHES, exist_ok=True)
    chunks = [(n, ids[i:i + BATCH]) for n, i in enumerate(range(0, len(ids), BATCH), 1)]
    todo = [(n, c) for n, c in chunks if not os.path.exists(batch_path(n))]
    print(f'[start] {datetime.now():%H:%M:%S} {len(ids):,} genomes, {len(chunks)} batches, '
          f'{len(todo)} to fetch', flush=True)
    t0, done = time.time(), 0
    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        for n, found in pool.map(lambda nc: do_batch(*nc), todo):
            done += 1
            if done % 20 == 0 or done == len(todo):
                rate = done / (time.time() - t0)
                print(f'[batch] {done}/{len(todo)} fetched, about '
                      f'{(len(todo) - done) / rate / 60:.0f} min left', flush=True)
    merge()
    report()
    print(f'[done] {datetime.now():%H:%M:%S}', flush=True)


def year_of(row):
    y = pd.to_numeric(row['collection_year'], errors='coerce')
    if pd.notna(y) and 1900 <= y <= 2100:
        return int(y), 'collection_year'
    m = YEAR.search(str(row['collection_date'])) if pd.notna(row['collection_date']) else None
    if m:
        return int(m.group(1)), 'collection_date'
    return None, ''


def merge():
    parts = [pd.read_csv(f, dtype=str) for f in sorted(glob.glob(os.path.join(BATCHES, '*.csv')))]
    meta = pd.concat(parts, ignore_index=True).drop_duplicates('genome_id')
    years = meta.apply(year_of, axis=1, result_type='expand')
    meta['year'] = years[0].astype('Int64')
    meta['year_from'] = years[1]
    ids = genome_ids()
    meta = ids.merge(meta, on='genome_id', how='left')
    meta['found'] = meta['genome_name'].notna() | meta['genome_status'].notna()
    meta.to_csv(MERGED, index=False)
    print(f'[merge] {MERGED}: {len(meta):,} genomes, {int(meta["found"].sum()):,} found', flush=True)


def pct(part, whole):
    return f'{part:,} ({100 * part / whole:.1f}%)' if whole else '0'


def report():
    m = pd.read_csv(MERGED, dtype={'genome_id': str}, low_memory=False)
    m['lab_tested'] = m['lab_tested'].astype(str).eq('True')
    country = m['isolation_country'].fillna('').str.strip().ne('')
    host = m['host_common_name'].fillna('').str.strip().ne('')
    lines = ['# Collection year and country coverage', '',
             'Genome records from the BV-BRC genome API for every Genome ID in the complete '
             f'AMR export (`Data/amr_full/`), fetched {datetime.now():%Y-%m-%d} by '
             '`scripts/bvbrc_download/download_genome_meta.py`. Year is `collection_year`, or '
             'else the year written in `collection_date`. Lab-tested here means at least one '
             'laboratory record in the raw export, including records with a measurement but no '
             'call, so the count is above the cleaned table\'s lab-tested genomes. Join '
             '`Data/genome_meta/genome_meta.csv` on Genome ID (as text) for the cleaned set.', '',
             '## Coverage', '',
             '| | All genomes | Lab-tested genomes |', '| --- | --- | --- |']
    for name, mask in [('Genomes', None), ('Found in the genome API', m['found']),
                       ('With a year', m['year'].notna()),
                       ('  year from collection_year', m['year_from'].eq('collection_year')),
                       ('  year from collection_date only', m['year_from'].eq('collection_date')),
                       ('With a country', country), ('With a host', host),
                       ('With a year and a country', m['year'].notna() & country)]:
        cells = []
        for sub in (pd.Series(True, index=m.index), m['lab_tested']):
            whole = int(sub.sum())
            cells.append(f'{whole:,}' if mask is None else pct(int((mask & sub).sum()), whole))
        lines.append(f'| {name} | {cells[0]} | {cells[1]} |')

    lab = m[m['lab_tested'] & m['year'].notna()]
    lines += ['', '## Lab-tested genomes by collection year', '',
              '| Years | Genomes | Share |', '| --- | --- | --- |']
    bins = [(1900, 1999), (2000, 2004), (2005, 2009), (2010, 2012), (2013, 2015),
            (2016, 2017), (2018, 2019), (2020, 2021), (2022, 2023), (2024, 2100)]
    for lo, hi in bins:
        k = int(lab['year'].between(lo, hi).sum())
        label = f'{lo} to {hi}' if hi < 2100 else f'{lo} on'
        if lo == 1900:
            label = 'before 2000'
        lines.append(f'| {label} | {k:,} | {100 * k / max(len(lab), 1):.1f}% |')
    lines += ['', f'Median year {int(lab["year"].median()) if len(lab) else "-"}. '
              'A temporal split needs enough lab-tested genomes on both sides of the cut-off; '
              'the table shows where that holds.']

    top = m.loc[m['lab_tested'] & country, 'isolation_country'].str.strip().value_counts().head(15)
    lines += ['', '## Lab-tested genomes by country (top 15)', '',
              '| Country | Genomes |', '| --- | --- |']
    lines += [f'| {c} | {k:,} |' for c, k in top.items()]
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nwrote {os.path.relpath(REPORT, ROOT)}')


def status():
    if not os.path.exists(IDS):
        return 'Reading Genome IDs from the export (first step)...'
    n = len(pd.read_csv(IDS, usecols=['genome_id']))
    total = -(-n // BATCH)
    done = len(glob.glob(os.path.join(BATCHES, '*.csv')))
    running = subprocess.run(['pgrep', '-f', 'download_genome_meta.py$|download_genome_meta.py '],
                             capture_output=True, text=True).stdout.strip()
    state = 'finished' if os.path.exists(REPORT) and done == total else (
        'running' if running else 'stopped (run the command again to resume)')
    return (f'Genome metadata   {datetime.now():%H:%M:%S}   {state}\n'
            f'{n:,} genomes, batches {done}/{total} ({100 * done / total:.1f}%)')


def watch():
    log = os.path.join(OUT, 'download.log')
    try:
        while True:
            tail = open(log, errors='ignore').read().splitlines()[-4:] if os.path.exists(log) else []
            print('\033[2J\033[H' + status() + '\n\nLast log lines:\n'
                  + '\n'.join('  ' + l for l in tail) + '\n\n(Ctrl+C closes this view only)',
                  flush=True)
            time.sleep(5)
    except KeyboardInterrupt:
        print()


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--status', action='store_true')
    ap.add_argument('--watch', action='store_true')
    ap.add_argument('--report', action='store_true', help='merge the batches and rewrite the report')
    a = ap.parse_args()
    if a.status:
        print(status())
    elif a.watch:
        watch()
    elif a.report:
        merge()
        report()
    else:
        download()
