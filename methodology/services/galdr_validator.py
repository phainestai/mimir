"""Pre-LLM structural validation for Galdr PIP assessments."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction

from methodology.models import PipChange, ProcessImprovementProposal
from methodology.services.pip_apply_changes_service import PipApplyChangesService
from methodology.services.pip_link_service import normalize_internal_ref

logger = logging.getLogger(__name__)


@dataclass
class StructuralReport:
    """Outcome of cheap structural checks before Galdr invokes an LLM."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


class GaldrStructuralValidator:
    """Validate that a PIP's changes can be applied without structural defects."""

    @classmethod
    def validate_pip_structure(cls, pip: ProcessImprovementProposal) -> StructuralReport:
        """
        Run structural checks on all changes in stable order.

        :param pip: Proposal in ``processing_galdr`` (or any status).
        :return: Report with blocking ``errors`` and non-blocking ``warnings``.
        """
        report = StructuralReport()
        changes = list(PipChange.objects.filter(pip=pip).order_by("order", "pk"))
        logger.info(
            "GaldrStructuralValidator pip id=%s change_count=%s",
            pip.pk,
            len(changes),
        )
        if not changes:
            report.errors.append("PIP has zero changes.")
            return report

        cls._check_duplicate_internal_refs(changes, report)
        if report.ok:
            cls._dry_run_apply(pip, changes, report)
        logger.info(
            "GaldrStructuralValidator pip id=%s ok=%s errors=%s warnings=%s",
            pip.pk,
            report.ok,
            len(report.errors),
            len(report.warnings),
        )
        return report

    @staticmethod
    def _check_duplicate_internal_refs(
        changes: list[PipChange],
        report: StructuralReport,
    ) -> None:
        seen: set[str] = set()
        for change in changes:
            if change.change_type != PipChange.CHANGE_ADD or not change.internal_ref:
                continue
            key = normalize_internal_ref(change.internal_ref)
            if key in seen:
                report.errors.append(f"Duplicate internal_ref '{key}'.")
            seen.add(key)

    @staticmethod
    def _dry_run_apply(
        pip: ProcessImprovementProposal,
        changes: list[PipChange],
        report: StructuralReport,
    ) -> None:
        try:
            with transaction.atomic():
                PipApplyChangesService.apply_changes(
                    pip=pip,
                    accepted=changes,
                    playbook=pip.playbook,
                )
                transaction.set_rollback(True)
        except ValidationError as exc:
            report.errors.append(str(exc))
            logger.info(
                "GaldrStructuralValidator dry-run failed pip id=%s: %s",
                pip.pk,
                exc,
            )
