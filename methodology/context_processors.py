"""Context processors for methodology app.

Injects global context variables into all template contexts.
"""

from methodology.services.notification_service import NotificationService


def notification_count(request):
    """Inject unread notification count for authenticated users.

    :param request: Django HTTP request.
    :returns: Dict with unread_notification_count key.
    """
    if request.user.is_authenticated:
        count = NotificationService.get_unread_count(request.user)
        return {"unread_notification_count": count}
    return {"unread_notification_count": 0}
