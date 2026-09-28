"""
Calibrate the mutation timeline's curve against published resistance data (T3.1).

The timeline (backend/ml_models/mutation_timeline.py) draws, per drug,

    R(t) = r0 + (peak - r0) / (1 + exp(-k (t - midpoint)))

with hand-set speed (k = 2.5 x speed per week) and peak, and a midpoint of
0.45 x the weeks asked. This fits the same curve to two kinds of published
data and compares the fitted shape with the hand-set one. The two are kept
apart because they measure different things:

  lab           Maltas, Huynh & Wood 2025, PLOS Biology, doi:10.1371/journal.pbio.3002970,
                S1 Data sheet Fig1B: E. faecalis V583 evolved under ciprofloxacin (CIP),
                ceftriaxone (CRO), doxycycline (DOX), daptomycin (DAP) or linezolid (LZD),
                4 replicate populations each, IC50 at days 2, 4, 6, 8 as log2 fold change
                over the ancestor (day 0 = 0 by definition). Fitted with r0 = 0 in log2
                units: how resistant one population becomes, over days.
  surveillance  ECDC Surveillance Atlas (EARS-Net), percentage of invasive Klebsiella
                pneumoniae isolates resistant to carbapenems, per country and year,
                2005-2024. Fitted in the timeline's own unit, the resistant fraction, for
                countries where resistance rose: what share of patients' bacteria are
                resistant, over years.

    python experiments/evolution/calibrate.py

Reads Data/evolution_curves/ (sources in Data/evolution_curves/sources.csv).
Writes into experiments/evolution/results/:

    calibration.csv                one row per fitted curve: parameters with 95% CI, RMSE
    calibration_summary.md         the tables and what they mean for the timeline
    figures/calibration_lab.png    replicate data, means and fit per drug
    figures/calibration_surveillance.png   yearly data and fit per country

and backend/trained_models/timeline_calibration.json, the `calibration` object
/api/timeline/ returns (format in progress/formats/README.md section 4).

ECDC data: "Dataset provided by ECDC based on data provided by public health
authorities, scientific institutes or health care providers in the relevant
reporting countries and/or by WHO" (CC BY 4.0; fitted curves are our adaptation).
"""
import math
import os
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import OptimizeWarning, curve_fit

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ml_models.mutation_timeline import ANTIBIOTIC_MUTATION_PROFILES  # noqa: E402

sys.path.insert(0, HERE)
from sensitivity import FIGURES, GRID, INK, INK_2, RESULTS, SERIES, SURFACE, style  # noqa: E402

CURVES = os.path.join(ROOT, 'Data', 'evolution_curves')
LAB_XLSX = os.path.join(CURVES, 'maltas2025_pbio.3002970_S1_Data.xlsx')
ECDC_CSV = os.path.join(CURVES, 'ecdc_kpneumoniae_carbapenems.csv')

LAB_DRUGS = {'CIP': 'ciprofloxacin', 'CRO': 'ceftriaxone', 'DOX': 'doxycycline',
             'DAP': 'daptomycin', 'LZD': 'linezolid'}
# Timeline profile each curve is compared with (None: the timeline has no profile)
PROFILE_FOR = {'ciprofloxacin': 'ciprofloxacin', 'ceftriaxone': 'cefotaxime',  # same class
               'doxycycline': 'tetracycline', 'daptomycin': None, 'linezolid': None,
               'carbapenems': 'imipenem'}
MIN_YEARS = 12          # surveillance: fit a country with at least this many years
MIN_RISE = 0.10         # ... whose resistant share rose by at least 10 points
LN81 = math.log(81)     # 10% to 90% of a logistic's rise takes ln(81) / k
LN9 = math.log(9)       # 90% of the rise is reached ln(9) / k after the midpoint
SERVED = os.path.join(ROOT, 'backend', 'trained_models', 'timeline_calibration.json')


def logistic(t, r0, peak, k, mid):
    return r0 + (peak - r0) / (1 + np.exp(-k * (t - mid)))


