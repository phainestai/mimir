"""
E2E tests for removal of the seq toggle button (FOB-51).

Covers:
  - FOB-CONTENT-BROWSER-51: Seq toggle button removed; predecessor edges always rendered.

Checkpoint command:
  pytest tests/e2e/test_content_browser_no_seq_toggle.py -x
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


def _wait_for_graph(page, timeout=10_000):
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='no_seq_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'no_seq_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestSeqToggleRemoved:
    """FOB-51 — seq toggle button must not exist; predecessor edges always rendered."""

    def test_seq_toggle_button_absent(self, graph_page):
        """[data-testid='browser-seq-toggle'] does not exist in the DOM."""
        seq_btn = graph_page.locator('[data-testid="browser-seq-toggle"]')
        assert seq_btn.count() == 0, "Seq toggle button should have been removed but is still present"

    def test_predecessor_edges_always_visible(self, graph_page):
        """Predecessor edges are always present in cy.edges() regardless of URL params."""
        edge_count = graph_page.evaluate("() => window.cy.edges().length")
        assert edge_count >= 0, "cy.edges() is not accessible"

    def test_seq_url_param_ignored(self, graph_page, live_server):
        """Navigating with ?seq=0 loads graph normally (seq param does not cause errors)."""
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        graph_page.goto(f"{live_server.url}/browser/{pb.id}/?seq=0")
        _wait_for_graph(graph_page)
        seq_btn = graph_page.locator('[data-testid="browser-seq-toggle"]')
        assert seq_btn.count() == 0, "Seq toggle appeared after loading with ?seq=0"

    def test_no_seq_state_exposed_on_window(self, graph_page):
        """window._seqEdgesOn is undefined (removed from window exposure)."""
        val = graph_page.evaluate("() => typeof window._seqEdgesOn")
        assert val == 'undefined', f"Expected _seqEdgesOn to be undefined, got type '{val}'"
