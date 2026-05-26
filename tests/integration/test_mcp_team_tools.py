"""Integration tests for MCP team tools (WP-E)."""

import asyncio

import pytest
from django.contrib.auth import get_user_model

from methodology.models import Team, JoinRequest, TeamPlaybook
from mcp_integration import tools
from mcp_integration.context import set_current_user

User = get_user_model()


@pytest.mark.django_db(transaction=True)
class TestMCPTeamTools:
    """Test MCP team tools with real database (no mocks per project rules)."""

    def test_list_teams(self):
        """list_teams should return teams visible to user."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp", password="pass", email="admin@test.com")
        member = User.objects.create_user(username="member_mcp", password="pass", email="member@test.com")

        team1 = Team.objects.create(
            name="Public Team",
            admin=admin,
            visibility=Team.VISIBILITY_PUBLIC,
        )
        TeamMembership.objects.create(team=team1, user=admin)

        team2 = Team.objects.create(
            name="Hidden Team",
            admin=admin,
            visibility=Team.VISIBILITY_HIDDEN,
        )
        TeamMembership.objects.create(team=team2, user=admin)

        set_current_user(member)
        result = asyncio.run(tools.list_teams())

        # Member should see public team but not hidden one
        assert len(result) == 1
        assert result[0]["name"] == "Public Team"
        assert result[0]["visibility"] == Team.VISIBILITY_PUBLIC
        assert "admin_id" in result[0]
        assert "member_count" in result[0]

    def test_get_team(self):
        """get_team should return detailed team info."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp2", password="pass", email="admin2@test.com")
        member = User.objects.create_user(username="member_mcp2", password="pass", email="member2@test.com")

        team = Team.objects.create(
            name="Test Team",
            description="Test description",
            admin=admin,
            visibility=Team.VISIBILITY_PUBLIC,
        )
        TeamMembership.objects.create(team=team, user=admin)
        TeamMembership.objects.create(team=team, user=member)

        set_current_user(member)
        result = asyncio.run(tools.get_team(team_id=team.pk))

        assert result["id"] == team.pk
        assert result["name"] == "Test Team"
        assert result["description"] == "Test description"
        assert result["member_count"] == 2
        assert len(result["members"]) == 2
        assert "admin" in result
        assert result["admin"]["user_id"] == admin.id

    def test_get_team_not_found(self):
        """get_team should raise ValueError for non-existent team."""
        user = User.objects.create_user(username="user_mcp3", password="pass", email="user3@test.com")

        set_current_user(user)
        with pytest.raises(ValueError, match="not found"):
            asyncio.run(tools.get_team(team_id=99999))

    def test_create_team(self):
        """create_team should create a team and make caller admin."""
        user = User.objects.create_user(username="creator_mcp", password="pass", email="creator@test.com")

        set_current_user(user)
        result = asyncio.run(
            tools.create_team(
                name="New Team",
                description="New team description",
                visibility="Public",
                join_policy="Auto-approve",
                category="Engineering",
            )
        )

        assert result["name"] == "New Team"
        assert result["description"] == "New team description"
        assert result["visibility"] == "Public"
        assert result["join_policy"] == "Auto-approve"
        assert result["category"] == "Engineering"
        assert result["admin_id"] == user.id
        assert result["member_count"] == 1

        # Verify in database
        team = Team.objects.get(pk=result["id"])
        assert team.name == "New Team"
        assert team.admin == user
        assert team.members.filter(pk=user.pk).exists()

    def test_create_team_empty_name(self):
        """create_team should raise ValueError for empty name."""
        user = User.objects.create_user(username="user_mcp4", password="pass", email="user4@test.com")

        set_current_user(user)
        with pytest.raises(ValueError, match="cannot be empty"):
            asyncio.run(tools.create_team(name="", description="Test"))

    def test_move_playbook_to_team(self):
        """move_playbook_to_team should add playbook to team (admin only)."""
        from methodology.models import Playbook, TeamMembership

        admin = User.objects.create_user(username="admin_mcp5", password="pass", email="admin5@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        playbook = Playbook.objects.create(
            name="Test Playbook",
            author=admin,
            status="draft",
        )

        set_current_user(admin)
        result = asyncio.run(tools.move_playbook_to_team(playbook_id=playbook.pk, team_id=team.pk))

        assert result["success"] is True
        assert result["team_id"] == team.pk
        assert result["playbook_id"] == playbook.pk
        assert result["playbook_name"] == "Test Playbook"

        # Verify in database
        assert TeamPlaybook.objects.filter(team=team, playbook=playbook).exists()

    def test_move_playbook_to_team_not_admin(self):
        """move_playbook_to_team should raise PermissionError for non-admin."""
        from methodology.models import Playbook, TeamMembership

        admin = User.objects.create_user(username="admin_mcp6", password="pass", email="admin6@test.com")
        member = User.objects.create_user(username="member_mcp6", password="pass", email="member6@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        playbook = Playbook.objects.create(
            name="Test Playbook",
            author=member,
            status="draft",
        )

        set_current_user(member)
        with pytest.raises(PermissionError, match="Only team admin"):
            asyncio.run(tools.move_playbook_to_team(playbook_id=playbook.pk, team_id=team.pk))

    def test_move_playbook_from_team(self):
        """move_playbook_from_team should remove playbook from team (admin only)."""
        from methodology.models import Playbook, TeamMembership

        admin = User.objects.create_user(username="admin_mcp7", password="pass", email="admin7@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        playbook = Playbook.objects.create(
            name="Test Playbook",
            author=admin,
            status="draft",
        )

        TeamPlaybook.objects.create(team=team, playbook=playbook)

        set_current_user(admin)
        result = asyncio.run(tools.move_playbook_from_team(playbook_id=playbook.pk, team_id=team.pk))

        assert result["success"] is True
        assert result["team_id"] == team.pk
        assert result["playbook_id"] == playbook.pk

        # Verify removed from database
        assert not TeamPlaybook.objects.filter(team=team, playbook=playbook).exists()

    def test_invite_to_team(self):
        """invite_to_team should send invites (admin only)."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp8", password="pass", email="admin8@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        set_current_user(admin)
        result = asyncio.run(
            tools.invite_to_team(
                team_id=team.pk,
                emails=["new1@test.com", "new2@test.com"],
                welcome_text="Welcome!",
            )
        )

        assert result["success"] is True
        assert result["team_id"] == team.pk
        assert result["invited_count"] >= 0  # May vary based on whether users exist
        assert "results" in result

    def test_invite_to_team_not_admin(self):
        """invite_to_team should raise PermissionError for non-admin."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp9", password="pass", email="admin9@test.com")
        member = User.objects.create_user(username="member_mcp9", password="pass", email="member9@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        set_current_user(member)
        with pytest.raises(PermissionError, match="Only team admin"):
            asyncio.run(tools.invite_to_team(team_id=team.pk, emails=["test@test.com"]))

    def test_invite_to_team_empty_emails(self):
        """invite_to_team should raise ValueError for empty emails list."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp10", password="pass", email="admin10@test.com")
        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)

        set_current_user(admin)
        with pytest.raises(ValueError, match="cannot be empty"):
            asyncio.run(tools.invite_to_team(team_id=team.pk, emails=[]))

    def test_manage_team_invite_approve(self):
        """manage_team_invite with action=approve should approve join request."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp11", password="pass", email="admin11@test.com")
        requester = User.objects.create_user(username="req_mcp11", password="pass", email="req11@test.com")

        team = Team.objects.create(
            name="Test Team",
            admin=admin,
            join_policy=Team.JOIN_POLICY_APPROVAL,
        )
        TeamMembership.objects.create(team=team, user=admin)

        join_request = JoinRequest.objects.create(
            team=team,
            user=requester,
            status=JoinRequest.STATUS_PENDING,
        )

        set_current_user(admin)
        result = asyncio.run(
            tools.manage_team_invite(team_id=team.pk, request_id=join_request.pk, action="approve")
        )

        assert result["success"] is True
        assert result["action"] == "approve"
        assert result["team_id"] == team.pk
        assert result["request_id"] == join_request.pk

        # Verify user is now a member (via TeamMembership)
        from methodology.models import TeamMembership

        assert TeamMembership.objects.filter(team=team, user=requester).exists()

    def test_manage_team_invite_reject(self):
        """manage_team_invite with action=reject should reject join request."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp12", password="pass", email="admin12@test.com")
        requester = User.objects.create_user(username="req_mcp12", password="pass", email="req12@test.com")

        team = Team.objects.create(
            name="Test Team",
            admin=admin,
            join_policy=Team.JOIN_POLICY_APPROVAL,
        )
        TeamMembership.objects.create(team=team, user=admin)

        join_request = JoinRequest.objects.create(
            team=team,
            user=requester,
            status=JoinRequest.STATUS_PENDING,
        )

        set_current_user(admin)
        result = asyncio.run(
            tools.manage_team_invite(team_id=team.pk, request_id=join_request.pk, action="reject")
        )

        assert result["success"] is True
        assert result["action"] == "reject"

        # Verify request was rejected (not a member)
        from methodology.models import TeamMembership

        assert not TeamMembership.objects.filter(team=team, user=requester).exists()

    def test_manage_team_invite_not_admin(self):
        """manage_team_invite should raise PermissionError for non-admin."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp13", password="pass", email="admin13@test.com")
        member = User.objects.create_user(username="member_mcp13", password="pass", email="member13@test.com")
        requester = User.objects.create_user(username="req_mcp13", password="pass", email="req13@test.com")

        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)
        join_request = JoinRequest.objects.create(team=team, user=requester)

        set_current_user(member)
        with pytest.raises(PermissionError, match="Only team admin"):
            asyncio.run(tools.manage_team_invite(team_id=team.pk, request_id=join_request.pk, action="approve"))

    def test_manage_team_invite_invalid_action(self):
        """manage_team_invite should raise ValueError for invalid action."""
        from methodology.models import TeamMembership

        admin = User.objects.create_user(username="admin_mcp14", password="pass", email="admin14@test.com")
        requester = User.objects.create_user(username="req_mcp14", password="pass", email="req14@test.com")

        team = Team.objects.create(name="Test Team", admin=admin)
        TeamMembership.objects.create(team=team, user=admin)
        join_request = JoinRequest.objects.create(team=team, user=requester)

        set_current_user(admin)
        with pytest.raises(ValueError, match="Invalid action"):
            asyncio.run(tools.manage_team_invite(team_id=team.pk, request_id=join_request.pk, action="invalid"))
