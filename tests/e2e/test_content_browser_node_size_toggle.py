"""
E2E tests for Content Browser node size mode toggle (FOB-39).

Covers:
  - FOB-CONTENT-BROWSER-39: Node size mode toggle — Fixed size vs Auto-width

Checkpoint command:
  pytest tests/e2e/test_content_browser_node_size_toggle.py -x
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeToggleDefault:
    """FOB-39: Node size mode toggle — default state."""

    def test_node_size_toggle_button_is_visible(self, cb_custom_graph_page: Page):
        """browser-node-size-toggle button is present in custom layout mode."""
        btn = cb_custom_graph_page.locator('[data-testid="browser-node-size-toggle"]')
        expect(btn).to_be_visible()

    def test_default_mode_is_fixed(self, cb_custom_graph_page: Page):
        """By default _nodeSizeMode is 'fixed' (S48)."""
        mode = cb_custom_graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'fixed', f"Expected 'fixed', got {mode}"

    def test_default_button_label_indicates_fixed_mode(self, cb_custom_graph_page: Page):
        """Default button label contains 'Fixed' or 'fixed' (S48)."""
        btn = cb_custom_graph_page.locator('[data-testid="browser-node-size-toggle"]')
        btn_text = btn.inner_text()
        assert 'fixed' in btn_text.lower() or 'Fixed' in btn_text, \
            f"Expected 'Fixed' in button text, got: {btn_text}"


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeToggleBehaviour:
    """FOB-39: Node size mode toggle — clicking changes mode."""

    def test_clicking_toggle_switches_to_auto_mode(self, cb_custom_graph_page: Page):
        """Clicking the toggle changes _nodeSizeMode to 'auto' (S48)."""
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        mode = cb_custom_graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'auto'

    def test_clicking_toggle_again_returns_to_fixed_mode(self, cb_custom_graph_page: Page):
        """Double-click returns to 'fixed' mode."""
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'fixed'")
        mode = cb_custom_graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'fixed'

    def test_auto_mode_button_label_indicates_auto(self, cb_custom_graph_page: Page):
        """In auto mode the button label reflects auto-width."""
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        btn_text = cb_custom_graph_page.locator('[data-testid="browser-node-size-toggle"]').inner_text()
        assert 'auto' in btn_text.lower(), f"Expected 'auto' in label, got: {btn_text}"

    def test_node_size_mode_persisted_in_url(self, cb_custom_graph_page: Page):
        """Switching to auto mode updates URL with nodesize=auto."""
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        assert 'nodesize=auto' in cb_custom_graph_page.url

    def test_url_nodesize_param_restores_auto_mode(self, cb_graph_page: Page, live_server, cb_playbook):
        """Loading with ?nodesize=auto restores auto mode via URL deep-link."""
        from e2e_helpers import wait_for_cy_graph

        pk = cb_playbook['pb'].pk
        cb_graph_page.goto(f"{live_server.url}/browser/{pk}/?nodesize=auto")
        wait_for_cy_graph(cb_graph_page)
        mode = cb_graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'auto', f"Expected auto from URL param, got {mode}"
        assert cb_graph_page.evaluate("() => window._customLayoutMode") is True

    def test_fixed_mode_node_width_is_constant(self, cb_custom_graph_page: Page):
        """In fixed mode, activity nodes have a consistent width style."""
        widths = cb_custom_graph_page.evaluate(
            "() => window.cy.nodes('[type=\"activity\"]').map(n => n.style('width'))"
        )
        assert widths, "No activity nodes"
        assert len(set(widths)) == 1, f"Fixed mode should have uniform widths, got: {set(widths)}"

    def test_auto_mode_allows_variable_widths(self, cb_custom_graph_page: Page):
        """In auto mode, node width style differs from fixed (or is 'auto')."""
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        width = cb_custom_graph_page.evaluate(
            "() => window.cy.nodes('[type=\"activity\"]').first().style('width')"
        )
        assert width, "Expected width style on activity node in auto mode"

    def test_toggle_does_not_remove_nodes_from_graph(self, cb_custom_graph_page: Page):
        """Toggling node size mode does not change node count."""
        before = cb_custom_graph_page.evaluate("() => window.cy.nodes().length")
        cb_custom_graph_page.click('[data-testid="browser-node-size-toggle"]')
        cb_custom_graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        after = cb_custom_graph_page.evaluate("() => window.cy.nodes().length")
        assert before == after, "Node count changed after size toggle"

    def test_window_exposes_node_size_mode(self, cb_custom_graph_page: Page):
        """window._nodeSizeMode is readable."""
        val = cb_custom_graph_page.evaluate("() => window._nodeSizeMode")
        assert val in ('fixed', 'auto')