def fit(t, y, fixed_r0=None, bounds=None, p0=None):
    """Fit the timeline's curve; returns params, 95% half-widths, RMSE, R^2."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    if fixed_r0 is not None:
        f = lambda t, peak, k, mid: logistic(t, fixed_r0, peak, k, mid)  # noqa: E731
    else:
        f = logistic
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', OptimizeWarning)
        popt, pcov = curve_fit(f, t, y, p0=p0, bounds=bounds, maxfev=20000)
    half = 1.96 * np.sqrt(np.clip(np.diag(pcov), 0, None))
    half = np.where(np.isfinite(half), half, np.nan)
    resid = y - f(t, *popt)
    rmse = float(np.sqrt(np.mean(resid ** 2)))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1 - float(np.sum(resid ** 2)) / ss_tot if ss_tot > 0 else float('nan')
    if fixed_r0 is not None:
        popt, half = np.r_[fixed_r0, popt], np.r_[0.0, half]
    return popt, half, rmse, r2


def load_lab():
    raw = pd.read_excel(LAB_XLSX, sheet_name='Fig1B', header=None)
    # Column names from the sheet's own header row (its order is CIP, DAP, DOX, CRO, LZD)
    header = [str(v).strip() for v in raw.iloc[1, 2:7]]
    assert sorted(header) == sorted(LAB_DRUGS), header
    body = raw.iloc[2:, :7].dropna(subset=[0])
    body.columns = ['population', 'day', *header]
    body['selected'] = body['population'].str.split().str[0]
    rows = []
    for code in LAB_DRUGS:
        own = body[body.selected == code]
        for pop in own.population.unique():
            rows.append({'drug': code, 'population': pop, 'day': 0, 'log2_fold': 0.0})  # the ancestor
        rows += [{'drug': code, 'population': r.population, 'day': int(r.day), 'log2_fold': float(r[code])}
                 for _, r in own.iterrows()]
    return pd.DataFrame(rows)


def fit_lab(lab):
    out = []
    for code, name in LAB_DRUGS.items():
        d = lab[lab.drug == code]
        top = d.log2_fold.max()
        p, h, rmse, r2 = fit(d.day, d.log2_fold, fixed_r0=0.0,
                             bounds=([0, 0.05, -5], [top * 1.5, 20, 10]), p0=[top, 1.0, 2.0])
        out.append({'source': 'lab', 'curve': name, 'organism': 'Enterococcus faecalis V583',
                    'unit': 'log2 IC50 fold change', 'time_unit': 'day', 'points': len(d),
                    'r0': p[0], 'peak': p[1], 'peak_ci': h[1], 'k': p[2], 'k_ci': h[2],
                    'midpoint': p[3], 'midpoint_ci': h[3], 'rise_10_90': LN81 / p[2],
                    'rmse': rmse, 'rmse_share_of_peak': rmse / p[1], 'r2': r2})
    return out


def load_ecdc():
    df = pd.read_csv(ECDC_CSV, na_values=['-'])
    df = df.dropna(subset=['NumValue'])
    df['share'] = df['NumValue'] / 100
    return df[['Time', 'RegionCode', 'RegionName', 'share']].rename(columns={'Time': 'year'})


def fit_ecdc(ecdc):
    out, kept = [], []
    for (code, country), d in ecdc.groupby(['RegionCode', 'RegionName']):
        d = d.sort_values('year')
        if len(d) < MIN_YEARS or d.share.max() - d.share.min() < MIN_RISE:
            continue
        t = d.year - d.year.min()
        try:
            p, h, rmse, r2 = fit(t, d.share, bounds=([0, 0, 0.05, -10], [1, 1, 10, 40]),
                                 p0=[d.share.iloc[0], d.share.max(), 0.5, t.median()])
        except RuntimeError:
            continue
        kept.append(code)
        out.append({'source': 'surveillance', 'curve': f'carbapenems, {country}',
                    'organism': 'Klebsiella pneumoniae', 'unit': 'fraction resistant',
                    'time_unit': 'year', 'points': len(d), 'first_year': int(d.year.min()),
                    'r0': p[0], 'peak': p[1], 'peak_ci': h[1], 'k': p[2], 'k_ci': h[2],
                    'midpoint': p[3] + d.year.min(), 'midpoint_ci': h[3], 'rise_10_90': LN81 / p[2],
                    'rmse': rmse, 'rmse_share_of_peak': rmse / p[1] if p[1] else np.nan, 'r2': r2,
                    # Still rising at the last year: the plateau is extrapolated, not measured
                    'plateau_reached': bool(p[3] + LN9 / p[2] <= t.max())})
    return out, kept


def timeline_reference(drug):
    """The hand-set profile's shape, in its own units (weeks, fraction)."""
    p = ANTIBIOTIC_MUTATION_PROFILES[drug]
    k = 2.5 * p['speed']
    return {'speed': p['speed'], 'peak': p['peak'], 'k_per_week': k, 'rise_10_90_weeks': LN81 / k}


