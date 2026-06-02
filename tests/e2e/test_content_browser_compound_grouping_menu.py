"""
E2E tests for FOB-CONTENT-BROWSER-61:
Compound grouping button becomes a 3-option context menu.

Checkpoint command: uv run pytest tests/e2e/test_content_browser_compound_grouping_menu.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


def _get_released_playbook_pk(page) -> int | None:
    """Return PK of first released playbook with at least one workflow, or None."""
    raise NotImplementedError()


def test_compound_dropdown_button_exists(page: Page, live_server):
    """Grouping button with data-testid='browser-compound-btn' is present."""
    raise NotImplementedError()


def test_old_compound_toggle_button_removed(page: Page, live_server):
    """Old data-testid='browser-compound-toggle' no longer exists in DOM."""
    raise NotImplementedError()


def test_compound_dropdown_has_three_options(page: Page, live_server):
    """Clicking the grouping button shows exactly 3 options."""
    raise NotImplementedError()


def test_compound_option_none_activates_flat_mode(page: Page, live_server):
    """Selecting 'No Grouping' sets _compoundLevel to 'none' (flat graph)."""
    raise NotImplementedError()


def test_compound_option_workflow_activates_workflow_grouping(page: Page, live_server):
    """Selecting 'Group by Workflow' sets _compoundLevel to 'workflow'."""
    raise NotImplementedError()


def test_compound_option_workflow_activity_activates_two_level_grouping(page: Page, live_server):
    """Selecting 'Group by Workflow & Activity' sets _compoundLevel to 'workflow-activity'."""
    raise NotImplementedError()


def test_compound_url_param_encodes_level(page: Page, live_server):
    """URL param 'compound' is updated to none/workflow/workflow-activity on selection."""
    raise NotImplementedError()


def test_compound_level_window_property_exposed(page: Page, live_server):
    """window._compoundLevel is accessible via page.evaluate."""
    raise NotImplementedError()


def test_compound_active_option_shows_checkmark(page: Page, live_server):
    """Active grouping option shows checkmark (✓) in dropdown."""
    raise NotImplementedError()
