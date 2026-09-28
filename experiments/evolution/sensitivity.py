"""
Sensitivity analysis of the mutation timeline (T3.1).

The timeline in backend/ml_models/mutation_timeline.py is a logistic curve
with hand-set parameters per antibiotic:

    R(t) = r0 + (peak - r0) / (1 + exp(-k (t - midpoint)))
    k = 2.5 * speed,  midpoint = 0.45 * n_weeks,
    r0 = clip(|GC - 0.5| * 0.3, 0.02, 0.15)

and treatment "fails" in the first week R reaches 50%. This asks how much
that failure week depends on each input: speed and peak scaled by 0.7 to 1.3
(the +-30% of the plan), the GC content that sets r0, and the number of weeks
the user asks for, which sets the midpoint.

    python experiments/evolution/sensitivity.py

It calls the backend's own generate_timeline, so it tests the served code,
not a copy. Writes into experiments/evolution/results/:

    sensitivity.csv          one row per drug x speed x peak x weeks x GC
    sensitivity_summary.md   one-at-a-time effects per drug, and the findings
    figures/sensitivity_heatmaps.png   failure week over speed x peak
    figures/sensitivity_ranges.png     how far each input moves it
    figures/sensitivity_horizon.png    failure week against weeks asked for
"""
import math
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ml_models.mutation_timeline import ANTIBIOTIC_MUTATION_PROFILES, generate_timeline  # noqa: E402

RESULTS = os.path.join(HERE, 'results')
FIGURES = os.path.join(RESULTS, 'figures')

FACTORS = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3]
HORIZONS = [8, 12, 26, 52]
GCS = [0.35, 0.50, 0.65]
BASE_WEEKS = 8          # the /timeline default
BASE_GC = 0.50
THRESHOLD = 0.50        # the backend's failure rule: resistant >= 50%

# Chart colours (dataviz reference palette, light mode)
SURFACE, INK, INK_2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
NEVER = '#f0efec'
SEQ = ['#cde2fb', '#9ec5f4', '#6da7ec', '#3987e5', '#256abf', '#184f95', '#0d366b']
SERIES = ['#2a78d6', '#eb6834', '#1baf7a']
SHORT = {'trimethoprim/sulfamethoxazole': 'trimethoprim/SMX'}   # fits a panel title
WEEK_BINS = [0, 3, 4, 5, 6, 8, 12, 30]                            # one colour per bin


def r0_for(gc):
    """Starting resistant share, as in generate_timeline."""
    return max(0.02, min(abs(gc - 0.50) * 0.3, 0.15))


def crossing_week(speed, peak, n_weeks, gc):
    """Exact time R(t) reaches the threshold, from the formula; None if it
    never does (peak at or below the threshold). May exceed n_weeks."""
    r0 = r0_for(gc)
    if peak <= THRESHOLD:
        return None
    if r0 >= THRESHOLD:
        return 0.0
    k, mid = 2.5 * speed, 0.45 * n_weeks
    return mid - math.log((peak - r0) / (THRESHOLD - r0) - 1) / k


def failure_week(profile, n_weeks, gc):
    """First whole week the served timeline reports >= 50% resistant."""
    rng = np.random.default_rng(42)
    timeline = generate_timeline(profile, n_weeks, gc, 1_000_000, rng)
    return next((e['week'] for e in timeline if e['resistant_fraction'] >= THRESHOLD * 100), None)


def run_grid():
    rows = []
    for drug, base in ANTIBIOTIC_MUTATION_PROFILES.items():
        for sf in FACTORS:
            for pf in FACTORS:
                speed, peak = base['speed'] * sf, min(base['peak'] * pf, 1.0)
                profile = {**base, 'speed': speed, 'peak': peak}
                for n in HORIZONS:
                    for gc in GCS:
                        exact = crossing_week(speed, peak, n, gc)
                        week = failure_week(profile, n, gc)
                        # The exact crossing and the served week must agree. The backend
                        # rounds the share to 2 decimals, so a crossing a hair after a
                        # whole week (49.998%) already counts in that week.
                        expected = None if exact is None or exact > n else max(0, math.ceil(exact - 1e-9))
                        near = exact is not None and abs(exact - round(exact)) < 0.01 and round(exact) <= n
                        assert week == expected or (near and week == max(0, round(exact))), \
                            (drug, sf, pf, n, gc, week, exact)
                        rows.append({'drug': drug, 'speed_factor': sf, 'peak_factor': pf,
                                     'speed': round(speed, 4), 'peak': round(peak, 4),
                                     'n_weeks': n, 'gc': gc, 'r0': round(r0_for(gc), 4),
                                     'failure_week': week,
                                     'crossing_week': None if exact is None else round(exact, 3),
                                     'outcome': ('never' if exact is None else
                                                 'within horizon' if exact <= n else 'after horizon')})
    return pd.DataFrame(rows)


