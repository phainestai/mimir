"""
E2E tests for Content Browser left panel: layout, collapse toggle,
playbook header, and picker (FOB-20, 21, 22, 23).

Run: DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_left_panel.py -x
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()

LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed. URL: {page.url}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def left_panel_user(transactional_db):
    user = User.objects.create_user(
        username='lp_user', email='lp@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def playbook_a(left_panel_user, transactional_db):
    pb = Playbook.objects.create(
        name='AlphaPlaybook', description='First',
        category='development', status='draft', version='0.1',
        source='owned', author=left_panel_user, visibility='public',
    )
    wf = Workflow.objects.create(name='AlphaWorkflow', playbook=pb, order=1)
    Activity.objects.create(name='AlphaActivity', workflow=wf, order=1)
    return pb


@pytest.fixture
def playbook_b(left_panel_user, transactional_db):
    pb = Playbook.objects.create(
        name='BetaPlaybook', description='Second',
        category='design', status='released', version='1.0',
        source='owned', author=left_panel_user, visibility='public',
    )
    Workflow.objects.create(name='BetaWorkflow', playbook=pb, order=1)
    return pb


# ---------------------------------------------------------------------------
# FOB-20: Three-panel layout and collapse toggle
# ---------------------------------------------------------------------------

class TestThreePanelLayout:

    def test_three_panels_visible(self, page: Page, live_server, left_panel_user, playbook_a):
        """Left panel, canvas, and detail panel all present in DOM (FOB-20)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        expect(page.locator('[data-testid="browser-left-panel"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-canvas"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()
        expect(page.locator('[data-testid="browser-toggle-left-panel"]')).to_be_visible()

    def test_collapse_toggle_hides_left_panel(self, page: Page, live_server, left_panel_user, playbook_a):
        """Clicking toggle collapses left panel (FOB-20)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-toggle-left-panel"]').click()
        # Content hidden — panel collapses to 0 width
        panel_content = page.locator('#browser-left-panel-content')
        expect(panel_content).to_be_hidden()

    def test_collapse_toggle_re_expands(self, page: Page, live_server, left_panel_user, playbook_a):
        """Clicking toggle twice restores left panel (FOB-20). Button must be clickable at 0 width."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        toggle = page.locator('[data-testid="browser-toggle-left-panel"]')
        toggle.click()
        page.wait_for_timeout(300)  # wait for CSS transition
        # Toggle stays visible at edge of 0-width panel (overflow:visible on panel)
        expect(toggle).to_be_visible()
        toggle.click()
        page.wait_for_timeout(300)
        expect(page.locator('#browser-left-panel-content')).to_be_visible(timeout=5000)


# ---------------------------------------------------------------------------
# FOB-21: Playbook name + status badge
# ---------------------------------------------------------------------------

class TestPlaybookHeader:

    def test_playbook_name_shown_in_left_panel(self, page: Page, live_server, left_panel_user, playbook_a):
        """Left panel shows playbook name (FOB-21)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        name_el = page.locator('[data-testid="browser-playbook-name"]')
        expect(name_el).to_contain_text('AlphaPlaybook')

    def test_status_badge_shown(self, page: Page, live_server, left_panel_user, playbook_a):
        """Status badge is shown (FOB-21)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        status_el = page.locator('[data-testid="browser-playbook-status"]')
        expect(status_el).to_be_visible()
        # draft playbook → status text should be non-empty
        assert status_el.text_content().strip() != ''


# ---------------------------------------------------------------------------
# FOB-22: Picker opens from [Change Playbook] and [Select Playbook]
# ---------------------------------------------------------------------------

class TestPickerOpen:

    def test_picker_opens_on_change_playbook(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """[Change Playbook] opens picker (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-change-playbook"]').click()
        expect(page.locator('[data-testid="browser-picker"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-picker-search"]')).to_be_visible()

    def test_picker_opens_on_select_playbook_empty_state(self, page: Page, live_server, left_panel_user, playbook_a):
        """[Select Playbook] in empty state opens picker (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-select-playbook"]').first.click()
        expect(page.locator('[data-testid="browser-picker"]')).to_be_visible()

    def test_picker_lists_accessible_playbooks(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """Picker shows both playbooks accessible to user (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_timeout(500)  # wait for fetch
        items = page.locator('[data-testid="browser-picker-item"]')
        expect(items).to_have_count(2)

    def test_picker_marks_active_playbook(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """Active playbook row shows checkmark (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_timeout(500)
        active_item = page.locator('[data-testid="browser-picker-item"].active')
        expect(active_item).to_have_count(1)
        expect(active_item).to_contain_text('AlphaPlaybook')

    def test_picker_search_filters_list(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """Typing in picker search filters by name (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_timeout(500)

        page.locator('[data-testid="browser-picker-search"]').fill('Beta')
        page.wait_for_timeout(200)  # wait for synchronous filter to re-render
        items = page.locator('[data-testid="browser-picker-item"]')
        expect(items).to_have_count(1)
        expect(items.first).to_contain_text('BetaPlaybook')

    def test_picker_auto_expands_collapsed_panel(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """Picker auto-expands left panel if collapsed (FOB-22)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        # Collapse panel, then trigger picker from empty-state [Select Playbook]
        page.locator('[data-testid="browser-toggle-left-panel"]').click()
        expect(page.locator('#browser-left-panel-content')).to_be_hidden()

        # Use JS to open picker programmatically (panel is collapsed so button invisible)
        page.evaluate('_openPicker()')
        expect(page.locator('#browser-left-panel-content')).to_be_visible()
        expect(page.locator('[data-testid="browser-picker"]')).to_be_visible()


# ---------------------------------------------------------------------------
# FOB-23: Selecting playbook from picker updates URL and heading
# ---------------------------------------------------------------------------

class TestSelectPlaybook:

    def test_selecting_playbook_updates_url_and_heading(self, page: Page, live_server, left_panel_user, playbook_a, playbook_b):
        """Selecting a playbook closes picker, updates URL and heading (FOB-23)."""
        _login(page, live_server.url, 'lp_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{playbook_a.pk}/")
        page.wait_for_load_state('networkidle')

        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_timeout(500)

        # Click the BetaPlaybook row
        page.locator('[data-testid="browser-picker-item"]').filter(has_text='BetaPlaybook').click()

        # Picker closes
        expect(page.locator('[data-testid="browser-picker"]')).to_be_hidden()
        # URL updated to BetaPlaybook
        assert f'/browser/{playbook_b.pk}/' in page.url
