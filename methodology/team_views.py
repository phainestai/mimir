"""Django views for the Teams feature (Act 11 — FOB-TEAMS-*).

Shared between browse (FOB-TEAMS-BROWSE-*) and create (FOB-TEAMS-CREATE-*)
scenarios.  Detail and manage views are stubs for WP-4 and WP-5.
"""

from __future__ import annotations

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import User as UserModel
from django.shortcuts import get_object_or_404, redirect, render

from methodology.models import JoinRequest, Playbook, Team
from methodology.services.team_service import TeamService

logger = logging.getLogger(__name__)

CATEGORIES: list[str] = ["Engineering", "Design", "Research", "Product", "Private", "Other"]
VISIBILITY_CHOICES: list[str] = ["Public", "Hidden"]
JOIN_POLICY_CHOICES: list[str] = ["Auto-approve", "Requires Approval", "Invite Only"]


@login_required
def teams_browse(request):
    """FOB-TEAMS-BROWSE-*: list teams visible to user with search and category filter.

    :param request: Django HTTP request.
    :returns: Rendered browse page.
    """
    logger.info("[teams] browse | user=%s", request.user.username)
    service = TeamService()
    teams = service.get_teams_visible_to(request.user)

    q, category = _extract_browse_filters(request)
    teams = _apply_browse_filters(teams, q, category)

    context = _build_browse_context(teams, q, category)
    return render(request, "teams/browse.html", context)


@login_required
def teams_create(request):
    """FOB-TEAMS-CREATE-*: render create-team form (GET) and handle POST.

    :param request: Django HTTP request.
    :returns: Rendered form or redirect to detail page on success.
    """
    logger.info("[teams] create | method=%s user=%s", request.method, request.user.username)
    if request.method == "POST":
        return _handle_create_post(request)
    return render(request, "teams/create.html", _empty_create_context())


@login_required
def teams_detail(request, pk: int):
    """FOB-TEAMS-VIEW-*: team detail, join, and leave.

    :param request: Django HTTP request.
    :param pk: Team primary key.
    :returns: Rendered detail page or redirect after POST action.
    """
    logger.info(
        "[teams] detail | pk=%s user=%s method=%s",
        pk, request.user.username, request.method,
    )
    service = TeamService()
    team = service.get_team_or_404(pk, request.user)

    if request.method == "POST":
        return _handle_detail_post(request, team, service)

    context = _build_detail_context(request.user, team, service)
    return render(request, "teams/detail.html", context)


def _compute_join_state(team, role: str | None, pending_request) -> str:
    """Determine join_state string from user's relationship to the team.

    :param team: Target Team instance.
    :param role: 'admin', 'member', or None.
    :param pending_request: JoinRequest or None.
    :returns: One of 'manage', 'leave', 'pending', 'invite_only', 'join'.
    """
    if role == "admin":
        return "manage"
    if role == "member":
        return "leave"
    if pending_request:
        return "pending"
    if team.join_policy == Team.JOIN_POLICY_INVITE:
        return "invite_only"
    return "join"


def _build_detail_context(user, team, service: TeamService) -> dict:
    """Build context dict for team detail page.

    :param user: Requesting user.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Context dictionary for the template.
    """
    role = service.get_member_role(team, user)
    pending_request = service.get_pending_join_request(team, user)
    join_state = _compute_join_state(team, role, pending_request)
    playbooks = service.get_team_playbooks(team)
    members = team.memberships.select_related("user").order_by("joined_at")[:25]
    logger.info(
        "[teams] detail context | team=%s join_state=%s members=%d",
        team.name, join_state, team.memberships.count(),
    )
    return {
        "team": team,
        "join_state": join_state,
        "playbooks": playbooks,
        "members": members,
        "member_count": team.memberships.count(),
        "active_page": "teams",
    }


def _handle_detail_post(request, team, service: TeamService):
    """Handle POST actions on team detail page: join or leave.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect response.
    """
    action = request.POST.get("action")
    logger.info(
        "[teams] detail POST | action=%s team=%s user=%s",
        action, team.name, request.user.username,
    )
    if action == "join":
        return _handle_join(request, team, service)
    if action == "leave":
        return _handle_leave(request, team, service)
    return redirect("teams:teams_detail", pk=team.pk)