def one_at_a_time(grid):
    """Crossing week at the base case and with one input changed."""
    def at(drug, sf=1.0, pf=1.0, n=BASE_WEEKS, gc=BASE_GC):
        r = grid[(grid.drug == drug) & (grid.speed_factor == sf) & (grid.peak_factor == pf)
                 & (grid.n_weeks == n) & (grid.gc == gc)].iloc[0]
        return r['crossing_week']
    out = []
    for drug in ANTIBIOTIC_MUTATION_PROFILES:
        out.append({'drug': drug, 'base': at(drug),
                    'speed -30%': at(drug, sf=0.7), 'speed +30%': at(drug, sf=1.3),
                    'peak -30%': at(drug, pf=0.7), 'peak +30%': at(drug, pf=1.3),
                    'GC 0.35': at(drug, gc=0.35), 'GC 0.65': at(drug, gc=0.65),
                    '12 weeks asked': at(drug, n=12), '52 weeks asked': at(drug, n=52)})
    return pd.DataFrame(out)


def fmt(x):
    return 'never' if x is None or (isinstance(x, float) and math.isnan(x)) else f'{x:.1f}'


def write_summary(grid, oat, path):
    base = grid[(grid.n_weeks == BASE_WEEKS) & (grid.gc == BASE_GC)]
    never_base = sorted(set(grid[(grid.speed_factor == 1) & (grid.peak_factor == 1)
                                 & (grid.outcome == 'never')].drug))
    flips = (base.groupby('drug')['outcome'].apply(lambda s: (s == 'never').any() and (s != 'never').any()))
    flips = sorted(flips[flips].index)
    ratio = (oat['52 weeks asked'] / oat['base']).dropna()
    speed_move = (oat['speed -30%'] - oat['speed +30%']).abs().dropna()

    lines = [
        '# Timeline sensitivity analysis', '',
        'Written by `sensitivity.py`. Crossing week = the exact time the resistant share reaches 50% '
        '(the served timeline reports the next whole week). Base case: the hand-set profile, '
        f'{BASE_WEEKS} weeks asked (the `/timeline` default), GC {BASE_GC}.', '',
        '## Findings', '',
        f'1. **The number of weeks asked for decides the answer.** The midpoint is 0.45 x the weeks asked, '
        f'so asking for 52 weeks instead of {BASE_WEEKS} moves the crossing '
        f'{ratio.min():.1f} to {ratio.max():.1f} times later for the same bacterium and drug. '
        'A biological quantity should not depend on the length of the chart.',
        f'2. **`peak` works as a switch.** At or below 50% the drug never fails. '
        f'{len(flips)} of {base.drug.nunique()} profiles switch between "fails" and "never fails" '
        f'within peak +-30%: {", ".join(flips) or "none"}.'
        + (f' At the hand-set values, {", ".join(never_base)} never '
           f'{"fails" if len(never_base) == 1 else "fail"}.' if never_base else ''),
        f'3. **`speed` matters less.** Speed +-30% moves the crossing by at most {speed_move.max():.1f} '
        f'weeks (median {speed_move.median():.1f}) at {BASE_WEEKS} weeks asked.',
        '4. **GC content sets the starting share (2% to 15%)** and moves the crossing only slightly.', '',
        'So the parameters worth calibrating are a per-drug midpoint (instead of 0.45 x the weeks asked) '
        'and the peak; speed is second.', '',
        '## One input at a time', '',
        '| Drug | Base | Speed -30% | Speed +30% | Peak -30% | Peak +30% | GC 0.35 | GC 0.65 | 12 weeks asked | 52 weeks asked |',
        '|---|---|---|---|---|---|---|---|---|---|',
    ]
    for r in oat.itertuples(index=False):
        lines.append('| ' + ' | '.join([r[0]] + [fmt(v) for v in r[1:]]) + ' |')
    lines += ['', f'Grid: {len(grid):,} rows ({grid.drug.nunique()} profiles x {len(FACTORS)} speeds x '
              f'{len(FACTORS)} peaks x {len(HORIZONS)} horizons x {len(GCS)} GC values) in `sensitivity.csv`. '
              'Every row was checked: the served `generate_timeline` and the exact crossing agree.', '']
    with open(path, 'w') as fh:
        fh.write('\n'.join(lines))


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    for side in ('left', 'bottom'):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8, length=0)


