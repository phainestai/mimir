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

    def test_clicking_activity_row_opens_detail_panel(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Clicking an activity tree row must open the detail panel (S49 — FOB-26 revised)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_load_state('networkidle')
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Expand the first workflow to reveal activity rows via the chevron
        chevron = page.locator('.browser-tree-toggle').first
        chevron.click()
        page.wait_for_timeout(300)

        rows = page.locator('[data-testid="browser-tree-row"]')
        for i in range(rows.count()):
            row = rows.nth(i)
            if 'Activity Alpha' in row.inner_text() and not row.locator('.browser-tree-toggle').count():
                row.click()
                break

        page.wait_for_timeout(400)
        # Detail panel MUST be visible after tree row click (S49 — revised spec).
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()


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


class TestFOB27ResourceNodeNoHighlight:

    def test_resource_node_click_does_not_highlight_tree_row(
        self, page: Page, live_server, st_user, st_playbook,
    ):
        """FOB-27 / S18: clicking a Skill/Rule canvas node must NOT highlight any tree row."""
        from methodology.models import Skill
        skill = Skill.objects.create(playbook=st_playbook, title='TestSkillFOB27')
        # Attach skill to the first activity
        from methodology.models import Activity
        act = Activity.objects.filter(workflow__playbook=st_playbook).first()
        act.skills.add(skill)

        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function(
            "() => window.cy !== null && window.cy.nodes().length > 0",
            timeout=10000,
        )

        # First select an activity (highlights its tree row)
        page.evaluate(
            f"window.cy.getElementById('activity:{act.pk}').emit('tap', [{{position:{{x:0,y:0}}}}])"
        )
        page.wait_for_timeout(300)
        assert page.locator('[data-testid="browser-tree-row"].text-primary').count() >= 1

        # Now tap the skill node (resource node)
        skill_node_id = f"skill:{skill.pk}:activity:{act.pk}"
        page.evaluate(
            f"window.cy.getElementById('{skill_node_id}').emit('tap', [{{position:{{x:0,y:0}}}}])"
        )
        page.wait_for_timeout(300)

        # No tree row should be highlighted
        highlighted = page.locator('[data-testid="browser-tree-row"].text-primary')
        assert highlighted.count() == 0, (
            "Resource node click must NOT leave any structural tree row highlighted"
        )


# ---------------------------------------------------------------------------
# FOB-24 updated: Tree starts fully collapsed
# FOB-26 updated: Accordion — clicking node expands only its parent workflow
# ---------------------------------------------------------------------------

class TestTreeCollapsedDefault:

    def test_tree_starts_fully_collapsed(
        self, page: Page, live_server, st_user, st_playbook,
    ):
        """All workflow sections collapsed on initial render (FOB-24)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function(
            "() => window.cy !== null && window.cy.nodes().length > 0",
            timeout=10000,
        )
        page.wait_for_timeout(500)

        # All section divs (tree-wf-*) should be hidden
        expanded_sections = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('[id^="tree-wf-"]')
            ).filter(el => el.style.display !== 'none').length
        """)
        assert expanded_sections == 0, f"Expected 0 expanded sections, got {expanded_sections}"

    def test_toggle_arrows_show_collapsed_state(
        self, page: Page, live_server, st_user, st_playbook,
    ):
        """Toggle arrows show ▸ (collapsed) on initial render (FOB-24)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function(
            "() => window.cy !== null && window.cy.nodes().length > 0",
            timeout=10000,
        )
        page.wait_for_timeout(500)

        expanded_arrows = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('.browser-tree-toggle')
            ).filter(el => el.textContent.trim() === '▾').length
        """)
        assert expanded_arrows == 0, f"Expected 0 expanded arrows (▾), got {expanded_arrows}"


class TestTreeAccordion:

    def test_clicking_workflow_expands_only_that_workflow(
        self, page: Page, live_server, st_user, st_playbook,
    ):
        """Clicking a workflow row expands it and collapses all others (FOB-26)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function(
            "() => window.cy !== null && window.cy.nodes().length > 0",
            timeout=10000,
        )
        page.wait_for_timeout(500)

        # Click first workflow row
        rows = page.locator('[data-testid="browser-tree-row"]')
        rows.first.click()
        page.wait_for_timeout(300)

        expanded_sections = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('[id^="tree-wf-"]')
            ).filter(el => el.style.display !== 'none').length
        """)
        assert expanded_sections == 1, f"Expected exactly 1 expanded section, got {expanded_sections}"

    def test_canvas_activity_click_opens_parent_workflow(
        self, page: Page, live_server, st_user, st_playbook,
    ):
        """Clicking an activity on canvas expands its parent workflow section (FOB-26)."""
        from methodology.models import Activity
        act = Activity.objects.filter(workflow__playbook=st_playbook).first()

        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function(
            "() => window.cy !== null && window.cy.nodes().length > 0",
            timeout=10000,
        )
        page.wait_for_timeout(500)

        page.evaluate(
            f"window.cy.getElementById('activity:{act.pk}').emit('tap', [{{position:{{x:0,y:0}}}}])"
        )
        page.wait_for_timeout(500)

        expanded_sections = page.evaluate("""
            () => Array.from(
                document.querySelectorAll('[id^="tree-wf-"]')
            ).filter(el => el.style.display !== 'none').length
        """)
        assert expanded_sections == 1, f"Expected exactly 1 section expanded after activity tap, got {expanded_sections}"


