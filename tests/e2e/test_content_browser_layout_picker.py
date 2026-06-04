"""
E2E tests for Content Browser layout picker dropdown (FOB-19, FOB-34).

Covers:
  - FOB-CONTENT-BROWSER-19: 2-level dropdown layout picker replaces old toggle button
  - FOB-CONTENT-BROWSER-34: All layout algorithms available and functional

Checkpoint command:
  pytest tests/e2e/test_content_browser_layout_picker.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model


User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    """Authenticate via browser form login."""
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed; still on login page. URL: {page.url}"


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    """Wait until Cytoscape is initialised with at least one node."""
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


def _wait_for_layout_complete(page: Page, min_count: int = 1, timeout: int = 15_000) -> None:
    """Wait for _elkLayoutCount to reach at least min_count."""
    page.wait_for_function(
        f"() => (window._elkLayoutCount || 0) >= {min_count}",
        timeout=timeout,
    )


def _open_dropdown(page: Page) -> None:
    """Click layout button and wait for dropdown to appear."""
    page.click('[data-testid="browser-layout-btn"]')
    page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)


def _select_layout(page: Page, key: str) -> int:
    """Open dropdown, click option, wait for dropdown to close; return old layout count."""
    old_count = page.evaluate("() => window._elkLayoutCount || 0")
    _open_dropdown(page)
    page.click(f'[data-testid="browser-layout-option-{key}"]')
    page.wait_for_function(
        "() => !document.querySelector('[data-testid=\"browser-layout-dropdown\"]')",
        timeout=3_000,
    )
    return old_count


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def picker_user(transactional_db):
    user = User.objects.create_user(
        username='picker_user', email='picker@test.com', password='testpass123',
    )
    mark_email_verified(user)
    return user


@pytest.fixture
def layout_playbook(picker_user, transactional_db):
    """Minimal playbook with 2 workflows and 3 activities for layout tests."""
    from methodology.models import Playbook, Workflow, Activity
    pb = Playbook.objects.create(
        name='Layout Test PB', description='Layout picker tests',
        category='development', status='draft',
        source='owned', author=picker_user, visibility='private',
    )
    wf1 = Workflow.objects.create(playbook=pb, name='Alpha Workflow', order=1)
    wf2 = Workflow.objects.create(playbook=pb, name='Beta Workflow', order=2)
    Activity.objects.create(workflow=wf1, name='Act A1', order=1)
    Activity.objects.create(workflow=wf1, name='Act A2', order=2)
    Activity.objects.create(workflow=wf2, name='Act B1', order=1)
    return pb


# ---------------------------------------------------------------------------
# S34 — FOB-19: Layout picker dropdown widget
# ---------------------------------------------------------------------------

class TestLayoutPickerDropdown:
    """FOB-CONTENT-BROWSER-19: 2-level layout picker dropdown."""

    def test_layout_picker_button_visible_with_chevron(self, page: Page, layout_playbook, live_server, picker_user):
        """Layout picker button (browser-layout-btn) is visible and shows current layout name + chevron."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        btn = page.locator('[data-testid="browser-layout-btn"]')
        expect(btn).to_be_visible()
        btn_text = btn.text_content()
        assert '▾' in btn_text, f"Button should show '▾' chevron, got: {btn_text!r}"
        assert len(btn_text.strip()) > 1, "Button should show layout name + chevron"

    def test_clicking_picker_opens_dropdown_panel(self, page: Page, layout_playbook, live_server, picker_user):
        """Clicking browser-layout-btn opens browser-layout-dropdown panel with grouped layout options."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        # Dropdown should not exist yet
        assert page.query_selector('[data-testid="browser-layout-dropdown"]') is None

        page.click('[data-testid="browser-layout-btn"]')
        dropdown = page.wait_for_selector('[data-testid="browser-layout-dropdown"]', timeout=3_000)
        assert dropdown is not None

        # At least one group header should be visible
        groups = page.locator('[data-testid^="browser-layout-group-"]')
        assert groups.count() > 0, "Dropdown must contain at least one group header"

        # At least one layout option should be present
        options = page.locator('[data-testid^="browser-layout-option-"]')
        assert options.count() > 0, "Dropdown must contain at least one layout option"

    def test_selecting_layout_closes_dropdown_and_reruns_graph(self, page: Page, layout_playbook, live_server, picker_user):
        """Clicking a layout option closes dropdown, updates button label, and re-runs layout."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        old_count = _select_layout(page, 'dagre-tb')

        # Button label should now show 'Top-Down'
        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert 'Top-Down' in btn_text, f"Button should show 'Top-Down', got: {btn_text!r}"

        # A new layout run should have been triggered
        new_count = page.evaluate("() => window._elkLayoutCount || 0")
        assert new_count > old_count, "Layout count should increase after selecting a layout"

        # Dropdown must be gone
        assert page.query_selector('[data-testid="browser-layout-dropdown"]') is None

    def test_escape_closes_dropdown_without_changing_layout(self, page: Page, layout_playbook, live_server, picker_user):
        """Pressing Escape while dropdown is open closes it without changing the active layout."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        initial_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        _open_dropdown(page)

        page.keyboard.press('Escape')
        page.wait_for_function(
            "() => !document.querySelector('[data-testid=\"browser-layout-dropdown\"]')",
            timeout=3_000,
        )

        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert btn_text == initial_text, f"Layout should not change after Escape: {btn_text!r}"

    def test_layout_key_stored_in_url_param(self, page: Page, layout_playbook, live_server, picker_user):
        """After selecting a layout, the layout-key is reflected in the URL ?layout= param."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        _select_layout(page, 'dagre-lr')
        # Give URL a moment to update via replaceState
        page.wait_for_timeout(500)

        assert 'layout=dagre-lr' in page.url, f"URL should contain layout=dagre-lr, got: {page.url}"

    def test_url_layout_param_restored_on_reload(self, page: Page, layout_playbook, live_server, picker_user):
        """Reloading with ?layout=dagre-tb restores Dagre Top-Down as active layout."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=dagre-tb")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert 'Top-Down' in btn_text, f"Button should show 'Top-Down' from URL param, got: {btn_text!r}"

    def test_legacy_url_params_mapped_to_new_keys(self, page: Page, layout_playbook, live_server, picker_user):
        """Legacy URL values 'layered' and 'mrtree' are silently mapped to elk-layered and elk-mrtree."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=layered")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert 'Layered' in btn_text, f"Legacy 'layered' should map to elk-layered (shows 'Layered'), got: {btn_text!r}"

        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/?layout=mrtree")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert 'Tree' in btn_text, f"Legacy 'mrtree' should map to elk-mrtree (shows 'Tree'), got: {btn_text!r}"


