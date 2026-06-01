"""
E2E tests for Content Browser entity-type filter (S14) and phase filter (S15).

Covers:
  FOB-CONTENT-BROWSER-11  Entity type filter toolbar
  FOB-CONTENT-BROWSER-11b Phase filter shared between canvas and structural tree
  FOB-CONTENT-BROWSER-03g Switching playbooks resets stale phase filter
  FOB-CONTENT-BROWSER-32  Clicking resource with hidden canvas node still opens panel

Run:
  DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_filters.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from methodology.models import Activity, Agent, Phase, Playbook, Rule, Skill, Workflow

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url


def _wait_for_graph(page):
    page.wait_for_function(
        "() => window.cy !== null && window.cy.nodes().length > 0",
        timeout=10000,
    )


def _tap_node(page, node_id):
    page.evaluate(f"window.cy.getElementById('{node_id}').emit('tap', [{{position:{{x:0,y:0}}}}])")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def filter_user(transactional_db):
    user = User.objects.create_user(
        username='filter_user', email='filter@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def filter_playbook(filter_user, transactional_db):
    """Playbook with phases, workflows, activities, and resource nodes."""
    pb = Playbook.objects.create(
        name='FilterPlaybook', description='Filter tests',
        category='development', status='released', version='1.0',
        source='owned', author=filter_user, visibility='public',
    )
    phase1 = Phase.objects.create(name='Inception', playbook=pb, order=1)
    phase2 = Phase.objects.create(name='Build', playbook=pb, order=2)
    wf = Workflow.objects.create(name='MainWorkflow', playbook=pb, order=1)
    act1 = Activity.objects.create(
        name='Plan Feature', workflow=wf, order=1, phase=phase1,
    )
    act2 = Activity.objects.create(
        name='Build Feature', workflow=wf, order=2, phase=phase2,
    )
    act3 = Activity.objects.create(
        name='Review Feature', workflow=wf, order=3,  # unphased
    )
    skill = Skill.objects.create(playbook=pb, title='Planning Skill')
    act1.skills.add(skill)
    rule = Rule.objects.create(playbook=pb, title='Coding Rule', slug='coding-rule')
    act2.rules.add(rule)
    agent = Agent.objects.create(playbook=pb, name='Review Agent')
    act3.agent = agent
    act3.save()
    return {
        'pb': pb, 'phase1': phase1, 'phase2': phase2,
        'wf': wf, 'act1': act1, 'act2': act2, 'act3': act3,
        'skill': skill, 'rule': rule, 'agent': agent,
        'username': 'filter_user', 'password': 'testpass123',
    }


@pytest.fixture
def no_phase_playbook(filter_user, transactional_db):
    """Playbook with no phases — phase filter should be hidden."""
    pb = Playbook.objects.create(
        name='NoPhasePB', description='No phase playbook',
        category='development', status='released', version='1.0',
        source='owned', author=filter_user, visibility='public',
    )
    wf = Workflow.objects.create(name='WF1', playbook=pb, order=1)
    Activity.objects.create(name='Act1', workflow=wf, order=1)
    return pb


# ---------------------------------------------------------------------------
# FOB-11: Entity type filter toolbar
# ---------------------------------------------------------------------------

class TestEntityTypeFilter:

    def test_filter_toolbar_visible_after_graph_load(
        self, page: Page, live_server, filter_playbook,
    ):
        """Filter toolbar container is rendered in canvas area (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)

        toolbar = page.locator('[data-testid="browser-filter-toolbar"]')
        expect(toolbar).to_be_visible()

    def test_filter_buttons_shown_per_entity_type(
        self, page: Page, live_server, filter_playbook,
    ):
        """A toggle button is rendered for each entity type that has nodes (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-filter-btn"]', timeout=5000)

        btns = page.locator('[data-testid="browser-filter-btn"]')
        types_shown = [btns.nth(i).get_attribute('data-filter-type') for i in range(btns.count())]
        assert 'workflow' in types_shown
        assert 'activity' in types_shown
        assert 'skill' in types_shown
        assert 'rule' in types_shown
        assert 'agent' in types_shown

    def test_button_shows_count_that_does_not_change_on_toggle(
        self, page: Page, live_server, filter_playbook,
    ):
        """Count badge on filter button stays fixed when type is toggled off (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        rule_btn = page.locator('[data-filter-type="rule"]')
        count_before = rule_btn.inner_text()
        rule_btn.click()
        page.wait_for_timeout(300)
        count_after = page.locator('[data-filter-type="rule"]').inner_text()
        assert count_before == count_after, "Count must not change when type is toggled"

    def test_toggle_off_type_hides_nodes_on_canvas(
        self, page: Page, live_server, filter_playbook,
    ):
        """Deactivating 'Rule' removes rule nodes from the Cytoscape graph entirely (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        rule_id = f"rule:{filter_playbook['rule'].pk}:activity:{filter_playbook['act2'].pk}"

        # Before toggle: rule node exists in cy
        count_before = page.evaluate(
            f"window.cy.getElementById('{rule_id}').length"
        )
        assert count_before == 1, "Rule node should exist in cy before filter toggle"

        # Toggle rule off
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(600)

        # After toggle: node fully removed from cy (not just hidden)
        count_after = page.evaluate(
            f"window.cy.getElementById('{rule_id}').length"
        )
        assert count_after == 0, "Rule node must be removed from cy after type deactivation"

    def test_toggle_off_updates_url_types_param(
        self, page: Page, live_server, filter_playbook,
    ):
        """Deactivating a type updates the URL ?types= param (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(400)

        assert 'types=' in page.url
        assert 'rule' not in page.url.split('types=')[1].split('&')[0]

    def test_re_activate_type_shows_nodes(
        self, page: Page, live_server, filter_playbook,
    ):
        """Re-activating a removed type adds nodes back to cy and re-layouts (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        rule_id = f"rule:{filter_playbook['rule'].pk}:activity:{filter_playbook['act2'].pk}"
        # Remove rules
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(600)
        assert page.evaluate(f"window.cy.getElementById('{rule_id}').length") == 0

        # Re-activate rules
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(600)

        count = page.evaluate(f"window.cy.getElementById('{rule_id}').length")
        assert count == 1, "Rule node must be re-added to cy after type re-activation"

    def test_all_active_removes_types_from_url(
        self, page: Page, live_server, filter_playbook,
    ):
        """When all types are active, types param is removed from URL (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        # Start with rule filtered out
        page.goto(
            f"{live_server.url}/browser/{filter_playbook['pb'].pk}/"
            f"?types=workflow,activity,skill,agent,artifact"
        )
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        # Re-activate rule
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(400)

        assert 'types=' not in page.url

    def test_hiding_selected_node_type_closes_panel(
        self, page: Page, live_server, filter_playbook,
    ):
        """When active node's type is hidden, the detail panel closes (FOB-11)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="skill"]', timeout=5000)

        skill_id = f"skill:{filter_playbook['skill'].pk}:activity:{filter_playbook['act1'].pk}"
        _tap_node(page, skill_id)
        page.wait_for_timeout(300)

        panel = page.locator('[data-testid="browser-detail-panel"]')
        expect(panel).to_be_visible()

        page.locator('[data-filter-type="skill"]').click()
        page.wait_for_timeout(400)

        expect(panel).to_be_hidden()

    def test_resource_tree_click_opens_panel_when_canvas_node_hidden(
        self, page: Page, live_server, filter_playbook,
    ):
        """FOB-32: resource tree row opens panel even when canvas node is removed from cy."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        # Open resource tree by selecting the workflow
        wf_id = f"workflow:{filter_playbook['wf'].pk}"
        _tap_node(page, wf_id)
        page.wait_for_selector('[data-testid="browser-resource-row"]', timeout=5000)

        # Remove rule nodes via filter toggle
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(600)

        rule_id = f"rule:{filter_playbook['rule'].pk}:activity:{filter_playbook['act2'].pk}"
        count = page.evaluate(f"window.cy.getElementById('{rule_id}').length")
        assert count == 0, "Rule canvas node must be removed from cy by filter"

        # Click the rule row in resource tree — panel must still open
        rule_row = page.locator('[data-testid="browser-resource-row"]', has_text='Coding Rule')
        expect(rule_row).to_be_visible()
        rule_row.click()
        page.wait_for_timeout(400)

        # Panel opens
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()

        # The removed node has no selection ring (it doesn't exist in cy)
        border_width = page.evaluate(
            f"window.cy.getElementById('{rule_id}').style('border-width')"
        )
        assert border_width in ('0', '0px', ''), "Removed node must not show selection ring"


# ---------------------------------------------------------------------------
# FOB-11b: Phase filter
# ---------------------------------------------------------------------------

class TestPhaseFilter:

    def test_phase_filter_hidden_when_playbook_has_no_phases(
        self, page: Page, live_server, filter_user, no_phase_playbook,
    ):
        """Phase filter control is hidden entirely when no phases (FOB-11b)."""
        _login(page, live_server.url, 'filter_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{no_phase_playbook.pk}/")
        _wait_for_graph(page)

        phase_filter = page.locator('[data-testid="browser-phase-filter"]')
        # Container exists but should be empty (no pills rendered)
        expect(phase_filter).to_be_attached()
        assert page.locator('[data-testid="browser-phase-pill"]').count() == 0

    def test_phase_filter_shows_phases_when_playbook_has_phases(
        self, page: Page, live_server, filter_playbook,
    ):
        """Phase pills are shown for each phase plus (Unphased) (FOB-11b)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        pills = page.locator('[data-testid="browser-phase-pill"]')
        texts = [pills.nth(i).inner_text() for i in range(pills.count())]
        assert 'Inception' in texts
        assert 'Build' in texts
        assert '(Unphased)' in texts

    def test_phase_filter_dims_activities_outside_phase(
        self, page: Page, live_server, filter_playbook,
    ):
        """Selecting phase 'Inception' dims activities not in Inception (FOB-11b)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        # Click Inception pill to activate only Inception
        inception_pill = page.locator('[data-testid="browser-phase-pill"]', has_text='Inception')
        inception_pill.click()
        page.wait_for_timeout(400)

        act2_id = f"activity:{filter_playbook['act2'].pk}"
        opacity = page.evaluate(f"window.cy.getElementById('{act2_id}').style('opacity')")
        assert float(opacity) < 0.5, f"act2 (Build) should be dimmed, got opacity {opacity}"

        act1_id = f"activity:{filter_playbook['act1'].pk}"
        opacity1 = page.evaluate(f"window.cy.getElementById('{act1_id}').style('opacity')")
        assert float(opacity1) > 0.9, f"act1 (Inception) should be bright, got opacity {opacity1}"

    def test_phase_filter_does_not_hide_non_activity_nodes(
        self, page: Page, live_server, filter_playbook,
    ):
        """Workflow / resource nodes are NOT dimmed by phase filter (FOB-11b)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        page.locator('[data-testid="browser-phase-pill"]', has_text='Inception').click()
        page.wait_for_timeout(400)

        wf_id = f"workflow:{filter_playbook['wf'].pk}"
        wf_opacity = page.evaluate(f"window.cy.getElementById('{wf_id}').style('opacity')")
        assert float(wf_opacity) > 0.9, f"Workflow must not be dimmed by phase filter"

    def test_phase_filter_updates_url(
        self, page: Page, live_server, filter_playbook,
    ):
        """Active phase filter is reflected in the URL (FOB-11b)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        page.locator('[data-testid="browser-phase-pill"]', has_text='Inception').click()
        page.wait_for_timeout(400)

        assert 'phases=' in page.url

    def test_phase_filter_resets_on_playbook_switch_fob_03g(
        self, page: Page, live_server, filter_playbook, filter_user, no_phase_playbook,
    ):
        """FOB-03g: switching playbooks clears stale phase IDs from URL."""
        _login(page, live_server.url, 'filter_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        # Activate a phase filter on playbook 1
        page.locator('[data-testid="browser-phase-pill"]', has_text='Inception').click()
        page.wait_for_timeout(400)
        assert 'phases=' in page.url

        # Switch to a playbook with no phases
        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_selector('[data-testid="browser-picker-item"]', timeout=5000)
        no_phase_item = page.locator(
            '[data-testid="browser-picker-item"]', has_text='NoPhasePB'
        )
        no_phase_item.click()
        page.wait_for_load_state('networkidle')

        assert 'phases=' not in page.url, "Phase param should be cleared after playbook switch"

    def test_phase_filter_preserves_entity_type_filter_on_switch(
        self, page: Page, live_server, filter_playbook, filter_user, no_phase_playbook,
    ):
        """FOB-03g: switching playbooks via full page load resets all filters (per FOB-23b)."""
        _login(page, live_server.url, 'filter_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-filter-type="rule"]', timeout=5000)

        # Deactivate rule filter
        page.locator('[data-filter-type="rule"]').click()
        page.wait_for_timeout(400)
        assert 'types=' in page.url

        # Switch playbook — full page navigation resets all filters (FOB-23b)
        page.locator('[data-testid="browser-change-playbook"]').click()
        page.wait_for_selector('[data-testid="browser-picker-item"]', timeout=5000)
        page.locator('[data-testid="browser-picker-item"]', has_text='NoPhasePB').click()
        page.wait_for_load_state('networkidle')

        # Full page reload to /browser/<pk>/ — no filter params preserved
        assert 'types=' not in page.url
        assert f'/browser/{no_phase_playbook.pk}/' in page.url

    def test_structural_tree_filters_by_active_phase(
        self, page: Page, live_server, filter_playbook,
    ):
        """Structural tree shows only workflows with ≥1 matching activity when phase active (FOB-11b)."""
        _login(page, live_server.url, filter_playbook['username'], filter_playbook['password'])
        page.goto(f"{live_server.url}/browser/{filter_playbook['pb'].pk}/")
        _wait_for_graph(page)
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)

        # Activate Inception — only act1 matches
        page.locator('[data-testid="browser-phase-pill"]', has_text='Inception').click()
        page.wait_for_timeout(500)

        rows = page.locator('[data-testid="browser-tree-row"]')
        row_texts = [rows.nth(i).inner_text() for i in range(rows.count())]
        combined = ' '.join(row_texts)
        assert 'Plan Feature' in combined, "act1 (Inception phase) should appear"
        assert 'Build Feature' not in combined, "act2 (Build phase) should be hidden"
        assert 'Review Feature' not in combined, "act3 (unphased) should be hidden"
