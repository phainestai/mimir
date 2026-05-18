"""UI mockup routes are disabled outside development settings."""

import pytest
from django.conf import settings
from django.test import Client


@pytest.mark.django_db
def test_mockup_urls_return_404_when_disabled(client: Client):
    """Production and pytest use ENABLE_UI_MOCKUPS=False — no /mockups/ mount."""
    assert getattr(settings, "ENABLE_UI_MOCKUPS", False) is False
    assert client.get("/mockups/auth/register/").status_code == 404
    assert client.get("/mockups/auth/login/").status_code == 404
    assert client.get("/mockups/pips/").status_code == 404
    assert client.get("/mockups/profile/").status_code == 404


@pytest.mark.django_db
def test_enable_ui_mockups_setting_documented():
    """Guardrail: dev enables mockups via mimir.settings.dev."""
    from mimir.settings import dev as dev_settings

    assert getattr(dev_settings, "ENABLE_UI_MOCKUPS", False) is True
