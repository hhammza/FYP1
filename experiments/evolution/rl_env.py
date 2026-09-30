"""
Antibiotic cycling environment for the RL agent (T3.1c).

Each week one drug is given. The resistant share of the population for that
drug grows along the same logistic curve as the mutation timeline
(backend/ml_models/mutation_timeline.py: rate k = 2.5 * speed, ceiling = peak),
and the drugs not given lose resistance slowly, because resistance usually
costs the bacteria some fitness. The question is which order of drugs keeps
at least one of them working for longest.

    state   resistant share per drug (0 to 1), plus the share of the horizon gone
    action  which drug to give this week
    reward  -(resistant share of the drug given)       the infection it fails to clear
            - lam * (total rise in resistance this week)

A week's treatment fails when the drug given is at 50% resistance or more.
Two measures: the first week that happens, and the number of effective weeks
(the drug given was under 50%). Episodes do not stop at a failure: with
negative rewards, ending early would pay the agent to fail fast. Every
episode runs the full horizon; both measures come from `info`.

Simplifications, to state in the report: drugs are from different classes and
no cross-resistance is modelled; the weekly decay (fitness cost) is a guess,
so results are shown for several values; the curves are the timeline's
hand-set profiles, and the time scale is illustrative (see results/
calibration_summary.md). The policy is learned on a simulation, not on
patient data.

    python experiments/evolution/rl_env.py          # check the environment, run the baselines

Writes results/rl_baselines.md.
"""
import argparse
import os
import sys

import gymnasium as gym
import numpy as np
from gymnasium import spaces

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from ml_models.mutation_timeline import ANTIBIOTIC_MUTATION_PROFILES  # noqa: E402

RESULTS = os.path.join(HERE, 'results')

# Three classes with fast, middle and slow resistance in the timeline profiles
DRUGS = ['ciprofloxacin', 'gentamicin', 'imipenem']
WEEKS = 104
FAIL_AT = 0.5


