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


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    """Log in and navigate to the content browser graph for any released playbook."""
    user = django_user_model.objects.create_user(username='routing_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'routing_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestRoutingCatalog:
    """FOB-35: Edge routing picker — catalog content and default state."""

    def test_routing_button_visible_in_canvas_controls(self, graph_page: Page):
        """browser-routing-btn is present in the canvas controls area."""
        btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_be_visible()

    def test_all_six_routing_options_present(self, graph_page: Page):
        """Dropdown contains all 6 routing options with correct data-testid values."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        expected_keys = ['bezier', 'straight', 'taxi', 'haystack', 'segments', 'round-segments']
        for key in expected_keys:
            opt = graph_page.locator(f'[data-testid="browser-routing-option-{key}"]')
            expect(opt).to_be_visible()
        # Close dropdown
        graph_page.keyboard.press('Escape')

    def test_default_routing_is_bezier(self, graph_page: Page):
        """Button shows 'Bezier (default)' label when no routing URL param is set."""
        btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text('Bezier (default)')

    def test_url_param_routing_sets_initial_state(self, graph_page: Page, live_server):
        """?routing=taxi causes button to show 'Orthogonal' on load."""
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        graph_page.goto(f"{live_server.url}/browser/graph/{pb.id}/?routing=taxi")
        _wait_for_graph(graph_page)
        btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text('Orthogonal')

    def test_unknown_routing_param_falls_back_to_bezier(self, graph_page: Page, live_server):
        """?routing=invalid causes silent fallback to bezier."""
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        graph_page.goto(f"{live_server.url}/browser/graph/{pb.id}/?routing=invalid")
        _wait_for_graph(graph_page)
        routing = graph_page.evaluate("() => window._currentRouting")
        assert routing == 'bezier'


@pytest.mark.django_db(transaction=True)
class TestRoutingPickerInteraction:
    """FOB-35: Edge routing picker — interaction and edge style update."""

    def test_click_opens_dropdown(self, graph_page: Page):
        """Clicking browser-routing-btn opens browser-routing-dropdown."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        dropdown = graph_page.locator('[data-testid="browser-routing-dropdown"]')
        expect(dropdown).to_be_visible()
        graph_page.keyboard.press('Escape')

    def test_select_straight_updates_button_label(self, graph_page: Page):
        """Selecting 'Straight' updates the routing button label to 'Straight'."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.click('[data-testid="browser-routing-option-straight"]')
        btn = graph_page.locator('[data-testid="browser-routing-btn"]')
        expect(btn).to_contain_text('Straight')

    def test_select_taxi_applies_curve_style_to_all_edges(self, graph_page: Page):
        """After selecting 'Orthogonal', all cy edges have curve-style 'taxi'."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.click('[data-testid="browser-routing-option-taxi"]')
        curve_styles = graph_page.evaluate(
            "() => window.cy.edges().map(e => e.style('curve-style'))"
        )
        assert all(s == 'taxi' for s in curve_styles), f"Expected all 'taxi', got: {set(curve_styles)}"

    def test_routing_change_does_not_rebuild_node_positions(self, graph_page: Page):
        """Edge style update does not trigger a layout re-run (node positions unchanged)."""
        positions_before = graph_page.evaluate(
            "() => window.cy.nodes().map(n => ({id: n.id(), x: Math.round(n.position('x')), y: Math.round(n.position('y'))}))"
        )
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.click('[data-testid="browser-routing-option-straight"]')
        positions_after = graph_page.evaluate(
            "() => window.cy.nodes().map(n => ({id: n.id(), x: Math.round(n.position('x')), y: Math.round(n.position('y'))}))"
        )
        assert positions_before == positions_after, "Node positions changed after routing update"

    def test_selected_routing_persisted_in_url_param(self, graph_page: Page):
        """After selecting 'Segments', URL contains ?routing=segments."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.click('[data-testid="browser-routing-option-segments"]')
        assert 'routing=segments' in graph_page.url, f"URL missing routing param: {graph_page.url}"

    def test_escape_closes_dropdown_without_changing_routing(self, graph_page: Page):
        """Pressing Escape closes dropdown; routing state is unchanged."""
        initial_routing = graph_page.evaluate("() => window._currentRouting")
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        graph_page.keyboard.press('Escape')
        expect(graph_page.locator('[data-testid="browser-routing-dropdown"]')).to_have_count(0)
        after_routing = graph_page.evaluate("() => window._currentRouting")
        assert after_routing == initial_routing

    def test_outside_click_closes_dropdown(self, graph_page: Page):
        """Clicking outside the dropdown closes it."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        graph_page.click('[data-testid="browser-canvas"]', position={"x": 10, "y": 10})
        expect(graph_page.locator('[data-testid="browser-routing-dropdown"]')).to_have_count(0)


    # ── S43 skeleton: unbundled-bezier in catalog ────────────────────────────

    def test_unbundled_bezier_option_present_in_dropdown(self, graph_page: Page):
        """Dropdown must include an unbundled-bezier option (S43 — FOB-35 fix)."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-routing-dropdown"]')
        expect(graph_page.locator('[data-testid="browser-routing-option-unbundled-bezier"]')).to_be_visible()

    def test_selecting_unbundled_bezier_applies_and_stores_param(self, graph_page: Page):
        """Selecting unbundled-bezier updates button label and URL param (S43)."""
        graph_page.click('[data-testid="browser-routing-btn"]')
        graph_page.click('[data-testid="browser-routing-option-unbundled-bezier"]')
        expect(graph_page.locator('[data-testid="browser-routing-btn"]')).to_contain_text('Unbundled Bezier')
        assert 'routing=unbundled-bezier' in graph_page.url
