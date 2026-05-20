"""Email notifications after a PIP is finalised by an administrator."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from methodology.models import PipChange, ProcessImprovementProposal

logger = logging.getLogger(__name__)


def _summarise_decisions(pip: ProcessImprovementProposal) -> tuple[str, str]:
    """Return `(verdict_keyword, headline)` used for subjects and banners."""
    changes = list(pip.changes.order_by("order", "pk"))
    accept_ct = sum(1 for ch in changes if ch.admin_decision == PipChange.ADMIN_ACCEPT)
    reject_ct = sum(1 for ch in changes if ch.admin_decision == PipChange.ADMIN_REJECT)
    total = len(changes)

    if total == 0:
        return ("none", "No changes were recorded.")

    if accept_ct == total:
        return ("accepted", "Accepted")
    if reject_ct == total:
        return ("rejected", "Rejected")
    return ("partial", "Partially accepted")


def _subject_line(pip: ProcessImprovementProposal, verdict_kw: str) -> str:
    title = pip.title.strip() or "Untitled"
    if verdict_kw == "accepted":
        return f'Your PIP "{title}" — Accepted ✓'
    if verdict_kw == "rejected":
        return f'Your PIP "{title}" — Rejected ✗'
    return f'Your PIP "{title}" — Partially accepted'


def send_decision_email(pip: ProcessImprovementProposal) -> None:
    """
    Notify the submitter after admin decisions are persisted.

    :param pip: Finalised proposal with populated ``changes.admin_decision``.
    """
    submitter = pip.created_by
    if submitter is None or not getattr(submitter, "email", None):
        logger.info(
            "Skipping PIP decision email pip_id=%s (no recipient email)", pip.pk
        )
        return

    verdict_kw, verdict_label = _summarise_decisions(pip)
    subject = _subject_line(pip, verdict_kw)
    pv = pip.playbook_versions.order_by("-version_number").first()
    context = {
        "pip": pip,
        "changes": pip.changes.order_by("order", "pk"),
        "verdict": verdict_label,
        "new_version": str(pv.version_number) if pv else "",
        "version_bump": bool(pv),
    }
    body = render_to_string("pips/email_decision.txt", context)
    sender = getattr(
        settings, "DEFAULT_FROM_EMAIL", "noreply@mimir.local"
    )
    logger.info(
        "Sending PIP decision email pip_id=%s to=%s verdict=%s",
        pip.pk,
        submitter.email,
        verdict_kw,
    )
    try:
        send_mail(subject, body, sender, [submitter.email], fail_silently=False)
    except Exception:
        logger.exception(
            "Failed to send PIP decision email pip_id=%s to=%s — email skipped",
            pip.pk,
            submitter.email,
        )

