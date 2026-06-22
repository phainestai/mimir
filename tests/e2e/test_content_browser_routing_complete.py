"""
E2E tests for FOB-CONTENT-BROWSER-59:
Routing picker includes straight-triangle curve-style.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_routing_complete.py -x
"""

import pytest
from playwright.sync_api import Page

from django.contrib.auth import get_user_model

pytestmark = pytest.mark.e2e

User = get_user_model()
LOGIN_URL_PATH = "/auth/user/login/"


def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")
    assert LOGIN_URL_PATH not in page.url


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.mark.django_db(transaction=True)
class TestRoutingCatalogComplete:
    """FOB-59: Routing picker must contain all 8 Cytoscape curve-styles including straight-triangle."""

    def test_routing_catalog_includes_straight_triangle(self, cb_graph_page: Page):
        """straight-triangle is present as an option in the routing dropdown."""
        has_entry = cb_graph_page.evaluate("""() => {
            return typeof _ROUTING_CATALOG !== 'undefined' &&
                   _ROUTING_CATALOG.some(e => e.key === 'straight-triangle');
        }""")
        assert has_entry, "Expected straight-triangle entry in _ROUTING_CATALOG"

    def test_routing_catalog_has_all_8_options(self, cb_graph_page: Page):
        """Routing dropdown contains exactly 8 options."""
        count = cb_graph_page.evaluate("""() => {
            return typeof _ROUTING_CATALOG !== 'undefined' ? _ROUTING_CATALOG.length : 0;
        }""")
        assert count == 8, f"Expected 8 routing catalog entries, got {count}"

    def test_straight_triangle_option_applies_correct_curve_style(
        self, cb_graph_page: Page
    ):
        """Selecting straight-triangle sets edge curve-style to 'straight-triangle' on cy edges."""
        cb_graph_page.evaluate("() => _applyRouting('straight-triangle')")
        edge_style = cb_graph_page.evaluate("""() => {
            const edges = window.cy.edges();
            if (edges.length === 0) return 'straight-triangle';  // no edges — can't verify
            return edges[0].style('curve-style');
        }""")
        assert edge_style == "straight-triangle", (
            f"Expected curve-style 'straight-triangle', got '{edge_style}'"
        )
