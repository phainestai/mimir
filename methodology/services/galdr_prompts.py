"""Galdr prompts and compact playbook summaries for Claude assessments."""

from __future__ import annotations

SYSTEM_PROMPT = """You are Galdr, an AI reviewer for playbook improvement proposals.
Assess whether each proposed change is consistent with the playbook's goals,
free of conflicts with existing entities, and structurally sound.

Respond ONLY with a JSON object — no prose, no markdown fences:
{"recommendation": "ACCEPT"|"REJECT"|"NEEDS_CLARIFICATION", "reasoning": "<one paragraph>"}
"""

HOLISTIC_SYSTEM_PROMPT = """You are Galdr, an AI reviewer for playbook improvement proposals.
Evaluate the FULL proposed PIP holistically: assess whether the TARGET STATE (after all
changes are applied in order) is architecturally coherent, then provide per-change diagnostics
in that full context — not against the current state in isolation.

Respond ONLY with a JSON object — no prose, no markdown fences:
{
  "holistic_assessment": {
    "overall_coherence": "COHERENT"|"INCOHERENT",
    "reasoning": "<one paragraph>"
  },
  "change_assessments": [
    {"change_id": <int>, "recommendation": "ACCEPT"|"REJECT"|"NEEDS_CLARIFICATION", "reasoning": "<one paragraph>"}
  ]
}
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


def build_extended_playbook_summary(playbook) -> str:
    """
    Build a richer playbook outline including skills, agents, rules, and links.

    :param playbook: :class:`~methodology.models.Playbook` instance.
    :return: Multi-line textual outline for Galdr target-state context.
    """
    from methodology.models import Activity, Agent, Rule, Skill, Workflow

    lines = [build_playbook_context_summary(playbook), "", "--- Skills ---"]
    for sk in Skill.objects.filter(playbook=playbook).order_by("pk"):
        lines.append(f"  Skill [{sk.pk}] {sk.title}")

    lines.append("")
    lines.append("--- Agents ---")
    for ag in Agent.objects.filter(playbook=playbook).order_by("pk"):
        lines.append(f"  Agent [{ag.pk}] {ag.name}")

    lines.append("")
    lines.append("--- Rules ---")
    for ru in Rule.objects.filter(playbook=playbook).order_by("pk"):
        lines.append(f"  Rule [{ru.pk}] {ru.title}")

    lines.append("")
    lines.append("--- Skill → Activity links ---")
    for act in (
        Activity.objects.filter(workflow__playbook=playbook)
        .prefetch_related("skills")
        .order_by("workflow__order", "order", "pk")
    ):
        for sk in act.skills.all():
            lines.append(f"  Skill [{sk.pk}] → Activity [{act.pk}] {act.name}")

    lines.append("")
    lines.append("--- Workflows (detail) ---")
    for wf in Workflow.objects.filter(playbook=playbook).order_by("order", "pk"):
        lines.append(f"  Workflow [{wf.pk}] {wf.name}: {wf.description[:120]}")
    return "\n".join(lines)


def _format_change_list(changes) -> str:
    blocks: list[str] = []
    for change in changes:
        header = (
            f"Change [{change.pk}] order={change.order} "
            f"{change.change_type} {change.entity_type or change.relationship_type}"
        )
        body_lines = [header, f"  name: {change.name or '(empty)'}"]
        if change.target_id:
            body_lines.append(f"  target_id: {change.target_id}")
        if change.content:
            body_lines.append(f"  content: {change.content[:500]}")
        if change.internal_ref:
            body_lines.append(f"  internal_ref: {change.internal_ref}")
        if change.change_type in {"LINK", "UNLINK"}:
            body_lines.append(
                f"  link: {change.source_entity_ref} → {change.target_entity_ref}"
            )
        blocks.append("\n".join(body_lines))
    return "\n\n".join(blocks)


def build_target_state_prompt(
    pip,
    current_summary: str,
    target_summary: str,
    changes,
) -> str:
    """
    Compose holistic Galdr user message with current + target state context.

    :param pip: Parent :class:`~methodology.models.ProcessImprovementProposal`.
    :param current_summary: Pre-change playbook outline.
    :param target_summary: Post-apply playbook outline from dry-run.
    :param changes: Ordered PipChange queryset or list.
    :return: Full user prompt for holistic assessment.
    """
    return "\n".join([
        f"Assess PIP [{pip.pk}] \"{pip.title}\" holistically.",
        f"Summary: {pip.summary or '(none)'}",
        "",
        "--- Current Playbook State ---",
        current_summary,
        "",
        "--- Target State After All Changes ---",
        target_summary,
        "",
        "--- Proposed Changes (in order) ---",
        _format_change_list(changes),
        "",
        "Evaluate target-state coherence first, then per-change recommendations "
        "in the context of the full PIP.",
    ])


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
