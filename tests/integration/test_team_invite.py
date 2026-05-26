"""Integration tests for the team invite-by-email flow (WP-7).

Tests cover:
- TeamInviteService: existing user invite, new user auto-registration, email sending
- TeamInviteView: invite tab visibility, form presence, POST success/error
"""

import pytest
from django.core import mail
from django.contrib.auth.models import User
from methodology.models import Team, TeamMembership, JoinRequest
from methodology.services.team_service import TeamService
from methodology.services.team_invite_service import TeamInviteService


@pytest.mark.django_db
class TestTeamInviteService:
    def setup_method(self):
        self.team_service = TeamService()
        self.invite_service = TeamInviteService()
        self.admin = User.objects.create_user("inv_admin", email="admin@example.com", password="pass")
        self.team = self.team_service.create_team(
            self.admin, "Invite Test Team", "desc", "Public", "Requires Approval", "Engineering"
        )

    def test_invite_existing_user_creates_join_request(self):
        existing = User.objects.create_user("existing_inv", email="existing@example.com", password="pass")
        result = self.invite_service.send_invites(self.team, self.admin, ["existing@example.com"], "Welcome!")
        assert result["sent"] == 1
        assert JoinRequest.objects.filter(team=self.team, user=existing, source="invited").exists()

    def test_invite_existing_user_sends_email(self):
        User.objects.create_user("existing_inv2", email="existing2@example.com", password="pass")
        mail.outbox.clear()
        self.invite_service.send_invites(self.team, self.admin, ["existing2@example.com"], "")
        assert len(mail.outbox) == 1
        assert "existing2@example.com" in mail.outbox[0].to
        assert "invited" in mail.outbox[0].subject.lower() or "Invite Test Team" in mail.outbox[0].body

    def test_invite_new_user_auto_registers(self):
        result = self.invite_service.send_invites(self.team, self.admin, ["newperson@acme.com"], "")
        assert result["created"] == 1
        assert User.objects.filter(email="newperson@acme.com").exists()
        new_user = User.objects.get(email="newperson@acme.com")
        assert new_user.username == "newperson"
        assert new_user.first_name == "newperson"
        assert new_user.last_name == "acme"
        assert not new_user.is_active

    def test_invite_new_user_creates_join_request_invited_new(self):
        self.invite_service.send_invites(self.team, self.admin, ["newuser2@corp.com"], "")
        new_user = User.objects.get(email="newuser2@corp.com")
        assert JoinRequest.objects.filter(team=self.team, user=new_user, source="invited_new").exists()

    def test_invite_new_user_sends_email(self):
        mail.outbox.clear()
        self.invite_service.send_invites(self.team, self.admin, ["brandnew@example.com"], "")
        assert len(mail.outbox) == 1
        assert "brandnew@example.com" in mail.outbox[0].to

    def test_invite_multiple_emails(self):
        User.objects.create_user("mult_existing", email="mult1@example.com", password="pass")
        mail.outbox.clear()
        result = self.invite_service.send_invites(
            self.team, self.admin, ["mult1@example.com", "mult2@acme.com", "mult3@corp.io"], ""
        )
        assert result["sent"] == 3
        assert len(mail.outbox) == 3

    def test_invite_invalid_email_returns_invalid_list(self):
        result = self.invite_service.send_invites(self.team, self.admin, ["not-an-email"], "")
        assert len(result["invalid"]) == 1
        assert result["sent"] == 0

    def test_invite_already_member_returns_skipped(self):
        existing = User.objects.create_user("member_inv", email="member@example.com", password="pass")
        self.team_service.add_member(self.team, existing)
        result = self.invite_service.send_invites(self.team, self.admin, ["member@example.com"], "")
        assert len(result["skipped"]) == 1
        assert result["sent"] == 0

    def test_parse_emails_returns_valid_and_invalid(self):
        service = TeamInviteService()
        valid, invalid = service._parse_emails("alice@example.com, not-valid, bob@example.com")
        assert sorted(valid) == ["alice@example.com", "bob@example.com"]
        assert invalid == ["not-valid"]

    def test_new_user_activation_flow(self, client):
        """Test that new-user invite generates token and activates user on verification."""
        mail.outbox.clear()
        
        # Send invite to new email address
        result = self.invite_service.send_invites(
            self.team, self.admin, ["activate_test@example.com"], "Welcome!"
        )
        assert result["created"] == 1
        assert result["sent"] == 1
        
        # Check user was created as inactive
        new_user = User.objects.get(email="activate_test@example.com")
        assert not new_user.is_active
        
        # Check email was sent with activation token
        assert len(mail.outbox) == 1
        email_body = mail.outbox[0].body
        assert "/auth/user/verify-email/" in email_body
        
        # Extract token from email body
        import re
        token_match = re.search(r'/auth/user/verify-email/([a-zA-Z0-9_-]+)/', email_body)
        assert token_match is not None
        token = token_match.group(1)
        
        # GET the verification URL
        response = client.get(f"/auth/user/verify-email/{token}/")
        assert response.status_code == 302  # Redirect to login
        
        # Check user is now active and verified
        new_user.refresh_from_db()
        assert new_user.is_active
        assert new_user.email_verification.is_verified


@pytest.mark.django_db
class TestTeamInviteView:
    def setup_method(self):
        self.team_service = TeamService()
        self.admin = User.objects.create_user("view_admin", email="vadmin@example.com", password="pass")
        self.team = self.team_service.create_team(
            self.admin, "View Invite Team", "desc", "Public", "Requires Approval", "Engineering"
        )

    def test_invite_tab_visible_on_manage_page(self, client):
        client.force_login(self.admin)
        response = client.get(f"/teams/{self.team.pk}/manage/")
        assert response.status_code == 200
        assert b'data-testid="team-tab-invite"' in response.content

    def test_invite_form_present_on_invite_tab(self, client):
        client.force_login(self.admin)
        response = client.get(f"/teams/{self.team.pk}/manage/?tab=invite")
        assert response.status_code == 200
        assert b'data-testid="invite-emails-input"' in response.content
        assert b'data-testid="team-invite-submit"' in response.content

    def test_invite_post_valid_email_success_banner(self, client):
        User.objects.create_user("invite_target", email="target@example.com", password="pass")
        client.force_login(self.admin)
        response = client.post(f"/teams/{self.team.pk}/manage/", {
            "action": "send_invites",
            "invite_emails": "target@example.com",
            "invite_welcome": "Hello!",
        })
        assert response.status_code == 302

    def test_invite_post_invalid_email_shows_error(self, client):
        client.force_login(self.admin)
        response = client.post(f"/teams/{self.team.pk}/manage/?tab=invite", {
            "action": "send_invites",
            "invite_emails": "not-an-email",
            "invite_welcome": "",
        })
        assert response.status_code == 200
        assert b"invalid" in response.content.lower() or b"not-an-email" in response.content
