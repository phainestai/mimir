"""
Skill model for step-by-step guidance attached to activities.

Each activity can have at most one skill providing detailed guidance
(steps, best practices, examples, prerequisites, tools, references).
"""

from django.db import models


class Skill(models.Model):
    """
    Skill provides detailed step-by-step guidance for an activity.

    A skill is a 1:1 companion to an Activity, offering richer content
    than the activity's guidance field — structured Markdown covering
    prerequisites, steps, examples, tools, and references.

    Permissions delegate up the hierarchy: Skill → Activity → Workflow → Playbook → Author.
    """

    activity = models.OneToOneField(
        'Activity',
        on_delete=models.CASCADE,
        related_name='skill',
        help_text="Parent activity for this skill (1:1 relationship)"
    )
    title = models.CharField(
        max_length=200,
        help_text="Short descriptive title for the skill"
    )
    content = models.TextField(
        blank=True,
        default='',
        help_text="Markdown content: steps, best practices, examples, prerequisites, tools, references"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        """String representation using skill title."""
        return self.title

    def is_owned_by(self, user):
        """
        Check if user owns this skill (via parent activity).

        :param user: User to check ownership for
        :returns: True if user owns the parent playbook
        :rtype: bool

        Example:
            >>> skill.is_owned_by(maria)
            True  # If maria owns the playbook containing the activity
        """
        return self.activity.is_owned_by(user)

    def can_edit(self, user):
        """
        Check if user can edit this skill (via parent activity).

        :param user: User to check edit permission for
        :returns: True if user can edit
        :rtype: bool

        Example:
            >>> skill.can_edit(maria)
            True  # If maria owns the playbook and it is editable
        """
        return self.activity.can_edit(user)
