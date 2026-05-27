"""Unit tests for pip_link_service structural ref validation."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from methodology.models import Activity, PipChange, Playbook, ProcessImprovementProposal, Workflow
from methodology.services.pip_link_service import validate_pending_or_live_ref
from methodology.services.pip_service import PIPService

User = get_user_model()


@pytest.fixture
def author(db):
    return User.objects.create_user(username="ref_author", password="pw")


@pytest.fixture
def released_playbook(db, author):
    return Playbook.objects.create(
        name="Ref PB",
        description="desc",
        category="development",
        author=author,
        status="released",
        version=Decimal("1.0"),
    )


@pytest.fixture
def draft_pip(db, author, released_playbook):
    return PIPService.create_draft_for_playbook(
        actor=author,
        playbook_id=released_playbook.pk,
        title="Ref validation PIP",
    )


@pytest.mark.django_db
def test_validate_pending_ref_accepts_prior_add(author, draft_pip):
    PIPService.add_change(
        actor=author,
        pip=draft_pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW,
        name="Pending WF",
        content="wf",
        internal_ref="#wf1",
    )
    assert validate_pending_or_live_ref(
        pip=draft_pip,
        ref="#wf1",
        expected_type=PipChange.ENTITY_WORKFLOW,
        order_hint=2,
        playbook_id=draft_pip.playbook_id,
    ) is True


@pytest.mark.django_db
def test_validate_pending_ref_rejects_forward_ref(author, draft_pip):
    PIPService.add_change(
        actor=author,
        pip=draft_pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW,
        name="Pending WF",
        content="wf",
        internal_ref="#wf1",
    )
    with pytest.raises(ValidationError, match="earlier ADD"):
        validate_pending_or_live_ref(
            pip=draft_pip,
            ref="#wf1",
            expected_type=PipChange.ENTITY_WORKFLOW,
            order_hint=1,
            playbook_id=draft_pip.playbook_id,
        )


@pytest.mark.django_db
def test_validate_pending_ref_rejects_wrong_entity_type(author, draft_pip):
    PIPService.add_change(
        actor=author,
        pip=draft_pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL,
        name="Skill",
        content="sk",
        internal_ref="#sk1",
    )
    with pytest.raises(ValidationError, match="expected Workflow"):
        validate_pending_or_live_ref(
            pip=draft_pip,
            ref="#sk1",
            expected_type=PipChange.ENTITY_WORKFLOW,
            order_hint=2,
            playbook_id=draft_pip.playbook_id,
        )


@pytest.mark.django_db
def test_validate_live_ref_accepts_playbook_workflow(author, released_playbook, draft_pip):
    wf = Workflow.objects.create(
        playbook=released_playbook, name="Live WF", description="w", order=1,
    )
    assert validate_pending_or_live_ref(
        pip=draft_pip,
        ref=str(wf.pk),
        expected_type=PipChange.ENTITY_WORKFLOW,
        order_hint=1,
        playbook_id=released_playbook.pk,
    ) is False


@pytest.mark.django_db
def test_validate_ref_rejects_invalid_format(author, draft_pip):
    with pytest.raises(ValidationError, match="Invalid entity reference"):
        validate_pending_or_live_ref(
            pip=draft_pip,
            ref="not-a-ref",
            expected_type=PipChange.ENTITY_ACTIVITY,
            order_hint=1,
            playbook_id=draft_pip.playbook_id,
        )


@pytest.mark.django_db
def test_validate_live_activity_ref(author, released_playbook, draft_pip):
    wf = Workflow.objects.create(
        playbook=released_playbook, name="WF", description="w", order=1,
    )
    act = Activity.objects.create(
        workflow=wf, name="Act", guidance="body", order=1,
    )
    assert validate_pending_or_live_ref(
        pip=draft_pip,
        ref=str(act.pk),
        expected_type=PipChange.ENTITY_ACTIVITY,
        order_hint=1,
        playbook_id=released_playbook.pk,
    ) is False
