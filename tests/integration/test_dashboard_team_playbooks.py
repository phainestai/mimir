"""
Integration test for team playbooks display in dashboard.

Tests that team playbooks are properly displayed in the dashboard's
"My Playbooks" section.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from methodology.models import Playbook, Team, TeamMembership, TeamPlaybook

User = get_user_model()


@pytest.mark.django_db
class TestDashboardTeamPlaybooks:
    """Test that team playbooks appear in the dashboard."""

    def test_team_playbooks_appear_in_dashboard(self):
        """
        Team playbooks should appear in the dashboard's My Playbooks section.
        
        Bug: Dashboard only showed owned playbooks, not team playbooks.
        This caused an empty state for users who had no owned playbooks
        but did have access to team playbooks.
        """
        # Setup: Create owner and team member users
        owner = User.objects.create_user(username="owner", password="pass")
        member = User.objects.create_user(username="member", password="pass")

        # Create a team with owner as admin
        team = Team.objects.create(
            name="Test Team",
            admin=owner,
            visibility="Public",
            join_policy="Auto-approve",
        )

        # Add member to team
        TeamMembership.objects.create(team=team, user=member, role="member")

        # Create a released playbook owned by admin
        playbook = Playbook.objects.create(
            name="Shared Team Playbook",
            description="Playbook shared with team",
            author=owner,
            version="1.0",
            status="released",
            visibility="public",
            source="owned",
            category="development",
        )

        # Share playbook with team
        TeamPlaybook.objects.create(team=team, playbook=playbook)

        # Test: Member should see the playbook in their dashboard
        client = Client()
        client.login(username="member", password="pass")
        response = client.get("/dashboard/")

        assert response.status_code == 200
        
        # Check that playbook appears in the response
        assert "Shared Team Playbook" in response.content.decode()
        
        # Check that recent_playbooks context includes the team playbook
        assert "recent_playbooks" in response.context
        recent_playbooks = response.context["recent_playbooks"]
        assert len(recent_playbooks) == 1
        assert recent_playbooks[0].name == "Shared Team Playbook"
        
        # Check that playbook_count reflects accessible playbooks
        assert response.context["playbook_count"] == 1

    def test_dashboard_shows_combined_playbooks(self):
        """
        Dashboard should show owned + public + team playbooks combined.
        """
        # Setup: Create users
        owner1 = User.objects.create_user(username="owner1", password="pass")
        owner2 = User.objects.create_user(username="owner2", password="pass")
        member = User.objects.create_user(username="member", password="pass")

        # Create a team
        team = Team.objects.create(
            name="Test Team",
            admin=owner1,
            visibility="Public",
            join_policy="Auto-approve",
        )
        TeamMembership.objects.create(team=team, user=member, role="member")

        # Create owned playbook
        owned_pb = Playbook.objects.create(
            name="My Own Playbook",
            description="Owned by member",
            author=member,
            version="0.1",
            status="draft",
            visibility="private",
            source="owned",
            category="development",
        )

        # Create public playbook by another user
        public_pb = Playbook.objects.create(
            name="Public Playbook",
            description="Public by owner2",
            author=owner2,
            version="1.0",
            status="released",
            visibility="public",
            source="owned",
            category="development",
        )

        # Create team playbook
        team_pb = Playbook.objects.create(
            name="Team Playbook",
            description="Shared with team",
            author=owner1,
            version="1.0",
            status="released",
            visibility="public",
            source="owned",
            category="development",
        )
        TeamPlaybook.objects.create(team=team, playbook=team_pb)

        # Test: Member should see all three types
        client = Client()
        client.login(username="member", password="pass")
        response = client.get("/dashboard/")

        assert response.status_code == 200
        
        # Check all three playbooks appear
        content = response.content.decode()
        assert "My Own Playbook" in content
        assert "Public Playbook" in content
        assert "Team Playbook" in content
        
        # Check total count
        assert response.context["playbook_count"] == 3
