"""
E2E tests for Content Browser workflow compound view toggle (FOB-37).

Covers:
  - FOB-CONTENT-BROWSER-37: Compound view toggle — workflows as containing boxes vs graph nodes

Checkpoint command:
  pytest tests/e2e/test_content_browser_compound_view.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model


User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


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


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    """Log in and navigate to the content browser graph for any released playbook."""
    user = django_user_model.objects.create_user(username='compound_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'compound_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestCompoundViewDefault:
    """FOB-37: Compound view toggle — default flat mode."""

    def test_compound_toggle_button_visible_in_canvas_controls(self, graph_page: Page):
        """browser-compound-toggle is present in the canvas controls area."""
        btn = graph_page.locator('[data-testid="browser-compound-toggle"]')
        expect(btn).to_be_visible()

    def test_default_mode_is_flat(self, graph_page: Page):
        """By default, _compoundViewOn is false and no node has a parent in cy."""
        is_compound = graph_page.evaluate("() => window._compoundViewOn")
        assert is_compound is False
        parent_count = graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isChild()).length"
        )
        assert parent_count == 0

    def test_compound_mode_activated_by_url_param(self, graph_page: Page, live_server):
        """?compound=1 causes compound mode to be active on page load."""
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        graph_page.goto(f"{live_server.url}/browser/graph/{pb.id}/?compound=1")
        _wait_for_graph(graph_page)
        is_compound = graph_page.evaluate("() => window._compoundViewOn")
        assert is_compound is True
        btn = graph_page.locator('[data-testid="browser-compound-toggle"]')
        expect(btn).to_contain_text('Grouped ✓')


@pytest.mark.django_db(transaction=True)
class TestCompoundViewActivation:
    """FOB-37: Compound view toggle — compound mode element structure."""

    def test_compound_on_sets_workflow_nodes_as_parents(self, graph_page: Page):
        """After enabling compound view, workflow nodes become compound parents in cy."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        parent_count = graph_page.evaluate(
            "() => window.cy.nodes('[type = \"workflow\"]').filter(n => n.isParent()).length"
        )
        assert parent_count > 0, "Expected at least one workflow node to be a compound parent"

    def test_compound_on_activities_have_parent_set_to_workflow(self, graph_page: Page):
        """Each activity node's parent() is its containing workflow node."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        orphan_activities = graph_page.evaluate(
            "() => window.cy.nodes('[type = \"activity\"]').filter(n => !n.isChild()).length"
        )
        assert orphan_activities == 0, f"{orphan_activities} activity nodes have no parent in compound mode"

    def test_compound_box_has_light_blue_background(self, graph_page: Page):
        """Compound workflow node background-color is #eef2ff in Cytoscape stylesheet."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        compound_style = graph_page.evaluate("""
            () => {
                const styles = window._cytoscapeCompoundStyle();
                return styles[0] ? styles[0].style['background-color'] : null;
            }
        """)
        assert compound_style == '#eef2ff', f"Expected #eef2ff, got {compound_style}"

    def test_compound_box_has_primary_blue_border(self, graph_page: Page):
        """Compound workflow node border-color is #0d6efd in Cytoscape stylesheet."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        border_color = graph_page.evaluate("""
            () => {
                const styles = window._cytoscapeCompoundStyle();
                return styles[0] ? styles[0].style['border-color'] : null;
            }
        """)
        assert border_color == '#0d6efd', f"Expected #0d6efd, got {border_color}"

    def test_compound_box_label_top_left(self, graph_page: Page):
        """Compound workflow node uses text-valign:top and text-halign:left for label."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        style = graph_page.evaluate("""
            () => {
                const styles = window._cytoscapeCompoundStyle();
                const s = styles[0] ? styles[0].style : {};
                return { valign: s['text-valign'], halign: s['text-halign'] };
            }
        """)
        assert style['valign'] == 'top'
        assert style['halign'] == 'left'

    def test_compound_on_triggers_full_rebuild(self, graph_page: Page):
        """Activating compound view triggers a layout re-run."""
        count_before = graph_page.evaluate("() => window._elkLayoutCount || 0")
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        count_after = graph_page.evaluate("() => window._elkLayoutCount || 0")
        assert count_after > count_before, "Layout re-run expected after compound toggle"

    def test_compound_off_clears_parent_assignments(self, graph_page: Page):
        """After turning compound view OFF, no cy node has a parent (flat mode restored)."""
        # Enable
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        # Disable
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        child_count = graph_page.evaluate(
            "() => window.cy.nodes().filter(n => n.isChild()).length"
        )
        assert child_count == 0, f"Expected 0 child nodes in flat mode, got {child_count}"

    def test_compound_off_triggers_full_rebuild(self, graph_page: Page):
        """Deactivating compound view triggers a layout re-run."""
        # Enable first
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        count_before = graph_page.evaluate("() => window._elkLayoutCount || 0")
        # Disable
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === false")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes().length > 0")
        count_after = graph_page.evaluate("() => window._elkLayoutCount || 0")
        assert count_after > count_before

    def test_compound_state_persisted_in_url(self, graph_page: Page):
        """Enabling compound view adds ?compound=1 to URL; disabling removes it."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        assert 'compound=1' in graph_page.url, f"URL missing compound=1: {graph_page.url}"
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === false")
        assert 'compound=1' not in graph_page.url, f"URL should not contain compound=1: {graph_page.url}"

    def test_clicking_workflow_compound_box_opens_detail_panel(self, graph_page: Page):
        """Clicking a compound parent workflow node opens the Workflow detail panel."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true")
        graph_page.wait_for_function("() => window.cy != null && window.cy.nodes('[type=\"workflow\"]').length > 0")
        # Tap the first workflow node via cy API
        graph_page.evaluate("""
            () => {
                const wfNode = window.cy.nodes('[type="workflow"]').first();
                wfNode.emit('tap');
            }
        """)
        panel = graph_page.locator('[data-testid="browser-detail-panel"]')
        expect(panel).not_to_have_class('d-none')


    # ── S45 skeleton: compound label visible above top-left corner ────────────

    def test_compound_parent_label_visible(self, graph_page: Page):
        """Compound parent nodes must display their workflow label (S45 — FOB-37 fix)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true && window.cy != null")
        graph_page.wait_for_function("() => window.cy.nodes(':parent').length > 0")
        label = graph_page.evaluate(
            "() => window.cy.nodes(':parent').first().data('label')"
        )
        assert label and len(label) > 0, "Parent node must have a non-empty label"

    def test_compound_parent_label_style_uses_floating_position(self, graph_page: Page):
        """Compound parent label style includes negative text-margin-y to float above border (S45)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true && window.cy != null")
        graph_page.wait_for_function("() => window.cy.nodes(':parent').length > 0")
        margin_y = graph_page.evaluate(
            "() => window.cy.nodes(':parent').first().style('text-margin-y')"
        )
        assert float(margin_y) < 0, f"text-margin-y should be negative, got {margin_y}"


    # ── S46 skeleton: compound layout reflowing activity nodes ────────────────

    def test_activity_nodes_positioned_inside_workflow_box(self, graph_page: Page):
        """Activity nodes must be visually contained within their parent compound box (S46)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true && window.cy != null")
        graph_page.wait_for_function("() => window.cy.nodes(':parent').length > 0")
        result = graph_page.evaluate("""
        () => {
            const parent = window.cy.nodes(':parent').first();
            const parentBB = parent.boundingBox();
            const children = parent.children();
            let allInside = true;
            children.forEach(child => {
                const childBB = child.boundingBox();
                if (childBB.x1 < parentBB.x1 || childBB.x2 > parentBB.x2) {
                    allInside = false;
                }
            });
            return allInside;
        }
        """)
        assert result, "All activity nodes should be inside their parent workflow box"

    def test_compound_reflow_on_layout_change_repositions_children(self, graph_page: Page):
        """Switching layout in compound mode must move activity nodes (S46)."""
        graph_page.click('[data-testid="browser-compound-toggle"]')
        graph_page.wait_for_function("() => window._compoundViewOn === true && window.cy != null")
        graph_page.wait_for_function("() => window.cy.nodes(':parent').length > 0")
        positions_before = graph_page.evaluate(
            "() => window.cy.nodes(':parent').first().children().map(n => ({x: n.position('x'), y: n.position('y')}))"
        )
        graph_page.click('[data-testid="browser-layout-btn"]')
        graph_page.wait_for_selector('[data-testid="browser-layout-dropdown"]')
        options = graph_page.locator('[data-testid^="browser-layout-option-"]').all()
        if len(options) > 1:
            options[1].click()
            graph_page.wait_for_function("() => window.cy.nodes().length > 0")
        positions_after = graph_page.evaluate(
            "() => window.cy.nodes(':parent').first().children().map(n => ({x: n.position('x'), y: n.position('y')}))"
        )
        assert positions_before != positions_after, "Positions should change after layout switch"
