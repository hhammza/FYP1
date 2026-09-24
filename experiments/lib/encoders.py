"""Target (mean) encoding of the resistance-rate features.

Three modes, and the difference between them is the single biggest measurement
question in this project:

  none   no rate features at all, shows what the model learns without them
  leaky  fitted on the full dataset before splitting, reproducing
         backend/train_models.py:186-209. Test rows carry a feature computed
         partly from their own label, which inflates every metric.
  oof    fitted out-of-fold on the training set only. Train rows get a value
         computed without their own label; test rows use the full-train map.

`oof` is correct. `leaky` exists so the cost of the bug can be quantified.
"""
import numpy as np
import pandas as pd

RATE_FEATURES = ['ab_resistance_rate', 'taxon_ab_resistance_rate', 'genus_ab_resistance_rate']

SPECS = [
    (['Antibiotic'], 'ab_resistance_rate', 1),
    (['Taxon ID', 'Antibiotic'], 'taxon_ab_resistance_rate', 3),
    (['genus', 'Antibiotic'], 'genus_ab_resistance_rate', 3),
]


def _rate_map(frame, keys, min_count):
    agg = frame.groupby(keys, observed=True)['target'].agg(['sum', 'count'])
    agg = agg[agg['count'] >= min_count]
    return (agg['sum'] / agg['count']).rename('rate')


def _apply_map(frame, keys, rate, fallback):
    joined = frame[keys].join(rate, on=keys)['rate']
    return joined.fillna(fallback).to_numpy()


def add_rate_features(df, train_mask, mode='oof', folds=None, verbose=True):
    """Attach the three rate features, fitted according to `mode`."""
    out = df.copy()
    if mode == 'none':
        return out, []

    global_mean = float(df.loc[train_mask, 'target'].mean())
    train_idx = np.flatnonzero(train_mask)

    for keys, name, min_count in SPECS:
        if mode == 'leaky':
            # Fitted on everything, including the test rows. This is the bug.
            rate = _rate_map(df, keys, min_count)
            out[name] = _apply_map(df, keys, rate, global_mean)
            continue

        if mode != 'oof':
            raise ValueError(f'unknown encoding mode {mode!r}')

        values = np.full(len(df), np.nan)

        # Training rows: encoded from the other folds only.
        train_frame = df.loc[train_mask]
        for fit_pos, enc_pos in folds:
            rate = _rate_map(train_frame.iloc[fit_pos], keys, min_count)
            rows = train_frame.iloc[enc_pos]
            values[train_idx[enc_pos]] = _apply_map(rows, keys, rate, global_mean)

        # Test rows: encoded from the whole training set.
        full_rate = _rate_map(train_frame, keys, min_count)
        test_idx = np.flatnonzero(~train_mask)
        values[test_idx] = _apply_map(df.loc[~train_mask], keys, full_rate, global_mean)

        out[name] = np.where(np.isnan(values), global_mean, values)

    # Narrower groupings fall back to the broader rate rather than the global
    # mean, mirroring what the served predictor does at inference time.
    out['taxon_ab_resistance_rate'] = out['taxon_ab_resistance_rate'].where(
        out['taxon_ab_resistance_rate'] != global_mean, out['ab_resistance_rate'])
    out['genus_ab_resistance_rate'] = out['genus_ab_resistance_rate'].where(
        out['genus_ab_resistance_rate'] != global_mean, out['ab_resistance_rate'])

    if verbose:
        print(f'[encode] mode={mode} global_mean={global_mean:.4f}')
    return out, RATE_FEATURES
