"""Unit tests for PlaybookVersion X.Y schema (VERSIONING-26)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from methodology.models.playbook import Playbook
from methodology.models.playbook_version import PlaybookVersion, VersionSource
from methodology.models.process_improvement_proposal import ProcessImprovementProposal

User = get_user_model()


@pytest.mark.django_db
def test_playbook_version_model_accepts_decimal_xy():
    user = User.objects.create_user(username="pvuser", password="x")
    playbook = Playbook.objects.create(
        name="Pb",
        description="d",
        category="development",
        author=user,
        status="draft",
    )

    pv = PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=Decimal("1.2"),
        snapshot_data={},
        change_summary="x",
        source=VersionSource.AUTHOR,
    )
    pv.refresh_from_db()
    assert pv.version_number == Decimal("1.2")


@pytest.mark.django_db
def test_unique_constraint_playbook_version():
    user = User.objects.create_user(username="pvuser2", password="x")
    playbook = Playbook.objects.create(
        name="Pb2",
        description="d",
        category="development",
        author=user,
        status="draft",
    )
    PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=Decimal("1.0"),
        snapshot_data={},
    )
    with pytest.raises(IntegrityError):
        PlaybookVersion.objects.create(
            playbook=playbook,
            version_number=Decimal("1.0"),
            snapshot_data={},
        )


@pytest.mark.django_db
def test_source_choices_defaults():
    user = User.objects.create_user(username="pvuser_sv", password="x")
    playbook = Playbook.objects.create(
        name="Pb_sv",
        description="d",
        category="product",
        author=user,
        status="draft",
    )
    pv = PlaybookVersion(
        playbook=playbook,
        version_number=Decimal("0.1"),
        snapshot_data={"nodes": []},
        created_by=user,
    )
    pv.full_clean()
    assert VersionSource.PIP_SOURCE == "pip"
    assert pv.source == VersionSource.AUTHOR


@pytest.mark.django_db
def test_pip_fk_nullable():
    user = User.objects.create_user(username="pvuser3", password="x")
    playbook = Playbook.objects.create(
        name="Pb3",
        description="d",
        category="development",
        author=user,
        status="released",
    )
    pip = ProcessImprovementProposal.objects.create(
        playbook=playbook, title="T", status="open"
    )
    v1 = PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=Decimal("1.0"),
        snapshot_data={},
        pip=None,
    )
    v2 = PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=Decimal("1.1"),
        snapshot_data={},
        pip=pip,
        source=VersionSource.PIP_SOURCE,
    )
    assert v1.pip_id is None
    assert v2.pip_id == pip.id
