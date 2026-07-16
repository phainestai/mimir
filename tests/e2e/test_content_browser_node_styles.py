"""
E2E tests for Content Browser enhanced node visual styling (FOB-38).

Covers:
  - FOB-CONTENT-BROWSER-38: Uniform round-rectangle shape, cool cyan-family palette
    (theme tokens --mimir-graph-*), FontAwesome icons per type, uniform theme-aware
    edges, no text overflow.

Checkpoint command:
  pytest tests/e2e/test_content_browser_node_styles.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model


User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'

# Light-theme graph tokens (must match design-system.css [data-bs-theme="light"]).
LIGHT_NODE_BACKGROUNDS = {
    'playbook': '#d4eef7',
    'workflow': '#cfe8f2',
    'activity': '#d4efe8',
    'artifact': '#f5edd8',
    'skill': '#f3e4d6',
    'agent': '#d6eef4',
    'rule': '#e4e8ed',
}
LIGHT_EDGE = '#5a6575'


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

    def test_all_node_types_use_ibm_plex_sans_font(self, graph_page: Page):
        """All nodes in cy stylesheet specify IBM Plex Sans as font-family."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert 'IBM Plex Sans' in style['font-family'], f"{node_type} missing IBM Plex Sans font"

    def test_all_nodes_have_2px_border_width(self, graph_page: Page):
        """All node selectors specify border-width 2 in Cytoscape stylesheet."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['border-width'] == 2, f"{node_type} border-width should be 2"


# ── S47: Theme-aware cool cyan palette ────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestNodePastelPalette:
    """FOB-38: Node backgrounds match --mimir-graph-* light theme tokens."""

    EXPECTED_BACKGROUNDS = LIGHT_NODE_BACKGROUNDS

    def test_all_node_types_use_pastel_backgrounds(self, graph_page: Page):
        """Each node type background-color matches the cool cyan-family light palette."""
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


# ── S47: Uniform theme-aware edges ─────────────────────────────────────────────

@pytest.mark.django_db(transaction=True)
class TestEdgeColour:
    """FOB-38: All edges use uniform theme slate (--mimir-graph-edge)."""

    def test_edges_use_theme_line_colour(self, graph_page: Page):
        """All edges rendered in cy have the light-theme edge colour."""
        non_matching = graph_page.evaluate(f"""
        () => {{
            const expected = '{LIGHT_EDGE}'.toLowerCase();
            return window.cy.edges().filter(e => {{
                const c = e.style('line-color').toLowerCase();
                return !c.includes(expected) && !c.includes('rgb(90, 101, 117)');
            }}).length;
        }}
        """)
        assert non_matching == 0, f"{non_matching} edges do not use theme edge colour {LIGHT_EDGE}"

    def test_build_edge_style_returns_array(self, graph_page: Page):
        """_buildEdgeStyle() returns an array of stylesheet objects (S47)."""
        result = graph_page.evaluate("() => Array.isArray(window._buildEdgeStyle())")
        assert result is True, "_buildEdgeStyle should return an array"

    def test_build_edge_style_contains_theme_edge_entry(self, graph_page: Page):
        """_buildEdgeStyle() includes an entry with the theme edge colour."""
        entries = graph_page.evaluate("() => window._buildEdgeStyle()")
        found = any(
            LIGHT_EDGE in str(entry.get('style', {}).get('line-color', ''))
            for entry in entries
        )
        assert found, f"No theme edge entry ({LIGHT_EDGE}) found in _buildEdgeStyle output"


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
