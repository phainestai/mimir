"""Unit tests for deploy-time UI brand pack (MIMIR_UI_BRAND / UI_BRAND)."""

import pytest
from django.test import RequestFactory, override_settings

from methodology.context_processors import ui_brand


@pytest.mark.django_db
class TestUiBrandContextProcessor:
    """context_processors.ui_brand exposes brand flags to templates."""

    def setup_method(self):
        self.factory = RequestFactory()

    @override_settings(UI_BRAND='')
    def test_stock_brand_is_empty(self):
        request = self.factory.get('/')
        ctx = ui_brand(request)
        assert ctx['ui_brand'] == ''
        assert ctx['ui_brand_professional'] is False

    @override_settings(UI_BRAND='professional')
    def test_professional_brand_flag_true(self):
        request = self.factory.get('/')
        ctx = ui_brand(request)
        assert ctx['ui_brand'] == 'professional'
        assert ctx['ui_brand_professional'] is True

    @override_settings(UI_BRAND='PROFESSIONAL')
    def test_brand_normalized_to_lowercase(self):
        request = self.factory.get('/')
        ctx = ui_brand(request)
        assert ctx['ui_brand'] == 'professional'
        assert ctx['ui_brand_professional'] is True


@pytest.mark.django_db
class TestUiBrandTemplateWiring:
    """base.html loads professional brand assets only when UI_BRAND=professional."""

    def test_stock_omits_professional_css_and_theme_toggle(self, client, django_user_model):
        user = django_user_model.objects.create_user(username='brand_stock', password='pass')
        client.force_login(user)
        with override_settings(UI_BRAND=''):
            resp = client.get('/dashboard/')
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'css/brands/professional.css' not in content
        assert 'data-testid="ui-brand-professional-css"' not in content
        assert 'data-testid="theme-toggle"' not in content
        assert 'IBM+Plex+Sans' not in content
        assert 'Montserrat' in content

    def test_professional_includes_brand_css_font_and_toggle(self, client, django_user_model):
        user = django_user_model.objects.create_user(username='brand_professional', password='pass')
        client.force_login(user)
        with override_settings(UI_BRAND='professional'):
            resp = client.get('/dashboard/')
        assert resp.status_code == 200
        content = resp.content.decode()
        assert 'css/brands/professional.css' in content
        assert 'data-testid="ui-brand-professional-css"' in content
        assert 'data-testid="theme-toggle"' in content
        assert 'IBM+Plex+Sans' in content
        assert 'Montserrat' in content
