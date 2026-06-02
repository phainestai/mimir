"""
E2E tests for Content Browser edge routing picker (FOB-35).

Covers:
  - FOB-CONTENT-BROWSER-35: Edge routing picker — dropdown to select Cytoscape curve-style

Checkpoint command:
  pytest tests/e2e/test_content_browser_routing_picker.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model


User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    """Authenticate via browser form login."""
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed; still on login page. URL: {page.url}"


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    """Wait until Cytoscape is initialised with at least one node."""
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.mark.django_db(transaction=True)
class TestRoutingCatalog:
    """FOB-35: Edge routing picker — catalog content and default state."""

    def test_routing_button_visible_in_canvas_controls(self, page: Page, live_server):
        """browser-routing-btn is present in the canvas controls area."""
        raise NotImplementedError

    def test_all_six_routing_options_present(self, page: Page, live_server):
        """Dropdown contains all 6 routing options with correct data-testid values."""
        raise NotImplementedError

    def test_default_routing_is_bezier(self, page: Page, live_server):
        """Button shows 'Bezier (default)' label when no routing URL param is set."""
        raise NotImplementedError

    def test_url_param_routing_sets_initial_state(self, page: Page, live_server):
        """?routing=taxi causes button to show 'Orthogonal' on load."""
        raise NotImplementedError

    def test_unknown_routing_param_falls_back_to_bezier(self, page: Page, live_server):
        """?routing=invalid causes silent fallback to bezier."""
        raise NotImplementedError


@pytest.mark.django_db(transaction=True)
class TestRoutingPickerInteraction:
    """FOB-35: Edge routing picker — interaction and edge style update."""

    def test_click_opens_dropdown(self, page: Page, live_server):
        """Clicking browser-routing-btn opens browser-routing-dropdown."""
        raise NotImplementedError

    def test_select_straight_updates_button_label(self, page: Page, live_server):
        """Selecting 'Straight' updates the routing button label to 'Straight'."""
        raise NotImplementedError

    def test_select_taxi_applies_curve_style_to_all_edges(self, page: Page, live_server):
        """After selecting 'Orthogonal', all cy edges have curve-style 'taxi'."""
        raise NotImplementedError

    def test_routing_change_does_not_rebuild_node_positions(self, page: Page, live_server):
        """Edge style update does not trigger a layout re-run (_elkLayoutCount unchanged)."""
        raise NotImplementedError

    def test_selected_routing_persisted_in_url_param(self, page: Page, live_server):
        """After selecting 'Segments', URL contains ?routing=segments."""
        raise NotImplementedError

    def test_escape_closes_dropdown_without_changing_routing(self, page: Page, live_server):
        """Pressing Escape closes dropdown; routing state is unchanged."""
        raise NotImplementedError

    def test_outside_click_closes_dropdown(self, page: Page, live_server):
        """Clicking outside the dropdown closes it."""
        raise NotImplementedError
