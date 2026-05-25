"""
Skill model for reusable, tech-specific guidance within a playbook.

Skills are playbook-scoped and carry capability_domain + technology_stack
metadata. Activities reference skills via M2M (many skills per activity).

See: https://en.wikipedia.org/wiki/Separation_of_concerns
     Workflow describes WHAT to do; Skill describes HOW with specific tech.
"""

import logging

from django.db import models

logger = logging.getLogger(__name__)


class Skill(models.Model):
    """
    Reusable, tech-specific guidance that lives at the playbook level.

    A Skill describes *how* to perform a capability (e.g., "Build a Form")
    using a specific technology (e.g., "React+Redux"). Multiple activities
    can reference the same skill (M2M via Activity.skills).

    Key fields:
        - **capability_domain**: What it does (e.g., "GUI_FORM", "API_CRUD")
        - **technology_stack**: How it does it (e.g., "React+Redux", "Django+HTMX")

    Permissions delegate: Skill -> Playbook -> Author.

    Example:
        >>> skill = Skill.objects.create(
        ...     playbook=playbook,
        ...     title="React Form Component",
        ...     capability_domain="GUI_FORM",
        ...     technology_stack="React+Redux",
        ...     content="## Steps\\n1. Install deps..."
        ... )
        >>> skill.get_activity_count()
        3
    """

    # Parent relationship — skill belongs to a playbook
    playbook = models.ForeignKey(
        'Playbook',
        on_delete=models.CASCADE,
        related_name='skills',
        help_text="Parent playbook owning this skill"
    )

    # Core fields
    title = models.CharField(
        max_length=200,
        help_text="Short descriptive title for the skill"
    )
    capability_domain = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="What capability this skill covers (e.g., GUI_FORM, API_CRUD, DB_MIGRATION)"
    )
    technology_stack = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Technology used (e.g., React+Redux, Django+HTMX, FastAPI)"
    )
    content = models.TextField(
        blank=True,
        default='',
        help_text="Markdown content: steps, best practices, examples, prerequisites, tools, references"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self) -> str:
        """String representation using skill title."""
        return self.title

    def is_owned_by(self, user) -> bool:
        """
        Check if user owns this skill (via parent playbook).

        :param user: User to check ownership for
        :returns: True if user owns the parent playbook
        :rtype: bool

        Example:
            >>> skill.is_owned_by(maria)
            True  # If maria owns the playbook
        """
        return self.playbook.is_owned_by(user)

    def can_edit(self, user) -> bool:
        """
        Check if user can edit this skill (via parent playbook).

        :param user: User to check edit permission for
        :returns: True if user can edit the parent playbook
        :rtype: bool

        Example:
            >>> skill.can_edit(maria)
            True  # If maria owns the playbook and it is editable
        """
        return self.playbook.can_edit(user)

    def get_activity_count(self) -> int:
        """
        Count activities referencing this skill.

        :returns: Number of activities with skill FK pointing here
        :rtype: int

        Example:
            >>> skill.get_activity_count()
            3
        """
        return self.activities.count()
