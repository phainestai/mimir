"""Integration tests for in-app notification system (WP-D)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Notification
from methodology.services.notification_service import NotificationService

User = get_user_model()


@pytest.mark.django_db
class TestNotificationService:
    """Test NotificationService methods."""

    def test_create_notification(self):
        """NotificationService.create should create a notification."""
        user = User.objects.create_user(username="notif_user", password="pass", email="user@test.com")

        notification = NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Test Notification",
            message="This is a test message",
            link="/teams/1/",
        )

        assert notification.user == user
        assert notification.type == Notification.TYPE_TEAM_INVITE
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test message"
        assert notification.link == "/teams/1/"
        assert not notification.is_read
        assert notification.created_at is not None

    def test_get_unread_count(self):
        """NotificationService.get_unread_count should return correct count."""
        user = User.objects.create_user(username="notif_user2", password="pass", email="user2@test.com")

        NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Unread 1",
            message="",
            link="",
        )
        NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_APPROVED,
            title="Unread 2",
            message="",
            link="",
        )

        assert NotificationService.get_unread_count(user) == 2

    def test_get_recent(self):
        """NotificationService.get_recent should return recent notifications."""
        user = User.objects.create_user(username="notif_user3", password="pass", email="user3@test.com")

        for i in range(25):
            NotificationService.create(
                user=user,
                notification_type=Notification.TYPE_TEAM_INVITE,
                title=f"Notification {i}",
                message="",
                link="",
            )

        recent = NotificationService.get_recent(user, limit=20)
        assert recent.count() == 20

    def test_mark_read(self):
        """NotificationService.mark_read should mark notification as read."""
        user = User.objects.create_user(username="notif_user4", password="pass", email="user4@test.com")

        notification = NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Test Mark Read",
            message="",
            link="",
        )

        assert not notification.is_read

        NotificationService.mark_read(notification.pk, user)
        notification.refresh_from_db()

        assert notification.is_read

    def test_mark_all_read(self):
        """NotificationService.mark_all_read should mark all user notifications as read."""
        user = User.objects.create_user(username="notif_user5", password="pass", email="user5@test.com")

        for i in range(5):
            NotificationService.create(
                user=user,
                notification_type=Notification.TYPE_TEAM_INVITE,
                title=f"Notification {i}",
                message="",
                link="",
            )

        assert NotificationService.get_unread_count(user) == 5

        count = NotificationService.mark_all_read(user)
        assert count == 5
        assert NotificationService.get_unread_count(user) == 0


@pytest.mark.django_db
class TestNotificationViews:
    """Test notification views and HTMX endpoints."""

    def test_notification_list_requires_login(self):
        """GET /notifications/ should require authentication."""
        client = Client()
        response = client.get(reverse("notifications:list"))
        assert response.status_code == 302  # Redirect to login

    def test_notification_list_for_authenticated_user(self):
        """GET /notifications/ should return notification dropdown HTML."""
        user = User.objects.create_user(username="notif_user6", password="pass", email="user6@test.com")
        client = Client()
        client.force_login(user)

        NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Test Notification",
            message="Test message",
            link="/teams/1/",
        )

        response = client.get(reverse("notifications:list"))
        assert response.status_code == 200
        assert b"Test Notification" in response.content
        assert b"Test message" in response.content
        assert b'data-testid="notification-item-' in response.content

    def test_notification_list_empty_state(self):
        """GET /notifications/ should show empty state when no notifications."""
        user = User.objects.create_user(username="notif_user7", password="pass", email="user7@test.com")
        client = Client()
        client.force_login(user)

        response = client.get(reverse("notifications:list"))
        assert response.status_code == 200
        assert b"No notifications yet" in response.content
        assert b'data-testid="notifications-empty"' in response.content

    def test_mark_read_endpoint(self):
        """POST /notifications/<pk>/read/ should mark notification as read."""
        user = User.objects.create_user(username="notif_user8", password="pass", email="user8@test.com")
        client = Client()
        client.force_login(user)

        notification = NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Test",
            message="",
            link="",
        )

        response = client.post(reverse("notifications:mark_read", args=[notification.pk]))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["unread_count"] == 0

        notification.refresh_from_db()
        assert notification.is_read

    def test_mark_read_endpoint_htmx_refreshes_dropdown_and_badge(self):
        """HTMX mark-read should return refreshed dropdown HTML and badge OOB swap."""
        user = User.objects.create_user(username="notif_user8b", password="pass", email="user8b@test.com")
        client = Client()
        client.force_login(user)

        notification = NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Unread alert",
            message="Please review",
            link="/teams/1/",
        )
        NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Second alert",
            message="",
            link="",
        )

        response = client.post(
            reverse("notifications:mark_read", args=[notification.pk]),
            HTTP_HX_REQUEST="true",
        )
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert "Unread alert" in content
        assert 'data-testid="notification-item-' in content
        assert 'id="notification-badge-container"' in content
        assert 'hx-swap-oob="innerHTML"' in content
        assert 'data-testid="notification-badge">1</span>' in content.replace(" ", "")

        notification.refresh_from_db()
        assert notification.is_read
        assert NotificationService.get_unread_count(user) == 1

    def test_mark_all_read_endpoint(self):
        """POST /notifications/read-all/ should mark all notifications as read."""
        user = User.objects.create_user(username="notif_user9", password="pass", email="user9@test.com")
        client = Client()
        client.force_login(user)

        for i in range(3):
            NotificationService.create(
                user=user,
                notification_type=Notification.TYPE_TEAM_INVITE,
                title=f"Notification {i}",
                message="",
                link="",
            )

        response = client.post(reverse("notifications:mark_all_read"))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 3
        assert data["unread_count"] == 0

        assert NotificationService.get_unread_count(user) == 0

    def test_mark_all_read_endpoint_htmx_clears_badge(self):
        """HTMX mark-all-read should return dropdown HTML with empty badge OOB."""
        user = User.objects.create_user(username="notif_user9b", password="pass", email="user9b@test.com")
        client = Client()
        client.force_login(user)

        for i in range(3):
            NotificationService.create(
                user=user,
                notification_type=Notification.TYPE_TEAM_INVITE,
                title=f"Notification {i}",
                message="",
                link="",
            )

        response = client.post(reverse("notifications:mark_all_read"), HTTP_HX_REQUEST="true")
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert 'id="notification-badge-container"' in content
        assert 'data-testid="notification-badge"' not in content
        assert 'data-testid="mark-all-read-btn"' not in content

        assert NotificationService.get_unread_count(user) == 0


@pytest.mark.django_db
class TestNotificationContextProcessor:
    """Test notification_count context processor."""

    def test_unread_count_in_context(self):
        """Context processor should inject unread_notification_count."""
        user = User.objects.create_user(username="notif_user10", password="pass", email="user10@test.com")
        client = Client()
        client.force_login(user)

        NotificationService.create(
            user=user,
            notification_type=Notification.TYPE_TEAM_INVITE,
            title="Test",
            message="",
            link="",
        )

        # Access any page that uses base.html
        response = client.get(reverse("index"))
        assert response.status_code == 200
        # Check that the notification bell badge is present
        assert b'data-testid="notification-badge"' in response.content
        # Check badge count (may have whitespace)
        content_str = response.content.decode("utf-8")
        assert "notification-badge" in content_str
        # The badge should contain "1" somewhere near it
        badge_idx = content_str.find('data-testid="notification-badge"')
        assert badge_idx > 0, "Badge testid found"
        # Check for the count "1" within 100 chars of the badge
        badge_section = content_str[badge_idx:badge_idx+100]
        assert "1" in badge_section, f"Count '1' not found near badge: {badge_section}"

    def test_no_badge_when_zero_unread(self):
        """Context processor should not show badge when unread_count is 0."""
        user = User.objects.create_user(username="notif_user11", password="pass", email="user11@test.com")
        client = Client()
        client.force_login(user)

        response = client.get(reverse("index"))
        assert response.status_code == 200
        # Badge should not be present
        assert b'data-testid="notification-badge"' not in response.content


@pytest.mark.django_db
class TestTeamNotificationIntegration:
    """Test that team events create in-app notifications."""

    def test_auto_join_creates_notification(self):
        """Joining a team should create a notification."""
        from methodology.models import Team, TeamMembership
        from methodology.services.team_notification_service import send_auto_join_confirmation

        admin = User.objects.create_user(username="admin_notif", password="pass", email="admin@test.com")
        member = User.objects.create_user(username="member_notif", password="pass", email="member@test.com")

        team = Team.objects.create(
            name="Test Team",
            admin=admin,
            visibility=Team.VISIBILITY_PUBLIC,
            join_policy=Team.JOIN_POLICY_AUTO,
        )
        membership = TeamMembership.objects.create(team=team, user=member)

        # Clear existing notifications from team creation
        Notification.objects.all().delete()

        send_auto_join_confirmation(membership)

        notifications = Notification.objects.filter(user=member)
        assert notifications.count() == 1
        notif = notifications.first()
        assert notif.type == Notification.TYPE_TEAM_APPROVED
        assert "Joined" in notif.title
        assert team.name in notif.title

    def test_join_request_creates_admin_notification(self):
        """Join request should create notification for admin."""
        from methodology.models import Team, JoinRequest
        from methodology.services.team_notification_service import send_join_request_to_admin

        admin = User.objects.create_user(username="admin_notif2", password="pass", email="admin2@test.com")
        requester = User.objects.create_user(
            username="requester_notif", password="pass", email="requester@test.com"
        )

        team = Team.objects.create(
            name="Test Team 2",
            admin=admin,
            visibility=Team.VISIBILITY_PUBLIC,
            join_policy=Team.JOIN_POLICY_APPROVAL,
        )

        join_request = JoinRequest.objects.create(team=team, user=requester)

        # Clear existing notifications
        Notification.objects.all().delete()

        send_join_request_to_admin(join_request)

        notifications = Notification.objects.filter(user=admin)
        assert notifications.count() == 1
        notif = notifications.first()
        assert notif.type == Notification.TYPE_TEAM_JOIN_REQUEST
        assert "Join request" in notif.title
        assert team.name in notif.title
