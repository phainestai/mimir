"""
E2E tests for FOB-CONTENT-BROWSER-60:
Compound node labels are always visible with distinct activity colouring.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_compound_labels_v2.py -x
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
    user = django_user_model.objects.create_user(username='compound_labels_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'compound_labels_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestCompoundLabelVisibility:
    """FOB-60: Compound labels always visible with correct colours and font size."""

    def test_compound_label_font_size_is_20px(self, graph_page: Page):
        """Compound parent :parent selector has font-size 20."""
        font_size = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            return parentEntry && parentEntry.css ? parentEntry.css['font-size'] : null;
        }""")
        assert font_size is not None, "Expected :parent entry in stylesheet"
        assert float(str(font_size).replace('px', '')) == pytest.approx(20, abs=2), \
            f"Expected compound label font-size ~20, got {font_size}"

    def test_compound_label_uses_padding_top_approach(self, graph_page: Page):
        """Compound parent style uses padding-top >= 28 to reserve space for label."""
        padding = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            if (!parentEntry || !parentEntry.css) return null;
            const pt = parentEntry.css['padding-top'];
            return pt ? parseFloat(pt) : null;
        }""")
        assert padding is not None and padding >= 20, \
            f"Expected compound padding-top >= 20px, got {padding}"

    def test_compound_label_has_text_background(self, graph_page: Page):
        """Compound parent style sets text-background-opacity > 0 for readable label."""
        opacity = graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            if (!parentEntry || !parentEntry.css) return 0;
            return parseFloat(parentEntry.css['text-background-opacity'] || 0);
        }""")
        assert opacity > 0, f"Expected text-background-opacity > 0, got {opacity}"

    def test_workflow_compound_background_colour(self, graph_page: Page):
        """Workflow compound nodes have theme cool-cyan wash background."""
        bg = graph_page.evaluate("() => _compoundBackgroundForType('workflow')")
        assert bg == '#e4f2f7', f"Expected '#e4f2f7' for workflow compound, got '{bg}'"

    def test_activity_compound_background_colour_distinct_from_workflow(self, graph_page: Page):
        """In workflow-activity mode, activity compound nodes have mint wash background."""
        bg = graph_page.evaluate("() => _compoundBackgroundForType('activity')")
        assert bg == '#e2f3ec', f"Expected '#e2f3ec' for activity compound, got '{bg}'"
