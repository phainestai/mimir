"""UI mockup routes are disabled outside development settings (DEBUG=False)."""

import pytest
from django.conf import settings
from django.test import Client


@pytest.mark.django_db
def test_mockup_urls_return_404_when_debug_false(client: Client):
    """Production and pytest use DEBUG=False — no /mockups/ mount."""
    assert settings.DEBUG is False
    assert client.get("/mockups/auth/register/").status_code == 404
    assert client.get("/mockups/auth/login/").status_code == 404
    assert client.get("/mockups/pips/").status_code == 404
    assert client.get("/mockups/profile/").status_code == 404
