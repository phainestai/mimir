"""
E2E tests for Content Browser graph rendering.

Covers: FOB-CONTENT-BROWSER-04, 06, 07, 07c, 14, 14b (CDN guard), 15

Requires: Playwright, live server, seeded DB.
Run: pytest tests/e2e/test_content_browser_graph.py -q --durations=10
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from e2e_helpers import login, open_content_browser, wait_for_cy_edges, wait_for_cy_graph
from methodology.models import Playbook, Workflow, Activity, Phase, Skill, Agent, Rule

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def graph_playbook(transactional_db):
    """Playbook with one workflow, two activities, a skill, agent, rule, and a phase."""
    user = User.objects.create_user(
        username='graph_e2e_user', email='graph_e2e@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='FeatureFactory', description='Test playbook',
        category='development', status='released', version='1.0',
        source='owned', author=user, visibility='public',
    )
    phase = Phase.objects.create(playbook=pb, name='Construction', order=1)
    wf = Workflow.objects.create(name='BPE', description='Build', playbook=pb, order=1)
    skill = Skill.objects.create(playbook=pb, title='Python Skill')
    agent = Agent.objects.create(playbook=pb, name='Build Agent')
    rule = Rule.objects.create(playbook=pb, title='Code Style Rule')
    act1 = Activity.objects.create(name='Plan', workflow=wf, order=1, phase=phase)
    act2 = Activity.objects.create(name='Implement', workflow=wf, order=2, predecessor=act1, agent=agent)
    act2.skills.add(skill)
    act2.rules.add(rule)
    return {'username': 'graph_e2e_user', 'password': 'testpass123', 'pb': pb, 'wf': wf}


@pytest.fixture
def empty_graph_playbook(transactional_db):
    """Playbook with no workflows (no graph content)."""
    user = User.objects.create_user(
        username='empty_graph_user', email='empty_graph@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='Empty Playbook', description='No workflows',
        category='development', status='released', version='1.0',
        source='owned', author=user, visibility='public',
    )
    return {'username': 'empty_graph_user', 'password': 'testpass123', 'pb': pb}


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-04: Graph shows all entities
# ---------------------------------------------------------------------------

def test_graph_renders_nodes_for_playbook_entities(page: Page, live_server_url: str, graph_playbook):
    """Graph renders node for each entity in the playbook."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    open_content_browser(page, live_server_url, data['pb'].pk)

    node_count = page.evaluate("() => window.cy.nodes().length")
    assert node_count >= 5, f"Expected at least 5 nodes, got {node_count}"

    has_workflow = page.evaluate("() => window.cy.nodes('[type = \"workflow\"]').length > 0")
    has_activity = page.evaluate("() => window.cy.nodes('[type = \"activity\"]').length > 0")
    has_skill = page.evaluate("() => window.cy.nodes('[type = \"skill\"]').length > 0")
    has_agent = page.evaluate("() => window.cy.nodes('[type = \"agent\"]').length > 0")
    has_rule = page.evaluate("() => window.cy.nodes('[type = \"rule\"]').length > 0")
    assert has_workflow, 'No workflow nodes'
    assert has_activity, 'No activity nodes'
    assert has_skill, 'No skill nodes'
    assert has_agent, 'No agent nodes'
    assert has_rule, 'No rule nodes'


def test_graph_nodes_are_visually_differentiated(page: Page, live_server_url: str, graph_playbook):
    """Workflow and activity nodes have different background colours."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    open_content_browser(page, live_server_url, data['pb'].pk)

    wf_colour = page.evaluate(
        "() => window.cy.nodes('[type = \"workflow\"]').first().style('background-color')"
    )
    act_colour = page.evaluate(
        "() => window.cy.nodes('[type = \"activity\"]').first().style('background-color')"
    )
    assert wf_colour != act_colour, "Workflow and activity have same colour"


def test_contains_edge_connects_workflow_to_activity(page: Page, live_server_url: str, graph_playbook):
    """A 'contains' edge exists from the workflow node to each activity node."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
    wait_for_cy_edges(page)

    contains_count = page.evaluate(
        "() => window.cy.edges('[relationship = \"contains\"]').length"
    )
    assert contains_count >= 2, f"Expected at least 2 contains edges, got {contains_count}"


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-06: Default layout is hierarchical top-down
# ---------------------------------------------------------------------------

def test_layout_workflow_above_activity(page: Page, live_server_url: str, graph_playbook):
    """Workflow nodes appear above (lower Y) than activity nodes in dagre TB layout."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    open_content_browser(page, live_server_url, data['pb'].pk)

    wf_y = page.evaluate(
        "() => window.cy.nodes('[type = \"workflow\"]').first().position().y"
    )
    act_y = page.evaluate(
        "() => window.cy.nodes('[type = \"activity\"]').first().position().y"
    )
    assert wf_y < act_y, f"Workflow Y ({wf_y}) should be less than Activity Y ({act_y})"


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-07: Pan, zoom controls and mini-map
# ---------------------------------------------------------------------------

def test_zoom_controls_are_visible(page: Page, live_server_url: str, graph_playbook):
    """Zoom in, zoom out, and fit buttons are present in the DOM."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
    page.wait_for_load_state('domcontentloaded')

    expect(page.get_by_test_id('browser-zoom-in')).to_be_visible()
    expect(page.get_by_test_id('browser-zoom-out')).to_be_visible()
    expect(page.get_by_test_id('browser-zoom-fit')).to_be_visible()


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-07c: Fit graph to screen
# ---------------------------------------------------------------------------

