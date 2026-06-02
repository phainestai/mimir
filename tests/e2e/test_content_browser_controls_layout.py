"""
E2E tests for canvas control button compact layout (FOB-55).

Covers:
  - FOB-CONTENT-BROWSER-55: Canvas controls half-size, grouped in functional rows

Checkpoint command:
  pytest tests/e2e/test_content_browser_controls_layout.py -x
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
    user = django_user_model.objects.create_user(username='controls_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'controls_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestControlButtonLayout:
    """FOB-55 — Controls panel: compact half-size buttons grouped in functional rows."""

    def test_seq_toggle_absent_from_dom(self, graph_page):
        """FOB-51: seq toggle button must not be present in the DOM."""
        raise NotImplementedError

    def test_zoom_buttons_grouped_in_row(self, graph_page):
        """Zoom in / zoom out / fit buttons are siblings in the same row."""
        raise NotImplementedError

    def test_layout_controls_grouped_in_row(self, graph_page):
        """Layout picker, re-layout, and routing picker are grouped in the same row."""
        raise NotImplementedError

    def test_view_toggle_buttons_grouped_in_row(self, graph_page):
        """Compound-view toggle, node-size toggle are in their own row."""
        raise NotImplementedError

    def test_control_buttons_remain_at_bottom_right_of_canvas(self, graph_page):
        """The controls panel is positioned at the bottom-right corner of the canvas."""
        raise NotImplementedError

    def test_button_size_is_compact(self, graph_page):
        """All control buttons have btn-sm class (compact size)."""
        raise NotImplementedError
