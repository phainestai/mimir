"""Notification views for in-app notification bell (WP-D).

Provides HTMX endpoints for notification dropdown and mark-read actions.
"""

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from methodology.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


def _is_htmx(request) -> bool:
    """Return True when the request was issued by HTMX."""
    return request.headers.get("HX-Request") == "true"


def _dropdown_context(user):
    """Build template context for the notification dropdown partial."""
    return {
        "notifications": NotificationService.get_recent(user, limit=20),
        "unread_count": NotificationService.get_unread_count(user),
    }


def _htmx_dropdown_response(request) -> HttpResponse:
    """Return refreshed dropdown HTML plus an OOB badge update for HTMX."""
    context = _dropdown_context(request.user)
    body = render_to_string("notifications/dropdown.html", context, request=request)
    body += render_to_string("notifications/badge_oob.html", context, request=request)
    return HttpResponse(body)


@login_required
def notification_list(request):
    """Return notification dropdown HTML (HTMX target).
    
    :param request: Django HTTP request.
    :return: Rendered partial HTML for notification dropdown.
    """
    context = _dropdown_context(request.user)

    logger.info(
        "[notifications] list view: user=%s count=%d unread=%d",
        request.user.username,
        context["notifications"].count(),
        context["unread_count"],
    )

    return render(request, "notifications/dropdown.html", context)


@login_required
@require_POST
def mark_read(request, notification_id: int):
    """Mark a notification as read and return updated count.
    
    :param request: Django HTTP request.
    :param notification_id: Notification PK to mark read.
    :return: JSON response with updated unread count.
    """
    try:
        NotificationService.mark_read(notification_id, request.user)
        unread_count = NotificationService.get_unread_count(request.user)
        logger.info(
            "[notifications] marked read: pk=%d user=%s new_count=%d",
            notification_id,
            request.user.username,
            unread_count,
        )
        if _is_htmx(request):
            return _htmx_dropdown_response(request)
        return JsonResponse({"success": True, "unread_count": unread_count})
    except Exception as exc:
        logger.error(
            "[notifications] mark read failed: pk=%d user=%s error=%s",
            notification_id,
            request.user.username,
            str(exc),
        )
        return JsonResponse({"success": False, "error": str(exc)}, status=400)


@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read.
    
    :param request: Django HTTP request.
    :return: JSON response with count of notifications marked read.
    """
    try:
        count = NotificationService.mark_all_read(request.user)
        logger.info("[notifications] marked all read: user=%s count=%d", request.user.username, count)
        if _is_htmx(request):
            return _htmx_dropdown_response(request)
        return JsonResponse({"success": True, "count": count, "unread_count": 0})
    except Exception as exc:
        logger.error(
            "[notifications] mark all read failed: user=%s error=%s",
            request.user.username,
            str(exc),
        )
        return JsonResponse({"success": False, "error": str(exc)}, status=400)