def test_fit_button_executes_cy_fit(page: Page, live_server_url: str, graph_playbook):
    """Clicking [Fit] calls cy.fit() without errors."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    open_content_browser(page, live_server_url, data['pb'].pk)

    page.evaluate("() => window.cy.panBy({ x: 200, y: 200 })")

    fit_btn = page.get_by_test_id('browser-zoom-fit')
    fit_btn.click()

    node_count = page.evaluate("() => window.cy.nodes().length")
    assert node_count > 0, "Graph lost nodes after fit"


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-14: Loading state while graph data is fetched
# ---------------------------------------------------------------------------

def test_loading_spinner_visible_during_fetch(page: Page, live_server_url: str, graph_playbook):
    """Loading spinner is shown while API request is in flight, then hidden after render."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])

    with page.expect_request("**/api/playbooks/*/graph/"):
        page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")

    wait_for_cy_graph(page)
    expect(page.get_by_test_id('browser-loading')).not_to_be_visible()
    expect(page.get_by_test_id('browser-error-state')).not_to_be_visible()


def test_spinner_hidden_after_graph_renders(page: Page, live_server_url: str, graph_playbook):
    """After graph renders successfully, the loading spinner is hidden."""
    data = graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    open_content_browser(page, live_server_url, data['pb'].pk)

    expect(page.get_by_test_id('browser-loading')).not_to_be_visible()
    expect(page.get_by_test_id('browser-error-state')).not_to_be_visible()


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-15: Empty playbook shows friendly empty state
# ---------------------------------------------------------------------------

def test_empty_playbook_shows_no_content_state(page: Page, live_server_url: str, empty_graph_playbook):
    """Empty playbook shows 'This playbook has no content yet.' message."""
    data = empty_graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
    page.wait_for_load_state('domcontentloaded')

    expect(page.get_by_test_id('browser-no-content-state')).to_be_visible()
    assert 'no content' in page.get_by_test_id('browser-no-content-state').inner_text().lower()


def test_empty_playbook_go_to_playbook_link(page: Page, live_server_url: str, empty_graph_playbook):
    """[Go to Playbook] button links to the playbook detail page."""
    data = empty_graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
    page.wait_for_load_state('domcontentloaded')

    link = page.get_by_test_id('browser-go-to-playbook')
    expect(link).to_be_visible()
    href = link.get_attribute('href')
    assert str(data['pb'].pk) in href, f"Link href {href} does not include playbook PK"


def test_empty_playbook_does_not_render_cytoscape(page: Page, live_server_url: str, empty_graph_playbook):
    """Empty playbook: window.cy stays null (no Cytoscape instance created)."""
    data = empty_graph_playbook
    login(page, live_server_url, data['username'], data['password'])
    page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
    page.wait_for_load_state('domcontentloaded')

    cy_is_null = page.evaluate("() => window.cy === null")
    assert cy_is_null, "window.cy should be null for an empty playbook"


def test_cdn_guard_shows_error_state_when_cytoscape_missing(
    page: Page, live_server_url: str, graph_playbook,
):
    """FOB-14b: If cytoscape CDN fails, the inline guard shows the error state."""
    login(page, live_server_url, graph_playbook['username'], graph_playbook['password'])

    page.route('**cytoscape*.min.js*', lambda r: r.abort())
    page.route('**cytoscape*.js*', lambda r: r.abort())

    page.goto(f"{live_server_url}/browser/{graph_playbook['pb'].pk}/")
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(1500)

    error_state = page.locator('[data-testid="browser-error-state"]')
    expect(error_state).to_be_visible()


# ---------------------------------------------------------------------------
# FOB-CONTENT-BROWSER-33: Deterministic node insertion order (S33)
# ---------------------------------------------------------------------------

@pytest.fixture
def order_playbook(transactional_db):
    """Playbook with 2 workflows, 3 activities, and resources per activity for order verification."""
    user = User.objects.create_user(
        username='order_user', email='order@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='OrderTest', description='For FOB-33',
        category='development', status='released', version='1.0',
        source='owned', author=user, visibility='public',
    )
    wf1 = Workflow.objects.create(name='Alpha', playbook=pb, order=1)
    wf2 = Workflow.objects.create(name='Beta', playbook=pb, order=2)
    skill = Skill.objects.create(playbook=pb, title='Test Skill')
    rule = Rule.objects.create(playbook=pb, title='Test Rule')
    agent = Agent.objects.create(playbook=pb, name='Test Agent')
    act1 = Activity.objects.create(name='Act1', workflow=wf1, order=1, agent=agent)
    act2 = Activity.objects.create(name='Act2', workflow=wf1, order=2)
    act2.skills.add(skill)
    act2.rules.add(rule)
    act3 = Activity.objects.create(name='Act3', workflow=wf2, order=1)
    return {
        'username': 'order_user', 'password': 'testpass123',
        'pb': pb, 'wf1': wf1, 'wf2': wf2,
        'act1': act1, 'act2': act2, 'act3': act3,
    }


