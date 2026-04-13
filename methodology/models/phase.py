"""
Phase model for grouping activities within a workflow.

A Phase is an optional organisational layer that sits between a Workflow
and its Activities.  Each Phase belongs to exactly one Workflow and has an
explicit integer order so phases can be sequenced (Planning → Execution →
Closure etc.).

When a Phase is deleted its Activities are moved to unassigned (phase FK
set to NULL).  The old Activity.phase CharField is preserved during the
migration period and will be removed after S3 completes the data migration.
"""

import logging

from django.db import models

logger = logging.getLogger(__name__)


class Phase(models.Model):
    """
    Phase groups related activities within a workflow.

    Phases are optional; a workflow may have zero phases.  When phases
    exist, every activity may optionally be assigned to one of them.

    Attributes:
        workflow: Parent workflow this phase belongs to.
        name: Display name (e.g. "Planning", "Execution"). Unique per workflow.
        description: Optional longer description of what this phase covers.
        order: Numeric sort order within the parent workflow (1-based).
        created_at: Auto-set creation timestamp.
        updated_at: Auto-set last-modified timestamp.
    """

    workflow = models.ForeignKey(
        'Workflow',
        on_delete=models.CASCADE,
        related_name='phases',
        help_text="Parent workflow that owns this phase",
    )
    name = models.CharField(
        max_length=100,
        help_text="Phase name, unique within the parent workflow",
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Optional description of activities covered by this phase",
    )
    order = models.IntegerField(
        default=1,
        help_text="Display order within the workflow (1 = first)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['workflow', 'order', 'name']
        verbose_name = 'Phase'
        verbose_name_plural = 'Phases'
        constraints = [
            models.UniqueConstraint(
                fields=['workflow', 'name'],
                name='unique_phase_per_workflow',
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} (#{self.order}) in {self.workflow.name}"

    def get_activity_count(self) -> int:
        """
        Return the number of activities currently assigned to this phase.

        :returns: Activity count.
        :rtype: int

        Example:
            >>> phase.get_activity_count()
            3
        """
        raise NotImplementedError()

    def is_owned_by(self, user) -> bool:
        """
        Return True if *user* owns the parent playbook.

        :param user: Django User instance.
        :returns: Ownership flag.
        :rtype: bool

        Example:
            >>> phase.is_owned_by(maria)
            True
        """
        raise NotImplementedError()

    def can_edit(self, user) -> bool:
        """
        Return True if *user* is allowed to modify this phase.

        :param user: Django User instance.
        :returns: Edit permission flag.
        :rtype: bool

        Example:
            >>> phase.can_edit(maria)
            True
        """
        raise NotImplementedError()
