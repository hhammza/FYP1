"""Train/test splitting strategies.

The default in backend/train_models.py is a random row-level split. With ~12
rows per genome that puts the same genome on both sides, so a model can score
well by recognising genomes rather than learning resistance. `grouped` is the
honest default here; `random` is kept so the difference can be measured.
"""
import numpy as np
from sklearn.model_selection import StratifiedGroupKFold, train_test_split


def make_split(df, strategy='grouped', test_size=0.2, seed=42,
               group_col='Genome ID', holdout_genus=None, verbose=True):
    """Return boolean masks (train, test) over df's rows."""
    y = df['target'].to_numpy()

    if strategy == 'random':
        idx = np.arange(len(df))
        tr, te = train_test_split(idx, test_size=test_size, stratify=y, random_state=seed)

    elif strategy == 'grouped':
        n_splits = max(2, int(round(1 / test_size)))
        splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
        tr, te = next(splitter.split(df, y, groups=df[group_col].to_numpy()))

    elif strategy == 'species_holdout':
        if not holdout_genus:
            raise ValueError('species_holdout needs holdout_genus')
        is_holdout = df['genus'].str.lower() == str(holdout_genus).lower()
        if not is_holdout.any():
            raise ValueError(f'no rows for genus {holdout_genus!r}')
        te = np.flatnonzero(is_holdout.to_numpy())
        tr = np.flatnonzero(~is_holdout.to_numpy())

    else:
        raise ValueError(f'unknown split strategy {strategy!r}')

    train_mask = np.zeros(len(df), dtype=bool)
    test_mask = np.zeros(len(df), dtype=bool)
    train_mask[tr] = True
    test_mask[te] = True

    if verbose:
        shared = len(set(df.loc[train_mask, group_col]) & set(df.loc[test_mask, group_col]))
        print(f'[split] {strategy}: train={train_mask.sum():,} test={test_mask.sum():,} '
              f'| genomes in both sides: {shared:,}')
    return train_mask, test_mask


def inner_folds(df, n_splits=5, seed=42, group_col='Genome ID'):
    """Grouped folds within the training set, for out-of-fold encoding."""
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(splitter.split(df, df['target'].to_numpy(), groups=df[group_col].to_numpy()))
