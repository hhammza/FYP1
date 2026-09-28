"""Download every AMR record from BV-BRC, resumable, with the Mac kept awake.

The April download (download_amr_csv.py) paged with a growing offset and
stopped at 500,000 rows per taxon, so the largest species broke: E. coli
(taxon 562, 7.2 M rows) is missing entirely, and K. pneumoniae stopped at
500,000 of 1.84 M. This script pages by record ID instead (sort by id, then
"id greater than the last one"), which has no depth limit and restarts
exactly where it stopped.

Two streams, lab results first because they matter most:
    lab             evidence = Laboratory Method       (~1.3 M rows, ~10 min)
    computational   evidence = Computational Method    (~16.3 M rows)

Output (Data/amr_full/, not in git):
    lab/shard_0/part_00001.csv, ...   16 shards (by the ID's first character),
    computational/shard_0/...         downloaded 8 at a time, 500,000 rows
                                      per file; legacy/ holds rows from an
                                      earlier single-thread run
    state.json       where each stream stopped (updated after every page)
    manifest.json    written at the end: rows per stream vs BV-BRC's count
    download.log     when started with the command below

The CSV columns are the April ones (so data_prep can read them), plus
Record ID, Date Inserted and Date Modified at the end.

Run from the project root:
    nohup .venv/bin/python -u scripts/bvbrc_download/download_amr_full.py \
        >> Data/amr_full/download.log 2>&1 &
    tail -f Data/amr_full/download.log           # watch it
    .venv/bin/python scripts/bvbrc_download/download_amr_full.py --status

Stop with: pkill -f download_amr_full.py
Run the same command again to resume. With no internet it waits and retries
instead of giving up. On macOS it keeps the Mac awake while it runs.
"""
import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

API = 'https://www.bv-brc.org/api/genome_amr/'
STREAMS = {
    'lab': 'Laboratory Method',
    'computational': 'Computational Method',
}

# April column names and order (download_amr_csv.py), then three new ones.
FIELDS = [
    ('taxon_id', 'Taxon ID'),
    ('genome_id', 'Genome ID'),
    ('genome_name', 'Genome Name'),
    ('antibiotic', 'Antibiotic'),
    ('resistant_phenotype', 'Resistant Phenotype'),
    ('measurement', 'Measurement'),
    ('measurement_sign', 'Measurement Sign'),
    ('measurement_value', 'Measurement Value'),
    ('measurement_unit', 'Measurement Unit'),
    ('laboratory_typing_method', 'Laboratory Typing Method'),
    ('laboratory_typing_method_version', 'Laboratory Typing Method Version'),
    ('laboratory_typing_platform', 'Laboratory Typing Platform'),
    ('vendor', 'Vendor'),
    ('testing_standard', 'Testing Standard'),
    ('testing_standard_year', 'Testing Standard Year'),
    ('computational_method', 'Computational Method'),
    ('computational_method_version', 'Computational Method Version'),
    ('computational_method_performance', 'Computational Method Performance'),
    ('evidence', 'Evidence'),
    ('source', 'Source'),
    ('pmid', 'PubMed'),
    ('id', 'Record ID'),
    ('date_inserted', 'Date Inserted'),
    ('date_modified', 'Date Modified'),
]
SELECT = ','.join(f for f, _ in FIELDS)
HEADER = [c for _, c in FIELDS]


def log(msg):
    print(f'[{datetime.now():%H:%M:%S}] {msg}', flush=True)


def keep_awake():
    """macOS: caffeinate stops sleep until this process exits."""
    if sys.platform == 'darwin':
        try:
            subprocess.Popen(['caffeinate', '-i', '-s', '-w', str(os.getpid())])
            log('Keeping the Mac awake while this runs (caffeinate).')
        except OSError:
            log('caffeinate not found; the Mac may sleep.')


