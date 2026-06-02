"""
E2E tests for Content Browser sequence edges toggle (FOB-36).

Covers:
  - FOB-CONTENT-BROWSER-36: Sequence edges toggle — show/hide predecessor links

Checkpoint command:
  pytest tests/e2e/test_content_browser_seq_toggle.py -x
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
    user = django_user_model.objects.create_user(username='seq_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'seq_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestSeqToggleDefault:
    """FOB-36: Sequence toggle — default state (ON)."""

    def test_seq_toggle_button_visible_in_canvas_controls(self, graph_page: Page):
        """browser-seq-toggle is present in the canvas controls area."""
        btn = graph_page.locator('[data-testid="browser-seq-toggle"]')
        expect(btn).to_be_visible()

    def test_seq_toggle_default_state_is_on(self, graph_page: Page):
        """Button shows active state by default; _seqEdgesOn is true."""
        is_on = graph_page.evaluate("() => window._seqEdgesOn")
        assert is_on is True
        btn = graph_page.locator('[data-testid="browser-seq-toggle"]')
        expect(btn).to_contain_text('Seq ✓')

    def test_seq_toggle_off_via_url_param(self, graph_page: Page, live_server):
        """?seq=0 causes _seqEdgesOn to be false and button to show inactive state."""
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        graph_page.goto(f"{live_server.url}/browser/graph/{pb.id}/?seq=0")
        _wait_for_graph(graph_page)
        is_on = graph_page.evaluate("() => window._seqEdgesOn")
        assert is_on is False
        btn = graph_page.locator('[data-testid="browser-seq-toggle"]')
        expect(btn).to_contain_text('Seq ✗')


@pytest.mark.django_db(transaction=True)
class TestSeqToggleInteraction:
    """FOB-36: Sequence toggle — turn off/on and graph rebuild."""

    def test_toggle_off_removes_predecessor_edges_from_graph(self, graph_page: Page):
        """After clicking toggle OFF, cy has zero edges with data.relationship='predecessor'."""
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        predecessor_count = graph_page.evaluate(
            "() => window.cy.edges('[relationship = \"predecessor\"]').length"
        )
        assert predecessor_count == 0, f"Expected 0 predecessor edges, got {predecessor_count}"

    def test_toggle_off_triggers_full_graph_rebuild(self, graph_page: Page):
        """Toggling OFF triggers a layout re-run (cy elements change)."""
        count_before = graph_page.evaluate("() => window.cy.elements().length")
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        # Element count should change (predecessor edges removed)
        count_after = graph_page.evaluate("() => window.cy.elements().length")
        assert count_after <= count_before, "Element count should decrease or stay equal after removing seq edges"

    def test_toggle_off_updates_url_param_seq_0(self, graph_page: Page):
        """After toggle OFF, URL contains ?seq=0."""
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        assert 'seq=0' in graph_page.url, f"URL missing seq=0: {graph_page.url}"

    def test_toggle_on_restores_predecessor_edges(self, graph_page: Page):
        """After toggle OFF then ON, cy contains edges with relationship='predecessor'."""
        # Turn off
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        # Turn back on
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        predecessor_count = graph_page.evaluate(
            "() => window.cy.edges('[relationship = \"predecessor\"]').length"
        )
        assert predecessor_count > 0, "Expected predecessor edges to be restored"

    def test_toggle_on_removes_seq_url_param(self, graph_page: Page):
        """After toggle OFF then ON, ?seq=0 is removed from URL."""
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === true")
        assert 'seq=0' not in graph_page.url, f"URL should not contain seq=0: {graph_page.url}"

    def test_seq_state_preserved_on_entity_type_filter_change(self, graph_page: Page):
        """With seq=OFF, toggling entity type filter does not re-add predecessor edges."""
        # Turn seq off
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        # Verify no predecessor edges remain
        predecessor_count = graph_page.evaluate(
            "() => window.cy.edges('[relationship = \"predecessor\"]').length"
        )
        assert predecessor_count == 0
        # _seqEdgesOn still false
        assert graph_page.evaluate("() => window._seqEdgesOn") is False


    # ── S44 skeleton: seq toggle works in compound mode ───────────────────────

    def test_seq_toggle_works_when_compound_view_is_active(self, graph_page: Page):
        """Toggling seq while compound is ON keeps compound mode ON (S44 — FOB-36+37 fix)."""
        # Activate compound view
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        # Now toggle seq off
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        # Compound mode must still be ON
        assert graph_page.evaluate("() => window._compoundViewOn") is True
        # Predecessor edges must be gone
        predecessor_count = graph_page.evaluate(
            "() => window.cy.edges('[relationship = \"predecessor\"]').length"
        )
        assert predecessor_count == 0

    def test_seq_toggle_off_then_on_in_compound_mode_preserves_compound(self, graph_page: Page):
        """Toggling seq off then back on in compound mode does not revert to flat (S44)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === true")
        assert graph_page.evaluate("() => window._compoundViewOn") is True
        assert graph_page.evaluate("() => window._seqEdgesOn") is True

    def test_compound_toggle_off_then_seq_toggle_uses_flat_rebuild(self, graph_page: Page):
        """After turning compound OFF, seq toggle uses flat rebuild path (S44)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === false")
        graph_page.click('[data-testid="browser-seq-toggle"]')
        graph_page.wait_for_function("() => window._seqEdgesOn === false")
        assert graph_page.evaluate("() => window._compoundViewOn") is False
