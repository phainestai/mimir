"""Integration tests for team detail view (WP-4 — FOB-TEAMS-VIEW-*).

Covers join_state logic, POST join/leave actions, and HTTP responses.
"""
import pytest
from django.contrib.auth.models import User

from methodology.models import JoinRequest, Team, TeamMembership
from methodology.services.team_service import TeamService


@pytest.mark.django_db
class TestTeamDetailView:
    def setup_method(self):
        self.service = TeamService()

    def test_detail_requires_login(self, client):
        admin = User.objects.create_user("adminx", password="pass")
        team = self.service.create_team(
            admin, "Test Team DV", "", "Public", "Auto-approve", "Engineering"
        )
        response = client.get(f"/teams/{team.pk}/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_detail_renders_for_public_team(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d1", password="pass")
        user = django_user_model.objects.create_user("user_d1", password="pass")
        team = self.service.create_team(
            admin, "Usability Team", "Best practices", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert response.status_code == 200
        assert b"Usability Team" in response.content
        assert b'data-testid="team-detail-page"' in response.content

    def test_detail_shows_join_button_for_non_member(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d2", password="pass")
        user = django_user_model.objects.create_user("user_d2", password="pass")
        team = self.service.create_team(
            admin, "Public Team D2", "", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-join-btn"' in response.content

    def test_detail_shows_manage_button_for_admin(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d3", password="pass")
        team = self.service.create_team(
            admin, "Admin Team D3", "", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(admin)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-manage-btn"' in response.content

    def test_detail_shows_leave_button_for_member(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d4", password="pass")
        user = django_user_model.objects.create_user("user_d4", password="pass")
        team = self.service.create_team(
            admin, "Member Team D4", "", "Public", "Auto-approve", "Engineering"
        )
        self.service.add_member(team, user)
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-leave-btn"' in response.content

    def test_detail_hidden_team_404_for_non_member(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d5", password="pass")
        user = django_user_model.objects.create_user("user_d5", password="pass")
        team = self.service.create_team(
            admin, "Hidden Team D5", "", "Hidden", "Invite Only", "Private"
        )
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert response.status_code == 404

    def test_post_join_auto_approve_adds_member(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d6", password="pass")
        user = django_user_model.objects.create_user("user_d6", password="pass")
        team = self.service.create_team(
            admin, "AutoJoin Team D6", "", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(user)
        response = client.post(f"/teams/{team.pk}/", {"action": "join"})
        assert response.status_code == 302
        assert TeamMembership.objects.filter(team=team, user=user).exists()

    def test_post_join_requires_approval_creates_request(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d7", password="pass")
        user = django_user_model.objects.create_user("user_d7", password="pass")
        team = self.service.create_team(
            admin, "ApprovalJoin Team D7", "", "Public", "Requires Approval", "Engineering"
        )
        client.force_login(user)
        response = client.post(f"/teams/{team.pk}/", {"action": "join"})
        assert response.status_code == 302
        assert JoinRequest.objects.filter(team=team, user=user, status="pending").exists()
        assert not TeamMembership.objects.filter(team=team, user=user).exists()

    def test_post_leave_removes_membership(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d8", password="pass")
        user = django_user_model.objects.create_user("user_d8", password="pass")
        team = self.service.create_team(
            admin, "Leave Team D8", "", "Public", "Auto-approve", "Engineering"
        )
        self.service.add_member(team, user)
        client.force_login(user)
        response = client.post(f"/teams/{team.pk}/", {"action": "leave"})
        assert response.status_code == 302
        assert not TeamMembership.objects.filter(team=team, user=user).exists()

    def test_invite_only_team_shows_no_join_button(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d9", password="pass")
        user = django_user_model.objects.create_user("user_d9", password="pass")
        team = self.service.create_team(
            admin, "InviteOnly Team D9", "", "Public", "Invite Only", "Other"
        )
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-join-btn"' not in response.content
        assert b"invitation only" in response.content.lower()

    def test_pending_request_shows_pending_button(self, client, django_user_model):
        admin = django_user_model.objects.create_user("admin_d10", password="pass")
        user = django_user_model.objects.create_user("user_d10", password="pass")
        team = self.service.create_team(
            admin, "Approval Team D10", "", "Public", "Requires Approval", "Engineering"
        )
        self.service.create_join_request(team, user)
        client.force_login(user)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-join-pending-btn"' in response.content
        assert b'data-testid="team-join-btn"' not in response.content
