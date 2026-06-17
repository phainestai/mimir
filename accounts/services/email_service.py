"""
Transactional email for accounts — uses Django ``EMAIL_BACKEND``.

All outbound mail is **plain text only** with absolute ``https://…`` links
(see ``FRONTEND_URL``). In development: console backend prints to stdout.
In production: ``django_ses.SESBackend`` (see ``mimir.settings.prod``).
Tests: ``locmem`` backend and ``django.core.mail.outbox``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from django.conf import settings
from django.core.mail import send_mail

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

logger = logging.getLogger(__name__)


class EmailService:
    """Send plain-text transactional email via Django's mail API."""

    @staticmethod
    def get_site_base_url() -> str:
        """Return configured site origin without trailing slash."""
        return getattr(settings, "FRONTEND_URL", "http://localhost:8000").rstrip("/")

    @staticmethod
    def build_absolute_url(path: str, *, base_url: str | None = None) -> str:
        """Join *path* (``/teams/1/``) with site origin → full URL."""
        root = (base_url or EmailService.get_site_base_url()).rstrip("/")
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{root}{normalized}"

    @staticmethod
    def send_text_email(subject: str, body: str, to_addresses: list[str]) -> None:
        """Send one plain-text email.

        :param subject: Email subject line.
        :param body: Plain-text body (include full URLs for links).
        :param to_addresses: Recipient list (not logged — privacy).
        :raises Exception: Re-raises any failure from Django's mail layer.
        """
        sender = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@mimir.local")
        send_mail(
            subject=subject,
            message=body,
            from_email=sender,
            recipient_list=to_addresses,
            fail_silently=False,
        )
        logger.info(
            "[EMAIL] Sent subject=%r to_n=%d from_backend=%s",
            subject,
            len(to_addresses),
            settings.EMAIL_BACKEND,
        )

    @staticmethod
    def send_welcome_email(user: AbstractBaseUser) -> None:
        """Send welcome email to new user.

        :param user: Django user with ``email`` set.
        :raises Exception: If delivery fails.
        """
        base_url = EmailService.get_site_base_url()
        login_url = EmailService.build_absolute_url("/auth/user/login/", base_url=base_url)
        name = user.first_name or user.username
        subject = "Welcome to Mimir!"
        body = f"""Hello {name},

Welcome to Mimir! Your account has been successfully created.

You can now start creating playbooks and workflows to organize your development processes.

Username: {user.username}
Email: {user.email}

Log in: {login_url}

If you have any questions, please don't hesitate to reach out.

Best regards,
The Mimir Team
"""
        EmailService.send_text_email(subject, body, [user.email])

    @staticmethod
    def send_password_reset_email(user: AbstractBaseUser, reset_url: str) -> None:
        """Send password reset email with confirm link.

        :param user: Django user.
        :param reset_url: Absolute URL to ``password_reset_confirm`` view.
        :raises Exception: If delivery fails.
        """
        name = user.first_name or user.username
        subject = "Password Reset - Mimir"
        body = f"""Hello {name},

You requested a password reset for your Mimir account.

Reset your password at:
{reset_url}

If you did not request this, please ignore this email.

Best regards,
The Mimir Team
"""
        EmailService.send_text_email(subject, body, [user.email])

    @staticmethod
    def send_verification_email(
        user: AbstractBaseUser,
        token: str,
        *,
        base_url: str | None = None,
    ) -> None:
        """Send email with one-click verification link.

        :param user: Django user; mail goes to ``user.email``.
        :param token: URL-safe verification token.
        :param base_url: Site origin (default: ``settings.FRONTEND_URL``).
        :raises Exception: If delivery fails.
        """
        verify_url = EmailService.build_absolute_url(
            f"/auth/user/verify-email/{token}/",
            base_url=base_url,
        )
        name = user.first_name or user.username
        subject = "Verify your Mimir email address"
        body = f"""Hello {name},

Please verify your Mimir email address by visiting the link below (valid for 24 hours):

{verify_url}

If you did not create a Mimir account, you can ignore this email.

Best regards,
The Mimir Team
"""
        EmailService.send_text_email(subject, body, [user.email])