def plot_heatmaps(grid, path):
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    base = grid[(grid.n_weeks == BASE_WEEKS) & (grid.gc == BASE_GC)]
    drugs = list(ANTIBIOTIC_MUTATION_PROFILES)
    cols = 5
    rows = math.ceil(len(drugs) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(13, 2.9 * rows), facecolor=SURFACE)
    cmap = ListedColormap(SEQ)
    cmap.set_bad(NEVER)
    norm = BoundaryNorm(WEEK_BINS, cmap.N)
    for ax, drug in zip(axes.flat, drugs):
        d = base[base.drug == drug].pivot(index='peak_factor', columns='speed_factor', values='crossing_week')
        z = np.ma.masked_invalid(d.values.astype(float))
        im = ax.imshow(z, origin='lower', cmap=cmap, norm=norm, aspect='auto')
        ax.set_xticks(range(len(FACTORS)), [f'{f:.1f}' for f in FACTORS])
        ax.set_yticks(range(len(FACTORS)), [f'{f:.1f}' for f in FACTORS])
        ax.add_patch(plt.Rectangle((2.5, 2.5), 1, 1, fill=False, ec=INK, lw=1.5))  # hand-set values
        ax.set_title(SHORT.get(drug, drug), fontsize=9, color=INK, loc='left')
        style(ax)
    for ax in list(axes.flat)[len(drugs):]:
        ax.axis('off')
    fig.supxlabel('speed (x hand-set value)', color=INK_2, fontsize=9)
    fig.supylabel('peak (x hand-set value)', color=INK_2, fontsize=9)
    fig.suptitle(f'Week resistance reaches 50%, {BASE_WEEKS} weeks asked, GC {BASE_GC}. '
                 'Outlined cell: hand-set values. Grey: never reaches 50%.',
                 color=INK, fontsize=11, x=0.01, ha='left')
    cbar = fig.colorbar(im, ax=axes, shrink=0.6, pad=0.01, spacing='uniform', ticks=WEEK_BINS)
    cbar.set_label('crossing week (past 8: after the chart ends)', color=INK_2, fontsize=9)
    cbar.ax.tick_params(colors=INK_2, labelsize=8)
    cbar.outline.set_visible(False)
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)


