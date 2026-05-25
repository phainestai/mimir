"""Galdr prompts and compact playbook summaries for Claude assessments."""

from __future__ import annotations

SYSTEM_PROMPT = """You are Galdr, an AI reviewer for playbook improvement proposals.
Assess whether each proposed change is consistent with the playbook's goals,
free of conflicts with existing entities, and structurally sound.

Respond ONLY with a JSON object — no prose, no markdown fences:
{"recommendation": "ACCEPT"|"REJECT"|"NEEDS_CLARIFICATION", "reasoning": "<one paragraph>"}
"""


def build_playbook_context_summary(playbook) -> str:
    """
    Build compact text summarising playbook structure for Galdr prompts.

    :param playbook: :class:`~methodology.models.Playbook` instance.
    :return: Multi-line textual outline of workflows and activities.
    """
    from methodology.models import Workflow

    lines = [
        f"Playbook: {playbook.name} v{playbook.version} (status={playbook.status})",
    ]
    for wf in Workflow.objects.filter(playbook=playbook).order_by("order", "pk"):
        lines.append(f"  Workflow [{wf.pk}] {wf.name} (#{wf.order})")
        for act in wf.activities.order_by("order", "pk"):
            lines.append(f"    Activity [{act.pk}] {act.name} (#{act.order})")
    return "\n".join(lines)


def build_change_prompt(change, context_summary: str) -> str:
    """
    Compose the user message assessing a single :class:`~methodology.models.PipChange`.

    :param change: PipChange row.
    :param context_summary: Output of :func:`build_playbook_context_summary`.
    :return: Full user prompt content.
    """
    from methodology.models import PipChange

    lines = [
        "Assess this single proposed playbook change.",
        "",
        "--- Playbook snapshot ---",
        context_summary,
        "",
        "--- Proposed change ---",
        f"change_type: {change.change_type}",
        f"entity_type: {change.entity_type}",
        f"name: {change.name or '(empty)'}",
        f"target_id: {change.target_id or '(none)'}",
        f"append_to_playbook_end: {change.append_to_playbook_end}",
        f"content / rationale:\n{change.content or '(empty)'}",
    ]
    if change.parent_workflow_id:
        lines.append(f"parent_workflow_id: {change.parent_workflow_id}")
    if change.change_type in {PipChange.CHANGE_LINK, PipChange.CHANGE_UNLINK}:
        lines.extend([
            f"relationship_type: {change.relationship_type}",
            f"source: {change.source_entity_type} {change.source_entity_ref}",
            f"target: {change.target_entity_type} {change.target_entity_ref}",
        ])
    if change.internal_ref:
        lines.append(f"internal_ref: {change.internal_ref}")
    if change.insert_after_activity_id:
        lines.append(f"insert_after_activity_id: {change.insert_after_activity_id}")
    return "\n".join(lines)
