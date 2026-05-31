"""
E2E tests for Content Browser URL management.

Tests scenarios from docs/features/act-16-content-browser/01-access-and-nav.feature:
  FOB-CONTENT-BROWSER-03b — URL is the source of truth for active playbook and filters
  FOB-CONTENT-BROWSER-03f — URL filter params are normalised on load

Requires: Playwright, a running dev server, and a seeded database.
Run: pytest tests/e2e/test_content_browser_url.py -x
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.fixture
def browser_url(live_server):
    """Return base URL for the Content Browser."""
    return f"{live_server.url}/browser"


@pytest.mark.django_db(transaction=True)
class TestURLManagement:
    """S3 — Client-side URL management (pushState + param normalisation)."""

    # FOB-CONTENT-BROWSER-03b
    def test_playbook_switch_updates_url_via_push_state(self, page: Page, browser_url, two_playbooks):
        """Switching playbook updates URL to /browser/<new_pk>/ via pushState."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03b
    def test_back_button_returns_to_previous_playbook(self, page: Page, browser_url, two_playbooks):
        """Browser back button after playbook switch returns to previous /browser/<pk>/."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03b
    def test_active_filters_reflected_in_url_query_params(self, page: Page, browser_url, playbook_with_phases):
        """Active type/phase filters appear as query params in the URL."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03b
    def test_default_state_has_no_query_params(self, page: Page, browser_url, playbook_with_phases):
        """When all types visible and no phase filter: URL is clean (no query string)."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03b
    def test_shared_url_restores_filter_state(self, page: Page, browser_url, playbook_with_phases):
        """Navigating directly to /browser/<pk>/?types=workflow,activity restores filters."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03f
    def test_empty_types_param_treated_as_all_types_shown(self, page: Page, browser_url, seeded_playbook):
        """?types= (empty) → all entity types visible, URL rewritten to canonical."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03f
    def test_unknown_phase_ids_dropped_on_load(self, page: Page, browser_url, seeded_playbook):
        """Phase IDs not present in the playbook are dropped and URL rewritten."""
        raise NotImplementedError()

    # FOB-CONTENT-BROWSER-03f
    def test_invalid_params_do_not_hide_content(self, page: Page, browser_url, seeded_playbook):
        """Invalid params result in graph rendering normally (nothing hidden, no error)."""
        raise NotImplementedError()
