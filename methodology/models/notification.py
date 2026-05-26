"""Notification model for in-app notifications (WP-D).

Tracks user notifications for team events (join requests, approvals, invites, etc.).
"""

from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    """In-app notification for team events."""

    # Notification types
    TYPE_TEAM_JOIN_REQUEST = "team_join_request"
    TYPE_TEAM_APPROVED = "team_approved"
    TYPE_TEAM_REJECTED = "team_rejected"
    TYPE_TEAM_INVITE = "team_invite"
    TYPE_TEAM_REMOVED = "team_removed"
    TYPE_TEAM_ADMIN_TRANSFER = "team_admin_transfer"

    TYPES = [
        (TYPE_TEAM_JOIN_REQUEST, "Team Join Request"),
        (TYPE_TEAM_APPROVED, "Team Approved"),
        (TYPE_TEAM_REJECTED, "Team Rejected"),
        (TYPE_TEAM_INVITE, "Team Invite"),
        (TYPE_TEAM_REMOVED, "Team Removed"),
        (TYPE_TEAM_ADMIN_TRANSFER, "Team Admin Transfer"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type = models.CharField(max_length=50, choices=TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True)
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["user", "is_read"]),
        ]

    def __str__(self):
        return f"Notification({self.type}, user={self.user.username}, read={self.is_read})"
