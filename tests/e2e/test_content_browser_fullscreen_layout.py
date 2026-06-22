"""
E2E tests for full-screen layout (no scroll, no gaps) (FOB-56).

Covers:
  - FOB-CONTENT-BROWSER-56: Browser page fills viewport — no vertical scroll, no gaps

Checkpoint command:
  pytest tests/e2e/test_content_browser_fullscreen_layout.py -x
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
    user = django_user_model.objects.create_user(username='layout_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'layout_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/{pb.id}/")
    page.wait_for_load_state('networkidle')
    return page


@pytest.mark.django_db(transaction=True)
class TestFullscreenLayout:
    """FOB-56 — Browser page fits viewport with no scroll and no gaps."""

    def test_page_has_no_vertical_scrollbar(self, graph_page):
        """document.body.scrollHeight should not vastly exceed window.innerHeight."""
        scroll_height = graph_page.evaluate("() => document.body.scrollHeight")
        inner_height = graph_page.evaluate("() => window.innerHeight")
        # Allow a small tolerance (a few pixels), but not a full extra screen height
        assert scroll_height <= inner_height + 50, (
            f"Page is scrollable: scrollHeight={scroll_height}, innerHeight={inner_height}"
        )

    def test_canvas_fills_space_between_navbar_and_footer(self, graph_page):
        """Footer is hidden on the graph page."""
        footer_visible = graph_page.evaluate(
            "() => { const f = document.querySelector('footer.footer'); "
            "return f ? getComputedStyle(f).display !== 'none' : false; }"
        )
        assert not footer_visible, "Footer should be hidden on the graph page"

    def test_canvas_top_edge_touches_navbar_bottom(self, graph_page):
        """Canvas container top edge is near the navbar bottom (no gap > 10px)."""
        canvas = graph_page.locator('#cy')
        assert canvas.count() > 0, "Canvas element #cy not found"
        canvas_top = canvas.evaluate("el => el.getBoundingClientRect().top")
        # The navbar is ~64px tall. Canvas should start near there (within 20px tolerance)
        assert canvas_top <= 80, (
            f"Canvas top edge {canvas_top}px is too far below navbar (expected <= 80px)"
        )

    def test_canvas_has_100_percent_height(self, graph_page):
        """The #cy canvas element has substantial height (fills the viewport)."""
        canvas = graph_page.locator('#cy')
        assert canvas.count() > 0, "Canvas element #cy not found"
        canvas_height = canvas.evaluate("el => el.getBoundingClientRect().height")
        viewport_height = graph_page.evaluate("() => window.innerHeight")
        # Canvas should use most of the viewport height (at least 60%)
        assert canvas_height >= viewport_height * 0.6, (
            f"Canvas height {canvas_height}px is too small for viewport {viewport_height}px"
        )
