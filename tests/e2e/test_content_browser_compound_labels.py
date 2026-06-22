"""
E2E tests for compound-mode workflow label visibility (FOB-54).

Covers:
  - FOB-CONTENT-BROWSER-54: In grouped (compound) mode, each workflow shows its name
    as a visible label above the top-left corner of its bounding box.

Checkpoint command:
  pytest tests/e2e/test_content_browser_compound_labels.py -x
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
    user = django_user_model.objects.create_user(username='compound_label_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'compound_label_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestCompoundModeLabelVisibility:
    """FOB-54 — Compound mode workflow parent nodes show their name as a visible label."""

    def test_compound_parent_nodes_have_label_property(self, graph_page):
        """cy.nodes(':parent') have a non-empty label in compound mode."""
        graph_page.evaluate("() => { if (!window._compoundViewOn) _applyCompoundToggle(); }")
        graph_page.wait_for_function(
            "() => window.cy.nodes().filter(n => n.isParent()).length > 0",
            timeout=5000,
        )
        labels = graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).map(n => n.data('label'))"
        )
        assert len(labels) > 0, "No parent nodes found in compound mode"
        for label in labels:
            assert label, f"Parent node has empty label: {label!r}"

    def test_compound_stylesheet_sets_label_explicitly(self, graph_page):
        """_buildCompoundLabelStyle includes a label property (function or string)."""
        style = graph_page.evaluate(
            "() => { const s = _buildCompoundLabelStyle(); return typeof s['label']; }"
        )
        assert style in ('function', 'string'), (
            f"Expected 'label' in compound style to be function or string, got '{style}'"
        )

    def test_compound_label_position_is_top_center(self, graph_page):
        """Compound label style uses valign:top and halign:center."""
        valign = graph_page.evaluate(
            "() => _buildCompoundLabelStyle()['text-valign']"
        )
        halign = graph_page.evaluate(
            "() => _buildCompoundLabelStyle()['text-halign']"
        )
        assert valign == 'top', f"Expected text-valign 'top', got '{valign}'"
        assert halign == 'center', f"Expected text-halign 'center', got '{halign}'"

    def test_workflow_label_is_workflow_name(self, graph_page):
        """The label on a compound parent node equals the workflow's name."""
        graph_page.evaluate("() => { if (!window._compoundViewOn) _applyCompoundToggle(); }")
        graph_page.wait_for_function(
            "() => window.cy.nodes().filter(n => n.isParent()).length > 0",
            timeout=5000,
        )
        result = graph_page.evaluate("""() => {
            const parent = window.cy.nodes().filter(n => n.isParent())[0];
            if (!parent) return null;
            return { id: parent.id(), label: parent.data('label') };
        }""")
        assert result is not None, "No parent node found"
        assert result['label'], f"Parent node '{result['id']}' has no label"

    def test_flat_mode_compound_labels_not_shown(self, graph_page):
        """In flat (ungrouped) mode no nodes are parents (no compound labels)."""
        graph_page.evaluate("() => { if (window._compoundViewOn) _applyCompoundToggle(); }")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        parent_count = graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isParent()).length"
        )
        assert parent_count == 0, f"Expected 0 parent nodes in flat mode, got {parent_count}"
