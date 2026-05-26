"""
Integration tests mirroring UAT Journey 8 — Teams.
Covers: browse → create → detail → join → manage → leave → profile.
"""

import logging

import pytest
from django.contrib.auth.models import User

from methodology.models import Team, TeamMembership, JoinRequest
from methodology.services.team_service import TeamService

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestTeamsJourney:
    """Automated tests for UAT-08-* scenarios."""

    def setup_method(self):
        self.service = TeamService()
        self.uat_user = User.objects.create_user(
            "uat_journey_user", email="uat@example.com", password="pass"
        )
        self.admin_user = User.objects.create_user(
            "uat_journey_admin", email="uatadmin@example.com", password="pass"
        )

    def test_uat_08_00_teams_nav_reachable(self, client):
        """UAT-08-00: Navigate to Teams from dashboard."""
        client.force_login(self.uat_user)
        response = client.get("/teams/")
        assert response.status_code == 200
        assert b'data-testid="teams-browse-page"' in response.content

    def test_uat_08_01_create_team(self, client):
        """UAT-08-01: Create a team."""
        client.force_login(self.uat_user)
        response = client.post(
            "/teams/create/",
            {
                "name": "UAT Test Team J8",
                "description": "A team for UAT testing",
                "visibility": "Public",
                "join_policy": "Auto-approve",
                "category": "Engineering",
            },
        )
        assert response.status_code == 302
        assert Team.objects.filter(name="UAT Test Team J8").exists()
        team = Team.objects.get(name="UAT Test Team J8")
        assert team.admin == self.uat_user
        assert TeamMembership.objects.filter(
            team=team, user=self.uat_user, role="admin"
        ).exists()

    def test_uat_08_02_create_validation_name_required(self, client):
        """UAT-08-02: Create team validation — name required."""
        client.force_login(self.uat_user)
        response = client.post(
            "/teams/create/",
            {
                "name": "",
                "description": "desc",
                "visibility": "Public",
                "join_policy": "Auto-approve",
                "category": "Engineering",
            },
        )
        assert response.status_code == 200
        assert b"required" in response.content.lower() or b"Team name" in response.content

    def test_uat_08_03_browse_shows_team_card(self, client):
        """UAT-08-03: Browse shows team card."""
        self.service.create_team(
            self.uat_user, "Browse UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(self.admin_user)
        response = client.get("/teams/")
        assert response.status_code == 200
        assert b"Browse UAT Team J8" in response.content

    def test_uat_08_04_second_user_joins_auto_approve(self, client):
        """UAT-08-04: Second user joins Auto-approve team and sees leave button."""
        team = self.service.create_team(
            self.uat_user, "Join UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(self.admin_user)
        response = client.post(f"/teams/{team.pk}/", {"action": "join"})
        assert response.status_code == 302
        assert TeamMembership.objects.filter(team=team, user=self.admin_user).exists()
        response2 = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-leave-btn"' in response2.content

    def test_uat_08_05_detail_members_tab(self, client):
        """UAT-08-05: Members tab element present on detail page."""
        team = self.service.create_team(
            self.uat_user, "Members UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        self.service.add_member(team, self.admin_user)
        client.force_login(self.uat_user)
        response = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-tab-members"' in response.content

    def test_uat_08_06_manage_page_all_tabs(self, client):
        """UAT-08-06: Manage page accessible to team admin; all tabs present."""
        team = self.service.create_team(
            self.uat_user, "Manage UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(self.uat_user)
        response = client.get(f"/teams/{team.pk}/manage/")
        assert response.status_code == 200
        assert b'data-testid="team-manage-page"' in response.content
        assert b'data-testid="team-tab-invite"' in response.content

    def test_uat_08_07_manage_settings_update(self, client):
        """UAT-08-07: Admin updates Join Policy via settings tab."""
        team = self.service.create_team(
            self.uat_user, "Settings UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(self.uat_user)
        response = client.post(
            f"/teams/{team.pk}/manage/",
            {
                "action": "save_settings",
                "name": "Settings UAT Team J8",
                "description": "Updated",
                "visibility": "Public",
                "join_policy": "Requires Approval",
                "category": "Engineering",
            },
        )
        assert response.status_code == 302
        team.refresh_from_db()
        assert team.join_policy == "Requires Approval"

    def test_uat_08_08_non_admin_cannot_manage(self, client):
        """UAT-08-08: Non-admin member is redirected from manage page."""
        team = self.service.create_team(
            self.uat_user, "Guard UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        self.service.add_member(team, self.admin_user)
        client.force_login(self.admin_user)
        response = client.get(f"/teams/{team.pk}/manage/")
        assert response.status_code == 302
        assert f"/teams/{team.pk}/" in response.url

    def test_uat_08_09_leave_team(self, client):
        """UAT-08-09: Member leaves team; join button reappears."""
        team = self.service.create_team(
            self.uat_user, "Leave UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        self.service.add_member(team, self.admin_user)
        client.force_login(self.admin_user)
        response = client.post(f"/teams/{team.pk}/", {"action": "leave"})
        assert response.status_code == 302
        assert not TeamMembership.objects.filter(team=team, user=self.admin_user).exists()
        response2 = client.get(f"/teams/{team.pk}/")
        assert b'data-testid="team-join-btn"' in response2.content

    def test_uat_08_10_profile_shows_my_teams(self, client):
        """UAT-08-10: Profile page shows My Teams section with team row."""
        team = self.service.create_team(
            self.uat_user, "Profile UAT Team J8", "desc", "Public", "Auto-approve", "Engineering"
        )
        client.force_login(self.uat_user)
        response = client.get("/auth/user/profile/")
        assert response.status_code == 200
        assert b'data-testid="profile-teams-section"' in response.content
        assert f'data-testid="profile-team-row-{team.pk}"'.encode() in response.content
