"""
E2E test settings for mimir project.

Extends dev.py with adjustments for Playwright browser tests:
- Cookie-based sessions so the django_session table is never consulted.
  This avoids a race between the live-server thread and the test thread
  sharing a single in-memory SQLite connection via connections_override.
- Faster password hashing.
- Logging suppressed (keeps test output clean).
"""

from .dev import *  # noqa: F401, F403

# Override environment identifier
MIMIR_ENV = 'e2e'

# --- Sessions ---
# Store session data in a signed cookie instead of the django_session table.
# The live server shares the same in-memory SQLite connection with the test
# thread (via connections_override).  SESSION_SAVE_EVERY_REQUEST=True (base)
# means every authenticated request writes a session row, creating a window
# for a read/write race that produces intermittent 401s on the graph API.
# Signed-cookie sessions bypass the DB entirely: no race, no 401.
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"

# --- Database ---
# Force SQLite for e2e tests regardless of any DATABASE_URL env var.
from pathlib import Path as _Path  # noqa: E402
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": _Path(__file__).resolve().parent.parent.parent / "mimir.db",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# --- Auth ---
# MD5 is fast enough for tests; bcrypt's key-stretching is wasteful.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# --- Logging ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {"class": "logging.NullHandler"},
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}
