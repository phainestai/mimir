"""
E2E tests for FOB-CONTENT-BROWSER-61:
Compound grouping button becomes a 3-option context menu.

Checkpoint command: pytest tests/e2e/test_content_browser_compound_grouping_menu.py -x
"""
import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


@pytest.mark.django_db(transaction=True)
class TestCompoundGroupingMenu:
    """FOB-61: Grouping dropdown replaces toggle; 3-level compound support."""

    def test_compound_dropdown_button_exists(self, cb_custom_graph_page: Page):
        """Grouping button with data-testid='browser-compound-btn' is present."""
        btn = cb_custom_graph_page.locator('[data-testid="browser-compound-btn"]')
        expect(btn).to_be_visible()

    def test_old_compound_toggle_button_removed(self, cb_custom_graph_page: Page):
        """Old data-testid='browser-compound-toggle' no longer exists in DOM."""
        old = cb_custom_graph_page.locator('[data-testid="browser-compound-toggle"]')
        expect(old).to_have_count(0)

    def test_compound_dropdown_has_three_options(self, cb_custom_graph_page: Page):
        """Clicking the grouping button shows exactly 3 options."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-dropdown"]')
        none_opt = cb_custom_graph_page.locator('[data-testid="browser-compound-option-none"]')
        wf_opt = cb_custom_graph_page.locator('[data-testid="browser-compound-option-workflow"]')
        wa_opt = cb_custom_graph_page.locator('[data-testid="browser-compound-option-workflow-activity"]')
        expect(none_opt).to_be_visible()
        expect(wf_opt).to_be_visible()
        expect(wa_opt).to_be_visible()
        cb_custom_graph_page.keyboard.press('Escape')

    def test_compound_option_none_activates_flat_mode(self, cb_custom_graph_page: Page):
        """Selecting 'No Grouping' sets _compoundLevel to 'none' (flat graph)."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-none"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-option-none"]')
        level = cb_custom_graph_page.evaluate("() => window._compoundLevel")
        assert level == 'none', f"Expected 'none', got '{level}'"

    def test_compound_option_workflow_activates_workflow_grouping(self, cb_custom_graph_page: Page):
        """Selecting 'Group by workflow' sets _compoundLevel to 'workflow'."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-option-workflow"]')
        level = cb_custom_graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow', f"Expected 'workflow', got '{level}'"

    def test_compound_option_workflow_activity_activates_two_level_grouping(
        self, cb_custom_graph_page: Page,
    ):
        """Selecting 'Group by workflow + activity' sets _compoundLevel to 'workflow-activity'."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow-activity"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-option-workflow-activity"]')
        level = cb_custom_graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow-activity', f"Expected 'workflow-activity', got '{level}'"

    def test_compound_url_param_encodes_level(self, cb_custom_graph_page: Page):
        """URL param 'compound' is updated when a grouping option is selected."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-option-workflow"]')
        assert 'compound=workflow' in cb_custom_graph_page.url

    def test_compound_level_window_property_exposed(self, cb_custom_graph_page: Page):
        """window._compoundLevel defaults to workflow-activity (FOB-63 default mode)."""
        level = cb_custom_graph_page.evaluate("() => window._compoundLevel")
        assert level == 'workflow-activity', f"Expected 'workflow-activity', got '{level}'"

    def test_compound_active_option_shows_checkmark(self, cb_custom_graph_page: Page):
        """Active grouping option shows checkmark (✓) in dropdown."""
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-option-workflow"]')
        cb_custom_graph_page.click('[data-testid="browser-compound-btn"]')
        cb_custom_graph_page.wait_for_selector('[data-testid="browser-compound-option-workflow"]')
        wf_btn = cb_custom_graph_page.locator('[data-testid="browser-compound-option-workflow"]')
        assert '✓' in wf_btn.text_content(), "Active option should show ✓"
        cb_custom_graph_page.keyboard.press('Escape')
