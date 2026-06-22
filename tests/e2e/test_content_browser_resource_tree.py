"""
E2E tests for Content Browser resource tree (FOB-28/32).

Run: pytest tests/e2e/test_content_browser_resource_tree.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from e2e_helpers import login, open_content_browser, set_compound_level
from methodology.models import Playbook, Workflow, Activity, Skill, Rule

User = get_user_model()


def _open_resource_tree_page(
    page: Page, live_server_url: str, username: str, password: str, pk: int
) -> None:
    login(page, live_server_url, username, password)
    open_content_browser(page, live_server_url, pk)
    set_compound_level(page, "none")
    page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8_000)


def _tap_first_activity(page: Page) -> None:
    page.evaluate("""
        () => {
            const node = window.cy.nodes('[type="activity"]').first();
            if (node.length) node.trigger('tap');
        }
    """)
    page.wait_for_timeout(500)


def _tap_first_workflow(page: Page) -> None:
    page.evaluate("""
        () => {
            const node = window.cy.nodes('[type="workflow"]').first();
            if (node.length) node.trigger('tap');
        }
    """)
    page.wait_for_timeout(500)


def _tap_second_activity(page: Page) -> None:
    page.evaluate("""
        () => {
            const acts = window.cy.nodes('[type="activity"]');
            if (acts.length >= 2) acts[1].trigger('tap');
        }
    """)
    page.wait_for_timeout(500)


@pytest.fixture
def rt_user(transactional_db):
    user = User.objects.create_user(
        username="rt_user",
        email="rt@test.com",
        password="testpass123",
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def rt_playbook(rt_user, transactional_db):
    """Playbook with 1 workflow, 2 activities sharing a skill; activity 1 also has a rule."""
    pb = Playbook.objects.create(
        name="ResourceTestPB",
        description="For resource tree tests",
        category="development",
        status="draft",
        version="0.1",
        source="owned",
        author=rt_user,
        visibility="public",
    )
    wf = Workflow.objects.create(name="MainWorkflow", playbook=pb, order=1)
    act1 = Activity.objects.create(name="Act One", workflow=wf, order=1)
    act2 = Activity.objects.create(name="Act Two", workflow=wf, order=2)

    shared_skill = Skill.objects.create(title="Shared Skill", playbook=pb)
    rule1 = Rule.objects.create(title="Rule Alpha", playbook=pb)

    act1.skills.add(shared_skill)
    act2.skills.add(shared_skill)
    act1.rules.add(rule1)

    return pb


class TestResourceTreeRendering:
    def test_resource_tree_placeholder_on_load(
        self, page: Page, live_server, rt_playbook
    ):
        """Resource tree shows placeholder text before any node is selected (FOB-28)."""
        login(page, live_server.url, "rt_user", "testpass123")
        open_content_browser(page, live_server.url, rt_playbook.pk)
        tree = page.locator('[data-testid="browser-resource-tree"]')
        expect(tree).to_contain_text("Select a Workflow")

    def test_selecting_activity_shows_resource_tree(
        self, page: Page, live_server, rt_playbook
    ):
        """Selecting an activity node renders the resource tree (FOB-28)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_first_activity(page)
        tree = page.locator('[data-testid="browser-resource-tree"]')
        assert "Select a Workflow" not in (tree.inner_text() or "")

    def test_resource_tree_shows_skill(self, page: Page, live_server, rt_playbook):
        """Resource tree lists the skill linked to the selected activity (FOB-28)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_first_activity(page)
        expect(page.locator('[data-testid="browser-resource-tree"]')).to_contain_text(
            "Shared Skill"
        )

    def test_resource_tree_clears_on_panel_close(
        self, page: Page, live_server, rt_playbook
    ):
        """Closing the detail panel resets the resource tree to placeholder (FOB-28)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_first_activity(page)
        page.locator('[data-testid="browser-panel-close"]').click()
        page.wait_for_timeout(300)
        expect(page.locator('[data-testid="browser-resource-tree"]')).to_contain_text(
            "Select a Workflow"
        )

    def test_workflow_selection_aggregates_resources(
        self, page: Page, live_server, rt_playbook
    ):
        """Selecting a workflow shows resources from all its activities, deduplicated (FOB-28)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_first_workflow(page)
        page.wait_for_selector('[data-testid="browser-resource-row"]', timeout=5_000)
        rows = page.locator('[data-testid="browser-resource-row"]')
        skill_rows = [
            rows.nth(i)
            for i in range(rows.count())
            if "Shared Skill" in (rows.nth(i).inner_text() or "")
        ]
        assert len(skill_rows) == 1, (
            f"Expected 1 Shared Skill row, got {len(skill_rows)}"
        )

    def test_activity_selection_shows_parent_workflow_resources(
        self,
        page: Page,
        live_server,
        rt_playbook,
    ):
        """FOB-28 / S18: Selecting Activity shows parent Workflow's resources (all siblings)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_second_activity(page)
        tree = page.locator('[data-testid="browser-resource-tree"]')
        expect(tree).to_contain_text("Rule Alpha")
        expect(tree).to_contain_text("Shared Skill")


class TestResourceTreeClick:
    def test_clicking_resource_row_opens_detail_panel(
        self, page: Page, live_server, rt_playbook
    ):
        """Clicking a resource row opens the detail panel for that resource (FOB-32)."""
        _open_resource_tree_page(
            page, live_server.url, "rt_user", "testpass123", rt_playbook.pk
        )
        _tap_first_activity(page)
        page.wait_for_selector('[data-testid="browser-resource-row"]', timeout=5_000)
        page.locator('[data-testid="browser-resource-row"]').first.click()
        page.wait_for_timeout(400)
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
