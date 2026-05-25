"""Administrative finalisation — apply typed PIP changes + major version bump."""

from __future__ import annotations

import logging

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from methodology.models import PipChange, ProcessImprovementProposal
from methodology.services.pip_apply_changes_service import (
    PipApplyChangesService,
    bump_playbook_major_version_after_pip_apply,
)
from methodology.services.pip_notification_service import send_decision_email

logger = logging.getLogger(__name__)


class PIPAdminService:
    """Apply administrator decisions atomically."""

    @staticmethod
    @transaction.atomic
    def finalize_pip(pip: ProcessImprovementProposal, actor) -> ProcessImprovementProposal:
        """
        Validate choices, mutate playbook rows, bump major version when needed, notify.

        :param pip: ``reviewed`` proposal with per-change decisions.
        :param actor: Staff user invoking finalisation.
        :return: Persisted proposal in a terminal workflow state.
        :raises ValidationError: when caller is not staff.
        :raises ValidationError: on invalid transitions or dangling decisions.
        """
        if actor is None or not actor.is_staff:
            raise ValidationError("Only staff administrators can finalise PIPs.")

        locked = ProcessImprovementProposal.objects.select_for_update(of=("self",)).select_related(
            "playbook", "created_by"
        ).get(pk=pip.pk)

        if locked.status != ProcessImprovementProposal.STATUS_REVIEWED:
            raise ValidationError("PIP must be in Reviewed state before finalising.")

        changes = list(
            PipChange.objects.filter(pip_id=locked.pk).order_by("order", "pk")
        )
        if not changes:
            raise ValidationError("No changes recorded for this PIP.")

        for ch in changes:
            if not ch.admin_decision or ch.admin_decision not in (
                PipChange.ADMIN_ACCEPT,
                PipChange.ADMIN_REJECT,
            ):
                raise ValidationError(
                    "Each change must have an explicit Accept/Reject decision."
                )

        accepted = [
            ch
            for ch in changes
            if ch.admin_decision == PipChange.ADMIN_ACCEPT
        ]
        rejected_cnt = sum(
            1 for ch in changes if ch.admin_decision == PipChange.ADMIN_REJECT
        )

        playbook = locked.playbook
        if playbook.status != "released":
            raise ValidationError("Only released playbooks consume PIPs.")

        bump_summary = ""

        if accepted:
            PipApplyChangesService.apply_changes(
                pip=locked,
                accepted=accepted,
                playbook=playbook,
            )
            bump_summary = PIPAdminService._describe_apply_summary(accepted)
            bump_playbook_major_version_after_pip_apply(
                pip=locked,
                playbook=playbook,
                actor=actor,
                summary_line=bump_summary,
            )

        PIPAdminService._apply_terminal_status(
            locked,
            len(accepted),
            rejected_cnt,
        )

        finalized_pk = locked.pk
        logger.info(
            "PIPAdminService.finalize_pip pk=%s actor=%s accepted=%s rejected=%s",
            finalized_pk,
            getattr(actor, "pk", None),
            len(accepted),
            rejected_cnt,
        )

        def _enqueue_email() -> None:
            refreshed = ProcessImprovementProposal.objects.prefetch_related(
                "changes"
            ).get(pk=finalized_pk)
            send_decision_email(refreshed)

        transaction.on_commit(_enqueue_email)

        locked.refresh_from_db()
        return locked

    @staticmethod
    def _describe_apply_summary(accepted: list[PipChange]) -> str:
        parts = []
        for ch in accepted:
            if ch.change_type in {PipChange.CHANGE_LINK, PipChange.CHANGE_UNLINK}:
                lbl = ch.target_name_snapshot or f"{ch.relationship_type} link"
            else:
                lbl = (
                    ch.name.strip()
                    or ch.target_name_snapshot.strip()
                    or f"{ch.change_type}-{ch.entity_type}"
                )
            parts.append(f"{ch.change_type} {lbl}")
        return "; ".join(parts)[:495]

    @staticmethod
    def _apply_terminal_status(
        pip_locked: ProcessImprovementProposal,
        accept_cnt: int,
        rejected_cnt: int,
    ) -> None:
        decided = timezone.now()

        if accept_cnt == 0:
            pip_locked.status = ProcessImprovementProposal.STATUS_REJECTED
        elif rejected_cnt == 0:
            pip_locked.status = ProcessImprovementProposal.STATUS_ACCEPTED
        else:
            pip_locked.status = ProcessImprovementProposal.STATUS_ACCEPTED_PARTIAL

        pip_locked.decided_at = decided
        pip_locked.save(update_fields=["status", "decided_at", "updated_at"])
