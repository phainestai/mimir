"""
E2E tests for the Custom Layout toggle (FOB-63).

Covers:
  - FOB-CONTENT-BROWSER-63: Default clean state vs user-configurable state

On page entry:
  - The "Custom layout" checkbox is unchecked.
  - Default settings are applied: layout=klay, routing=straight, compound=workflow-activity.
  - Layout picker, routing picker, and compound btn are hidden.
  - Node-size toggle, re-plot, and zoom buttons remain visible.

When the user ticks the checkbox:
  - The three advanced buttons become visible.
  - Current settings are not changed by the toggle itself.

When the user unticks the checkbox:
  - Default settings are re-applied and advanced buttons are hidden.

Checkpoint command:
  pytest tests/e2e/test_content_browser_custom_layout.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='custom_layout_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'custom_layout_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=10_000,
    )
    return page


@pytest.mark.django_db(transaction=True)
class TestCustomLayoutToggle:
    """FOB-63 — Default clean state vs custom configurable state."""

    def test_checkbox_present_and_unchecked_on_load(self, graph_page):
        """Custom layout checkbox is always present and starts unchecked."""
        toggle = graph_page.locator('[data-testid="browser-custom-layout-toggle"]')
        assert toggle.count() > 0, "Custom layout toggle checkbox not found"
        assert not toggle.is_checked(), "Custom layout toggle should start unchecked"

    def test_default_mode_hides_layout_btn(self, graph_page):
        """In default mode, the layout picker button is hidden."""
        layout_btn = graph_page.locator('[data-testid="browser-layout-btn"]')
        assert layout_btn.count() > 0, "Layout btn must be in DOM"
        assert not layout_btn.is_visible(), "Layout btn should be hidden in default mode"

    def test_default_mode_hides_routing_btn(self, graph_page):
        """In default mode, the routing picker button is hidden."""
        routing_btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        assert routing_btn.count() > 0, "Routing btn must be in DOM"
        assert not routing_btn.is_visible(), "Routing btn should be hidden in default mode"

    def test_default_mode_hides_compound_btn(self, graph_page):
        """In default mode, the grouping/compound button is hidden."""
        compound_btn = graph_page.locator('[data-testid="browser-compound-btn"]')
        assert compound_btn.count() > 0, "Compound btn must be in DOM"
        assert not compound_btn.is_visible(), "Compound btn should be hidden in default mode"

    def test_default_mode_applies_klay_layout(self, graph_page):
        """In default mode, klay layout is applied."""
        layout = graph_page.evaluate("() => window._currentLayout")
        assert layout == 'klay', f"Expected klay layout in default mode, got: {layout}"

    def test_default_mode_applies_straight_routing(self, graph_page):
        """In default mode, straight routing is applied."""
        routing = graph_page.evaluate("() => window._currentRouting")
        assert routing == 'straight', f"Expected straight routing in default mode, got: {routing}"

    def test_default_mode_applies_workflow_activity_grouping(self, graph_page):
        """In default mode, workflow+activity compound grouping is applied."""
        level = graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow-activity', (
            f"Expected workflow-activity grouping in default mode, got: {level}"
        )

    def test_always_visible_buttons_present_in_default_mode(self, graph_page):
        """Node-size, re-plot, and zoom buttons are always visible regardless of mode."""
        selectors = [
            'browser-node-size-toggle',
            'browser-replot-btn',
            'browser-zoom-in',
            'browser-zoom-out',
            'browser-zoom-fit',
        ]
        for testid in selectors:
            btn = graph_page.locator(f'[data-testid="{testid}"]')
            assert btn.count() > 0, f"{testid} not found"
            assert btn.is_visible(), f"{testid} should be visible in default mode"

    def test_toggle_on_shows_advanced_buttons(self, graph_page):
        """Ticking the checkbox shows layout, routing, and compound buttons."""
        toggle = graph_page.locator('[data-testid="browser-custom-layout-toggle"]')
        toggle.check()
        graph_page.wait_for_timeout(200)

        layout_btn = graph_page.locator('[data-testid="browser-layout-btn"]')
        routing_btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        compound_btn = graph_page.locator('[data-testid="browser-compound-btn"]')

        assert layout_btn.is_visible(), "Layout btn should be visible in custom mode"
        assert routing_btn.is_visible(), "Routing btn should be visible in custom mode"
        assert compound_btn.is_visible(), "Compound btn should be visible in custom mode"

    def test_toggle_on_sets_custom_layout_mode_flag(self, graph_page):
        """Ticking the checkbox sets _customLayoutMode to True."""
        toggle = graph_page.locator('[data-testid="browser-custom-layout-toggle"]')
        toggle.check()
        graph_page.wait_for_timeout(200)
        mode = graph_page.evaluate("() => window._customLayoutMode")
        assert mode is True, "Expected _customLayoutMode to be True after enabling"

    def test_toggle_off_reapplies_defaults_and_hides_buttons(self, graph_page):
        """Unticking the checkbox re-applies default settings and hides advanced buttons."""
        toggle = graph_page.locator('[data-testid="browser-custom-layout-toggle"]')
        toggle.check()
        graph_page.wait_for_timeout(200)
        toggle.uncheck()
        graph_page.wait_for_timeout(200)

        layout_btn = graph_page.locator('[data-testid="browser-layout-btn"]')
        routing_btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        compound_btn = graph_page.locator('[data-testid="browser-compound-btn"]')

        assert not layout_btn.is_visible(), "Layout btn should be hidden after disabling custom mode"
        assert not routing_btn.is_visible(), "Routing btn should be hidden after disabling custom mode"
        assert not compound_btn.is_visible(), "Compound btn should be hidden after disabling custom mode"

        layout = graph_page.evaluate("() => window._currentLayout")
        routing = graph_page.evaluate("() => window._currentRouting")
        level = graph_page.evaluate("() => window._compoundLevel")
        assert layout == 'klay', f"Layout should revert to klay, got: {layout}"
        assert routing == 'straight', f"Routing should revert to straight, got: {routing}"
        assert level == 'workflow-activity', f"Compound should revert to workflow-activity, got: {level}"