def lab_shapes(lab):
    """One sentence per shape, from the fitted midpoint and rise time."""
    early = lab[lab.midpoint < 2].curve.tolist()                       # before the first measurement
    sharp = lab[(lab.midpoint >= 2) & (lab.rise_10_90 < 2)].curve.tolist()
    slow = lab[(lab.midpoint >= 2) & (lab.rise_10_90 >= 2)].curve.tolist()
    parts = []
    verb = lambda names, one, many: one if len(names) == 1 else many  # noqa: E731
    if early:
        parts.append(f'{", ".join(early)} {verb(early, "rises", "rise")} mostly before day 2, the first '
                     f'measurement, so {verb(early, "its", "their")} midpoint rests on day 0 and day 2 alone')
    if sharp:
        parts.append(f'{", ".join(sharp)} {verb(sharp, "jumps", "jump")} between two measurements')
    if slow:
        parts.append(f'{", ".join(slow)} {verb(slow, "rises", "rise")} gradually over the week')
    return '; '.join(parts).capitalize() + '.'


def ci(v, h):
    return f'{v:.2f} ± {h:.2f}' if np.isfinite(h) else f'{v:.2f} (CI undefined)'


def write_summary(res, path):
    lab = res[res.source == 'lab']
    sur = res[res.source == 'surveillance'].sort_values('peak', ascending=False)
    done = sur[sur.plateau_reached.astype(bool)]
    rising = sur[~sur.plateau_reached.astype(bool)]
    imi = timeline_reference('imipenem')
    lines = [
        '# Timeline calibration against published curves', '',
        'Written by `calibrate.py`. The timeline\'s logistic curve fitted to published resistance data; '
        'parameters with 95% confidence intervals. Rise time = how long the curve takes from 10% to 90% of its '
        'rise (ln 81 / k), which compares shapes across time units.', '',
        '## Summary', '',
        f'- **{len(res)} curves fitted**: {len(lab)} lab (days) and {len(sur)} surveillance (years). '
        f'Median R² {res.r2.median():.2f}; the logistic shape fits both kinds of data.',
        f'- **Lab:** resistance to the selecting drug rises within days; rise times {lab.rise_10_90.min():.1f} to '
        f'{lab.rise_10_90.max():.1f} days. ' + lab_shapes(lab),
        f'- **Surveillance:** in the {len(done)} countries where carbapenem-resistant *K. pneumoniae* has levelled '
        f'off, it did so at {done.peak.min():.0%} to {done.peak.max():.0%} (median {done.peak.median():.0%}), '
        f'rising over a median {done.rise_10_90.median():.1f} years. In {len(rising)} more '
        f'({", ".join(c.split(", ", 1)[1] for c in rising.curve)}) it is still rising in the last year, so their '
        f'plateau is extrapolated and left out of these figures. The timeline\'s hand-set imipenem peak is '
        f'{imi["peak"]:.0%}.',
        '- **For the timeline:** the peak is the parameter the data can set, and it varies by setting '
        '(country) far more than the ±30% the sensitivity analysis tried. The time scale cannot be carried over: '
        'lab curves run in days and surveillance in years, while the timeline shows weeks. So the timeline\'s '
        'weeks remain an illustration, which the page should say, and its midpoint should be a per-drug value '
        'rather than 0.45 x the weeks asked (see `sensitivity_summary.md`).', '',
        '## Lab curves (Maltas, Huynh & Wood 2025)', '',
        '*E. faecalis* V583, 4 replicate populations per drug, resistance to the drug each was evolved in, '
        'log2 IC50 fold change over the ancestor. r0 fixed at 0 (the ancestor).', '',
        '| Drug | Points | Plateau (log2) | k per day | Midpoint (day) | Rise 10 to 90% (days) | RMSE (log2) | R² | Timeline profile |',
        '|---|---|---|---|---|---|---|---|---|',
    ]
    for r in lab.itertuples():
        prof = PROFILE_FOR.get(r.curve)
        ref = (f'{prof}: rise {timeline_reference(prof)["rise_10_90_weeks"]:.1f} weeks, peak '
               f'{timeline_reference(prof)["peak"]:.0%}' if prof else 'none')
        lines.append(f'| {r.curve} | {r.points} | {ci(r.peak, r.peak_ci)} | {ci(r.k, r.k_ci)} | '
                     f'{ci(r.midpoint, r.midpoint_ci)} | {r.rise_10_90:.1f} | {r.rmse:.2f} | {r.r2:.2f} | {ref} |')
    lines += ['', '## Surveillance curves (ECDC EARS-Net)', '',
              f'Carbapenem-resistant *K. pneumoniae*, share of invasive isolates, per country. Fitted where a '
              f'country has at least {MIN_YEARS} years and resistance rose by at least {MIN_RISE:.0%} points. '
              f'Compare with the timeline\'s imipenem profile: peak {imi["peak"]:.0%}, rise '
              f'{imi["rise_10_90_weeks"]:.1f} weeks.', '',
              '| Country | Years | Start | Plateau | Plateau reached? | k per year | Midpoint (year) | Rise 10 to 90% (years) | RMSE (points) | R² |',
              '|---|---|---|---|---|---|---|---|---|---|']
    for r in sur.itertuples():
        reached = 'yes' if r.plateau_reached else 'no, still rising (extrapolated)'
        lines.append(f'| {r.curve.split(", ", 1)[1]} | {r.points} | {r.r0:.0%} | {r.peak:.0%} ± {r.peak_ci:.0%} | '
                     f'{reached} | {ci(r.k, r.k_ci)} | {r.midpoint:.1f} | {r.rise_10_90:.1f} | {100 * r.rmse:.1f} | '
                     f'{r.r2:.2f} |')
    lines += ['', '## Caveats', '',
              '- Lab data measure how resistant one population becomes (IC50), not what share of a population '
              'is resistant; the two are not pooled.',
              '- Surveillance percentages mix many strains, hospitals and changes in testing; some countries fall '
              'after their peak (Italy), which a logistic curve cannot follow.',
              '- Neither source is in weeks. The fits calibrate the curve\'s shape and plateau, not the timing the '
              'timeline shows.', '',
              'ECDC data: "Dataset provided by ECDC based on data provided by public health authorities, scientific '
              'institutes or health care providers in the relevant reporting countries and/or by WHO" (CC BY 4.0); '
              'the fitted curves are our adaptation.', '']
    with open(path, 'w') as fh:
        fh.write('\n'.join(lines))


