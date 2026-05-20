"""Integration tests for feedback UI and bug report API."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


pytestmark = pytest.mark.integration
User = get_user_model()


@pytest.mark.django_db
def test_submit_feedback_happy_path(client):
    user = User.objects.create_user(
        username="fb_user",
        email="fb@example.com",
        password="not-used-here",
    )
    client.force_login(user)
    url = reverse("feedback_report")
    response = client.post(
        url,
        data={
            "description": "Export button does nothing",
            "page_url": "http://testserver/playbooks/1/",
            "app_version": "0.1.0-rc1",
            "form_data": "",
        },
    )
    assert response.status_code == 200
    content = response.content.decode()
    assert "Thank you" in content
    assert "feedback-submit-result" in content


@pytest.mark.django_db
def test_submit_feedback_redirects_when_anonymous(client):
    url = reverse("feedback_report")
    response = client.post(
        url,
        data={
            "description": "Something",
            "reporter_email": "anon@example.com",
        },
    )
    assert response.status_code == 302
    assert "login" in response.url


@pytest.mark.django_db
def test_submit_feedback_requires_description(client):
    user = User.objects.create_user(
        username="fb2",
        email="fb2@example.com",
        password="x",
    )
    client.force_login(user)
    url = reverse("feedback_report")
    response = client.post(
        url,
        data={
            "description": "",
        },
    )
    assert response.status_code == 200
    assert "Please describe" in response.content.decode()


@pytest.mark.django_db
def test_api_feedback_report_creates_issue():
    user = User.objects.create_user(
        username="api_fb",
        email="api@example.com",
        password="secret123",
    )
    token, _ = Token.objects.get_or_create(user=user)
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    url = reverse("api_feedback_report")
    response = api.post(
        url,
        data={
            "description": "MCP list_playbooks returned empty",
            "page_context": "playbook_id=3",
        },
        format="json",
    )
    assert response.status_code == 201
    assert "issue_url" in response.data
    assert response.data.get("issue_number") == 0  # dry-run in test settings


@pytest.mark.django_db
def test_api_feedback_report_requires_auth():
    api = APIClient()
    url = reverse("api_feedback_report")
    response = api.post(
        url,
        data={"description": "x", "reporter_email": "a@b.com"},
        format="json",
    )
    assert response.status_code == 401
