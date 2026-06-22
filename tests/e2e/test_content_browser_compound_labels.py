"""
E2E tests for compound-mode workflow label visibility (FOB-54).

Covers:
  - FOB-CONTENT-BROWSER-54: In grouped (compound) mode, each workflow shows its name
    as a visible label above the top-left corner of its bounding box.

Checkpoint command:
  pytest tests/e2e/test_content_browser_compound_labels.py -x
"""
import pytest
from playwright.sync_api import Page

from e2e_helpers import set_compound_level, wait_for_cy_graph


@pytest.mark.django_db(transaction=True)
class TestCompoundModeLabelVisibility:
    """FOB-54 — Compound mode workflow parent nodes show their name as a visible label."""

    def test_compound_parent_nodes_have_label_property(self, cb_graph_page: Page):
        """cy.nodes(':parent') have a non-empty label in compound mode."""
        cb_graph_page.wait_for_function(
            "() => window.cy.nodes().filter(n => n.isParent()).length > 0",
            timeout=10_000,
        )
        labels = cb_graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).map(n => n.data('label'))"
        )
        assert len(labels) > 0, "No parent nodes found in compound mode"
        for label in labels:
            assert label, f"Parent node has empty label: {label!r}"

    def test_compound_stylesheet_sets_label_explicitly(self, cb_graph_page: Page):
        """_buildCompoundLabelStyle includes a label property (function or string)."""
        style = cb_graph_page.evaluate(
            "() => { const s = _buildCompoundLabelStyle(); return typeof s['label']; }"
        )
        assert style in ('function', 'string'), (
            f"Expected 'label' in compound style to be function or string, got '{style}'"
        )

    def test_compound_label_position_is_top_center(self, cb_graph_page: Page):
        """Compound label style uses valign:top and halign:center."""
        valign = cb_graph_page.evaluate(
            "() => _buildCompoundLabelStyle()['text-valign']"
        )
        halign = cb_graph_page.evaluate(
            "() => _buildCompoundLabelStyle()['text-halign']"
        )
        assert valign == 'top', f"Expected text-valign 'top', got '{valign}'"
        assert halign == 'center', f"Expected text-halign 'center', got '{halign}'"

    def test_workflow_label_is_workflow_name(self, cb_graph_page: Page):
        """The label on a compound parent node equals the workflow's name."""
        cb_graph_page.wait_for_function(
            "() => window.cy.nodes().filter(n => n.isParent()).length > 0",
            timeout=10_000,
        )
        result = cb_graph_page.evaluate("""() => {
            const parent = window.cy.nodes().filter(n => n.isParent())[0];
            if (!parent) return null;
            return { id: parent.id(), label: parent.data('label') };
        }""")
        assert result is not None, "No parent node found"
        assert result['label'], f"Parent node '{result['id']}' has no label"

    def test_flat_mode_compound_labels_not_shown(self, cb_graph_page: Page):
        """In flat (ungrouped) mode no nodes are parents (no compound labels)."""
        set_compound_level(cb_graph_page, 'none')
        wait_for_cy_graph(cb_graph_page)
        parent_count = cb_graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).length"
        )
        assert parent_count == 0, f"Expected 0 parent nodes in flat mode, got {parent_count}"
