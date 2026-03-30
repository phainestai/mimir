"""
Service layer for Agent operations.

Provides business logic for agent CRUD operations and validation.
Agents are AI assistants scoped to a Playbook.
"""

import logging

from django.core.exceptions import ValidationError
from django.db.models import Q

from methodology.models import Agent

logger = logging.getLogger(__name__)


class AgentService:
    """Service class for agent operations."""

    @staticmethod
    def create_agent(playbook, name, description=''):
        """
        Create an agent for a playbook with validation.

        :param playbook: Parent Playbook instance
        :param name: Agent name (max 200 chars, required, unique per playbook)
        :param description: Optional description text
        :returns: Created Agent instance
        :raises ValidationError: If name is empty or already exists in the playbook

        Example:
            >>> agent = AgentService.create_agent(
            ...     playbook=pb,
            ...     name='Code Reviewer',
            ...     description='Reviews pull requests and suggests improvements'
            ... )
        """
        if not name or not name.strip():
            logger.warning(f"Agent creation failed: empty name for playbook {playbook.id}")
            raise ValidationError("Agent name cannot be empty")

        if len(name) > 200:
            logger.warning(f"Agent creation failed: name too long ({len(name)} chars)")
            raise ValidationError("Agent name cannot exceed 200 characters")

        if Agent.objects.filter(playbook=playbook, name=name.strip()).exists():
            logger.warning(
                f"Agent creation failed: name '{name}' already exists in playbook {playbook.id}"
            )
            raise ValidationError(f"Agent '{name}' already exists in this playbook")

        agent = Agent.objects.create(
            playbook=playbook,
            name=name.strip(),
            description=description.strip() if description else ''
        )
        logger.info(
            f"Created agent '{agent.name}' (id={agent.id}) for playbook {playbook.id}"
        )
        return agent

    @staticmethod
    def get_agent(agent_id):
        """
        Get an agent by ID with playbook pre-fetched.

        :param agent_id: Agent primary key
        :returns: Agent instance
        :raises Agent.DoesNotExist: If agent not found

        Example:
            >>> agent = AgentService.get_agent(42)
        """
        return Agent.objects.select_related('playbook', 'playbook__author').get(pk=agent_id)

    @staticmethod
    def list_agents_for_playbook(playbook_id):
        """
        List all agents within a playbook, ordered by name.

        :param playbook_id: Playbook primary key
        :returns: QuerySet of Agent instances ordered by name
        :rtype: QuerySet[Agent]

        Example:
            >>> agents = AgentService.list_agents_for_playbook(1)
        """
        return Agent.objects.filter(
            playbook_id=playbook_id
        ).select_related('playbook').order_by('name')

    @staticmethod
    def search_agents(query, user=None):
        """
        Search agents by name or description across all playbooks.

        :param query: Search string (case-insensitive, matches name or description)
        :param user: If provided, restrict to agents owned by this user
        :returns: QuerySet of matching Agent instances ordered by name
        :rtype: QuerySet[Agent]

        Example:
            >>> results = AgentService.search_agents('reviewer', user=maria)
        """
        qs = Agent.objects.select_related('playbook', 'playbook__author')

        if user is not None:
            qs = qs.filter(
                playbook__author=user,
                playbook__source='owned'
            )

        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        return qs.order_by('name')

    @staticmethod
    def update_agent(agent_id, **kwargs):
        """
        Update agent fields with validation.

        :param agent_id: Agent primary key
        :param kwargs: Fields to update (name, description)
        :returns: Updated Agent instance
        :raises ValidationError: If updated name is empty or already exists

        Example:
            >>> agent = AgentService.update_agent(42, name='Senior Reviewer', description='...')
        """
        agent = Agent.objects.get(pk=agent_id)

        if 'name' in kwargs:
            new_name = kwargs['name']
            if not new_name or not new_name.strip():
                raise ValidationError("Agent name cannot be empty")
            if len(new_name) > 200:
                raise ValidationError("Agent name cannot exceed 200 characters")
            kwargs['name'] = new_name.strip()
            if (
                Agent.objects.filter(playbook=agent.playbook, name=kwargs['name'])
                .exclude(pk=agent_id)
                .exists()
            ):
                raise ValidationError(f"Agent '{kwargs['name']}' already exists in this playbook")

        if 'description' in kwargs and kwargs['description']:
            kwargs['description'] = kwargs['description'].strip()

        for field, value in kwargs.items():
            setattr(agent, field, value)

        agent.save()
        logger.info(f"Updated agent {agent_id}: {', '.join(kwargs.keys())}")
        return agent

    @staticmethod
    def delete_agent(agent_id):
        """
        Delete an agent by ID.

        :param agent_id: Agent primary key
        :raises Agent.DoesNotExist: If agent not found

        Example:
            >>> AgentService.delete_agent(42)
        """
        agent = Agent.objects.get(pk=agent_id)
        name = agent.name
        playbook_id = agent.playbook_id
        agent.delete()
        logger.info(f"Deleted agent '{name}' (id={agent_id}) from playbook {playbook_id}")
