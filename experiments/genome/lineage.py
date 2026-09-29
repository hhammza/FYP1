"""Lineage clusters for a lineage-grouped split (Track B check).

    python experiments/genome/lineage.py

A genome-grouped split keeps each genome on one side, but near-identical
isolates (one outbreak, one clone) are separate genomes and can still land on
both sides. A model could then score well by recognising the lineage rather
than the resistance. Grouping by lineage cluster closes that gap.

Genomes are compared by the cosine distance between their 6-mer frequency
profiles (1 - cosine similarity), then clustered with average linkage and cut
at several distances, because there is no single right cut for "same lineage".
Measured on the first 2,587 complete genomes:

    nearest neighbour      median 0.0002; 10% below 0.00001
    same species           median 0.0007; 90% below 0.003
    different species      at least 0.0068

so the cuts below run from near-clones to about species level.

Clustering runs within each species (E. coli and Shigella as one, see
SAME_GENOMIC_SPECIES). Between-species distances are above the coarsest cut,
so this matches clustering all genomes at once. Checked on the 2,587: the
clone cut is identical, the others agree to an adjusted Rand index of at
least 0.997; the few differences are genomes whose recorded species
disagrees with their k-mer profile, which all-pairs clustering had joined
across species. Per species, memory grows with the largest species
(K. pneumoniae, 5,934 genomes: about 0.3 GB) instead of with all 24,926
genomes (about 5 GB), which an 8 GB laptop cannot hold.

Writes experiments/cache/lineage_clusters.csv: genome_id, species, lineage_<cut>...
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(HERE)
ROOT = os.path.dirname(EXPERIMENTS)
sys.path.insert(0, HERE)
sys.path.insert(0, EXPERIMENTS)
import kmers  # noqa: E402
from lib import data_prep  # noqa: E402

OUT = os.path.join(EXPERIMENTS, 'cache', 'lineage_clusters.csv')
TAXON_SPECIES = os.path.join(ROOT, 'backend', 'taxon_species.csv')
LAB_GENOMES = os.path.join(HERE, 'features', 'lab_genomes.csv')

# name -> average-linkage cut on 6-mer cosine distance
CUTS = {
    'clone': 0.00005,     # near-identical isolates
    'close': 0.0002,      # the typical nearest-neighbour distance
    'broad': 0.0007,      # the typical distance within a species
    'species': 0.005,     # below every between-species distance seen
}


def genome_species(ids):
    """Species taxon ID per genome, from the download manifest and Ali's
    lab-genome list (both carry the taxon ID) via backend/taxon_species.csv.
    Genomes with no species become 'unknown' and are clustered together."""
    frames = []
    manifest = os.path.join(data_prep.data_root(), 'genomes_full', 'manifest.csv')
    for path in (manifest, LAB_GENOMES):
        if os.path.exists(path):
            frames.append(pd.read_csv(path, dtype=str, usecols=['genome_id', 'taxon_id']))
    taxa = pd.concat(frames).drop_duplicates('genome_id').set_index('genome_id')['taxon_id']
    table = pd.read_csv(TAXON_SPECIES, dtype=str)
    species = dict(zip(table['taxon_id'], table['species_taxon_id'].fillna(table['taxon_id'])))
    out = pd.Series(ids, index=ids).map(taxa).map(species).replace(SAME_GENOMIC_SPECIES)
    return out.fillna('unknown').to_numpy()


# Shigella is genomically E. coli (named apart for clinical reasons), and its
# k-mer distances to E. coli fall inside the cuts, so they are clustered as one
# group: S. flexneri 623, S. dysenteriae 622, S. boydii 621, S. sonnei 624.
SAME_GENOMIC_SPECIES = {'621': '562', '622': '562', '623': '562', '624': '562'}


def cosine_distances(freq):
    """Pairwise 1 - cosine similarity of the rows of `freq`."""
    f = freq.astype(np.float64)
    f /= np.linalg.norm(f, axis=1, keepdims=True)
    d = np.clip(1.0 - f @ f.T, 0.0, None)
    np.fill_diagonal(d, 0.0)
    return (d + d.T) / 2          # exactly symmetric for squareform


def cluster_group(freq):
    """{cut name: cluster labels 1..k} for one species' genomes."""
    if len(freq) == 1:
        return {name: np.array([1]) for name in CUTS}
    tree = linkage(squareform(cosine_distances(freq), checks=False), method='average')
    return {name: fcluster(tree, t=cut, criterion='distance') for name, cut in CUTS.items()}


def build():
    ids, counts, _, _ = kmers.load_counts()
    freq, _ = kmers.kmer_matrix(counts, 6)
    species = genome_species(ids)
    out = pd.DataFrame({'genome_id': ids, 'species': species})
    labels = {name: np.zeros(len(ids), dtype=np.int64) for name in CUTS}
    offset = {name: 0 for name in CUTS}
    groups = pd.Series(np.arange(len(ids))).groupby(species)
    print(f'[lineage] {len(ids):,} genomes in {groups.ngroups:,} species; '
          f'largest {groups.size().max():,}')
    for _, idx in groups:
        rows = idx.to_numpy()
        for name, lab in cluster_group(freq[rows]).items():
            labels[name][rows] = lab + offset[name]      # unique across species
            offset[name] += int(lab.max())
    for name, cut in CUTS.items():
        out[f'lineage_{name}'] = labels[name]
        sizes = out[f'lineage_{name}'].value_counts()
        print(f'[lineage] {name:8s} cut {cut:<8} {sizes.size:6,} clusters; '
              f'largest {sizes.iloc[0]:,} genomes; {int((sizes == 1).sum()):,} singletons')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f'[lineage] wrote {os.path.relpath(OUT, ROOT)}')
    return out


def load():
    if not os.path.exists(OUT):
        raise FileNotFoundError(f'{OUT} missing: run python experiments/genome/lineage.py')
    return pd.read_csv(OUT, dtype={'genome_id': str})


if __name__ == '__main__':
    build()
