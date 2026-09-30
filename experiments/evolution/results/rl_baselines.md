# RL environment: baseline policies

Drugs ciprofloxacin, gentamicin, imipenem; horizon 104 weeks. A week's treatment fails when the drug given is at 50% resistance or more. First failed week: the first such week (105 = none). Effective weeks: weeks the drug given was under 50%, out of 104. Burden: resistant share of the drug given, averaged over the weeks. 100 episodes each (seeds 1000 on), mean and 2.5 to 97.5 percentile. Built by `experiments/evolution/rl_env.py`.

## Fitness cost: resistance falls 0% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 36.5 [31.5 to 41.5] | 21.9 [16.0 to 28.0] | 0.570 | -61.4 [-64.9 to -58.2] |
| cycle every 4 weeks | 36.5 [30.5 to 41.0] | 18.3 [14.0 to 26.0] | 0.573 | -61.8 [-65.2 to -58.6] |
| lowest resistance (greedy) | 36.6 [31.0 to 41.0] | 37.6 [32.0 to 42.0] | 0.492 | -53.0 [-56.0 to -50.1] |

## Fitness cost: resistance falls 2% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 56.6 [53.0 to 61.0] | 25.0 [19.0 to 32.6] | 0.470 | -52.7 [-56.2 to -49.6] |
| cycle every 4 weeks | 53.4 [49.0 to 58.0] | 20.8 [15.0 to 27.0] | 0.475 | -53.2 [-56.7 to -50.2] |
| lowest resistance (greedy) | 48.0 [41.0 to 54.0] | 48.7 [41.5 to 55.0] | 0.427 | -48.0 [-51.4 to -44.8] |

## Fitness cost: resistance falls 5% a week when a drug is not used

| Policy | Effective weeks | First failed week | Mean burden | Total reward |
| --- | --- | --- | --- | --- |
| always ciprofloxacin | 7.0 [5.0 to 9.0] | 8.0 [6.0 to 10.0] | 0.861 | -90.4 [-91.6 to -88.5] |
| always gentamicin | 11.3 [9.0 to 14.0] | 12.3 [10.0 to 15.0] | 0.684 | -71.8 [-73.3 to -69.6] |
| always imipenem | 18.2 [15.0 to 23.0] | 19.2 [16.0 to 24.0] | 0.571 | -59.9 [-61.8 to -57.2] |
| cycle every week | 79.5 [77.0 to 83.0] | 32.6 [25.0 to 43.0] | 0.333 | -39.7 [-43.1 to -36.6] |
| cycle every 4 weeks | 74.5 [70.0 to 78.5] | 23.9 [16.0 to 28.0] | 0.341 | -40.5 [-43.8 to -37.4] |
| lowest resistance (greedy) | 104.0 [104.0 to 104.0] | 105.0 [105.0 to 105.0] | 0.299 | -35.8 [-39.4 to -32.6] |
