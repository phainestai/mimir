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


def _wait_for_graph(page, timeout=10_000):
    page.wait_for_function(
        "() => window.cy != null && window.cy.edges().length > 0",
        timeout=timeout,
    )


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
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestRoutingCatalog:
    """FOB-57 — All standard Cytoscape routing styles are present and correctly keyed."""

    def test_routing_catalog_contains_all_expected_keys(self, graph_page):
        """The routing dropdown has one item per expected routing key."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        for key in EXPECTED_ROUTING_KEYS:
            item = graph_page.locator(f'[data-testid="browser-routing-option-{key}"]')
            assert item.count() == 1, f"Routing option for key '{key}' not found in dropdown"

    def test_round_segments_key_is_correct(self, graph_page):
        """'round-seg' old key must not exist; 'round-segments' must exist."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        old = graph_page.locator('[data-testid="browser-routing-option-round-seg"]')
        assert old.count() == 0, "'round-seg' key still present (not fixed to 'round-segments')"
        new = graph_page.locator('[data-testid="browser-routing-option-round-segments"]')
        assert new.count() == 1, "'round-segments' key not found in dropdown"

    def test_taxi_is_present_in_catalog(self, graph_page):
        """'taxi' entry is in the routing dropdown."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        taxi = graph_page.locator('[data-testid="browser-routing-option-taxi"]')
        assert taxi.count() == 1, "Taxi routing option not found in dropdown"

    def test_cy_values_match_valid_cytoscape_curve_styles(self, graph_page):
        """Applying each routing key sets _currentRouting to the expected key."""
        for key in EXPECTED_ROUTING_KEYS:
            graph_page.evaluate(f"() => _applyRouting('{key}')")
            current = graph_page.evaluate("() => window._currentRouting")
            assert current == key, f"After _applyRouting('{key}'), _currentRouting = '{current}'"

    def test_routing_dropdown_shows_all_catalog_entries(self, graph_page):
        """The routing dropdown has exactly 7 items (one per catalog entry)."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        items = graph_page.locator('[data-testid^="browser-routing-option-"]')
        assert items.count() == len(EXPECTED_ROUTING_KEYS), (
            f"Expected {len(EXPECTED_ROUTING_KEYS)} routing options, got {items.count()}"
        )

    def test_applying_taxi_routing_sets_curve_style_on_edges(self, graph_page):
        """Selecting taxi routing applies curve-style:taxi to edges in cy."""
        graph_page.evaluate("() => _applyRouting('taxi')")
        graph_page.wait_for_function("() => window.cy != null && window.cy.edges().length > 0")
        curve = graph_page.evaluate(
            "() => window.cy.edges()[0].style('curve-style')"
        )
        assert curve == 'taxi', f"Expected curve-style 'taxi', got '{curve}'"

    def test_applying_round_segments_sets_correct_cy_style(self, graph_page):
        """Selecting round-segments applies curve-style:round-segments (not round-seg)."""
        graph_page.evaluate("() => _applyRouting('round-segments')")
        graph_page.wait_for_function("() => window.cy != null && window.cy.edges().length > 0")
        curve = graph_page.evaluate(
            "() => window.cy.edges()[0].style('curve-style')"
        )
        assert curve == 'round-segments', (
            f"Expected curve-style 'round-segments', got '{curve}'"
        )
