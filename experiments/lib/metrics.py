"""Evaluation metrics.

Pooled AUC alone hides too much here: the classes are imbalanced, the UI shows
the probability as a number users are meant to read, and a missed resistance
call is far costlier than a false alarm. So every run reports AUPRC, the
clinical error rates, and a calibration score alongside AUC.

Very major error (VME) = a truly Resistant isolate called Susceptible.
Major error (ME)       = a truly Susceptible isolate called Resistant.
FDA guidance for susceptibility devices asks for VME <= 1.5-3% and ME <= 3%.
"""
import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, confusion_matrix, f1_score,
                             precision_recall_curve, roc_auc_score)


def evaluate(y_true, y_score, threshold=0.5):
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    y_pred = (y_score >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    both = len(np.unique(y_true)) > 1

    return {
        'n': int(len(y_true)),
        'prevalence': float(y_true.mean()),
        'threshold': float(threshold),
        'auc_roc': float(roc_auc_score(y_true, y_score)) if both else float('nan'),
        'auc_pr': float(average_precision_score(y_true, y_score)) if both else float('nan'),
        'f1': float(f1_score(y_true, y_pred, zero_division=0)),
        'accuracy': float((tp + tn) / len(y_true)) if len(y_true) else float('nan'),
        'balanced_acc': float(balanced_accuracy_score(y_true, y_pred)),
        'brier': float(brier_score_loss(y_true, y_score)),
        'sensitivity': float(tp / (tp + fn)) if (tp + fn) else float('nan'),
        'specificity': float(tn / (tn + fp)) if (tn + fp) else float('nan'),
        'very_major_error': float(fn / (tp + fn)) if (tp + fn) else float('nan'),
        'major_error': float(fp / (tn + fp)) if (tn + fp) else float('nan'),
        'tp': int(tp), 'fp': int(fp), 'tn': int(tn), 'fn': int(fn),
    }


def fit_calibrator(y_true, y_score, method='isotonic'):
    """Map raw scores to calibrated probabilities, as plain numbers.

    Returned as a dict rather than a fitted estimator so the served model can
    apply it with numpy alone (no pickled scikit-learn object to go stale).
    Both methods are monotone, so they never reorder predictions; Platt keeps
    AUC exactly, isotonic can merge near-equal scores into ties.
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    if method == 'isotonic':
        from sklearn.isotonic import IsotonicRegression
        iso = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds='clip').fit(y_score, y_true)
        return {'method': 'isotonic',
                'x': [float(v) for v in iso.X_thresholds_],
                'y': [float(v) for v in iso.y_thresholds_]}
    if method == 'platt':
        from sklearn.linear_model import LogisticRegression
        eps = 1e-6
        logit = np.log(np.clip(y_score, eps, 1 - eps) / np.clip(1 - y_score, eps, 1 - eps))
        lr = LogisticRegression(C=1e6).fit(logit.reshape(-1, 1), y_true)
        return {'method': 'platt', 'a': float(lr.coef_[0][0]), 'b': float(lr.intercept_[0])}
    raise ValueError(f'unknown calibration method {method!r}')


def apply_calibrator(cal, y_score):
    """Apply a calibrator from fit_calibrator(); None returns scores unchanged."""
    y_score = np.asarray(y_score, dtype=float)
    if not cal:
        return y_score
    if cal['method'] == 'isotonic':
        return np.interp(y_score, cal['x'], cal['y'])
    if cal['method'] == 'platt':
        eps = 1e-6
        logit = np.log(np.clip(y_score, eps, 1 - eps) / np.clip(1 - y_score, eps, 1 - eps))
        return 1.0 / (1.0 + np.exp(-(cal['a'] * logit + cal['b'])))
    raise ValueError(f'unknown calibration method {cal["method"]!r}')


def calibration_curve_points(y_true, y_score, n_bins=10):
    """Reliability diagram: mean predicted vs observed rate per score decile."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    edges = np.unique(np.quantile(y_score, np.linspace(0, 1, n_bins + 1)))
    bins = np.clip(np.searchsorted(edges, y_score, side='right') - 1, 0, len(edges) - 2)
    out = []
    for b in range(len(edges) - 1):
        m = bins == b
        if m.any():
            out.append({'predicted': round(float(y_score[m].mean()), 4),
                        'observed': round(float(y_true[m].mean()), 4),
                        'n': int(m.sum())})
    return out


def pick_threshold(y_true, y_score, strategy='fixed', fixed=0.5, vme_budget=0.03):
    """Choose a decision threshold on validation data, never on test."""
    if strategy == 'fixed':
        return float(fixed)

    if strategy == 'maximize_f1':
        prec, rec, thr = precision_recall_curve(y_true, y_score)
        f1 = np.divide(2 * prec * rec, prec + rec,
                       out=np.zeros_like(prec), where=(prec + rec) > 0)
        return float(thr[max(0, int(np.argmax(f1)) - 1)]) if len(thr) else float(fixed)

    if strategy == 'vme_constrained':
        # Highest threshold whose very-major-error rate still fits the budget.
        # VME rises with the threshold, so walk down until it fits.
        for t in np.linspace(0.95, 0.05, 91):
            pred = (y_score >= t).astype(int)
            fn = int(((y_true == 1) & (pred == 0)).sum())
            pos = int((y_true == 1).sum())
            if pos and fn / pos <= vme_budget:
                return float(t)
        return 0.05

    raise ValueError(f'unknown threshold strategy {strategy!r}')


def per_group(y_true, y_score, groups, threshold=0.5, min_n=30):
    """Metrics per antibiotic (or any grouping), worst AUC first."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    groups = np.asarray(groups)
    rows = []
    for g in np.unique(groups):
        m = groups == g
        if m.sum() < min_n or len(np.unique(y_true[m])) < 2:
            continue
        r = evaluate(y_true[m], y_score[m], threshold)
        r['group'] = str(g)
        rows.append(r)
    return sorted(rows, key=lambda r: r['auc_roc'])


def bootstrap_ci(y_true, y_score, groups, metric=roc_auc_score, n_boot=200, seed=42):
    """Percentile CI, resampling genomes rather than rows.

    Rows from one genome are correlated, so resampling rows would give a
    misleadingly tight interval.
    """
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score)
    groups = np.asarray(groups)

    order = np.argsort(groups, kind='stable')
    sorted_groups = groups[order]
    uniq, starts = np.unique(sorted_groups, return_index=True)
    bounds = np.append(starts, len(sorted_groups))
    blocks = [order[bounds[i]:bounds[i + 1]] for i in range(len(uniq))]

    rng = np.random.default_rng(seed)
    stats = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(blocks), size=len(blocks))
        idx = np.concatenate([blocks[i] for i in pick])
        if len(np.unique(y_true[idx])) < 2:
            continue
        stats.append(metric(y_true[idx], y_score[idx]))
    if not stats:
        return (float('nan'), float('nan'))
    return float(np.percentile(stats, 2.5)), float(np.percentile(stats, 97.5))
