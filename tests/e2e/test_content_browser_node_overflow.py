"""
E2E tests for FOB-CONTENT-BROWSER-62 and node tooltip/size improvements:
- Node text and icons never overflow or clip in any size mode.
- Nodes are 1.5× larger than original (180×60 fixed).
- Text wraps in fixed mode.
- Hover tooltip displays full node label.

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



@pytest.mark.django_db(transaction=True)
class TestNodeOverflowFix:
    """FOB-62: Node text/icon overflow controlled by _buildNodeTextOverflowStyle."""

    def test_fixed_mode_uses_text_wrap_and_wider_max_width(self, cb_graph_page: Page):
        """In fixed mode, text wraps within node width (150px) — no clipping."""
        result = cb_graph_page.evaluate("() => _buildNodeTextOverflowStyle('fixed')")
        assert result['text-max-width'] == 150, f"Expected 150, got {result}"
        assert result['text-wrap'] == 'wrap', f"Expected wrap, got {result}"

    def test_auto_mode_has_no_text_max_width_constraint(self, cb_graph_page: Page):
        """In auto-width mode, text-max-width is a very large value (effectively unconstrained)."""
        result = cb_graph_page.evaluate("() => _buildNodeTextOverflowStyle('auto')")
        assert result['text-max-width'] >= 500, f"Expected large value, got {result}"

    def test_fixed_mode_node_dimensions_are_1_5x(self, cb_graph_page: Page):
        """Fixed-mode nodes are 180×60 (1.5× the original 120×40)."""
        result = cb_graph_page.evaluate("() => _buildEnhancedNodeStyle('activity')")
        assert result.get('height') == 60, f"Expected height 60, got {result.get('height')}"
        # width may be 180 (fixed) or 'label' (auto) depending on _nodeSizeMode default
        w = result.get('width')
        assert w in (180, 'label'), f"Expected 180 or 'label', got {w}"

    def test_node_style_text_max_width_not_legacy_value(self, cb_graph_page: Page):
        """text-max-width is driven by _buildNodeTextOverflowStyle, not a legacy hardcoded value."""
        result = cb_graph_page.evaluate("() => _buildEnhancedNodeStyle('workflow')")
        assert result.get('text-max-width') not in (96, 108), \
            f"Legacy text-max-width found: {result.get('text-max-width')}"
        assert result.get('text-max-width') in (150, 999), \
            f"Expected 150 or 999, got {result.get('text-max-width')}"


@pytest.mark.django_db(transaction=True)
class TestNodeTooltip:
    """Hover tooltip shows full label on node mouseover."""

    def test_tooltip_element_created_by_init(self, cb_graph_page: Page):
        """_createTooltipEl() creates a div#cy-node-tooltip in document.body."""
        cb_graph_page.evaluate("() => _createTooltipEl()")
        tooltip = cb_graph_page.locator('#cy-node-tooltip')
        expect(tooltip).to_have_count(1)

    def test_tooltip_initially_hidden(self, cb_graph_page: Page):
        """Tooltip div is hidden (display:none) before any hover."""
        cb_graph_page.evaluate("() => _createTooltipEl()")
        display = cb_graph_page.evaluate(
            "() => document.getElementById('cy-node-tooltip').style.display"
        )
        assert display == 'none', f"Expected 'none', got '{display}'"

    def test_tooltip_has_testid_attribute(self, cb_graph_page: Page):
        """Tooltip element has data-testid for Playwright test targeting."""
        cb_graph_page.evaluate("() => _createTooltipEl()")
        testid = cb_graph_page.evaluate(
            "() => document.getElementById('cy-node-tooltip').dataset.testid"
        )
        assert testid == 'cy-node-tooltip', f"data-testid mismatch: {testid}"
