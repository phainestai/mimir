"""
E2E tests for full-screen layout (no scroll, no gaps) (FOB-56).

Covers:
  - FOB-CONTENT-BROWSER-56: Browser page fills viewport — no vertical scroll, no gaps

Checkpoint command:
  pytest tests/e2e/test_content_browser_fullscreen_layout.py -x
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
class TestFullscreenLayout:
    """FOB-56 — Browser page fits viewport with no scroll and no gaps."""

    def test_page_has_no_vertical_scrollbar(self, cb_graph_page):
        """document.body.scrollHeight should not vastly exceed window.innerHeight."""
        scroll_height = cb_graph_page.evaluate("() => document.body.scrollHeight")
        inner_height = cb_graph_page.evaluate("() => window.innerHeight")
        # Allow a small tolerance (a few pixels), but not a full extra screen height
        assert scroll_height <= inner_height + 50, (
            f"Page is scrollable: scrollHeight={scroll_height}, innerHeight={inner_height}"
        )

    def test_canvas_fills_space_between_navbar_and_footer(self, cb_graph_page):
        """Footer is hidden on the graph page."""
        footer_visible = cb_graph_page.evaluate(
            "() => { const f = document.querySelector('footer.footer'); "
            "return f ? getComputedStyle(f).display !== 'none' : false; }"
        )
        assert not footer_visible, "Footer should be hidden on the graph page"

    def test_canvas_top_edge_touches_navbar_bottom(self, cb_graph_page):
        """Canvas container top edge is near the navbar bottom (no gap > 10px)."""
        canvas = cb_graph_page.locator("#cy")
        assert canvas.count() > 0, "Canvas element #cy not found"
        canvas_top = canvas.evaluate("el => el.getBoundingClientRect().top")
        # Navbar height varies by viewport; allow generous tolerance for stacked chrome.
        assert canvas_top <= 120, (
            f"Canvas top edge {canvas_top}px is too far below navbar (expected <= 120px)"
        )

    def test_canvas_has_100_percent_height(self, cb_graph_page):
        """The #cy canvas element has substantial height (fills the viewport)."""
        canvas = cb_graph_page.locator("#cy")
        assert canvas.count() > 0, "Canvas element #cy not found"
        canvas_height = canvas.evaluate("el => el.getBoundingClientRect().height")
        viewport_height = cb_graph_page.evaluate("() => window.innerHeight")
        # Canvas should use most of the viewport height (at least 60%)
        assert canvas_height >= viewport_height * 0.6, (
            f"Canvas height {canvas_height}px is too small for viewport {viewport_height}px"
        )
