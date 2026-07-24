"""Regression tests for Mimir base layout (Huginn hg-* design system shell)."""

import pytest
from django.test import Client


@pytest.mark.django_db
def test_authenticated_dashboard_includes_hg_navbar_and_main(client, django_user_model):
    user = django_user_model.objects.create_user(username="shell_tester", password="pass")
    client.force_login(user)
    response = client.get("/dashboard/")
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="main-navbar"' in body
    assert "hg-navbar" in body
    assert 'class="hg-main flex-grow-1"' in body
    assert 'data-testid="nav-playbooks"' in body
    assert "Montserrat" in body
    assert 'data-testid="theme-toggle"' not in body


@pytest.mark.django_db
def test_anonymous_landing_uses_hg_landing_classes():
    client = Client()
    response = client.get("/")
    assert response.status_code == 200
    body = response.content.decode()
    assert 'data-testid="landing-loaded"' in body
    assert 'data-testid="landing-hero"' in body
    assert "hg-landing-hero" in body
    assert "mm-landing-hero" not in body


@pytest.mark.django_db
def test_anonymous_landing_hides_app_nav_items():
    client = Client()
    response = client.get("/")
    body = response.content.decode()
    for testid in ("nav-dashboard", "nav-playbooks", "nav-workflows", "nav-pips"):
        assert f'data-testid="{testid}"' not in body, f"app nav {testid!r} leaked to landing"


@pytest.mark.django_db
def test_playbook_list_renders_hg_page_header(client, django_user_model):
    user = django_user_model.objects.create_user(username="list_shell", password="pass")
    client.force_login(user)
    response = client.get("/playbooks/")
    assert response.status_code == 200
    body = response.content.decode()
    assert "hg-page-header" in body
    assert 'data-testid="playbooks-list-header"' in body
    assert "design-system.css" in body
    assert "mimir-app.css" in body
