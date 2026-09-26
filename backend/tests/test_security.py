"""Security settings and checks of the API (T2.4).

    python -m unittest discover -s backend/tests

Runs the API as production would (DEBUG off), with a test SECRET_KEY,
ALLOWED_HOSTS and ADMIN_TOKEN. Loading the models takes a few seconds.
"""
import json
import os
import subprocess
import sys
import unittest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

TOKEN = 'test-admin-token'
os.environ.update({
    'DJANGO_SETTINGS_MODULE': 'backend.settings',
    'DEBUG': 'False',
    'SECRET_KEY': 'test-only-secret-key',
    'ALLOWED_HOSTS': 'testserver',
    'ADMIN_TOKEN': TOKEN,
})

import django  # noqa: E402
django.setup()

from django.core.cache import cache  # noqa: E402
from django.test import Client, override_settings  # noqa: E402
from django.conf import settings  # noqa: E402


def run_check(env):
    """`manage.py check` in a fresh process with only the given settings."""
    clean = {k: v for k, v in os.environ.items()
             if k not in ('DEBUG', 'SECRET_KEY', 'ALLOWED_HOSTS', 'ADMIN_TOKEN')}
    clean.update(env)
    return subprocess.run([sys.executable, 'manage.py', 'check'], cwd=BACKEND, env=clean,
                          capture_output=True, text=True, timeout=300)


class Secrets(unittest.TestCase):
    def test_production_needs_a_secret_key(self):
        r = run_check({})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('SECRET_KEY must be set', r.stderr)

    def test_production_needs_allowed_hosts(self):
        r = run_check({'SECRET_KEY': 'x'})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn('ALLOWED_HOSTS must be set', r.stderr)

    def test_development_runs_without_secrets(self):
        r = run_check({'DEBUG': 'True'})
        self.assertEqual(r.returncode, 0, r.stderr[-500:])

    def test_no_wildcard_host_and_no_open_cors(self):
        self.assertNotIn('*', settings.ALLOWED_HOSTS)
        self.assertFalse(getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False))
        r = Client().get('/api/health/', HTTP_ORIGIN='https://evil.example')
        self.assertNotIn('Access-Control-Allow-Origin', r.headers)

    def test_unknown_host_is_refused(self):
        self.assertEqual(Client().get('/api/health/', HTTP_HOST='evil.example').status_code, 400)


class AdminToken(unittest.TestCase):
    def post(self, path, token=None, body=None):
        headers = {'HTTP_X_ADMIN_TOKEN': token} if token is not None else {}
        return Client().post(path, data=json.dumps(body or {}), content_type='application/json', **headers)

    def test_train_and_reload_without_token_are_401(self):
        for path in ('/api/train/', '/api/reload/'):
            self.assertEqual(self.post(path).status_code, 401, path)
            self.assertEqual(self.post(path, token='wrong').status_code, 401, path)

    def test_reload_with_token_is_200(self):
        self.assertEqual(self.post('/api/reload/', token=TOKEN).status_code, 200)

    def test_train_rejects_an_unknown_model_name(self):
        r = self.post('/api/train/', token=TOKEN, body={'model': '../../elsewhere'})
        self.assertEqual(r.status_code, 400)

    @override_settings(ADMIN_TOKEN='')
    def test_no_token_configured_switches_admin_off(self):
        for path in ('/api/train/', '/api/reload/'):
            self.assertEqual(self.post(path, token='anything').status_code, 503, path)


class UploadSize(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def test_pasted_fasta_over_the_limit_is_413(self):
        fasta = '>big\n' + 'A' * settings.MAX_FASTA_BYTES
        for path in ('/api/predict/', '/api/timeline/'):
            r = Client().post(path, data=json.dumps({'fasta_text': fasta, 'antibiotic': 'ampicillin'}),
                              content_type='application/json')
            self.assertEqual(r.status_code, 413, path)

    def test_body_over_the_limit_is_413_before_reading(self):
        body = json.dumps({'fasta_text': 'A' * (settings.DATA_UPLOAD_MAX_MEMORY_SIZE + 10)})
        r = Client().post('/api/predict/', data=body, content_type='application/json')
        self.assertEqual(r.status_code, 413)

    def test_uploaded_file_over_the_limit_is_413(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        big = SimpleUploadedFile('big.fasta', b'>x\n' + b'A' * (settings.MAX_FASTA_BYTES + 1))
        r = Client().post('/api/predict/', data={'fasta_file': big, 'antibiotic': 'ampicillin'})
        self.assertEqual(r.status_code, 413)


class RateLimit(unittest.TestCase):
    def setUp(self):
        cache.clear()

    @override_settings(RATE_LIMITS={'forecast': '2/m', 'predict': '2/m', 'timeline': '2/m'})
    def test_forecast_is_limited_per_ip(self):
        def forecast(ip):
            return Client().post('/api/forecast/', data=json.dumps({'antibiotic': 'ciprofloxacin'}),
                                 content_type='application/json', HTTP_X_FORWARDED_FOR=ip).status_code
        self.assertEqual([forecast('10.0.0.1') for _ in range(3)], [200, 200, 429])
        self.assertEqual(forecast('10.0.0.2'), 200)   # another visitor is not affected


if __name__ == '__main__':
    unittest.main()
