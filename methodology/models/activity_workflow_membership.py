"""Secondary workflow membership for activities (cross-listing)."""

from django.core.exceptions import ValidationError
from django.db import models


class ActivityWorkflowMembership(models.Model):
    """
    Records an activity appearing in a workflow beyond its primary ``Activity.workflow`` FK.

    Primary home workflow stays on ``Activity.workflow``; this table holds secondary listings.
    """

    activity = models.ForeignKey(
        "methodology.Activity",
        on_delete=models.CASCADE,
        related_name="workflow_memberships",
    )
    workflow = models.ForeignKey(
        "methodology.Workflow",
        on_delete=models.CASCADE,
        related_name="secondary_activities",
    )
    order = models.PositiveIntegerField(
        default=1,
        help_text="Display order within the secondary workflow",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="True when this row mirrors the activity primary workflow FK",
    )

    class Meta:
        verbose_name = "Activity workflow membership"
        verbose_name_plural = "Activity workflow memberships"
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "workflow"],
                name="unique_activity_workflow_membership",
            )
        ]
        ordering = ["workflow", "order", "pk"]

    def __str__(self) -> str:
        return f"{self.activity_id} in workflow {self.workflow_id} (#{self.order})"

    def clean(self):
        if self.activity_id and self.workflow_id:
            if self.activity.workflow.playbook_id != self.workflow.playbook_id:
                raise ValidationError(
                    "Activity and workflow must belong to the same playbook."
                )
            if not self.is_primary and self.activity.workflow_id == self.workflow_id:
                raise ValidationError(
                    "Primary workflow membership is represented by Activity.workflow FK."
                )
