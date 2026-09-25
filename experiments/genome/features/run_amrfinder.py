"""
Run AMRFinderPlus on every complete assembly in Data/genomes_full/.

Needs the `amrfinder` conda environment (see experiments/genome/README.md)
and the downloads from download_genomes.py. Run it with the project's
Python; it finds the amrfinder binary itself.

    python experiments/genome/features/run_amrfinder.py            # all
    python experiments/genome/features/run_amrfinder.py --limit 5  # test

Writes Data/amrfinder_output/<genome_id>.tsv (gitignored) and
Data/amrfinder_output/run_summary.csv (organism used, hits, seconds, error).
Safe to stop and re-run: genomes with a finished .tsv are skipped.

--organism turns on point-mutation detection (for example gyrA_S83L) and
species-specific filtering. Each genome gets it only when its NCBI species or
genus is on AMRFinderPlus's list; other genomes (Mycobacterium tuberculosis,
Klebsiella michiganensis, Acinetobacter nosocomialis) run without it, which
still finds acquired genes but reports no point mutations.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(EXPERIMENTS)
sys.path.insert(0, EXPERIMENTS)
from lib import data_prep  # noqa: E402

GENOME_DIR = os.path.join(data_prep.data_root(), 'genomes_full')
MANIFEST = os.path.join(GENOME_DIR, 'manifest.csv')
OUT_DIR = os.path.join(data_prep.data_root(), 'amrfinder_output')
SUMMARY = os.path.join(OUT_DIR, 'run_summary.csv')

# Genera AMRFinderPlus covers as one organism; Shigella is part of Escherichia
GENUS_ALIASES = {'Shigella': 'Escherichia'}


def find_amrfinder(given=None):
    candidates = [given, shutil.which('amrfinder')] + [
        os.path.expanduser(f'~/{base}/envs/amrfinder/bin/amrfinder')
        for base in ('anaconda3', 'miniconda3', 'miniforge3')] + [
        '/opt/anaconda3/envs/amrfinder/bin/amrfinder']
    for path in candidates:
        if path and os.path.exists(path):
            return path
    sys.exit('amrfinder not found. Install it first:\n'
             '  conda create -n amrfinder -c conda-forge -c bioconda ncbi-amrfinderplus\n'
             '  conda activate amrfinder && amrfinder -u')


def tool_env(amrfinder):
    """The conda env's bin first on PATH, so amrfinder finds blast and hmmer, and
    CONDA_PREFIX set to that env, which is where amrfinder looks for its database."""
    env = dict(os.environ)
    env['PATH'] = os.path.dirname(amrfinder) + os.pathsep + env.get('PATH', '')
    env['CONDA_PREFIX'] = os.path.dirname(os.path.dirname(amrfinder))
    return env


def supported_organisms(amrfinder, env):
    out = subprocess.run([amrfinder, '--list_organisms'], capture_output=True, text=True, env=env)
    line = next(l for l in (out.stdout + out.stderr).splitlines() if 'organism options' in l)
    return {o.strip() for o in line.split(':', 1)[1].split(',')}


def organism_for(species_name, genus_name, supported):
    """The --organism value for a genome, or None if AMRFinderPlus has none."""
    if isinstance(species_name, str) and species_name.replace(' ', '_') in supported:
        return species_name.replace(' ', '_')
    genus = GENUS_ALIASES.get(genus_name, genus_name)
    return genus if genus in supported else None


def genomes_with_organism(supported):
    manifest = pd.read_csv(MANIFEST, dtype={'genome_id': str})
    taxa = pd.read_csv(os.path.join(ROOT, 'backend', 'taxon_species.csv'))
    df = manifest.merge(taxa[['taxon_id', 'species_name', 'genus_name']], on='taxon_id', how='left')
    df['organism'] = [organism_for(s, g, supported) for s, g in zip(df['species_name'], df['genus_name'])]
    df['fna'] = df['genome_id'].map(lambda g: os.path.join(GENOME_DIR, f'{g}.fna'))
    return df[df['fna'].map(os.path.exists)]


def run_one(amrfinder, env, row, threads):
    out = os.path.join(OUT_DIR, f'{row.genome_id}.tsv')
    tmp = out + '.part'
    cmd = [amrfinder, '-n', row.fna, '--name', row.genome_id, '--threads', str(threads), '-o', tmp]
    if row.organism:
        cmd += ['--organism', row.organism]
    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    seconds = round(time.time() - start, 1)
    if proc.returncode != 0 or not os.path.exists(tmp):
        return {'genome_id': row.genome_id, 'organism': row.organism, 'hits': None,
                'seconds': seconds, 'error': proc.stderr.strip().splitlines()[-1:] or ['unknown']}
    os.replace(tmp, out)
    hits = sum(1 for _ in open(out)) - 1
    return {'genome_id': row.genome_id, 'organism': row.organism, 'hits': hits,
            'seconds': seconds, 'error': None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--limit', type=int, help='only the first N genomes (for testing)')
    ap.add_argument('--jobs', type=int, default=4, help='genomes at a time (default 4)')
    ap.add_argument('--threads', type=int, default=2, help='threads per genome (default 2)')
    ap.add_argument('--amrfinder', help='path to the amrfinder binary')
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)

    amrfinder = find_amrfinder(args.amrfinder)
    env = tool_env(amrfinder)
    version = subprocess.run([amrfinder, '--version'], capture_output=True, text=True, env=env).stdout.strip()
    db = subprocess.run([amrfinder, '--database_version'], capture_output=True, text=True, env=env)
    db_version = next((l.split(':', 1)[1].strip() for l in (db.stdout + db.stderr).splitlines()
                       if l.startswith('Database version')), 'unknown')
    print(f'[amrfinder] version {version}, database {db_version}')

    genomes = genomes_with_organism(supported_organisms(amrfinder, env))
    if args.limit:
        genomes = genomes.head(args.limit)
    done = genomes['genome_id'].map(lambda g: os.path.exists(os.path.join(OUT_DIR, f'{g}.tsv')))
    todo = genomes[~done]
    print(f'[amrfinder] {len(genomes):,} genomes downloaded, {done.sum():,} already run, '
          f'{len(todo):,} to run; {genomes["organism"].isna().sum()} without --organism')

    previous = pd.read_csv(SUMMARY, dtype={'genome_id': str}) if os.path.exists(SUMMARY) else pd.DataFrame()
    results = []
    with ThreadPoolExecutor(args.jobs) as pool:
        jobs = [pool.submit(run_one, amrfinder, env, row, args.threads) for row in todo.itertuples()]
        for n, job in enumerate(as_completed(jobs), 1):
            r = job.result()
            results.append(r)
            if r['error']:
                print(f'  FAILED {r["genome_id"]}: {r["error"]}')
            if n % 25 == 0 or n == len(jobs):
                print(f'  {n:,} / {len(jobs):,}')

    summary = pd.concat([previous, pd.DataFrame(results)], ignore_index=True)
    if len(summary):
        summary = summary.drop_duplicates('genome_id', keep='last')
        summary['amrfinder_version'] = version
        summary['database_version'] = db_version
        summary.to_csv(SUMMARY, index=False)
    failed = summary['error'].notna().sum() if len(summary) else 0
    print(f'[amrfinder] {len(summary):,} genomes in {os.path.relpath(SUMMARY)}; {failed} failed '
          f'(re-run to retry)')


if __name__ == '__main__':
    main()
