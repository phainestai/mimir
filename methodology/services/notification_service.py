"""Notification service for in-app notifications (WP-D).

Handles creating, retrieving, and marking notifications as read.
"""

import logging

from methodology.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing in-app notifications."""

    @staticmethod
    def create(user, notification_type: str, title: str, message: str = "", link: str = "") -> Notification:
        """Create a new notification for a user.

        :param user: User to notify.
        :param notification_type: Type of notification (use Notification.TYPE_* constants).
        :param title: Notification title.
        :param message: Optional message body.
        :param link: Optional link URL.
        :returns: Created Notification instance.
        """
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            link=link,
        )
        logger.info(
            "[notifications] created: type=%s user=%s pk=%s",
            notification_type,
            user.username,
            notification.pk,
        )
        return notification

    @staticmethod
    def get_unread_count(user) -> int:
        """Get count of unread notifications for user.

        :param user: User to check.
        :returns: Count of unread notifications.
        """
        count = Notification.objects.filter(user=user, is_read=False).count()
        logger.debug("[notifications] unread count user=%s count=%d", user.username, count)
        return count

    @staticmethod
    def get_recent(user, limit: int = 20):
        """Get recent notifications for user (read and unread).

        :param user: User to fetch notifications for.
        :param limit: Maximum number of notifications to return.
        :returns: QuerySet of Notification instances (newest first).
        """
        notifications = Notification.objects.filter(user=user).order_by("-created_at")[:limit]
        logger.debug(
            "[notifications] fetched recent user=%s count=%d limit=%d",
            user.username,
            notifications.count(),
            limit,
        )
        return notifications

    @staticmethod
    def mark_read(notification_id: int, user) -> Notification:
        """Mark a notification as read.

        :param notification_id: Notification PK.
        :param user: User owning the notification (for security).
        :returns: Updated Notification instance.
        :raises Notification.DoesNotExist: If notification not found or not owned by user.
        """
        notification = Notification.objects.get(pk=notification_id, user=user)
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])
            logger.info(
                "[notifications] marked read: pk=%s user=%s type=%s",
                notification.pk,
                user.username,
                notification.type,
            )
        return notification

    @staticmethod
    def mark_all_read(user) -> int:
        """Mark all notifications as read for user.

        :param user: User whose notifications to mark read.
        :returns: Count of notifications updated.
        """
        count = Notification.objects.filter(user=user, is_read=False).update(is_read=True)
        logger.info("[notifications] marked all read: user=%s count=%d", user.username, count)
        return count
