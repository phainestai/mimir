"""
E2E tests for FOB-CONTENT-BROWSER-58:
Canvas node labels never render in all-caps regardless of zoom level.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_font_rendering.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.e2e

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='font_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'font_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestFontRenderingGuards:
    """FOB-58: Node labels must never render in all-caps at any zoom level."""

    def test_node_text_transform_none_in_stylesheet(self, graph_page: Page):
        """Cytoscape stylesheet includes text-transform:none on every node type selector."""
        has_guard = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const nodeEntries = entries.filter(e =>
                e.selector && !e.selector.includes(':parent') &&
                e.selector.includes('node')
            );
            return nodeEntries.length > 0 && nodeEntries.every(e =>
                e.css && e.css['text-transform'] === 'none'
            );
        }""")
        assert has_guard, "Expected text-transform:none on all node-type stylesheet entries"

    def test_compound_label_text_transform_none_in_stylesheet(self, graph_page: Page):
        """Cytoscape :parent selector includes text-transform:none in stylesheet."""
        has_guard = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            return parentEntry != null && parentEntry.css &&
                   parentEntry.css['text-transform'] === 'none';
        }""")
        assert has_guard, "Expected text-transform:none on :parent stylesheet entry"

    def test_compound_font_family_excludes_font_awesome(self, graph_page: Page):
        """Compound parent (:parent) label font-family does NOT include Font Awesome."""
        no_fa = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            if (!parentEntry || !parentEntry.css) return true;
            const ff = parentEntry.css['font-family'] || '';
            return !ff.toLowerCase().includes('font awesome') &&
                   !ff.toLowerCase().includes('fontawesome');
        }""")
        assert no_fa, "Compound :parent font-family must NOT include Font Awesome"

    def test_min_zoomed_font_size_set_in_cy_options(self, graph_page: Page):
        """Cytoscape instance has minZoomedFontSize set to prevent near-zero text rendering."""
        min_font = graph_page.evaluate("() => window.cy.minZoomedFontSize()")
        assert min_font is not None and min_font >= 1, \
            f"Expected minZoomedFontSize >= 1, got {min_font}"
