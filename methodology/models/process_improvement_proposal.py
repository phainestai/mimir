"""
Playbook Improvement Proposal (PIP) lifecycle model.

Statuses follow Act 9 (docs/features/act-9-pips/): draft → submitted → reviewed → decided.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class ProcessImprovementProposal(models.Model):
    """Structured change proposal targeting exactly one Released playbook."""

    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_PROCESSING_GALDR = "processing_galdr"
    STATUS_REVIEWED = "reviewed"
    STATUS_ACCEPTED = "accepted"
    STATUS_ACCEPTED_PARTIAL = "accepted_partial"
    STATUS_REJECTED = "rejected"
    STATUS_WITHDRAWN = "withdrawn"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SUBMITTED, "Submitted"),
        (STATUS_PROCESSING_GALDR, "Processing (Galdr)"),
        (STATUS_REVIEWED, "Reviewed"),
        (STATUS_ACCEPTED, "Accepted"),
        (STATUS_ACCEPTED_PARTIAL, "Partially Accepted"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_WITHDRAWN, "Withdrawn"),
    ]

    STATUS_BADGE_CLASSES = {
        STATUS_DRAFT: "bg-secondary",
        STATUS_SUBMITTED: "bg-primary",
        STATUS_PROCESSING_GALDR: "bg-warning text-dark",
        STATUS_REVIEWED: "pip-status-reviewed",
        STATUS_ACCEPTED: "bg-success",
        STATUS_ACCEPTED_PARTIAL: "bg-success",
        STATUS_REJECTED: "bg-danger",
        STATUS_WITHDRAWN: "bg-dark",
    }

    playbook = models.ForeignKey(
        "Playbook",
        on_delete=models.CASCADE,
        related_name="process_improvement_proposals",
    )
    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When Galdr finished (PIP moved to Reviewed).",
    )
    galdr_holistic_assessment = models.TextField(
        blank=True,
        default="",
        help_text="Galdr v2 overall coherence reasoning (when GALDR_USE_TARGET_STATE is enabled).",
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    status_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Updated whenever status changes — drives unread nav count.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_pips",
    )

    class Meta:
        ordering = ["-updated_at", "-pk"]

    def __str__(self) -> str:
        return f"PIP-{self.pk} {self.title[:40]}"

    def status_changed_since_visit(self, last_list_visit) -> bool:
        """
        Whether this PIP's status changed strictly after user's last list visit marker.

        :param last_list_visit: ``datetime`` or ``None``.
        :return: ``True`` if unread indicator should render for submitter UX.
        """
        if self.status_changed_at is None:
            return False
        if last_list_visit is None:
            return False
        return self.status_changed_at > last_list_visit

    def status_bootstrap_class(self) -> str:
        """Bootstrap badge CSS class for list/detail UI."""
        return self.STATUS_BADGE_CLASSES.get(self.status, "bg-secondary")

    def save(self, *args, **kwargs) -> None:
        """Stamp ``status_changed_at`` whenever ``status`` changes."""
        update_fields = kwargs.get("update_fields")
        if self.pk:
            prev = (
                ProcessImprovementProposal.objects.filter(pk=self.pk)
                .values_list("status", flat=True)
                .first()
            )
            if prev is not None and prev != self.status:
                self.status_changed_at = timezone.now()
                if (
                    isinstance(update_fields, (list, tuple))
                    and "status_changed_at" not in update_fields
                ):
                    kwargs["update_fields"] = tuple(update_fields) + (
                        "status_changed_at",
                    )
        else:
            if self.status_changed_at is None:
                self.status_changed_at = timezone.now()
        super().save(*args, **kwargs)
