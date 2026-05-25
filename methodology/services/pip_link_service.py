"""Validation and resolution helpers for LINK / UNLINK PIP changes."""

from __future__ import annotations

import logging
import re
from typing import Optional

from django.core.exceptions import ValidationError

from methodology.models import (
    Activity,
    ActivityWorkflowMembership,
    Agent,
    PipChange,
    ProcessImprovementProposal,
    Rule,
    Skill,
    Workflow,
)

logger = logging.getLogger(__name__)

_INTERNAL_REF_RE = re.compile(r"^#[A-Za-z0-9_-]+$")

_RELATIONSHIP_ENDPOINTS: dict[str, tuple[str, str]] = {
    PipChange.REL_SKILL_ACTIVITY: (PipChange.ENTITY_SKILL, PipChange.ENTITY_ACTIVITY),
    PipChange.REL_RULE_ACTIVITY: (PipChange.ENTITY_RULE, PipChange.ENTITY_ACTIVITY),
    PipChange.REL_AGENT_ACTIVITY: (PipChange.ENTITY_AGENT, PipChange.ENTITY_ACTIVITY),
    PipChange.REL_ACTIVITY_WORKFLOW: (PipChange.ENTITY_ACTIVITY, PipChange.ENTITY_WORKFLOW),
}


def normalize_internal_ref(raw: str) -> str:
    """Return canonical ``#label`` or empty string."""
    val = (raw or "").strip()
    if not val:
        return ""
    if not val.startswith("#"):
        val = f"#{val}"
    return val


def is_internal_ref(raw: str) -> bool:
    return bool(raw and str(raw).strip().startswith("#"))


def validate_internal_ref_label(raw: str) -> str:
    val = normalize_internal_ref(raw)
    if not val:
        raise ValidationError("internal_ref must be a non-empty #label.")
    if not _INTERNAL_REF_RE.match(val):
        raise ValidationError("internal_ref must match #letters-digits-underscore.")
    return val


def relationship_endpoint_types(relationship_type: str) -> tuple[str, str]:
    try:
        return _RELATIONSHIP_ENDPOINTS[relationship_type]
    except KeyError as exc:
        raise ValidationError(f"Invalid relationship_type '{relationship_type}'.") from exc


def resolve_entity_ref(
    *,
    ref: str,
    expected_type: str,
    playbook_id: int,
    ref_map: dict[str, tuple[str, int]],
) -> int:
    """
    Resolve ``ref`` to an integer pk — either direct id or ``#internal_ref`` from ``ref_map``.
    """
    raw = (ref or "").strip()
    if not raw:
        raise ValidationError(f"{expected_type} reference is required.")

    if is_internal_ref(raw):
        key = normalize_internal_ref(raw)
        hit = ref_map.get(key)
        if hit is None:
            raise ValidationError(f"Unresolved internal reference '{key}'.")
        etype, pk = hit
        if etype != expected_type:
            raise ValidationError(
                f"Internal ref '{key}' resolves to {etype}, expected {expected_type}."
            )
        logger.info("Resolved internal ref %s → %s pk=%s", key, etype, pk)
        return pk

    if not raw.isdigit():
        raise ValidationError(f"Invalid entity reference '{raw}' — use pk or #internal_ref.")
    pk = int(raw)
    _assert_entity_in_playbook(expected_type, pk, playbook_id)
    return pk


def _assert_entity_in_playbook(entity_type: str, pk: int, playbook_id: int) -> None:
    if entity_type == PipChange.ENTITY_ACTIVITY:
        act = Activity.objects.select_related("workflow").get(pk=pk)
        if act.workflow.playbook_id != playbook_id:
            raise ValidationError("Activity playbook mismatch.")
        return
    if entity_type == PipChange.ENTITY_WORKFLOW:
        wf = Workflow.objects.get(pk=pk)
        if wf.playbook_id != playbook_id:
            raise ValidationError("Workflow playbook mismatch.")
        return
    if entity_type == PipChange.ENTITY_SKILL:
        sk = Skill.objects.get(pk=pk)
        if sk.playbook_id != playbook_id:
            raise ValidationError("Skill playbook mismatch.")
        return
    if entity_type == PipChange.ENTITY_AGENT:
        ag = Agent.objects.get(pk=pk)
        if ag.playbook_id != playbook_id:
            raise ValidationError("Agent playbook mismatch.")
        return
    if entity_type == PipChange.ENTITY_RULE:
        ru = Rule.objects.get(pk=pk)
        if ru.playbook_id != playbook_id:
            raise ValidationError("Rule playbook mismatch.")
        return
    raise ValidationError(f"Unsupported entity type '{entity_type}'.")


def relationship_exists(
    *,
    relationship_type: str,
    source_id: int,
    target_id: int,
) -> bool:
    """Return True when the relationship is already present in live playbook data."""
    if relationship_type == PipChange.REL_SKILL_ACTIVITY:
        return Activity.objects.filter(pk=target_id, skills__pk=source_id).exists()
    if relationship_type == PipChange.REL_RULE_ACTIVITY:
        return Activity.objects.filter(pk=target_id, rules__pk=source_id).exists()
    if relationship_type == PipChange.REL_AGENT_ACTIVITY:
        act = Activity.objects.filter(pk=target_id).first()
        return act is not None and act.agent_id == source_id
    if relationship_type == PipChange.REL_ACTIVITY_WORKFLOW:
        act = Activity.objects.filter(pk=source_id).first()
        if act is None:
            return False
        if act.workflow_id == target_id:
            return True
        return ActivityWorkflowMembership.objects.filter(
            activity_id=source_id,
            workflow_id=target_id,
        ).exists()
    return False


