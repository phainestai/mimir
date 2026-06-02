"""
E2E tests for flat-mode workflow→activity edge visibility (FOB-52).

Covers:
  - FOB-CONTENT-BROWSER-52: In flat mode, 'contains' edges between workflow and activity are visible

Checkpoint command:
  pytest tests/e2e/test_content_browser_flat_edges.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='flat_edge_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'flat_edge_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestFlatModeContainsEdges:
    """FOB-52 — In flat mode, workflow→activity 'contains' edges are visible."""

    def test_contains_edges_visible_in_flat_mode(self, graph_page):
        """In flat (ungrouped) mode, contains edges are rendered (not display:none)."""
        raise NotImplementedError

    def test_contains_edges_hidden_in_compound_mode(self, graph_page):
        """In compound (grouped) mode, contains edges are hidden."""
        raise NotImplementedError

    def test_workflow_connects_to_all_its_activities_in_flat_mode(self, graph_page):
        """Each workflow node has cy edges to each of its activities in flat mode."""
        raise NotImplementedError

    def test_flat_mode_graph_is_connected(self, graph_page):
        """No workflow or activity is isolated (disconnected) in flat mode."""
        raise NotImplementedError
