"""Download one exact AMRFinderPlus database version (used by backend/Dockerfile).

The gene model was trained with AMRFinderPlus 4.2.7 and database 2026-08-07.1
(Hamza, gene_summary.md). `amrfinder -u` would fetch the newest database, so
gene and mutation names could drift from training; this fetches the training
version instead.

    python fetch_amrfinder_db.py <version> <target folder>

Downloads every file of NCBI's database folder for that version (not the
documentation subfolders), checks that version.txt names the version asked
for, and exits non-zero on any failure, so the image build stops. The Dockerfile
then runs `amrfinder_index` on the folder. Standard library only: the build
runs it before the Python requirements are installed.
"""
import os
import re
import sys
import time
import urllib.request

BASE = 'https://ftp.ncbi.nlm.nih.gov/pathogen/Antimicrobial_resistance/AMRFinderPlus/database/4.2/'


def get(url, tries=4):
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                return r.read()
        except OSError as e:
            if attempt == tries:
                raise
            print(f'  retry {attempt} for {url}: {e}', flush=True)
            time.sleep(5 * attempt)


def main(version, target):
    folder = f'{BASE}{version}/'
    listing = get(folder).decode('utf-8', errors='replace')
    names = sorted({n for n in re.findall(r'href="([^"?/][^"?]*)"', listing)
                    if not n.startswith(('http', 'mailto')) and not n.endswith('/')})
    if not names or 'version.txt' not in names:
        sys.exit(f'no database files found at {folder}')
    os.makedirs(target, exist_ok=True)
    total = 0
    for name in names:
        data = get(folder + name)
        with open(os.path.join(target, name), 'wb') as fh:
            fh.write(data)
        total += len(data)
    with open(os.path.join(target, 'version.txt'), encoding='utf-8') as fh:
        found = fh.read().strip()
    if found != version:
        sys.exit(f'version.txt says {found!r}, expected {version!r}')
    print(f'AMRFinderPlus database {version}: {len(names)} files, {total / 1e6:.0f} MB in {target}')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
