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
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=10000,
    )


def _wait_for_elk_complete(page):
    """Wait for ELK layoutstop to have fired at least once (initial render done)."""
    page.wait_for_function(
        "() => (window._elkLayoutCount || 0) >= 1",
        timeout=15000,
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
    wf2 = Workflow.objects.create(name='LayoutWF2', playbook=pb, order=2)
    Activity.objects.create(name='LayoutAct', workflow=wf, order=1)
    Activity.objects.create(name='LayoutAct2', workflow=wf, order=2)
    Activity.objects.create(name='LayoutAct3', workflow=wf, order=3)
    Activity.objects.create(name='LayoutAct4', workflow=wf2, order=1)
    Activity.objects.create(name='LayoutAct5', workflow=wf2, order=2)
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
        """Layout button is present and defaults to 'Layered ▾' (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        btn = page.locator('[data-testid="browser-layout-btn"]')
        expect(btn).to_be_visible()
        btn_text = btn.text_content()
        assert 'Layered' in btn_text, f"Button should contain 'Layered', got: {btn_text!r}"
        assert '▾' in btn_text, f"Button should contain '▾' chevron, got: {btn_text!r}"

    def test_clicking_layout_button_opens_dropdown(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking layout button opens the 2-level dropdown panel (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        dropdown = page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        assert dropdown is not None, "Dropdown should open after clicking layout button"

    def test_selecting_mrtree_switches_button_label(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Selecting elk-mrtree from dropdown switches button label to 'Tree ▾' (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_elk_complete(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-elk-mrtree"]').click()
        page.wait_for_timeout(500)

        expect(page.locator('[data-testid="browser-layout-btn"]')).to_contain_text('Tree')

    def test_layout_persists_in_url(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """After selecting elk-mrtree, URL contains ?layout=elk-mrtree (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_elk_complete(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-elk-mrtree"]').click()
        page.wait_for_timeout(500)

        assert 'layout=elk-mrtree' in page.url

    def test_selecting_elk_layered_restores_default_label(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Selecting elk-layered from dropdown restores 'Layered ▾' button label (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=elk-mrtree")
        _wait_for_graph(page)
        _wait_for_elk_complete(page)

        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-elk-layered"]').click()
        page.wait_for_timeout(500)

        expect(page.locator('[data-testid="browser-layout-btn"]')).to_contain_text('Layered')

    def test_layout_url_param_applied_on_page_load(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Loading URL with ?layout=elk-mrtree applies Tree layout (FOB-19)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=elk-mrtree")
        _wait_for_graph(page)

        expect(page.locator('[data-testid="browser-layout-btn"]')).to_contain_text('Tree')

    def test_clicking_layout_button_repositions_nodes(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Selecting a different layout actually repositions nodes on canvas (FOB-19 bug fix S27)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_elk_complete(page)  # ensure initial ELK is done before counting

        # Capture positions of all nodes before layout switch
        positions_before = page.evaluate("""() => {
            if (!window.cy) return null;
            return window.cy.nodes().map(n => ({ id: n.id(), x: n.position('x'), y: n.position('y') }));
        }""")
        assert positions_before and len(positions_before) > 0

        count_before = page.evaluate("() => window._elkLayoutCount || 0")
        # Switch to dagre-tb via dropdown
        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-dagre-tb"]').click()
        # Wait for layout run to complete
        page.wait_for_function(f"window._elkLayoutCount > {count_before}", timeout=10000)

        positions_after = page.evaluate("""() => {
            if (!window.cy) return null;
            return window.cy.nodes().map(n => ({ id: n.id(), x: n.position('x'), y: n.position('y') }));
        }""")
        assert positions_after and len(positions_after) == len(positions_before)
        # At least one node must have moved
        changed = any(
            abs(b['x'] - a['x']) > 1 or abs(b['y'] - a['y']) > 1
            for b, a in zip(positions_before, positions_after)
        )
        assert changed, "No nodes repositioned after layout switch — layout did not run"

        positions_after = page.evaluate("""() => {
            if (!window.cy) return null;
            return window.cy.nodes().map(n => ({ id: n.id(), x: n.position('x'), y: n.position('y') }));
        }""")
        assert positions_after and len(positions_after) == len(positions_before)
        # At least one node must have moved
        changed = any(
            abs(b['x'] - a['x']) > 1 or abs(b['y'] - a['y']) > 1
            for b, a in zip(positions_before, positions_after)
        )
        assert changed, "No nodes repositioned after layout switch — layout did not run"


# ---------------------------------------------------------------------------
# S28 — Re-plot button (FOB-29)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestReplotButton:
    """Re-plot button is a manual re-trigger for ELK layout (FOB-29 / S28).

    Note: entity-type filter toggles auto-trigger re-layout on their own.
    Re-plot is for cases where manual re-arrangement is desired without
    changing filter state (e.g. after window resize, after phase dimming).
    """

    def test_replot_button_present(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Re-plot button is visible on the canvas controls (FOB-29)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        expect(page.locator('[data-testid="browser-replot-btn"]')).to_be_visible()

    def test_replot_button_repositions_nodes(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking re-plot manually re-runs ELK layout on current nodes (FOB-29 / S28)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_elk_complete(page)  # ensure initial ELK is done before counting

        # Switch to dagre-tb so re-plot produces a different layout than initial ELK
        count1 = page.evaluate("() => window._elkLayoutCount || 0")
        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-dagre-tb"]').click()
        page.wait_for_function(f"window._elkLayoutCount > {count1}", timeout=10000)

        positions_before = page.evaluate("""() => {
            if (!window.cy) return null;
            return window.cy.nodes().map(n => ({ id: n.id(), x: n.position('x'), y: n.position('y') }));
        }""")
        assert positions_before and len(positions_before) > 0

        # Switch back to elk-layered, then click re-plot — positions should change
        count2 = page.evaluate("() => window._elkLayoutCount || 0")
        page.locator('[data-testid="browser-layout-btn"]').click()
        page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        page.locator('[data-testid="browser-layout-option-elk-layered"]').click()
        page.wait_for_function(f"window._elkLayoutCount > {count2}", timeout=10000)
        count3 = page.evaluate("() => window._elkLayoutCount || 0")
        page.locator('[data-testid="browser-replot-btn"]').click()
        page.wait_for_function(f"window._elkLayoutCount > {count3}", timeout=10000)

        positions_after = page.evaluate("""() => {
            if (!window.cy) return null;
            return window.cy.nodes().map(n => ({ id: n.id(), x: n.position('x'), y: n.position('y') }));
        }""")
        assert positions_after and len(positions_after) == len(positions_before)
        changed = any(
            abs(b['x'] - a['x']) > 1 or abs(b['y'] - a['y']) > 1
            for b, a in zip(positions_before, positions_after)
        )
        assert changed, "Re-plot button did not reposition nodes"


# ---------------------------------------------------------------------------
# S29 — Zoom control buttons (FOB-07b)
# ---------------------------------------------------------------------------

@pytest.mark.django_db(transaction=True)
class TestZoomControls:
    """Zoom control buttons (+, -, fit) work on the canvas (FOB-07b / S29)."""

    def test_zoom_in_button_increases_zoom(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking zoom-in button increases the Cytoscape zoom level (FOB-07b)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        zoom_before = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        assert zoom_before is not None
        page.locator('[data-testid="browser-zoom-in"]').click()
        page.wait_for_timeout(300)
        zoom_after = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        assert zoom_after > zoom_before, f"Zoom-in did not increase zoom: {zoom_before} → {zoom_after}"

    def test_zoom_out_button_decreases_zoom(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking zoom-out button decreases the Cytoscape zoom level (FOB-07b)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        zoom_before = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        assert zoom_before is not None
        page.locator('[data-testid="browser-zoom-out"]').click()
        page.wait_for_timeout(300)
        zoom_after = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        assert zoom_after < zoom_before, f"Zoom-out did not decrease zoom: {zoom_before} → {zoom_after}"

    def test_zoom_fit_button_restores_fit(
        self, page: Page, live_server, layout_user, layout_playbook,
    ):
        """Clicking fit button adjusts zoom so all nodes are visible (FOB-07b)."""
        _login(page, live_server.url, 'layout_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)

        # Zoom in dramatically so the graph is not fully visible
        page.evaluate("() => window.cy && window.cy.zoom(3.0)")
        page.wait_for_timeout(200)
        zoom_after_manual = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        assert zoom_after_manual > 2.5

        page.locator('[data-testid="browser-zoom-fit"]').click()
        page.wait_for_timeout(500)
        zoom_after_fit = page.evaluate("() => window.cy ? window.cy.zoom() : null")
        # Fit should reduce zoom so all nodes are visible (zoom < 3)
        assert zoom_after_fit < zoom_after_manual, f"Fit did not reduce zoom: {zoom_after_manual} → {zoom_after_fit}"
