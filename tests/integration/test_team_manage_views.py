"""Integration tests for team manage view (WP-5 — FOB-TEAMS-MANAGE-*).

Covers access control, tab routing, and all POST actions.
"""
import pytest
from django.contrib.auth.models import User

from methodology.models import Team, TeamMembership, JoinRequest
from methodology.services.team_service import TeamService


@pytest.mark.django_db
class TestTeamManageView:
    def setup_method(self):
        self.service = TeamService()

    def _setup_team(self, django_user_model):
        admin = django_user_model.objects.create_user("mg_admin", password="pass")
        member = django_user_model.objects.create_user("mg_member", password="pass")
        team = self.service.create_team(admin, "Manage Test Team", "desc", "Public", "Requires Approval", "Engineering")
        self.service.add_member(team, member)
        return admin, member, team

    def test_manage_requires_login(self, client, django_user_model):
        admin = django_user_model.objects.create_user("mg_anon_admin", password="pass")
        team = self.service.create_team(admin, "ManageAnon Team", "", "Public", "Auto-approve", "Engineering")
        response = client.get(f"/teams/{team.pk}/manage/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_non_admin_redirected_with_warning(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(member)
        response = client.get(f"/teams/{team.pk}/manage/")
        assert response.status_code == 302
        assert f"/teams/{team.pk}/" in response.url

    def test_admin_can_access_manage_page(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.get(f"/teams/{team.pk}/manage/")
        assert response.status_code == 200
        assert b'data-testid="team-manage-page"' in response.content

    def test_manage_page_has_all_tabs(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.get(f"/teams/{team.pk}/manage/")
        assert b'data-testid="team-tab-members"' in response.content
        assert b'data-testid="team-tab-join-requests"' in response.content
        assert b'data-testid="team-tab-playbooks"' in response.content
        assert b'data-testid="team-settings-tab"' in response.content

    def test_approve_join_request(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        requester = django_user_model.objects.create_user("mg_requester", password="pass")
        jr = self.service.create_join_request(team, requester)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "approve_request",
            "request_id": jr.pk,
        })
        assert response.status_code == 302
        jr.refresh_from_db()
        assert jr.status == "approved"
        assert TeamMembership.objects.filter(team=team, user=requester).exists()

    def test_reject_join_request(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        requester = django_user_model.objects.create_user("mg_requester2", password="pass")
        jr = self.service.create_join_request(team, requester)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "reject_request",
            "request_id": jr.pk,
        })
        assert response.status_code == 302
        jr.refresh_from_db()
        assert jr.status == "rejected"
        assert not TeamMembership.objects.filter(team=team, user=requester).exists()

    def test_remove_member(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "remove_member",
            "user_id": member.pk,
        })
        assert response.status_code == 302
        assert not TeamMembership.objects.filter(team=team, user=member).exists()

    def test_transfer_admin(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "transfer_admin",
            "user_id": member.pk,
        })
        assert response.status_code == 302
        team.refresh_from_db()
        assert team.admin == member

    def test_update_settings(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "save_settings",
            "name": "Updated Team Name",
            "description": "Updated desc",
            "visibility": "Public",
            "join_policy": "Auto-approve",
            "category": "Design",
        })
        assert response.status_code == 302
        team.refresh_from_db()
        assert team.name == "Updated Team Name"
        assert team.join_policy == "Auto-approve"

    def test_settings_validation_name_required(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        client.force_login(admin)
        response = client.post(f"/teams/{team.pk}/manage/", {
            "action": "save_settings",
            "name": "",
            "description": "desc",
            "visibility": "Public",
            "join_policy": "Auto-approve",
            "category": "Engineering",
        })
        assert response.status_code == 200
        assert b"required" in response.content.lower() or b"Team name" in response.content

    def test_join_requests_tab_shows_pending(self, client, django_user_model):
        admin, member, team = self._setup_team(django_user_model)
        requester = django_user_model.objects.create_user("mg_r3", password="pass")
        self.service.create_join_request(team, requester)
        client.force_login(admin)
        response = client.get(f"/teams/{team.pk}/manage/?tab=join-requests")
        assert response.status_code == 200
        assert b"mg_r3" in response.content
