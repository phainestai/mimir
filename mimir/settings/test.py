"""
Test settings for mimir project.

Optimized for fast test execution with in-memory SQLite.
"""

import os
from .base import *  # noqa: F401, F403

# Environment identifier
MIMIR_ENV = 'test'

# Use a fixed secret key for tests
SECRET_KEY = "django-test-secret-key-not-for-production"

# Debug off in tests (closer to prod)
DEBUG = False

# Allow testserver hostname
ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']

# CSRF trusted origins for test client
CSRF_TRUSTED_ORIGINS = [
    'http://testserver',
    'http://localhost',
    'http://127.0.0.1',
]


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# In-memory SQLite for fast tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}


# Password hashers (faster for tests)
# https://docs.djangoproject.com/en/5.2/topics/testing/overview/#password-hashing

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]


# Logging configuration (minimal for tests)
# https://docs.djangoproject.com/en/5.2/topics/logging/

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
        'level': 'CRITICAL',
    },
}
