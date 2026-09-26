"""
Build the genome x gene matrix from the AMRFinderPlus output.

Format agreed with Hamza in progress/formats/README.md section 3.

    python experiments/genome/features/build_gene_matrix.py             # all
    python experiments/genome/features/build_gene_matrix.py --sample 20 # sample

Reads Data/amrfinder_output/<genome_id>.tsv and writes, in
experiments/genome/features/ (or sample/ for --sample):

  gene_matrix.parquet  one row per searched genome (index `Genome ID`, string),
                       one uint8 0/1 column per AMRFinderPlus Element symbol,
                       genes and point mutations, Scope = core and Type = AMR
  gene_info.csv        one row per column: symbol, type, class, subclass, genomes
  gene_summary.md      genes found, genes per genome, the join with the labels,
                       and the most common genes overall and per genus

A genome counts as searched when its .tsv exists: run_amrfinder.py writes it
only when AMRFinderPlus succeeds, and a genome with no hits gets a header-only
file, so it becomes a row of zeros. A genome that was never searched has no
row. The sample takes genomes from every genus searched so far, with and
without hits, chosen with a fixed seed.
"""
import argparse
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, EXPERIMENTS)
from lib import data_prep  # noqa: E402

DATA = data_prep.data_root()
AMR_DIR = os.path.join(DATA, 'amrfinder_output')
MANIFEST = os.path.join(DATA, 'genomes_full', 'manifest.csv')
MAPPED_DIR = os.path.join(DATA, 'mapped_output')

POINT_SUBTYPES = {'POINT', 'POINT_DISRUPT'}
SEED = 42


def searched_genomes():
    """Genome IDs with a finished AMRFinderPlus file, as strings."""
    return sorted(os.path.basename(p)[:-4] for p in glob.glob(os.path.join(AMR_DIR, '*.tsv')))


def read_hits(genome_ids):
    """Core AMR hits for these genomes: one row per (genome, symbol)."""
    frames = []
    for gid in genome_ids:
        df = pd.read_csv(os.path.join(AMR_DIR, f'{gid}.tsv'), sep='\t', dtype=str)
        df['Genome ID'] = gid   # from the file name, never parsed as a float
        frames.append(df)
    hits = pd.concat(frames, ignore_index=True)
    return hits[(hits['Scope'] == 'core') & (hits['Type'] == 'AMR')]


def genus_of(genome_ids):
    """Genus of each genome, from the manifest folder name taxon_<id>_<Genus>_<species>."""
    manifest = pd.read_csv(MANIFEST, dtype={'genome_id': str}, usecols=['genome_id', 'folder'])
    genus = manifest.set_index('genome_id')['folder'].str.split('_').str[2]
    return genus.reindex(genome_ids).fillna('unknown')


def pick_sample(genome_ids, hits, n):
    """n genomes spread over genus and hits / no hits, round-robin after a seeded shuffle."""
    info = pd.DataFrame({'genome_id': genome_ids, 'genus': genus_of(genome_ids).values})
    info['has_hits'] = info['genome_id'].isin(hits['Genome ID'])
    info = info.sample(frac=1, random_state=SEED)
    info['turn'] = info.groupby(['genus', 'has_hits']).cumcount()
    return sorted(info.sort_values(['turn', 'genus', 'has_hits']).head(n)['genome_id'])


def build(genome_ids, hits):
    hits = hits[hits['Genome ID'].isin(genome_ids)]
    pairs = hits[['Genome ID', 'Element symbol']].drop_duplicates()
    matrix = (pd.crosstab(pairs['Genome ID'], pairs['Element symbol'])
              .reindex(genome_ids, fill_value=0)
              .clip(upper=1)
              .astype('uint8'))
    matrix.index = matrix.index.astype(str)
    matrix.index.name = 'Genome ID'
    matrix.columns.name = None
    matrix = matrix[sorted(matrix.columns)]

    first = hits.drop_duplicates('Element symbol').set_index('Element symbol')
    info = pd.DataFrame({
        'symbol': matrix.columns,
        'type': ['point_mutation' if first.at[s, 'Subtype'] in POINT_SUBTYPES else 'gene'
                 for s in matrix.columns],
        'class': [first.at[s, 'Class'] for s in matrix.columns],
        'subclass': [first.at[s, 'Subclass'] for s in matrix.columns],
        'genomes': matrix.sum().astype(int).values,
    })
    return matrix, info


