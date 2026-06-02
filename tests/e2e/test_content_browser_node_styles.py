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


@pytest.mark.django_db(transaction=True)
class TestNodeStyles:
    """FOB-38: Enhanced node shapes and Mimir-aligned visual styling."""

    def test_workflow_node_uses_round_octagon_shape(self, page: Page, live_server):
        """Workflow nodes render with round-octagon shape in Cytoscape stylesheet."""
        raise NotImplementedError

    def test_activity_node_uses_bottom_round_rectangle_shape(self, page: Page, live_server):
        """Activity nodes render with bottom-round-rectangle shape."""
        raise NotImplementedError

    def test_artifact_node_uses_round_diamond_shape(self, page: Page, live_server):
        """Artifact nodes render with round-diamond shape."""
        raise NotImplementedError

    def test_skill_node_uses_hexagon_shape(self, page: Page, live_server):
        """Skill nodes render with hexagon shape."""
        raise NotImplementedError

    def test_rule_node_uses_cut_rectangle_shape(self, page: Page, live_server):
        """Rule nodes render with cut-rectangle shape."""
        raise NotImplementedError

    def test_agent_node_uses_ellipse_shape(self, page: Page, live_server):
        """Agent nodes retain ellipse shape."""
        raise NotImplementedError

    def test_all_node_types_use_montserrat_font(self, page: Page, live_server):
        """All nodes in cy stylesheet specify Montserrat as font-family."""
        raise NotImplementedError

    def test_structural_nodes_have_font_weight_600(self, page: Page, live_server):
        """Playbook, Workflow, Activity nodes have font-weight 600 in stylesheet."""
        raise NotImplementedError

    def test_resource_nodes_have_font_weight_400(self, page: Page, live_server):
        """Artifact, Skill, Agent, Rule nodes have font-weight 400 in stylesheet."""
        raise NotImplementedError

    def test_all_nodes_have_2px_border_width(self, page: Page, live_server):
        """All node selectors specify border-width 2 in Cytoscape stylesheet."""
        raise NotImplementedError