def plot_lab(lab, res, path):
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, len(LAB_DRUGS), figsize=(14, 3.4), sharey=True, facecolor=SURFACE)
    tt = np.linspace(0, 8, 200)
    for ax, (code, name) in zip(axes, LAB_DRUGS.items()):
        d = lab[lab.drug == code]
        r = res[(res.source == 'lab') & (res.curve == name)].iloc[0]
        ax.plot(d.day, d.log2_fold, 'o', ms=4, mfc='none', mec=INK_2, alpha=0.6)
        m = d.groupby('day').log2_fold.mean()
        ax.plot(m.index, m.values, 'o', ms=6, color=INK_2)
        ax.plot(tt, logistic(tt, r.r0, r.peak, r.k, r.midpoint), color=SERIES[0], lw=2)
        ax.set_title(f'{name}\nR² {r.r2:.2f}, rise {r.rise_10_90:.1f} days', fontsize=9, color=INK, loc='left')
        ax.set_xticks([0, 2, 4, 6, 8])
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        style(ax)
        ax.set_xlabel('day', color=INK_2, fontsize=8)
    axes[0].set_ylabel('log2 IC50 fold change', color=INK_2, fontsize=9)
    fig.suptitle('Lab evolution (Maltas et al. 2025, E. faecalis): open circles replicates, filled means, '
                 'line the timeline\'s curve fitted', color=INK, fontsize=11, x=0.01, ha='left')
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)