def mapped_genome_ids():
    ids = set()
    for path in glob.glob(os.path.join(MAPPED_DIR, '*_mapped.csv')):
        ids.update(pd.read_csv(path, usecols=['Genome ID'], dtype=str)['Genome ID'].dropna())
    return ids


def summary(matrix, info, check_join):
    genus = genus_of(list(matrix.index))
    per_genome = matrix.sum(axis=1)
    print(f'[matrix] {len(matrix):,} genomes x {matrix.shape[1]:,} symbols '
          f'({(info["type"] == "point_mutation").sum()} point mutations)')
    print(f'[matrix] {(per_genome == 0).sum():,} genomes searched with no core AMR hit; '
          f'median {per_genome.median():.0f} symbols per genome, max {per_genome.max()}')
    for g, rows in matrix.groupby(genus.values):
        top = rows.sum().sort_values(ascending=False)
        top = ', '.join(f'{s} ({c})' for s, c in top[top > 0].head(5).items()) or 'none'
        print(f'  {g}: {len(rows):,} genomes; top: {top}')
    if check_join:
        missing = mapped_genome_ids() - set(matrix.index)
        print(f'[join] {len(missing):,} genomes in Data/mapped_output/ have no row')


def write_summary(matrix, info, path):
    """gene_summary.md: genes found, genes per genome, the join, and the most
    common genes overall and per genus. Rewritten on every full build."""
    n = len(matrix)
    per_genome = matrix.sum(axis=1)
    genus = pd.Series(genus_of(list(matrix.index)).values, index=matrix.index)
    mapped = mapped_genome_ids()
    in_matrix = set(matrix.index)
    no_row = sorted(mapped - in_matrix)
    unmapped = sorted(in_matrix - mapped)
    points = int((info['type'] == 'point_mutation').sum())
    version = database = 'unknown'
    summary_csv = os.path.join(AMR_DIR, 'run_summary.csv')
    if os.path.exists(summary_csv):
        s = pd.read_csv(summary_csv, dtype=str)
        version = s['amrfinder_version'].dropna().iloc[-1]
        database = s['database_version'].dropna().iloc[-1]
    pct = lambda k, total=n: f'{100 * k / total:.1f}%'

    out = ['# Gene matrix summary', '',
           f'Written by `build_gene_matrix.py`; regenerate it with the matrix. AMRFinderPlus {version}, '
           f'database {database}. Only Scope = core, Type = AMR elements are counted.', '',
           '## Genes found', '',
           '| | Count |', '|---|---|',
           f'| Genomes searched | {n:,} |',
           f'| Genomes with at least one gene or mutation | {(per_genome > 0).sum():,} ({pct((per_genome > 0).sum())}) |',
           f'| Genomes with none (searched, nothing found) | {(per_genome == 0).sum():,} ({pct((per_genome == 0).sum())}) |',
           f'| Different genes and mutations (matrix columns) | {matrix.shape[1]:,}: {matrix.shape[1] - points:,} genes, {points:,} point mutations |',
           f'| Hits (cells that are 1) | {int(matrix.values.sum()):,} of {matrix.size:,} ({pct(matrix.values.sum(), matrix.size)}) |',
           '', '## Genes per genome', '',
           f'Median {per_genome.median():g}, mean {per_genome.mean():.1f}, maximum {per_genome.max()}.', '',
           '| Genes and mutations | Genomes | Share |', '|---|---|---|']
    for label, lo, hi in (('0', 0, 0), ('1', 1, 1), ('2', 2, 2), ('3 to 5', 3, 5), ('6 to 10', 6, 10),
                          ('11 to 20', 11, 20), ('21 or more', 21, 10 ** 6)):
        k = int(((per_genome >= lo) & (per_genome <= hi)).sum())
        out.append(f'| {label} | {k:,} | {pct(k)} |')

    out += ['', '## Join with the labels', '',
            f'- Every Genome ID in `Data/mapped_output/` has a row: **{"yes" if not no_row else "no"}** '
            f'({len(mapped) - len(no_row):,} of {len(mapped):,}).']
    if no_row:
        out.append(f'- Without a row: {", ".join(no_row[:10])}{" ..." if len(no_row) > 10 else ""}')
    out.append(f'- Matrix genomes with no rows in `Data/mapped_output/`: {len(unmapped):,}'
               + (f' ({", ".join(unmapped[:5])}{" ..." if len(unmapped) > 5 else ""})' if unmapped else '') + '.')

    classes = []
    for cls, symbols in info.groupby('class')['symbol']:
        classes.append((int((matrix[list(symbols)].sum(axis=1) > 0).sum()), cls, len(symbols)))
    out += ['', '## Drug classes', '', '| Class | Genomes with a gene | Genes and mutations |', '|---|---|---|']
    for k, cls, count in sorted(classes, reverse=True)[:12]:
        out.append(f'| {cls.title()} | {k:,} ({pct(k)}) | {count} |')

    top = info.sort_values(['genomes', 'symbol'], ascending=[False, True]).head(15)
    out += ['', '## Most common genes and mutations', '', '| Gene | Type | Class | Genomes |', '|---|---|---|---|']
    for _, r in top.iterrows():
        out.append(f'| `{r.symbol}` | {r.type.replace("_", " ")} | {r["class"].title()} | {r.genomes:,} ({pct(r.genomes)}) |')

    out += ['', '## Most common genes per genus', '',
            '| Genus | Genomes | With a gene | Median | Most common (share of the genus) |', '|---|---|---|---|---|']
    for g in genus.value_counts().index:
        rows = matrix[genus == g]
        counts = rows.sum().sort_values(ascending=False)
        common = ', '.join(f'`{s}` {100 * c / len(rows):.0f}%' for s, c in counts[counts > 0].head(5).items()) or 'none found'
        with_gene = int((rows.sum(axis=1) > 0).sum())
        out.append(f'| *{g}* | {len(rows):,} | {pct(with_gene, len(rows))} | {rows.sum(axis=1).median():g} | {common} |')

    with open(path, 'w') as fh:
        fh.write('\n'.join(out) + '\n')
    print(f'[matrix] wrote {os.path.relpath(path)}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sample', type=int, help='only N genomes, written to sample/')
    args = ap.parse_args()

    genome_ids = searched_genomes()
    if not genome_ids:
        sys.exit(f'No AMRFinderPlus output in {AMR_DIR}; run run_amrfinder.py first')
    hits = read_hits(genome_ids)
    out_dir = HERE
    if args.sample:
        genome_ids = pick_sample(genome_ids, hits, args.sample)
        out_dir = os.path.join(HERE, 'sample')
    os.makedirs(out_dir, exist_ok=True)

    matrix, info = build(genome_ids, hits)
    matrix.to_parquet(os.path.join(out_dir, 'gene_matrix.parquet'))
    info.to_csv(os.path.join(out_dir, 'gene_info.csv'), index=False)
    print(f'[matrix] wrote {os.path.relpath(out_dir)}/gene_matrix.parquet and gene_info.csv')
    summary(matrix, info, check_join=not args.sample)
    if not args.sample:
        write_summary(matrix, info, os.path.join(out_dir, 'gene_summary.md'))


if __name__ == '__main__':
    main()