class TestNodeInsertionOrder:
    """FOB-CONTENT-BROWSER-33: Nodes are inserted into Cytoscape in deterministic order."""

    def _wait_for_order(self, page):
        page.wait_for_function(
            "() => Array.isArray(window._lastElementOrder) && window._lastElementOrder.length > 0",
            timeout=10000,
        )

    def test_workflow_nodes_precede_activity_nodes(
        self, page: Page, live_server_url: str, order_playbook,
    ):
        """All workflow nodes appear before any activity node in _lastElementOrder."""
        data = order_playbook
        login(page, live_server_url, data['username'], data['password'])
        page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
        self._wait_for_order(page)

        order = page.evaluate("() => window._lastElementOrder.map(n => n.type)")
        wf_indices = [i for i, t in enumerate(order) if t == 'workflow']
        act_indices = [i for i, t in enumerate(order) if t == 'activity']
        assert wf_indices, "No workflow nodes found in _lastElementOrder"
        assert act_indices, "No activity nodes found in _lastElementOrder"
        assert max(wf_indices) < min(act_indices), (
            f"Workflow nodes must all precede activity nodes. "
            f"Last wf at {max(wf_indices)}, first act at {min(act_indices)}"
        )

    def test_activity_nodes_precede_resource_nodes(
        self, page: Page, live_server_url: str, order_playbook,
    ):
        """All activity nodes appear before any resource (skill/rule/agent/artifact) node."""
        data = order_playbook
        login(page, live_server_url, data['username'], data['password'])
        page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
        self._wait_for_order(page)

        order = page.evaluate("() => window._lastElementOrder.map(n => n.type)")
        act_indices = [i for i, t in enumerate(order) if t == 'activity']
        resource_types = {'skill', 'rule', 'agent', 'artifact'}
        res_indices = [i for i, t in enumerate(order) if t in resource_types]
        assert act_indices, "No activity nodes found"
        assert res_indices, "No resource nodes found — check fixture has skills/rules/agent"
        assert max(act_indices) < min(res_indices), (
            f"All activity nodes must precede resource nodes. "
            f"Last act at {max(act_indices)}, first resource at {min(res_indices)}"
        )

    def test_resource_nodes_grouped_after_parent_activity(
        self, page: Page, live_server_url: str, order_playbook,
    ):
        """Resource nodes for act1 appear before resource nodes for act2."""
        data = order_playbook
        login(page, live_server_url, data['username'], data['password'])
        page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
        self._wait_for_order(page)

        act1_pk = str(data['act1'].pk)
        act2_pk = str(data['act2'].pk)
        order = page.evaluate("() => window._lastElementOrder.map(n => n.id)")
        resource_types = {'skill', 'rule', 'agent', 'artifact'}

        def resource_indices_for(act_pk):
            return [
                i for i, node_id in enumerate(order)
                if f':activity:{act_pk}' in node_id
            ]

        act1_res = resource_indices_for(act1_pk)
        act2_res = resource_indices_for(act2_pk)
        assert act1_res, f"No resource nodes found for act1 (pk={act1_pk})"
        assert act2_res, f"No resource nodes found for act2 (pk={act2_pk})"
        assert max(act1_res) < min(act2_res), (
            f"Resources for act1 must precede resources for act2. "
            f"act1 last at {max(act1_res)}, act2 first at {min(act2_res)}"
        )

    def test_order_preserved_after_filter_rebuild(
        self, page: Page, live_server_url: str, order_playbook,
    ):
        """After deactivating and reactivating a type, insertion order is still correct."""
        data = order_playbook
        login(page, live_server_url, data['username'], data['password'])
        page.goto(f"{live_server_url}/browser/{data['pb'].pk}/")
        self._wait_for_order(page)

        skill_btn = page.locator('[data-filter-type="skill"]')
        skill_btn.click()
        page.wait_for_timeout(500)
        skill_btn.click()
        self._wait_for_order(page)

        order = page.evaluate("() => window._lastElementOrder.map(n => n.type)")
        wf_indices = [i for i, t in enumerate(order) if t == 'workflow']
        act_indices = [i for i, t in enumerate(order) if t == 'activity']
        res_indices = [i for i, t in enumerate(order) if t not in ('workflow', 'activity')]
        assert wf_indices and act_indices, "Missing workflow or activity nodes after rebuild"
        assert max(wf_indices) < min(act_indices), "Workflows not before activities after rebuild"
        if res_indices:
            assert max(act_indices) < min(res_indices), "Activities not before resources after rebuild"
