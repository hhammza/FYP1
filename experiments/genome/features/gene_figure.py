"""
Figure for the report: what AMRFinderPlus found in the complete genomes.

Left: the 20 genes and point mutations found in the most genomes, coloured by
kind. Right: how many genes and mutations each genome carries. Both from
gene_info.csv and gene_matrix.parquet (build_gene_matrix.py).

    python experiments/genome/features/gene_figure.py   # → ../results/figures/gene_summary.png
"""
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'results', 'figures', 'gene_summary.png')

KINDS = {'gene': ('Acquired gene', '#2a78d6'), 'point_mutation': ('Point mutation', '#eb6834')}
INK, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
TOP = 20


def main():
    info = pd.read_csv(os.path.join(HERE, 'gene_info.csv'))
    matrix = pd.read_parquet(os.path.join(HERE, 'gene_matrix.parquet'))
    n_genomes = len(matrix)
    per_genome = matrix.sum(axis=1)
    top = info.sort_values('genomes', ascending=False).head(TOP).iloc[::-1]

    fig, (left, right) = plt.subplots(1, 2, figsize=(10, 5.2), facecolor=SURFACE,
                                      gridspec_kw={'width_ratios': [1.25, 1]})
    for ax in (left, right):
        ax.set_facecolor(SURFACE)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9, length=0)
        ax.grid(axis='x', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)

    share = top['genomes'] / n_genomes * 100
    colours = [KINDS.get(k, KINDS['gene'])[1] for k in top['type']]
    left.barh(range(len(top)), share, color=colours, height=0.7)
    left.set_yticks(range(len(top)))
    left.set_yticklabels([f'{s}  ({c.lower()})' for s, c in zip(top['symbol'], top['class'])],
                         fontsize=8.5, color=INK)
    left.set_xlabel('Share of genomes (%)', fontsize=9, color=MUTED)
    left.set_title(f'The {TOP} most common genes and mutations', fontsize=10, color=INK, loc='left')
    left.legend(handles=[Patch(color=colour, label=label) for label, colour in KINDS.values()],
                frameon=False, fontsize=9, loc='lower right', labelcolor=INK)

    bins = list(range(0, int(per_genome.max()) + 2))
    right.hist(per_genome, bins=bins, color='#2a78d6', edgecolor=SURFACE, linewidth=0.8)
    right.grid(axis='x', visible=False)
    right.grid(axis='y', color=GRID, linewidth=0.8)
    right.set_xlabel('Genes and mutations in one genome', fontsize=9, color=MUTED)
    right.set_ylabel('Genomes', fontsize=9, color=MUTED)
    right.set_title(f'Per genome: median {per_genome.median():.0f}, {(per_genome == 0).mean():.1%} none',
                    fontsize=10, color=INK, loc='left')

    fig.suptitle(f'AMRFinderPlus 4.2.7 on {n_genomes:,} complete genomes (core AMR elements)',
                 fontsize=11, color=INK, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=SURFACE)
    print('wrote', OUT)


if __name__ == '__main__':
    main()
