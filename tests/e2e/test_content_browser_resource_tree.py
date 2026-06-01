"""
E2E tests for Content Browser resource tree (FOB-28/32).

Run: DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_resource_tree.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Skill, Rule

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
def rt_user(transactional_db):
    user = User.objects.create_user(
        username='rt_user', email='rt@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def rt_playbook(rt_user, transactional_db):
    """Playbook with 1 workflow, 2 activities sharing a skill; activity 1 also has a rule."""
    pb = Playbook.objects.create(
        name='ResourceTestPB', description='For resource tree tests',
        category='development', status='draft', version='0.1',
        source='owned', author=rt_user, visibility='public',
    )
    wf = Workflow.objects.create(name='MainWorkflow', playbook=pb, order=1)
    act1 = Activity.objects.create(name='Act One',   workflow=wf, order=1)
    act2 = Activity.objects.create(name='Act Two',   workflow=wf, order=2)

    shared_skill = Skill.objects.create(title='Shared Skill', playbook=pb)
    rule1        = Rule.objects.create(title='Rule Alpha',  playbook=pb)

    act1.skills.add(shared_skill)
    act2.skills.add(shared_skill)
    act1.rules.add(rule1)

    return pb


# ---------------------------------------------------------------------------
# FOB-28: Resource tree appears when workflow selected
# ---------------------------------------------------------------------------

class TestResourceTreeRendering:

    def test_resource_tree_placeholder_on_load(self, page: Page, live_server, rt_user, rt_playbook):
        """Resource tree shows placeholder text before any node is selected (FOB-28)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')

        tree = page.locator('[data-testid="browser-resource-tree"]')
        expect(tree).to_contain_text('Select a Workflow')

    def test_selecting_activity_shows_resource_tree(self, page: Page, live_server, rt_user, rt_playbook):
        """Selecting an activity node renders the resource tree (FOB-28)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Tap the activity node for Act One via JS
        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes('[type="activity"]').first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(500)

        tree = page.locator('[data-testid="browser-resource-tree"]')
        # Resource tree should no longer show the placeholder
        assert 'Select a Workflow' not in (tree.inner_text() or '')

    def test_resource_tree_shows_skill(self, page: Page, live_server, rt_user, rt_playbook):
        """Resource tree lists the skill linked to the selected activity (FOB-28)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes('[type="activity"]').first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(500)

        tree = page.locator('[data-testid="browser-resource-tree"]')
        expect(tree).to_contain_text('Shared Skill')

    def test_resource_tree_clears_on_panel_close(self, page: Page, live_server, rt_user, rt_playbook):
        """Closing the detail panel resets the resource tree to placeholder (FOB-28)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes('[type="activity"]').first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(400)
        page.locator('[data-testid="browser-panel-close"]').click()
        page.wait_for_timeout(300)

        tree = page.locator('[data-testid="browser-resource-tree"]')
        expect(tree).to_contain_text('Select a Workflow')

    def test_workflow_selection_aggregates_resources(self, page: Page, live_server, rt_user, rt_playbook):
        """Selecting a workflow shows resources from all its activities, deduplicated (FOB-28)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes('[type="workflow"]').first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(500)

        # Shared skill appears once (deduplicated by entity_pk)
        rows = page.locator('[data-testid="browser-resource-row"]')
        page.wait_for_selector('[data-testid="browser-resource-row"]', timeout=5000)
        skill_rows = [rows.nth(i) for i in range(rows.count())
                      if 'Shared Skill' in (rows.nth(i).inner_text() or '')]
        assert len(skill_rows) == 1, f"Expected 1 Shared Skill row, got {len(skill_rows)}"

    def test_activity_selection_shows_parent_workflow_resources(
        self, page: Page, live_server, rt_user, rt_playbook,
    ):
        """FOB-28 / S18: Selecting Activity shows parent Workflow's resources (all siblings)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # act1 has: Shared Skill + Rule Alpha
        # act2 has: Shared Skill
        # Clicking act2 should show BOTH Shared Skill AND Rule Alpha (parent wf aggregation)
        page.evaluate("""
            () => {
                // Get the second activity (act2)
                const acts = window.cy && window.cy.nodes('[type="activity"]');
                const act2 = acts && acts.length >= 2 ? acts[1] : null;
                if (act2) act2.trigger('tap');
            }
        """)
        page.wait_for_timeout(500)

        tree = page.locator('[data-testid="browser-resource-tree"]')
        # Should show resources from parent workflow (incl. act1's rule)
        expect(tree).to_contain_text('Rule Alpha')
        expect(tree).to_contain_text('Shared Skill')


# ---------------------------------------------------------------------------
# FOB-32: Clicking resource row opens detail panel
# ---------------------------------------------------------------------------

class TestResourceTreeClick:

    def test_clicking_resource_row_opens_detail_panel(self, page: Page, live_server, rt_user, rt_playbook):
        """Clicking a resource row opens the detail panel for that resource (FOB-32)."""
        _login(page, live_server.url, 'rt_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{rt_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Select an activity to populate the resource tree
        page.evaluate("""
            () => {
                const node = window.cy && window.cy.nodes('[type="activity"]').first();
                if (node && node.length) node.trigger('tap');
            }
        """)
        page.wait_for_timeout(500)
        page.wait_for_selector('[data-testid="browser-resource-row"]', timeout=5000)

        # Click the first resource row
        page.locator('[data-testid="browser-resource-row"]').first.click()
        page.wait_for_timeout(400)

        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
