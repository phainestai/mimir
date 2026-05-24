"""
Base Django settings for mimir project.

Common settings shared across all environments (dev, test, prod).
Environment-specific overrides in dev.py, test.py, prod.py.
"""

import logging
import os
from pathlib import Path

from django.contrib.messages import constants as message_constants

logger = logging.getLogger(__name__)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Bug reports → GitHub Issues (UI offcanvas + MCP `report_bug` / HTTP facade).
#   GITHUB_TOKEN — PAT or fine-grained token with **Issues: write** on GITHUB_BUG_REPO.
#   GITHUB_BUG_REPO — "owner/repo"; default phainestai/mimir.
#   BUG_REPORT_DRY_RUN — if "1"/"true"/"yes", skip PyGithub (placeholder issue URL).
# See README and docs/architecture/SAO.md for production / Elastic Beanstalk setup.
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "").strip()
GITHUB_BUG_REPO = os.environ.get("GITHUB_BUG_REPO", "phainestai/mimir").strip()
BUG_REPORT_DRY_RUN = os.environ.get("BUG_REPORT_DRY_RUN", "").lower() in (
    "1",
    "true",
    "yes",
)


def _installed_apps() -> list[str]:
    """Return INSTALLED_APPS; register django_ses only if the package is present."""

    third_party = [
        "rest_framework",
        "rest_framework.authtoken",
    ]
    try:
        import django_ses  # noqa: F401
    except ImportError:
        logger.warning(
            "django_ses is not installed; SES email backend is unavailable. "
            "Run: pip install -r requirements.txt"
        )
    else:
        third_party.append("django_ses")

    return (
        [
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
            "django.contrib.staticfiles",
        ]
        + third_party
        + [
            # Mimir apps
            "accounts",
            "methodology",
            "mcp_integration",
        ]
    )


# Application definition
INSTALLED_APPS = _installed_apps()

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware for request ID tracking
    "mimir.middleware.RequestIDMiddleware",
]

ROOT_URLCONF = "mimir.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "methodology.context_processors.app_version",
                "methodology.context_processors.pip_nav",
                "methodology.context_processors.primary_nav_section",
            ],
        },
    },
]

WSGI_APPLICATION = "mimir.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Galdr AI review worker
GALDR_MODEL = os.environ.get("GALDR_MODEL", "claude-sonnet-4-20250514")
GALDR_USE_ANTHROPIC = bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@mimir.local")

# Galdr MVP: use synchronous assessments in tests only (sqlite + threads are flaky).
GALDR_EAGER = False

# Authentication settings
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth

LOGIN_URL = "/auth/user/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/auth/user/login/"

# Session settings
# https://docs.djangoproject.com/en/5.2/ref/settings/#sessions

SESSION_COOKIE_AGE = 1209600  # 2 weeks (default)
SESSION_SAVE_EVERY_REQUEST = True  # Refresh session on each request
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection

# Django REST Framework settings
# https://www.django-rest-framework.org/api-guide/settings/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Disable in prod
    ],
    'EXCEPTION_HANDLER': 'methodology.api.exceptions.custom_exception_handler',
}

# Django messages → Bootstrap alert classes (alert-danger, not alert-error).
MESSAGE_TAGS = {message_constants.ERROR: 'danger'}
