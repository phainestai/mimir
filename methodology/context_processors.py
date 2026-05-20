"""Inject global template variables for methodology nav."""

from __future__ import annotations

import logging

from django.http import HttpRequest

from mimir.versioning import get_deployed_revision

logger = logging.getLogger(__name__)


def app_version(request: HttpRequest) -> dict:
    """
    Expose deployed revision for templates — mirrors Huginn's ``MIMIR_GIT_REVISION`` pattern.

    :param request: Incoming HTTP request (unused; required for context processor signature).
    :returns: Mapping with ``DEPLOYED_REVISION`` (env var or ``"unknown"``).
    """
    deployed = get_deployed_revision()
    logger.debug("Template context DEPLOYED_REVISION=%s path=%s", deployed, getattr(request, "path", ""))
    return {"DEPLOYED_REVISION": deployed}


def primary_nav_section(request: HttpRequest) -> dict:
    """
    Exactly one primary navbar section should appear active.

    Nested URLs like ``/playbooks/…/workflows/…/activities/…`` must highlight
    Activities only, not Playbooks (substring checks caused double-active tabs).

    :returns: ``{"nav_section": str | None}`` — one of ``home``, ``playbooks``,
        ``workflows``, ``phases``, ``activities``, ``artifacts``, ``agents``,
        ``skills``, ``rules``, ``pips``, or ``None``.
    """
    path = getattr(request, "path", "") or ""
    match = getattr(request, "resolver_match", None)
    url_name = getattr(match, "url_name", None) if match else None

    if path.startswith("/activities/") or (
        "/playbooks/" in path and "/activities/" in path
    ):
        section = "activities"
    elif path.startswith("/workflows/") or (
        "/playbooks/" in path
        and "/workflows/" in path
        and "/activities/" not in path
    ):
        section = "workflows"
    elif path.startswith("/phases/") or (
        "/playbooks/" in path and "/phases/" in path
    ):
        section = "phases"
    elif path.startswith("/artifacts/") or (
        "/playbooks/" in path and "/artifacts/" in path
    ):
        section = "artifacts"
    elif path.startswith("/agents/") or (
        "/playbooks/" in path and "/agents/" in path
    ):
        section = "agents"
    elif path.startswith("/skills/") or (
        "/playbooks/" in path and "/skills/" in path
    ):
        section = "skills"
    elif path.startswith("/rules/") or ("/playbooks/" in path and "/rules/" in path):
        section = "rules"
    elif path.startswith("/pips/") or path.startswith("/pip/"):
        section = "pips"
    elif "/playbooks/" in path:
        section = "playbooks"
    elif path == "/dashboard/" or url_name == "dashboard":
        section = "home"
    else:
        section = None

    return {"nav_section": section}


def pip_nav(request: HttpRequest) -> dict:
    """
    Unread count for top-nav PIPs pill.

    :param request: Incoming HTTP request.
    :returns: Mapping with ``pip_nav_unread_count`` when authenticated.
    """
    if request.user.is_authenticated:
        from methodology.services.pip_service import PIPService

        return {"pip_nav_unread_count": PIPService.unread_submitter_count(request.user)}
    return {"pip_nav_unread_count": 0}
