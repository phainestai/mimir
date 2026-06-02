"""
E2E tests for FOB-CONTENT-BROWSER-58:
Canvas node labels never render in all-caps regardless of zoom level.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_font_rendering.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _get_released_playbook_pk(page) -> int | None:
    """Return PK of first released playbook with at least one workflow, or None."""
    raise NotImplementedError()


def test_node_text_transform_none_in_stylesheet(page: Page, live_server):
    """Cytoscape stylesheet includes text-transform:none on every node type selector."""
    raise NotImplementedError()


def test_compound_label_text_transform_none_in_stylesheet(page: Page, live_server):
    """Cytoscape :parent selector includes text-transform:none in stylesheet."""
    raise NotImplementedError()


def test_compound_font_family_excludes_font_awesome(page: Page, live_server):
    """Compound parent (:parent) label font-family does NOT include Font Awesome."""
    raise NotImplementedError()


def test_min_zoomed_font_size_set_in_cy_options(page: Page, live_server):
    """Cytoscape instance has minZoomedFontSize set to prevent near-zero text rendering."""
    raise NotImplementedError()
