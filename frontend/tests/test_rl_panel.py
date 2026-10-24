"""The RL panel on /timeline (format §4, "RL panel"): hidden until the
response has `rl`, labelled as a simulation, every policy compared.

    python -m unittest discover -s frontend/tests

Needs no backend: the page is rendered from the agreed sample.
"""
import copy
import json
import os
import re
import sys
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
os.environ.pop('PORT', None)
import app  # noqa: E402

with open(os.path.join(HERE, '..', '..', 'progress', 'formats', 'timeline_response.sample.json'), encoding='utf-8') as fh:
    SAMPLE = json.load(fh)
SAMPLE.pop('_comment', None)


def render(result):
    with app.app.test_request_context('/timeline'), mock.patch.object(app, 'model_health', return_value={}):
        return app.render_template('mutation_timeline.html', result=result, error=None,
                                   form_data={'antibiotic': result.get('antibiotic', ''), 'n_weeks': '4'})


def panel(h):
    m = re.search(r'id="rlPanel".*?</table>', h, re.S)
    return m.group(0) if m else ''


class RlPanel(unittest.TestCase):
    def test_hidden_without_rl(self):
        h = render({k: v for k, v in SAMPLE.items() if k != 'rl'})
        self.assertNotIn('id="rlPanel"', h)
        self.assertNotIn('id="rl-data"', h)

    def test_labelled_as_a_simulation(self):
        self.assertIn('Simulation + RL policy <span class="text-muted fw-normal">(not trained on patient data)</span>',
                      render(SAMPLE))

    def test_every_policy_compared_best_marked(self):
        p = panel(render(SAMPLE))
        for policy in SAMPLE['rl']['policies']:
            self.assertIn(policy['label'], p)
        best = next(x for x in SAMPLE['rl']['policies'] if x['name'] == SAMPLE['rl']['best'])
        self.assertRegex(p, rf'report-best-row">\s*<td class="small">{re.escape(best["label"])} <span class="status-badge')
        self.assertIn('Never in 4 weeks', p)                              # failure_week null
        self.assertIn('Week 4', p)
        self.assertIn('PPO (stable-baselines3)', render(SAMPLE))

    def test_optional_measures_shown_when_sent(self):
        r = copy.deepcopy(SAMPLE)
        r['rl']['policies'][0].update(effective_weeks=4, mean_burden=3.6)
        p = panel(render(r))
        self.assertIn('4 / 4', p)
        self.assertIn('3.6%', p)
        self.assertIn('—', panel(render(SAMPLE)))                          # absent in the sample: a dash

    def test_chart_data_is_the_rl_block(self):
        h = render(SAMPLE)
        data = json.loads(re.search(r'id="rl-data">(.*?)</script>', h, re.S).group(1))
        self.assertEqual(data, SAMPLE['rl'])

    def test_baselines_only_without_an_agent(self):
        r = copy.deepcopy(SAMPLE)
        r['rl']['agent'] = None
        r['rl']['policies'] = r['rl']['policies'][1:]
        r['rl']['best'] = 'cycle'
        h = render(r)
        self.assertIn('fixed baselines', h)
        self.assertNotIn('RL agent', panel(h))


class SamplePreview(unittest.TestCase):
    def test_local_preview(self):
        with mock.patch.object(app, 'model_health', return_value={}):
            r = app.app.test_client().get('/timeline/sample')
        h = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn('Sample response, not a real simulation.', h)
        self.assertIn('id="rlPanel"', h)

    def test_not_on_the_deployed_site(self):
        with mock.patch.dict(os.environ, {'PORT': '8080'}), mock.patch.object(app, 'model_health', return_value={}):
            r = app.app.test_client().get('/timeline/sample')
        self.assertEqual(r.status_code, 404)


if __name__ == '__main__':
    unittest.main()
