"""
Production settings for mimir project.

Hardened for AWS Elastic Beanstalk deployment with Postgres RDS.
"""

import os
import urllib.request

import dj_database_url

from .base import *  # noqa: F401, F403

# Environment identifier
MIMIR_ENV = "prod"

# SECURITY WARNING: SECRET_KEY must be set via environment variable in production
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# SECURITY WARNING: DEBUG must be False in production
DEBUG = False

# ALLOWED_HOSTS must include the ALB hostname + CloudFront domain
ALLOWED_HOSTS = os.getenv(
    "DJANGO_ALLOWED_HOSTS", "mimir.featurefactory.io,.elasticbeanstalk.com,localhost"
).split(",")

# Append the EC2 instance's private IP so ELB target-group health checks
# (Host: <instance-ip>) are accepted instead of returning 400.
def _ec2_private_ip() -> str | None:
    """Fetch private IPv4 from IMDSv2; return None if not on EC2."""
    try:
        token_req = urllib.request.Request(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            method="PUT",
        )
        token = urllib.request.urlopen(token_req, timeout=1).read().decode()
        ip_req = urllib.request.Request(
            "http://169.254.169.254/latest/meta-data/local-ipv4",
            headers={"X-aws-ec2-metadata-token": token},
        )
        return urllib.request.urlopen(ip_req, timeout=1).read().decode()
    except Exception:
        return None

_instance_ip = _ec2_private_ip()
if _instance_ip:
    ALLOWED_HOSTS.append(_instance_ip)

# CSRF trusted origins — include the EB direct URL so blue/green testing works.
# In production, CloudFront always uses HTTPS; EB direct URL is HTTP only.
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://mimir.featurefactory.io,http://mimir-blue.us-east-1.elasticbeanstalk.com,https://mimir-blue.us-east-1.elasticbeanstalk.com",
).split(",")


# Security settings for production
# https://docs.djangoproject.com/en/5.2/ref/settings/#security

# Trust X-Forwarded-Proto forwarded by CloudFront custom origin header.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS is enforced by CloudFront (Viewer Protocol Policy: Redirect HTTP→HTTPS).
# The EB origin is reached over HTTP so Django's SECURE_SSL_REDIRECT would loop.
# Matches the proven Huginn pattern — cookies are still Secure because viewers
# always speak HTTPS at the CloudFront edge.
SECURE_SSL_REDIRECT = False

# Secure cookies — opt-in via env var.
# Default True when behind CloudFront (production); set to False for EB direct access
# (e.g. blue/green testing over plain HTTP on the EB URL).
_cookie_secure = os.getenv("COOKIE_SECURE", "true").lower() == "true"
SESSION_COOKIE_SECURE = _cookie_secure
CSRF_COOKIE_SECURE = _cookie_secure

# HSTS — start at 1 hour; bump to 31536000 after a week of stable operation.
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# DATABASE_URL is required in production (from SSM Parameter Store)
# Format: postgresql://mimir:PASSWORD@huginn-db.cmd1ovmhpsfb.us-east-1.rds.amazonaws.com:5432/mimir
DATABASES = {
    "default": dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
        ssl_require=True,
    )
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

# WhiteNoise for static file serving
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# TODO Phase 7: Add django-storages for S3 media files
# MEDIA_URL = 'https://mimir-static-411113550285.s3.amazonaws.com/media/'
# DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
# AWS_STORAGE_BUCKET_NAME = 'mimir-static-411113550285'
# AWS_S3_REGION_NAME = 'us-east-1'
# AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'


# Logging configuration (JSON for CloudWatch)
# https://docs.djangoproject.com/en/5.2/topics/logging/

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(pathname)s %(lineno)d",
        },
    },
    "filters": {
        "request_id": {
            "()": "mimir.logging_filters.RequestIDFilter",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_id"],
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
        "accounts": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "methodology": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "mcp_integration": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Email — AWS SES via django-ses
# ─────────────────────────────────────────────────────────────────────────────
# Required environment variables:
#   AWS_SES_REGION_NAME       e.g. "us-east-1"          (mandatory)
#   DEFAULT_FROM_EMAIL        e.g. "noreply@featurefactory.io"  (mandatory, must be SES-verified)
#   AWS_ACCESS_KEY_ID         IAM key with ses:SendEmail  (or use EC2/EB instance role)
#   AWS_SECRET_ACCESS_KEY     paired secret
#
# Optional tuning:
#   AWS_SES_CONFIGURATION_SET  SES configuration set name for open/click tracking
#
# django-ses docs: https://github.com/django-ses/django-ses
EMAIL_BACKEND = "django_ses.SESBackend"
AWS_SES_REGION_NAME = os.getenv("AWS_SES_REGION_NAME", "us-east-1")
AWS_SES_REGION_ENDPOINT = f"email.{AWS_SES_REGION_NAME}.amazonaws.com"
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@featurefactory.io")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://mimir.featurefactory.io")

# SES Configuration Set (optional; enables CloudWatch bounce/complaint metrics)
_ses_cfg_set = os.getenv("AWS_SES_CONFIGURATION_SET", "")
if _ses_cfg_set:
    AWS_SES_CONFIGURATION_SET = _ses_cfg_set

# ─────────────────────────────────────────────────────────────────────────────
# Bug reports — GitHub Issues (PyGithub)
# ─────────────────────────────────────────────────────────────────────────────
# Values are read in ``mimir.settings.base`` from the environment. Set on the EB
# environment (recommended) or in the shell that starts Gunicorn:
#
#   GITHUB_TOKEN — classic PAT or fine-grained token with **Issues: write** on
#                  the repo given by GITHUB_BUG_REPO.
#   GITHUB_BUG_REPO — default ``phainestai/mimir`` (override for forks).
#   BUG_REPORT_DRY_RUN — optional; ``1``/``true`` skips PyGithub (staging only).
#
# If GITHUB_TOKEN is unset, the feedback widget and ``POST /api/feedback/report/``
# return a clear configuration error when users try to file a report.
#
# The MCP HTTP facade does **not** need GITHUB_TOKEN; it calls the web API, which
# files issues using the token on the FOB container.
