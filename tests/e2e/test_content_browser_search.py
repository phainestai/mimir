"""
E2E tests for Content Browser node-name search (S16).

Covers:
  FOB-CONTENT-BROWSER-12  Search nodes by name

Run:
  DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_search.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from methodology.models import Activity, Phase, Playbook, Skill, Workflow

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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def search_user(transactional_db):
    user = User.objects.create_user(
        username='search_user', email='search@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def search_playbook(search_user, transactional_db):
    """Playbook with two activities: one matching 'Plan', one not."""
    pb = Playbook.objects.create(
        name='SearchPlaybook', description='Search tests',
        category='development', status='released', version='1.0',
        source='owned', author=search_user, visibility='public',
    )
    phase = Phase.objects.create(name='Alpha', playbook=pb, order=1)
    wf = Workflow.objects.create(name='SearchWorkflow', playbook=pb, order=1)
    act_match = Activity.objects.create(
        name='Plan the Feature', workflow=wf, order=1, phase=phase,
    )
    act_no_match = Activity.objects.create(
        name='Build the Feature', workflow=wf, order=2, phase=phase,
    )
    skill = Skill.objects.create(playbook=pb, title='PlanningSkill')
    act_match.skills.add(skill)
    return {
        'pb': pb, 'wf': wf,
        'act_match': act_match, 'act_no_match': act_no_match,
        'skill': skill, 'phase': phase,
        'username': 'search_user', 'password': 'testpass123',
    }


# ---------------------------------------------------------------------------
# FOB-12: Search nodes by name
# ---------------------------------------------------------------------------

class TestNodeSearch:

    def test_search_input_visible_in_left_panel(
        self, page: Page, live_server, search_playbook,
    ):
        """Search input is present in the left panel (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        search_input = page.locator('[data-testid="browser-search-input"]')
        expect(search_input).to_be_visible()

    def test_search_dims_non_matching_nodes(
        self, page: Page, live_server, search_playbook,
    ):
        """Non-matching nodes are dimmed when search term is entered (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        act_no_match_id = f"activity:{search_playbook['act_no_match'].pk}"

        page.locator('[data-testid="browser-search-input"]').fill('Plan')
        page.wait_for_timeout(400)  # debounce

        opacity = page.evaluate(f"window.cy.getElementById('{act_no_match_id}').style('opacity')")
        assert float(opacity) < 0.5, f"Non-matching node should be dimmed, got {opacity}"

    def test_search_highlights_matching_nodes(
        self, page: Page, live_server, search_playbook,
    ):
        """Matching nodes are at full opacity when search term is entered (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        act_match_id = f"activity:{search_playbook['act_match'].pk}"

        page.locator('[data-testid="browser-search-input"]').fill('Plan')
        page.wait_for_timeout(400)

        opacity = page.evaluate(f"window.cy.getElementById('{act_match_id}').style('opacity')")
        assert float(opacity) > 0.9, f"Matching node should be bright, got {opacity}"

    def test_edges_not_dimmed_by_search(
        self, page: Page, live_server, search_playbook,
    ):
        """Edges remain at full opacity during search (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-search-input"]').fill('Plan')
        page.wait_for_timeout(400)

        edge_opacity = page.evaluate(
            "() => window.cy.edges().map(e => parseFloat(e.style('opacity')))"
        )
        for op in edge_opacity:
            assert op > 0.9, f"Edge opacity should not be reduced by search, got {op}"

    def test_clear_search_restores_node_opacity(
        self, page: Page, live_server, search_playbook,
    ):
        """Clearing the search restores all nodes to full opacity (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        inp = page.locator('[data-testid="browser-search-input"]')
        inp.fill('Plan')
        page.wait_for_timeout(400)
        inp.fill('')
        page.wait_for_timeout(400)

        act_no_match_id = f"activity:{search_playbook['act_no_match'].pk}"
        opacity = page.evaluate(f"window.cy.getElementById('{act_no_match_id}').style('opacity')")
        assert float(opacity) > 0.9, f"After clearing search, node should be bright, got {opacity}"

    def test_search_and_phase_filter_combined(
        self, page: Page, live_server, search_playbook,
    ):
        """A node must satisfy BOTH search AND phase filter to appear bright (FOB-12)."""
        _login(page, live_server.url, search_playbook['username'], search_playbook['password'])
        page.goto(f"{live_server.url}/browser/{search_playbook['pb'].pk}/")
        _wait_for_graph(page)

        # Activate phase Alpha (both activities are in Alpha — neither gets phase-dimmed)
        # Then search for 'Plan' — only act_match is bright; act_no_match is search-dimmed
        page.wait_for_selector('[data-testid="browser-phase-pill"]', timeout=5000)
        page.locator('[data-testid="browser-phase-pill"]', has_text='Alpha').click()
        page.wait_for_timeout(400)

        page.locator('[data-testid="browser-search-input"]').fill('Plan')
        page.wait_for_timeout(400)

        act_match_id = f"activity:{search_playbook['act_match'].pk}"
        act_no_match_id = f"activity:{search_playbook['act_no_match'].pk}"

        op_match = float(page.evaluate(
            f"window.cy.getElementById('{act_match_id}').style('opacity')"
        ))
        op_no_match = float(page.evaluate(
            f"window.cy.getElementById('{act_no_match_id}').style('opacity')"
        ))

        assert op_match > 0.9, f"Matching + correct phase: should be bright, got {op_match}"
        assert op_no_match < 0.5, f"Non-matching: should be dimmed, got {op_no_match}"
