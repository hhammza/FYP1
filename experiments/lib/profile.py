"""Describe a training set, so models trained on different data can be compared."""


def profile(df, min_genus_share=0.001):
    """Summary of a cleaned frame.

    Expects the columns data_prep.clean() produces: Genome ID, Taxon ID,
    Antibiotic, genus, target, is_lab_confirmed and, optionally, has_mic.
    """
    n = len(df)
    genus = df['genus'].value_counts()
    keep = genus[genus / n >= min_genus_share]
    out = {
        'rows': int(n),
        'genomes': int(df['Genome ID'].nunique()),
        'taxa': int(df['Taxon ID'].nunique()),
        'antibiotics': int(df['Antibiotic'].nunique()),
        'genera': int(genus.size),
        'prevalence': round(float(df['target'].mean()), 4),
        'lab_share': round(float(df['is_lab_confirmed'].mean()), 4),
        'genus_rows': {str(k): int(v) for k, v in keep.items()},
    }
    if len(keep) < genus.size:
        out['genus_rows']['Other'] = int(genus.drop(keep.index).sum())
    if 'has_mic' in df:
        out['mic_share'] = round(float(df['has_mic'].mean()), 4)
    return out
