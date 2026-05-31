"""
E2E tests for Content Browser structural tree (FOB-24/25/26/27).

Run: DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_structure_tree.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Phase

User = get_user_model()

LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed. URL: {page.url}"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def st_user(transactional_db):
    user = User.objects.create_user(
        username='st_user', email='st@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def st_playbook(st_user, transactional_db):
    """Playbook with 2 workflows, 2 activities each, one phase."""
    pb = Playbook.objects.create(
        name='StructureTestPB', description='For structure tree tests',
        category='development', status='draft', version='0.1',
        source='owned', author=st_user, visibility='public',
    )
    phase = Phase.objects.create(name='Build', playbook=pb, order=1)
    wf1 = Workflow.objects.create(name='Workflow One', playbook=pb, order=1)
    wf2 = Workflow.objects.create(name='Workflow Two', playbook=pb, order=2)
    Activity.objects.create(name='Activity Alpha', workflow=wf1, order=1, phase=phase)
    Activity.objects.create(name='Activity Beta',  workflow=wf1, order=2)
    Activity.objects.create(name='Activity Gamma', workflow=wf2, order=1)
    return pb


# ---------------------------------------------------------------------------
# FOB-24: Structural tree renders
# ---------------------------------------------------------------------------

class TestStructureTreeRendering:

    def test_structure_tree_present_after_graph_load(self, page: Page, live_server, st_user, st_playbook):
        """Structure tree container is present in left panel (FOB-24)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')

        expect(page.locator('[data-testid="browser-structure-tree"]')).to_be_visible()

    def test_structure_tree_shows_workflow_rows(self, page: Page, live_server, st_user, st_playbook):
        """Structure tree has a row for each workflow (FOB-24)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        tree_rows = page.locator('[data-testid="browser-tree-row"]')
        row_texts = [tree_rows.nth(i).inner_text() for i in range(tree_rows.count())]
        combined = ' '.join(row_texts)
        assert 'Workflow One' in combined
        assert 'Workflow Two' in combined

    def test_structure_tree_shows_activity_rows(self, page: Page, live_server, st_user, st_playbook):
        """Structure tree has rows for activities (FOB-24)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        tree_rows = page.locator('[data-testid="browser-tree-row"]')
        row_texts = ' '.join(tree_rows.nth(i).inner_text() for i in range(tree_rows.count()))
        assert 'Activity Alpha' in row_texts
        assert 'Activity Beta'  in row_texts
        assert 'Activity Gamma' in row_texts

    def test_activity_row_shows_phase_chip(self, page: Page, live_server, st_user, st_playbook):
        """Activity with a phase shows a coloured chip in its tree row (FOB-27)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Find the row for Activity Alpha and check it contains a coloured circle chip.
        rows = page.locator('[data-testid="browser-tree-row"]')
        alpha_row = None
        for i in range(rows.count()):
            if 'Activity Alpha' in rows.nth(i).inner_text():
                alpha_row = rows.nth(i)
                break
        assert alpha_row is not None, "Row for Activity Alpha not found"
        chip = alpha_row.locator('span.rounded-circle')
        expect(chip).to_have_count(1)


# ---------------------------------------------------------------------------
# FOB-25: Clicking tree row navigates canvas
# ---------------------------------------------------------------------------

class TestStructureTreeNavigation:

    def test_clicking_activity_row_does_not_open_detail_panel(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Clicking an activity tree row navigates canvas but does NOT open detail panel (FOB-25)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        rows = page.locator('[data-testid="browser-tree-row"]')
        for i in range(rows.count()):
            if 'Activity Alpha' in rows.nth(i).inner_text():
                rows.nth(i).click()
                break

        page.wait_for_timeout(400)
        # Detail panel should remain hidden after tree row click (navigation only).
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()


# ---------------------------------------------------------------------------
# FOB-26: Selected canvas node is highlighted in tree
# ---------------------------------------------------------------------------

class TestStructureTreeHighlight:

    def test_canvas_node_tap_highlights_tree_row(self, page: Page, live_server, st_user, st_playbook):
        """Tapping a canvas node highlights the corresponding tree row (FOB-26)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Tap the first canvas node via JS.
        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes().first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(400)

        # At least one tree row should now have the highlight class.
        highlighted = page.locator('[data-testid="browser-tree-row"].text-primary')
        assert highlighted.count() >= 1, "No tree row was highlighted after canvas node tap"

    def test_panel_close_clears_tree_highlight(self, page: Page, live_server, st_user, st_playbook):
        """Closing the detail panel clears the tree highlight (FOB-26)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes().first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(300)
        page.locator('[data-testid="browser-panel-close"]').click()
        page.wait_for_timeout(300)

        highlighted = page.locator('[data-testid="browser-tree-row"].text-primary')
        assert highlighted.count() == 0, "Tree highlight should be cleared after panel close"
