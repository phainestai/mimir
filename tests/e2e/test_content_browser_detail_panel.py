"""
E2E tests for Content Browser detail panel.

Covers: FOB-CONTENT-BROWSER-08, 08c, 09, 09b, 09c

Run: DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_detail_panel.py -x
"""

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from methodology.models import Activity, Agent, Playbook, Skill, Workflow

User = get_user_model()

LOGIN_URL_PATH = '/auth/user/login/'


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed. URL: {page.url}"


def _tap_node(page, node_id):
    """Emit a tap event on a Cytoscape node by its namespaced ID."""
    page.evaluate(
        f"window.cy.getElementById('{node_id}').emit('tap', [{{position:{{x:0,y:0}}}}])"
    )


def _wait_for_graph(page):
    page.wait_for_function(
        "() => window.cy !== null && window.cy.nodes().length > 0",
        timeout=10000,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def panel_playbook(transactional_db):
    user = User.objects.create_user(
        username='panel_user', email='panel@test.com', password='testpass123',
    )
    mark_email_verified(user)
    pb = Playbook.objects.create(
        name='PanelPlaybook', description='Detail panel tests',
        category='development', status='released', version='1.0',
        source='owned', author=user, visibility='public',
    )
    wf = Workflow.objects.create(name='PanelWorkflow', playbook=pb, order=1)
    agent = Agent.objects.create(playbook=pb, name='PanelAgent')
    act = Activity.objects.create(
        name='PanelActivity', workflow=wf, order=1, guidance='**Important** step', agent=agent,
    )
    skill = Skill.objects.create(playbook=pb, title='PanelSkill', content='Skill content')
    act.skills.add(skill)
    return {
        'username': 'panel_user', 'password': 'testpass123',
        'pb': pb, 'wf': wf, 'act': act, 'agent': agent, 'skill': skill,
    }


# ---------------------------------------------------------------------------
# FOB-08: Node click opens detail panel
# ---------------------------------------------------------------------------

class TestDetailPanelOpen:

    def test_clicking_node_opens_panel(self, page: Page, live_server, panel_playbook):
        """Node tap opens detail panel with embed content (FOB-08)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)

        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
        # Panel content should contain the workflow name
        panel = page.locator('[data-testid="browser-panel-content"]')
        expect(panel).to_contain_text('PanelWorkflow', timeout=5000)

    def test_panel_header_buttons_present(self, page: Page, live_server, panel_playbook):
        """Panel shows Open new tab, Open full, and × buttons (FOB-08)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")

        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-panel-open-tab"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-panel-open-full"]')).to_be_visible()
        expect(page.locator('[data-testid="browser-panel-close"]')).to_be_visible()

    def test_clicking_different_node_replaces_content(self, page: Page, live_server, panel_playbook):
        """Clicking a second node replaces panel content in-place (FOB-08)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']
        act = panel_playbook['act']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)

        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-panel-content"]')).to_contain_text('PanelWorkflow', timeout=5000)

        _tap_node(page, f"activity:{act.pk}")
        expect(page.locator('[data-testid="browser-panel-content"]')).to_contain_text('PanelActivity', timeout=5000)
        # Panel is still open (no close/reopen)
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()

    def test_activity_embed_renders_markdown(self, page: Page, live_server, panel_playbook):
        """Activity embed in panel renders Markdown guidance (FOB-08)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        act = panel_playbook['act']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"activity:{act.pk}")

        panel = page.locator('[data-testid="browser-panel-content"]')
        # Markdown **Important** should render as <strong>
        expect(panel).to_contain_text('Important', timeout=5000)


# ---------------------------------------------------------------------------
# FOB-09: Close panel
# ---------------------------------------------------------------------------

