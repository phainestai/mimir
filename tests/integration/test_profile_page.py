"""Integration tests for the authenticated profile page."""

import pytest
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse
from rest_framework.authtoken.models import Token

from methodology.models import Playbook, ProcessImprovementProposal


@pytest.mark.django_db
class TestProfilePage:
    def test_profile_requires_login(self):
        client = Client()
        response = client.get(reverse("profile"))
        assert response.status_code == 302

    def test_profile_shows_user_token_pips_playbooks(self):
        client = Client()
        user = User.objects.create_user(
            username="profile_user",
            email="pu@example.com",
            password="SecurePass123",
            first_name="Pat",
            last_name="Profile",
        )
        playbook = Playbook.objects.create(
            name="PB One",
            description="d",
            category="development",
            author=user,
        )
        pip = ProcessImprovementProposal.objects.create(
            playbook=playbook,
            title="My PIP",
            summary="",
            status=ProcessImprovementProposal.STATUS_DRAFT,
            created_by=user,
        )
        client.force_login(user)

        response = client.get(reverse("profile"))

        assert response.status_code == 200
        html = response.content.decode("utf-8")
        assert 'data-testid="profile-page"' in html
        assert "Pat" in html
        assert "Profile" in html
        assert "pu@example.com" in html
        assert 'data-testid="profile-token-field"' in html
        token = Token.objects.get(user=user)
        assert token.key in html
        assert "My PIP" in html
        assert "PB One" in html
        assert reverse("pip_detail", kwargs={"pk": pip.pk}) in html
        assert reverse("playbook_detail", kwargs={"pk": playbook.pk}) in html

    def test_profile_regenerate_token_with_password(self):
        client = Client()
        user = User.objects.create_user(
            username="tok_user",
            email="tok@example.com",
            password="SecurePass123",
        )
        Token.objects.get_or_create(user=user)
        old_key = Token.objects.get(user=user).key
        client.force_login(user)

        response = client.post(
            reverse("profile_regenerate_token"),
            {"current_password": "SecurePass123"},
            follow=True,
        )

        assert response.status_code == 200
        new_key = Token.objects.get(user=user).key
        assert new_key != old_key
        assert new_key.encode() in response.content
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("regenerated" in m.lower() for m in msgs)

    def test_profile_edit_get_shows_prepopulated_form(self):
        client = Client()
        user = User.objects.create_user(
            username="edit_user",
            email="edit@example.com",
            password="SecurePass123",
            first_name="Edit",
            last_name="User",
        )
        client.force_login(user)
        response = client.get(reverse("profile_edit"))
        assert response.status_code == 200
        html = response.content.decode()
        assert 'data-testid="profile-edit-page"' in html
        assert 'value="Edit"' in html
        assert 'value="User"' in html
        assert 'value="edit@example.com"' in html

    def test_profile_edit_saves_and_redirects(self):
        client = Client()
        user = User.objects.create_user(
            username="edit_user2",
            email="edit2@example.com",
            password="SecurePass123",
        )
        client.force_login(user)
        response = client.post(
            reverse("profile_edit"),
            {"first_name": "New", "last_name": "Name", "email": "new@example.com"},
            follow=True,
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.first_name == "New"
        assert user.last_name == "Name"
        assert user.email == "new@example.com"
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("updated" in m.lower() for m in msgs)

    def test_profile_edit_rejects_blank_email(self):
        client = Client()
        user = User.objects.create_user(
            username="edit_user3",
            email="edit3@example.com",
            password="SecurePass123",
        )
        client.force_login(user)
        response = client.post(
            reverse("profile_edit"),
            {"first_name": "X", "last_name": "Y", "email": ""},
        )
        assert response.status_code == 200
        assert 'is-invalid' in response.content.decode()
        user.refresh_from_db()
        assert user.email == "edit3@example.com"

    def test_profile_edit_rejects_duplicate_email(self):
        client = Client()
        User.objects.create_user(username="other_u", email="taken@example.com", password="x")
        user = User.objects.create_user(
            username="edit_user4",
            email="mine@example.com",
            password="SecurePass123",
        )
        client.force_login(user)
        response = client.post(
            reverse("profile_edit"),
            {"first_name": "X", "last_name": "Y", "email": "taken@example.com"},
        )
        assert response.status_code == 200
        assert "already used" in response.content.decode()
        user.refresh_from_db()
        assert user.email == "mine@example.com"

    def test_profile_regenerate_token_rejects_bad_password(self):
        client = Client()
        user = User.objects.create_user(
            username="tok_user2",
            email="tok2@example.com",
            password="SecurePass123",
        )
        Token.objects.get_or_create(user=user)
        old_key = Token.objects.get(user=user).key
        client.force_login(user)

        response = client.post(
            reverse("profile_regenerate_token"),
            {"current_password": "wrong-password"},
            follow=True,
        )

        assert response.status_code == 200
        assert Token.objects.get(user=user).key == old_key
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        assert any("incorrect" in m.lower() or "not changed" in m.lower() for m in msgs)