def plot_ranges(oat, path):
    """For each input: base crossing (dot) and the -/+ values (range)."""
    import matplotlib.pyplot as plt

    panels = [('speed', 'speed -30%', 'speed +30%'), ('peak', 'peak -30%', 'peak +30%'),
              ('GC content', 'GC 0.35', 'GC 0.65'), ('weeks asked', '12 weeks asked', '52 weeks asked')]
    subtitles = {'speed': 'open: -30%, filled: +30%', 'peak': 'open: -30%, filled: +30%',
                 # r0 uses |GC - 0.5|, so both give the same start and the dots overlap
                 'GC content': '0.35 and 0.65 give the same start', 'weeks asked': 'open: 12, filled: 52'}
    order = oat.sort_values('base', na_position='last')
    y = np.arange(len(order))
    fig, axes = plt.subplots(1, len(panels), figsize=(14, 5.2), sharey=True, facecolor=SURFACE)
    for ax, (title, lo, hi) in zip(axes, panels):
        lows, highs, bases = order[lo].astype(float), order[hi].astype(float), order['base'].astype(float)
        for i in range(len(order)):
            pts = [v for v in (lows.iloc[i], highs.iloc[i], bases.iloc[i]) if not math.isnan(v)]
            if len(pts) > 1:
                ax.plot([min(pts), max(pts)], [y[i], y[i]], color=SERIES[0], lw=2, alpha=0.35,
                        solid_capstyle='round')
            if not math.isnan(lows.iloc[i]):
                ax.plot(lows.iloc[i], y[i], 'o', ms=5, mfc=SURFACE, mec=SERIES[0], mew=1.5)
            if not math.isnan(highs.iloc[i]):
                ax.plot(highs.iloc[i], y[i], 'o', ms=5, color=SERIES[0])
            if not math.isnan(bases.iloc[i]):
                ax.plot(bases.iloc[i], y[i], '|', ms=12, mew=2, color=INK)
            else:
                ax.text(0.02, y[i], 'never at base', va='center', fontsize=7, color=INK_2,
                        transform=ax.get_yaxis_transform())
        ax.set_title(f'{title}\n({subtitles[title]})', fontsize=9, color=INK, loc='left')
        ax.grid(axis='x', color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        style(ax)
        ax.set_xlabel('crossing week', color=INK_2, fontsize=8)
    axes[0].set_yticks(y, [SHORT.get(d, d) for d in order['drug']])
    fig.suptitle(f'How far each input moves the week resistance reaches 50% '
                 f'(black tick: hand-set profile, {BASE_WEEKS} weeks asked, GC {BASE_GC})',
                 color=INK, fontsize=11, x=0.01, ha='left')
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)


def plot_horizon(path):
    """Crossing week against weeks asked, for a fast, a middle and a slow drug."""
    import matplotlib.pyplot as plt

    weeks = np.arange(4, 53)
    fig, ax = plt.subplots(figsize=(7.5, 4.6), facecolor=SURFACE)
    ax.plot(weeks, weeks, color=INK_2, lw=1, ls=(0, (4, 3)))
    ax.text(weeks[-1], weeks[-1], ' end of chart', color=INK_2, fontsize=8, va='center')
    for colour, drug in zip(SERIES, ['ampicillin', 'gentamicin', 'imipenem']):
        p = ANTIBIOTIC_MUTATION_PROFILES[drug]
        cross = [crossing_week(p['speed'], p['peak'], n, BASE_GC) for n in weeks]
        ax.plot(weeks, cross, color=colour, lw=2)
        ax.text(weeks[-1] + 0.5, cross[-1], f' {drug}', color=INK, fontsize=9, va='center')
        ax.plot(weeks[-1], cross[-1], 'o', ms=6, color=colour, mec=SURFACE, mew=2)
    ax.set_xlabel('weeks asked for on /timeline', color=INK_2, fontsize=9)
    ax.set_ylabel('week resistance reaches 50%', color=INK_2, fontsize=9)
    ax.set_title('Same bacterium, same drug: the answer grows with the chart length',
                 color=INK, fontsize=11, loc='left')
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.set_xlim(4, 62)
    style(ax)
    fig.tight_layout()
    fig.savefig(path, dpi=160, bbox_inches='tight', facecolor=SURFACE)
    plt.close(fig)


def main():
    os.makedirs(FIGURES, exist_ok=True)
    grid = run_grid()
    grid.to_csv(os.path.join(RESULTS, 'sensitivity.csv'), index=False)
    oat = one_at_a_time(grid)
    write_summary(grid, oat, os.path.join(RESULTS, 'sensitivity_summary.md'))
    print(f'[sensitivity] {len(grid):,} rows; served timeline and exact crossing agree on every row')
    print(oat.to_string(index=False, float_format=lambda x: f'{x:.1f}'))

    import matplotlib
    matplotlib.use('Agg')
    plot_heatmaps(grid, os.path.join(FIGURES, 'sensitivity_heatmaps.png'))
    plot_ranges(oat, os.path.join(FIGURES, 'sensitivity_ranges.png'))
    plot_horizon(os.path.join(FIGURES, 'sensitivity_horizon.png'))
    print(f'[sensitivity] wrote {os.path.relpath(RESULTS, ROOT)}/')


if __name__ == '__main__':
    main()
