"""
E2E tests for Content Browser URL management.

Covers layout query params on playbook-scoped browser entry (FOB-63).

Run: pytest tests/e2e/test_content_browser_url.py -x
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from e2e_helpers import login
from methodology.models import Activity, Playbook, Workflow

User = get_user_model()

_FOB63_QS = "?layout=klay&routing=straight&compound=workflow-activity"


@pytest.fixture
def browser_playbook(transactional_db):
    """Single playbook for URL param tests."""
    user = User.objects.create_user(
        username="url_user",
        email="url@test.com",
        password="testpass123",
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name="Playbook Alpha",
        description="",
        category="development",
        author=user,
        visibility="public",
        status="released",
    )
    wf = Workflow.objects.create(playbook=pb, name="Alpha WF", order=1)
    Activity.objects.create(workflow=wf, name="Alpha Act", order=1)
    return {
        "username": "url_user",
        "password": "testpass123",
        "pb": pb,
    }


@pytest.mark.django_db(transaction=True)
class TestURLManagement:
    """Playbook-scoped browser persists layout params in URL after init."""

    def test_browser_root_returns_404(
        self, page: Page, live_server_url, browser_playbook
    ):
        """GET /browser/ without pk returns 404."""
        login(
            page,
            live_server_url,
            browser_playbook["username"],
            browser_playbook["password"],
        )
        page.goto(f"{live_server_url}/browser/")
        expect(page.locator("body")).to_contain_text("Not Found")

    def test_playbook_browser_loads_with_default_layout_params(
        self, page: Page, live_server_url, browser_playbook
    ):
        """Direct /browser/<pk>/ entry applies FOB-63 default query params."""
        login(
            page,
            live_server_url,
            browser_playbook["username"],
            browser_playbook["password"],
        )
        pk = browser_playbook["pb"].pk
        page.goto(f"{live_server_url}/browser/{pk}/")
        page.wait_for_function(
            "() => typeof window.cy !== 'undefined' && window.cy.nodes().length >= 1",
            timeout=15_000,
        )
        expect(page).to_have_url(f"{live_server_url}/browser/{pk}/{_FOB63_QS}")
