"""
E2E tests for FOB-CONTENT-BROWSER-62:
Node text and icons never overflow or clip in any size mode.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_node_overflow.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _get_released_playbook_pk(page) -> int | None:
    """Return PK of first released playbook with at least one workflow, or None."""
    raise NotImplementedError()


def test_fixed_mode_uses_text_max_width_for_text_portion(page: Page, live_server):
    """In fixed mode, text-max-width constrains text WITHOUT clipping the icon glyph."""
    raise NotImplementedError()


def test_auto_mode_has_no_text_max_width_constraint(page: Page, live_server):
    """In auto-width mode, text-max-width is not set (or set to a very large value)."""
    raise NotImplementedError()


def test_auto_mode_node_width_is_label_driven(page: Page, live_server):
    """In auto mode, node width property is 'label' (expands to fit text)."""
    raise NotImplementedError()


def test_toggling_size_mode_triggers_reflow(page: Page, live_server):
    """Toggling node size mode calls _runLayout() and visibly repositions nodes."""
    raise NotImplementedError()
