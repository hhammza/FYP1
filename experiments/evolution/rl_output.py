"""
The `rl` block of POST /api/timeline/ (progress/formats/README.md §4), built
from rl_env.py's environment and policies.

rl_env.py keeps its own units, which its results table relies on:
resistance as a share from 0 to 1, and "never failed" as week `weeks + 1`.
This module only converts for the website, following §4:

  * `resistant_fraction` in percent, 0 to 100, one decimal
  * `failure_week` is null when the drug given never reaches 50% in the window
  * each policy also carries `effective_weeks` (weeks the drug given was under
    50%) and `mean_burden` (resistant share of the drug given, averaged over
    the weeks, in percent): optional §4 fields for the comparison table

Every policy is run on the same seed, so all of them start from the same
resistance and meet the same week-to-week noise: a fair comparison.

    python experiments/evolution/rl_output.py ciprofloxacin 12    # print the block
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rl_env import DRUGS, CyclingEnv, always, cycle, lowest_resistance  # noqa: E402


def run_policy(env, policy, seed):
    """One episode of `policy`, in §4 units."""
    obs, _ = env.reset(seed=seed)
    trace, given, burdens, total, info = [env.r.copy()], [], [], 0.0, {}
    for t in range(env.weeks):
        obs, reward, _, truncated, info = env.step(policy(obs, t))
        total += reward
        given.append(info['drug'])
        burdens.append(info['burden'])
        trace.append(env.r.copy())
        if truncated:
            break
    trace = np.array(trace)
    return {
        'policy': given,
        'resistant_fraction': {d: [round(float(v) * 100, 1) for v in trace[:, i]]
                               for i, d in enumerate(env.drugs)},
        'failure_week': info.get('failure_week'),                 # None = never failed
        'total_reward': round(float(total), 2),
        'effective_weeks': int(info.get('effective_weeks', 0)),
        'mean_burden': round(float(np.mean(burdens)) * 100, 1) if burdens else None,
    }


def baseline_policies(env):
    """(name, label, policy) for the fixed baselines, `always_<drug>` first."""
    arrow = ' → '.join(d.capitalize() if i == 0 else d for i, d in enumerate(env.drugs))
    pols = [(f'always_{d}', f'Always {d}', always(i)) for i, d in enumerate(env.drugs)]
    pols += [('cycle', f'Cycle {arrow}, every week', cycle(1)),
             ('cycle_4', f'Cycle {arrow}, every 4 weeks', cycle(4)),
             ('lowest_resistance', 'Lowest resistance first (greedy)', lowest_resistance)]
    return pols


def pick_best(policies):
    """§4 tie rule: latest `failure_week` (null = later than any week), then the
    higher `total_reward`, then the one listed first (so the agent wins a full tie)."""
    def key(item):
        i, p = item
        fw = p['failure_week']
        return (float('inf') if fw is None else fw, p['total_reward'], -i)
    return max(enumerate(policies), key=key)[1]['name']


def rl_block(antibiotic, n_weeks, seed=42, drugs=DRUGS, agent=None, **env_kw):
    """The §4 `rl` object for `antibiotic` over `n_weeks`, or None when the
    environment does not have the drug (§4: `rl` absent, panel hidden).

    `agent` is the trained policy, as (label, policy) where policy takes
    (observation, week) and returns a drug index, e.g.
    ('PPO (stable-baselines3)', lambda obs, t: int(model.predict(obs)[0])).
    Without one, only the baselines are returned and `agent` is null.
    """
    if antibiotic not in drugs:
        return None
    order = [antibiotic] + [d for d in drugs if d != antibiotic]     # requested drug first
    env = CyclingEnv(drugs=order, weeks=int(n_weeks), **env_kw)
    entries = [('rl', 'RL agent', agent[1])] if agent else []
    entries += baseline_policies(env)
    policies = [dict(name=name, label=label, **run_policy(env, pol, seed)) for name, label, pol in entries]
    return {
        'drugs': order,
        'n_weeks': int(n_weeks),
        'agent': agent[0] if agent else None,
        'best': pick_best(policies),
        'policies': policies,
    }


if __name__ == '__main__':
    drug = sys.argv[1] if len(sys.argv) > 1 else DRUGS[0]
    weeks = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    print(json.dumps(rl_block(drug, weeks), indent=1, ensure_ascii=False))
