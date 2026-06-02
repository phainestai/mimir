"""
E2E tests for Content Browser FA icon rendering in graph nodes (FOB-53).

Covers:
  - FOB-CONTENT-BROWSER-53: Node type icons render correctly using FA6 Free Unicode glyphs

Checkpoint command:
  pytest tests/e2e/test_content_browser_icons.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'

EXPECTED_ICONS = {
    'playbook':  '\uf5da',
    'workflow':  '\uf542',
    'activity':  '\ue0a3',
    'artifact':  '\uf06b',
    'skill':     '\uf544',
    'agent':     '\ue0c4',
    'rule':      '\uf24e',
}


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='icon_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'icon_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestNodeIconCodepoints:
    """FOB-53 — FA6 Free codepoints map to valid glyphs (no blank rectangles)."""

    def test_all_icon_codepoints_are_valid_fa6_free_glyphs(self, graph_page):
        """_buildNodeIcon returns codepoints that exist in FA6 Free solid."""
        raise NotImplementedError

    def test_icon_codepoints_match_feature_spec(self, graph_page):
        """Each node type maps to the exact codepoint in FOB-CONTENT-BROWSER-53."""
        raise NotImplementedError

    def test_font_family_includes_font_awesome_6_free_first(self, graph_page):
        """_buildEnhancedNodeStyle font-family starts with 'Font Awesome 6 Free'."""
        raise NotImplementedError

    def test_font_weight_is_900_for_solid_icons(self, graph_page):
        """font-weight must be 900 so FA6 solid icons render."""
        raise NotImplementedError

    def test_label_is_function_mapper_not_string_literal(self, graph_page):
        """label property is a function (ele => ...), not a plain string."""
        raise NotImplementedError
