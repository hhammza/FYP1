"""
Train the RL agent on the cycling environment and compare it with the baselines (T3.1c).

PPO from stable-baselines3 learns which drug to give each week in
rl_env.CyclingEnv. One agent per fitness cost (the weekly decay of resistance
to a drug that is not used: 0%, 2%, 5%), each trained from three seeds, then
evaluated on the same 100 seeds as the baselines (1000 on; training never
sees them), deterministically (the most likely drug each week).

    python experiments/evolution/rl_train.py                 # train, evaluate, export
    python experiments/evolution/rl_train.py --steps 20000   # quick check
    python experiments/evolution/rl_train.py --from-saved    # re-evaluate the saved agents

Writes
    results/rl_agent.md      agent vs baselines per fitness cost, spread over evaluation and training seeds
    results/rl_agent.csv     the same numbers, one row per policy and fitness cost
    models/ppo_decay<d>_seed<s>.zip   the trained agents (stable-baselines3)
    backend/trained_models/rl_agent/  the served agent (decay 5%, best training seed by mean
                                      reward on the training-side check): weights as numpy, read by
                                      backend/ml_models/rl_agent.py without torch
"""
import argparse
import csv
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from rl_env import DRUGS, FAIL_AT, WEEKS, CyclingEnv, baselines, evaluate, run_episode  # noqa: E402

RESULTS = os.path.join(HERE, 'results')
MODELS = os.path.join(HERE, 'models')
SERVED = os.path.join(ROOT, 'backend', 'trained_models', 'rl_agent')

DECAYS = (0.0, 0.02, 0.05)
SERVED_DECAY = 0.05          # CyclingEnv's default, the setting the website uses
TRAIN_SEEDS = (0, 1, 2)
EVAL_SEEDS = range(1000, 1100)
CHECK_SEEDS = range(500, 550)  # picks the served training seed; disjoint from EVAL_SEEDS


def train(decay, seed, steps, n_envs=8):
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env
    venv = make_vec_env(lambda: CyclingEnv(decay=decay), n_envs=n_envs, seed=seed)
    model = PPO('MlpPolicy', venv, seed=seed, verbose=0, gamma=0.99, n_steps=512,
                batch_size=256, learning_rate=3e-4, ent_coef=0.01)
    model.learn(total_timesteps=steps)
    return model


def agent_policy(model):
    return lambda obs, t: int(model.predict(obs, deterministic=True)[0])


def export(model, decay, seed, metrics):
    """The policy network as plain arrays: Linear-Tanh-Linear-Tanh, then the action logits."""
    pol = model.policy
    layers = [m for m in pol.mlp_extractor.policy_net if hasattr(m, 'weight')] + [pol.action_net]
    arrays = {}
    for i, layer in enumerate(layers):
        arrays[f'w{i}'] = layer.weight.detach().cpu().numpy().astype(np.float64)
        arrays[f'b{i}'] = layer.bias.detach().cpu().numpy().astype(np.float64)
    os.makedirs(SERVED, exist_ok=True)
    np.savez(os.path.join(SERVED, 'policy.npz'), **arrays)
    # Check the numpy forward pass picks the same drug as stable-baselines3
    rng = np.random.default_rng(0)
    obs = rng.uniform(0, 1, size=(2000, len(DRUGS) + 1)).astype(np.float32)
    h = obs.astype(np.float64)
    for i in range(len(layers) - 1):
        h = np.tanh(h @ arrays[f'w{i}'].T + arrays[f'b{i}'])
    logits = h @ arrays[f'w{len(layers) - 1}'].T + arrays[f'b{len(layers) - 1}']
    agree = float(np.mean(np.argmax(logits, 1) == model.predict(obs, deterministic=True)[0]))
    meta = {
        'agent': 'PPO (stable-baselines3)',
        'drugs': DRUGS, 'train_weeks': WEEKS, 'decay': decay, 'training_seed': seed,
        'layers': len(layers), 'activation': 'tanh',
        'observation': 'resistant share per drug (0 to 1) in `drugs` order, then week / train_weeks',
        'numpy_agrees_with_sb3': agree,
        'evaluation': metrics,
        'built_by': 'experiments/evolution/rl_train.py',
    }
    with open(os.path.join(SERVED, 'rl_agent.json'), 'w') as fh:
        json.dump(meta, fh, indent=1)
    return agree