class CyclingEnv(gym.Env):
    metadata = {'render_modes': []}

    def __init__(self, drugs=DRUGS, weeks=WEEKS, decay=0.05, lam=1.0, noise=0.1,
                 r0=(0.02, 0.10)):
        super().__init__()
        self.drugs = list(drugs)
        self.weeks, self.decay, self.lam, self.noise, self.r0 = weeks, decay, lam, noise, r0
        prof = [ANTIBIOTIC_MUTATION_PROFILES[d] for d in self.drugs]
        self.k = np.array([2.5 * p['speed'] for p in prof])
        self.peak = np.array([p['peak'] for p in prof])
        n = len(self.drugs)
        self.action_space = spaces.Discrete(n)
        self.observation_space = spaces.Box(0.0, 1.0, shape=(n + 1,), dtype=np.float32)

    def _obs(self):
        return np.append(self.r, self.t / self.weeks).astype(np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.r = self.np_random.uniform(*self.r0, size=len(self.drugs))
        # A drug whose ceiling is under its start never grows; keep r below peak
        self.r = np.minimum(self.r, self.peak * 0.99)
        self.t = 0
        self.failure_week = None
        self.effective_weeks = 0
        return self._obs(), {}

    def step(self, action):
        a = int(action)
        old = self.r.copy()
        burden = float(self.r[a])          # share of the infection this week's drug misses

        # The drug given: one week along its logistic curve (exact solution,
        # so large rates cannot overshoot), rate varied a little week to week.
        k = self.k[a] * float(np.exp(self.np_random.normal(0, self.noise)))
        p, r = self.peak[a], self.r[a]
        self.r[a] = p / (1 + (p / r - 1) * np.exp(-k))
        # The others: resistance fades while the drug is not used
        rest = np.arange(len(self.r)) != a
        self.r[rest] *= (1 - self.decay)

        self.t += 1
        growth = float(np.clip(self.r - old, 0, None).sum())
        reward = -burden - self.lam * growth
        works = burden < FAIL_AT
        self.effective_weeks += works
        if self.failure_week is None and not works:
            self.failure_week = self.t
        truncated = self.t >= self.weeks
        info = {'failure_week': self.failure_week, 'effective_weeks': self.effective_weeks,
                'burden': burden, 'drug': self.drugs[a]}
        return self._obs(), reward, False, truncated, info


# Policies to beat: each takes (observation, week) and returns a drug index
def always(i):
    return lambda obs, t: i


def cycle(period=1):
    """A, B, C, A, ... changing drug every `period` weeks."""
    return lambda obs, t: (t // period) % (len(obs) - 1)


def lowest_resistance(obs, t):
    """Greedy: the drug that currently works best."""
    return int(np.argmin(obs[:-1]))


def run_episode(env, policy, seed):
    obs, _ = env.reset(seed=seed)
    total, burdens, trace = 0.0, [], [env.r.copy()]
    for t in range(env.weeks):
        obs, reward, _, truncated, info = env.step(policy(obs, t))
        total += reward
        burdens.append(info['burden'])
        trace.append(env.r.copy())
        if truncated:
            break
    fw = info['failure_week']
    return {'reward': total, 'mean_burden': float(np.mean(burdens)),
            'failure_week': fw if fw is not None else env.weeks + 1,
            'effective_weeks': info['effective_weeks'],
            'failed': fw is not None, 'trace': np.array(trace)}


def evaluate(env, policy, seeds):
    eps = [run_episode(env, policy, s) for s in seeds]
    out = {}
    for key in ('failure_week', 'effective_weeks', 'reward', 'mean_burden'):
        v = np.array([e[key] for e in eps], dtype=float)
        out[key] = (v.mean(), *np.percentile(v, [2.5, 97.5]))
    out['failed_share'] = float(np.mean([e['failed'] for e in eps]))
    return out


def baselines(env):
    pols = {f'always {d}': always(i) for i, d in enumerate(env.drugs)}
    pols['cycle every week'] = cycle(1)
    pols['cycle every 4 weeks'] = cycle(4)
    pols['lowest resistance (greedy)'] = lowest_resistance
    return pols


def fmt(m):
    return f'{m[0]:.1f} [{m[1]:.1f} to {m[2]:.1f}]'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--episodes', type=int, default=100)
    args = ap.parse_args()

    from gymnasium.utils.env_checker import check_env
    check_env(CyclingEnv(), skip_render_check=True)
    print('[env] gymnasium check passed')

    seeds = range(1000, 1000 + args.episodes)   # evaluation seeds; training uses others
    lines = ['# RL environment: baseline policies', '',
             f'Drugs {", ".join(DRUGS)}; horizon {WEEKS} weeks. A week\'s treatment fails when '
             f'the drug given is at {FAIL_AT:.0%} resistance or more. First failed week: the first '
             f'such week ({WEEKS + 1} = none). Effective weeks: weeks the drug given was under '
             f'{FAIL_AT:.0%}, out of {WEEKS}. Burden: resistant share of the drug given, averaged '
             f'over the weeks. {args.episodes} episodes each (seeds 1000 on), mean and 2.5 to 97.5 '
             'percentile. Built by `experiments/evolution/rl_env.py`.']
    for decay in (0.0, 0.02, 0.05):
        env = CyclingEnv(decay=decay)
        lines += ['', f'## Fitness cost: resistance falls {decay:.0%} a week when a drug is not used', '',
                  '| Policy | Effective weeks | First failed week | Mean burden | Total reward |',
                  '| --- | --- | --- | --- | --- |']
        for name, pol in baselines(env).items():
            m = evaluate(env, pol, seeds)
            lines.append(f'| {name} | {fmt(m["effective_weeks"])} | {fmt(m["failure_week"])} | '
                         f'{m["mean_burden"][0]:.3f} | {fmt(m["reward"])} |')
    os.makedirs(RESULTS, exist_ok=True)
    out = os.path.join(RESULTS, 'rl_baselines.md')
    with open(out, 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    print(f'\nwrote {os.path.relpath(out, ROOT)}')


if __name__ == '__main__':
    main()
