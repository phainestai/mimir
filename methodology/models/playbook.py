"""
Playbook model — the top-level container for methodology content.

A Playbook owns Workflows, which own Activities, which own Artifacts and Skills.
Playbooks start as drafts (v0.x) and are released to production (v1.0+).
"""

import logging
from decimal import Decimal, ROUND_DOWN

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
logger = logging.getLogger(__name__)


class Playbook(models.Model):
    """
    Playbook is the top-level container for a methodology.

    Draft playbooks (version < 1.0) can be freely edited.
    Released playbooks (version >= 1.0) require PIP workflow for changes.

    Permissions: Playbook.author is the owner; source='owned' means local ownership.
    """

    CATEGORY_CHOICES = [
        ('product', 'Product'),
        ('development', 'Development'),
        ('research', 'Research'),
        ('design', 'Design'),
        ('other', 'Other'),
    ]

    VISIBILITY_CHOICES = [
        ('private', 'Private (only me)'),
        ('family', 'Family'),
        ('local', 'Local only (not uploaded to Homebase)'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('released', 'Released'),
        ('disabled', 'Disabled'),
    ]

    SOURCE_CHOICES = [
        ('owned', 'Owned'),
        ('downloaded', 'Downloaded'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = models.JSONField(blank=True, default=list)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='private')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    version = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        default=Decimal('0.1'),
        help_text="Draft: 0.1, 0.2, etc. Released: 1.0, 2.0, etc."
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='owned')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playbooks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_playbook_per_author'
            )
        ]

    def __str__(self):
        """String representation: name and version."""
        return f"{self.name} (v{self.version})"

    # ---- Permission helpers ----

    def is_owned_by(self, user):
        """
        Check if the given user owns this playbook.

        :param user: User instance to check
        :returns: True if user is the author and source is 'owned'
        :rtype: bool

        Example:
            >>> playbook.is_owned_by(maria)
            True
        """
        return self.source == 'owned' and self.author == user

    def can_edit(self, user):
        """
        Check if user can edit this playbook.

        Editing is allowed only for owned draft playbooks.

        :param user: User instance to check
        :returns: True if user can edit
        :rtype: bool

        Example:
            >>> playbook.can_edit(maria)
            True  # If maria owns it and it's a draft
        """
        return self.is_owned_by(user) and self.is_draft

    # ---- Status helpers ----

    @property
    def is_draft(self):
        """
        Return True if playbook is in draft state (version < 1.0).

        :returns: True if version is less than 1.0
        :rtype: bool

        Example:
            >>> playbook.is_draft
            True  # For version 0.3
        """
        return Decimal(str(self.version)) < Decimal('1.0')

    def release(self):
        """
        Transition playbook from draft to released state (version 1.0).

        Sets status to 'released' and version to 1.0. Does not save — caller must save.

        Example:
            >>> playbook.release()
            >>> playbook.version
            Decimal('1.0')
        """
        self.status = 'released'
        self.version = Decimal('1.0')
        logger.info(f"Playbook '{self.name}' (id={self.pk}) released to v1.0")

    def increment_version(self):
        """
        Increment draft version by 0.1 (e.g. 0.1 → 0.2).

        No-op for released playbooks. Does not save — caller must save.

        Example:
            >>> playbook.increment_version()
            >>> playbook.version
            Decimal('0.2')
        """
        current = Decimal(str(self.version))
        if current < Decimal('1.0'):
            self.version = (current + Decimal('0.1')).quantize(Decimal('0.1'), rounding=ROUND_DOWN)

    def get_status_badge_color(self):
        """
        Return Bootstrap badge colour string for the current status.

        :returns: Bootstrap colour name ('success', 'warning', 'secondary', etc.)
        :rtype: str

        Example:
            >>> playbook.get_status_badge_color()
            'success'  # For 'active' status
        """
        colour_map = {
            'active': 'success',
            'draft': 'warning',
            'released': 'primary',
            'disabled': 'secondary',
        }
        return colour_map.get(self.status, 'secondary')

    def get_quick_stats(self):
        """
        Return a dict of quick statistics for the playbook detail view.

        :returns: Dict with integer counts for key entities, plus agents count.
        :rtype: dict

        Example:
            >>> playbook.get_quick_stats()
            {'workflows': 3, 'phases': 0, 'activities': 12, 'artifacts': 5,
             'roles': 0, 'agents': 2, 'howtos': 0, 'goals': 'Coming soon (v2.1)'}
        """
        workflow_count = self.workflows.count()
        activity_count = sum(w.activities.count() for w in self.workflows.all())
        artifact_count = self.artifacts.count() if hasattr(self, 'artifacts') else 0
        agent_count = self.agents.count() if hasattr(self, 'agents') else 0

        return {
            'workflows': workflow_count,
            'phases': 0,            # Phase model not yet implemented
            'activities': activity_count,
            'artifacts': artifact_count,
            'roles': 0,             # Human roles placeholder (ACT 8)
            'agents': agent_count,  # AI Agents (ACT 7)
            'howtos': 0,            # How-tos placeholder
            'goals': 'Coming soon (v2.1)',
        }
