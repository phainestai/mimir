"""
E2E tests for Content Browser enhanced node visual styling (FOB-38).

Covers:
  - FOB-CONTENT-BROWSER-38: Uniform round-rectangle shape, pastel Bootstrap 5.3 palette,
    FontAwesome icons per type, uniform black (#212529) edges, no text overflow.

Checkpoint command:
  pytest tests/e2e/test_content_browser_node_styles.py -x
"""
import pytest
from playwright.sync_api import Page

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


def _get_stylesheet_for_type(page: Page, node_type: str) -> dict:
    """Return the computed Cytoscape stylesheet entry for a given node type."""
    return page.evaluate(f"""
        () => {{
            const style = window._buildEnhancedNodeStyle('{node_type}');
            return style;
        }}
    """)


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    """Log in and navigate to the content browser graph for any released playbook."""
    user = django_user_model.objects.create_user(username='style_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'style_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


# ── S47: Uniform shape ────────────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestNodeShape:
    """FOB-38: All node types must use uniform round-rectangle shape (S47)."""

    def test_all_node_types_use_round_rectangle(self, graph_page: Page):
        """Every node type stylesheet entry specifies round-rectangle shape."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['shape'] == 'round-rectangle', \
                f"{node_type} should use round-rectangle, got {style.get('shape')}"

    def test_all_node_types_use_montserrat_font(self, graph_page: Page):
        """All nodes in cy stylesheet specify Montserrat as font-family."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert 'Montserrat' in style['font-family'], f"{node_type} missing Montserrat font"

    def test_all_nodes_have_2px_border_width(self, graph_page: Page):
        """All node selectors specify border-width 2 in Cytoscape stylesheet."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['border-width'] == 2, f"{node_type} border-width should be 2"


# ── S47: Pastel Bootstrap 5.3 palette ─────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestNodePastelPalette:
    """FOB-38: Node background colours must be pastel Bootstrap 5.3 tints (S47)."""

    EXPECTED_BACKGROUNDS = {
        'playbook':  '#e0cffc',
        'workflow':  '#cfe2ff',
        'activity':  '#d1e7dd',
        'artifact':  '#fff3cd',
        'skill':     '#ffe5d0',
        'agent':     '#cff4fc',
        'rule':      '#e2e3e5',
    }

    def test_all_node_types_use_pastel_backgrounds(self, graph_page: Page):
        """Each node type background-color matches the pastel Bootstrap 5.3 palette."""
        for node_type, expected_hex in self.EXPECTED_BACKGROUNDS.items():
            style = _get_stylesheet_for_type(graph_page, node_type)
            bg = style.get('background-color', '').lower()
            assert expected_hex in bg or expected_hex.lstrip('#') in bg, \
                f"{node_type} expected background {expected_hex}, got {bg}"

    def test_node_text_colours_are_dark_on_pastel(self, graph_page: Page):
        """Node text colours are dark (not white) to ensure readability on pastel bg (S47)."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            color = style.get('color', '').lower()
            assert '#ffffff' not in color and 'rgb(255, 255, 255)' not in color, \
                f"{node_type} should not use white text on pastel background, got {color}"


# ── S47: Uniform black edges ───────────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestEdgeColour:
    """FOB-38: All edges must use uniform black #212529 colour (S47)."""

    def test_edges_use_black_line_colour(self, graph_page: Page):
        """All edges rendered in cy have line-color #212529 (S47)."""
        non_black = graph_page.evaluate("""
        () => window.cy.edges().filter(e => {
            const c = e.style('line-color').toLowerCase();
            return !c.includes('#212529') && !c.includes('rgb(33, 37, 41)');
        }).length
        """)
        assert non_black == 0, f"{non_black} edges do not use black line colour"

    def test_build_edge_style_returns_array(self, graph_page: Page):
        """_buildEdgeStyle() returns an array of stylesheet objects (S47)."""
        result = graph_page.evaluate("() => Array.isArray(window._buildEdgeStyle())")
        assert result is True, "_buildEdgeStyle should return an array"

    def test_build_edge_style_contains_black_edge_entry(self, graph_page: Page):
        """_buildEdgeStyle() includes an entry with line-color #212529 (S47)."""
        entries = graph_page.evaluate("() => window._buildEdgeStyle()")
        found_black = any(
            '#212529' in str(entry.get('style', {}).get('line-color', ''))
            for entry in entries
        )
        assert found_black, "No black edge entry found in _buildEdgeStyle output"


# ── S47: FA icons in node labels ───────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestNodeIcons:
    """FOB-38: Node labels must include a FontAwesome icon glyph prefix (S47)."""

    def test_build_node_icon_returns_glyph_for_each_type(self, graph_page: Page):
        """_buildNodeIcon(type) returns a non-empty string for all node types (S47)."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            glyph = graph_page.evaluate(f"() => window._buildNodeIcon('{node_type}')")
            assert glyph and len(glyph) > 0, f"_buildNodeIcon('{node_type}') returned empty"

    def test_build_node_icon_glyphs_are_fa_unicode(self, graph_page: Page):
        """_buildNodeIcon returns codepoints in FontAwesome Private Use Area (S47)."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            glyph = graph_page.evaluate(f"() => window._buildNodeIcon('{node_type}')")
            code_points = [ord(c) for c in (glyph or '')]
            has_glyph = any(0xE000 <= cp <= 0xF8FF for cp in code_points)
            assert has_glyph, f"No FA glyph codepoint for {node_type}: {repr(glyph)}"
