"""Business logic for Playbook Improvement Proposals (PIPs).

Shared by Django views, admin, and MCP tool wrappers.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable, Optional

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Max, QuerySet
from django.utils import timezone

from methodology.models import (
    Activity,
    Agent,
    Artifact,
    Phase,
    PipChange,
    Playbook,
    ProcessImprovementProposal,
    Rule,
    Skill,
    UserPIPListVisit,
    Workflow,
)
from methodology.services.pip_link_service import (
    link_change_summary_label,
    validate_internal_ref_label,
    validate_link_change_for_persist,
    validate_pending_or_live_ref,
)

from methodology.services.playbook_service import PlaybookService

logger = logging.getLogger(__name__)

_WITHDRAW_ALLOWED = frozenset(
    {
        ProcessImprovementProposal.STATUS_DRAFT,
        ProcessImprovementProposal.STATUS_SUBMITTED,
        ProcessImprovementProposal.STATUS_PROCESSING_GALDR,
    }
)


def _last_list_visit(user) -> Optional[datetime]:
    """Return stored list visit timestamp or ``None``.

    :param user: Django user.
    """
    row = UserPIPListVisit.objects.filter(user=user).only("last_visited_at").first()
    return row.last_visited_at if row else None


def _pip_require_submitter_for_submitter_tools(
    pip: ProcessImprovementProposal, actor
) -> None:
    """Owner-only UX actions (withdraw, submit, draft edits)."""
    if pip.created_by_id != actor.pk:
        raise ValidationError("Only the submitter can perform this action.")


def _pip_allow_submit_for_review(pip: ProcessImprovementProposal, actor) -> None:
    """
    Submit from Draft or re-queue after Galdr rollback to ``submitted``.

    :raises ValidationError: when wrong actor or incompatible status.
    """
    _pip_require_submitter_for_submitter_tools(pip, actor)
    allowed = frozenset(
        {
            ProcessImprovementProposal.STATUS_DRAFT,
            ProcessImprovementProposal.STATUS_SUBMITTED,
        }
    )
    if pip.status not in allowed:
        raise ValidationError("Submit is only allowed from Draft or a retry queue.")


def _pip_require_draft(pip: ProcessImprovementProposal, actor) -> None:
    """Guard mutating draft builder operations."""
    _pip_require_submitter_for_submitter_tools(pip, actor)
    if pip.status != ProcessImprovementProposal.STATUS_DRAFT:
        raise ValidationError("Editable only while Draft.")


def _next_change_sequence(pip: ProcessImprovementProposal) -> int:
    agg = PipChange.objects.filter(pip=pip).aggregate(m=Max("order"))
    return (agg["m"] or 0) + 1


def _renumber_sequences(pip: ProcessImprovementProposal) -> None:
    qs = PipChange.objects.filter(pip=pip).order_by("order", "pk")
    for idx, change in enumerate(qs, start=1):
        if change.order != idx:
            change.order = idx
            change.save(update_fields=["order", "updated_at"])


def _entity_target_label(playbook: Playbook, entity_type: str, target_id: int) -> str:
    """Resolve human label for ALTER/DROP targets."""
    if entity_type == PipChange.ENTITY_ACTIVITY:
        act = Activity.objects.select_related("workflow").get(pk=target_id)
        if act.workflow.playbook_id != playbook.pk:
            raise ValidationError("Activity is outside the target playbook.")
        return act.name
    if entity_type == PipChange.ENTITY_SKILL:
        sk = Skill.objects.get(pk=target_id)
        if sk.playbook_id != playbook.pk:
            raise ValidationError("Skill playbook mismatch.")
        return sk.title
    if entity_type == PipChange.ENTITY_AGENT:
        ag = Agent.objects.get(pk=target_id)
        if ag.playbook_id != playbook.pk:
            raise ValidationError("Agent playbook mismatch.")
        return ag.name
    if entity_type == PipChange.ENTITY_WORKFLOW:
        wf = Workflow.objects.get(pk=target_id)
        if wf.playbook_id != playbook.pk:
            raise ValidationError("Workflow playbook mismatch.")
        return wf.name
    if entity_type == PipChange.ENTITY_ARTIFACT:
        art = Artifact.objects.get(pk=target_id)
        if art.playbook_id != playbook.pk:
            raise ValidationError("Artifact playbook mismatch.")
        return art.name
    if entity_type == PipChange.ENTITY_RULE:
        ru = Rule.objects.get(pk=target_id)
        if ru.playbook_id != playbook.pk:
            raise ValidationError("Rule playbook mismatch.")
        return ru.title
    if entity_type == PipChange.ENTITY_PHASE:
        ph = Phase.objects.get(pk=target_id)
        if ph.playbook_id != playbook.pk:
            raise ValidationError("Phase playbook mismatch.")
        return ph.name
    raise ValidationError(f"Unsupported entity '{entity_type}' for targets.")


def _normalize_entity_ref(raw: str) -> str:
    return (raw or "").strip()


def _validate_ref_pair(
    *,
    pip: ProcessImprovementProposal,
    fk_set: bool,
    ref_raw: str,
    field_label: str,
) -> None:
    ref = _normalize_entity_ref(ref_raw)
    if fk_set and ref:
        raise ValidationError(f"{field_label}: use either FK or ref, not both.")


def _persist_pip_change(
    pip: ProcessImprovementProposal,
    *,
    change_type: str,
    entity_type: str,
    name: str,
    content: str,
    target_id: Optional[int],
    parent_workflow_id: Optional[int],
    parent_workflow_ref: str,
    insert_after_activity_id: Optional[int],
    insert_after_activity_ref: str,
    phase_ref: str,
    produced_by_activity_ref: str,
    artifact_type: str,
    artifact_is_required: bool,
    append_to_playbook_end: bool,
    internal_ref: str = "",
) -> PipChange:
    pb = pip.playbook
    ct = change_type.upper().strip()
    et = entity_type.strip()
    entities = {c[0] for c in PipChange.ENTITY_TYPE_CHOICES}
    if et not in entities:
        raise ValidationError("Invalid entity type.")
    if ct not in {
        PipChange.CHANGE_ADD,
        PipChange.CHANGE_ALTER,
        PipChange.CHANGE_DROP,
    }:
        raise ValidationError("Invalid change type.")

    nm = name.strip()
    body = content.strip()

    parent_wf: Optional[Workflow] = None
    if parent_workflow_id:
        parent_wf = Workflow.objects.get(pk=parent_workflow_id)
        if parent_wf.playbook_id != pb.pk:
            raise ValidationError("Parent workflow mismatch.")

    after_act: Optional[Activity] = None
    if insert_after_activity_id:
        after_act = Activity.objects.select_related("workflow").get(
            pk=insert_after_activity_id
        )
        if after_act.workflow.playbook_id != pb.pk:
            raise ValidationError("Sibling activity playbook mismatch.")

    order_val = _next_change_sequence(pip)
    parent_ref = _normalize_entity_ref(parent_workflow_ref)
    insert_ref = _normalize_entity_ref(insert_after_activity_ref)
    phase_ref_norm = _normalize_entity_ref(phase_ref)
    producer_ref = _normalize_entity_ref(produced_by_activity_ref)

    _validate_ref_pair(
        pip=pip, fk_set=bool(parent_workflow_id), ref_raw=parent_ref,
        field_label="parent_workflow",
    )
    _validate_ref_pair(
        pip=pip, fk_set=bool(insert_after_activity_id), ref_raw=insert_ref,
        field_label="insert_after_activity",
    )

    if ct == PipChange.CHANGE_ADD and et == PipChange.ENTITY_ACTIVITY:
        if not parent_workflow_id and not parent_ref:
            raise ValidationError("ADD Activity requires parent_workflow_id or parent_workflow_ref.")
        if parent_ref:
            validate_pending_or_live_ref(
                pip=pip, ref=parent_ref, expected_type=PipChange.ENTITY_WORKFLOW,
                order_hint=order_val, playbook_id=pb.pk,
            )
        if insert_ref:
            validate_pending_or_live_ref(
                pip=pip, ref=insert_ref, expected_type=PipChange.ENTITY_ACTIVITY,
                order_hint=order_val, playbook_id=pb.pk,
            )
        if phase_ref_norm:
            validate_pending_or_live_ref(
                pip=pip, ref=phase_ref_norm, expected_type=PipChange.ENTITY_PHASE,
                order_hint=order_val, playbook_id=pb.pk,
            )

    if ct == PipChange.CHANGE_ADD and et == PipChange.ENTITY_ARTIFACT:
        if not producer_ref:
            raise ValidationError("ADD Artifact requires produced_by_activity_ref.")
        validate_pending_or_live_ref(
            pip=pip, ref=producer_ref, expected_type=PipChange.ENTITY_ACTIVITY,
            order_hint=order_val, playbook_id=pb.pk,
        )

    if ct == PipChange.CHANGE_ALTER and et == PipChange.ENTITY_ACTIVITY and phase_ref_norm:
        validate_pending_or_live_ref(
            pip=pip, ref=phase_ref_norm, expected_type=PipChange.ENTITY_PHASE,
            order_hint=order_val, playbook_id=pb.pk,
        )

    display_name = nm
    if ct == PipChange.CHANGE_ADD and not nm:
        raise ValidationError("Name is required for ADD changes.")
    if ct == PipChange.CHANGE_ALTER and not nm and not body:
        raise ValidationError("ALTER requires at least one of name or content.")
    if ct == PipChange.CHANGE_DROP and not body:
        raise ValidationError("Rationale is required for DROP changes.")
    tgt = target_id
    if ct == PipChange.CHANGE_ALTER:
        if not tgt:
            raise ValidationError("ALTER requires target_id.")
        display_name = nm or _entity_target_label(pb, et, tgt)
    elif ct == PipChange.CHANGE_DROP:
        if not tgt:
            raise ValidationError("DROP requires target_id.")
        display_name = nm or _entity_target_label(pb, et, tgt)

    ref_label = ""
    if ct == PipChange.CHANGE_ADD and internal_ref.strip():
        ref_label = validate_internal_ref_label(internal_ref)
        dup = PipChange.objects.filter(
            pip=pip,
            change_type=PipChange.CHANGE_ADD,
            internal_ref=ref_label,
        ).exists()
        if dup:
            raise ValidationError(f"Duplicate internal_ref '{ref_label}' in this PIP.")

    art_type = (artifact_type or "Document").strip() or "Document"
    pc = PipChange.objects.create(
        pip=pip,
        change_type=ct,
        entity_type=et,
        order=order_val,
        name=nm if ct in {PipChange.CHANGE_ADD, PipChange.CHANGE_ALTER} else "",
        content=body,
        target_id=tgt,
        target_name_snapshot=(display_name or "") if ct != PipChange.CHANGE_ADD else "",
        parent_workflow=parent_wf,
        insert_after_activity=after_act,
        parent_workflow_ref=parent_ref,
        insert_after_activity_ref=insert_ref,
        phase_ref=phase_ref_norm,
        produced_by_activity_ref=producer_ref,
        artifact_type=art_type,
        artifact_is_required=bool(artifact_is_required),
        append_to_playbook_end=bool(append_to_playbook_end),
        internal_ref=ref_label,
    )
    logger.info("Persisted PipChange pk=%s pip=%s", pc.pk, pip.pk)
    return pc


def _persist_link_change(
    pip: ProcessImprovementProposal,
    *,
    change_type: str,
    relationship_type: str,
    source_entity_ref: str,
    target_entity_ref: str,
    content: str = "",
) -> PipChange:
    order_val = _next_change_sequence(pip)
    rel, src_type, src_ref, tgt_type, tgt_ref = validate_link_change_for_persist(
        pip=pip,
        change_type=change_type,
        relationship_type=relationship_type,
        source_entity_ref=source_entity_ref,
        target_entity_ref=target_entity_ref,
        order_hint=order_val,
    )
    ct = change_type.upper().strip()
    snapshot = link_change_summary_label(
        PipChange(
            change_type=ct,
            relationship_type=rel,
            source_entity_type=src_type,
            source_entity_ref=src_ref,
            target_entity_type=tgt_type,
            target_entity_ref=tgt_ref,
        )
    )
    pc = PipChange.objects.create(
        pip=pip,
        change_type=ct,
        entity_type="",
        order=order_val,
        relationship_type=rel,
        source_entity_type=src_type,
        source_entity_ref=src_ref,
        target_entity_type=tgt_type,
        target_entity_ref=tgt_ref,
        content=(content or "").strip(),
        target_name_snapshot=snapshot[:255],
    )
    logger.info("Persisted LINK PipChange pk=%s pip=%s %s", pc.pk, pip.pk, rel)
    return pc


class PIPService:
    """CRUD-ish workflow helpers for ProcessImprovementProposal records."""

    @staticmethod
    def create_pip_from_protocol(protocol_file: str, pip_title: str, actor=None) -> dict:
        """
        MCP / API façade for WorkflowProtocolService (protocol-path PIPs).

        :param protocol_file: Path passed to WorkflowProtocolService.
        :param pip_title: Caller-provided proposal title.
        :param actor: Django user creating the PIP.
        :return: Service result dictionary.
        """
        from methodology.services.workflow_protocol_service import (
            WorkflowProtocolService,
        )

        logger.info("PIPService.create_pip_from_protocol title=%s actor=%s",
                    pip_title, getattr(actor, 'pk', None))
        return WorkflowProtocolService.create_pip_from_protocol(
            protocol_file, pip_title, actor=actor
        )

    @staticmethod
    def last_list_visit_at(user):
        """
        Stored timestamp from the user's last ``/pips/`` navigation.

        :param user: Django user.
        """
        return _last_list_visit(user)

    @staticmethod
    def unread_submitter_count(user) -> int:
        """
        Navigation badge: submissions by ``user`` changed after last list visit.

        :param user: Django user (submitter role).
        :return: Whole number for badge rendering.
        """
        last_visit = _last_list_visit(user)
        qs = ProcessImprovementProposal.objects.filter(created_by=user)
        if last_visit is None:
            n = 0
        else:
            n = qs.filter(status_changed_at__gt=last_visit).count()
        logger.info(
            "PIPService.unread_submitter_count user=%s last_visit=%s count=%s",
            user.pk,
            last_visit,
            n,
        )
        return n

    @staticmethod
    def mark_list_viewed(user) -> None:
        """
        Call when user opens ``/pips/`` list — clears unread nav count & blue dots.

        :param user: Authenticated user.
        """
        visit, _created = UserPIPListVisit.objects.get_or_create(user=user)
        visit.last_visited_at = timezone.now()
        visit.save(update_fields=["last_visited_at"])
        logger.info("PIPService.mark_list_viewed user=%s", user.pk)

    @staticmethod
    def list_queryset_for_user(
        *,
        actor,
        scope: str = "mine",
        status_filters: Optional[Iterable[str]] = None,
        playbook_id: Optional[int] = None,
    ) -> QuerySet[ProcessImprovementProposal]:
        """
        Filtered PIP queryset for list views.

        :param actor: Current user.
        :param scope: ``mine`` (submitter) or ``all`` (staff-only).
        :param status_filters: Optional iterable of status codes.
        :param playbook_id: Optional target playbook primary key.
        :return: Annotated queryset with ``change_count``.
        :raises PermissionError: when ``all`` requested by non-staff.
        """
        if scope not in {"mine", "all"}:
            raise ValueError("scope must be 'mine' or 'all'")
        if scope == "all" and not actor.is_staff:
            raise PermissionError("Staff only: All PIPs tab.")

        base = ProcessImprovementProposal.objects.select_related(
            "playbook", "created_by"
        )
        if scope == "mine":
            base = base.filter(created_by=actor)
        qs = base.annotate(change_count=Count("changes", distinct=True))
        if status_filters:
            qs = qs.filter(status__in=list(status_filters))
        if playbook_id:
            qs = qs.filter(playbook_id=playbook_id)
        return qs.order_by("-updated_at", "-pk")

    @staticmethod
    def get_pip_with_changes(pip_id: int, actor) -> ProcessImprovementProposal:
        """Alias preserving explicit prefetch contract."""
        return PIPService.get_pip(pip_id, actor)

    @staticmethod
    def get_pip(pip_id: int, actor) -> ProcessImprovementProposal:
        """
        Fetch a single PIP with permission checks.

        :param pip_id: Primary key.
        :param actor: Requesting user.
        :return: Loaded instance.
        :raises ProcessImprovementProposal.DoesNotExist: when missing.
        :raises PermissionError: when neither owner nor staff.
        """
        pip = (
            ProcessImprovementProposal.objects.select_related(
                "playbook", "created_by"
            )
            .prefetch_related("changes")
            .get(pk=pip_id)
        )
        if pip.created_by_id != actor.pk and not actor.is_staff:
            raise PermissionError("Not allowed to view this PIP.")
        return pip

    @staticmethod
    @transaction.atomic
    def withdraw_pip(pip: ProcessImprovementProposal, actor) -> None:
        """
        Mark a PIP as withdrawn (status=withdrawn) for proposals still in editable / pre-review queues.

        :raises ValidationError: if already progressed past Galdr inbox.
        """
        _pip_require_submitter_for_submitter_tools(pip, actor)
        if pip.status not in _WITHDRAW_ALLOWED:
            raise ValidationError("This PIP can no longer be withdrawn.")
        pip.status = ProcessImprovementProposal.STATUS_WITHDRAWN
        pip.save(update_fields=["status"])
        logger.info("PIPService.withdraw_pip set pip=%s to withdrawn actor=%s", pip.pk, actor.pk)

    cancel_pip = withdraw_pip

    @staticmethod
    @transaction.atomic
    def create_draft_for_playbook(
        *,
        actor,
        playbook_id: int,
        title: str,
        summary: str = "",
    ) -> ProcessImprovementProposal:
        try:
            playbook = PlaybookService.get_playbook(playbook_id, actor)
        except Playbook.DoesNotExist:
            raise ValidationError(f"Playbook with id {playbook_id} does not exist.")
        except PermissionError as exc:
            raise ValidationError(str(exc)) from exc
        if playbook.status != "released":
            raise ValidationError("PIP targets must be Released playbooks.")
        ttl = title.strip()
        if not ttl:
            raise ValidationError("Title is required.")
        pip = ProcessImprovementProposal.objects.create(
            playbook=playbook,
            title=ttl,
            summary=(summary or "").strip(),
            status=ProcessImprovementProposal.STATUS_DRAFT,
            created_by=actor,
        )
        logger.info("PIP draft created pk=%s playbook=%s", pip.pk, playbook_id)
        return pip

    @staticmethod
    @transaction.atomic
    def save_draft_header(
        *, actor, pip: ProcessImprovementProposal, title: str, summary: str = ""
    ) -> ProcessImprovementProposal:
        _pip_require_draft(pip, actor)
        ttl = title.strip()
        if not ttl:
            raise ValidationError("Title is required.")
        pip.title = ttl
        pip.summary = (summary or "").strip()
        pip.save(update_fields=["title", "summary", "updated_at"])
        return pip

    @staticmethod
    @transaction.atomic
    def add_change(
        *,
        actor,
        pip: ProcessImprovementProposal,
        change_type: str,
        entity_type: str = "",
        name: str = "",
        content: str = "",
        target_id: Optional[int] = None,
        parent_workflow_id: Optional[int] = None,
        parent_workflow_ref: str = "",
        insert_after_activity_id: Optional[int] = None,
        insert_after_activity_ref: str = "",
        phase_ref: str = "",
        produced_by_activity_ref: str = "",
        artifact_type: str = "",
        artifact_is_required: bool = False,
        append_to_playbook_end: bool = False,
        internal_ref: str = "",
        relationship_type: str = "",
        source_entity_ref: str = "",
        target_entity_ref: str = "",
    ) -> PipChange:
        _pip_require_draft(pip, actor)
        ct = (change_type or "").upper().strip()
        if ct in {PipChange.CHANGE_LINK, PipChange.CHANGE_UNLINK}:
            return _persist_link_change(
                pip=pip,
                change_type=ct,
                relationship_type=relationship_type,
                source_entity_ref=source_entity_ref,
                target_entity_ref=target_entity_ref,
                content=content,
            )
        return _persist_pip_change(
            pip=pip,
            change_type=change_type,
            entity_type=entity_type,
            name=name,
            content=content,
            target_id=target_id,
            parent_workflow_id=parent_workflow_id,
            parent_workflow_ref=parent_workflow_ref,
            insert_after_activity_id=insert_after_activity_id,
            insert_after_activity_ref=insert_after_activity_ref,
            phase_ref=phase_ref,
            produced_by_activity_ref=produced_by_activity_ref,
            artifact_type=artifact_type,
            artifact_is_required=artifact_is_required,
            append_to_playbook_end=append_to_playbook_end,
            internal_ref=internal_ref,
        )

    @staticmethod
    @transaction.atomic
    def remove_change(
        *, actor, pip: ProcessImprovementProposal, change_id: int
    ) -> None:
        _pip_require_draft(pip, actor)
        deleted_count, _ = PipChange.objects.filter(pk=change_id, pip=pip).delete()
        if not deleted_count:
            raise ValidationError("Change not found.")
        _renumber_sequences(pip)
        logger.info("Removed change=%s pip=%s", change_id, pip.pk)

    @staticmethod
    def summarize_preview_rows(pip: ProcessImprovementProposal) -> list[dict]:
        entity_bucket = {
            PipChange.CHANGE_ADD: "Added",
            PipChange.CHANGE_ALTER: "Modified",
            PipChange.CHANGE_DROP: "Removed",
        }
        link_bucket = {
            PipChange.CHANGE_LINK: "Links Added",
            PipChange.CHANGE_UNLINK: "Links Removed",
        }
        rows = []
        for ch in PipChange.objects.filter(pip=pip).order_by("order", "pk"):
            if ch.change_type in link_bucket:
                label = ch.target_name_snapshot or link_change_summary_label(ch)
                rows.append(
                    {
                        "section": link_bucket[ch.change_type],
                        "change_type": ch.change_type,
                        "snippet": label,
                        "relationship_type": ch.relationship_type,
                    }
                )
                continue
            label = (
                ch.name or ch.target_name_snapshot or str(ch.target_id or "")
            ).strip()
            rows.append(
                {
                    "section": f"{ch.entity_type}:{label or 'target'}",
                    "change_type": entity_bucket.get(ch.change_type, ch.change_type),
                    "snippet": (ch.content or "")[:400],
                }
            )
        return rows

    @staticmethod
    def submit_for_review(*, actor, pip: ProcessImprovementProposal):
        """Move Draft/Submitted retry → processing_galdr and enqueue Galdr."""
        from django.conf import settings

        from methodology.services.galdr_engine import GaldrEngine

        _pip_allow_submit_for_review(pip, actor)
        if not PipChange.objects.filter(pip=pip).exists():
            raise ValidationError("Add at least one Change before submitting.")
        pk_holder = pip.pk

        def _enqueue() -> None:
            GaldrEngine.schedule(pk_holder)

        now = timezone.now()
        with transaction.atomic():
            locked = ProcessImprovementProposal.objects.select_for_update().get(
                pk=pk_holder
            )
            _pip_allow_submit_for_review(locked, actor)
            if not PipChange.objects.filter(pip_id=locked.pk).exists():
                raise ValidationError("Add at least one Change before submitting.")
            locked.status = ProcessImprovementProposal.STATUS_PROCESSING_GALDR
            if locked.submitted_at is None:
                locked.submitted_at = now
            locked.save(
                update_fields=["status", "submitted_at", "updated_at"],
            )

        # Tests wrap each case in ambient transactions; ``on_commit`` would defer
        # until teardown. Production keeps the daemon thread tied to HTTP commits.
        if getattr(settings, "GALDR_EAGER", False):
            _enqueue()
        else:
            transaction.on_commit(_enqueue)
        logger.info("PIP queued for Galdr pk=%s", pk_holder)
        return ProcessImprovementProposal.objects.get(pk=pk_holder)
