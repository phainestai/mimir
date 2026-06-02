"""
E2E tests for FOB-CONTENT-BROWSER-60:
Compound node labels are always visible with distinct activity colouring.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_compound_labels_v2.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _get_released_playbook_pk(page) -> int | None:
    """Return PK of first released playbook with at least one workflow, or None."""
    raise NotImplementedError()


def test_compound_label_font_size_is_20px(page: Page, live_server):
    """Compound parent :parent selector has font-size 20 (1.5x base 13px)."""
    raise NotImplementedError()


def test_compound_label_uses_padding_top_approach(page: Page, live_server):
    """Compound parent style uses padding-top >= 28px to reserve space for label."""
    raise NotImplementedError()


def test_compound_label_has_text_background(page: Page, live_server):
    """Compound parent style sets text-background-opacity > 0 for readable label."""
    raise NotImplementedError()


def test_workflow_compound_background_colour(page: Page, live_server):
    """Workflow compound nodes have background '#eef2ff'."""
    raise NotImplementedError()


def test_activity_compound_background_colour_distinct_from_workflow(page: Page, live_server):
    """In workflow-activity mode, activity compound nodes have background '#d4edda' (not '#eef2ff')."""
    raise NotImplementedError()
