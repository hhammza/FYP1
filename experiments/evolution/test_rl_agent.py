"""The backend's copy of the RL agent and environment gives the same `rl` block
as the experiment code that trained it.

backend/ml_models/rl_agent.py runs without gymnasium and torch, so it keeps a
numpy copy of rl_env.CyclingEnv and of the PPO policy network. These tests run
both sides on the same seeds and compare the blocks number for number.

    python -m unittest experiments/evolution/test_rl_agent.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'backend'))
from rl_output import rl_block  # noqa: E402
from ml_models import rl_agent  # noqa: E402

MODEL_DIR = os.path.join(ROOT, 'backend', 'trained_models')


@unittest.skipUnless(os.path.exists(os.path.join(MODEL_DIR, 'rl_agent', 'policy.npz')),
                     'no trained agent: run experiments/evolution/rl_train.py')
class BackendMatchesExperiment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = rl_agent.load(MODEL_DIR)

    def test_same_block_for_every_drug_window_and_seed(self):
        a = self.agent
        for drug in a.drugs:
            order = [drug] + [d for d in a.drugs if d != drug]
            for weeks in (1, 8, 26, 52):
                for seed in (42, 7):
                    with self.subTest(drug=drug, weeks=weeks, seed=seed):
                        expected = rl_block(drug, weeks, seed=seed, decay=a.decay,
                                            agent=(a.label, a.policy_for(order)))
                        self.assertEqual(a.block(drug, weeks, seed=seed), expected)

    def test_agent_listed_first_and_named(self):
        b = self.agent.block(self.agent.drugs[0], 12)
        self.assertEqual(b['policies'][0]['name'], 'rl')
        self.assertEqual(b['agent'], 'PPO (stable-baselines3)')

    def test_no_block_for_a_drug_it_was_not_trained_with(self):
        self.assertIsNone(self.agent.block('ampicillin', 12))

    def test_order_does_not_change_the_agent_s_choice(self):
        """The agent picks the same drug whichever drug the request puts first."""
        a = self.agent
        import numpy as np
        rng = np.random.default_rng(0)
        for _ in range(200):
            r = dict(zip(a.drugs, rng.uniform(0, 0.9, len(a.drugs))))
            t = int(rng.integers(0, 52))
            picks = set()
            for first in a.drugs:
                order = [first] + [d for d in a.drugs if d != first]
                obs = np.append([r[d] for d in order], 0.0).astype(np.float32)
                picks.add(order[a.policy_for(order)(obs, t)])
            self.assertEqual(len(picks), 1)


if __name__ == '__main__':
    unittest.main()
