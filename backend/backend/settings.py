import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

from django.core.exceptions import ImproperlyConfigured


def env_list(name):
    return [v.strip() for v in os.environ.get(name, '').split(',') if v.strip()]


# Local development: start.bat / start.sh set DEBUG=True. Production (Railway)
# leaves DEBUG unset, so it is False, and must set SECRET_KEY and ALLOWED_HOSTS.
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# No default key is committed. With DEBUG on and no key, a random one is made
# per process: the API keeps no sessions or signed cookies, so nothing breaks.
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('SECRET_KEY must be set when DEBUG is False.')
    from django.core.management.utils import get_random_secret_key
    SECRET_KEY = get_random_secret_key()

# Comma-separated host names this API answers to, e.g. the Railway domain.
# With DEBUG on and none set, Django allows localhost, 127.0.0.1 and [::1].
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS')
if not ALLOWED_HOSTS and not DEBUG:
    raise ImproperlyConfigured('ALLOWED_HOSTS must be set when DEBUG is False.')

# Token for /api/train/ and /api/reload/, sent as the X-Admin-Token header.
# Unset = those endpoints are switched off (503), not open.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': ['django.template.context_processors.request']},
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# No database: the API is stateless and stores no user data.
DATABASES = {}

# Per-process cache, used only for the rate-limit counters.
CACHES = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Browsers never call this API directly: the Flask frontend calls it from
# its server. So no cross-origin access is needed; list origins here only if a
# page ever fetches the API from the browser.
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS')

# Uploads. A FASTA over MAX_FASTA_BYTES is refused with 413 before it is read.
MAX_FASTA_BYTES = 20 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_FASTA_BYTES + 1024 * 1024   # pasted FASTA arrives as JSON
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024                 # larger files spool to disk

# Requests per client IP (per worker process) on the prediction endpoints.
# RATELIMIT_ENABLE=False switches them off, e.g. for a load test.
RATELIMIT_ENABLE = os.environ.get('RATELIMIT_ENABLE', 'True') == 'True'
RATE_LIMITS = {'forecast': '60/m', 'predict': '10/m', 'timeline': '10/m'}

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser', 'rest_framework.parsers.MultiPartParser'],
}

# ML Model paths
TRAINED_MODELS_DIR = BASE_DIR / 'trained_models'
# /api/train/ writes here, never over the served model. A candidate reaches
# TRAINED_MODELS_DIR only through experiments/promote.py, which also writes
# its threshold, calibration and metrics.json.
CANDIDATE_MODELS_DIR = TRAINED_MODELS_DIR / 'candidates'
DATA_DIR = BASE_DIR.parent  # FYP1 root

AMR_OUTPUT_DIR   = DATA_DIR / 'amr_output'
MAPPED_OUTPUT_DIR = DATA_DIR / 'mapped_output'
FASTA_OUTPUT_DIR  = DATA_DIR / 'fasta_output'
SAMPLE_MAPPED_DIR = DATA_DIR / 'sample_mapped_output'
SAMPLE_FASTA_DIR  = DATA_DIR / 'sample_fasta_output'