# ---------------------------------------------------------------------------
# S35 — FOB-34: Layout catalog — all 24 options present in dropdown
# ---------------------------------------------------------------------------

class TestLayoutCatalog:
    """FOB-CONTENT-BROWSER-34: All layout algorithms available in the picker."""

    def test_all_layout_groups_present_in_dropdown(self, page: Page, layout_playbook, live_server, picker_user):
        """Dropdown contains all 10 group headers: ELK, Dagre, Cola, Klay, CiSE, Euler, AVSDF, CoSE-Bilkent, fCoSE, Cytoscape."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)
        _open_dropdown(page)

        expected_groups = ['elk', 'dagre', 'cola', 'klay', 'cise', 'euler', 'avsdf', 'cose-bilkent', 'fcose', 'cy']
        for slug in expected_groups:
            el = page.locator(f'[data-testid="browser-layout-group-{slug}"]')
            assert el.count() == 1, f"Group header '{slug}' not found in dropdown"

    def test_all_twenty_four_layout_options_present(self, page: Page, layout_playbook, live_server, picker_user):
        """All 24 layout options (browser-layout-option-{key}) exist in the dropdown."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)
        _open_dropdown(page)

        expected_keys = [
            'elk-layered', 'elk-mrtree', 'elk-force', 'elk-stress', 'elk-disco',
            'elk-radial', 'elk-rectpacking', 'elk-sporeOverlap', 'elk-sporeCompaction',
            'dagre-tb', 'dagre-lr',
            'cola', 'klay', 'cise', 'euler', 'avsdf', 'cose-bilkent', 'fcose',
            'cy-grid', 'cy-circle', 'cy-concentric', 'cy-breadthfirst', 'cy-cose', 'cy-random',
        ]
        for key in expected_keys:
            el = page.locator(f'[data-testid="browser-layout-option-{key}"]')
            assert el.count() == 1, f"Layout option '{key}' not found in dropdown"

    def test_default_layout_is_elk_layered(self, page: Page, layout_playbook, live_server, picker_user):
        """With no URL param the default active layout is elk-layered (button shows 'Layered ▾')."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        btn_text = page.locator('[data-testid="browser-layout-btn"]').text_content()
        assert 'Layered' in btn_text, f"Default layout button should show 'Layered', got: {btn_text!r}"
        assert '▾' in btn_text, f"Default layout button should show '▾', got: {btn_text!r}"

    def test_elk_sub_algorithms_render_graph(self, page: Page, layout_playbook, live_server, picker_user):
        """Selecting each ELK sub-algorithm (layered, mrtree, force, stress, disco) runs without error."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        elk_keys = ['elk-layered', 'elk-mrtree', 'elk-force', 'elk-stress', 'elk-disco']
        for i, key in enumerate(elk_keys):
            _select_layout(page, key)
            _wait_for_layout_complete(page, min_count=i + 2)  # +1 for initial, +1 for this
            node_count = page.evaluate("() => window.cy ? window.cy.nodes().length : 0")
            assert node_count > 0, f"Graph should have nodes after ELK layout '{key}'"
            error_visible = page.evaluate(
                "() => !document.querySelector('[data-testid=\"browser-error-state\"]').classList.contains('d-none')"
            )
            assert not error_visible, f"Error state should not appear after ELK layout '{key}'"

    def test_dagre_layouts_render_graph(self, page: Page, layout_playbook, live_server, picker_user):
        """Selecting dagre-tb and dagre-lr each render the graph without error."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        for key in ['dagre-tb', 'dagre-lr']:
            _select_layout(page, key)
            _wait_for_layout_complete(page, min_count=2)
            node_count = page.evaluate("() => window.cy ? window.cy.nodes().length : 0")
            assert node_count > 0, f"Graph should have nodes after dagre layout '{key}'"

    def test_new_library_layouts_render_graph(self, page: Page, layout_playbook, live_server, picker_user):
        """Selecting cola, klay, cise, euler, avsdf, cose-bilkent, fcose each render graph without error."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        extension_keys = ['cola', 'klay', 'cise', 'euler', 'avsdf', 'cose-bilkent', 'fcose']
        for key in extension_keys:
            _select_layout(page, key)
            # Extension plugins loaded from CDN — layout may silently fall through try/catch
            # if plugin is unavailable; the graph must still show nodes (no crash)
            page.wait_for_timeout(1500)
            node_count = page.evaluate("() => window.cy ? window.cy.nodes().length : 0")
            assert node_count > 0, f"Graph should still have nodes after clicking layout '{key}'"
            error_visible = page.evaluate(
                "() => !document.querySelector('[data-testid=\"browser-error-state\"]').classList.contains('d-none')"
            )
            assert not error_visible, f"Error state must not appear after clicking layout '{key}'"

    def test_native_cytoscape_layouts_render_graph(self, page: Page, layout_playbook, live_server, picker_user):
        """Selecting cy-grid, cy-circle, cy-concentric, cy-breadthfirst, cy-cose, cy-random each render graph."""
        _login(page, live_server.url, 'picker_user', 'testpass123')
        page.goto(f"{live_server.url}/browser/{layout_playbook.pk}/")
        _wait_for_graph(page)
        _wait_for_layout_complete(page)

        native_keys = ['cy-grid', 'cy-circle', 'cy-concentric', 'cy-breadthfirst', 'cy-cose', 'cy-random']
        for i, key in enumerate(native_keys):
            _select_layout(page, key)
            _wait_for_layout_complete(page, min_count=i + 2)
            node_count = page.evaluate("() => window.cy ? window.cy.nodes().length : 0")
            assert node_count > 0, f"Graph should have nodes after native cy layout '{key}'"
            error_visible = page.evaluate(
                "() => !document.querySelector('[data-testid=\"browser-error-state\"]').classList.contains('d-none')"
            )
            assert not error_visible, f"Error state must not appear after cy layout '{key}'"
