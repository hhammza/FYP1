"""Timeline ML model: forecast the resistant share of an organism to a drug, year by year.

The /timeline page used to show only a simulation (hand-set logistic curves).
This model is trained on real resistance trends instead: the BV-BRC laboratory
results with a collection year (Ali's genome metadata), grouped per genus and
antibiotic into yearly resistant percentages.

    python experiments/timeline_ml/timeline_model.py series    # build series.csv
    python experiments/timeline_ml/timeline_model.py train     # train, test, write results/TL_timeline_ml/
    python experiments/timeline_ml/timeline_model.py promote   # copy to backend/trained_models/timeline_ml/

The task: predict a year's resistant percentage from the years BEFORE it only
(the last values, the recent slope, the gap since the last value), the genus,
the antibiotic and its drug class. LightGBM predicts the change from the last
observed value. Tested on 2017 to 2022, after training on years up to 2016:
every test year is in the model's future. Compared with three baselines that
need no learning: the last value, the recent straight-line trend, and the
historical mean. Errors are in percentage points (pp); the 95% CI resamples
whole series. External check: the ECDC European surveillance series for
K. pneumoniae and carbapenems (Data/evolution_curves/), which the model never
saw.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS = os.path.dirname(HERE)
ROOT = os.path.dirname(EXPERIMENTS)
sys.path.insert(0, EXPERIMENTS)

SERIES_CSV = os.path.join(HERE, 'series.csv')
RUN_ID = 'TL_timeline_ml'
RUN_DIR = os.path.join(EXPERIMENTS, 'results', RUN_ID)
SERVED_DIR = os.path.join(ROOT, 'backend', 'trained_models', 'timeline_ml')
ECDC_CSV = os.path.join(ROOT, 'Data', 'evolution_curves', 'ecdc_kpneumoniae_carbapenems.csv')

FIRST_YEAR, LAST_YEAR = 2000, 2022
MIN_RESULTS = 20          # lab results needed for a year to count
TRAIN_UNTIL = 2016        # train on targets up to this year, test on the years after
VALID_FROM = 2014         # last training years used for early stopping
MIN_HISTORY = 2           # past points a target needs
SEED = 42

NUMERIC = ['lag1', 'lag2', 'lag3', 'gap1', 'slope3', 'mean_past', 'n_past', 'log_n1']
CATEGORICAL = ['genus', 'Antibiotic', 'drug_class']
FEATURES = NUMERIC + CATEGORICAL


# ── 1. The yearly series ─────────────────────────────────────────────────

def build_series(verbose=True):
    """Yearly resistant percentage per (genus, antibiotic) from the lab results
    with a collection year; a year counts with at least MIN_RESULTS results."""
    import run as pipeline
    from lib import data_prep
    df = pipeline.compact(data_prep.get_clean(verbose=False), verbose=False)
    df = df[df['label_source'] == 'lab']
    meta = pd.read_csv(os.path.join(ROOT, 'Data', 'genome_meta', 'genome_meta.csv'),
                       dtype={'genome_id': str}, usecols=['genome_id', 'year']).dropna()
    years = dict(zip(meta['genome_id'], meta['year'].astype(int)))
    df = df.assign(year=df['Genome ID'].astype(str).map(years)).dropna(subset=['year'])
    df = df[(df['year'] >= FIRST_YEAR) & (df['year'] <= LAST_YEAR)]
    g = (df.groupby(['genus', 'Antibiotic', 'drug_class', 'year'], observed=True)['target']
           .agg(resistant_pct='mean', n='size').reset_index())
    g = g[g['n'] >= MIN_RESULTS].copy()
    g['resistant_pct'] = (g['resistant_pct'] * 100).round(3)
    g['year'] = g['year'].astype(int)
    g = g.sort_values(['genus', 'Antibiotic', 'year']).reset_index(drop=True)
    for c in ['genus', 'Antibiotic', 'drug_class']:
        g[c] = g[c].astype(str)
    if verbose:
        n_series = g.groupby(['genus', 'Antibiotic']).ngroups
        print(f'[series] {len(df):,} lab results with a year {FIRST_YEAR}-{LAST_YEAR} -> '
              f'{len(g):,} year points in {n_series} series (>= {MIN_RESULTS} results each)')
    return g


def load_series():
    return pd.read_csv(SERIES_CSV)


# ── 2. Features: only the years before the target ────────────────────────

def history_features(years, pcts, ns, t):
    """Features for predicting year t from the points strictly before t."""
    past = [(y, p, n) for y, p, n in zip(years, pcts, ns) if y < t]
    if len(past) < 1:
        return None
    py = np.array([p[0] for p in past], float)
    pp = np.array([p[1] for p in past], float)
    last3y, last3p = py[-3:], pp[-3:]
    slope = float(np.polyfit(last3y, last3p, 1)[0]) if len(last3y) >= 2 else 0.0
    lag = lambda k: float(pp[-k]) if len(pp) >= k else np.nan
    return {
        'lag1': lag(1), 'lag2': lag(2), 'lag3': lag(3),
        'gap1': float(t - py[-1]),
        'slope3': slope,
        'mean_past': float(pp.mean()),
        'n_past': float(len(pp)),
        'log_n1': float(np.log1p(past[-1][2])),
    }


def make_rows(series):
    """One row per target point with at least MIN_HISTORY earlier points."""
    rows = []
    for (genus, ab), s in series.groupby(['genus', 'Antibiotic'], sort=False):
        ys, ps, ns = s['year'].tolist(), s['resistant_pct'].tolist(), s['n'].tolist()
        dc = s['drug_class'].iloc[0]
        for i in range(MIN_HISTORY, len(ys)):
            f = history_features(ys, ps, ns, ys[i])
            rows.append({**f, 'genus': genus, 'Antibiotic': ab, 'drug_class': dc,
                         'year': ys[i], 'target': ps[i], 'n': ns[i]})
    out = pd.DataFrame(rows)
    for c in CATEGORICAL:
        out[c] = out[c].astype('category')
    return out


def baselines(X):
    last = X['lag1'].to_numpy()
    trend = np.clip(X['lag1'] + X['slope3'] * X['gap1'], 0, 100).to_numpy()
    mean = X['mean_past'].to_numpy()
    return {'last value': last, 'linear trend': trend, 'historical mean': mean}


# ── 3. Train and test ────────────────────────────────────────────────────

PARAMS = {'objective': 'regression_l1', 'learning_rate': 0.03, 'num_leaves': 15,
          'min_data_in_leaf': 20, 'feature_fraction': 0.9, 'bagging_fraction': 0.9,
          'bagging_freq': 1, 'lambda_l2': 1.0, 'seed': SEED, 'deterministic': True,
          'num_threads': 1, 'verbose': -1}


def fit(train, rounds=None, valid=None):
    """LightGBM on the change from the last value, weighted by sqrt(n)."""
    import lightgbm as lgb
    def ds(d):
        return lgb.Dataset(d[FEATURES], d['target'] - d['lag1'], weight=np.sqrt(d['n']),
                           categorical_feature=CATEGORICAL, free_raw_data=False)
    if valid is not None:
        model = lgb.train(PARAMS, ds(train), num_boost_round=2000, valid_sets=[ds(valid)],
                          callbacks=[lgb.early_stopping(100, verbose=False)])
        return model, model.best_iteration
    return lgb.train(PARAMS, ds(train), num_boost_round=rounds), rounds


def predict(model, X):
    return np.clip(X['lag1'].to_numpy() + model.predict(X[FEATURES]), 0, 100)


def mae_ci(err, groups, n_boot=1000, seed=SEED):
    """MAE with a 95% CI that resamples whole series."""
    err = np.abs(np.asarray(err)); groups = np.asarray(groups)
    codes, idx = np.unique(groups, return_inverse=True)
    by = [err[idx == k] for k in range(len(codes))]
    rng = np.random.default_rng(seed)
    boots = [np.concatenate([by[k] for k in rng.integers(0, len(by), len(by))]).mean() for _ in range(n_boot)]
    return float(err.mean()), [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))]


def paired_gain(err_a, err_b, groups, n_boot=1000, seed=SEED):
    """MAE(b) - MAE(a), positive when a is better, with a series bootstrap CI."""
    a, b = np.abs(np.asarray(err_a)), np.abs(np.asarray(err_b))
    groups = np.asarray(groups)
    codes, idx = np.unique(groups, return_inverse=True)
    pos = [np.flatnonzero(idx == k) for k in range(len(codes))]
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        sel = np.concatenate([pos[k] for k in rng.integers(0, len(pos), len(pos))])
        diffs.append(b[sel].mean() - a[sel].mean())
    diffs = np.array(diffs)
    return {'gain_pp': float(b.mean() - a.mean()),
            'ci': [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
            'p_no_gain': float((diffs <= 0).mean())}


def ecdc_check(model, cats):
    """One-year-ahead forecasts on the ECDC K. pneumoniae / carbapenem series
    (per country, % resistant isolates), 2017 onwards, against the baselines.
    The model never saw these data; the series are read as genus Klebsiella,
    meropenem (a carbapenem)."""
    if not os.path.exists(ECDC_CSV):
        return None
    e = pd.read_csv(ECDC_CSV)
    e = e[pd.to_numeric(e['NumValue'], errors='coerce').notna()].copy()
    e['pct'] = pd.to_numeric(e['NumValue']); e['year'] = e['Time'].astype(int)
    rows = []
    for country, s in e.groupby('RegionCode'):
        s = s.sort_values('year')
        ys, ps = s['year'].tolist(), s['pct'].tolist()
        for i in range(MIN_HISTORY, len(ys)):
            if ys[i] <= TRAIN_UNTIL:
                continue
            f = history_features(ys, ps, [100] * len(ys), ys[i])
            rows.append({**f, 'genus': 'Klebsiella', 'Antibiotic': 'meropenem', 'drug_class': 'carbapenem',
                         'year': ys[i], 'target': ps[i], 'n': 100, 'series': country})
    X = pd.DataFrame(rows)
    for c in CATEGORICAL:
        X[c] = pd.Categorical(X[c], categories=cats[c])
    out = {'points': int(len(X)), 'countries': int(X['series'].nunique()),
           'years': [int(X['year'].min()), int(X['year'].max())]}
    out['model'] = mae_ci(predict(model, X) - X['target'], X['series'])
    for name, pred in baselines(X).items():
        out[name] = mae_ci(pred - X['target'], X['series'])
    return out


def train_and_test(series=None, verbose=True):
    series = load_series() if series is None else series
    rows = make_rows(series)
    rows['series'] = rows['genus'].astype(str) + ' | ' + rows['Antibiotic'].astype(str)
    train = rows[rows['year'] <= TRAIN_UNTIL]
    test = rows[rows['year'] > TRAIN_UNTIL]
    # rounds chosen on the last training years, then refit on all training years
    _, rounds = fit(train[train['year'] < VALID_FROM], valid=train[train['year'] >= VALID_FROM])
    rounds = max(rounds, 50)
    model, _ = fit(train, rounds=rounds)

    pred = predict(model, test)
    result = {'model': mae_ci(pred - test['target'], test['series'])}
    base = baselines(test)
    for name, p in base.items():
        result[name] = mae_ci(p - test['target'], test['series'])
    gains = {name: paired_gain(pred - test['target'], p - test['target'], test['series'])
             for name, p in base.items()}
    abs_err = np.abs(pred - test['target'].to_numpy())
    within = {k: float((abs_err <= k).mean()) for k in (5, 10)}
    cats = {c: list(train[c].cat.categories) for c in CATEGORICAL}
    ecdc = ecdc_check(model, cats)

    metrics = {
        'id': RUN_ID,
        'description': 'Timeline ML model: next-year resistant share per genus and antibiotic from earlier years '
                       '(BV-BRC lab results with a collection year); trained on years up to '
                       f'{TRAIN_UNTIL}, tested on {TRAIN_UNTIL + 1}-{LAST_YEAR}',
        'data': {'series': int(series.groupby(['genus', 'Antibiotic']).ngroups), 'year_points': int(len(series)),
                 'lab_results': int(series['n'].sum()), 'min_results_per_year': MIN_RESULTS,
                 'train_targets': int(len(train)), 'test_targets': int(len(test)),
                 'test_series': int(test['series'].nunique()), 'train_until': TRAIN_UNTIL},
        'model_info': {'algorithm': 'LightGBM regression (L1) on the change from the last value',
                       'rounds': int(rounds), 'features': FEATURES, 'params': PARAMS},
        'test_mae_pp': result,
        'gain_over_baselines_pp': gains,
        'share_within_pp': within,
        'interval_abs_error_pp': {'q80': float(np.quantile(abs_err, 0.8)), 'q95': float(np.quantile(abs_err, 0.95))},
        'ecdc_check': ecdc,
        'feature_importance': dict(zip(FEATURES, [int(v) for v in model.feature_importance('gain')])),
    }
    if verbose:
        print(f"[timeline] {metrics['data']['series']} series, train {len(train):,} targets (<= {TRAIN_UNTIL}), "
              f"test {len(test):,} targets ({test['series'].nunique()} series), {rounds} rounds")
        for k, (m, ci) in result.items():
            print(f'  MAE {k:16s} {m:6.2f} pp  [{ci[0]:.2f}, {ci[1]:.2f}]')
        for k, g in gains.items():
            print(f"  model better than {k:16s} by {g['gain_pp']:+.2f} pp [{g['ci'][0]:+.2f}, {g['ci'][1]:+.2f}], "
                  f"share of resamples with no gain {g['p_no_gain']:.3f}")
        if ecdc:
            print(f"  ECDC check ({ecdc['points']} points, {ecdc['countries']} countries): "
                  + ', '.join(f"{k} {ecdc[k][0]:.2f}" for k in ['model'] + list(base)))
    return model, metrics, test.assign(pred=pred)


def save_run(model, metrics, test):
    os.makedirs(os.path.join(RUN_DIR, 'model'), exist_ok=True)
    model.save_model(os.path.join(RUN_DIR, 'model', 'model.txt'))
    with open(os.path.join(RUN_DIR, 'metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump(metrics, fh, indent=2)
    test[['genus', 'Antibiotic', 'year', 'target', 'pred', 'n']].to_csv(
        os.path.join(RUN_DIR, 'predictions.csv'), index=False)
    print(f'[timeline] wrote {os.path.relpath(RUN_DIR, ROOT)}')


# ── 4. Forecast for the website (the same functions the backend copies) ──

def forecast(model, history, genus, antibiotic, drug_class, cats, years_ahead=5, q80=None):
    """Recursive forecast: each predicted year is fed back as history."""
    ys = [int(h['year']) for h in history]
    ps = [float(h['resistant_pct']) for h in history]
    ns = [int(h['n']) for h in history]
    out = []
    for h in range(1, years_ahead + 1):
        t = ys[-1] + 1
        f = history_features(ys, ps, ns, t)
        X = pd.DataFrame([{**f, 'genus': genus, 'Antibiotic': antibiotic, 'drug_class': drug_class}])
        for c in CATEGORICAL:
            X[c] = pd.Categorical(X[c], categories=cats[c])
        p = float(predict(model, X)[0])
        band = (q80 or 0) * np.sqrt(h)
        out.append({'year': t, 'resistant_pct': round(p, 1),
                    'lo': round(max(0.0, p - band), 1), 'hi': round(min(100.0, p + band), 1)})
        ys.append(t); ps.append(p); ns.append(ns[-1])
    return out


def promote():
    """Train on every year (the served model) and write what the backend needs:
    the booster, the categories, the series' history and the held-out metrics."""
    series = load_series()
    with open(os.path.join(RUN_DIR, 'metrics.json'), encoding='utf-8') as fh:
        metrics = json.load(fh)
    rows = make_rows(series)
    model, _ = fit(rows, rounds=metrics['model_info']['rounds'])
    os.makedirs(SERVED_DIR, exist_ok=True)
    model.save_model(os.path.join(SERVED_DIR, 'model.txt'))
    history = {}
    for (genus, ab), s in series.groupby(['genus', 'Antibiotic']):
        history.setdefault(genus, {})[ab] = {
            'drug_class': s['drug_class'].iloc[0],
            'points': [{'year': int(r.year), 'resistant_pct': float(r.resistant_pct), 'n': int(r.n)}
                       for r in s.itertuples()]}
    meta = {'run_id': RUN_ID, 'features': FEATURES, 'categorical': CATEGORICAL,
            'categories': {c: list(rows[c].cat.categories) for c in CATEGORICAL},
            'q80_abs_error_pp': metrics['interval_abs_error_pp']['q80'], 'min_history': MIN_HISTORY,
            'label': 'ML model trained on BV-BRC laboratory results',
            'history': history}
    with open(os.path.join(SERVED_DIR, 'timeline_ml.json'), 'w', encoding='utf-8') as fh:
        json.dump(meta, fh)
    with open(os.path.join(SERVED_DIR, 'timeline_metrics.json'), 'w', encoding='utf-8') as fh:
        json.dump({k: metrics[k] for k in ['id', 'description', 'data', 'model_info', 'test_mae_pp',
                                           'gain_over_baselines_pp', 'share_within_pp',
                                           'interval_abs_error_pp', 'ecdc_check']}, fh, indent=2)
    print(f'[timeline] promoted to {os.path.relpath(SERVED_DIR, ROOT)} '
          f'({sum(len(v) for v in history.values())} series)')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'train'
    if cmd == 'series':
        build_series().to_csv(SERIES_CSV, index=False)
        print(f'[series] wrote {os.path.relpath(SERIES_CSV, ROOT)}')
    elif cmd == 'train':
        save_run(*train_and_test())
    elif cmd == 'promote':
        promote()
    else:
        sys.exit('usage: timeline_model.py series | train | promote')


if __name__ == '__main__':
    import lib  # noqa: F401  (UTF-8 output on Windows)
    main()
