"""
The `rl` block of POST /api/timeline/ (progress/formats/README.md section 4):
which drug to give each week, the trained RL agent against fixed baselines.

The agent was trained by experiments/evolution/rl_train.py (PPO,
stable-baselines3) on experiments/evolution/rl_env.py's cycling environment.
The backend has neither gymnasium nor torch, so this module keeps a numpy copy
of both: the environment (same equations, same random stream for a seed) and
the agent's policy network (weights in trained_models/rl_agent/policy.npz).
experiments/evolution/test_rl_agent.py checks that this block equals
rl_output.rl_block() with the same agent, number for number.

Units follow section 4: resistance in percent 0 to 100, `failure_week` null
when the drug given never starts a week at 50% or more.

Artifacts, in trained_models/rl_agent/:
    policy.npz       the policy network's weights (w0, b0, w1, b1, w2, b2)
    rl_agent.json    drugs and horizon it was trained on, fitness cost, evaluation
"""
import json
import os

import numpy as np

from ml_models.mutation_timeline import ANTIBIOTIC_MUTATION_PROFILES

FOLDER = 'rl_agent'
FAIL_AT = 0.5


class CyclingSim:
    """numpy copy of rl_env.CyclingEnv (same defaults)."""

    def __init__(self, drugs, weeks, decay=0.05, lam=1.0, noise=0.1, r0=(0.02, 0.10)):
        self.drugs, self.weeks = list(drugs), int(weeks)
        self.decay, self.lam, self.noise, self.r0 = decay, lam, noise, r0
        prof = [ANTIBIOTIC_MUTATION_PROFILES[d] for d in self.drugs]
        self.k = np.array([2.5 * p['speed'] for p in prof])
        self.peak = np.array([p['peak'] for p in prof])

    def reset(self, seed):
        self.rng = np.random.default_rng(seed)       # what gymnasium's reset(seed=...) builds
        self.r = self.rng.uniform(*self.r0, size=len(self.drugs))
        self.r = np.minimum(self.r, self.peak * 0.99)
        self.t, self.failure_week, self.effective_weeks = 0, None, 0
        return self.obs()

    def obs(self):
        return np.append(self.r, self.t / self.weeks).astype(np.float32)

    def step(self, a):
        old = self.r.copy()
        burden = float(self.r[a])
        k = self.k[a] * float(np.exp(self.rng.normal(0, self.noise)))
        p, r = self.peak[a], self.r[a]
        self.r[a] = p / (1 + (p / r - 1) * np.exp(-k))
        rest = np.arange(len(self.r)) != a
        self.r[rest] *= (1 - self.decay)
        self.t += 1
        growth = float(np.clip(self.r - old, 0, None).sum())
        works = burden < FAIL_AT
        self.effective_weeks += works
        if self.failure_week is None and not works:
            self.failure_week = self.t
        return self.obs(), -burden - self.lam * growth, burden


def always(i):
    return lambda obs, t: i


def cycle(period=1):
    return lambda obs, t: (t // period) % (len(obs) - 1)


def lowest_resistance(obs, t):
    return int(np.argmin(obs[:-1]))


def run_policy(sim, policy, seed):
    obs = sim.reset(seed)
    trace, given, burdens, total = [sim.r.copy()], [], [], 0.0
    for t in range(sim.weeks):
        a = policy(obs, t)
        obs, reward, burden = sim.step(a)
        total += reward
        given.append(sim.drugs[a])
        burdens.append(burden)
        trace.append(sim.r.copy())
    trace = np.array(trace)
    return {
        'policy': given,
        'resistant_fraction': {d: [round(float(v) * 100, 1) for v in trace[:, i]]
                               for i, d in enumerate(sim.drugs)},
        'failure_week': sim.failure_week,
        'total_reward': round(float(total), 2),
        'effective_weeks': int(sim.effective_weeks),
        'mean_burden': round(float(np.mean(burdens)) * 100, 1) if burdens else None,
    }


def baseline_policies(drugs):
    arrow = ' → '.join(d.capitalize() if i == 0 else d for i, d in enumerate(drugs))
    pols = [(f'always_{d}', f'Always {d}', always(i)) for i, d in enumerate(drugs)]
    pols += [('cycle', f'Cycle {arrow}, every week', cycle(1)),
             ('cycle_4', f'Cycle {arrow}, every 4 weeks', cycle(4)),
             ('lowest_resistance', 'Lowest resistance first (greedy)', lowest_resistance)]
    return pols


def pick_best(policies):
    """Section 4 tie rule: latest failure_week (null = never), then total_reward, then listed first."""
    def key(item):
        i, p = item
        fw = p['failure_week']
        return (float('inf') if fw is None else fw, p['total_reward'], -i)
    return max(enumerate(policies), key=key)[1]['name']


class RLAgent:
    """The trained policy, usable on any drug order and any window of weeks."""

    def __init__(self, folder):
        with open(os.path.join(folder, 'rl_agent.json')) as fh:
            self.meta = json.load(fh)
        z = np.load(os.path.join(folder, 'policy.npz'))
        n = self.meta['layers']
        self.layers = [(z[f'w{i}'], z[f'b{i}']) for i in range(n)]
        self.drugs = list(self.meta['drugs'])
        self.train_weeks = int(self.meta['train_weeks'])
        self.decay = float(self.meta['decay'])
        self.label = self.meta.get('agent', 'RL agent')

    def act(self, resistance, week):
        """Drug index (in self.drugs order) for resistant shares in self.drugs order."""
        h = np.append(np.asarray(resistance, float), week / self.train_weeks).astype(np.float32).astype(np.float64)
        for w, b in self.layers[:-1]:
            h = np.tanh(h @ w.T + b)
        w, b = self.layers[-1]
        return int(np.argmax(h @ w.T + b))

    def policy_for(self, order):
        """policy(obs, t) for an environment whose drugs are in `order`.

        The agent sees the drugs in its training order and the week against its
        training horizon, whatever window the request asks for (1 to 52 weeks of
        the 104 it was trained on)."""
        to_train = [order.index(d) for d in self.drugs]
        return lambda obs, t: order.index(self.drugs[self.act(np.asarray(obs)[to_train], t)])

    def block(self, antibiotic, n_weeks, seed=42):
        """The section 4 `rl` object, or None when the agent was not trained with this drug."""
        if antibiotic not in self.drugs:
            return None
        order = [antibiotic] + [d for d in self.drugs if d != antibiotic]
        sim = CyclingSim(order, n_weeks, decay=self.decay)
        entries = [('rl', 'RL agent', self.policy_for(order))] + baseline_policies(order)
        policies = [dict(name=name, label=label, **run_policy(sim, pol, seed)) for name, label, pol in entries]
        return {'drugs': order, 'n_weeks': int(n_weeks), 'agent': self.label,
                'best': pick_best(policies), 'policies': policies}


def load(model_dir):
    """The served agent, or None when trained_models/rl_agent/ is missing (no `rl` block then)."""
    folder = os.path.join(model_dir, FOLDER)
    if not os.path.exists(os.path.join(folder, 'policy.npz')):
        return None
    try:
        return RLAgent(folder)
    except Exception as e:
        print(f'[RL] Could not load the agent: {e}')
        return None
