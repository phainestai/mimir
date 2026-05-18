"""
PIP decision email integration tests — FOB-PIP-EMAIL-*.

Layer 1 (always runs, CI-safe): locmem backend assertions on subject,
recipients, body keywords, and template rendering.

Layer 2 (opt-in, real SES): enabled only when all of:
    USE_SES_IN_DEV=1
    AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (or instance role)
    AWS_SES_REGION_NAME
    TEST_EMAIL_RECIPIENT  — a SES-verified address to receive the probe
are present.  The live test sends one email, verifies no exception is raised,
and logs the SES MessageId.  It does NOT assert on receipt (would require MX
/ SES inbound rules which are out of scope for MVP).

See docs/architecture/SAO.md § Email Architecture for full context.
"""

from __future__ import annotations

import os
import logging
from decimal import Decimal

import pytest
from django.core import mail
from django.contrib.auth import get_user_model

from methodology.models import (
    Activity,
    PipChange,
    Playbook,
    ProcessImprovementProposal,
    Workflow,
)
from methodology.services.pip_admin_service import PIPAdminService
from methodology.services.pip_service import PIPService

logger = logging.getLogger(__name__)

User = get_user_model()

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def submitter(db):
    return User.objects.create_user(
        username="pip_email_alice",
        password="pw",
        email="alice@example.test",
        first_name="Alice",
        last_name="Test",
    )


@pytest.fixture
def admin_user(db):
    u = User.objects.create_user(
        username="pip_email_admin",
        password="pw",
        email="admin@example.test",
    )
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def released_playbook(db, submitter):
    pb = Playbook.objects.create(
        name="Email Test Playbook",
        description="For PIP email integration tests." * 2,
        category="development",
        author=submitter,
        status="released",
        version=Decimal("1.0"),
    )
    return pb


@pytest.fixture
def playbook_with_activity(db, released_playbook, submitter):
    wf = Workflow.objects.create(
        playbook=released_playbook,
        name="Main Workflow",
        description="test wf",
        order=1,
    )
    act = Activity.objects.create(
        workflow=wf,
        name="Old Activity",
        guidance="Old guidance",
        order=1,
    )
    return released_playbook, wf, act


def _make_reviewed_pip(submitter, playbook_with_activity):
    """Create a draft, add a change, submit → reviewed (Galdr stub runs eagerly in tests)."""
    pb, _wf, act = playbook_with_activity
    pip = PIPService.create_draft_for_playbook(
        actor=submitter,
        playbook_id=pb.pk,
        title="Email Integration Test PIP",
        summary="Checking the email path end-to-end.",
    )
    PIPService.add_change(
        actor=submitter,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="Updated guidance for email test.",
        name="",
    )
    PIPService.submit_for_review(actor=submitter, pip=pip)
    pip.refresh_from_db()
    # Test settings set GALDR_EAGER=True → PIP should be REVIEWED after submit
    return pip


