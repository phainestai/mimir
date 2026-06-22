"""
E2E tests for Content Browser edge routing picker (FOB-35).

Covers:
  - FOB-CONTENT-BROWSER-35: Edge routing picker — dropdown to select Cytoscape curve-style

Checkpoint command:
  pytest tests/e2e/test_content_browser_routing_picker.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from e2e_helpers import wait_for_cy_graph


@pytest.mark.django_db(transaction=True)
class TestRoutingCatalog:
    """FOB-35: Edge routing picker — catalog content and default state."""

    def test_routing_button_visible_in_custom_mode(self, cb_custom_graph_page: Page):
        """browser-routing-btn is visible when custom layout mode is enabled."""
        btn = cb_custom_graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_be_visible()

    def test_all_six_routing_options_present(self, cb_custom_graph_page: Page):
        """Dropdown contains all 6 routing options with correct data-testid values."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.wait_for_selector(
            '[data-testid="browser-routing-dropdown"]'
        )
        expected_keys = [
            "bezier",
            "straight",
            "taxi",
            "haystack",
            "segments",
            "round-segments",
        ]
        for key in expected_keys:
            opt = cb_custom_graph_page.locator(
                f'[data-testid="browser-routing-option-{key}"]'
            )
            expect(opt).to_be_visible()
        cb_custom_graph_page.keyboard.press("Escape")

    def test_default_routing_is_straight_in_custom_mode(
        self, cb_custom_graph_page: Page
    ):
        """FOB-63 default routing is straight; button shows Straight in custom mode."""
        btn = cb_custom_graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text("Straight")

    def test_url_param_routing_sets_initial_state(
        self, cb_graph_page: Page, live_server, cb_playbook
    ):
        """?routing=taxi applies on load via URL deep-link custom canvas mode."""
        pk = cb_playbook["pb"].pk
        cb_graph_page.goto(f"{live_server.url}/browser/{pk}/?routing=taxi")
        wait_for_cy_graph(cb_graph_page)
        routing = cb_graph_page.evaluate("() => window._currentRouting")
        assert routing == "taxi", f"Expected taxi from URL param, got {routing}"
        btn = cb_graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text("Orthogonal")

    def test_unknown_routing_param_falls_back_to_bezier(
        self, cb_graph_page: Page, live_server, cb_playbook
    ):
        """?routing=invalid falls back to bezier per _parseRoutingParam."""
        pk = cb_playbook["pb"].pk
        cb_graph_page.goto(f"{live_server.url}/browser/{pk}/?routing=invalid")
        wait_for_cy_graph(cb_graph_page)
        routing = cb_graph_page.evaluate("() => window._currentRouting")
        assert routing == "bezier"


@pytest.mark.django_db(transaction=True)
class TestRoutingPickerInteraction:
    """FOB-35: Edge routing picker — interaction and edge style update."""

    def test_click_opens_dropdown(self, cb_custom_graph_page: Page):
        """Clicking browser-routing-btn opens browser-routing-dropdown."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        dropdown = cb_custom_graph_page.locator(
            '[data-testid="browser-routing-dropdown"]'
        )
        expect(dropdown).to_be_visible()
        cb_custom_graph_page.keyboard.press("Escape")

    def test_select_straight_updates_button_label(self, cb_custom_graph_page: Page):
        """Selecting 'Straight' updates the routing button label to 'Straight'."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.click('[data-testid="browser-routing-option-straight"]')
        btn = cb_custom_graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text("Straight")

    def test_select_taxi_applies_curve_style_to_all_edges(
        self, cb_custom_graph_page: Page
    ):
        """After selecting 'Orthogonal', all cy edges have curve-style 'taxi'."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.click('[data-testid="browser-routing-option-taxi"]')
        curve_styles = cb_custom_graph_page.evaluate(
            "() => window.cy.edges().map(e => e.style('curve-style'))"
        )
        assert all(s == "taxi" for s in curve_styles), (
            f"Expected all 'taxi', got: {set(curve_styles)}"
        )

    def test_routing_change_does_not_rebuild_node_positions(
        self, cb_custom_graph_page: Page
    ):
        """Edge style update does not trigger a layout re-run (node positions unchanged)."""
        positions_before = cb_custom_graph_page.evaluate(
            "() => window.cy.nodes().map(n => ({id: n.id(), x: Math.round(n.position('x')), y: Math.round(n.position('y'))}))"
        )
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.click('[data-testid="browser-routing-option-straight"]')
        positions_after = cb_custom_graph_page.evaluate(
            "() => window.cy.nodes().map(n => ({id: n.id(), x: Math.round(n.position('x')), y: Math.round(n.position('y'))}))"
        )
        assert positions_before == positions_after, (
            "Node positions changed after routing update"
        )

    def test_selected_routing_persisted_in_url_param(self, cb_custom_graph_page: Page):
        """After selecting 'Segments', URL contains ?routing=segments."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.click('[data-testid="browser-routing-option-segments"]')
        assert "routing=segments" in cb_custom_graph_page.url

    def test_escape_closes_dropdown_without_changing_routing(
        self, cb_custom_graph_page: Page
    ):
        """Pressing Escape closes dropdown; routing state is unchanged."""
        initial_routing = cb_custom_graph_page.evaluate("() => window._currentRouting")
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.wait_for_selector(
            '[data-testid="browser-routing-dropdown"]'
        )
        cb_custom_graph_page.keyboard.press("Escape")
        expect(
            cb_custom_graph_page.locator('[data-testid="browser-routing-dropdown"]')
        ).to_have_count(0)
        after_routing = cb_custom_graph_page.evaluate("() => window._currentRouting")
        assert after_routing == initial_routing

    def test_outside_click_closes_dropdown(self, cb_custom_graph_page: Page):
        """Clicking outside the dropdown closes it."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.wait_for_selector(
            '[data-testid="browser-routing-dropdown"]'
        )
        cb_custom_graph_page.click(
            '[data-testid="browser-canvas"]', position={"x": 10, "y": 10}
        )
        expect(
            cb_custom_graph_page.locator('[data-testid="browser-routing-dropdown"]')
        ).to_have_count(0)

    def test_unbundled_bezier_option_present_in_dropdown(
        self, cb_custom_graph_page: Page
    ):
        """Dropdown must include an unbundled-bezier option (S43 — FOB-35 fix)."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.wait_for_selector(
            '[data-testid="browser-routing-dropdown"]'
        )
        expect(
            cb_custom_graph_page.locator(
                '[data-testid="browser-routing-option-unbundled-bezier"]'
            )
        ).to_be_visible()

    def test_selecting_unbundled_bezier_applies_and_stores_param(
        self, cb_custom_graph_page: Page
    ):
        """Selecting unbundled-bezier updates button label and URL param (S43)."""
        cb_custom_graph_page.click('[data-testid="browser-routing-btn"]')
        cb_custom_graph_page.click(
            '[data-testid="browser-routing-option-unbundled-bezier"]'
        )
        expect(
            cb_custom_graph_page.locator('[data-testid="browser-routing-btn"]')
        ).to_contain_text("Unbundled Bezier")
        assert "routing=unbundled-bezier" in cb_custom_graph_page.url
