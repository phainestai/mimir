"""Integration tests for guest-only auth page guards.

Covers FOB-AUTH-GUARD-* scenarios in docs/features/act-0-auth/authentication.feature
and UAT-01-05 in tests/uat/e2e-uat-flow.feature.

NO MOCKING per .windsurf/rules/do-not-mock-in-integration-tests.md
"""
import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from accounts.models import mark_email_verified


@pytest.mark.django_db
class TestAuthGuestGuards:
    """Logged-in users must not see login or registration forms."""

    @pytest.fixture
    def authenticated_client(self):
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="ValidPass123",
        )
        mark_email_verified(user)
        client.force_login(user)
        return client, user

    def test_logged_in_get_login_redirects_to_profile(self, authenticated_client):
        """FOB-AUTH-GUARD-01: login page redirects authenticated users to profile."""
        client, _user = authenticated_client
        response = client.get(reverse("login"), follow=False)

        assert response.status_code == 302
        assert response.url == reverse("profile")

        profile_response = client.get(reverse("profile"))
        content = profile_response.content.decode("utf-8")
        assert 'data-testid="profile-page"' in content
        assert 'data-testid="login-form"' not in content

    def test_logged_in_get_register_redirects_to_profile(self, authenticated_client):
        """FOB-AUTH-GUARD-02: registration page redirects authenticated users to profile."""
        client, _user = authenticated_client
        response = client.get(reverse("register"), follow=False)

        assert response.status_code == 302
        assert response.url == reverse("profile")

        profile_response = client.get(reverse("profile"))
        content = profile_response.content.decode("utf-8")
        assert 'data-testid="profile-page"' in content
        assert 'data-testid="register-form"' not in content

    def test_logged_in_post_login_redirects_to_profile_without_reauth(
        self, authenticated_client
    ):
        """FOB-AUTH-GUARD-03: POST login while authenticated redirects to profile."""
        client, user = authenticated_client
        response = client.post(
            reverse("login"),
            {"username": "other", "password": "WrongPass123"},
            follow=False,
        )

        assert response.status_code == 302
        assert response.url == reverse("profile")

        dashboard = client.get("/dashboard/")
        assert dashboard.wsgi_request.user.is_authenticated
        assert dashboard.wsgi_request.user.username == user.username

    def test_anonymous_user_can_still_access_login_and_register(self):
        """Guest pages remain available to anonymous sessions."""
        client = Client()

        login_response = client.get(reverse("login"))
        assert login_response.status_code == 200
        assert 'data-testid="login-form"' in login_response.content.decode("utf-8")

        register_response = client.get(reverse("register"))
        assert register_response.status_code == 200
        assert 'data-testid="register-form"' in register_response.content.decode("utf-8")