def _handle_join(request, team, service: TeamService):
    """Handle join action: auto-approve or create join request.

    :param request: Django HTTP request.
    :param team: Team to join.
    :param service: TeamService instance.
    :returns: Redirect to team detail page.
    """
    if team.join_policy == Team.JOIN_POLICY_AUTO:
        service.add_member(team, request.user)
        logger.info("[teams] joined team: %s user=%s", team.name, request.user.username)
        messages.success(request, f"You've joined the {team.name} team.")
    else:
        service.create_join_request(team, request.user)
        logger.info("[teams] join request created: team=%s user=%s", team.name, request.user.username)
        messages.info(
            request,
            f"Your request to join '{team.name}' has been sent. Awaiting approval.",
        )
    return redirect("teams:teams_detail", pk=team.pk)


def _handle_leave(request, team, service: TeamService):
    """Handle leave action with admin guard.

    :param request: Django HTTP request.
    :param team: Team to leave.
    :param service: TeamService instance.
    :returns: Redirect to team detail page.
    """
    try:
        service.leave_team(team, request.user)
        logger.info("[teams] left team: %s user=%s", team.name, request.user.username)
        messages.success(request, f"You have left the {team.name} team.")
    except ValidationError as exc:
        logger.warning(
            "[teams] leave blocked: %s user=%s reason=%s",
            team.name, request.user.username, str(exc),
        )
        messages.warning(request, exc.message)
    return redirect("teams:teams_detail", pk=team.pk)


@login_required
def teams_manage(request, pk: int):
    """FOB-TEAMS-MANAGE-*: admin-only management panel with tab routing.

    :param request: Django HTTP request.
    :param pk: Team primary key.
    :returns: Rendered manage page or redirect.
    """
    logger.info("[teams] manage | pk=%s user=%s method=%s", pk, request.user.username, request.method)
    service = TeamService()
    team = service.get_team_or_404(pk, request.user)

    if service.get_member_role(team, request.user) != "admin":
        logger.warning("[teams] manage access denied: user=%s team=%s", request.user.username, team.name)
        messages.warning(request, "You don't have permission to manage this team.")
        return redirect("teams:teams_detail", pk=pk)

    tab = request.GET.get("tab", "members")

    if request.method == "POST":
        return _handle_manage_post(request, team, service, tab)

    context = _build_manage_context(request.user, team, service, tab)
    return render(request, "teams/manage.html", context)


def _build_manage_context(user, team, service: TeamService, tab: str) -> dict:
    """Build context dict for team manage page.

    :param user: Requesting user.
    :param team: Team instance.
    :param service: TeamService instance.
    :param tab: Active tab name.
    :returns: Context dictionary for the template.
    """
    all_released = Playbook.objects.filter(status="released")
    team_playbook_ids = service.get_team_playbooks(team).values_list("id", flat=True)
    available_playbooks = all_released.exclude(id__in=team_playbook_ids)
    logger.info("[teams] manage context | team=%s tab=%s", team.name, tab)
    return {
        "team": team,
        "members": team.memberships.select_related("user").order_by("joined_at"),
        "join_requests": team.join_requests.filter(status="pending").select_related("user").order_by("requested_at"),
        "join_request_count": team.join_requests.filter(status="pending").count(),
        "playbooks": service.get_team_playbooks(team),
        "available_playbooks": available_playbooks,
        "categories": CATEGORIES,
        "visibility_choices": VISIBILITY_CHOICES,
        "join_policy_choices": JOIN_POLICY_CHOICES,
        "active_tab": tab,
        "active_page": "teams",
        "errors": {},
    }


def _handle_manage_post(request, team, service: TeamService, tab: str):
    """Dispatch POST action to the right handler.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :param tab: Current active tab (for error re-render).
    :returns: HTTP response (redirect or render).
    """
    action = request.POST.get("action")
    logger.info("[teams] manage POST | action=%s team=%s user=%s", action, team.name, request.user.username)
    handlers = {
        "approve_request": _handle_approve_request,
        "reject_request": _handle_reject_request,
        "remove_member": _handle_remove_member,
        "transfer_admin": _handle_transfer_admin,
        "add_playbook": _handle_add_playbook,
        "remove_playbook": _handle_remove_playbook,
        "save_settings": lambda req, t, svc: _handle_save_settings(req, t, svc, tab),
    }
    handler = handlers.get(action)
    if handler:
        return handler(request, team, service)
    logger.warning("[teams] manage unknown action=%s team=%s", action, team.name)
    return redirect("teams:teams_manage", pk=team.pk)


