"""
E2E tests for FOB-CONTENT-BROWSER-59:
Routing picker includes straight-triangle curve-style.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_routing_complete.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _get_released_playbook_pk(page) -> int | None:
    """Return PK of first released playbook with at least one workflow, or None."""
    raise NotImplementedError()


def test_routing_catalog_includes_straight_triangle(page: Page, live_server):
    """straight-triangle is present as an option in the routing dropdown."""
    raise NotImplementedError()


def test_routing_catalog_has_all_8_options(page: Page, live_server):
    """Routing dropdown contains exactly 8 options including straight-triangle."""
    raise NotImplementedError()


def test_straight_triangle_option_applies_correct_curve_style(page: Page, live_server):
    """Selecting straight-triangle sets edge curve-style to 'straight-triangle' on cy edges."""
    raise NotImplementedError()
