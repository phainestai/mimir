"""
Development settings for mimir project.

Optimized for local development with SQLite or Postgres.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from repo root if present (only affects runserver; docker compose handles this itself)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=False)

from .base import *  # noqa: F401, F403

# Environment identifier
MIMIR_ENV = 'dev'

# PIP wireframes and other static UI mockups at /mockups/
ENABLE_UI_MOCKUPS = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    "django-insecure-)t!u$2p(q=x4m54)-kh39ti_an3_(6%aej&p!#w3pcs(s&q0$="
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv(
    'DJANGO_ALLOWED_HOSTS',
    'localhost,127.0.0.1,0.0.0.0,testserver'
).split(',')

# Trust localhost for development (CSRF protection)
CSRF_TRUSTED_ORIGINS = os.getenv(
    'DJANGO_CSRF_TRUSTED_ORIGINS',
    'http://localhost:8000,http://127.0.0.1:8000,http://localhost:49819,http://127.0.0.1:49819'
).split(',')

# Session cookies (insecure for dev)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# If DATABASE_URL is set → use Postgres (via dj-database-url)
# Else → fall back to SQLite (current dev behavior)
database_url = os.getenv('DATABASE_URL')

if database_url:
    # Postgres via DATABASE_URL (e.g., postgresql://user:pass@host:5432/dbname)
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=database_url,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # SQLite fallback (preserves current local-dev behavior)
    # Support for volume-mounted database in Docker container
    db_path = os.getenv('MIMIR_DB_PATH')
    if db_path:
        # Use environment variable path (for Docker)
        database_path = Path(db_path)
    else:
        # Check if we're in containerized environment (data directory exists)
        data_dir = BASE_DIR / "data"  # noqa: F405
        if data_dir.exists():
            database_path = data_dir / "mimir.db"
        else:
            # Development fallback
            database_path = BASE_DIR / "mimir.db"  # noqa: F405

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": database_path,
        }
    }


# Logging configuration
# https://docs.djangoproject.com/en/5.2/topics/logging/

# Detect if we're running MCP server (needs clean stdio for JSON-RPC)
_IS_MCP_SERVER = os.environ.get('MIMIR_MCP_MODE') == '1'

# Choose handlers based on mode
_LOG_HANDLERS = ['file'] if _IS_MCP_SERVER else ['file', 'console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': (
                '[{asctime}] [{levelname:<8}] [REQ:{request_id}] [PID:{process}:TID:{thread}] '
                '[{pathname}:{lineno}] [{module}.{funcName}] '
                '{message}'
            ),
            'datefmt': '%Y-%m-%d %H:%M:%S',
            'style': '{',
        },
        'simple': {
            'format': '[REQ:{request_id}] {levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'request_id': {
            '()': 'mimir.logging_filters.RequestIDFilter',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'app.log',  # noqa: F405
            'mode': 'w',  # Overwrite on each restart
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'filters': ['request_id'],
        },
    },
    'root': {
        'handlers': _LOG_HANDLERS,
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'accounts': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'methodology': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
        'mcp_integration': {
            'handlers': _LOG_HANDLERS,
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Email — dev default: AWS SES (same as production). Opt out with USE_SES_IN_DEV=0
# to print messages to the runserver terminal instead (no inbox delivery).
# Requires AWS credentials locally (`aws login` needs botocore[crt] in requirements.txt).
# ─────────────────────────────────────────────────────────────────────────────
import logging as _logging

_email_log = _logging.getLogger("mimir.settings.dev")


def _env_flag(name: str, *, default: str = "1") -> bool:
    """Return True unless the env var is an explicit falsey token."""
    raw = os.getenv(name, default).strip().lower()
    return raw not in ("", "0", "false", "no", "off")


_USE_SES_IN_DEV = _env_flag("USE_SES_IN_DEV", default="1")

if _USE_SES_IN_DEV:
    EMAIL_BACKEND = "django_ses.SESBackend"
    AWS_SES_REGION_NAME = os.getenv("AWS_SES_REGION_NAME", "us-east-1")
    AWS_SES_REGION_ENDPOINT = f"email.{AWS_SES_REGION_NAME}.amazonaws.com"
    DEFAULT_FROM_EMAIL = os.getenv(
        "DEFAULT_FROM_EMAIL",
        "noreply@featurefactory.io",
    )
    _ses_cfg_set = os.getenv("AWS_SES_CONFIGURATION_SET", "mimir-transactional")
    if _ses_cfg_set:
        AWS_SES_CONFIGURATION_SET = _ses_cfg_set
    _email_log.info(
        "[EMAIL] Dev SES enabled: backend=%s from=%s region=%s config_set=%s",
        EMAIL_BACKEND,
        DEFAULT_FROM_EMAIL,
        AWS_SES_REGION_NAME,
        _ses_cfg_set or "(none)",
    )
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@mimir.local")
    _email_log.warning(
        "[EMAIL] Console backend active — verification emails are printed to the "
        "runserver terminal only, not sent to real inboxes. Unset USE_SES_IN_DEV=0 "
        "or remove it to deliver via AWS SES."
    )

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")

# ─────────────────────────────────────────────────────────────────────────────
# Bug reports — optional GitHub filing from local UI / mcp_server
# ─────────────────────────────────────────────────────────────────────────────
# Dry-run by default locally so the form works without a GITHUB_TOKEN.
# Set GITHUB_TOKEN env var to file real issues from dev.
BUG_REPORT_DRY_RUN = not bool(os.environ.get("GITHUB_TOKEN", "").strip())
