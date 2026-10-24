# RL agent: PPO against the baselines

Environment `rl_env.CyclingEnv`: drugs ciprofloxacin, gentamicin, imipenem, horizon 104 weeks, a week fails when the drug given starts the week at 50% resistance or more. PPO (stable-baselines3, MLP 64-64, 300,000 steps, 8 parallel environments) trained from 3 seeds per fitness cost. Every policy is evaluated on the same 100 episodes (seeds 1000 on, never used in training); the agent picks its most likely drug each week. Mean and 2.5 to 97.5 percentile over the evaluation episodes; for the agent, the three training seeds are pooled (300 episodes), and the spread of the per-seed means is given separately. Built by `experiments/evolution/rl_train.py`.

## Fitness cost: resistance falls 0% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| **PPO agent** | 35.8 [31.0 to 41.0] | 35.4 [30.0 to 40.0] | 0.496 | -53.1 [-56.3 to -50.2] |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 36.5 [31.5 to 41.5] | 21.9 [16.0 to 28.0] | 0.570 | -61.4 [-64.9 to -58.2] |
| cycle every 4 weeks | 36.5 [30.5 to 41.0] | 18.3 [14.0 to 26.0] | 0.573 | -61.8 [-65.2 to -58.6] |
| lowest resistance (greedy) | 36.6 [31.0 to 41.0] | 37.6 [32.0 to 42.0] | 0.492 | -53.0 [-56.0 to -50.1] |

Per training seed (mean over the evaluation episodes): seed 0: effective 35.3, first failed 34.6, reward -53.2; seed 1: effective 35.8, first failed 35.0, reward -53.1; seed 2: effective 36.5, first failed 36.4, reward -53.0. Spread of the seed means: effective weeks sd 0.47, first failed week sd 0.77.

Agent minus baseline on the same episodes (mean difference, 95% bootstrap interval; positive = the agent is better, except mean burden where negative is better):

| Against | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| lowest resistance (greedy) | -0.7 [-0.9 to -0.6] | -2.2 [-2.3 to -2.1] | +0.004 [+0.004 to +0.004] | -0.1 [-0.1 to -0.1] |
| cycle every week | -0.6 [-0.8 to -0.5] | +13.4 [+12.7 to +14.1] | -0.074 [-0.075 to -0.073] | +8.3 [+8.2 to +8.4] |
| always imipenem | +17.6 [+17.3 to +17.9] | +16.1 [+15.8 to +16.5] | -0.075 [-0.077 to -0.073] | +6.8 [+6.6 to +7.1] |

## Fitness cost: resistance falls 2% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| **PPO agent** | 49.3 [44.0 to 54.0] | 40.1 [34.0 to 46.0] | 0.438 | -47.9 [-51.3 to -44.7] |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 56.6 [53.0 to 61.0] | 25.0 [19.0 to 32.6] | 0.470 | -52.7 [-56.2 to -49.6] |
| cycle every 4 weeks | 53.4 [49.0 to 58.0] | 20.8 [15.0 to 27.0] | 0.475 | -53.2 [-56.7 to -50.2] |
| lowest resistance (greedy) | 48.0 [41.0 to 54.0] | 48.7 [41.5 to 55.0] | 0.427 | -48.0 [-51.4 to -44.8] |

Per training seed (mean over the evaluation episodes): seed 0: effective 48.9, first failed 40.1, reward -48.0; seed 1: effective 49.5, first failed 39.9, reward -47.8; seed 2: effective 49.4, first failed 40.4, reward -47.9. Spread of the seed means: effective weeks sd 0.28, first failed week sd 0.20.

Agent minus baseline on the same episodes (mean difference, 95% bootstrap interval; positive = the agent is better, except mean burden where negative is better):

| Against | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| lowest resistance (greedy) | +1.3 [+1.0 to +1.5] | -8.6 [-8.8 to -8.4] | +0.011 [+0.011 to +0.012] | +0.1 [+0.1 to +0.1] |
| cycle every week | -7.3 [-7.8 to -6.9] | +15.1 [+14.4 to +15.9] | -0.032 [-0.032 to -0.031] | +4.9 [+4.8 to +4.9] |
| always imipenem | +31.0 [+30.7 to +31.4] | +20.9 [+20.5 to +21.3] | -0.132 [-0.134 to -0.130] | +12.1 [+11.8 to +12.3] |

## Fitness cost: resistance falls 5% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| **PPO agent** | 95.0 [87.0 to 101.0] | 81.3 [68.0 to 94.0] | 0.300 | -35.3 [-38.9 to -32.1] |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 79.5 [77.0 to 83.0] | 32.6 [25.0 to 43.0] | 0.333 | -39.7 [-43.1 to -36.6] |
| cycle every 4 weeks | 74.5 [70.0 to 78.5] | 23.9 [16.0 to 28.0] | 0.341 | -40.5 [-43.8 to -37.4] |
| lowest resistance (greedy) | 104.0 [104.0 to 104.0] | 105.0 [105.0 to 105.0] | 0.299 | -35.8 [-39.4 to -32.6] |

Per training seed (mean over the evaluation episodes): seed 0: effective 92.5, first failed 77.1, reward -35.3; seed 1: effective 96.4, first failed 83.7, reward -35.3; seed 2: effective 96.1, first failed 83.2, reward -35.3. Spread of the seed means: effective weeks sd 1.77, first failed week sd 2.96.

Agent minus baseline on the same episodes (mean difference, 95% bootstrap interval; positive = the agent is better, except mean burden where negative is better):

| Against | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| lowest resistance (greedy) | -9.0 [-9.6 to -8.4] | -23.7 [-24.8 to -22.7] | +0.001 [+0.001 to +0.001] | +0.5 [+0.5 to +0.5] |
| cycle every week | +15.5 [+14.9 to +16.0] | +48.7 [+47.6 to +49.9] | -0.033 [-0.034 to -0.032] | +4.4 [+4.3 to +4.5] |
| always imipenem | +76.8 [+76.2 to +77.3] | +62.1 [+61.2 to +63.0] | -0.271 [-0.273 to -0.269] | +24.6 [+24.3 to +24.9] |

Served on `/api/timeline/` (`rl` block): the decay 5% agent from training seed 0, picked on separate check episodes; its numpy copy picks the same drug as stable-baselines3 on 100.0% of 2,000 random states.
