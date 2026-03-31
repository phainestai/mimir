"""
Agent model for AI assistants attached to playbooks.

Each playbook can have multiple agents that represent AI assistants
configured to perform specific activities within a methodology.
"""

import logging

from django.db import models

logger = logging.getLogger(__name__)


class Agent(models.Model):
    """
    Agent represents an AI assistant within a playbook.

    Agents are scoped to a playbook and can be assigned to activities.
    They describe an AI model's name, purpose, and configuration.

    Permissions delegate up the hierarchy: Agent → Playbook → Author.
    """

    playbook = models.ForeignKey(
        'Playbook',
        on_delete=models.CASCADE,
        related_name='agents',
        help_text="Parent playbook this agent belongs to"
    )
    name = models.CharField(
        max_length=200,
        help_text="Short descriptive name for the agent (e.g., 'Code Reviewer')"
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="What this agent does and when to use it"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        constraints = [
            models.UniqueConstraint(
                fields=['playbook', 'name'],
                name='unique_agent_name_per_playbook'
            )
        ]

    def __str__(self):
        """String representation using agent name."""
        return self.name

    def is_owned_by(self, user):
        """
        Check if user owns this agent (via parent playbook).

        :param user: User to check ownership for
        :returns: True if user owns the parent playbook
        :rtype: bool

        Example:
            >>> agent.is_owned_by(maria)
            True  # If maria owns the playbook
        """
        return self.playbook.is_owned_by(user)

    def can_edit(self, user):
        """
        Check if user can edit this agent (via parent playbook).

        :param user: User to check edit permission for
        :returns: True if user can edit the parent playbook
        :rtype: bool

        Example:
            >>> agent.can_edit(maria)
            True  # If maria owns the playbook and it is editable
        """
        return self.playbook.can_edit(user)

    def get_activity_count(self):
        """
        Return the number of activities assigned to this agent.

        :returns: Count of activities using this agent
        :rtype: int

        Example:
            >>> agent.get_activity_count()
            3
        """
        return self.activities.count()

    def to_dict(self):
        """
        Serialise agent to a plain dictionary.

        :returns: Dict with id, name, description, playbook_id, created_at, updated_at
        :rtype: dict

        Example:
            >>> agent.to_dict()
            {'id': 1, 'name': 'Code Reviewer', 'description': '...', 'playbook_id': 5}
        """
        return {
            'id': self.pk,
            'name': self.name,
            'description': self.description,
            'playbook_id': self.playbook_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
