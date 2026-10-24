"""The `rl` block of /api/timeline/ (format section 4): the trained RL agent
against the fixed baselines, sent when the agent was trained with the drug.

    python -m unittest discover -s backend/tests
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.core.cache import cache  # noqa: E402
from django.test import Client  # noqa: E402

from ml_models import rl_agent  # noqa: E402

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVED = os.path.join(BACKEND, 'trained_models')
FASTA = '>test\n' + 'ATGCGTACGTTAGCCGATCGATCGGCTAGCTAGGCTTACG' * 20


def post(**body):
    return Client().post('/api/timeline/', data=json.dumps(body), content_type='application/json')


@unittest.skipUnless(os.path.exists(os.path.join(SERVED, 'rl_agent', 'policy.npz')), 'no RL agent trained')
class RLBlock(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def test_sent_for_a_drug_the_agent_knows(self):
        r = post(fasta_text=FASTA, antibiotic='ciprofloxacin', n_weeks=12)
        self.assertEqual(r.status_code, 200)
        rl = r.json()['rl']
        self.assertEqual(rl['drugs'][0], 'ciprofloxacin')
        self.assertEqual(rl['n_weeks'], 12)
        self.assertEqual(rl['policies'][0]['name'], 'rl')
        names = [p['name'] for p in rl['policies']]
        self.assertIn('always_ciprofloxacin', names)
        self.assertIn(rl['best'], names)
        for p in rl['policies']:
            self.assertEqual(len(p['policy']), 12)
            for series in p['resistant_fraction'].values():
                self.assertEqual(len(series), 13)
                self.assertTrue(all(0 <= v <= 100 for v in series))

    def test_absent_for_other_drugs(self):
        r = post(fasta_text=FASTA, antibiotic='ampicillin', n_weeks=12)
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('rl', r.json())

    def test_same_request_same_block(self):
        a = post(fasta_text=FASTA, antibiotic='imipenem', n_weeks=20).json()['rl']
        cache.clear()
        b = post(fasta_text=FASTA, antibiotic='imipenem', n_weeks=20).json()['rl']
        self.assertEqual(a, b)

    def test_simulation_not_reported_as_trained(self):
        r = Client().get('/api/health/')
        self.assertFalse(r.json()['models']['mutation_timeline']['trained'])


class Loading(unittest.TestCase):
    def test_missing_folder_means_no_agent(self):
        self.assertIsNone(rl_agent.load('/nonexistent'))


if __name__ == '__main__':
    unittest.main()
