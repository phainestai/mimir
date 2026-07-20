"""
E2E tests for removal of the seq toggle button (FOB-51).

Covers:
  - FOB-CONTENT-BROWSER-51: Seq toggle button removed; predecessor edges always rendered.

Checkpoint command:
  pytest tests/e2e/test_content_browser_no_seq_toggle.py -x
"""

import pytest
from playwright.sync_api import Page

from e2e_helpers import wait_for_cy_graph


@pytest.mark.django_db(transaction=True)
class TestSeqToggleRemoved:
    """FOB-51 — seq toggle button must not exist; predecessor edges always rendered."""

    def test_seq_toggle_button_absent(self, cb_graph_page: Page):
        """[data-testid='browser-seq-toggle'] does not exist in the DOM."""
        seq_btn = cb_graph_page.locator('[data-testid="browser-seq-toggle"]')
        assert seq_btn.count() == 0, (
            "Seq toggle button should have been removed but is still present"
        )

    def test_predecessor_edges_always_visible(self, cb_graph_page: Page):
        """Predecessor edges are always present with dashed styling."""
        edge_count = cb_graph_page.evaluate("() => window.cy.edges().length")
        assert edge_count > 0, "Expected at least one edge on the graph"
        pred_count = cb_graph_page.evaluate(
            "() => window.cy.edges('[relationship = \"predecessor\"]').length"
        )
        assert pred_count > 0, "Expected predecessor edges to be rendered"
        dashed = cb_graph_page.evaluate("""() => {
            const e = window.cy.edges('[relationship = "predecessor"]').first();
            return e ? e.style('line-style') : '';
        }""")
        assert dashed == "dashed", (
            f"Expected dashed predecessor edges, got line-style={dashed!r}"
        )

    def test_seq_url_param_ignored(self, cb_graph_page: Page, live_server, cb_playbook):
        """Navigating with ?seq=0 loads graph normally (seq param does not cause errors)."""
        cb_graph_page.goto(f"{live_server.url}/browser/{cb_playbook['pb'].pk}/?seq=0")
        wait_for_cy_graph(cb_graph_page)
        seq_btn = cb_graph_page.locator('[data-testid="browser-seq-toggle"]')
        assert seq_btn.count() == 0, "Seq toggle appeared after loading with ?seq=0"

    def test_no_seq_state_exposed_on_window(self, cb_graph_page: Page):
        """window._seqEdgesOn is undefined (removed from window exposure)."""
        val = cb_graph_page.evaluate("() => typeof window._seqEdgesOn")
        assert val == "undefined", (
            f"Expected _seqEdgesOn to be undefined, got type '{val}'"
        )