def validate_link_change_for_persist(
    *,
    pip: ProcessImprovementProposal,
    change_type: str,
    relationship_type: str,
    source_entity_ref: str,
    target_entity_ref: str,
    order_hint: int,
) -> tuple[str, str, str, str, str]:
    """
    Validate LINK/UNLINK row before persist.

    Returns normalized (relationship_type, source_type, source_ref, target_type, target_ref).
    """
    ct = change_type.upper().strip()
    if ct not in {PipChange.CHANGE_LINK, PipChange.CHANGE_UNLINK}:
        raise ValidationError("change_type must be LINK or UNLINK.")

    rel = relationship_type.strip()
    src_type, tgt_type = relationship_endpoint_types(rel)
    src_ref = (source_entity_ref or "").strip()
    tgt_ref = (target_entity_ref or "").strip()
    if not src_ref or not tgt_ref:
        raise ValidationError("Source and target references are required for LINK/UNLINK.")

    src_pending = _validate_endpoint_ref(
        pip=pip,
        ref=src_ref,
        expected_type=src_type,
        before_order=order_hint,
        playbook_id=pip.playbook_id,
    )
    tgt_pending = _validate_endpoint_ref(
        pip=pip,
        ref=tgt_ref,
        expected_type=tgt_type,
        before_order=order_hint,
        playbook_id=pip.playbook_id,
    )

    if not src_pending and not tgt_pending:
        src_id = resolve_entity_ref(
            ref=src_ref,
            expected_type=src_type,
            playbook_id=pip.playbook_id,
            ref_map={},
        )
        tgt_id = resolve_entity_ref(
            ref=tgt_ref,
            expected_type=tgt_type,
            playbook_id=pip.playbook_id,
            ref_map={},
        )
        exists = relationship_exists(
            relationship_type=rel,
            source_id=src_id,
            target_id=tgt_id,
        )
        if ct == PipChange.CHANGE_LINK and exists:
            raise ValidationError("Relationship already exists — duplicate LINK rejected.")
        if ct == PipChange.CHANGE_UNLINK and not exists:
            raise ValidationError("Relationship does not exist — cannot UNLINK.")
        _validate_activity_workflow_constraints(
            rel=rel,
            ct=ct,
            source_id=src_id,
            target_id=tgt_id,
        )

    logger.info(
        "Validated %s %s src=%s tgt=%s pip=%s pending=%s/%s",
        ct,
        rel,
        src_ref,
        tgt_ref,
        pip.pk,
        src_pending,
        tgt_pending,
    )
    return rel, src_type, src_ref, tgt_type, tgt_ref


def _validate_endpoint_ref(
    *,
    pip: ProcessImprovementProposal,
    ref: str,
    expected_type: str,
    before_order: int,
    playbook_id: int,
) -> bool:
    """Return True when ref is a pending internal_ref to a prior ADD row."""
    if is_internal_ref(ref):
        key = normalize_internal_ref(ref)
        for ch in PipChange.objects.filter(pip=pip, order__lt=before_order).order_by("order", "pk"):
            if (
                ch.change_type == PipChange.CHANGE_ADD
                and normalize_internal_ref(ch.internal_ref) == key
            ):
                if ch.entity_type != expected_type:
                    raise ValidationError(
                        f"Internal ref '{key}' is ADD {ch.entity_type}, expected {expected_type}."
                    )
                return True
        raise ValidationError(
            f"Internal ref '{key}' must reference an earlier ADD change in this PIP."
        )
    if not ref.isdigit():
        raise ValidationError(f"Invalid entity reference '{ref}' — use pk or #internal_ref.")
    _assert_entity_in_playbook(expected_type, int(ref), playbook_id)
    return False


def _validate_activity_workflow_constraints(
    *,
    rel: str,
    ct: str,
    source_id: int,
    target_id: int,
) -> None:
    if rel != PipChange.REL_ACTIVITY_WORKFLOW:
        return
    act = Activity.objects.get(pk=source_id)
    if ct == PipChange.CHANGE_UNLINK and act.workflow_id == target_id:
        raise ValidationError(
            "Cannot UNLINK primary workflow — activity home workflow is immutable via PIP."
        )
    if ct == PipChange.CHANGE_LINK and act.workflow_id == target_id:
        raise ValidationError(
            "Activity already belongs to this workflow as its primary home."
        )


def _build_pending_ref_map(
    pip: ProcessImprovementProposal,
    applied_add_refs: dict[str, tuple[str, int]],
) -> dict[str, tuple[str, int]]:
    """Merge in-flight applied ADD refs with any pre-existing target_id on ADD rows."""
    ref_map = dict(applied_add_refs)
    for ch in PipChange.objects.filter(pip=pip).order_by("order", "pk"):
        if ch.change_type != PipChange.CHANGE_ADD or not ch.internal_ref:
            continue
        key = normalize_internal_ref(ch.internal_ref)
        if ch.target_id and key not in ref_map:
            ref_map[key] = (ch.entity_type, ch.target_id)
    return ref_map


def link_change_summary_label(change: PipChange) -> str:
    """Human-readable label for preview / admin summary."""
    rel = change.relationship_type or "link"
    return (
        f"{change.source_entity_type}:{change.source_entity_ref} → "
        f"{change.target_entity_type}:{change.target_entity_ref} ({rel})"
    )
