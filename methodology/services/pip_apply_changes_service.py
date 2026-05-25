"""Apply accepted :class:`~methodology.models.PipChange` rows to playbook data."""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db.models import Max

from methodology.models import (
    Activity,
    Agent,
    Artifact,
    PipChange,
    Rule,
    Skill,
    Workflow,
)
from methodology.services.activity_service import ActivityService
from methodology.services.pip_link_service import (
    link_change_summary_label,
    normalize_internal_ref,
    relationship_exists,
    resolve_entity_ref,
)
from methodology.services.workflow_service import WorkflowService

if TYPE_CHECKING:
    from methodology.models import Playbook, ProcessImprovementProposal

logger = logging.getLogger(__name__)


class PipApplyChangesService:
    """Routes typed deltas to playbook mutations."""

    @staticmethod
    def apply_changes(
        *,
        pip: ProcessImprovementProposal,
        accepted: list[PipChange],
        playbook: Playbook,
    ) -> None:
        """
        Apply accepted changes to the playbook in stable order.

        :param pip: Parent proposal (audit context).
        :param accepted: Ordered list accepted by administrators.
        :param playbook: Target released playbook row.
        :raises ValidationError: if a change cannot be applied safely.
        """
        ref_map: dict[str, tuple[str, int]] = {}
        for change in sorted(accepted, key=lambda c: (c.order, c.pk)):
            PipApplyChangesService._apply_single_change(
                pip=pip,
                playbook=playbook,
                change=change,
                ref_map=ref_map,
            )

    @staticmethod
    def _apply_single_change(
        *,
        pip: ProcessImprovementProposal,
        playbook: Playbook,
        change: PipChange,
        ref_map: dict[str, tuple[str, int]],
    ) -> None:
        ct = change.change_type
        et = change.entity_type
        if ct == PipChange.CHANGE_ADD:
            created_pk = PipApplyChangesService._apply_add(
                playbook=playbook,
                change=change,
                pip_pk=pip.pk,
            )
            if change.internal_ref and created_pk is not None:
                key = normalize_internal_ref(change.internal_ref)
                ref_map[key] = (change.entity_type, created_pk)
                logger.info(
                    "PIP apply registered internal_ref %s → %s pk=%s",
                    key,
                    change.entity_type,
                    created_pk,
                )
            return
        if ct == PipChange.CHANGE_ALTER:
            PipApplyChangesService._apply_alter(
                playbook=playbook,
                entity_type=et,
                change=change,
                pip_pk=pip.pk,
            )
            return
        if ct == PipChange.CHANGE_DROP:
            PipApplyChangesService._apply_drop(
                playbook=playbook,
                entity_type=et,
                change=change,
                pip_pk=pip.pk,
            )
            return
        if ct in {PipChange.CHANGE_LINK, PipChange.CHANGE_UNLINK}:
            PipApplyChangesService._apply_link_or_unlink(
                playbook=playbook,
                change=change,
                ref_map=ref_map,
                pip_pk=pip.pk,
            )
            return
        raise ValidationError(f"Unknown change_type {ct}.")

    @staticmethod
    def _apply_add(
        *,
        playbook: Playbook,
        change: PipChange,
        pip_pk: int,
    ) -> int | None:
        et = change.entity_type
        if et == PipChange.ENTITY_ACTIVITY:
            parent = change.parent_workflow
            if parent is None or parent.playbook_id != playbook.pk:
                raise ValidationError("ADD Activity requires parent_workflow in target playbook.")
            name = change.name.strip()
            if not name:
                raise ValidationError("ADD Activity requires a name.")
            guidance_body = (
                change.content.strip() if change.content and change.content.strip() else "## TBD"
            )
            if change.append_to_playbook_end or change.insert_after_activity_id is None:
                agg = Activity.objects.filter(workflow_id=parent.pk).aggregate(
                    m=Max("order"),
                )
                next_order = int(agg["m"] or 0) + 1
            else:
                after = change.insert_after_activity
                if (
                    after is None
                    or after.workflow_id != parent.pk
                ):
                    raise ValidationError("Insert-after activity mismatch.")
                _bump_orders_after_activity(after.workflow_id, after.order)
                next_order = after.order + 1
            act = Activity.objects.create(
                workflow=parent,
                name=name[:200],
                guidance=guidance_body,
                order=next_order,
            )
            logger.info(
                "PIP apply ADD Activity pk=%s pip=%s workflow=%s order=%s",
                act.pk,
                pip_pk,
                parent.pk,
                next_order,
            )
            return act.pk

        if et == PipChange.ENTITY_WORKFLOW:
            name = change.name.strip()
            if not name:
                raise ValidationError("ADD Workflow requires a name.")
            agg = Workflow.objects.filter(playbook_id=playbook.pk).aggregate(m=Max("order"))
            next_order = int(agg["m"] or 0) + 1
            wf = Workflow.objects.create(
                playbook=playbook,
                name=name[:100],
                description=(change.content or "")[:500],
                order=next_order,
                abbreviation="",
            )
            logger.info(
                "PIP apply ADD Workflow pk=%s pip=%s order=%s",
                wf.pk,
                pip_pk,
                next_order,
            )
            return wf.pk

        if et == PipChange.ENTITY_SKILL:
            title = change.name.strip()
            if not title:
                raise ValidationError("ADD Skill requires a name/title.")
            sk = Skill.objects.create(
                playbook=playbook,
                title=title[:200],
                content=change.content.strip(),
            )
            logger.info("PIP apply ADD Skill pk=%s pip=%s", sk.pk, pip_pk)
            return sk.pk

        if et == PipChange.ENTITY_AGENT:
            name = change.name.strip()
            if not name:
                raise ValidationError("ADD Agent requires a name.")
            ag = Agent.objects.create(
                playbook=playbook,
                name=name[:200],
                description=change.content.strip(),
            )
            logger.info("PIP apply ADD Agent pk=%s pip=%s", ag.pk, pip_pk)
            return ag.pk

        if et == PipChange.ENTITY_RULE:
            title = change.name.strip()
            if not title:
                raise ValidationError("ADD Rule requires a name/title.")
            from django.utils.text import slugify

            base_slug = slugify(title)[:200] or "rule"
            slug = base_slug
            n = 1
            while Rule.objects.filter(playbook=playbook, slug=slug).exists():
                slug = f"{base_slug}-{n}"[:220]
                n += 1
            ru = Rule.objects.create(
                playbook=playbook,
                title=title[:200],
                slug=slug,
                content=change.content.strip(),
            )
            logger.info("PIP apply ADD Rule pk=%s pip=%s", ru.pk, pip_pk)
            return ru.pk

        if et == PipChange.ENTITY_ARTIFACT:
            raise ValidationError(
                "ADD Artifact via PIP is not supported yet (producer activity unknown)."
            )
        raise ValidationError(f"Unsupported ADD entity '{et}'.")

    @staticmethod
    def _apply_link_or_unlink(
        *,
        playbook: Playbook,
        change: PipChange,
        ref_map: dict[str, tuple[str, int]],
        pip_pk: int,
    ) -> None:
        rel = change.relationship_type
        src_id = resolve_entity_ref(
            ref=change.source_entity_ref,
            expected_type=change.source_entity_type,
            playbook_id=playbook.pk,
            ref_map=ref_map,
        )
        tgt_id = resolve_entity_ref(
            ref=change.target_entity_ref,
            expected_type=change.target_entity_type,
            playbook_id=playbook.pk,
            ref_map=ref_map,
        )
        is_link = change.change_type == PipChange.CHANGE_LINK
        exists = relationship_exists(
            relationship_type=rel,
            source_id=src_id,
            target_id=tgt_id,
        )
        if is_link and exists:
            logger.info(
                "PIP apply LINK skipped duplicate %s pip=%s",
                link_change_summary_label(change),
                pip_pk,
            )
            return
        if not is_link and not exists:
            raise ValidationError(
                f"UNLINK target relationship missing: {link_change_summary_label(change)}"
            )

        if rel == PipChange.REL_SKILL_ACTIVITY:
            if is_link:
                ActivityService.add_activity_skill(tgt_id, src_id)
            else:
                ActivityService.remove_activity_skill(tgt_id, src_id)
        elif rel == PipChange.REL_RULE_ACTIVITY:
            if is_link:
                ActivityService.add_activity_rule(tgt_id, src_id)
            else:
                ActivityService.remove_activity_rule(tgt_id, src_id)
        elif rel == PipChange.REL_AGENT_ACTIVITY:
            if is_link:
                ActivityService.set_activity_agent(tgt_id, src_id)
            else:
                ActivityService.clear_activity_agent(tgt_id)
        elif rel == PipChange.REL_ACTIVITY_WORKFLOW:
            if is_link:
                WorkflowService.add_activity_to_workflow(src_id, tgt_id, order=change.order)
            else:
                WorkflowService.remove_activity_from_workflow(src_id, tgt_id)
        else:
            raise ValidationError(f"Unsupported relationship_type '{rel}'.")

        logger.info(
            "PIP apply %s %s pip=%s src=%s tgt=%s",
            change.change_type,
            rel,
            pip_pk,
            src_id,
            tgt_id,
        )

    @staticmethod
    def _apply_alter(
        *,
        playbook: Playbook,
        entity_type: str,
        change: PipChange,
        pip_pk: int,
    ) -> None:
        cid = change.target_id
        if cid is None:
            raise ValidationError("ALTER requires target_id.")

        body = change.content.strip() if change.content else ""

        if entity_type == PipChange.ENTITY_ACTIVITY:
            act = Activity.objects.select_related("workflow").get(pk=cid)
            if act.workflow.playbook_id != playbook.pk:
                raise ValidationError("Activity not in playbook.")
            if body:
                act.guidance = body
            if change.name.strip():
                act.name = change.name.strip()[:200]
            act.save(update_fields=["guidance", "name", "updated_at"])
            logger.info("PIP apply ALTER Activity pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_WORKFLOW:
            wf = Workflow.objects.get(pk=cid)
            if wf.playbook_id != playbook.pk:
                raise ValidationError("Workflow playbook mismatch.")
            wf.description = (body or wf.description or "")[:500]
            wf.save(update_fields=["description", "updated_at"])
            logger.info("PIP apply ALTER Workflow pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_SKILL:
            sk = Skill.objects.get(pk=cid)
            if sk.playbook_id != playbook.pk:
                raise ValidationError("Skill playbook mismatch.")
            if change.name.strip():
                sk.title = change.name.strip()[:200]
            if body:
                sk.content = body
            sk.save(update_fields=["title", "content", "updated_at"])
            logger.info("PIP apply ALTER Skill pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_AGENT:
            ag = Agent.objects.get(pk=cid)
            if ag.playbook_id != playbook.pk:
                raise ValidationError("Agent playbook mismatch.")
            if body:
                ag.description = body
            if change.name.strip():
                ag.name = change.name.strip()[:200]
            ag.save(update_fields=["description", "name", "updated_at"])
            logger.info("PIP apply ALTER Agent pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_ARTIFACT:
            art = Artifact.objects.get(pk=cid)
            if art.playbook_id != playbook.pk:
                raise ValidationError("Artifact playbook mismatch.")
            art.description = body or art.description or ""
            art.save(update_fields=["description", "updated_at"])
            logger.info("PIP apply ALTER Artifact pk=%s pip=%s", cid, pip_pk)
            return

        raise ValidationError(f"Unsupported ALTER entity '{entity_type}'.")

    @staticmethod
    def _apply_drop(
        *,
        playbook: Playbook,
        entity_type: str,
        change: PipChange,
        pip_pk: int,
    ) -> None:
        cid = change.target_id
        if cid is None:
            raise ValidationError("DROP requires target_id.")

        if entity_type == PipChange.ENTITY_ACTIVITY:
            act = Activity.objects.select_related("workflow").get(pk=cid)
            if act.workflow.playbook_id != playbook.pk:
                raise ValidationError("Activity not in playbook.")
            wf_id = act.workflow_id
            act.delete()
            _renormalize_activity_orders(wf_id)
            logger.info("PIP apply DROP Activity pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_WORKFLOW:
            wf = Workflow.objects.get(pk=cid, playbook_id=playbook.pk)
            wf_pk = wf.pk
            wf.delete()
            logger.info("PIP apply DROP Workflow pk=%s pip=%s", wf_pk, pip_pk)
            return

        if entity_type == PipChange.ENTITY_SKILL:
            Skill.objects.filter(pk=cid, playbook_id=playbook.pk).delete()
            logger.info("PIP apply DROP Skill pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_AGENT:
            Agent.objects.filter(pk=cid, playbook_id=playbook.pk).delete()
            logger.info("PIP apply DROP Agent pk=%s pip=%s", cid, pip_pk)
            return

        if entity_type == PipChange.ENTITY_ARTIFACT:
            Artifact.objects.filter(pk=cid, playbook_id=playbook.pk).delete()
            logger.info("PIP apply DROP Artifact pk=%s pip=%s", cid, pip_pk)
            return

        raise ValidationError(f"Unsupported DROP entity '{entity_type}'.")


def _bump_orders_after_activity(workflow_id: int, after_order: int) -> None:
    """Shift ``order`` for activities strictly after ``after_order`` (stable)."""
    to_shift = Activity.objects.filter(
        workflow_id=workflow_id,
        order__gt=after_order,
    ).order_by("-order")
    for act in to_shift:
        Activity.objects.filter(pk=act.pk).update(order=act.order + 1)


def _renormalize_activity_orders(workflow_id: int) -> None:
    """After deletes, consolidate ``order`` to 1…N gaps."""
    items = list(
        Activity.objects.filter(workflow_id=workflow_id).order_by("order", "pk")
    )
    for idx, act in enumerate(items, start=1):
        if act.order != idx:
            Activity.objects.filter(pk=act.pk).update(order=idx)


def bump_playbook_major_version_after_pip_apply(
    *,
    pip: ProcessImprovementProposal,
    playbook,
    actor,
    summary_line: str,
) -> Decimal:
    """
    Record Playbook history line and bump to next major revision.

    Examples: ``1.0 -> 2.0``, ``1.9 -> 2.0``.
    """
    from methodology.models import PlaybookVersion
    from methodology.models.playbook_version import VersionSource

    playbook.refresh_from_db()
    previous = playbook.version
    next_ver = playbook.compute_next_major_line_version()
    playbook.version = next_ver
    playbook.save(update_fields=["version", "updated_at"])
    summary = summary_line.strip() or "PIP applied — playbook revised."
    PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=next_ver,
        snapshot_data={
            "pip_id": pip.pk,
            "playbook_name": playbook.name,
            "version_before": str(previous),
            "version_after": str(next_ver),
        },
        change_summary=summary[:500],
        description=summary[:500],
        is_major=True,
        source=VersionSource.PIP_SOURCE,
        pip=pip,
        created_by=actor,
    )
    logger.info(
        "Playbook pk=%s PIP-major bump %s→%s via pip=%s",
        playbook.pk,
        previous,
        next_ver,
        pip.pk,
    )
    return next_ver
