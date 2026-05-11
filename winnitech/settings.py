"""
Django settings for Winneba Technical Institute Staff Management System
"""
import logging
import os
from pathlib import Path

_logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Read SECRET_KEY from env, fallback for local dev
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-winnitech-staff-system-2026-secure-key-ghana'
)

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'winnitech.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.admin_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'winnitech.wsgi.application'
ASGI_APPLICATION = 'winnitech.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Database — use DATABASE_URL env var on Render, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# No password validators — admin sets passwords directly
AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Accra'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ── Cloudinary for persistent media storage on Render ────────────────────────
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
if CLOUDINARY_URL and not CLOUDINARY_URL.startswith('cloudinary://'):
    _logger.warning(
        'CLOUDINARY_URL is set but does not start with cloudinary:// — '
        'uploads will use local disk (ephemeral on many hosts; set a valid URL).'
    )
if CLOUDINARY_URL and CLOUDINARY_URL.startswith('cloudinary://'):
    try:
        import cloudinary
        cloudinary.config(cloudinary_url=CLOUDINARY_URL)
        DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
        INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']
    except Exception as exc:
        _logger.exception(
            'Cloudinary failed to load; using local MEDIA_ROOT for uploads (%s). '
            'Fix CLOUDINARY_URL / install cloudinary packages.',
            exc,
        )

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SCHOOL_START_TIME = '07:00'
SCHOOL_END_TIME = '15:30'

# CSRF trusted origins for Render deployment
CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://winnetech.onrender.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
