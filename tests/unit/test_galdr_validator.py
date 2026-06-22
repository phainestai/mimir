"""Unit tests for Galdr structural pre-validation."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from methodology.models import Activity, PipChange, Playbook, Workflow
from methodology.services.galdr_validator import GaldrStructuralValidator
from methodology.services.pip_service import PIPService

User = get_user_model()


@pytest.fixture
def author(db):
    return User.objects.create_user(username="galdr_val", password="pw")


@pytest.fixture
def released_playbook(db, author):
    pb = Playbook.objects.create(
        name="Galdr Val PB",
        description="desc",
        category="development",
        author=author,
        status="released",
        version=Decimal("1.0"),
    )
    wf = Workflow.objects.create(playbook=pb, name="Main", description="wf", order=1)
    Activity.objects.create(workflow=wf, name="Step", guidance="body", order=1)
    return pb


@pytest.fixture
def draft_pip(db, author, released_playbook):
    return PIPService.create_draft_for_playbook(
        actor=author,
        playbook_id=released_playbook.pk,
        title="Structural test PIP",
    )


@pytest.mark.django_db
def test_validator_rejects_empty_pip(author, released_playbook):
    pip = PIPService.create_draft_for_playbook(
        actor=author,
        playbook_id=released_playbook.pk,
        title="Empty",
    )
    report = GaldrStructuralValidator.validate_pip_structure(pip)
    assert not report.ok
    assert "zero changes" in report.errors[0].lower()


@pytest.mark.django_db
def test_validator_accepts_valid_alter(author, draft_pip, released_playbook):
    act = Activity.objects.filter(workflow__playbook=released_playbook).first()
    PIPService.add_change(
        actor=author,
        pip=draft_pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="updated guidance",
        name="",
    )
    report = GaldrStructuralValidator.validate_pip_structure(draft_pip)
    assert report.ok


@pytest.mark.django_db
def test_validator_rejects_duplicate_internal_ref(author, draft_pip):
    PipChange.objects.create(
        pip=draft_pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL,
        order=1,
        name="Skill A",
        content="content a",
        internal_ref="#dup-skill",
    )
    PipChange.objects.create(
        pip=draft_pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL,
        order=2,
        name="Skill B",
        content="content b",
        internal_ref="#dup-skill",
    )
    report = GaldrStructuralValidator.validate_pip_structure(draft_pip)
    assert not report.ok
    assert any("duplicate internal_ref" in e.lower() for e in report.errors)


@pytest.mark.django_db
def test_validator_rejects_unresolved_link_ref(author, draft_pip, released_playbook):
    act = Activity.objects.filter(workflow__playbook=released_playbook).first()
    PipChange.objects.create(
        pip=draft_pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        order=1,
        source_entity_type=PipChange.ENTITY_SKILL,
        source_entity_ref="#missing-skill",
        target_entity_type=PipChange.ENTITY_ACTIVITY,
        target_entity_ref=str(act.pk),
        content="link rationale",
    )
    report = GaldrStructuralValidator.validate_pip_structure(draft_pip)
    assert not report.ok
    assert report.errors
