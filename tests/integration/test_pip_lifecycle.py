"""Integration flow: Draft → Galdr reviewed → Admin finalise (+ email + major bump)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core import mail

from methodology.models import (
    Activity,
    PipChange,
    Playbook,
    ProcessImprovementProposal,
    Workflow,
)
from methodology.services.galdr_client import GaldrLLMError
from methodology.services.pip_admin_service import PIPAdminService
from methodology.services.pip_service import PIPService

User = get_user_model()


@pytest.fixture
def alice(db):
    u = User.objects.create_user(
        username="alice_pip_j", password="pw", email="alice@example.test"
    )
    return u


@pytest.fixture
def staff_bob(db):
    u = User.objects.create_user(
        username="bob_admin_pip", password="pw", email="bob@example.test"
    )
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def playbook_bundle(db, alice):
    pb = Playbook.objects.create(
        name="Lifecycle PB",
        description="desc",
        category="development",
        author=alice,
        status="released",
        version=Decimal("1.0"),
    )
    wf = Workflow.objects.create(
        playbook=pb,
        name="Main",
        description="wf",
        order=1,
    )
    act = Activity.objects.create(
        workflow=wf,
        name="Step One",
        guidance="legacy body",
        order=1,
    )
    return pb, wf, act


@pytest.mark.django_db
def test_galdr_eager_moves_to_reviewed(alice, playbook_bundle):
    pb, _wf, act = playbook_bundle
    pip = PIPService.create_draft_for_playbook(
        actor=alice,
        playbook_id=pb.pk,
        title="Bump guidance",
        summary="",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="new guidance markdown",
        name="",
    )
    PIPService.submit_for_review(actor=alice, pip=pip)
    pip.refresh_from_db()
    assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED


@pytest.mark.django_db
def test_galdr_failure_returns_to_submitted(monkeypatch, alice, playbook_bundle):
    pb, _wf, act = playbook_bundle
    pip = PIPService.create_draft_for_playbook(
        actor=alice,
        playbook_id=pb.pk,
        title="Fail galdr",
        summary="",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="x",
        name="",
    )

    class _BadClient:
        def evaluate_change(self, user_prompt):  # noqa: ARG002
            raise GaldrLLMError("forced failure")

    monkeypatch.setattr(
        "methodology.services.galdr_client.get_galdr_client", lambda: _BadClient()
    )

    PIPService.submit_for_review(actor=alice, pip=pip)
    pip.refresh_from_db()
    assert pip.status == ProcessImprovementProposal.STATUS_SUBMITTED


@pytest.mark.django_db(transaction=True)
def test_finalize_accepts_changes_major_bumps_version_and_emails_owner(
    alice, staff_bob, playbook_bundle
):
    pb, _wf, act = playbook_bundle

    pip = PIPService.create_draft_for_playbook(
        actor=alice,
        playbook_id=pb.pk,
        title="Admin finalize",
        summary="please",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="released guidance ✓",
        name="",
    )
    PIPService.submit_for_review(actor=alice, pip=pip)
    pip.refresh_from_db()
    assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED

    for ch in pip.changes.all():
        ch.galdr_recommendation = PipChange.GALDR_ACCEPT
        ch.galdr_reasoning = "ok"
        ch.admin_decision = PipChange.ADMIN_ACCEPT
        ch.save(
            update_fields=[
                "galdr_recommendation",
                "galdr_reasoning",
                "admin_decision",
                "updated_at",
            ]
        )

    mail.outbox.clear()
    PIPAdminService.finalize_pip(pip, staff_bob)

    pip.refresh_from_db()
    pb.refresh_from_db()
    act.refresh_from_db()

    assert pip.status == ProcessImprovementProposal.STATUS_ACCEPTED
    assert pb.version == Decimal("2.0")
    assert "released guidance ✓" in act.guidance
    assert mail.outbox, "Decision email must be queued"
    assert mail.outbox[0].to == ["alice@example.test"]