def _handle_approve_request(request, team, service: TeamService):
    """Approve a pending join request and add user as member.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to manage page.
    """
    jr = get_object_or_404(JoinRequest, pk=request.POST.get("request_id"), team=team)
    service.approve_join_request(jr, request.user)
    logger.info("[teams] approved join request pk=%s user=%s team=%s", jr.pk, jr.user.username, team.name)
    messages.success(request, f"{jr.user.username} has been approved.")
    return redirect("teams:teams_manage", pk=team.pk)


def _handle_reject_request(request, team, service: TeamService):
    """Reject a pending join request.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to manage page.
    """
    jr = get_object_or_404(JoinRequest, pk=request.POST.get("request_id"), team=team)
    service.reject_join_request(jr, request.user)
    logger.info("[teams] rejected join request pk=%s user=%s team=%s", jr.pk, jr.user.username, team.name)
    messages.info(request, f"{jr.user.username}'s request has been rejected.")
    return redirect("teams:teams_manage", pk=team.pk)


def _handle_remove_member(request, team, service: TeamService):
    """Remove a member from the team.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to manage page.
    """
    target = get_object_or_404(UserModel, pk=request.POST.get("user_id"))
    service.remove_member(team, request.user, target)
    logger.info("[teams] removed member user=%s from team=%s", target.username, team.name)
    messages.success(request, f"{target.username} has been removed from the team.")
    return redirect("teams:teams_manage", pk=team.pk)


def _handle_transfer_admin(request, team, service: TeamService):
    """Transfer admin rights to another team member.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to team detail page.
    """
    new_admin = get_object_or_404(UserModel, pk=request.POST.get("user_id"))
    service.transfer_admin(team, request.user, new_admin)
    logger.info("[teams] admin transferred to user=%s team=%s", new_admin.username, team.name)
    messages.success(request, f"Admin rights transferred to {new_admin.username}.")
    return redirect("teams:teams_detail", pk=team.pk)


def _handle_add_playbook(request, team, service: TeamService):
    """Add a released playbook to the team.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to manage page (playbooks tab).
    """
    playbook = get_object_or_404(Playbook, pk=request.POST.get("playbook_id"))
    service.add_playbook_to_team(team, playbook, request.user)
    logger.info("[teams] playbook=%s added to team=%s by user=%s", playbook.name, team.name, request.user.username)
    messages.success(request, f"Playbook '{playbook.name}' added to team.")
    return redirect(f"/teams/{team.pk}/manage/?tab=playbooks")


def _handle_remove_playbook(request, team, service: TeamService):
    """Remove a playbook from the team.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :returns: Redirect to manage page (playbooks tab).
    """
    playbook = get_object_or_404(Playbook, pk=request.POST.get("playbook_id"))
    service.remove_playbook_from_team(team, playbook, request.user)
    logger.info("[teams] playbook=%s removed from team=%s by user=%s", playbook.name, team.name, request.user.username)
    messages.success(request, f"Playbook '{playbook.name}' removed from team.")
    return redirect(f"/teams/{team.pk}/manage/?tab=playbooks")


def _handle_save_settings(request, team, service: TeamService, tab: str):
    """Validate and persist team settings changes.

    :param request: Django HTTP request.
    :param team: Team instance.
    :param service: TeamService instance.
    :param tab: Current tab (for re-render on error).
    :returns: Redirect on success; re-rendered page with errors on failure.
    """
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    visibility = request.POST.get("visibility", team.visibility)
    join_policy = request.POST.get("join_policy", team.join_policy)
    category = request.POST.get("category", team.category)

    errors = _validate_team_form(name)
    if errors:
        logger.warning("[teams] settings validation failed: errors=%s team=%s", errors, team.name)
        context = _build_manage_context(request.user, team, service, "settings")
        context["errors"] = errors
        return render(request, "teams/manage.html", context)

    service.update_team(team, request.user, name=name, description=description,
                        visibility=visibility, join_policy=join_policy, category=category)
    logger.info("[teams] settings saved for team=%s by user=%s", team.name, request.user.username)
    messages.success(request, "Team settings saved.")
    return redirect("teams:teams_manage", pk=team.pk)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_browse_filters(request) -> tuple[str, str]:
    """Extract search query and category from GET params.

    :param request: Django HTTP request.
    :returns: Tuple of (query_string, category_string).
    """
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    return q, category


