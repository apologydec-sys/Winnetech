"""
Django settings for Winneba Technical Institute Staff Management System.
Configured for local development and deployment on Render.
"""

import logging
import os
from pathlib import Path

import dj_database_url

_logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-winnitech-staff-system-local-dev-only",
)

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "ALLOWED_HOSTS",
        ".onrender.com,localhost,127.0.0.1",
    ).split(",")
    if host.strip()
]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    "daphne",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Channels
    "channels",

    # Forms
    "crispy_forms",
    "crispy_bootstrap5",
    "widget_tweaks",

    # Project apps
    "core",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",

    # WhiteNoise for static files on Render
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL / WSGI / ASGI
# ============================================================

ROOT_URLCONF = "winnitech.urls"

WSGI_APPLICATION = "winnitech.wsgi.application"
ASGI_APPLICATION = "winnitech.asgi.application"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",

                # Custom context processors
                "core.context_processors.admin_context",
                "core.context_processors.teacher_portal_context",
            ],
        },
    },
]


# ============================================================
# CHANNELS
# ============================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


# ============================================================
# DATABASE
# ============================================================
#
# Render:
#   DATABASE_URL = PostgreSQL connection string
#
# Local:
#   SQLite database
#

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = []


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Accra"

USE_I18N = True
USE_TZ = True


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise
STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# CLOUDINARY
# ============================================================
#
# Render's filesystem is ephemeral, so Cloudinary is recommended
# for uploaded teacher profile pictures and other media.
#
# Set this environment variable on Render:
#
# CLOUDINARY_URL=cloudinary://...
#

CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "").strip()

if CLOUDINARY_URL:
    if not CLOUDINARY_URL.startswith("cloudinary://"):
        _logger.warning(
            "CLOUDINARY_URL is set but does not start with "
            "'cloudinary://'. Cloudinary storage will not be enabled."
        )
    else:
        try:
            import cloudinary

            cloudinary.config(
                cloudinary_url=CLOUDINARY_URL
            )

            INSTALLED_APPS += [
                "cloudinary_storage",
                "cloudinary",
            ]

            DEFAULT_FILE_STORAGE = (
                "cloudinary_storage.storage.MediaCloudinaryStorage"
            )

        except Exception as exc:
            _logger.exception(
                "Cloudinary failed to initialize: %s",
                exc,
            )


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# CRISPY FORMS
# ============================================================

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# ============================================================
# AUTHENTICATION
# ============================================================

LOGIN_URL = "/login/"

LOGIN_REDIRECT_URL = "/"

LOGOUT_REDIRECT_URL = "/"


# ============================================================
# SCHOOL SETTINGS
# ============================================================

SCHOOL_START_TIME = "07:00"
SCHOOL_END_TIME = "15:30"


# ============================================================
# CSRF
# ============================================================
#
# IMPORTANT:
# These must be normal strings, NOT Markdown links.
#

CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://winnetech.onrender.com",

    # Local development
    "http://localhost:8000",
    "https://localhost:8000",
    "http://127.0.0.1:8000",
    "https://127.0.0.1:8000",
    "http://0.0.0.0:8000",
    "https://0.0.0.0:8000",
]

# Allow additional Render/custom domains through environment variable
CSRF_TRUSTED_ORIGINS += [
    origin.strip()
    for origin in os.environ.get(
        "CSRF_TRUSTED_ORIGINS",
        "",
    ).split(",")
    if origin.strip()
]


# ============================================================
# RENDER / HTTPS
# ============================================================

# Render terminates HTTPS before forwarding requests to Django.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)


# Only enable these production protections when DEBUG=False.
if not DEBUG:

    # Browser should only access the site over HTTPS
    SECURE_SSL_REDIRECT = True

    # Secure cookies
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Prevent browsers from MIME-sniffing responses
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # Clickjacking protection
    X_FRAME_OPTIONS = "DENY"

    # HSTS
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = False


# ============================================================
# LOGGING
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {name}: {message}",
            "style": "{",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },

    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },

    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}