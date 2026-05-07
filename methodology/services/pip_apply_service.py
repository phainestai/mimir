"""
Apply approved Process Improvement Proposals (PIP) to released playbooks.

Batches structural edits then applies exactly one minor line bump (+0.1) and one
audit ``PlaybookVersion`` row per apply call.
"""

import logging
from collections.abc import Callable
from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from methodology.models import PlaybookVersion, ProcessImprovementProposal, VersionSource

logger = logging.getLogger(__name__)


@transaction.atomic
def apply_approved_pip_aggregate(
    *,
    pip: ProcessImprovementProposal,
    actor,
    aggregated_description: str,
    apply_mutations: Callable[[], None],
) -> ProcessImprovementProposal:
    """
    Run ORM mutations, then bump ``playbook.version`` by 0.1 once and record history.

    :param pip: Approved PIP linked to a released playbook
    :param actor: User performing the apply (must own the playbook)
    :param aggregated_description: Human-readable notes for the version row
    :param apply_mutations: Zero-argument callable performing ORM saves (no version bumping)
    """
    text = (aggregated_description or "").strip()
    if not text:
        raise ValidationError("Aggregated PIP description is required.")

    playbook = pip.playbook
    if playbook.author_id != actor.pk:
        raise PermissionError("You don't have permission to apply this PIP.")
    if playbook.status != "released":
        raise ValidationError("PIP apply is only valid for released playbooks.")
    if pip.status != "approved":
        raise ValidationError(f"PIP must be approved (current status: {pip.status}).")

    apply_mutations()

    playbook.refresh_from_db()
    current = Decimal(str(playbook.version))
    next_minor = (current + Decimal("0.1")).quantize(Decimal("0.1"))
    playbook.version = next_minor
    playbook.save(update_fields=["version", "updated_at"])

    PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=next_minor,
        snapshot_data={
            "pip_id": pip.pk,
            "playbook_name": playbook.name,
            "version": str(next_minor),
        },
        change_summary=text,
        description=text,
        is_major=False,
        source=VersionSource.PIP_SOURCE,
        pip=pip,
        created_by=actor,
    )

    pip.status = "implemented"
    pip.save(update_fields=["status"])

    logger.info(
        "Applied PIP id=%s to playbook id=%s → v%s",
        pip.pk,
        playbook.pk,
        next_minor,
    )
    return pip
