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
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestFullscreenLayout:
    """FOB-56 — Browser page fits viewport with no scroll and no gaps."""

    def test_page_has_no_vertical_scrollbar(self, graph_page):
        """document.body.scrollHeight should equal window.innerHeight (no overflow)."""
        raise NotImplementedError

    def test_canvas_fills_space_between_navbar_and_footer(self, graph_page):
        """Canvas div bottom edge equals footer top edge (no gap)."""
        raise NotImplementedError

    def test_canvas_top_edge_touches_navbar_bottom(self, graph_page):
        """Canvas div top edge equals navbar bottom edge (no gap above canvas)."""
        raise NotImplementedError

    def test_canvas_has_100_percent_height(self, graph_page):
        """The canvas container uses 100% height via CSS (not fixed pixel value)."""
        raise NotImplementedError