def _apply_browse_filters(teams, q: str, category: str):
    """Apply text search and category filter to teams queryset.

    :param teams: Base queryset of Team objects.
    :param q: Search term (matches name or description).
    :param category: Category string to filter on.
    :returns: Filtered queryset.
    """
    from django.db.models import Q as DjangoQ

    if q:
        teams = teams.filter(
            DjangoQ(name__icontains=q) | DjangoQ(description__icontains=q)
        ).distinct()
        logger.info("[teams] search q=%r results=%d", q, teams.count())
    if category:
        teams = teams.filter(category=category)
        logger.info("[teams] category filter=%r results=%d", category, teams.count())
    return teams


def _build_browse_context(teams, q: str, category: str) -> dict:
    """Build template context for the browse page.

    :param teams: Filtered queryset of Team objects.
    :param q: Active search query string.
    :param category: Active category filter string.
    :returns: Context dictionary for the template.
    """
    return {
        "teams": teams,
        "team_count": teams.count(),
        "categories": CATEGORIES,
        "search_query": q,
        "active_category": category,
        "active_page": "teams",
        "nav_section": "teams",
    }


def _handle_create_post(request):
    """Handle POST for team creation: validate, delegate to TeamService, redirect.

    :param request: Django HTTP request (method must be POST).
    :returns: Redirect on success; rendered form with errors on failure.
    """
    name = request.POST.get("name", "").strip()
    description = request.POST.get("description", "").strip()
    visibility = request.POST.get("visibility", "Public")
    join_policy = request.POST.get("join_policy", "Auto-approve")
    category = request.POST.get("category", "Other")

    logger.info(
        "[teams] create POST | user=%s name=%r visibility=%s",
        request.user.username, name, visibility,
    )

    errors = _validate_team_form(name)
    if errors:
        return _render_create_with_errors(request, errors)

    service = TeamService()
    try:
        team = service.create_team(
            request.user, name, description, visibility, join_policy, category
        )
        logger.info("[teams] created pk=%s name=%r by user=%s", team.pk, name, request.user.username)
        messages.success(request, f"Team '{team.name}' created successfully.")
        return redirect("teams:teams_detail", pk=team.pk)
    except IntegrityError:
        logger.warning("[teams] duplicate name=%r for user=%s", name, request.user.username)
        errors["name"] = "A team with this name already exists."
        return _render_create_with_errors(request, errors)


def _validate_team_form(name: str) -> dict:
    """Validate team creation form fields.

    :param name: Proposed team name.
    :returns: Dict mapping field names to error messages; empty if valid.
    """
    errors: dict = {}
    if not name:
        errors["name"] = "Team name is required."
    elif len(name) > 100:
        errors["name"] = "Team name cannot exceed 100 characters."
    return errors


def _render_create_with_errors(request, errors: dict):
    """Render the create form template with validation errors.

    :param request: Django HTTP request.
    :param errors: Dict of field → error message.
    :returns: Rendered HTTP response with status 200.
    """
    context = {
        **_empty_create_context(),
        "errors": errors,
        "form_data": request.POST,
    }
    return render(request, "teams/create.html", context)


def _empty_create_context() -> dict:
    """Return a default (empty) context dict for the create form.

    :returns: Context dictionary with choice lists and empty errors.
    """
    return {
        "categories": CATEGORIES,
        "visibility_choices": VISIBILITY_CHOICES,
        "join_policy_choices": JOIN_POLICY_CHOICES,
        "errors": {},
        "form_data": {},
        "active_page": "teams",
        "nav_section": "teams",
    }
