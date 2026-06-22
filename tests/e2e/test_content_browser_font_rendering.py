"""
E2E tests for FOB-CONTENT-BROWSER-58:
Canvas node labels never render in all-caps regardless of zoom level.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_font_rendering.py -x
"""
import pytest
from playwright.sync_api import Page

pytestmark = pytest.mark.e2e


@pytest.mark.django_db(transaction=True)
class TestFontRenderingGuards:
    """FOB-58: Node labels must never render in all-caps at any zoom level."""

    def test_node_text_transform_none_in_stylesheet(self, cb_graph_page: Page):
        """Enhanced node style builder includes text-transform:none (FOB-58)."""
        has_guard = cb_graph_page.evaluate("""() => {
            const types = ['playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
            return types.every(t => _buildEnhancedNodeStyle(t)['text-transform'] === 'none');
        }""")
        assert has_guard, "Expected text-transform:none on all enhanced node styles"

    def test_compound_label_text_transform_none_in_stylesheet(self, cb_graph_page: Page):
        """Compound label builder includes text-transform:none."""
        has_guard = cb_graph_page.evaluate(
            "() => _buildCompoundLabelStyle()['text-transform'] === 'none'"
        )
        assert has_guard, "Expected text-transform:none on compound label style"

    def test_compound_font_family_excludes_font_awesome(self, cb_graph_page: Page):
        """Compound parent (:parent) label font-family does NOT include Font Awesome."""
        no_fa = cb_graph_page.evaluate("""() => {
            const entries = window.cy.style().json();
            const parentEntry = entries.find(e => e.selector === ':parent');
            if (!parentEntry || !parentEntry.style) return true;
            const ff = parentEntry.style['font-family'] || '';
            return !ff.toLowerCase().includes('font awesome') &&
                   !ff.toLowerCase().includes('fontawesome');
        }""")
        assert no_fa, "Compound :parent font-family must NOT include Font Awesome"

    def test_min_zoomed_font_size_set_in_cy_options(self, cb_graph_page: Page):
        """Cytoscape instance has minZoomedFontSize set to prevent near-zero text rendering."""
        min_font = cb_graph_page.evaluate("""() => {
            if (typeof window.cy.minZoomedFontSize === 'function') {
                return window.cy.minZoomedFontSize();
            }
            return window.cy._private?.options?.minZoomedFontSize;
        }""")
        assert min_font is not None and min_font >= 1, \
            f"Expected minZoomedFontSize >= 1, got {min_font}"
