from pathlib import Path
from decouple import config
import dj_database_url
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

def _env_bool(value, default=False):
    """
    Parse truthy/falsey env values without raising.

    python-decouple's built-in bool casting throws on unexpected values (e.g. "release").
    """
    if value is None:
        return default
    s = str(value).strip().lower()
    if s in {'1', 'true', 't', 'yes', 'y', 'on'}:
        return True
    if s in {'0', 'false', 'f', 'no', 'n', 'off', ''}:
        return False
    # Common non-bool deployment markers.
    if s in {'release', 'prod', 'production'}:
        return False
    return default

SECRET_KEY = config('SECRET_KEY', default='django-insecure-a6=m0&%y@5dlj1fynp^=)p*!o22ci%s!=o!wgn0v4k&3rv35!m')
DEBUG = _env_bool(config('DEBUG', default='true'), default=True)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'auth_app',
    'crm',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

AUTH_USER_MODEL = 'auth_app.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── DRF ──
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
}

# ── JWT ──
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
}

# ── CORS ──
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173',
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ── GHL Scheduler (APScheduler) ──
# Auto-sync runs every 60 minutes via management command or APScheduler
SCHEDULER_ENABLED = config('SCHEDULER_ENABLED', default=False, cast=bool)

# ── GHL Webhook Secret (optional) ──
GHL_WEBHOOK_SECRET = config('GHL_WEBHOOK_SECRET', default='')

SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
EMAIL_USE_TLS = _env_bool(config('EMAIL_USE_TLS', default='true'), default=True)
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
