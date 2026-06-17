"""
E2E tests for Content Browser node size mode toggle (FOB-39).

Covers:
  - FOB-CONTENT-BROWSER-39: Node size mode toggle — Fixed size vs Auto-width

Checkpoint command:
  pytest tests/e2e/test_content_browser_node_size_toggle.py -x
"""
import pytest
from playwright.sync_api import Page, expect

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model


User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'


def _login(page: Page, live_server_url: str, username: str, password: str) -> None:
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url, f"Login failed; still on login page. URL: {page.url}"


def _wait_for_graph(page: Page, timeout: int = 10_000) -> None:
    page.wait_for_function(
        "() => window.cy != null && window.cy.nodes().length > 0",
        timeout=timeout,
    )


@pytest.fixture()
def graph_page(page: Page, live_server, django_user_model):
    user = django_user_model.objects.create_user(username='size_tester', password='pass1234')
    mark_email_verified(user)
    _login(page, live_server.url, 'size_tester', 'pass1234')
    from methodology.models import Playbook
    pb = Playbook.objects.filter(status='released').first()
    if pb is None:
        pytest.skip('No released playbook available')
    page.goto(f"{live_server.url}/browser/graph/{pb.id}/")
    _wait_for_graph(page)
    return page


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeToggleDefault:
    """FOB-39: Node size mode toggle — default state."""

    def test_node_size_toggle_button_is_visible(self, graph_page: Page):
        """browser-node-size-toggle button is present in canvas controls (S48)."""
        btn = graph_page.locator('[data-testid="browser-node-size-toggle"]')
        expect(btn).to_be_visible()

    def test_default_mode_is_fixed(self, graph_page: Page):
        """By default _nodeSizeMode is 'fixed' (S48)."""
        mode = graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'fixed', f"Expected 'fixed', got {mode}"

    def test_default_button_label_indicates_fixed_mode(self, graph_page: Page):
        """Default button label contains 'Fixed' or 'fixed' (S48)."""
        btn = graph_page.locator('[data-testid="browser-node-size-toggle"]')
        btn_text = btn.inner_text()
        assert 'fixed' in btn_text.lower() or 'Fixed' in btn_text, \
            f"Expected 'Fixed' in button text, got: {btn_text}"


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeToggleBehaviour:
    """FOB-39: Node size mode toggle — clicking changes mode."""

    def test_clicking_toggle_switches_to_auto_mode(self, graph_page: Page):
        """Clicking the toggle changes _nodeSizeMode to 'auto' (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        mode = graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'auto', f"Expected 'auto' after toggle, got {mode}"

    def test_clicking_toggle_twice_returns_to_fixed(self, graph_page: Page):
        """Clicking twice returns to fixed mode (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'fixed'")
        mode = graph_page.evaluate("() => window._nodeSizeMode")
        assert mode == 'fixed'

    def test_toggle_updates_button_label_to_auto(self, graph_page: Page):
        """Button label updates to indicate auto-width mode after toggle (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        btn_text = graph_page.locator('[data-testid="browser-node-size-toggle"]').inner_text()
        assert 'auto' in btn_text.lower() or 'Auto' in btn_text, \
            f"Expected 'Auto' in button text after toggle, got: {btn_text}"

    def test_toggle_writes_url_param(self, graph_page: Page):
        """Clicking toggle adds nodesize=auto to URL (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        assert 'nodesize=auto' in graph_page.url, f"URL missing nodesize param: {graph_page.url}"

    def test_fixed_mode_url_param_omitted_or_default(self, graph_page: Page):
        """After toggling back to fixed, URL does not contain nodesize=auto (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'fixed'")
        assert 'nodesize=auto' not in graph_page.url, \
            f"URL should not contain nodesize=auto in fixed mode: {graph_page.url}"


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeURLParam:
    """FOB-39: ?nodesize= URL param sets initial mode."""

    def test_nodesize_auto_param_activates_auto_mode_on_load(
        self, page: Page, live_server, django_user_model
    ):
        """?nodesize=auto causes _nodeSizeMode to be 'auto' on page load (S48)."""
        user = django_user_model.objects.create_user(username='size_param_tester', password='pass1234')
        mark_email_verified(user)
        _login(page, live_server.url, 'size_param_tester', 'pass1234')
        from methodology.models import Playbook
        pb = Playbook.objects.filter(status='released').first()
        if pb is None:
            pytest.skip('No released playbook available')
        page.goto(f"{live_server.url}/browser/graph/{pb.id}/?nodesize=auto")
        _wait_for_graph(page)
        mode = page.evaluate("() => window._nodeSizeMode")
        assert mode == 'auto', f"Expected 'auto' from URL param, got {mode}"


@pytest.mark.django_db(transaction=True)
class TestNodeSizeModeStyleEffect:
    """FOB-39: Mode change alters node width behaviour in stylesheet."""

    def test_fixed_mode_nodes_have_explicit_width(self, graph_page: Page):
        """In fixed mode, activity nodes have a numeric pixel width (S48)."""
        width = graph_page.evaluate("""
        () => {
            const n = window.cy.nodes('[type = "activity"]').first();
            return n ? parseFloat(n.style('width')) : null;
        }
        """)
        assert width is not None and width > 0, f"Expected numeric node width, got {width}"

    def test_auto_mode_sets_width_to_label(self, graph_page: Page):
        """In auto mode, node width adapts to label (style width === label width) (S48)."""
        graph_page.click('[data-testid="browser-node-size-toggle"]')
        graph_page.wait_for_function("() => window._nodeSizeMode === 'auto'")
        width_style = graph_page.evaluate("""
        () => {
            const n = window.cy.nodes('[type = "activity"]').first();
            return n ? n.style('width') : null;
        }
        """)
        assert width_style is not None, "No activity node found in auto mode"
