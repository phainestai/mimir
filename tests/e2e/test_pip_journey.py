"""E2E sanity: authenticated user reaches PIP list (Act 9 shell)."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from playwright.sync_api import Page

User = get_user_model()


@pytest.fixture
def pip_e2e_user(db):
    u = User.objects.create_user(
        username="pip_e2e", password="pipE2Epw!", email="e2e@example.test"
    )
    return u


@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
def test_login_and_open_pip_list(page: Page, live_server_url: str, pip_e2e_user):
    login_url = f"{live_server_url}{reverse('login')}"

    page.goto(login_url)
    page.fill('input[name="username"]', "pip_e2e")
    page.fill('input[name="password"]', "pipE2Epw!")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    page.goto(f"{live_server_url}{reverse('pip_list')}")
    page.wait_for_load_state("networkidle")
    txt = page.content()
    assert "PIPs" in txt or "pip-empty-state" in txt
