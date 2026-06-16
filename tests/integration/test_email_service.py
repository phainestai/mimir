"""Integration tests for accounts EmailService — locmem backend, no SES."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings

import pytest

from accounts.services.email_service import EmailService

User = get_user_model()

_LOCMEM = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def mail_user(db):
    return User.objects.create_user(
        username="mailtest",
        email="mailtest@example.com",
        password="x" * 12,
        first_name="Mail",
    )


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_verification_email_sends_correct_subject(mail_user):
    EmailService.send_verification_email(
        mail_user, "tok123", base_url="https://mimir.example"
    )
    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Verify your Mimir email address"


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_verification_email_contains_token_url(mail_user):
    EmailService.send_verification_email(
        mail_user, "secret-token-abc", base_url="https://mimir.example"
    )
    body = mail.outbox[0].body
    assert "https://mimir.example/auth/user/verify-email/secret-token-abc/" in body
    assert "<" not in body


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_welcome_email_is_plain_text_with_login_link(mail_user):
    EmailService.send_welcome_email(mail_user)
    msg = mail.outbox[0]
    assert msg.content_subtype == "plain"
    assert "http://testserver/auth/user/login/" in msg.body
    assert "<html" not in msg.body.lower()


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_verification_email_recipient_is_user_email(mail_user):
    EmailService.send_verification_email(mail_user, "t", base_url="http://localhost:8000")
    assert mail.outbox[0].to == [mail_user.email]


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_welcome_email_uses_email_backend(mail_user):
    EmailService.send_welcome_email(mail_user)
    assert len(mail.outbox) == 1
    assert "Welcome to Mimir" in mail.outbox[0].subject


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM)
def test_send_password_reset_email_uses_email_backend(mail_user):
    reset_url = "http://localhost:8000/auth/user/password-reset-confirm/abc/token/"
    EmailService.send_password_reset_email(mail_user, reset_url)
    assert len(mail.outbox) == 1
    assert "Password Reset" in mail.outbox[0].subject
    assert reset_url in mail.outbox[0].body


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM, DEFAULT_FROM_EMAIL="noreply@test.local")
def test_send_password_reset_email_uses_default_from_email(mail_user):
    EmailService.send_password_reset_email(mail_user, "http://localhost/reset/")
    assert mail.outbox[0].from_email == "noreply@test.local"


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND=_LOCMEM, DEFAULT_FROM_EMAIL="noreply@test.local")
def test_send_uses_default_from_email(mail_user):
    EmailService.send_verification_email(mail_user, "x", base_url="http://x")
    assert mail.outbox[0].from_email == "noreply@test.local"
