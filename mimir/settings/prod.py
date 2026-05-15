"""
Production settings for mimir project.

Hardened for AWS Elastic Beanstalk deployment with Postgres RDS.
"""

import os

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

# CSRF trusted origins (HTTPS only in prod)
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS", "https://mimir.featurefactory.io"
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

# Secure cookies — viewers always connect via HTTPS through CloudFront.
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

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

# Email configuration (AWS SES)
# AWS credentials should be set via environment variables:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@featurefactory.io")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://mimir.featurefactory.io")
