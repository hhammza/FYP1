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

Genomes elsewhere, gzipped or not, in subfolders (the Google Drive download of
notebooks/download_genomes_to_drive.ipynb), with results written there too:

    python run_amrfinder.py --genomes DIR --list lab_genomes_todo.csv \
        --taxa taxon_species.csv --out OUT_DIR --skip-genus Mycobacterium

(notebooks/amrfinder_on_drive.ipynb runs this in Colab). A gzipped genome is
unpacked to a temporary file for AMRFinderPlus and deleted afterwards.

--organism turns on point-mutation detection (for example gyrA_S83L) and
species-specific filtering. Each genome gets it only when its NCBI species or
genus is on AMRFinderPlus's list; other genomes (Mycobacterium tuberculosis,
Klebsiella michiganensis, Acinetobacter nosocomialis) run without it, which
still finds acquired genes but reports no point mutations.
"""
import argparse
import glob
import gzip
import os
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(EXPERIMENTS)
sys.path.insert(0, EXPERIMENTS)
try:
    from lib import data_prep  # noqa: E402
    DATA = data_prep.data_root()
except ImportError:            # run on its own (Colab): every path comes from the options
    DATA = os.getcwd()

GENOME_DIR = os.path.join(DATA, 'genomes_full')
MANIFEST = os.path.join(GENOME_DIR, 'manifest.csv')
OUT_DIR = os.path.join(DATA, 'amrfinder_output')
SUMMARY = os.path.join(OUT_DIR, 'run_summary.csv')
TAXA = os.path.join(ROOT, 'backend', 'taxon_species.csv')

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


def genome_files(folder):
    """{genome_id: path} for every finished .fna or .fna.gz under `folder`, any depth."""
    out = {}
    for path in glob.glob(os.path.join(folder, '**', '*.fna*'), recursive=True):
        name = os.path.basename(path)
        if name.endswith('.fna.gz'):
            out[name[:-len('.fna.gz')]] = path
        elif name.endswith('.fna'):
            out[name[:-len('.fna')]] = path
    return out


def genomes_with_organism(supported, genome_dir=None, genome_list=None, taxa_path=TAXA):
    if genome_dir:
        listed = pd.read_csv(genome_list, dtype={'genome_id': str})
        listed = listed[[c for c in ('genome_id', 'taxon_id', 'genus') if c in listed]]
        files = genome_files(genome_dir)
        listed['fna'] = listed['genome_id'].map(files)
        df = listed[listed['fna'].notna()]
    else:
        df = pd.read_csv(MANIFEST, dtype={'genome_id': str})
        df['fna'] = df['genome_id'].map(lambda g: os.path.join(GENOME_DIR, f'{g}.fna'))
        df = df[df['fna'].map(os.path.exists)]
    taxa = pd.read_csv(taxa_path)
    df = df.merge(taxa[['taxon_id', 'species_name', 'genus_name']], on='taxon_id', how='left')
    if 'genus' in df:          # the list's genus where the taxon table has none
        df['genus_name'] = df['genus_name'].fillna(df['genus'])
    df['organism'] = [organism_for(s, g, supported) for s, g in zip(df['species_name'], df['genus_name'])]
    return df.reset_index(drop=True)


def run_one(amrfinder, env, row, threads):
    out = os.path.join(OUT_DIR, f'{row.genome_id}.tsv')
    if OUT_DIR.startswith('/content/drive') and not os.path.ismount('/content/drive'):
        # Colab lost Google Drive: writing now would land on its temporary disk
        raise SystemExit('Google Drive is no longer connected. Runtime → Disconnect and delete '
                         'runtime, then Run all: finished genomes are skipped.')
    tmp = out + '.part'
    fna, unpacked = row.fna, None
    if fna.endswith('.gz'):    # AMRFinderPlus reads plain FASTA: unpack to local disk first
        unpacked = os.path.join(tempfile.gettempdir(), f'{row.genome_id}.fna')
        with gzip.open(fna, 'rb') as src, open(unpacked, 'wb') as dst:
            shutil.copyfileobj(src, dst)
        fna = unpacked
    cmd = [amrfinder, '-n', fna, '--name', row.genome_id, '--threads', str(threads), '-o', tmp]
    # Missing organism is NaN here, not None (pandas 3 string columns), and NaN is truthy
    if isinstance(row.organism, str):
        cmd += ['--organism', row.organism]
    start = time.time()
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    seconds = round(time.time() - start, 1)
    if unpacked:
        os.remove(unpacked)
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
    ap.add_argument('--genomes', help='folder of .fna / .fna.gz files, any depth (needs --list)')
    ap.add_argument('--list', help='CSV with genome_id and taxon_id for the genomes in --genomes')
    ap.add_argument('--taxa', default=TAXA, help='taxon_species.csv (species per taxon ID)')
    ap.add_argument('--out', help='folder for the .tsv results (default Data/amrfinder_output/)')
    ap.add_argument('--skip-genus', action='append', default=[],
                    help='leave out a genus, e.g. Mycobacterium (repeatable)')
    args = ap.parse_args()
    global OUT_DIR, SUMMARY
    if args.out:
        OUT_DIR, SUMMARY = args.out, os.path.join(args.out, 'run_summary.csv')
    if args.genomes and not args.list:
        ap.error('--genomes needs --list (genome_id, taxon_id)')
    os.makedirs(OUT_DIR, exist_ok=True)

    amrfinder = find_amrfinder(args.amrfinder)
    env = tool_env(amrfinder)
    version = subprocess.run([amrfinder, '--version'], capture_output=True, text=True, env=env).stdout.strip()
    db = subprocess.run([amrfinder, '--database_version'], capture_output=True, text=True, env=env)
    db_version = next((l.split(':', 1)[1].strip() for l in (db.stdout + db.stderr).splitlines()
                       if l.startswith('Database version')), 'unknown')
    print(f'[amrfinder] version {version}, database {db_version}')

    genomes = genomes_with_organism(supported_organisms(amrfinder, env),
                                    args.genomes, args.list, args.taxa)
    if args.skip_genus:
        skipped = genomes['genus_name'].isin(args.skip_genus)
        print(f'[amrfinder] leaving out {int(skipped.sum()):,} genomes of {", ".join(args.skip_genus)}')
        genomes = genomes[~skipped].reset_index(drop=True)
    if args.limit:
        genomes = genomes.head(args.limit)
    done = genomes['genome_id'].map(lambda g: os.path.exists(os.path.join(OUT_DIR, f'{g}.tsv')))
    todo = genomes[~done]
    print(f'[amrfinder] {len(genomes):,} genomes downloaded, {done.sum():,} already run, '
          f'{len(todo):,} to run; {genomes["organism"].isna().sum()} without --organism')

    previous = pd.read_csv(SUMMARY, dtype={'genome_id': str}) if os.path.exists(SUMMARY) else pd.DataFrame()
    # Genomes finished by a run that was stopped before it saved the summary
    # have a .tsv but no summary row; recover their organism and hit count.
    known = set(previous['genome_id']) if len(previous) else set()
    orphans = genomes[done & ~genomes['genome_id'].isin(known)]
    recovered = [{'genome_id': r.genome_id, 'organism': r.organism,
                  'hits': sum(1 for _ in open(os.path.join(OUT_DIR, f'{r.genome_id}.tsv'))) - 1,
                  'seconds': None, 'error': None} for r in orphans.itertuples()]
    if recovered:
        print(f'[amrfinder] {len(recovered):,} finished genomes had no summary row; recovered')

    def save_summary(results):
        summary = pd.concat([previous, pd.DataFrame(recovered + results)], ignore_index=True)
        if len(summary):
            summary = summary.drop_duplicates('genome_id', keep='last')
            summary['amrfinder_version'] = version
            summary['database_version'] = db_version
            summary.to_csv(SUMMARY, index=False)
        return summary

    # Saved every 25 genomes, so stopping the run loses nothing
    results = []
    t0 = time.time()
    with ThreadPoolExecutor(args.jobs) as pool:
        jobs = [pool.submit(run_one, amrfinder, env, row, args.threads) for row in todo.itertuples()]
        for n, job in enumerate(as_completed(jobs), 1):
            r = job.result()
            results.append(r)
            if r['error']:
                print(f'  FAILED {r["genome_id"]}: {r["error"]}')
            if n % 25 == 0 or n == len(jobs):
                left = (len(jobs) - n) / (n / (time.time() - t0)) / 3600
                print(f'  {n:,} / {len(jobs):,}, about {left:.1f} h left', flush=True)
                save_summary(results)

    summary = save_summary(results)
    failed = summary['error'].notna().sum() if len(summary) else 0
    print(f'[amrfinder] {len(summary):,} genomes in {os.path.relpath(SUMMARY)}; {failed} failed '
          f'(re-run to retry)')


if __name__ == '__main__':
    main()
