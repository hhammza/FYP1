"""Reliability diagram for a run: predicted risk against the observed
resistant share on its test rows, before and after calibration.

    python experiments/calibration_plot.py                          # the served forecaster
    python experiments/calibration_plot.py D3_forecaster_deploy_v7  # any run with calibration

Reads metrics.json (calibration.reliability_before / _after, 10 bins of
equal width), so it needs no data or model. Writes
experiments/results/figures/calibration_<run>.png.
"""
import argparse
import json
import os

import matplotlib
import lib  # noqa: E402,F401  (UTF-8 output on Windows; see lib/__init__.py)
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SERVED_META = os.path.join(ROOT, 'backend', 'trained_models', 'lgbm_metrics.json')


def served_run():
    with open(SERVED_META) as fh:
        return json.load(fh)['run_id']


def plot(run_id):
    with open(os.path.join(HERE, 'results', run_id, 'metrics.json')) as fh:
        m = json.load(fh)
    cal = m.get('calibration') or {}
    if 'reliability_after' not in cal:
        raise SystemExit(f'{run_id} has no calibration block (config "calibration" not set)')

    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.plot([0, 1], [0, 1], ls='--', c='grey', lw=1, label='perfect calibration')
    for key, label, colour in (
            ('reliability_before', f"raw scores (Brier {cal['test_brier_before']:.3f})", '#d95f02'),
            ('reliability_after', f"{cal['method']} calibrated (Brier {cal['test_brier_after']:.3f})", '#1b9e77')):
        pts = [p for p in cal[key] if p['n'] > 0]
        ax.plot([p['predicted'] for p in pts], [p['observed'] for p in pts],
                marker='o', c=colour, label=label)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('Predicted probability of resistance (bin mean)')
    ax.set_ylabel('Observed resistant share')
    ax.set_title(f"{run_id}\n{m['test']['n']:,} test rows, AUC {cal['test_auc_after']:.3f}", fontsize=10)
    ax.legend(loc='upper left', fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = os.path.join(HERE, 'results', 'figures', f'calibration_{run_id}.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=150)
    print(f'[calibration] wrote {os.path.relpath(out, ROOT)}')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('run_id', nargs='?', help='default: the run /forecast serves')
    plot(ap.parse_args().run_id or served_run())
