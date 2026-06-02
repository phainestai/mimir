"""
E2E tests for node size toggle triggering layout reflow (FOB-50).

Covers:
  - FOB-CONTENT-BROWSER-50: Switching node size mode visibly repositions nodes on canvas

Checkpoint command:
  pytest tests/e2e/test_content_browser_node_size_reflow.py -x
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
    user = django_user_model.objects.create_user(username='size_reflow_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'size_reflow_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    return page


class TestNodeSizeReflow:
    """FOB-50 — Toggling node size mode calls _runLayout so nodes reposition."""

    def test_toggle_to_auto_width_triggers_layout_rerun(self, graph_page):
        """Switching to auto-width mode runs _runLayout after stylesheet update."""
        raise NotImplementedError

    def test_toggle_to_fixed_size_triggers_layout_rerun(self, graph_page):
        """Switching back to fixed-size mode also runs _runLayout."""
        raise NotImplementedError

    def test_auto_width_nodes_width_reflects_label_length(self, graph_page):
        """In auto-width mode, nodes with longer names are visibly wider."""
        raise NotImplementedError

    def test_fixed_size_nodes_all_same_width(self, graph_page):
        """In fixed-size mode all activity nodes have the same computed width."""
        raise NotImplementedError
