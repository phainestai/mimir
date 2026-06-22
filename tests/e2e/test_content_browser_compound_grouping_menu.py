"""
E2E tests for FOB-CONTENT-BROWSER-61:
Compound grouping button becomes a 3-option context menu.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_compound_grouping_menu.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.e2e

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='compound_menu_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'compound_menu_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestCompoundGroupingMenu:
    """FOB-61: Grouping dropdown replaces toggle; 3-level compound support."""

    def test_compound_dropdown_button_exists(self, graph_page: Page):
        """Grouping button with data-testid='browser-compound-btn' is present."""
        btn = graph_page.locator('[data-testid="browser-compound-btn"]')
        expect(btn).to_be_visible()

    def test_old_compound_toggle_button_removed(self, graph_page: Page):
        """Old data-testid='browser-compound-toggle' no longer exists in DOM."""
        old = graph_page.locator('[data-testid="browser-compound-toggle"]')
        expect(old).to_have_count(0)

    def test_compound_dropdown_has_three_options(self, graph_page: Page):
        """Clicking the grouping button shows exactly 3 options."""
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-dropdown"]')
        none_opt = graph_page.locator('[data-testid="browser-compound-option-none"]')
        wf_opt = graph_page.locator('[data-testid="browser-compound-option-workflow"]')
        wa_opt = graph_page.locator('[data-testid="browser-compound-option-workflow-activity"]')
        expect(none_opt).to_be_visible()
        expect(wf_opt).to_be_visible()
        expect(wa_opt).to_be_visible()
        # Close dropdown
        graph_page.keyboard.press('Escape')

    def test_compound_option_none_activates_flat_mode(self, graph_page: Page):
        """Selecting 'No Grouping' sets _compoundLevel to 'none' (flat graph)."""
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-none"]')
        graph_page.click('[data-testid="browser-compound-option-none"]')
        level = graph_page.evaluate("() => window._compoundLevel")
        assert level == 'none', f"Expected 'none', got '{level}'"

    def test_compound_option_workflow_activates_workflow_grouping(self, graph_page: Page):
        """Selecting 'Group by workflow' sets _compoundLevel to 'workflow'."""
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        graph_page.click('[data-testid="browser-compound-option-workflow"]')
        level = graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow', f"Expected 'workflow', got '{level}'"

    def test_compound_option_workflow_activity_activates_two_level_grouping(self, graph_page: Page):
        """Selecting 'Group by workflow + activity' sets _compoundLevel to 'workflow-activity'."""
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow-activity"]')
        graph_page.click('[data-testid="browser-compound-option-workflow-activity"]')
        level = graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow-activity', f"Expected 'workflow-activity', got '{level}'"

    def test_compound_url_param_encodes_level(self, graph_page: Page):
        """URL param 'compound' is updated when a grouping option is selected."""
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        graph_page.click('[data-testid="browser-compound-option-workflow"]')
        assert 'compound=workflow' in graph_page.url, f"Expected compound=workflow in URL: {graph_page.url}"

    def test_compound_level_window_property_exposed(self, graph_page: Page):
        """window._compoundLevel is accessible and defaults to 'none'."""
        level = graph_page.evaluate("() => window._compoundLevel")
        assert level == 'none', f"Expected default 'none', got '{level}'"

    def test_compound_active_option_shows_checkmark(self, graph_page: Page):
        """Active grouping option shows checkmark (✓) in dropdown."""
        # Set to workflow first
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        graph_page.click('[data-testid="browser-compound-option-workflow"]')
        # Re-open dropdown and check active option has ✓
        graph_page.click('[data-testid="browser-compound-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        wf_btn = graph_page.locator('[data-testid="browser-compound-option-workflow"]')
        assert '✓' in wf_btn.text_content(), "Active option should show ✓"
        graph_page.keyboard.press('Escape')
