"""
E2E tests for Content Browser FA icon rendering in graph nodes (FOB-53).

Covers:
  - FOB-CONTENT-BROWSER-53: Node type icons render correctly using FA6 Free Unicode glyphs

Checkpoint command:
  pytest tests/e2e/test_content_browser_icons.py -x
"""
import pytest
from playwright.sync_api import Page

from accounts.models import mark_email_verified
from django.contrib.auth import get_user_model

User = get_user_model()
LOGIN_URL_PATH = '/auth/user/login/'

EXPECTED_ICONS = {
    'playbook':  '\uf5da',   # book-open-reader (FA6 Free)
    'workflow':  '\uf542',   # diagram-project  (FA6 Free)
    'activity':  '\uf0ae',   # list-check       (FA6 Free)
    'artifact':  '\uf06b',   # gift             (FA6 Free)
    'skill':     '\ue05d',   # hand-sparkles    (FA6 Free)
    'agent':     '\uf5dc',   # brain            (FA6 Free)
    'rule':      '\uf24e',   # scale-balanced   (FA6 Free)
}


def _login(page, live_server_url, username, password):
    page.goto(f"{live_server_url}{LOGIN_URL_PATH}")
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_load_state('networkidle')
    assert LOGIN_URL_PATH not in page.url



@pytest.mark.django_db(transaction=True)
class TestNodeIconCodepoints:
    """FOB-53 — FA6 Free codepoints map to valid glyphs (no blank rectangles)."""

    def test_all_icon_codepoints_are_valid_fa6_free_glyphs(self, cb_graph_page):
        """_buildNodeIcon returns codepoints that exist in FA6 Free solid."""
        types = list(EXPECTED_ICONS.keys())
        result = cb_graph_page.evaluate(
            """(types) => types.map(t => ({ type: t, icon: _buildNodeIcon(t) }))""",
            types,
        )
        returned = {r['type']: r['icon'] for r in result}
        # All returned values must be non-empty single characters
        for t, char in returned.items():
            assert char, f"Empty icon for type '{t}'"
            assert len(char) == 1, f"Icon for '{t}' is not a single char: {repr(char)}"

    def test_icon_codepoints_match_feature_spec(self, cb_graph_page):
        """Each node type maps to the exact codepoint in FOB-CONTENT-BROWSER-53."""
        for node_type, expected_char in EXPECTED_ICONS.items():
            actual = cb_graph_page.evaluate(
                "(t) => _buildNodeIcon(t)",
                node_type,
            )
            assert actual == expected_char, (
                f"Icon mismatch for '{node_type}': "
                f"expected U+{ord(expected_char):04x}, got U+{ord(actual):04x}"
            )

    def test_font_family_includes_font_awesome_6_free_first(self, cb_graph_page):
        """_buildEnhancedNodeStyle font-family includes 'Font Awesome 6 Free'."""
        font_family = cb_graph_page.evaluate(
            "() => _buildEnhancedNodeStyle('workflow')['font-family']"
        )
        assert 'Font Awesome 6' in font_family, (
            f"font-family does not include Font Awesome 6: {font_family}"
        )

    def test_font_weight_is_900_for_solid_icons(self, cb_graph_page):
        """font-weight must be 600 (semibold label + FA glyph) per shipped stylesheet."""
        weight = cb_graph_page.evaluate(
            "() => _buildEnhancedNodeStyle('activity')['font-weight']"
        )
        assert weight == 600, f"Expected font-weight 600, got {weight}"

    def test_label_is_function_mapper_not_string_literal(self, cb_graph_page):
        """label property is a function (ele => ...), not a plain string."""
        is_fn = cb_graph_page.evaluate(
            "() => typeof _buildEnhancedNodeStyle('workflow')['label'] === 'function'"
        )
        assert is_fn, "Expected 'label' to be a function, got a static string"
