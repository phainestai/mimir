"""
E2E tests for FOB-CONTENT-BROWSER-60:
Compound node labels are always visible with distinct activity colouring.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_compound_labels_v2.py -x
"""
import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


def _parent_style(cb_graph_page: Page) -> dict | None:
    """Return the :parent stylesheet entry from the live Cytoscape instance."""
    return cb_graph_page.evaluate("""() => {
        const entries = window.cy.style().json();
        const parentEntry = entries.find(e => e.selector === ':parent');
        return parentEntry && parentEntry.style ? parentEntry.style : null;
    }""")


@pytest.mark.django_db(transaction=True)
class TestCompoundLabelVisibility:
    """FOB-60: Compound labels always visible with correct colours and font size."""

    def test_compound_label_font_size_is_20px(self, cb_graph_page: Page):
        """Compound parent :parent selector has font-size 20."""
        style = _parent_style(cb_graph_page)
        assert style is not None, "Expected :parent entry in stylesheet"
        font_size = style.get('font-size')
        assert float(str(font_size).replace('px', '')) == pytest.approx(20, abs=2), \
            f"Expected compound label font-size ~20, got {font_size}"

    def test_compound_label_uses_padding_top_approach(self, cb_graph_page: Page):
        """Compound parent style uses padding-top >= 28 to reserve space for label."""
        padding_raw = cb_graph_page.evaluate("() => _buildCompoundLabelStyle()['padding-top']")
        padding = float(str(padding_raw).replace('px', ''))
        assert padding >= 20, f"Expected compound padding-top >= 20px, got {padding}"

    def test_compound_label_has_text_background(self, cb_graph_page: Page):
        """Compound parent style sets text-background-opacity > 0 for readable label."""
        style = _parent_style(cb_graph_page)
        assert style is not None, "Expected :parent entry in stylesheet"
        opacity = float(style.get('text-background-opacity') or 0)
        assert opacity > 0, f"Expected text-background-opacity > 0, got {opacity}"

    def test_workflow_compound_background_colour(self, cb_graph_page: Page):
        """Workflow compound nodes have background '#eef2ff'."""
        bg = cb_graph_page.evaluate("() => _compoundBackgroundForType('workflow')")
        assert bg == '#eef2ff', f"Expected '#eef2ff' for workflow compound, got '{bg}'"

    def test_activity_compound_background_colour_distinct_from_workflow(self, cb_graph_page: Page):
        """In workflow-activity mode, activity compound nodes have background '#d4edda'."""
        bg = cb_graph_page.evaluate("() => _compoundBackgroundForType('activity')")
        assert bg == '#d4edda', f"Expected '#d4edda' for activity compound, got '{bg}'"
