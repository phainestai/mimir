"""
E2E tests for Content Browser enhanced node visual styling (FOB-38).

Covers:
  - FOB-CONTENT-BROWSER-38: Node shapes and styles fit Mimir design language

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


@pytest.mark.django_db(transaction=True)
class TestNodeStyles:
    """FOB-38: Enhanced node shapes and Mimir-aligned visual styling."""

    def test_workflow_node_uses_round_rectangle_shape(self, graph_page: Page):
        """Workflow nodes render with round-rectangle shape in Cytoscape stylesheet."""
        style = _get_stylesheet_for_type(graph_page, 'workflow')
        assert style['shape'] == 'round-rectangle'

    def test_activity_node_uses_bottom_round_rectangle_shape(self, graph_page: Page):
        """Activity nodes render with bottom-round-rectangle shape."""
        style = _get_stylesheet_for_type(graph_page, 'activity')
        assert style['shape'] == 'bottom-round-rectangle'

    def test_artifact_node_uses_round_diamond_shape(self, graph_page: Page):
        """Artifact nodes render with round-diamond shape."""
        style = _get_stylesheet_for_type(graph_page, 'artifact')
        assert style['shape'] == 'round-diamond'

    def test_skill_node_uses_hexagon_shape(self, graph_page: Page):
        """Skill nodes render with hexagon shape."""
        style = _get_stylesheet_for_type(graph_page, 'skill')
        assert style['shape'] == 'hexagon'

    def test_rule_node_uses_cut_rectangle_shape(self, graph_page: Page):
        """Rule nodes render with cut-rectangle shape."""
        style = _get_stylesheet_for_type(graph_page, 'rule')
        assert style['shape'] == 'cut-rectangle'

    def test_agent_node_uses_ellipse_shape(self, graph_page: Page):
        """Agent nodes retain ellipse shape."""
        style = _get_stylesheet_for_type(graph_page, 'agent')
        assert style['shape'] == 'ellipse'

    def test_all_node_types_use_montserrat_font(self, graph_page: Page):
        """All nodes in cy stylesheet specify Montserrat as font-family."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert 'Montserrat' in style['font-family'], f"{node_type} missing Montserrat font"

    def test_structural_nodes_have_font_weight_600(self, graph_page: Page):
        """Playbook, Workflow, Activity nodes have font-weight 600 in stylesheet."""
        for node_type in ('playbook', 'workflow', 'activity'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['font-weight'] == 600, f"{node_type} font-weight should be 600"

    def test_resource_nodes_have_font_weight_400(self, graph_page: Page):
        """Artifact, Skill, Agent, Rule nodes have font-weight 400 in stylesheet."""
        for node_type in ('artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['font-weight'] == 400, f"{node_type} font-weight should be 400"

    def test_all_nodes_have_2px_border_width(self, graph_page: Page):
        """All node selectors specify border-width 2 in Cytoscape stylesheet."""
        for node_type in ('playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'):
            style = _get_stylesheet_for_type(graph_page, node_type)
            assert style['border-width'] == 2, f"{node_type} border-width should be 2"

    def test_playbook_node_uses_round_octagon_shape(self, graph_page: Page):
        """Playbook node uses round-octagon shape (most prominent anchor node)."""
        style = _get_stylesheet_for_type(graph_page, 'playbook')
        assert style['shape'] == 'round-octagon'
