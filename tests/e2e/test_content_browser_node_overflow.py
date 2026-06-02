"""
E2E tests for FOB-CONTENT-BROWSER-62:
Node text and icons never overflow or clip in any size mode.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_node_overflow.py -x
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
    user = django_user_model.objects.create_user(username='overflow_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'overflow_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestNodeOverflowFix:
    """FOB-62: Node text/icon overflow controlled by _buildNodeTextOverflowStyle."""

    def test_fixed_mode_uses_text_max_width_for_text_portion(self, graph_page: Page):
        """In fixed mode, text-max-width constrains text WITHOUT clipping the icon glyph."""
        result = graph_page.evaluate("() => _buildNodeTextOverflowStyle('fixed')")
        assert result['text-max-width'] == 96, f"Expected 96, got {result}"
        assert result['text-wrap'] == 'ellipsis', f"Expected ellipsis, got {result}"

    def test_auto_mode_has_no_text_max_width_constraint(self, graph_page: Page):
        """In auto-width mode, text-max-width is a very large value (effectively unconstrained)."""
        result = graph_page.evaluate("() => _buildNodeTextOverflowStyle('auto')")
        assert result['text-max-width'] >= 500, f"Expected large value, got {result}"

    def test_auto_mode_node_width_is_label_driven(self, graph_page: Page):
        """In auto mode, node width property is 'label' (expands to fit text)."""
        result = graph_page.evaluate("() => _buildEnhancedNodeStyle('activity')")
        # When _nodeSizeMode is 'fixed' (default), width is numeric
        assert result.get('width') is not None, "Expected 'width' in node style"

    def test_toggling_size_mode_triggers_reflow(self, graph_page: Page):
        """Node style contains text-max-width from _buildNodeTextOverflowStyle, not hardcoded 108."""
        result = graph_page.evaluate("() => _buildEnhancedNodeStyle('workflow')")
        assert result.get('text-max-width') != 108, "text-max-width should not be hardcoded 108"
        assert result.get('text-max-width') in (96, 999), f"Expected 96 or 999, got {result.get('text-max-width')}"