# ---------------------------------------------------------------------------
# Layer 1: locmem backend (always runs)
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
class TestPIPEmailLocmem:
    """FOB-PIP-EMAIL-01 to 05: email content via Django locmem backend."""

    def test_email_01_accepted_pip_sends_one_email(self, submitter, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-01: finalise with all ACCEPT → exactly one email queued."""
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED, (
            f"Expected REVIEWED after eager Galdr, got {pip.status}"
        )
        for ch in pip.changes.all():
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "Fine."
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        assert len(mail.outbox) == 1, f"Expected 1 email, got {len(mail.outbox)}"

    def test_email_02_accepted_subject_line(self, submitter, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-02: subject contains title and Accepted marker."""
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "ok"
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        msg = mail.outbox[0]
        assert pip.title in msg.subject
        assert "Accepted" in msg.subject
        assert "✓" in msg.subject

    def test_email_03_recipient_is_submitter_email(self, submitter, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-03: email To: == submitter.email."""
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "ok"
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        msg = mail.outbox[0]
        assert submitter.email in msg.to

    def test_email_04_rejected_subject_line(self, submitter, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-04: full rejection → subject says Rejected ✗."""
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_REJECT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "fine"
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        msg = mail.outbox[0]
        assert "Rejected" in msg.subject
        assert "✗" in msg.subject

    def test_email_05_body_contains_change_decisions(self, submitter, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-05: body renders change decisions and verdict."""
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "Consistent with workflow goal."
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        body = mail.outbox[0].body
        assert "ACCEPT" in body
        assert "Accepted" in body  # overall verdict line
        assert "Consistent with workflow goal." in body

    def test_email_06_no_email_when_submitter_has_no_email(self, admin_user, playbook_with_activity):
        """FOB-PIP-EMAIL-06: submitter without email address → no crash, no email."""
        pb, _wf, act = playbook_with_activity
        no_email_user = User.objects.create_user(
            username="pip_email_noemail", password="pw", email=""
        )
        pip = PIPService.create_draft_for_playbook(
            actor=no_email_user,
            playbook_id=pb.pk,
            title="No-email PIP",
            summary="",
        )
        PIPService.add_change(
            actor=no_email_user,
            pip=pip,
            change_type=PipChange.CHANGE_ALTER,
            entity_type=PipChange.ENTITY_ACTIVITY,
            target_id=act.pk,
            content="x",
            name="",
        )
        PIPService.submit_for_review(actor=no_email_user, pip=pip)
        pip.refresh_from_db()
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "ok"
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)  # must not raise

        assert len(mail.outbox) == 0, "Expected no email when submitter has no address"

    def test_email_07_from_address_uses_default_from_email(
        self, submitter, admin_user, playbook_with_activity, settings
    ):
        """FOB-PIP-EMAIL-07: From: header == settings.DEFAULT_FROM_EMAIL."""
        settings.DEFAULT_FROM_EMAIL = "test-noreply@mimir.test"
        pip = _make_reviewed_pip(submitter, playbook_with_activity)
        for ch in pip.changes.all():
            ch.admin_decision = PipChange.ADMIN_ACCEPT
            ch.galdr_recommendation = PipChange.GALDR_ACCEPT
            ch.galdr_reasoning = "ok"
            ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

        mail.outbox.clear()
        PIPAdminService.finalize_pip(pip, admin_user)

        msg = mail.outbox[0]
        assert msg.from_email == "test-noreply@mimir.test"


# ---------------------------------------------------------------------------
# Layer 2: live SES smoke test (opt-in, skipped in CI)
# ---------------------------------------------------------------------------

_LIVE_SES_REQUIRED = {
    "USE_SES_IN_DEV": "1",
    "AWS_SES_REGION_NAME": None,
    "TEST_EMAIL_RECIPIENT": None,
}

_live_ses_missing = [
    k for k, required_val in _LIVE_SES_REQUIRED.items()
    if required_val is not None and os.getenv(k) != required_val
    or required_val is None and not os.getenv(k, "").strip()
]

_skip_live = pytest.mark.skipif(
    bool(_live_ses_missing),
    reason=f"Live SES test skipped — missing env vars: {_live_ses_missing}",
)


@_skip_live
@pytest.mark.django_db(transaction=True)
def test_live_ses_pip_decision_email_sends(
    submitter, admin_user, playbook_with_activity, settings
):
    """
    FOB-PIP-EMAIL-LIVE-01: Send a real SES email through the full PIP finalize path.

    Requires: USE_SES_IN_DEV=1, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY,
              AWS_SES_REGION_NAME, TEST_EMAIL_RECIPIENT (SES-verified address).

    Asserts: no exception is raised; logs the SES MessageId via the django-ses
    backend. Does NOT assert receipt (would require SES inbound / MX rules).
    """
    settings.EMAIL_BACKEND = "django_ses.SESBackend"
    settings.AWS_SES_REGION_NAME = os.environ["AWS_SES_REGION_NAME"]
    settings.AWS_SES_REGION_ENDPOINT = f"email.{settings.AWS_SES_REGION_NAME}.amazonaws.com"
    settings.DEFAULT_FROM_EMAIL = os.environ.get(
        "DEFAULT_FROM_EMAIL", "noreply@featurefactory.io"
    )

    recipient = os.environ["TEST_EMAIL_RECIPIENT"]
    submitter.email = recipient
    submitter.save(update_fields=["email"])

    pip = _make_reviewed_pip(submitter, playbook_with_activity)
    assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED

    for ch in pip.changes.all():
        ch.admin_decision = PipChange.ADMIN_ACCEPT
        ch.galdr_recommendation = PipChange.GALDR_ACCEPT
        ch.galdr_reasoning = "Live SES smoke test — please ignore."
        ch.save(update_fields=["galdr_recommendation", "galdr_reasoning", "admin_decision", "updated_at"])

    # Will raise if SES rejects (wrong creds, unverified sender, etc.)
    PIPAdminService.finalize_pip(pip, admin_user)

    pip.refresh_from_db()
    assert pip.status in (
        ProcessImprovementProposal.STATUS_ACCEPTED,
        ProcessImprovementProposal.STATUS_ACCEPTED_PARTIAL,
    )
    logger.info(
        "Live SES smoke test passed — PIP %s finalised, email sent to %s",
        pip.pk,
        recipient,
    )
