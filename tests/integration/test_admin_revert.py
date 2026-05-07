"""S09–S10 admin revert released playbook to draft."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from methodology.models import Activity, Playbook, PlaybookVersion, Workflow
from methodology.models.playbook_version import VersionSource
from methodology.services.playbook_service import PlaybookService

User = get_user_model()


@pytest.fixture
def staff_admin(db):
    return User.objects.create_user(
        username="staff_adm",
        password="adm",
        is_staff=True,
    )


@pytest.fixture
def pb_owner(db):
    return User.objects.create_user(username="pb_owner_rev", password="pw")


@pytest.mark.django_db
def test_revert_keeps_version_changes_status(staff_admin, pb_owner):
    """Released playbook becomes draft; version number unchanged; optional admin PV row."""
    pb = Playbook.objects.create(
        name="Revert Me",
        description="desc " * 8,
        category="product",
        status="released",
        version=Decimal("1.2"),
        author=pb_owner,
    )

    PlaybookService.revert_released_playbook_to_draft(
        pb.id,
        actor=staff_admin,
        reason="Customer rollback requested",
    )
    pb.refresh_from_db()
    assert pb.status == "draft"
    assert pb.version == Decimal("1.2")

    av = PlaybookVersion.objects.filter(
        playbook=pb, version_number=Decimal("1.2"), source=VersionSource.ADMIN
    )
    assert av.count() == 1


@pytest.mark.django_db
def test_post_revert_edits_then_release(staff_admin, pb_owner):
    pb = Playbook.objects.create(
        name="Revert Then Ship",
        description="desc " * 8,
        category="product",
        status="released",
        version=Decimal("1.2"),
        author=pb_owner,
    )
    wf = Workflow.objects.create(playbook=pb, name="W", description="w", order=1)
    act = Activity.objects.create(
        workflow=wf,
        name="Step",
        guidance="original guidance text here ok",
        order=1,
    )

    PlaybookService.revert_released_playbook_to_draft(
        pb.id,
        actor=staff_admin,
        reason="Temporarily unlocking edits",
    )
    pb.refresh_from_db()
    assert pb.status == "draft"

    act.guidance = "edited after revert"
    act.save()

    pb.refresh_from_db()
    assert pb.version == Decimal("1.3")

    PlaybookService.release_playbook(
        pb.id,
        pb_owner,
        description="Next major after hotfix line",
    )
    pb.refresh_from_db()
    assert pb.status == "released"
    assert pb.version == Decimal("2.0")
    assert act.guidance == "edited after revert"
