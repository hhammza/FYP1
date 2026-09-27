"""Lineage clusters for a lineage-grouped split (Track B check).

    python experiments/genome/lineage.py

A genome-grouped split keeps each genome on one side, but near-identical
isolates (one outbreak, one clone) are separate genomes and can still land on
both sides. A model could then score well by recognising the lineage rather
than the resistance. Grouping by lineage cluster closes that gap.

Genomes are compared by the cosine distance between their 6-mer frequency
profiles (1 - cosine similarity), then clustered with average linkage and cut
at several distances, because there is no single right cut for "same lineage".
Measured on the 2,587 complete genomes:

    nearest neighbour      median 0.0002; 10% below 0.00001
    same species           median 0.0007; 90% below 0.003
    different species      at least 0.0068

so the cuts below run from near-clones to about species level. A model whose
gain over the taxonomy baseline survives the coarser cuts has learned more
than lineage.

Writes experiments/cache/lineage_clusters.csv: genome_id, lineage_<cut>...
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import kmers  # noqa: E402

OUT = os.path.join(EXPERIMENTS, 'cache', 'lineage_clusters.csv')

# name -> average-linkage cut on 6-mer cosine distance
CUTS = {
    'clone': 0.00005,     # near-identical isolates
    'close': 0.0002,      # the typical nearest-neighbour distance
    'broad': 0.0007,      # the typical distance within a species
    'species': 0.005,     # below every between-species distance seen
}


def cosine_distances(k=6):
    ids, counts, _, _ = kmers.load_counts()
    f, _ = kmers.kmer_matrix(counts, k)
    f = f.astype(np.float64)
    f /= np.linalg.norm(f, axis=1, keepdims=True)
    d = np.clip(1.0 - f @ f.T, 0.0, None)
    np.fill_diagonal(d, 0.0)
    return ids, (d + d.T) / 2          # exactly symmetric for squareform


def build():
    ids, d = cosine_distances()
    tree = linkage(squareform(d, checks=False), method='average')
    out = pd.DataFrame({'genome_id': ids})
    for name, cut in CUTS.items():
        out[f'lineage_{name}'] = fcluster(tree, t=cut, criterion='distance')
        sizes = out[f'lineage_{name}'].value_counts()
        print(f'[lineage] {name:8s} cut {cut:<8} {sizes.size:5,} clusters; '
              f'largest {sizes.iloc[0]:,} genomes; {int((sizes == 1).sum()):,} singletons')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f'[lineage] wrote {os.path.relpath(OUT, os.path.dirname(EXPERIMENTS))}')
    return out


def load():
    if not os.path.exists(OUT):
        raise FileNotFoundError(f'{OUT} missing: run python experiments/genome/lineage.py')
    return pd.read_csv(OUT, dtype={'genome_id': str})


if __name__ == '__main__':
    build()
