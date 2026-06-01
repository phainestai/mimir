"""
E2E tests for Content Browser layout position guard (S17).

Covers:
  FOB-CONTENT-BROWSER layout position — panels rendered in expected positions
  Regression guard: the Django template multiline comment bug must not recur

Run:
  DJANGO_SETTINGS_MODULE=mimir.settings uv run pytest tests/e2e/test_content_browser_layout_position.py -x
"""

import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model
from methodology.models import Activity, Playbook, Workflow

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
def layout_user(transactional_db):
    user = User.objects.create_user(
        username='layout_user', email='layout@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def layout_playbook(layout_user, transactional_db):
    pb = Playbook.objects.create(
        name='LayoutPlaybook', description='Layout position tests',
        category='development', status='released', version='1.0',
        source='owned', author=layout_user, visibility='public',
    )
    wf = Workflow.objects.create(name='LayoutWF', playbook=pb, order=1)
    Activity.objects.create(name='LayoutAct', workflow=wf, order=1)
    return pb


# ---------------------------------------------------------------------------
# Layout position guard tests
# ---------------------------------------------------------------------------

class TestLayoutPosition:

    def test_left_panel_positioned_on_left_side(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Left panel must start at x ≈ 0 (no stray text pushes it right)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        left = page.evaluate(
            "document.getElementById('browser-left-panel').getBoundingClientRect().left"
        )
        assert left < 20, f"Left panel should start near 0, got {left}px"

    def test_canvas_positioned_after_left_panel(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Canvas must start to the right of the left panel (≥ 270 px)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        canvas_left = page.evaluate(
            "document.getElementById('browser-canvas-wrapper').getBoundingClientRect().left"
        )
        assert canvas_left >= 270, f"Canvas should be to right of panel, got {canvas_left}px"

    def test_toggle_button_positioned_at_panel_edge(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Toggle button should be at ≈ 280 px from left when panel is expanded."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        # The toggle button's centre should be at ~280px (within ±30px tolerance)
        btn_rect = page.evaluate(
            "document.querySelector('[data-testid=\"browser-toggle-left-panel\"]').getBoundingClientRect()"
        )
        centre_x = (btn_rect['left'] + btn_rect['right']) / 2
        assert 250 <= centre_x <= 310, f"Toggle button centre should be ~280px, got {centre_x}"

    def test_no_stray_text_rendered_outside_browser_root(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """No raw template comment text should appear in the DOM (regression guard)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        root_text = page.evaluate(
            "() => { const root = document.getElementById('browser-root'); "
            "  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT); "
            "  const texts = []; let n; "
            "  while ((n = walker.nextNode())) { "
            "    const t = n.textContent.trim(); "
            "    if (t.length > 5 && n.parentElement.id === 'browser-root') texts.push(t); "
            "  } return texts; }"
        )
        assert root_text == [], f"Stray text nodes found in #browser-root: {root_text}"

    def test_after_collapse_panel_width_is_zero(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """After collapsing the panel, its width should be 0 (or near 0)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-toggle-left-panel"]').click()
        page.wait_for_timeout(400)

        width = page.evaluate(
            "document.getElementById('browser-left-panel').getBoundingClientRect().width"
        )
        assert width < 5, f"Collapsed panel width should be ~0, got {width}px"

    def test_after_collapse_toggle_button_is_on_left_edge(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """After collapse, toggle button should move near left edge (≤ 20 px)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-toggle-left-panel"]').click()
        page.wait_for_timeout(400)

        btn_rect = page.evaluate(
            "document.querySelector('[data-testid=\"browser-toggle-left-panel\"]').getBoundingClientRect()"
        )
        centre_x = (btn_rect['left'] + btn_rect['right']) / 2
        assert centre_x <= 20, f"Collapsed toggle button should be near left, got {centre_x}px"


# ---------------------------------------------------------------------------
# FOB-20b: No performance warning banner in DOM (S19)
# ---------------------------------------------------------------------------

class TestNoDegradedBanner:

    def test_degraded_banner_absent_from_dom(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """browser-degraded-banner must not exist in the DOM at all (FOB-20b)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        count = page.locator('[data-testid="browser-degraded-banner"]').count()
        assert count == 0, "Degraded-mode banner must be absent from the DOM"


# ---------------------------------------------------------------------------
# S21 / FOB-19: ELK layout switcher (Layered ↔ MTree)
# ---------------------------------------------------------------------------

class TestLayoutSwitcher:

    def test_layout_button_present_and_shows_layered(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Layout switcher button is present and defaults to 'Layered' (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        btn = page.locator('[data-testid="browser-layout-btn"]')
        expect(btn).to_be_visible()
        expect(btn).to_contain_text('Layered')

    def test_clicking_layout_button_switches_to_mrtree(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking layout button switches label to 'MTree' (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_timeout(500)

        expect(page.locator('[data-testid="browser-layout-btn"]')).to_contain_text('MTree')

    def test_layout_persists_in_url(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """After switching to MTree, URL contains ?layout=mrtree (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_timeout(500)

        assert 'layout=mrtree' in page.url

    def test_clicking_again_switches_back_to_layered(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking layout button twice returns to 'Layered' and removes URL param (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        btn = page.locator('[data-testid="browser-layout-btn"]')
        btn.click()
        page.wait_for_timeout(500)
        btn.click()
        page.wait_for_timeout(500)

        expect(btn).to_contain_text('Layered')
        assert 'layout=' not in page.url

    def test_layout_url_param_applied_on_page_load(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Loading URL with ?layout=mrtree applies MTree layout (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=mrtree")
        _wait_for_graph(page)

        expect(page.locator('[data-testid="browser-layout-btn"]')).to_contain_text('MTree')
