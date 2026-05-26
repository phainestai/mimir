"""Business logic for Team operations.

Shared by Django views and MCP tool wrappers.
Handles team CRUD, membership management, join requests, and playbook access.
"""

from __future__ import annotations

import logging

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.http import Http404

from methodology.models import JoinRequest, Playbook, Team, TeamMembership, TeamPlaybook

logger = logging.getLogger(__name__)


class TeamService:
    """Central service for all team-related business logic.

    All methods are shared between Django views and MCP tools.
    No email sending, no MCP-specific logic.
    """

    # ------------------------------------------------------------------
    # Team CRUD
    # ------------------------------------------------------------------

    def create_team(
        self,
        user,
        name: str,
        description: str,
        visibility: str,
        join_policy: str,
        category: str,
    ) -> Team:
        """Create a team; creator becomes admin and first member.

        :param user: User creating the team.
        :param name: Unique team name.
        :param description: Optional description.
        :param visibility: 'Public' or 'Hidden'.
        :param join_policy: Join policy string.
        :param category: Team category string.
        :returns: Newly created Team instance.
        """
        logger.info(
            "create_team: user=%s name=%r visibility=%s join_policy=%s",
            user,
            name,
            visibility,
            join_policy,
        )
        with transaction.atomic():
            team = Team.objects.create(
                name=name,
                description=description,
                visibility=visibility,
                join_policy=join_policy,
                category=category,
                admin=user,
            )
            TeamMembership.objects.create(team=team, user=user, role=TeamMembership.ROLE_ADMIN)
            logger.info("create_team: team pk=%s created; admin membership set", team.pk)
        return team

    def update_team(self, team: Team, actor, **fields) -> Team:
        """Update team fields. Actor must be team admin.

        :param team: Team instance to update.
        :param actor: User requesting the update.
        :param fields: Keyword arguments mapping field names to new values.
        :returns: Updated Team instance.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info("update_team: actor=%s team=%s fields=%s", actor, team, list(fields))
        self._require_admin(team, actor)
        for field, value in fields.items():
            setattr(team, field, value)
        team.save()
        logger.info("update_team: team pk=%s updated successfully", team.pk)
        return team

    def delete_team(self, team: Team, actor) -> None:
        """Delete a team. Actor must be team admin.

        :param team: Team instance to delete.
        :param actor: User requesting deletion.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info("delete_team: actor=%s team=%s pk=%s", actor, team, team.pk)
        self._require_admin(team, actor)
        team.delete()
        logger.info("delete_team: team pk deleted successfully")

    # ------------------------------------------------------------------
    # Discovery / visibility
    # ------------------------------------------------------------------

    def get_teams_visible_to(self, user) -> QuerySet:
        """Return teams visible to the given user.

        Public teams are always included. Hidden teams are included only
        when the user is a member.

        :param user: User whose visibility scope to apply.
        :returns: Filtered QuerySet of Team objects.
        """
        logger.info("get_teams_visible_to: user=%s", user)
        qs = Team.objects.filter(
            Q(visibility=Team.VISIBILITY_PUBLIC)
            | Q(memberships__user=user)
        ).distinct()
        logger.info("get_teams_visible_to: returning %s teams", qs.count())
        return qs

    def get_team_or_404(self, pk: int, user) -> Team:
        """Return team by pk, applying visibility rules.

        :param pk: Primary key of the team.
        :param user: User requesting access.
        :returns: Team instance.
        :raises Http404: If team does not exist or is hidden and user is not a member.
        """
        logger.info("get_team_or_404: pk=%s user=%s", pk, user)
        try:
            team = Team.objects.get(pk=pk)
        except Team.DoesNotExist:
            logger.warning("get_team_or_404: pk=%s not found", pk)
            raise Http404
        if team.visibility == Team.VISIBILITY_HIDDEN and not self._is_member(team, user):
            logger.warning(
                "get_team_or_404: user=%s denied access to hidden team=%s", user, team
            )
            raise Http404
        logger.info("get_team_or_404: returning team=%s", team)
        return team

    # ------------------------------------------------------------------
    # Membership
    # ------------------------------------------------------------------

    def add_member(self, team: Team, user, role: str = "member") -> TeamMembership:
        """Add a user to the team (idempotent).

        :param team: Target team.
        :param user: User to add.
        :param role: 'admin' or 'member'. Defaults to 'member'.
        :returns: TeamMembership instance (new or existing).
        """
        logger.info("add_member: team=%s user=%s role=%s", team, user, role)
        membership, created = TeamMembership.objects.get_or_create(
            team=team, user=user, defaults={"role": role}
        )
        if created:
            logger.info("add_member: new membership pk=%s created", membership.pk)
        else:
            logger.info("add_member: membership pk=%s already exists (idempotent)", membership.pk)
        return membership

    def remove_member(self, team: Team, actor, target_user) -> None:
        """Remove a member from the team. Actor must be team admin.

        :param team: Target team.
        :param actor: User requesting the removal.
        :param target_user: User to remove.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info("remove_member: actor=%s removing user=%s from team=%s", actor, target_user, team)
        self._require_admin(team, actor)
        TeamMembership.objects.filter(team=team, user=target_user).delete()
        logger.info("remove_member: user=%s removed from team=%s", target_user, team)

    def transfer_admin(self, team: Team, actor, new_admin) -> None:
        """Transfer admin role to another member.

        :param team: Target team.
        :param actor: Current admin initiating the transfer.
        :param new_admin: Member who will become the new admin.
        :raises PermissionDenied: If actor is not the current admin.
        :raises ValidationError: If new_admin is not a member.
        """
        logger.info("transfer_admin: actor=%s new_admin=%s team=%s", actor, new_admin, team)
        self._require_admin(team, actor)
        if not self._is_member(team, new_admin):
            raise ValidationError(
                f"{new_admin} is not a member of '{team.name}'."
            )
        with transaction.atomic():
            TeamMembership.objects.filter(team=team, user=new_admin).update(role=TeamMembership.ROLE_ADMIN)
            TeamMembership.objects.filter(team=team, user=actor).update(role=TeamMembership.ROLE_MEMBER)
            team.admin = new_admin
            team.save(update_fields=["admin"])
        logger.info("transfer_admin: team=%s admin transferred to user=%s", team, new_admin)

    def leave_team(self, team: Team, user) -> None:
        """Remove user from team. Raises error if user is the only admin.

        :param team: Team to leave.
        :param user: User leaving.
        :raises ValidationError: If user is the sole admin.
        """
        logger.info("leave_team: user=%s team=%s", user, team)
        admin_count = TeamMembership.objects.filter(team=team, role=TeamMembership.ROLE_ADMIN).count()
        is_admin = self._is_admin(team, user)
        if is_admin and admin_count == 1:
            raise ValidationError(
                f"You are the admin of '{team.name}'. "
                "Transfer admin rights to another member before leaving."
            )
        TeamMembership.objects.filter(team=team, user=user).delete()
        logger.info("leave_team: user=%s left team=%s", user, team)

    def get_member_role(self, team: Team, user) -> str | None:
        """Return the user's role in the team, or None if not a member.

        :param team: Target team.
        :param user: User to check.
        :returns: 'admin', 'member', or None.
        """
        membership = TeamMembership.objects.filter(team=team, user=user).first()
        role = membership.role if membership else None
        logger.info("get_member_role: team=%s user=%s role=%s", team, user, role)
        return role

    def get_user_teams(self, user) -> QuerySet:
        """Return all teams where user has a membership.

        :param user: User whose teams to retrieve.
        :returns: QuerySet of Team objects.
        """
        logger.info("get_user_teams: user=%s", user)
        return Team.objects.filter(memberships__user=user).distinct()

    # ------------------------------------------------------------------
    # Join requests
    # ------------------------------------------------------------------

    def get_pending_join_request(self, team: Team, user) -> JoinRequest | None:
        """Return pending JoinRequest for (team, user), or None.

        :param team: Target team.
        :param user: Requesting user.
        :returns: JoinRequest or None.
        """
        return JoinRequest.objects.filter(
            team=team, user=user, status=JoinRequest.STATUS_PENDING
        ).first()

    def create_join_request(self, team: Team, user) -> JoinRequest:
        """Create a pending join request.

        :param team: Target team.
        :param user: Requesting user.
        :returns: New JoinRequest.
        :raises ValidationError: If a pending request already exists.
        """
        logger.info("create_join_request: user=%s team=%s", user, team)
        if self.get_pending_join_request(team, user) is not None:
            raise ValidationError(
                f"A pending join request for '{team.name}' already exists."
            )
        jr = JoinRequest.objects.create(team=team, user=user)
        logger.info("create_join_request: created JoinRequest pk=%s", jr.pk)
        return jr

    def approve_join_request(self, join_request: JoinRequest, actor) -> TeamMembership:
        """Approve join request and create membership.

        :param join_request: The request to approve.
        :param actor: Admin approving the request.
        :returns: New TeamMembership.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info(
            "approve_join_request: actor=%s request pk=%s team=%s",
            actor,
            join_request.pk,
            join_request.team,
        )
        self._require_admin(join_request.team, actor)
        with transaction.atomic():
            join_request.status = JoinRequest.STATUS_APPROVED
            join_request.save(update_fields=["status"])
            membership = self.add_member(join_request.team, join_request.user, role=TeamMembership.ROLE_MEMBER)
        logger.info("approve_join_request: request pk=%s approved; membership pk=%s", join_request.pk, membership.pk)
        return membership

    def reject_join_request(self, join_request: JoinRequest, actor) -> None:
        """Reject join request.

        :param join_request: The request to reject.
        :param actor: Admin rejecting the request.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info(
            "reject_join_request: actor=%s request pk=%s team=%s",
            actor,
            join_request.pk,
            join_request.team,
        )
        self._require_admin(join_request.team, actor)
        join_request.status = JoinRequest.STATUS_REJECTED
        join_request.save(update_fields=["status"])
        logger.info("reject_join_request: request pk=%s rejected", join_request.pk)

    # ------------------------------------------------------------------
    # Team playbooks
    # ------------------------------------------------------------------

    def get_team_playbooks(self, team: Team) -> QuerySet:
        """Return all Playbook objects linked to the team.

        :param team: Target team.
        :returns: QuerySet of Playbook objects.
        """
        logger.info("get_team_playbooks: team=%s", team)
        return Playbook.objects.filter(team_playbooks__team=team)

    def add_playbook_to_team(self, team: Team, playbook, actor) -> TeamPlaybook:
        """Add a released playbook to the team.

        :param team: Target team.
        :param playbook: Playbook to add.
        :param actor: User adding the playbook.
        :returns: TeamPlaybook join record.
        :raises ValidationError: If playbook is not released.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info("add_playbook_to_team: actor=%s team=%s playbook=%s", actor, team, playbook)
        self._require_admin(team, actor)
        if playbook.status != "released":
            raise ValidationError(
                f"Only released playbooks can be added to a team. "
                f"'{playbook.name}' has status '{playbook.status}'."
            )
        tp, created = TeamPlaybook.objects.get_or_create(
            team=team, playbook=playbook, defaults={"added_by": actor}
        )
        logger.info("add_playbook_to_team: TeamPlaybook pk=%s created=%s", tp.pk, created)
        return tp

    def remove_playbook_from_team(self, team: Team, playbook, actor) -> None:
        """Remove a playbook from the team.

        :param team: Target team.
        :param playbook: Playbook to remove.
        :param actor: User requesting removal.
        :raises PermissionDenied: If actor is not the team admin.
        """
        logger.info("remove_playbook_from_team: actor=%s team=%s playbook=%s", actor, team, playbook)
        self._require_admin(team, actor)
        TeamPlaybook.objects.filter(team=team, playbook=playbook).delete()
        logger.info("remove_playbook_from_team: playbook=%s removed from team=%s", playbook, team)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_admin(self, team: Team, user) -> bool:
        """Return True if user has the admin role in team.

        :param team: Target team.
        :param user: User to check.
        :returns: True if user is an admin member.
        """
        return TeamMembership.objects.filter(
            team=team, user=user, role=TeamMembership.ROLE_ADMIN
        ).exists()

    def _is_member(self, team: Team, user) -> bool:
        """Return True if user has any membership in team.

        :param team: Target team.
        :param user: User to check.
        :returns: True if user is a member.
        """
        return TeamMembership.objects.filter(team=team, user=user).exists()

    def _require_admin(self, team: Team, actor) -> None:
        """Raise PermissionDenied if actor is not team admin.

        :param team: Target team.
        :param actor: Actor to check.
        :raises PermissionDenied: If actor is not an admin member.
        """
        if not self._is_admin(team, actor):
            logger.warning(
                "_require_admin: actor=%s is not admin of team=%s — raising PermissionDenied",
                actor,
                team,
            )
            raise PermissionDenied(f"{actor} is not an admin of team '{team.name}'.")
