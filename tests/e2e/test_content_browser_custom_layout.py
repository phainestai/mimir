"""
E2E tests for the Custom Layout toggle (FOB-63).

Covers:
  - FOB-CONTENT-BROWSER-63: Default clean state vs user-configurable state

On page entry:
  - The "Custom layout" checkbox is unchecked.
  - Default settings are applied: layout=klay, routing=straight, compound=workflow-activity.
  - Layout picker, routing picker, compound btn, and node-size toggle are hidden.
  - Re-plot and zoom buttons remain visible.

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
from e2e_helpers import login, open_content_browser
from methodology.models import Activity, Playbook, Workflow

User = get_user_model()


@pytest.fixture()
def graph_page(page: Page, live_server, transactional_db):
    user = User.objects.create_user(username='custom_layout_tester', password='pass1234')
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='Custom Layout PB', description='FOB-63 tests',
        category='development', status='released', version='1.0',
        source='owned', author=user, visibility='public',
    )
    wf = Workflow.objects.create(name='CL Workflow', playbook=pb, order=1)
    Activity.objects.create(name='CL Act', workflow=wf, order=1)
    login(page, live_server.url, 'custom_layout_tester', 'pass1234')
    open_content_browser(page, live_server.url, pb.pk)
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

    def test_default_mode_hides_node_size_toggle(self, graph_page):
        """In default mode, the node-size toggle button is hidden."""
        node_size = graph_page.locator('[data-testid="browser-node-size-toggle"]')
        assert node_size.count() > 0, "Node-size toggle must be in DOM"
        assert not node_size.is_visible(), "Node-size toggle should be hidden in default mode"

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
        """Ticking the checkbox shows layout, routing, compound, and node-size buttons."""
        toggle = graph_page.locator('[data-testid="browser-custom-layout-toggle"]')
        toggle.check()
        graph_page.wait_for_timeout(200)

        layout_btn = graph_page.locator('[data-testid="browser-layout-btn"]')
        routing_btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        compound_btn = graph_page.locator('[data-testid="browser-compound-btn"]')
        node_size = graph_page.locator('[data-testid="browser-node-size-toggle"]')

        assert layout_btn.is_visible(), "Layout btn should be visible in custom mode"
        assert routing_btn.is_visible(), "Routing btn should be visible in custom mode"
        assert compound_btn.is_visible(), "Compound btn should be visible in custom mode"
        assert node_size.is_visible(), "Node-size toggle should be visible in custom mode"

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

        node_size = graph_page.locator('[data-testid="browser-node-size-toggle"]')
        assert not node_size.is_visible(), "Node-size toggle should be hidden after disabling custom mode"

        layout = graph_page.evaluate("() => window._currentLayout")
        routing = graph_page.evaluate("() => window._currentRouting")
        level = graph_page.evaluate("() => window._compoundLevel")
        assert layout == 'klay', f"Layout should revert to klay, got: {layout}"
        assert routing == 'straight', f"Routing should revert to straight, got: {routing}"
        assert level == 'workflow-activity', f"Compound should revert to workflow-activity, got: {level}"
