"""
Figure for the report: the RL agent against the baselines (results/rl_agent.md).

Two panels, one per measure (first failed week, effective weeks), each policy a
row, one marker per fitness cost: the mean over the 100 evaluation episodes
with a line for the 2.5 to 97.5 percentile range. Run rl_train.py first.

    python experiments/evolution/rl_figure.py     # → results/figures/rl_comparison.png
"""
import os
import re

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, 'results', 'rl_agent.md')
OUT = os.path.join(HERE, 'results', 'figures', 'rl_comparison.png')

# Validated categorical slots 1 to 3 (light surface); markers differ too
COSTS = [('0%', '#2a78d6', 'o'), ('2%', '#eb6834', 's'), ('5%', '#1baf7a', '^')]
INK, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
ORDER = ['PPO agent', 'lowest resistance (greedy)', 'cycle every week', 'cycle every 4 weeks',
         'always imipenem', 'always gentamicin', 'always ciprofloxacin']
CELL = re.compile(r'([\d.]+) \[([\d.]+) to ([\d.]+)\]')


def read_tables():
    """{cost: {policy: {'effective': (mean, lo, hi), 'failed': (mean, lo, hi)}}}"""
    out, cost = {}, None
    for line in open(SOURCE):
        m = re.match(r'## Fitness cost: resistance falls (\d+%)', line)
        if m:
            cost = m.group(1)
            out[cost] = {}
            continue
        if cost and line.startswith('| ') and '[' in line:
            cells = [c.strip() for c in line.strip().strip('|').split('|')]
            name = cells[0].replace('**', '')
            if name not in ORDER or name in out[cost]:   # the paired table repeats names
                continue
            eff, fail = CELL.match(cells[1]), CELL.match(cells[2])
            out[cost][name] = {'effective': tuple(map(float, eff.groups())),
                               'failed': tuple(map(float, fail.groups()))}
    return out


def main():
    data = read_tables()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True, facecolor=SURFACE)
    panels = [('failed', 'First failed week (105 = never in 104 weeks)'),
              ('effective', 'Effective weeks (drug given under 50%), of 104')]
    rows = list(range(len(ORDER)))[::-1]
    for ax, (key, title) in zip(axes, panels):
        ax.set_facecolor(SURFACE)
        for j, (cost, colour, marker) in enumerate(COSTS):
            offset = (j - 1) * 0.22
            for row, name in zip(rows, ORDER):
                mean, lo, hi = data[cost][name][key]
                ax.plot([lo, hi], [row + offset] * 2, color=colour, linewidth=2, solid_capstyle='round')
                ax.plot(mean, row + offset, marker=marker, markersize=8, color=colour,
                        markeredgecolor=SURFACE, markeredgewidth=1.5, linestyle='none',
                        label=f'Fitness cost {cost}' if row == rows[0] else None)
        ax.set_title(title, fontsize=10, color=INK, loc='left')
        ax.set_xlim(0, 108)
        ax.grid(axis='x', color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
        ax.spines['bottom'].set_color(GRID)
        ax.tick_params(colors=MUTED, labelsize=9, length=0)
    axes[0].set_yticks(rows)
    axes[0].set_yticklabels(ORDER, fontsize=9, color=INK)
    axes[0].get_yticklabels()[0].set_fontweight('bold')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=3, frameon=False, fontsize=9,
               labelcolor=INK, bbox_to_anchor=(0.5, -0.01))
    fig.suptitle('RL agent vs baselines, 100 evaluation episodes per policy (mean, 95% range)',
                 fontsize=11, color=INK, x=0.01, ha='left')
    fig.tight_layout(rect=(0, 0.06, 1, 0.95))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=200, facecolor=SURFACE)
    print('wrote', os.path.relpath(OUT, os.path.dirname(os.path.dirname(HERE))))


if __name__ == '__main__':
    main()