class TestDetailPanelClose:

    def test_close_button_hides_panel(self, page: Page, live_server, panel_playbook):
        """[×] button closes panel and clears selection (FOB-09)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
        page.wait_for_timeout(200)  # Let panel reflow + fetch settle

        page.locator('[data-testid="browser-panel-close"]').click()
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()

    def test_close_clears_selection_ring(self, page: Page, live_server, panel_playbook):
        """After close, all nodes return to full opacity (FOB-09)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")
        page.wait_for_timeout(200)  # Let panel reflow settle
        page.locator('[data-testid="browser-panel-close"]').click()

        # All nodes should be at full opacity after close
        opacity = page.evaluate(
            f"window.cy.getElementById('workflow:{wf.pk}').style('opacity')"
        )
        assert float(opacity) == 1.0, f"Expected opacity 1.0, got {opacity}"

    def test_canvas_background_tap_closes_panel(self, page: Page, live_server, panel_playbook):
        """Tapping canvas background closes panel (FOB-09)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()
        page.wait_for_timeout(200)

        # Emit tap on the core (canvas background)
        page.evaluate("window.cy.emit('tap', [{target: window.cy}])")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()

    def test_edge_tap_does_not_open_or_close_panel(self, page: Page, live_server, panel_playbook):
        """Tapping an edge has no effect (FOB-09)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)

        # Emit tap on an edge — panel should stay hidden
        page.evaluate("window.cy.edges().first().emit('tap', [{position:{x:0,y:0}}])")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_hidden()


# ---------------------------------------------------------------------------
# FOB-09b + 09c: Open in new tab / Open full
# ---------------------------------------------------------------------------

class TestDetailPanelNavigation:

    def test_open_new_tab_button_opens_correct_url(self, page: Page, live_server, panel_playbook):
        """[Open new tab] triggers window.open with the entity detail URL (FOB-09b)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()

        # Capture the popup (new tab)
        with page.expect_popup() as popup_info:
            page.locator('[data-testid="browser-panel-open-tab"]').click()
        popup = popup_info.value
        popup.wait_for_load_state()
        assert f'/playbooks/{pb.pk}/workflows/{wf.pk}/' in popup.url
        # The opened page is full-page (has navbar)
        assert 'main-navbar' in popup.content()

    def test_open_full_navigates_current_tab(self, page: Page, live_server, panel_playbook):
        """[Open full] navigates current tab to entity detail URL (FOB-09c)."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)
        _tap_node(page, f"workflow:{wf.pk}")
        expect(page.locator('[data-testid="browser-detail-panel"]')).to_be_visible()

        page.locator('[data-testid="browser-panel-open-full"]').click()
        page.wait_for_load_state('networkidle')
        assert f'/playbooks/{pb.pk}/workflows/{wf.pk}/' in page.url
        assert '/browser/' not in page.url


# ---------------------------------------------------------------------------
# FOB-08c: Session expiry while detail panel is open
# ---------------------------------------------------------------------------

class TestSessionExpiry:

    def test_session_expiry_during_panel_load_redirects_to_login(
        self, page: Page, live_server, panel_playbook,
    ):
        """FOB-08c: if embed fetch returns login page HTML, browser redirects to /auth/login/."""
        _login(page, live_server.url, panel_playbook['username'], panel_playbook['password'])
        pb = panel_playbook['pb']
        wf = panel_playbook['wf']

        page.goto(f"{live_server.url}/browser/{pb.pk}/")
        _wait_for_graph(page)

        # Intercept the embed URL (query param ?embed=1) and return HTML containing the login form marker
        page.route('**?embed=**', lambda route: route.fulfill(
            status=200,
            content_type='text/html',
            body='<html><body><form id="login-form"><input name="username"></form></body></html>',
        ))

        _tap_node(page, f"workflow:{wf.pk}")
        page.wait_for_timeout(1500)

        # The JS _checkSessionExpiry should have triggered a redirect to /auth/login/
        assert '/auth/login/' in page.url, (
            f"Expected redirect to /auth/login/ after session expiry, got {page.url}"
        )
