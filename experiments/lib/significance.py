"""Significance tests for comparing two models on the same test rows.

DeLong's test compares two AUCs from correlated scores (same rows, same
labels); McNemar's test compares two sets of yes/no calls at each model's own
threshold. Both treat rows as independent. Here rows cluster by genome (about
nine drugs per genome), so the paired genome bootstrap is reported beside them
as the check that respects that clustering: when the two disagree, quote the
bootstrap.

DeLong: DeLong, DeLong & Clarke-Pearson (1988), with the fast midrank
algorithm of Sun & Xu (2014). McNemar: exact binomial for few discordant
pairs, else chi-square with continuity correction.
"""
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score


def _midrank(x):
    return stats.rankdata(x, method='average')


def delong(y_true, score_a, score_b):
    """Paired DeLong test. Returns auc_a, auc_b, diff (a - b), se, z, p and the
    95% CI of the difference."""
    y = np.asarray(y_true).astype(int)
    pos, neg = y == 1, y == 0
    m, n = int(pos.sum()), int(neg.sum())
    if m == 0 or n == 0:
        raise ValueError('DeLong needs both classes')
    scores = np.vstack([np.asarray(score_a, float), np.asarray(score_b, float)])
    aucs, v10, v01 = [], [], []
    for s in scores:
        x, yy = s[pos], s[neg]
        tx, ty, tz = _midrank(x), _midrank(yy), _midrank(np.concatenate([x, yy]))
        aucs.append((tz[:m].sum() - m * (m + 1) / 2) / (m * n))
        v10.append((tz[:m] - tx) / n)          # placement of each positive
        v01.append(1 - (tz[m:] - ty) / m)      # placement of each negative
    s10, s01 = np.cov(np.vstack(v10)), np.cov(np.vstack(v01))
    cov = s10 / m + s01 / n
    diff = aucs[0] - aucs[1]
    var = cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]
    se = float(np.sqrt(max(var, 0.0)))
    z = diff / se if se > 0 else float('inf') if diff else 0.0
    p = float(2 * stats.norm.sf(abs(z)))
    return {'auc_a': float(aucs[0]), 'auc_b': float(aucs[1]), 'diff': float(diff),
            'se': se, 'z': float(z), 'p': p,
            'ci': [float(diff - 1.96 * se), float(diff + 1.96 * se)]}


def mcnemar(y_true, pred_a, pred_b):
    """McNemar's test on correct/incorrect calls. b = only A right, c = only
    B right."""
    y = np.asarray(y_true).astype(int)
    ra = np.asarray(pred_a).astype(int) == y
    rb = np.asarray(pred_b).astype(int) == y
    b, c = int((ra & ~rb).sum()), int((~ra & rb).sum())
    if b + c == 0:
        return {'only_a_right': b, 'only_b_right': c, 'statistic': 0.0, 'p': 1.0, 'method': 'none'}
    if b + c < 25:
        p = float(min(1.0, 2 * stats.binom.cdf(min(b, c), b + c, 0.5)))
        return {'only_a_right': b, 'only_b_right': c, 'statistic': float(min(b, c)),
                'p': p, 'method': 'exact'}
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    return {'only_a_right': b, 'only_b_right': c, 'statistic': float(chi2),
            'p': float(stats.chi2.sf(chi2, 1)), 'method': 'chi2_cc'}


def paired_bootstrap(y_true, score_a, score_b, groups, n_boot=1000, seed=0):
    """AUC difference (a - b) with a 95% CI from resampling whole groups
    (genomes), so a genome's drugs stay together. p_no_gain is the share of
    resamples where A is not ahead."""
    y = np.asarray(y_true).astype(int)
    a, b = np.asarray(score_a, float), np.asarray(score_b, float)
    codes = np.unique(np.asarray(groups).astype(str), return_inverse=True)[1]
    n_groups = codes.max() + 1
    order = np.argsort(codes, kind='stable')
    starts = np.searchsorted(codes[order], np.arange(n_groups + 1))
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        pick = rng.integers(0, n_groups, n_groups)
        idx = np.concatenate([order[starts[g]:starts[g + 1]] for g in pick])
        yy = y[idx]
        if yy.min() == yy.max():
            continue
        diffs.append(roc_auc_score(yy, a[idx]) - roc_auc_score(yy, b[idx]))
    diffs = np.asarray(diffs)
    return {'diff': float(roc_auc_score(y, a) - roc_auc_score(y, b)),
            'ci': [float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
            'p_no_gain': float((diffs <= 0).mean()), 'n_boot': int(len(diffs))}
