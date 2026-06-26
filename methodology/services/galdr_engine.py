"""Galdr playbook assessment runner (daemon thread MVP + Anthropic staging)."""

from __future__ import annotations

import logging
import threading

from django.conf import settings
from django.db import close_old_connections, transaction
from django.utils import timezone

from methodology.models import PipChange, ProcessImprovementProposal

logger = logging.getLogger(__name__)


class GaldrEngine:
    """Background worker transitioning ``processing_galdr → reviewed``."""

    REC_CODE = {
        "ACCEPT": PipChange.GALDR_ACCEPT,
        "REJECT": PipChange.GALDR_REJECT,
        "NEEDS_CLARIFICATION": PipChange.GALDR_NEEDS_CLARIFICATION,
    }

    @classmethod
    def schedule(cls, pip_id: int) -> None:
        """Fire-and-forget thread; survives the HTTP response lifecycle."""
        if getattr(settings, "GALDR_EAGER", False):
            try:
                cls.assess_sync(pip_id)
            except ProcessImprovementProposal.DoesNotExist:
                logger.error("Galdr eager: missing pip id=%s", pip_id)
            except Exception:
                logger.exception("Galdr eager failure pip id=%s", pip_id)
            return

        def _runner() -> None:
            close_old_connections()
            try:
                cls.assess_sync(pip_id)
            except ProcessImprovementProposal.DoesNotExist:
                logger.error("Galdr: missing pip id=%s", pip_id)
            except Exception:
                logger.exception("Galdr: unhandled failure pip id=%s", pip_id)

        threading.Thread(
            target=_runner,
            name=f"galdr-pip-{pip_id}",
            daemon=True,
        ).start()
        logger.info("GaldrEngine.schedule dispatched pip id=%s", pip_id)

    @classmethod
    def _mark_submitted_retry(cls, pip_id: int) -> None:
        """Return PIP to Submitted state when synchronous assessment fails."""
        cls._rollback_to_submitted(pip_id, holistic_note="")

    @classmethod
    def _mark_submitted_with_errors(cls, pip_id: int, errors: list[str]) -> None:
        """Return PIP to Submitted after structural validation failures."""
        note = f"Structural validation failed: {'; '.join(errors)}"
        cls._rollback_to_submitted(pip_id, holistic_note=note)

    @classmethod
    def _rollback_to_submitted(cls, pip_id: int, *, holistic_note: str) -> None:
        try:
            with transaction.atomic():
                locked = ProcessImprovementProposal.objects.select_for_update().get(
                    pk=pip_id
                )
                if locked.status == ProcessImprovementProposal.STATUS_PROCESSING_GALDR:
                    locked.status = ProcessImprovementProposal.STATUS_SUBMITTED
                    update_fields = ["status", "updated_at"]
                    if holistic_note:
                        locked.galdr_holistic_assessment = holistic_note[:2000]
                        update_fields.append("galdr_holistic_assessment")
                    locked.save(update_fields=update_fields)
                    logger.warning(
                        "Galdr pip id=%s rolled back → submitted%s",
                        pip_id,
                        " (structural errors)" if holistic_note else " for retry",
                    )
        except ProcessImprovementProposal.DoesNotExist:
            logger.warning("Galdr failure handler: pip id=%s missing", pip_id)

    @classmethod
    def assess_sync(cls, pip_id: int) -> None:
        """
        Blocking assessment used by daemon thread and ``manage.py run_galdr``.

        Performs LLM turns **outside** DB locks to avoid holding rows open.
        """
        if getattr(settings, "GALDR_USE_TARGET_STATE", False):
            cls._assess_sync_holistic(pip_id)
        else:
            cls._assess_sync_per_change(pip_id)

    @classmethod
    def _assess_sync_per_change(cls, pip_id: int) -> None:
        from methodology.services.galdr_client import GaldrLLMError, get_galdr_client
        from methodology.services.galdr_prompts import (
            build_change_prompt,
            build_playbook_context_summary,
        )

        bootstrap = ProcessImprovementProposal.objects.select_related("playbook").get(
            pk=pip_id
        )
        if bootstrap.status != ProcessImprovementProposal.STATUS_PROCESSING_GALDR:
            logger.info(
                "Galdr skipped pip id=%s unexpected status=%s",
                pip_id,
                bootstrap.status,
            )
            return

        playbook = bootstrap.playbook
        summary_text = build_playbook_context_summary(playbook)
        client = get_galdr_client()

        payloads: list[tuple[int, str, str]] = []
        try:
            qs = PipChange.objects.filter(pip_id=pip_id).order_by("order", "pk")
            if not qs.exists():
                raise GaldrLLMError("PIP has zero changes.")

            for change in qs.iterator():
                user_prompt = build_change_prompt(change, summary_text)
                rec_text, reasoning = client.evaluate_change(user_prompt)
                rec_upper = rec_text.upper()
                if rec_upper not in cls.REC_CODE:
                    raise GaldrLLMError(f"Unsupported recommendation '{rec_text}'.")
                payloads.append((change.pk, rec_upper, reasoning))
        except GaldrLLMError as exc:
            logger.warning("Galdr assess LLM phase failed pip id=%s: %s", pip_id, exc)
            cls._mark_submitted_retry(pip_id)
            return
        except Exception:
            logger.exception("Galdr assess unexpected pip id=%s", pip_id)
            cls._mark_submitted_retry(pip_id)
            return

        cls._persist_recommendations(pip_id, payloads, holistic_note="")

    @classmethod
    def _assess_sync_holistic(cls, pip_id: int) -> None:
        from methodology.services.galdr_client import GaldrLLMError, get_galdr_client
        from methodology.services.galdr_prompts import (
            build_playbook_context_summary,
            build_target_state_prompt,
        )
        from methodology.services.galdr_validator import GaldrStructuralValidator
        from methodology.services.pip_apply_changes_service import PipApplyChangesService

        bootstrap = ProcessImprovementProposal.objects.select_related("playbook").get(
            pk=pip_id
        )
        if bootstrap.status != ProcessImprovementProposal.STATUS_PROCESSING_GALDR:
            logger.info(
                "Galdr holistic skipped pip id=%s unexpected status=%s",
                pip_id,
                bootstrap.status,
            )
            return

        playbook = bootstrap.playbook
        changes = list(
            PipChange.objects.filter(pip_id=pip_id).order_by("order", "pk"),
        )

        structural = GaldrStructuralValidator.validate_pip_structure(bootstrap)
        if not structural.ok:
            cls._mark_submitted_with_errors(pip_id, structural.errors)
            return

        try:
            current_summary = build_playbook_context_summary(playbook)
            target_summary = PipApplyChangesService.build_target_state_summary(
                pip=bootstrap,
                playbook=playbook,
            )
            prompt = build_target_state_prompt(
                bootstrap,
                current_summary,
                target_summary,
                changes,
            )
            client = get_galdr_client()
            holistic, payloads = client.evaluate_pip_holistically(prompt)
        except GaldrLLMError as exc:
            logger.warning(
                "Galdr holistic LLM phase failed pip id=%s: %s",
                pip_id,
                exc,
            )
            cls._mark_submitted_retry(pip_id)
            return
        except Exception:
            logger.exception("Galdr holistic unexpected pip id=%s", pip_id)
            cls._mark_submitted_retry(pip_id)
            return

        for _cid, rec_upper, _why in payloads:
            if rec_upper not in cls.REC_CODE:
                logger.warning(
                    "Galdr holistic unsupported recommendation pip id=%s rec=%s",
                    pip_id,
                    rec_upper,
                )
                cls._mark_submitted_retry(pip_id)
                return

        holistic_note = (
            f"{holistic['overall_coherence']}: {holistic['reasoning']}"
        )
        cls._persist_recommendations(pip_id, payloads, holistic_note=holistic_note)

    @classmethod
    def _persist_recommendations(
        cls,
        pip_id: int,
        payloads: list[tuple[int, str, str]],
        *,
        holistic_note: str,
    ) -> None:
        try:
            with transaction.atomic():
                pip = ProcessImprovementProposal.objects.select_for_update().get(
                    pk=pip_id
                )
                if pip.status != ProcessImprovementProposal.STATUS_PROCESSING_GALDR:
                    logger.info(
                        "Galdr aborted save pip id=%s status changed to=%s",
                        pip_id,
                        pip.status,
                    )
                    return
                for cid, code, reasoning in payloads:
                    rec_value = cls.REC_CODE[code]
                    PipChange.objects.filter(pk=cid).update(
                        galdr_recommendation=rec_value,
                        galdr_reasoning=reasoning,
                        updated_at=timezone.now(),
                    )
                pip.status = ProcessImprovementProposal.STATUS_REVIEWED
                pip.reviewed_at = timezone.now()
                update_fields = ["status", "reviewed_at", "updated_at"]
                if holistic_note:
                    pip.galdr_holistic_assessment = holistic_note[:2000]
                    update_fields.append("galdr_holistic_assessment")
                pip.save(update_fields=update_fields)
                logger.info("Galdr persisted pip id=%s → reviewed", pip_id)
        except Exception:
            logger.exception("Galdr DB persist pip id=%s", pip_id)
            cls._mark_submitted_retry(pip_id)