def get(query, accept='application/json', timeout=180):
    """GET with retries forever: short waits first, then every 5 minutes."""
    url = f'{API}?{query}'
    wait = 5
    while True:
        try:
            r = requests.get(url, headers={'Accept': accept}, timeout=timeout)
            if r.status_code == 200:
                return r.json()
            log(f'HTTP {r.status_code}: {r.text[:150]}')
        except (requests.RequestException, ValueError) as exc:
            log(f'No answer from BV-BRC ({type(exc).__name__}); retrying in {wait}s')
        time.sleep(wait)
        wait = min(wait * 2, 300)


def count(evidence):
    q = f'eq(evidence,{quote(evidence)})&select(id)&limit(1)'
    return int(get(q, accept='application/solr+json')['response']['numFound'])


def cell(v):
    if v is None:
        return ''
    if isinstance(v, list):
        return ';'.join(str(x) for x in v)
    return v


class State:
    """state.json, saved atomically; one lock for every thread."""

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.data = json.load(open(path)) if os.path.exists(path) else {}

    def save(self):
        with self.lock:
            tmp = self.path + '.tmp'
            with open(tmp, 'w') as fh:
                json.dump(self.data, fh, indent=2)
            os.replace(tmp, self.path)


HEX = '0123456789abcdef'   # record IDs are lowercase UUIDs: one shard per first character


def part_path(folder, n):
    return os.path.join(folder, f'part_{n:05d}.csv')


def new_shard():
    return {'rows': 0, 'last_id': None, 'part': 1, 'part_rows': 0, 'part_bytes': 0, 'done': False}


def migrate(name, folder, s):
    """Old single-thread state (one last_id per stream) -> 16 shards.

    The rows already downloaded (every ID up to last_id) are kept in
    <stream>/legacy/; shards before last_id's first character are complete,
    that shard carries on after last_id, the rest start from scratch.
    """
    legacy = os.path.join(folder, 'legacy')
    os.makedirs(legacy, exist_ok=True)
    for f in sorted(os.listdir(folder)):
        if f.startswith('part_') and f.endswith('.csv'):
            os.replace(os.path.join(folder, f), os.path.join(legacy, f))
    last = part_path(legacy, s['part'])
    if os.path.exists(last) and os.path.getsize(last) > s['part_bytes']:
        with open(last, 'r+b') as fh:
            fh.truncate(s['part_bytes'])
    shards = {h: new_shard() for h in HEX}
    first = s['last_id'][0]
    for h in HEX:
        if h < first:
            shards[h]['done'] = True
    shards[first]['last_id'] = s['last_id']
    s['legacy_rows'] = s['rows']
    s['shards'] = shards
    for k in ('last_id', 'part', 'part_rows', 'part_bytes'):
        s.pop(k, None)
    log(f'{name}: kept {s["legacy_rows"]:,} rows already downloaded (in {name}/legacy/); '
        f'continuing in 16 parallel shards')


def download_shard(name, evidence, folder, s, h, state, page, part_rows, progress):
    sh = s['shards'][h]
    sfolder = os.path.join(folder, f'shard_{h}')
    os.makedirs(sfolder, exist_ok=True)
    hi = HEX[HEX.index(h) + 1] if h != HEX[-1] else None

    path = part_path(sfolder, sh['part'])
    if os.path.exists(path) and os.path.getsize(path) > sh['part_bytes']:
        with open(path, 'r+b') as fh:
            fh.truncate(sh['part_bytes'])

    while True:
        conds = [f'eq(evidence,{quote(evidence)})']
        # gt() includes its boundary; the one-character bounds never equal a
        # real ID, and the repeated last record is dropped below.
        lower = sh['last_id'] or (h if h != HEX[0] else None)
        if lower:
            conds.append(f'gt(id,{quote(lower)})')
        if hi:
            conds.append(f'lt(id,{hi})')
        cond = conds[0] if len(conds) == 1 else f'and({",".join(conds)})'
        batch = get(f'{cond}&select({SELECT})&sort(+id)&limit({page})')
        full_page = len(batch) == page
        batch = [r for r in batch if r.get('id') != sh['last_id']]
        if not batch:
            break

        path = part_path(sfolder, sh['part'])
        new_file = not os.path.exists(path) or os.path.getsize(path) == 0
        with open(path, 'a', newline='', encoding='utf-8') as fh:
            w = csv.writer(fh, quoting=csv.QUOTE_NONNUMERIC)
            if new_file:
                w.writerow(HEADER)
            for rec in batch:
                w.writerow([cell(rec.get(f)) for f, _ in FIELDS])
            fh.flush()
            os.fsync(fh.fileno())

        with state.lock:
            sh['rows'] += len(batch)
            sh['part_rows'] += len(batch)
            sh['last_id'] = batch[-1]['id']
            sh['part_bytes'] = os.path.getsize(path)
            if sh['part_rows'] >= part_rows:
                sh['part'] += 1
                sh['part_rows'] = 0
                sh['part_bytes'] = 0
            s['rows'] = s.get('legacy_rows', 0) + sum(x['rows'] for x in s['shards'].values())
        state.save()
        progress()
        if not full_page:
            break

    with state.lock:
        sh['done'] = True
    state.save()
    log(f'{name}: shard {h} complete ({sh["rows"]:,} rows)')


