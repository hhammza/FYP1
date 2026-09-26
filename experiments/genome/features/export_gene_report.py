"""
Summarise the AMRFinderPlus run for the /genes page.

    python experiments/genome/features/export_gene_report.py

Reads Data/amrfinder_output/ and the cleaned AMR labels, and writes two files
the backend serves (both committed, since the deployed backend has no Data/):

  backend/trained_models/gene_report.json  run summary, top genes, genes per
      genome, drug classes, genes by genus, and gene vs lab result
  backend/trained_models/gene_hits.json    every genome's genes, for the lookup

Same filter as the gene matrix: Scope = core and Type = AMR. Run it again
after AMRFinderPlus finishes; the page shows how many genomes it covers.

Gene vs lab result compares, for one gene and an antibiotic its AMRFinderPlus
subclass says it acts on, how often genomes with and without the gene were
resistant. The main
table uses laboratory results only: most BV-BRC labels on these genomes come
from BV-BRC's own prediction models, which read the genome, so testing genes
against them would be partly circular. The computational table is kept, and
labelled, for comparison.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
ROOT = os.path.dirname(EXPERIMENTS)
sys.path[:0] = [HERE, EXPERIMENTS]
import build_gene_matrix as gm  # noqa: E402
from lib import data_prep  # noqa: E402
from amr_constants import DRUG_CLASS_MAP, normalize_antibiotic  # noqa: E402  (data_prep puts backend/ on the path)

OUT_DIR = os.path.join(ROOT, 'backend', 'trained_models')
SUMMARY = os.path.join(gm.AMR_DIR, 'run_summary.csv')

TOP_GENES = 20
HEATMAP_GENES = 15
HEATMAP_MIN_GENOMES = 10    # genera with fewer genomes are left off the heatmap
MIN_CARRIERS = {'lab': 5, 'all': 20}
MAX_PAIRS = 30
PREVIEW_GENES = 10
PREVIEW_GENOMES = 9

# Whether a gene acts on an antibiotic, from its AMRFinderPlus Subclass. A
# subclass word is either a family (matched by this project's drug class, see
# amr_constants.py) or a named drug (matched by canonical name), so aph(6)-Id
# (STREPTOMYCIN) is compared with streptomycin but not with gentamicin
FAMILIES = {
    'BETA-LACTAM': {'beta_lactam', 'carbapenem', 'monobactam'},
    'CARBAPENEM': {'carbapenem'},
    'QUINOLONE': {'fluoroquinolone'},
    'FLUOROQUINOLONE': {'fluoroquinolone'},
    'AMINOGLYCOSIDE': {'aminoglycoside'},
    'TETRACYCLINE': {'tetracycline'},
    'MACROLIDE': {'macrolide'},
    'LINCOSAMIDE': {'lincosamide'},
    'STREPTOGRAMIN': {'streptogramin'},
    'PHENICOL': {'phenicol'},
    'GLYCOPEPTIDE': {'glycopeptide'},
    'NITROFURAN': {'nitrofuran'},
}


def acts_on(subclass, antibiotic):
    parts = [normalize_antibiotic(p) for p in str(antibiotic).split('/')]
    classes = {DRUG_CLASS_MAP.get(x) for x in parts + [antibiotic]} - {None}
    for word in str(subclass).upper().split('/'):
        word = word.strip()
        if word in FAMILIES and classes & FAMILIES[word]:
            return True
        if word == 'CEPHALOSPORIN' and any(x.startswith(('cef', 'ceph')) for x in parts):
            return True
        if word == 'SULFONAMIDE' and any(x.startswith('sulf') for x in parts):
            return True
        if normalize_antibiotic(word.replace('_', ' ')) in parts:
            return True
    return False


def species_of(genome_ids):
    """'Escherichia coli' for each genome, from the manifest folder taxon_<id>_<Genus>_<species>."""
    manifest = pd.read_csv(gm.MANIFEST, dtype={'genome_id': str}, usecols=['genome_id', 'folder'])
    name = manifest.set_index('genome_id')['folder'].str.split('_', n=2).str[2].str.replace('_', ' ')
    return name.reindex(genome_ids).fillna('unknown')


def run_info(searched):
    downloaded = len(pd.read_csv(gm.MANIFEST, usecols=['genome_id']))
    version = database = None
    if os.path.exists(SUMMARY):
        s = pd.read_csv(SUMMARY, dtype=str)
        version = s['amrfinder_version'].dropna().iloc[-1] if 'amrfinder_version' in s else None
        database = s['database_version'].dropna().iloc[-1] if 'database_version' in s else None
    try:
        commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip() or None
    except OSError:
        commit = None
    return {
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'git_commit': commit,
        'amrfinder_version': version,
        'database_version': database,
        'genomes_downloaded': downloaded,
        'genomes_searched': len(searched),
        'complete': len(searched) >= downloaded,
        'filter': 'Scope = core, Type = AMR',
    }


def labels_per_genome(genome_ids):
    """One label per (genome, antibiotic, source): resistant if most of its rows say so."""
    df = data_prep.get_clean(verbose=False)
    df = df[df['Genome ID'].astype(str).isin(set(genome_ids))].copy()
    df['Genome ID'] = df['Genome ID'].astype(str)
    out = {}
    for source, rows in (('lab', df[df['label_source'] == 'lab']), ('all', df)):
        g = rows.groupby(['Genome ID', 'Antibiotic'], observed=True)['target'].mean()
        out[source] = (g >= 0.5).astype(int).rename('resistant').reset_index()
    return out


def gene_vs_lab(matrix, info, labels, source):
    rows = []
    classes = dict(zip(info['symbol'], info['class']))
    subclasses = dict(zip(info['symbol'], info['subclass']))
    lab = labels[source]
    for ab, group in lab.groupby('Antibiotic', observed=True):
        genomes = group.set_index('Genome ID')['resistant']
        genomes = genomes[genomes.index.isin(matrix.index)]
        if len(genomes) < MIN_CARRIERS[source]:
            continue
        sub = matrix.loc[genomes.index]
        for symbol in sub.columns[sub.sum() >= MIN_CARRIERS[source]]:
            if not acts_on(subclasses[symbol], ab):
                continue
            has = sub[symbol] == 1
            carriers, others = genomes[has], genomes[~has]
            rows.append({
                'gene': symbol, 'gene_class': classes[symbol], 'gene_subclass': subclasses[symbol],
                'antibiotic': str(ab),
                'carriers': int(len(carriers)), 'carriers_resistant': round(float(carriers.mean()), 4),
                'others': int(len(others)),
                'others_resistant': round(float(others.mean()), 4) if len(others) else None,
            })
    rows.sort(key=lambda r: (-r['carriers'], r['gene'], r['antibiotic']))
    return {'min_carriers': MIN_CARRIERS[source], 'pairs': rows[:MAX_PAIRS], 'pairs_total': len(rows),
            'genomes_labelled': int(labels[source]['Genome ID'].nunique())}


def main():
    searched = gm.searched_genomes()
    if not searched:
        sys.exit(f'No AMRFinderPlus output in {gm.AMR_DIR}; run run_amrfinder.py first')
    hits = gm.read_hits(searched)
    matrix, info = gm.build(searched, hits)
    species = species_of(searched)
    genus = species.str.split().str[0]
    per_genome = matrix.sum(axis=1)
    n = len(matrix)

    top = info.sort_values(['genomes', 'symbol'], ascending=[False, True]).head(TOP_GENES)
    names = hits.drop_duplicates('Element symbol').set_index('Element symbol')['Element name']

    class_rows = []
    for cls, symbols in info.groupby('class')['symbol']:
        carrying = int((matrix[list(symbols)].sum(axis=1) > 0).sum())
        class_rows.append({'class': cls, 'genomes': carrying, 'share': round(carrying / n, 4),
                           'symbols': int(len(symbols))})
    class_rows.sort(key=lambda r: -r['genomes'])

    genus_rows = []
    for g, idx in matrix.groupby(genus.values).groups.items():
        sub = matrix.loc[idx]
        counts = sub.sum().sort_values(ascending=False)
        genus_rows.append({
            'genus': g, 'genomes': int(len(sub)),
            'with_gene': round(float((sub.sum(axis=1) > 0).mean()), 4),
            'median_genes': float(sub.sum(axis=1).median()),
            'top': [{'gene': s, 'share': round(c / len(sub), 4)} for s, c in counts[counts > 0].head(5).items()],
        })
    genus_rows.sort(key=lambda r: -r['genomes'])
    heat_genera = [r['genus'] for r in genus_rows if r['genomes'] >= HEATMAP_MIN_GENOMES]
    heat_genes = list(top['symbol'].head(HEATMAP_GENES))
    heat = [[round(float(matrix.loc[genus.values == g, s].mean()), 4) for s in heat_genes] for g in heat_genera]

    histogram = per_genome.clip(upper=10).value_counts().sort_index()

    # A readable corner of the matrix: one genome per large genus that carries
    # at least two of the most common genes, plus one genome with none
    preview_genes = list(top['symbol'].head(PREVIEW_GENES))
    preview_ids = []
    for g in heat_genera[:PREVIEW_GENOMES - 1]:
        ids = [i for i in matrix.index[genus.values == g] if matrix.loc[i, preview_genes].sum() >= 2]
        if ids:
            preview_ids.append(sorted(ids)[0])
    preview_ids.append(sorted(matrix.index[per_genome.values == 0])[0])
    labels = labels_per_genome(searched)

    report = {
        'run': run_info(searched),
        'summary': {
            'genomes': n,
            'with_gene': int((per_genome > 0).sum()),
            'symbols': int(matrix.shape[1]),
            'genes': int((info['type'] == 'gene').sum()),
            'point_mutations': int((info['type'] == 'point_mutation').sum()),
            'median_genes': float(per_genome.median()),
            'max_genes': int(per_genome.max()),
        },
        'matrix': {
            'genomes': n, 'symbols': int(matrix.shape[1]), 'cells': int(matrix.size),
            'ones': int(matrix.values.sum()),
            'preview': {'genes': preview_genes, 'rows': [
                {'genome': i, 'species': species[i], 'values': [int(v) for v in matrix.loc[i, preview_genes]],
                 'total': int(per_genome[i])} for i in preview_ids]},
        },
        'genes_per_genome': [{'genes': int(k), 'genomes': int(v), 'capped': bool(k == 10)}
                             for k, v in histogram.items()],
        'top_genes': [{'gene': r.symbol, 'name': names.get(r.symbol), 'type': r.type, 'class': r['class'],
                       'subclass': r.subclass, 'genomes': int(r.genomes), 'share': round(r.genomes / n, 4)}
                      for _, r in top.iterrows()],
        'classes': class_rows,
        'genera': genus_rows,
        'heatmap': {'genera': heat_genera, 'genes': heat_genes, 'share': heat,
                    'min_genomes': HEATMAP_MIN_GENOMES},
        'gene_vs_lab': {s: gene_vs_lab(matrix, info, labels, s) for s in ('lab', 'all')},
    }

    lookup_cols = ['Genome ID', 'Element symbol', '% Identity to reference', '% Coverage of reference', 'Method']
    per = {gid: [] for gid in searched}
    for gid, sym, ident, cov, method in hits[lookup_cols].itertuples(index=False):
        per[gid].append([sym, float(ident), float(cov), method])
    symbols = {r.symbol: [r.type, r['class'], r.subclass, names.get(r.symbol)] for _, r in info.iterrows()}
    lookup = {'generated_at': report['run']['generated_at'], 'symbols': symbols,
              'genomes': {gid: {'species': species[gid], 'hits': per[gid]} for gid in searched}}

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, 'gene_report.json'), 'w') as fh:
        json.dump(report, fh, indent=1)
    with open(os.path.join(OUT_DIR, 'gene_hits.json'), 'w') as fh:
        json.dump(lookup, fh, separators=(',', ':'))
    r = report['run']
    print(f"[genes] {r['genomes_searched']:,} of {r['genomes_downloaded']:,} genomes searched; "
          f"{report['summary']['with_gene']:,} with a core AMR gene; {report['summary']['symbols']} symbols")
    for s in ('lab', 'all'):
        v = report['gene_vs_lab'][s]
        print(f"[genes] gene vs {s} labels: {v['pairs_total']} pairs over {v['genomes_labelled']:,} labelled genomes")
    print(f'[genes] wrote {os.path.relpath(OUT_DIR)}/gene_report.json and gene_hits.json')


if __name__ == '__main__':
    main()