def plot_surveillance(ecdc, res, kept, path):
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    sur = res[res.source == 'surveillance'].sort_values('peak', ascending=False)
    n = len(sur)
    cols = min(4, n)
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(3.4 * cols, 2.7 * rows), sharey=True, facecolor=SURFACE,
                             squeeze=False)
    peak_ref = ANTIBIOTIC_MUTATION_PROFILES['imipenem']['peak']
    for ax, r in zip(axes.flat, sur.itertuples()):
        country = r.curve.split(', ', 1)[1]
        d = ecdc[ecdc.RegionName == country].sort_values('year')
        yy = np.linspace(d.year.min(), d.year.max(), 200)
        ax.axhline(peak_ref * 100, color=INK_2, lw=1, ls=(0, (4, 3)))
        ax.plot(d.year, d.share * 100, 'o', ms=4, color=INK_2)
        ax.plot(yy, 100 * logistic(yy - d.year.min(), r.r0, r.peak, r.k, r.midpoint - d.year.min()),
                color=SERIES[0], lw=2)
        label = f'plateau {r.peak:.0%}' if r.plateau_reached else 'still rising'
        ax.set_title(f'{country}: {label}, R² {r.r2:.2f}', fontsize=9, color=INK, loc='left')
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
        ax.grid(color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        style(ax)
    for ax in list(axes.flat)[n:]:
        ax.axis('off')
    for ax in axes[:, 0]:
        ax.set_ylabel('% resistant', color=INK_2, fontsize=8)
    fig.suptitle(f'Carbapenem-resistant K. pneumoniae (ECDC EARS-Net): dots data, line fitted curve, '
                 f'dashed the timeline\'s imipenem peak ({peak_ref:.0%})', color=INK, fontsize=11, x=0.01, ha='left')
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)


def write_served(res, path):
    """The calibration object /api/timeline/ returns. rmse is in percentage points on the
    0-100 resistant_fraction scale (format section 4), so it averages the surveillance
    curves, the only ones in that unit; the lab curves are log2 IC50 and are counted in
    `curves` and `lab_curves` only. The simulation's constants are not changed by this."""
    import json
    lab = res[res.source == 'lab']
    sur = res[res.source == 'surveillance']
    obj = {
        'curves': int(len(res)),
        'drugs': list(lab.curve) + ['carbapenems'],
        'rmse': round(float(sur.rmse.mean() * 100), 1),
        'lab_curves': int(len(lab)),
        'surveillance_curves': int(len(sur)),
        'median_r2': round(float(res.r2.median()), 2),
        'parameters_changed': False,
        'sources': ['Maltas, Huynh & Wood 2025, PLOS Biology, doi:10.1371/journal.pbio.3002970',
                    'ECDC Surveillance Atlas, EARS-Net (carbapenem-resistant K. pneumoniae, 2005-2024)'],
        'note': ('The logistic shape fits published resistance curves, but they run in days (lab) or '
                 'years (hospitals), so the weeks shown are illustrative. The hand-set constants are unchanged.'),
    }
    with open(path, 'w') as fh:
        json.dump(obj, fh, indent=2)
        fh.write('\n')
    return obj


def main():
    os.makedirs(FIGURES, exist_ok=True)
    lab, ecdc = load_lab(), load_ecdc()
    sur, kept = fit_ecdc(ecdc)
    res = pd.DataFrame(fit_lab(lab) + sur)
    res.to_csv(os.path.join(RESULTS, 'calibration.csv'), index=False, float_format='%.4f')
    write_summary(res, os.path.join(RESULTS, 'calibration_summary.md'))
    served = write_served(res, SERVED)
    print(f'[calibrate] served calibration: {served["curves"]} curves, rmse {served["rmse"]} points')
    cols = ['source', 'curve', 'points', 'peak', 'k', 'midpoint', 'rise_10_90', 'rmse', 'r2']
    print(res[cols].to_string(index=False, float_format=lambda x: f'{x:.2f}'))

    import matplotlib
    matplotlib.use('Agg')
    plot_lab(lab, res, os.path.join(FIGURES, 'calibration_lab.png'))
    plot_surveillance(ecdc, res, kept, os.path.join(FIGURES, 'calibration_surveillance.png'))
    print(f'[calibrate] {len(res)} curves; wrote {os.path.relpath(RESULTS, ROOT)}/')


if __name__ == '__main__':
    main()
