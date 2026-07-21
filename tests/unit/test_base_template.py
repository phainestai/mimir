"""Unit tests for base.html's default UI chrome (theme toggle, font link)."""

import pytest


@pytest.mark.django_db
class TestBaseTemplateDefaultTheme:
    """base.html renders the default design system unconditionally."""

    def test_dashboard_renders_theme_toggle_and_ibm_plex_font(self, client, django_user_model):
        user = django_user_model.objects.create_user(username='base_template_tester', password='pass')
        client.force_login(user)
        resp = client.get('/dashboard/')
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'data-testid="theme-toggle"' in content
        assert 'id="mimir-theme-toggle"' in content
        assert 'IBM+Plex+Sans' in content
        assert 'data-bs-theme="light"' in content