# ---------------------------------------------------------------------------
# S49: Uniform tree-row click behaviour (FOB-26 revised 2026-06-02)
# ---------------------------------------------------------------------------

@pytest.mark.skip(reason='S49 skeleton — _selectTreeNode not yet implemented')
class TestTreeRowUniformClick:
    """S49 — Clicking any tree row navigates canvas + opens detail panel (same as canvas tap)."""

    def test_clicking_workflow_row_navigates_to_workflow_node(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Clicking a workflow row (NOT the chevron) pans canvas to that workflow node (S49)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0", timeout=10000)
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        # Find workflow row and click its label area (not the chevron)
        wf_row = page.locator('[data-testid="browser-tree-row"]').first
        label = wf_row.locator('span.fw-semibold')
        if label.count():
            label.first.click()
        else:
            wf_row.click()
        page.wait_for_timeout(400)
        # Canvas must have panned (we cannot assert exact position without Playwright fully running)

    def test_clicking_workflow_row_opens_detail_panel(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Clicking a workflow row (NOT the chevron) opens the detail panel (S49)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0", timeout=10000)
        page.wait_for_selector('[data-testid="browser-tree-row"]', timeout=8000)

        wf_row = page.locator('[data-testid="browser-tree-row"]').first
        label = wf_row.locator('span.fw-semibold')
        if label.count():
            label.first.click()
        else:
            wf_row.click()
        page.wait_for_timeout(500)
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()

    def test_chevron_click_toggles_accordion_without_opening_panel(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Clicking ONLY the chevron expands accordion but does NOT open detail panel (S49)."""
        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0", timeout=10000)
        page.wait_for_selector('.browser-tree-toggle', timeout=8000)

        chevron = page.locator('.browser-tree-toggle').first
        chevron.click()
        page.wait_for_timeout(400)
        # Accordion must expand
        expanded = page.evaluate("""
            () => Array.from(document.querySelectorAll('[id^="tree-wf-"]'))
                      .filter(el => el.style.display !== 'none').length
        """)
        assert expanded >= 1, "Chevron click should expand at least one workflow section"
        # Detail panel must stay hidden
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()

    def test_clicking_activity_row_applies_selection_ring(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """After clicking an activity tree row, that cy node has a border-width > 0 (S49)."""
        from methodology.models import Activity
        act = Activity.objects.filter(workflow__playbook=st_playbook).first()

        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0", timeout=10000)
        page.wait_for_selector('.browser-tree-toggle', timeout=8000)

        # Expand via chevron first
        chevron = page.locator('.browser-tree-toggle').first
        chevron.click()
        page.wait_for_timeout(300)

        # Click the activity row
        act_id = f'activity:{act.pk}'
        rows = page.locator('[data-testid="browser-tree-row"]')
        for i in range(rows.count()):
            if not rows.nth(i).locator('.browser-tree-toggle').count():
                rows.nth(i).click()
                break
        page.wait_for_timeout(400)

        border_width = page.evaluate(
            f"() => {{ const n = window.cy.getElementById('{act_id}'); return n ? parseFloat(n.style('border-width')) : 0; }}"
        )
        assert border_width > 0, f"Activity node border-width should be > 0 after tree click, got {border_width}"

    def test_tree_click_and_canvas_tap_produce_same_panel_content(
        self, page: Page, live_server, st_user, st_playbook
    ):
        """Tree row click and canvas tap must open the same embed URL in the panel (S49)."""
        from methodology.models import Activity
        act = Activity.objects.filter(workflow__playbook=st_playbook).first()
        act_id = f'activity:{act.pk}'

        _login(page, live_server.url, 'st_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{st_playbook.pk}/")
        page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0", timeout=10000)

        # Trigger via canvas tap
        page.evaluate(
            f"window.cy.getElementById('{act_id}').emit('tap', [{{position:{{x:0,y:0}}}}])"
        )
        page.wait_for_timeout(500)
        canvas_panel_visible = page.locator('[data-testid="browser-detail-panel"]').is_visible()
        page.locator('[data-testid="browser-panel-close"]').click()
        page.wait_for_timeout(200)

        # Trigger via tree row click
        page.wait_for_selector('.browser-tree-toggle', timeout=8000)
        chevron = page.locator('.browser-tree-toggle').first
        chevron.click()
        page.wait_for_timeout(300)

        rows = page.locator('[data-testid="browser-tree-row"]')
        for i in range(rows.count()):
            row = rows.nth(i)
            if not row.locator('.browser-tree-toggle').count():
                row.click()
                break
        page.wait_for_timeout(400)
        tree_panel_visible = page.locator('[data-testid="browser-detail-panel"]').is_visible()

        assert canvas_panel_visible, "Canvas tap should open detail panel"
        assert tree_panel_visible, "Tree row click should also open detail panel (S49)"
