"""
List every genome with at least one laboratory AST result, for download.

Only 136 of the 2,587 genomes in Data/fasta_output/ have lab results, so the
genome models can barely be tested against real phenotypes. This lists all
22,475 lab-tested genomes in the cleaned data (v5) for download_genomes.py.

    python experiments/genome/features/select_lab_genomes.py
    python experiments/genome/features/download_genomes.py --genome-list \
        experiments/genome/features/lab_genomes.csv --workers 12

The order is round-robin across genera (seeded shuffle within each genus), so
a download stopped halfway still holds a balanced sample instead of only
Klebsiella and Neisseria, the two largest genera.

Writes experiments/genome/features/lab_genomes.csv: genome_id, taxon_id,
genus, lab_rows (lab results for that genome), lab_drugs.
"""
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, EXPERIMENTS)
from lib import data_prep  # noqa: E402

OUT = os.path.join(HERE, 'lab_genomes.csv')
SEED = 42


def main():
    df = data_prep.get_clean()
    lab = df[df['is_lab_confirmed'] == 1]
    genomes = (lab.groupby('Genome ID')
                  .agg(taxon_id=('Taxon ID', 'first'), genus=('genus', 'first'),
                       lab_rows=('Antibiotic', 'size'), lab_drugs=('Antibiotic', 'nunique'))
                  .reset_index()
                  .rename(columns={'Genome ID': 'genome_id'}))

    # Seeded shuffle, then rank within genus, then interleave: position k of
    # every genus comes before position k + 1 of any genus.
    genomes = genomes.sample(frac=1, random_state=SEED)
    genomes['rank'] = genomes.groupby('genus').cumcount()
    genomes = genomes.sort_values(['rank', 'genus'], kind='stable').drop(columns='rank')
    genomes.to_csv(OUT, index=False)

    print(f'[lab] {len(genomes):,} genomes with lab results, '
          f'{genomes["lab_rows"].sum():,} lab rows, written to {os.path.relpath(OUT)}')
    print(genomes['genus'].value_counts().head(12).to_string())


if __name__ == '__main__':
    main()