def download_stream(name, evidence, out, state, page, part_rows, workers):
    folder = os.path.join(out, name)
    os.makedirs(folder, exist_ok=True)
    s = state.data.setdefault(name, {'rows': 0, 'done': False})
    if s.get('done'):
        log(f'{name}: already complete ({s["rows"]:,} rows)')
        return
    s['expected'] = count(evidence)
    if 'shards' not in s:
        if s.get('last_id'):
            migrate(name, folder, s)
        else:
            s['shards'] = {h: new_shard() for h in HEX}
    state.save()
    todo = [h for h in HEX if not s['shards'][h]['done']]
    log(f'{name}: {s["rows"]:,} of {s["expected"]:,} rows so far; '
        f'{len(todo)} of 16 shards to go, {workers} at a time')

    started, start_rows = time.time(), s['rows']
    last_print = [0.0]

    def progress():
        now = time.time()
        if now - last_print[0] < 10:
            return
        last_print[0] = now
        rate = (s['rows'] - start_rows) / max(now - started, 1)
        left = max(s['expected'] - s['rows'], 0) / rate if rate else 0
        done = sum(1 for x in s['shards'].values() if x['done'])
        log(f'{name}: {s["rows"]:,}/{s["expected"]:,} '
            f'({100 * s["rows"] / max(s["expected"], 1):.1f}%)  {rate:,.0f} rows/s  '
            f'~{left / 60:.0f} min left  shards done {done}/16')

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(download_shard, name, evidence, folder, s, h, state,
                               page, part_rows, progress) for h in todo]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    s['done'] = True
    s['finished'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    state.save()
    log(f'{name}: complete, {s["rows"]:,} rows (BV-BRC reported {s["expected"]:,})')


def status(out):
    path = os.path.join(out, 'state.json')
    if not os.path.exists(path):
        print('Not started yet.')
        return
    data = json.load(open(path))
    print(f'Started: {data.get("started", "?")}')
    for name in STREAMS:
        s = data.get(name)
        if not s:
            print(f'  {name:14s} not started')
            continue
        exp = s.get('expected') or 0
        pct = 100 * s['rows'] / exp if exp else 0
        state = 'complete' if s.get('done') else 'in progress'
        print(f'  {name:14s} {s["rows"]:>12,} / {exp:,}  ({pct:.1f}%)  {state}')
    running = subprocess.run(['pgrep', '-f', 'download_amr_full.py --run'],
                             capture_output=True, text=True).stdout.strip()
    print('Running now: ' + ('yes' if running else 'no'))


def bar(frac, width=30):
    n = int(round(frac * width))
    return '#' * n + '-' * (width - n)


def watch(out, every=5):
    """Live view: a bar per stream, speed and time left. Ctrl+C closes it."""
    path = os.path.join(out, 'state.json')
    last = {}
    try:
        while True:
            lines = [f'BV-BRC AMR download   {datetime.now():%H:%M:%S}   (Ctrl+C closes this view only)', '']
            data = json.load(open(path)) if os.path.exists(path) else {}
            total_rows = total_exp = 0
            for name in STREAMS:
                s = data.get(name)
                if not s:
                    lines.append(f'{name:14s} [{bar(0)}]   not started')
                    continue
                exp = s.get('expected') or 0
                frac = s['rows'] / exp if exp else 0
                total_rows += s['rows']
                total_exp += exp
                speed = ''
                if name in last and not s.get('done'):
                    rows0, t0 = last[name]
                    rate = (s['rows'] - rows0) / max(time.time() - t0, 1)
                    if rate > 0:
                        speed = f'   {rate:,.0f} rows/s, ~{(exp - s["rows"]) / rate / 60:.0f} min left'
                if name not in last or s['rows'] != last[name][0]:
                    last[name] = (s['rows'], time.time())
                state = 'complete' if s.get('done') else 'downloading'
                lines.append(f'{name:14s} [{bar(frac)}] {100 * frac:5.1f}%  '
                             f'{s["rows"]:,} / {exp:,}  {state}{speed}')
            running = subprocess.run(['pgrep', '-f', 'download_amr_full.py --run'],
                                     capture_output=True, text=True).stdout.strip()
            size = sum(os.path.getsize(os.path.join(dp, f))
                       for dp, _, fs in os.walk(out) for f in fs if f.endswith('.csv'))
            finished = all(data.get(n, {}).get('done') for n in STREAMS)
            state_text = ('finished, all rows downloaded' if finished else
                          'yes' if running else 'NO (run the start command again to resume)')
            lines += ['', f'Running: {state_text}'
                          f'    On disk: {size / 1e9:.2f} GB',
                      '', 'Last log lines:']
            log_path = os.path.join(out, 'download.log')
            if os.path.exists(log_path):
                with open(log_path, errors='ignore') as fh:
                    lines += ['  ' + l.rstrip() for l in fh.readlines()[-3:]]
            print('\033[2J\033[H' + '\n'.join(lines), flush=True)
            time.sleep(every)
    except KeyboardInterrupt:
        print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', default='Data/amr_full')
    ap.add_argument('--streams', nargs='+', choices=list(STREAMS), default=list(STREAMS),
                    help='which evidence types to download (default: lab, then computational)')
    ap.add_argument('--page', type=int, default=25000, help='rows per request')
    ap.add_argument('--part-rows', type=int, default=500000, help='rows per CSV file')
    ap.add_argument('--workers', type=int, default=8, help='parallel downloads (default 8)')
    ap.add_argument('--status', action='store_true', help='show progress and exit')
    ap.add_argument('--watch', action='store_true', help='live progress view (Ctrl+C closes it)')
    ap.add_argument('--run', action='store_true', help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.status:
        status(args.out)
        return
    if args.watch:
        watch(args.out)
        return
    if '--run' not in sys.argv:
        # Re-exec with a marker so --status can tell whether a download is running.
        os.execv(sys.executable, [sys.executable, '-u', __file__, '--run'] + sys.argv[1:])

    os.makedirs(args.out, exist_ok=True)
    keep_awake()
    state = State(os.path.join(args.out, 'state.json'))
    state.data.setdefault('started', datetime.now(timezone.utc).isoformat(timespec='seconds'))
    state.data['api'] = API
    state.save()

    for name in args.streams:
        download_stream(name, STREAMS[name], args.out, state, args.page, args.part_rows,
                        args.workers)

    manifest = {
        'api': API,
        'started': state.data['started'],
        'finished': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'streams': {n: {k: state.data[n].get(k) for k in ('rows', 'expected', 'finished')}
                    for n in args.streams},
        'columns': HEADER,
    }
    with open(os.path.join(args.out, 'manifest.json'), 'w') as fh:
        json.dump(manifest, fh, indent=2)
    log(f'All done. Manifest: {os.path.join(args.out, "manifest.json")}')


if __name__ == '__main__':
    main()
