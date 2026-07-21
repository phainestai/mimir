"""Context processors for methodology app.

Injects global context variables into all template contexts.
"""

from methodology.services.notification_service import NotificationService


def app_version(request):
    """Inject application version information.

    :param request: Django HTTP request.
    :returns: Empty dict (version injected via other means).
    """
    return {}


def pip_nav(request):
    """Inject PIP navigation badge count for unread PIPs.

    :param request: Django HTTP request.
    :returns: Dict with pip_nav_unread_count key.
    """
    if request.user.is_authenticated:
        from methodology.models import ProcessImprovementProposal

        unread_count = ProcessImprovementProposal.objects.filter(
            status=ProcessImprovementProposal.STATUS_SUBMITTED
        ).count()
        return {"pip_nav_unread_count": unread_count}
    return {"pip_nav_unread_count": 0}


def primary_nav_section(request):
    """Inject primary navigation section context based on request path.

    Maps URL prefixes to nav section identifiers so the active navbar tab
    can be highlighted without each view setting it manually.

    :param request: Django HTTP request.
    :returns: Dict with ``nav_section`` key matching a navbar tab id, or ``None``.
    """
    path = request.path
    section = _resolve_nav_section(path)
    return {"nav_section": section}


def _resolve_nav_section(path: str):
    """Return nav section string for ``path``, or ``None`` if no match.

    More specific entity paths win over playbook nesting so e.g.
    ``/playbooks/12/workflows/25/activities/129/`` highlights Activities,
    and ``/playbooks/12/phases/`` highlights Phases — not Playbooks.

    Dashboard is checked before the generic ``/activities/`` substring so
    ``/dashboard/activities/`` stays on Home.

    :param path: URL path string.
    :returns: Section identifier or ``None``.
    """
    if path.startswith("/dashboard/"):
        return "home"
    if path.startswith("/browser/"):
        return "browser"
    if path.startswith("/teams/"):
        return "teams"
    if path.startswith("/pips/") or path.startswith("/pip/"):
        return "pips"

    # Nested or global entity routes (before bare /playbooks/)
    if "/activities/" in path or path.startswith("/activities/"):
        return "activities"
    if "/workflows/" in path or path.startswith("/workflows/"):
        return "workflows"
    if "/phases/" in path or path.startswith("/phases/"):
        return "phases"
    if "/artifacts/" in path or path.startswith("/artifacts/"):
        return "artifacts"
    if "/agents/" in path or path.startswith("/agents/"):
        return "agents"
    if "/skills/" in path or path.startswith("/skills/"):
        return "skills"
    if "/rules/" in path or path.startswith("/rules/"):
        return "rules"

    if path.startswith("/playbooks/"):
        return "playbooks"
    return None


def notification_count(request):
    """Inject unread notification count for authenticated users.

    :param request: Django HTTP request.
    :returns: Dict with unread_notification_count key.
    """
    if request.user.is_authenticated:
        count = NotificationService.get_unread_count(request.user)
        return {"unread_notification_count": count}
    return {"unread_notification_count": 0}
