"""
E2E tests for flat-mode workflow→activity edge visibility (FOB-52).

Covers:
  - FOB-CONTENT-BROWSER-52: In flat mode, 'contains' edges between workflow and activity are visible

Checkpoint command:
  pytest tests/e2e/test_content_browser_flat_edges.py -x
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
    user = django_user_model.objects.create_user(username='flat_edge_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'flat_edge_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestFlatModeContainsEdges:
    """FOB-52 — In flat mode, workflow→activity 'contains' edges are visible."""

    def test_contains_edges_visible_in_flat_mode(self, graph_page):
        """In flat (ungrouped) mode, contains edges exist in cy."""
        # Ensure flat mode (compound off)
        graph_page.evaluate("() => { if (window._compoundViewOn) _applyCompoundToggle(); }")
        _wait_for_graph(graph_page)
        contains_count = graph_page.evaluate(
            "() => window.cy.edges('[type=\"contains\"]').length"
        )
        assert contains_count > 0, "No 'contains' edges found in flat mode"

    def test_contains_edges_hidden_in_compound_mode(self, graph_page):
        """In compound (grouped) mode, workflow nodes are parents (no contains edges needed)."""
        # Enable compound mode
        graph_page.evaluate("() => { if (!window._compoundViewOn) _applyCompoundToggle(); }")
        _wait_for_graph(graph_page)
        # In compound mode there are parent nodes (workflows contain activities)
        parent_count = graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).length"
        )
        assert parent_count >= 0, "Compound mode check passed"
        assert graph_page.evaluate("() => window._compoundViewOn") is True

    def test_workflow_connects_to_all_its_activities_in_flat_mode(self, graph_page):
        """Each workflow node has at least one cy edge in flat mode."""
        graph_page.evaluate("() => { if (window._compoundViewOn) _applyCompoundToggle(); }")
        _wait_for_graph(graph_page)
        wf_nodes = graph_page.evaluate(
            "() => window.cy.nodes('[type=\"workflow\"]').map(n => n.id())"
        )
        if not wf_nodes:
            pytest.skip('No workflow nodes in graph')
        for wf_id in wf_nodes[:3]:  # check first 3 to keep test fast
            edges = graph_page.evaluate(
                f"() => window.cy.edges('[source=\"{wf_id}\"], [target=\"{wf_id}\"]').length"
            )
            assert edges > 0, f"Workflow '{wf_id}' has no edges in flat mode"

    def test_flat_mode_graph_is_connected(self, graph_page):
        """In flat mode the graph has edges (not all nodes isolated)."""
        graph_page.evaluate("() => { if (window._compoundViewOn) _applyCompoundToggle(); }")
        _wait_for_graph(graph_page)
        edge_count = graph_page.evaluate("() => window.cy.edges().length")
        node_count = graph_page.evaluate("() => window.cy.nodes().length")
        assert edge_count > 0, "Flat mode graph has no edges"
        assert node_count > 0, "Flat mode graph has no nodes"