def fmt(m):
    return f'{m[0]:.1f} [{m[1]:.1f} to {m[2]:.1f}]'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--steps', type=int, default=300_000, help='training steps per agent')
    ap.add_argument('--from-saved', action='store_true', help='evaluate the agents in models/ instead of training')
    args = ap.parse_args()
    os.makedirs(MODELS, exist_ok=True)
    os.makedirs(RESULTS, exist_ok=True)

    rows, lines = [], [
        '# RL agent: PPO against the baselines', '',
        f'Environment `rl_env.CyclingEnv`: drugs {", ".join(DRUGS)}, horizon {WEEKS} weeks, a week fails '
        f'when the drug given starts the week at {FAIL_AT:.0%} resistance or more. PPO '
        f'(stable-baselines3, MLP 64-64, {args.steps:,} steps, 8 parallel environments) trained from '
        f'{len(TRAIN_SEEDS)} seeds per fitness cost. Every policy is evaluated on the same '
        f'{len(EVAL_SEEDS)} episodes (seeds {EVAL_SEEDS.start} on, never used in training); the agent picks '
        'its most likely drug each week. Mean and 2.5 to 97.5 percentile over the evaluation episodes; '
        'for the agent, the three training seeds are pooled (300 episodes), and the spread of the '
        'per-seed means is given separately. Built by `experiments/evolution/rl_train.py`.']

    served = None
    for decay in DECAYS:
        env = CyclingEnv(decay=decay)
        per_seed, eps_metrics, models = [], [], {}
        for seed in TRAIN_SEEDS:
            t0 = time.time()
            path = os.path.join(MODELS, f'ppo_decay{decay:.2f}_seed{seed}.zip')
            if args.from_saved:
                from stable_baselines3 import PPO
                model = PPO.load(path)
            else:
                model = train(decay, seed, args.steps)
                model.save(path)
            models[seed] = model
            m = evaluate(env, agent_policy(model), EVAL_SEEDS)
            check = evaluate(env, agent_policy(model), CHECK_SEEDS)['reward'][0]
            per_seed.append((seed, m, check))
            print(f'[rl] decay {decay:.2f} seed {seed}: effective {m["effective_weeks"][0]:.1f}, '
                  f'first failed {m["failure_week"][0]:.1f}, reward {m["reward"][0]:.1f} '
                  f'({time.time() - t0:.0f}s)', flush=True)

        # Pool the agents' episodes for the table
        episodes = {s: [run_episode(env, agent_policy(models[s]), e) for e in EVAL_SEEDS] for s in TRAIN_SEEDS}
        pooled = {}
        for key in ('effective_weeks', 'failure_week', 'reward', 'mean_burden'):
            v = np.array([ep[key] for s in TRAIN_SEEDS for ep in episodes[s]], dtype=float)
            pooled[key] = (v.mean(), *np.percentile(v, [2.5, 97.5]))
        seed_means = {k: [p[1][k][0] for p in per_seed] for k in ('effective_weeks', 'failure_week', 'reward')}

        lines += ['', f'## Fitness cost: resistance falls {decay:.0%} a week when a drug is not used', '',
                  '| Policy | Effective weeks | First failed week | Mean burden | Total reward |',
                  '| --- | --- | --- | --- | --- |',
                  f'| **PPO agent** | {fmt(pooled["effective_weeks"])} | {fmt(pooled["failure_week"])} | '
                  f'{pooled["mean_burden"][0]:.3f} | {fmt(pooled["reward"])} |']
        rows.append(dict(decay=decay, policy='PPO agent', **{k: round(pooled[k][0], 3) for k in pooled}))
        for name, pol in baselines(env).items():
            m = evaluate(env, pol, EVAL_SEEDS)
            lines.append(f'| {name} | {fmt(m["effective_weeks"])} | {fmt(m["failure_week"])} | '
                         f'{m["mean_burden"][0]:.3f} | {fmt(m["reward"])} |')
            rows.append(dict(decay=decay, policy=name, **{k: round(m[k][0], 3)
                                                          for k in ('effective_weeks', 'failure_week', 'reward', 'mean_burden')}))
        lines += ['', 'Per training seed (mean over the evaluation episodes): ' + '; '.join(
            f'seed {s}: effective {m["effective_weeks"][0]:.1f}, first failed {m["failure_week"][0]:.1f}, '
            f'reward {m["reward"][0]:.1f}' for s, m, _ in per_seed) +
            f'. Spread of the seed means: effective weeks sd {np.std(seed_means["effective_weeks"]):.2f}, '
            f'first failed week sd {np.std(seed_means["failure_week"]):.2f}.']

        # Paired on the same evaluation episodes: agent (mean of its training seeds) minus a baseline
        lines += ['', 'Agent minus baseline on the same episodes (mean difference, 95% bootstrap interval; '
                      'positive = the agent is better, except mean burden where negative is better):', '',
                  '| Against | Effective weeks | First failed week | Mean burden | Total reward |',
                  '| --- | --- | --- | --- | --- |']
        pols = baselines(env)
        rng = np.random.default_rng(0)
        for name in ('lowest resistance (greedy)', 'cycle every week', 'always imipenem'):
            base = [run_episode(env, pols[name], e) for e in EVAL_SEEDS]
            cells = []
            for key in ('effective_weeks', 'failure_week', 'mean_burden', 'reward'):
                agent_v = np.mean([[ep[key] for ep in episodes[s]] for s in TRAIN_SEEDS], axis=0)
                d = agent_v - np.array([b[key] for b in base], dtype=float)
                boots = [rng.choice(d, len(d)).mean() for _ in range(2000)]
                lo, hi = np.percentile(boots, [2.5, 97.5])
                digits = 3 if key == 'mean_burden' else 1
                cells.append(f'{d.mean():+.{digits}f} [{lo:+.{digits}f} to {hi:+.{digits}f}]')
            lines.append(f'| {name} | ' + ' | '.join(cells) + ' |')

        if decay == SERVED_DECAY:
            seed, m, _ = max(per_seed, key=lambda p: p[2])   # chosen on CHECK_SEEDS, not the evaluation
            metrics = {k: round(m[k][0], 3) for k in ('effective_weeks', 'failure_week', 'reward', 'mean_burden')}
            served = (models[seed], decay, seed, metrics)

    model, decay, seed, metrics = served
    agree = export(model, decay, seed, metrics)
    lines += ['', f'Served on `/api/timeline/` (`rl` block): the decay {decay:.0%} agent from training seed {seed}, '
              f'picked on separate check episodes; its numpy copy picks the same drug as stable-baselines3 '
              f'on {agree:.1%} of 2,000 random states.']

    with open(os.path.join(RESULTS, 'rl_agent.md'), 'w') as fh:
        fh.write('\n'.join(lines) + '\n')
    with open(os.path.join(RESULTS, 'rl_agent.csv'), 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
