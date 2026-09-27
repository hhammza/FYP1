"""Django configured as production runs it (DEBUG off), for every API test.

Imported first by each test module that needs Django. Django reads its
settings once, so every module must use the same values: whichever loads
first decides for the whole run.
"""
import os
import sys

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
