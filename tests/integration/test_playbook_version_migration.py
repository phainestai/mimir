"""S02 — VERSIONING-27 data migration backfill (integer-era rows → Decimal X.Y metadata)."""

import json
from decimal import Decimal

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone

from methodology.models.playbook_version import PlaybookVersion

User = get_user_model()


def _insert_legacy_playbook_version(
    *,
    playbook_pk: int,
    user_pk: int,
    version_number: int,
    snapshot_data: dict,
    change_summary: str,
) -> None:
    """Insert a row shaped like methodology.0011 (integer version_number)."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO methodology_playbookversion
                (playbook_id, version_number, snapshot_data, change_summary,
                 created_at, created_by_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            [
                playbook_pk,
                version_number,
                json.dumps(snapshot_data),
                change_summary or "",
                timezone.now(),
                user_pk,
            ],
        )


@pytest.mark.django_db(transaction=True)
def test_backfill_decimal_versions_from_integers():
    executor = MigrationExecutor(connection)
    executor.migrate([("methodology", "0011_rule_model_and_activity_m2m")])

    user = User.objects.create_user(username="pv_mig_u1", password="pw")
    Playbook = apps.get_model("methodology", "Playbook")
    playbook = Playbook.objects.create(
        name="Legacy PB Migr",
        description="d" * 30,
        category="product",
        author=user,
        status="active",
    )

    _insert_legacy_playbook_version(
        playbook_pk=playbook.pk,
        user_pk=user.pk,
        version_number=2,
        snapshot_data={"stub": True},
        change_summary="Release notes",
    )

    call_command(
        "migrate",
        "methodology",
        "0013_playbook_version_legacy_backfill",
        verbosity=0,
        interactive=False,
    )

    pv = PlaybookVersion.objects.get(playbook_id=playbook.pk)
    assert pv.version_number == Decimal("2.0")
    assert pv.is_major is True
    assert pv.source == "release"
    assert pv.description == "Release notes"


@pytest.mark.django_db(transaction=True)
def test_no_rows_deleted_after_migration():
    executor = MigrationExecutor(connection)
    executor.migrate([("methodology", "0011_rule_model_and_activity_m2m")])

    user = User.objects.create_user(username="pv_mig_u2", password="pw")
    Playbook = apps.get_model("methodology", "Playbook")
    playbook = Playbook.objects.create(
        name="Legacy PB Migr Two",
        description="d" * 30,
        category="product",
        author=user,
        status="draft",
    )

    _insert_legacy_playbook_version(
        playbook_pk=playbook.pk,
        user_pk=user.pk,
        version_number=1,
        snapshot_data={},
        change_summary="",
    )
    _insert_legacy_playbook_version(
        playbook_pk=playbook.pk,
        user_pk=user.pk,
        version_number=2,
        snapshot_data={"a": 1},
        change_summary="Second",
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM methodology_playbookversion WHERE playbook_id = %s",
            [playbook.pk],
        )
        n_before = cursor.fetchone()[0]

    call_command(
        "migrate",
        "methodology",
        "0013_playbook_version_legacy_backfill",
        verbosity=0,
        interactive=False,
    )
    n_after = PlaybookVersion.objects.filter(playbook_id=playbook.pk).count()

    assert n_before == n_after == 2
