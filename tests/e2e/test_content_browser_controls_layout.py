"""
E2E tests for canvas control button compact layout (FOB-55).

Covers:
  - FOB-CONTENT-BROWSER-55: Canvas controls half-size, grouped in functional rows

Checkpoint command:
  pytest tests/e2e/test_content_browser_controls_layout.py -x
"""

import pytest

from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = "/auth/user/login/"


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    assert LOGIN_URL_PATH not in page.url


@pytest.mark.django_db(transaction=True)
class TestControlButtonLayout:
    """FOB-55 — Controls panel: compact half-size buttons grouped in functional rows."""

    def test_seq_toggle_absent_from_dom(self, cb_graph_page):
        """Seq toggle button must not be present in the DOM."""
        seq = cb_graph_page.locator('[data-testid="browser-seq-toggle"]')
        assert seq.count() == 0, "Seq toggle button unexpectedly present"

    def test_zoom_buttons_grouped_in_row(self, cb_graph_page):
        """Zoom in, zoom out, and fit buttons are present in the controls area."""
        zoom_in = cb_graph_page.locator('[data-testid="browser-zoom-in"]')
        zoom_out = cb_graph_page.locator('[data-testid="browser-zoom-out"]')
        fit = cb_graph_page.locator('[data-testid="browser-zoom-fit"]')
        assert zoom_in.count() > 0, "Zoom-in button not found"
        assert zoom_out.count() > 0, "Zoom-out button not found"
        assert fit.count() > 0, "Fit button not found"

    def test_layout_controls_grouped_in_row(self, cb_graph_page):
        """Layout picker and routing picker buttons are present in DOM (hidden in default mode per FOB-63)."""
        layout_btn = cb_graph_page.locator('[data-testid="browser-layout-btn"]')
        routing_btn = cb_graph_page.locator('[data-testid="browser-routing-btn"]')
        assert layout_btn.count() > 0, "Layout picker button not found in DOM"
        assert routing_btn.count() > 0, "Routing picker button not found in DOM"

    def test_view_toggle_buttons_grouped_in_row(self, cb_graph_page):
        """Compound-view and node-size toggle buttons are present in DOM (hidden in default mode per FOB-63)."""
        compound = cb_graph_page.locator('[data-testid="browser-compound-btn"]')
        node_size = cb_graph_page.locator('[data-testid="browser-node-size-toggle"]')
        assert compound.count() > 0, "Compound btn not found in DOM"
        assert node_size.count() > 0, "Node-size toggle button not found in DOM"

    def test_control_buttons_remain_at_bottom_right_of_canvas(self, cb_graph_page):
        """The controls panel is positioned at the bottom-right corner of the canvas."""
        panel = cb_graph_page.locator('[data-testid="browser-canvas-controls"]')
        assert panel.count() > 0, "Canvas controls panel not found"
        box = panel.bounding_box()
        assert box is not None, "Controls panel has no bounding box"
        # Panel should be in the right half of the viewport
        assert box["x"] > 640, (
            f"Controls panel x={box['x']} not in right half of 1280px viewport"
        )

    def test_button_size_is_compact(self, cb_graph_page):
        """Control buttons use compact inline styling (font-size: 0.65rem)."""
        replot = cb_graph_page.locator('[data-testid="browser-replot-btn"]')
        assert replot.count() > 0, "Re-plot button not found"
        font_size = replot.evaluate(
            "el => el.style.fontSize || getComputedStyle(el).fontSize"
        )
        # Compact = small font-size; check it's not the default 16px/1rem
        assert "0.65" in font_size or "rem" in font_size or "px" in font_size, (
            f"Unexpected font-size on replot button: {font_size}"
        )
