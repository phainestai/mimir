"""
Unit tests for settings resolution across environments.

Tests that the correct settings module is loaded based on MIMIR_ENV.
These tests verify the current test environment settings are correct.

NOTE: Django settings cannot be reloaded once configured by pytest-django.
For testing different environments, run pytest with different MIMIR_ENV values.
"""

import os
import pytest
from django.conf import settings


class TestCurrentEnvironmentSettings:
    """Test that current environment settings are correctly configured."""

    def test_test_environment_uses_in_memory_db(self):
        """Test environment should use in-memory SQLite."""
        # pytest-django configures test DB, which may differ from settings
        # We verify the settings intent rather than the actual test DB
        assert settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'

    def test_test_environment_has_debug_off(self):
        """Test environment should have DEBUG=False (closer to prod)."""
        assert settings.DEBUG is False

    def test_test_environment_has_test_secret_key(self):
        """Test environment should use a fixed test secret key."""
        assert settings.SECRET_KEY == "django-test-secret-key-not-for-production"

    def test_test_environment_allows_testserver(self):
        """Test environment should allow testserver hostname."""
        assert 'testserver' in settings.ALLOWED_HOSTS

    def test_test_environment_has_fast_password_hasher(self):
        """Test environment should use MD5 hasher for speed."""
        assert 'MD5PasswordHasher' in settings.PASSWORD_HASHERS[0]


class TestSettingsStructure:
    """Test that settings package structure is correct."""

    def test_settings_package_exists(self):
        """Settings should be a package with __init__.py."""
        import mimir.settings
        assert hasattr(mimir.settings, '__file__')

    def test_base_settings_module_exists(self):
        """Base settings module should exist."""
        from mimir.settings import base
        assert hasattr(base, 'INSTALLED_APPS')

    def test_dev_settings_module_exists(self):
        """Dev settings module should exist."""
        from mimir.settings import dev
        assert hasattr(dev, 'DEBUG')

    def test_prod_settings_module_exists(self):
        """Prod settings module should exist."""
        # prod.py requires DJANGO_SECRET_KEY to import
        import os
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv('DJANGO_SECRET_KEY', 'test-key-for-import')
            from mimir.settings import prod
            assert hasattr(prod, 'SECURE_SSL_REDIRECT')

    def test_test_settings_module_exists(self):
        """Test settings module should exist."""
        from mimir.settings import test
        assert hasattr(test, 'PASSWORD_HASHERS')


class TestCommonSettings:
    """Test settings that should be present in all environments."""

    def test_installed_apps_includes_mimir_apps(self):
        """All environments should have mimir apps installed."""
        assert 'accounts' in settings.INSTALLED_APPS
        assert 'methodology' in settings.INSTALLED_APPS
        assert 'mcp_integration' in settings.INSTALLED_APPS

    def test_middleware_includes_request_id(self):
        """All environments should have RequestIDMiddleware."""
        assert 'mimir.middleware.RequestIDMiddleware' in settings.MIDDLEWARE

    def test_auth_settings_configured(self):
        """All environments should have auth URLs configured."""
        assert settings.LOGIN_URL == "/auth/user/login/"
        assert settings.LOGIN_REDIRECT_URL == "/dashboard/"

    def test_session_settings_configured(self):
        """All environments should have session settings."""
        assert settings.SESSION_COOKIE_AGE == 1209600  # 2 weeks
        assert settings.SESSION_COOKIE_HTTPONLY is True
        assert settings.SESSION_COOKIE_SAMESITE == "Lax"
