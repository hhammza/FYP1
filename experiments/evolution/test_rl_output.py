"""The `rl` block for /api/timeline/ follows progress/formats/README.md §4.

    python -m unittest experiments/evolution/test_rl_output.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rl_env  # noqa: E402
from rl_output import pick_best, rl_block  # noqa: E402

WEEKS = 30


class RlBlock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.block = rl_block('ciprofloxacin', WEEKS, seed=7)
        cls.by_name = {p['name']: p for p in cls.block['policies']}

    def test_shape_follows_section_4(self):
        b = self.block
        self.assertEqual(b['drugs'][0], 'ciprofloxacin')              # requested drug first
        self.assertEqual(b['n_weeks'], WEEKS)
        self.assertIn('always_ciprofloxacin', self.by_name)
        self.assertIn(b['best'], self.by_name)
        for p in b['policies']:
            self.assertEqual(len(p['policy']), WEEKS)
            self.assertEqual(sorted(p['resistant_fraction']), sorted(b['drugs']))
            for series in p['resistant_fraction'].values():
                self.assertEqual(len(series), WEEKS + 1)               # week 0 to n_weeks

    def test_resistance_is_percent(self):
        values = [v for p in self.block['policies'] for s in p['resistant_fraction'].values() for v in s]
        self.assertTrue(all(0 <= v <= 100 for v in values))
        self.assertGreater(max(values), 1)                             # not a 0-1 share

    def test_never_failing_is_null(self):
        short = rl_block('ciprofloxacin', 2, seed=7)                    # too short to reach 50%
        self.assertTrue(all(p['failure_week'] is None for p in short['policies']))
        self.assertIsInstance(self.by_name['always_ciprofloxacin']['failure_week'], int)

    def test_same_numbers_as_rl_env(self):
        env = rl_env.CyclingEnv(drugs=self.block['drugs'], weeks=WEEKS)
        for name, pol in (('always_ciprofloxacin', rl_env.always(0)), ('cycle', rl_env.cycle(1)),
                          ('lowest_resistance', rl_env.lowest_resistance)):
            ref = rl_env.run_episode(env, pol, 7)
            got = self.by_name[name]
            self.assertEqual(got['effective_weeks'], ref['effective_weeks'], name)
            self.assertAlmostEqual(got['mean_burden'], ref['mean_burden'] * 100, delta=0.05)
            self.assertEqual(got['failure_week'], ref['failure_week'] if ref['failed'] else None)
            self.assertAlmostEqual(got['total_reward'], ref['reward'], delta=0.005)

    def test_same_seed_same_block(self):
        self.assertEqual(rl_block('ciprofloxacin', WEEKS, seed=7), self.block)

    def test_unknown_drug_means_no_rl_block(self):
        self.assertIsNone(rl_block('ampicillin', WEEKS))

    def test_a_trained_agent_comes_first(self):
        b = rl_block('gentamicin', 12, agent=('PPO (stable-baselines3)', rl_env.lowest_resistance))
        self.assertEqual(b['policies'][0]['name'], 'rl')
        self.assertEqual(b['agent'], 'PPO (stable-baselines3)')

    def test_tie_rule(self):
        p = lambda n, fw, r: {'name': n, 'failure_week': fw, 'total_reward': r}
        self.assertEqual(pick_best([p('a', 10, -1), p('b', None, -9)]), 'b')     # null is latest
        self.assertEqual(pick_best([p('a', 10, -5), p('b', 10, -2)]), 'b')       # then reward
        self.assertEqual(pick_best([p('rl', 10, -2), p('b', 10, -2)]), 'rl')     # then first listed


if __name__ == '__main__':
    unittest.main()
