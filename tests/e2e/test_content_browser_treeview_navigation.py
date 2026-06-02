"""
E2E tests for uniform treeview-to-canvas behaviour on workflow/activity clicks (FOB-58 / FOB-26b).

Covers:
  - FOB-26 (updated): Clicking a workflow row in treeview expands its accordion section
  - FOB-58 / FOB-27b: Clicking any treeview row moves camera to that node + opens detail panel;
    clicking an activity on canvas expands the parent workflow accordion in the treeview.

Checkpoint command:
  pytest tests/e2e/test_content_browser_treeview_navigation.py -x
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


def _wait_for_graph(page, timeout=10_000):
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='tree_nav_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'tree_nav_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


class TestTreeviewWorkflowClick:
    """FOB-26 updated — clicking workflow row expands accordion and navigates to workflow node."""

    def test_workflow_row_click_expands_accordion_section(self, graph_page):
        """Clicking a collapsed workflow row opens its children section in the treeview."""
        raise NotImplementedError

    def test_workflow_row_click_centers_camera_on_workflow_node(self, graph_page):
        """Clicking a workflow row moves the canvas camera so the workflow node is visible."""
        raise NotImplementedError

    def test_workflow_row_click_opens_detail_panel(self, graph_page):
        """Clicking a workflow row opens the right-side detail panel for that workflow."""
        raise NotImplementedError


class TestTreeviewActivityClick:
    """FOB-58 — clicking activity row navigates to node; canvas click expands treeview."""

    def test_activity_row_click_centers_camera_on_activity_node(self, graph_page):
        """Clicking an activity row moves the canvas camera to that activity node."""
        raise NotImplementedError

    def test_activity_row_click_opens_detail_panel(self, graph_page):
        """Clicking an activity row opens the right-side detail panel for that activity."""
        raise NotImplementedError

    def test_canvas_tap_activity_expands_parent_workflow_in_treeview(self, graph_page):
        """Clicking an activity node on canvas expands its parent workflow in the treeview."""
        raise NotImplementedError

    def test_canvas_tap_activity_highlights_row_in_treeview(self, graph_page):
        """After clicking an activity on canvas, the matching treeview row gets active styling."""
        raise NotImplementedError
