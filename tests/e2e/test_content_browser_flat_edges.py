"""
E2E tests for flat-mode workflow→activity edge visibility (FOB-52).

Covers:
  - FOB-CONTENT-BROWSER-52: In flat mode, 'contains' edges between workflow and activity are visible

Checkpoint command:
  pytest tests/e2e/test_content_browser_flat_edges.py -x
"""
import pytest
from playwright.sync_api import Page

from e2e_helpers import set_compound_level, wait_for_cy_graph


@pytest.mark.django_db(transaction=True)
class TestFlatModeContainsEdges:
    """FOB-52 — In flat mode, workflow→activity 'contains' edges are visible."""

    def test_contains_edges_visible_in_flat_mode(self, cb_graph_page: Page):
        """In flat (ungrouped) mode, contains edges exist in cy."""
        set_compound_level(cb_graph_page, 'none')
        wait_for_cy_graph(cb_graph_page)
        contains_count = cb_graph_page.evaluate(
            "() => window.cy.edges('[relationship=\"contains\"]').length"
        )
        assert contains_count > 0, "No 'contains' edges found in flat mode"

    def test_contains_edges_hidden_in_compound_mode(self, cb_graph_page: Page):
        """In compound mode, parent nodes exist and contains edges are hidden."""
        cb_graph_page.wait_for_function(
            "() => window.cy.nodes().filter(n => n.isParent()).length > 0",
            timeout=10_000,
        )
        parent_count = cb_graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).length"
        )
        assert parent_count > 0, "Expected compound parent nodes in workflow-activity mode"
        visible_contains = cb_graph_page.evaluate("""() => {
            return window.cy.edges('[relationship = "contains"]').filter(e => e.visible()).length;
        }""")
        assert visible_contains == 0, "Contains edges should be hidden in compound mode"

    def test_workflow_connects_to_all_its_activities_in_flat_mode(self, cb_graph_page: Page):
        """Each workflow node has at least one cy edge in flat mode."""
        set_compound_level(cb_graph_page, 'none')
        wait_for_cy_graph(cb_graph_page)
        wf_nodes = cb_graph_page.evaluate(
            "() => window.cy.nodes('[type=\"workflow\"]').map(n => n.id())"
        )
        assert wf_nodes, 'No workflow nodes in graph'
        for wf_id in wf_nodes[:3]:
            edges = cb_graph_page.evaluate(
                f"() => window.cy.edges('[source=\"{wf_id}\"], [target=\"{wf_id}\"]').length"
            )
            assert edges > 0, f"Workflow '{wf_id}' has no edges in flat mode"

    def test_flat_mode_graph_is_connected(self, cb_graph_page: Page):
        """In flat mode the graph has edges (not all nodes isolated)."""
        set_compound_level(cb_graph_page, 'none')
        wait_for_cy_graph(cb_graph_page)
        edge_count = cb_graph_page.evaluate("() => window.cy.edges().length")
        node_count = cb_graph_page.evaluate("() => window.cy.nodes().length")
        assert edge_count > 0, "Flat mode graph has no edges"
        assert node_count > 0, "Flat mode graph has no nodes"
