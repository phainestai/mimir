"""
Unit tests for TeamService.

Covers team CRUD, membership management, join requests, and playbook operations.
All tests use real database objects — no mocking per project convention.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404

from methodology.models import JoinRequest, Playbook, Team, TeamMembership, TeamPlaybook
from methodology.services.team_service import TeamService

User = get_user_model()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def service():
    """Return a TeamService instance."""
    return TeamService()


@pytest.fixture
def admin_user(db):
    """Create an admin/owner user."""
    return User.objects.create_user(username="ts_admin", password="testpass123")


@pytest.fixture
def member_user(db):
    """Create a second user for membership tests."""
    return User.objects.create_user(username="ts_member", password="testpass123")


@pytest.fixture
def other_user(db):
    """Create a third unrelated user."""
    return User.objects.create_user(username="ts_other", password="testpass123")


@pytest.fixture
def team(admin_user):
    """Create a team with admin_user as admin (bypassing service to isolate tests)."""
    t = Team.objects.create(
        name="Alpha Team",
        description="Test team",
        visibility=Team.VISIBILITY_PUBLIC,
        join_policy=Team.JOIN_POLICY_AUTO,
        category="Engineering",
        admin=admin_user,
    )
    TeamMembership.objects.create(team=t, user=admin_user, role=TeamMembership.ROLE_ADMIN)
    return t


@pytest.fixture
def released_playbook(admin_user):
    """Create a released playbook."""
    return Playbook.objects.create(
        name="Released PB",
        description="A released playbook",
        category="development",
        status="released",
        source="owned",
        author=admin_user,
    )


@pytest.fixture
def draft_playbook(admin_user):
    """Create a draft playbook."""
    return Playbook.objects.create(
        name="Draft PB",
        description="A draft playbook",
        category="development",
        status="draft",
        source="owned",
        author=admin_user,
    )


# ---------------------------------------------------------------------------
# create_team
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateTeam:
    """Tests for TeamService.create_team()."""

    def test_create_team_returns_team_with_admin_membership(self, service, admin_user):
        """create_team should return a persisted Team instance."""
        team = service.create_team(
            user=admin_user,
            name="New Team",
            description="Desc",
            visibility=Team.VISIBILITY_PUBLIC,
            join_policy=Team.JOIN_POLICY_AUTO,
            category="Engineering",
        )
        assert team.pk is not None
        assert team.name == "New Team"
        assert team.admin == admin_user

    def test_create_team_creator_is_admin_member(self, service, admin_user):
        """Creator should be added as a membership with role=admin."""
        team = service.create_team(
            user=admin_user,
            name="Creator Team",
            description="",
            visibility=Team.VISIBILITY_PUBLIC,
            join_policy=Team.JOIN_POLICY_AUTO,
            category="Engineering",
        )
        membership = TeamMembership.objects.get(team=team, user=admin_user)
        assert membership.role == TeamMembership.ROLE_ADMIN


# ---------------------------------------------------------------------------
# update_team
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUpdateTeam:
    """Tests for TeamService.update_team()."""

    def test_update_team_by_admin_succeeds(self, service, team, admin_user):
        """Admin can update team fields."""
        updated = service.update_team(team, admin_user, name="Updated Name")
        assert updated.name == "Updated Name"

    def test_update_team_by_non_admin_raises_permission_denied(
        self, service, team, other_user
    ):
        """Non-admin cannot update team fields."""
        with pytest.raises(PermissionDenied):
            service.update_team(team, other_user, name="Hack")


# ---------------------------------------------------------------------------
# delete_team
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestDeleteTeam:
    """Tests for TeamService.delete_team()."""

    def test_delete_team_by_admin_succeeds(self, service, team, admin_user):
        """Admin can delete a team."""
        team_pk = team.pk
        service.delete_team(team, admin_user)
        assert not Team.objects.filter(pk=team_pk).exists()

    def test_delete_team_by_non_admin_raises_permission_denied(
        self, service, team, other_user
    ):
        """Non-admin cannot delete a team."""
        with pytest.raises(PermissionDenied):
            service.delete_team(team, other_user)


# ---------------------------------------------------------------------------
# get_teams_visible_to
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetTeamsVisibleTo:
    """Tests for TeamService.get_teams_visible_to()."""

    def test_get_teams_visible_to_includes_public(self, service, team, other_user):
        """Public teams are always visible."""
        result = service.get_teams_visible_to(other_user)
        assert team in result

    def test_get_teams_visible_to_includes_member_hidden(
        self, service, admin_user, member_user
    ):
        """Hidden teams are visible to their members."""
        hidden = Team.objects.create(
            name="Hidden Team",
            visibility=Team.VISIBILITY_HIDDEN,
            admin=admin_user,
        )
        TeamMembership.objects.create(team=hidden, user=member_user, role=TeamMembership.ROLE_MEMBER)
        result = service.get_teams_visible_to(member_user)
        assert hidden in result

    def test_get_teams_visible_to_excludes_non_member_hidden(
        self, service, admin_user, other_user
    ):
        """Hidden teams are not visible to non-members."""
        hidden = Team.objects.create(
            name="Invisible Team",
            visibility=Team.VISIBILITY_HIDDEN,
            admin=admin_user,
        )
        result = service.get_teams_visible_to(other_user)
        assert hidden not in result


# ---------------------------------------------------------------------------
# get_team_or_404
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetTeamOr404:
    """Tests for TeamService.get_team_or_404()."""

    def test_get_team_or_404_returns_team_for_public(self, service, team, other_user):
        """Public team is accessible by anyone."""
        result = service.get_team_or_404(team.pk, other_user)
        assert result.pk == team.pk

    def test_get_team_or_404_raises_404_for_hidden_non_member(
        self, service, admin_user, other_user
    ):
        """Hidden team raises Http404 for non-members."""
        hidden = Team.objects.create(
            name="Secret Team",
            visibility=Team.VISIBILITY_HIDDEN,
            admin=admin_user,
        )
        with pytest.raises(Http404):
            service.get_team_or_404(hidden.pk, other_user)


# ---------------------------------------------------------------------------
# add_member
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAddMember:
    """Tests for TeamService.add_member()."""

    def test_add_member_creates_membership(self, service, team, member_user):
        """add_member creates a new TeamMembership."""
        membership = service.add_member(team, member_user)
        assert membership.pk is not None
        assert membership.user == member_user
        assert membership.team == team

    def test_add_member_idempotent_if_already_member(self, service, team, member_user):
        """add_member returns existing membership if user is already a member."""
        first = service.add_member(team, member_user)
        second = service.add_member(team, member_user)
        assert first.pk == second.pk


# ---------------------------------------------------------------------------
# remove_member
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRemoveMember:
    """Tests for TeamService.remove_member()."""

    def test_remove_member_by_admin_succeeds(self, service, team, admin_user, member_user):
        """Admin can remove a member."""
        TeamMembership.objects.create(team=team, user=member_user, role=TeamMembership.ROLE_MEMBER)
        service.remove_member(team, admin_user, member_user)
        assert not TeamMembership.objects.filter(team=team, user=member_user).exists()

    def test_remove_member_by_non_admin_raises(self, service, team, member_user, other_user):
        """Non-admin cannot remove members."""
        TeamMembership.objects.create(team=team, user=member_user, role=TeamMembership.ROLE_MEMBER)
        TeamMembership.objects.create(team=team, user=other_user, role=TeamMembership.ROLE_MEMBER)
        with pytest.raises(PermissionDenied):
            service.remove_member(team, other_user, member_user)


# ---------------------------------------------------------------------------
# transfer_admin
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTransferAdmin:
    """Tests for TeamService.transfer_admin()."""

    def test_transfer_admin_changes_admin(self, service, team, admin_user, member_user):
        """Admin can transfer their role to a member."""
        TeamMembership.objects.create(team=team, user=member_user, role=TeamMembership.ROLE_MEMBER)
        service.transfer_admin(team, admin_user, member_user)

        team.refresh_from_db()
        assert team.admin == member_user
        new_admin_m = TeamMembership.objects.get(team=team, user=member_user)
        old_admin_m = TeamMembership.objects.get(team=team, user=admin_user)
        assert new_admin_m.role == TeamMembership.ROLE_ADMIN
        assert old_admin_m.role == TeamMembership.ROLE_MEMBER

    def test_transfer_admin_non_member_raises_validation_error(
        self, service, team, admin_user, other_user
    ):
        """Transferring admin to a non-member raises ValidationError."""
        with pytest.raises(ValidationError):
            service.transfer_admin(team, admin_user, other_user)


# ---------------------------------------------------------------------------
# leave_team
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestLeaveTeam:
    """Tests for TeamService.leave_team()."""

    def test_leave_team_removes_membership(self, service, team, admin_user, member_user):
        """Member can leave a team."""
        TeamMembership.objects.create(team=team, user=member_user, role=TeamMembership.ROLE_MEMBER)
        service.leave_team(team, member_user)
        assert not TeamMembership.objects.filter(team=team, user=member_user).exists()

    def test_leave_team_only_admin_raises_validation_error(
        self, service, team, admin_user
    ):
        """Only admin cannot leave — must transfer first."""
        with pytest.raises(ValidationError, match="admin"):
            service.leave_team(team, admin_user)


# ---------------------------------------------------------------------------
# get_member_role
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetMemberRole:
    """Tests for TeamService.get_member_role()."""

    def test_get_member_role_returns_correct_role(self, service, team, admin_user, member_user):
        """Returns 'admin' or 'member' based on membership role."""
        TeamMembership.objects.create(team=team, user=member_user, role=TeamMembership.ROLE_MEMBER)
        assert service.get_member_role(team, admin_user) == TeamMembership.ROLE_ADMIN
        assert service.get_member_role(team, member_user) == TeamMembership.ROLE_MEMBER

    def test_get_member_role_returns_none_for_non_member(
        self, service, team, other_user
    ):
        """Returns None for a user who is not a member."""
        assert service.get_member_role(team, other_user) is None


# ---------------------------------------------------------------------------
# get_user_teams
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetUserTeams:
    """Tests for TeamService.get_user_teams()."""

    def test_get_user_teams_returns_teams_for_user(self, service, team, admin_user):
        """Returns teams where user has a membership."""
        result = service.get_user_teams(admin_user)
        assert team in result


# ---------------------------------------------------------------------------
# join requests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestJoinRequests:
    """Tests for TeamService join request operations."""

    def test_create_join_request_creates_pending(self, service, team, member_user):
        """create_join_request creates a pending JoinRequest."""
        jr = service.create_join_request(team, member_user)
        assert jr.pk is not None
        assert jr.status == JoinRequest.STATUS_PENDING
        assert jr.team == team
        assert jr.user == member_user

    def test_create_join_request_duplicate_raises_validation_error(
        self, service, team, member_user
    ):
        """Creating a second pending request raises ValidationError."""
        service.create_join_request(team, member_user)
        with pytest.raises(ValidationError):
            service.create_join_request(team, member_user)

    def test_approve_join_request_creates_membership(
        self, service, team, admin_user, member_user
    ):
        """Approving a join request creates a TeamMembership with role=member."""
        jr = JoinRequest.objects.create(team=team, user=member_user)
        membership = service.approve_join_request(jr, admin_user)
        jr.refresh_from_db()
        assert jr.status == JoinRequest.STATUS_APPROVED
        assert membership.user == member_user
        assert membership.role == TeamMembership.ROLE_MEMBER

    def test_reject_join_request_sets_rejected(self, service, team, admin_user, member_user):
        """Rejecting a join request sets status=rejected."""
        jr = JoinRequest.objects.create(team=team, user=member_user)
        service.reject_join_request(jr, admin_user)
        jr.refresh_from_db()
        assert jr.status == JoinRequest.STATUS_REJECTED


# ---------------------------------------------------------------------------
# team playbooks
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTeamPlaybooks:
    """Tests for TeamService team playbook operations."""

    def test_get_team_playbooks_returns_released_playbooks(
        self, service, team, admin_user, released_playbook
    ):
        """get_team_playbooks returns linked Playbook objects."""
        TeamPlaybook.objects.create(team=team, playbook=released_playbook, added_by=admin_user)
        result = service.get_team_playbooks(team)
        assert released_playbook in result

    def test_add_playbook_to_team_draft_raises_validation_error(
        self, service, team, admin_user, draft_playbook
    ):
        """add_playbook_to_team raises ValidationError for non-released playbooks."""
        with pytest.raises(ValidationError):
            service.add_playbook_to_team(team, draft_playbook, admin_user)

    def test_remove_playbook_from_team(
        self, service, team, admin_user, released_playbook
    ):
        """remove_playbook_from_team deletes the TeamPlaybook entry."""
        TeamPlaybook.objects.create(team=team, playbook=released_playbook, added_by=admin_user)
        service.remove_playbook_from_team(team, released_playbook, admin_user)
        assert not TeamPlaybook.objects.filter(team=team, playbook=released_playbook).exists()
