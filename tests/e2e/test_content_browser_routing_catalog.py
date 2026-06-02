"""
E2E tests for complete edge routing catalog (FOB-57).

Covers:
  - FOB-CONTENT-BROWSER-57: All valid Cytoscape curve-style values are selectable;
    'round-seg' key corrected to 'round-segments'; taxi present.

Checkpoint command:
  pytest tests/e2e/test_content_browser_routing_catalog.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'

EXPECTED_ROUTING_KEYS = [
    'bezier',
    'unbundled-bezier',
    'straight',
    'taxi',
    'haystack',
    'segments',
    'round-segments',
]

EXPECTED_CY_VALUES = {
    'bezier': 'bezier',
    'unbundled-bezier': 'unbundled-bezier',
    'straight': 'straight',
    'taxi': 'taxi',
    'haystack': 'haystack',
    'segments': 'segments',
    'round-segments': 'round-segments',
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
    user = django_user_model.objects.create_user(username='routing_catalog_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'routing_catalog_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestRoutingCatalog:
    """FOB-57 — All standard Cytoscape routing styles are present and correctly keyed."""

    def test_routing_catalog_contains_all_expected_keys(self, graph_page):
        """_ROUTING_CATALOG has exactly the 7 expected entries."""
        raise NotImplementedError

    def test_round_segments_key_is_correct(self, graph_page):
        """'round-seg' old key must not exist; 'round-segments' must exist."""
        raise NotImplementedError

    def test_taxi_is_present_in_catalog(self, graph_page):
        """'taxi' entry is in _ROUTING_CATALOG with cyValue 'taxi'."""
        raise NotImplementedError

    def test_cy_values_match_valid_cytoscape_curve_styles(self, graph_page):
        """Each entry's cyValue is a valid Cytoscape.js curve-style value."""
        raise NotImplementedError

    def test_routing_dropdown_shows_all_catalog_entries(self, graph_page):
        """The routing dropdown/picker contains one item per _ROUTING_CATALOG entry."""
        raise NotImplementedError

    def test_applying_taxi_routing_sets_curve_style_on_edges(self, graph_page):
        """Selecting taxi routing applies curve-style:taxi to all cy edges."""
        raise NotImplementedError

    def test_applying_round_segments_sets_correct_cy_style(self, graph_page):
        """Selecting round-segments applies curve-style:round-segments (not round-seg)."""
        raise NotImplementedError
