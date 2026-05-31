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
    :returns: Dict with ``nav_section`` key: one of
        ``"home"``, ``"playbooks"``, ``"workflows"``, ``"activities"``,
        ``"pips"``, or ``None`` for unmatched paths.
    """
    path = request.path
    section = _resolve_nav_section(path)
    return {"nav_section": section}


def _resolve_nav_section(path: str):
    """Return nav section string for ``path``, or ``None`` if no match.

    Activity paths take priority over playbook/workflow paths so that
    nested URLs like ``/playbooks/12/workflows/25/activities/129/``
    highlight the Activities tab.

    :param path: URL path string.
    :returns: Section identifier or ``None``.
    """
    if "/activities/" in path:
        return "activities"
    if path.startswith("/browser/"):
        return "browser"
    if path.startswith("/dashboard/"):
        return "home"
    if path.startswith("/workflows/") or "/workflows/" in path:
        return "workflows"
    if path.startswith("/playbooks/"):
        return "playbooks"
    if path.startswith("/pips/") or path.startswith("/pip/"):
        return "pips"
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
