"""
Minimal Process Improvement Proposal model for playbook versioning and PIP workflows.

Extended in later scenarios; this satisfies PlaybookVersion.pip FK integrity.
"""

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ProcessImprovementProposal(models.Model):
    """A proposed change to a released playbook (PIP)."""

    playbook = models.ForeignKey(
        "Playbook",
        on_delete=models.CASCADE,
        related_name="process_improvement_proposals",
    )
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=32,
        default="pending",
        help_text="e.g. pending, approved, implemented",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_pips",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PIP-{self.pk} {self.title[:40]}"
