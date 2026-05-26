"""Team invite-by-email service (WP-7 — MANAGE-23/24).

Handles sending invitations to both existing and new (auto-registered) users.
For new users, creates an inactive account and a JoinRequest with source='invited_new'.
For existing users, creates a JoinRequest with source='invited'.
"""

from __future__ import annotations

import logging
import re

from django.contrib.auth.models import User
from django.db import transaction

from methodology.models import JoinRequest, Team, TeamMembership

logger = logging.getLogger(__name__)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class TeamInviteService:
    """Service for inviting users to a team via email address.

    Supports inviting both existing platform users and newcomers who get
    auto-registered with an inactive account pending activation.
    """

    def send_invites(self, team: Team, inviter, emails: list, welcome_text: str) -> dict:
        """Process invite list for a team.

        :param team: Target Team instance.
        :param inviter: User sending the invites.
        :param emails: List of email address strings.
        :param welcome_text: Optional custom message included in invite emails.
        :returns: Dict with keys sent, created, skipped, invalid.
        """
        result: dict = {"sent": 0, "created": 0, "skipped": [], "invalid": []}
        valid_emails, invalid_emails = self._parse_emails_list(emails)
        result["invalid"] = invalid_emails

        for email in valid_emails:
            self._process_single_invite(team, inviter, email, welcome_text, result)

        logger.info(
            "[teams] invites processed: sent=%d created=%d skipped=%d invalid=%d team=%s inviter=%s",
            result["sent"],
            result["created"],
            len(result["skipped"]),
            len(result["invalid"]),
            team.name,
            inviter.username,
        )
        return result

    def _process_single_invite(
        self, team: Team, inviter, email: str, welcome_text: str, result: dict
    ) -> None:
        """Process one email address: check membership, create request, send email.

        :param team: Target Team instance.
        :param inviter: User sending the invite.
        :param email: Single email address to invite.
        :param welcome_text: Optional welcome message.
        :param result: Mutable result dict to update in place.
        """
        try:
            user = User.objects.get(email=email)
            if TeamMembership.objects.filter(team=team, user=user).exists():
                result["skipped"].append(email)
                logger.info("[teams] invite skipped (already member): email=%s team=%s", email, team.name)
                return
            jr = self._create_invite_join_request(team, user, JoinRequest.SOURCE_INVITED)
            self._send_existing_user_invite(jr, welcome_text)
        except User.DoesNotExist:
            with transaction.atomic():
                new_user, activation_token = self._auto_register(email)
                jr = self._create_invite_join_request(team, new_user, JoinRequest.SOURCE_INVITED_NEW)
            result["created"] += 1
            self._send_new_user_invite(jr, activation_token, welcome_text)

        result["sent"] += 1

    def _create_invite_join_request(self, team: Team, user, source: str) -> JoinRequest:
        """Create a JoinRequest with the given source, avoiding duplicates.

        :param team: Target Team instance.
        :param user: User to create the request for.
        :param source: JoinRequest.SOURCE_INVITED or SOURCE_INVITED_NEW.
        :returns: New or existing pending JoinRequest.
        """
        existing = JoinRequest.objects.filter(team=team, user=user, status=JoinRequest.STATUS_PENDING).first()
        if existing:
            logger.info(
                "[teams] invite: reusing existing pending join request pk=%s user=%s team=%s",
                existing.pk,
                user.username,
                team.name,
            )
            return existing
        jr = JoinRequest.objects.create(team=team, user=user, source=source)
        logger.info(
            "[teams] invite: created join request pk=%s source=%s user=%s team=%s",
            jr.pk,
            source,
            user.username,
            team.name,
        )
        return jr

    def _auto_register(self, email: str) -> tuple[User, str]:
        """Create an inactive account from an email address and generate activation token.

        username  = local part before @
        first_name = local part before first '.' (or full local if no '.')
        last_name  = domain name without TLD
        password  = unusable
        is_active  = False

        :param email: Email address to create account for.
        :returns: Tuple of (newly created inactive User instance, activation token).
        """
        from accounts.models import generate_verification_token
        
        local, domain = email.split("@", 1)
        username = self._safe_username(local)
        first_name = local.split(".")[0]
        domain_parts = domain.split(".")
        last_name = domain_parts[0] if len(domain_parts) >= 2 else domain

        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
        )
        user.set_unusable_password()
        user.save()
        
        # Generate email verification token for activation
        token = generate_verification_token(user)
        
        logger.info(
            "[teams] auto-registered inactive user: username=%s email=%s first_name=%s last_name=%s token_generated=True",
            username,
            email,
            first_name,
            last_name,
        )
        return user, token

    def _safe_username(self, local: str) -> str:
        """Derive a unique username from the local part of an email.

        :param local: Local part of the email address (before @).
        :returns: Unique username string.
        """
        base = local.replace("+", "_")
        if not User.objects.filter(username=base).exists():
            return base
        i = 1
        while User.objects.filter(username=f"{base}_{i}").exists():
            i += 1
        return f"{base}_{i}"

    def _parse_emails_list(self, emails: list) -> tuple:
        """Validate a list of email strings.

        :param emails: List of raw email strings.
        :returns: Tuple of (valid_list, invalid_list).
        """
        valid: list = []
        invalid: list = []
        for email in emails:
            email = email.strip()
            if not email:
                continue
            if EMAIL_REGEX.match(email):
                valid.append(email)
            else:
                invalid.append(email)
        return valid, invalid

    def _parse_emails(self, raw: str) -> tuple:
        """Split a comma-separated email string and validate each address.

        :param raw: Comma-separated email addresses as a single string.
        :returns: Tuple of (valid_list, invalid_list).
        """
        parts = [e.strip() for e in raw.split(",") if e.strip()]
        return self._parse_emails_list(parts)

    def _send_existing_user_invite(self, jr: JoinRequest, welcome_text: str) -> None:
        """Send invite email to an existing platform user.

        :param jr: JoinRequest created for this invite.
        :param welcome_text: Optional welcome message from the admin.
        """
        from methodology.services import team_notification_service

        try:
            team_notification_service.send_invite_existing_user(jr, welcome_text)
        except Exception as exc:
            logger.warning("[teams] invite email failed (non-fatal): %s", str(exc))

    def _send_new_user_invite(self, jr: JoinRequest, activation_token: str, welcome_text: str) -> None:
        """Send activation + invite email to a newly auto-registered user.

        :param jr: JoinRequest created for this invite.
        :param activation_token: Email verification token for account activation.
        :param welcome_text: Optional welcome message from the admin.
        """
        from methodology.services import team_notification_service

        try:
            team_notification_service.send_invite_new_user(jr, activation_token, welcome_text)
        except Exception as exc:
            logger.warning("[teams] new user invite email failed (non-fatal): %s", str(exc))
