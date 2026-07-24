"""
E2E tests for Content Browser left panel: layout, collapse toggle,
playbook header (FOB-20, 21).

Run: DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_left_panel.py -x
"""

import re

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()

LOGIN_URL_PATH = "/auth/user/login/"


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    assert LOGIN_URL_PATH not in page.url, f"Login failed. URL: {page.url}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def left_panel_user(transactional_db):
    user = User.objects.create_user(
        username="lp_user",
        email="lp@test.com",
        password="testpass123",
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def playbook_a(left_panel_user, transactional_db):
    pb = Playbook.objects.create(
        name="AlphaPlaybook",
        description="First",
        category="development",
        status="draft",
        version="0.1",
        source="owned",
        author=left_panel_user,
        visibility="public",
    )
    wf = Workflow.objects.create(name="AlphaWorkflow", playbook=pb, order=1)
    Activity.objects.create(name="AlphaActivity", workflow=wf, order=1)
    return pb


# ---------------------------------------------------------------------------
# FOB-20: Three-panel layout and collapse toggle
# ---------------------------------------------------------------------------


class TestThreePanelLayout:
    def test_three_panels_visible(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Left panel, canvas, and detail panel all present in DOM (FOB-20)."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        expect(page.locator('[data-testid="browser-left-panel"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-canvas"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()
        expect(
            page.locator('[data-testid="browser-toggle-left-panel"]')
        ).to_be_visible()

    def test_collapse_toggle_hides_left_panel(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Clicking toggle collapses left panel (FOB-20)."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        page.locator('[data-testid="browser-toggle-left-panel"]').click()
        panel_content = page.locator("#browser-left-panel-content")
        expect(panel_content).to_be_hidden()

    def test_collapse_toggle_re_expands(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Clicking toggle twice restores left panel (FOB-20). Button must be clickable at 0 width."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        toggle = page.locator('[data-testid="browser-toggle-left-panel"]')
        toggle.click()
        page.wait_for_timeout(300)
        expect(toggle).to_be_visible()
        toggle.click()
        page.wait_for_timeout(300)
        expect(page.locator("#browser-left-panel-content")).to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# FOB-21: Playbook name + status badge (no picker controls)
# ---------------------------------------------------------------------------


class TestPlaybookHeader:
    def test_playbook_name_shown_in_left_panel(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Left panel shows playbook name (FOB-21)."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        name_el = page.locator('[data-testid="browser-playbook-title"]')
        expect(name_el).to_contain_text("AlphaPlaybook")

    def test_status_badge_shown(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Status badge is shown (FOB-21)."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        status_el = page.locator('[data-testid="browser-playbook-status"]')
        expect(status_el).to_be_visible()
        assert status_el.text_content().strip() != ""

    def test_no_picker_buttons_in_left_panel(
        self, page: Page, live_server, left_panel_user, playbook_a
    ):
        """Playbook-scoped browser has no Change/Select playbook controls (FOB-21)."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state("networkidle")

        expect(page.locator('[data-testid="browser-change-playbook"]')).to_have_count(0)
        expect(page.locator('[data-testid="browser-select-playbook"]')).to_have_count(0)
        expect(page.locator('[data-testid="browser-picker"]')).to_have_count(0)

    def test_status_badge_keeps_draft_warning_color_after_graph_load(
        self,
        page: Page,
        live_server,
        left_panel_user,
        playbook_a,
    ):
        """Graph fetch must not downgrade draft badge from warning to secondary grey."""
        _login(page, live_server.url, "lp_user", "testpass123")
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_function(
            "() => window.cy && window.cy.nodes().length >= 1", timeout=15_000
        )

        status_el = page.locator('[data-testid="browser-playbook-status"]')
        expect(status_el).to_have_class(re.compile(r"bg-warning"))
        expect(status_el).to_have_text("Draft")
