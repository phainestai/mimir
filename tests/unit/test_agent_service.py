"""
Unit tests for AgentService.

Tests agent CRUD operations, validation, search, and error handling.
All tests use real objects (no mocking) per project convention.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from methodology.models import Agent, Playbook
from methodology.services.agent_service import AgentService

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username='maria_svc', password='testpass123')


@pytest.fixture
def playbook(user):
    """Create a test playbook."""
    return Playbook.objects.create(
        name='React Frontend Service',
        description='React methodology for service tests',
        category='development',
        status='draft',
        source='owned',
        author=user
    )


@pytest.mark.django_db
class TestCreateAgent:
    """Test AgentService.create_agent()."""

    def test_create_agent_success(self, playbook):
        """Create agent with valid data succeeds."""
        agent = AgentService.create_agent(
            playbook=playbook,
            name='Code Reviewer',
            description='Reviews pull requests and suggests improvements'
        )
        assert agent.pk is not None
        assert agent.name == 'Code Reviewer'
        assert agent.description == 'Reviews pull requests and suggests improvements'
        assert agent.playbook == playbook

    def test_create_agent_strips_whitespace(self, playbook):
        """Name and description are stripped of surrounding whitespace."""
        agent = AgentService.create_agent(
            playbook=playbook,
            name='  Trimmed Name  ',
            description='  Trimmed desc  '
        )
        assert agent.name == 'Trimmed Name'
        assert agent.description == 'Trimmed desc'

    def test_create_agent_empty_name_fails(self, playbook):
        """Creating with empty name raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentService.create_agent(playbook=playbook, name='')

    def test_create_agent_whitespace_name_fails(self, playbook):
        """Creating with whitespace-only name raises ValidationError."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentService.create_agent(playbook=playbook, name='   ')

    def test_create_agent_name_too_long_fails(self, playbook):
        """Creating with name > 200 chars raises ValidationError."""
        long_name = 'x' * 201
        with pytest.raises(ValidationError, match="200 characters"):
            AgentService.create_agent(playbook=playbook, name=long_name)

    def test_create_agent_duplicate_name_fails(self, playbook):
        """Creating duplicate name within same playbook raises ValidationError."""
        AgentService.create_agent(playbook=playbook, name='Unique Agent')
        with pytest.raises(ValidationError, match="already exists"):
            AgentService.create_agent(playbook=playbook, name='Unique Agent')

    def test_create_agent_no_description(self, playbook):
        """Creating without description uses empty string default."""
        agent = AgentService.create_agent(playbook=playbook, name='No Desc Agent')
        assert agent.description == ''


@pytest.mark.django_db
class TestGetAgent:
    """Test AgentService.get_agent()."""

    def test_get_agent_success(self, playbook):
        """Retrieve existing agent by ID."""
        created = Agent.objects.create(playbook=playbook, name='Retrievable Agent')
        found = AgentService.get_agent(created.pk)
        assert found.pk == created.pk
        assert found.name == 'Retrievable Agent'

    def test_get_agent_not_found(self):
        """Raise Agent.DoesNotExist for non-existent ID."""
        with pytest.raises(Agent.DoesNotExist):
            AgentService.get_agent(999999)


@pytest.mark.django_db
class TestListAgents:
    """Test AgentService.list_agents_for_playbook()."""

    def test_list_agents_for_playbook(self, playbook):
        """Returns all agents in a playbook, ordered by name."""
        Agent.objects.create(playbook=playbook, name='Zebra Agent')
        Agent.objects.create(playbook=playbook, name='Alpha Agent')
        Agent.objects.create(playbook=playbook, name='Middle Agent')

        agents = AgentService.list_agents_for_playbook(playbook.pk)
        names = [a.name for a in agents]
        assert names == ['Alpha Agent', 'Middle Agent', 'Zebra Agent']

    def test_list_agents_excludes_other_playbooks(self, user, playbook):
        """list_agents_for_playbook only returns agents for that playbook."""
        other = Playbook.objects.create(
            name='Other PB', description='Other', category='other',
            author=user, source='owned'
        )
        Agent.objects.create(playbook=playbook, name='My Agent')
        Agent.objects.create(playbook=other, name='Other Agent')

        agents = AgentService.list_agents_for_playbook(playbook.pk)
        assert len(agents) == 1
        assert agents[0].name == 'My Agent'


@pytest.mark.django_db
class TestSearchAgents:
    """Test AgentService.search_agents()."""

    def test_search_agents_by_name(self, playbook, user):
        """Search filters agents by name (case-insensitive)."""
        Agent.objects.create(playbook=playbook, name='Developer Agent')
        Agent.objects.create(playbook=playbook, name='Reviewer Agent')

        results = AgentService.search_agents('developer', user=user)
        assert len(results) == 1
        assert results[0].name == 'Developer Agent'

    def test_search_agents_by_description(self, playbook, user):
        """Search filters agents by description content."""
        Agent.objects.create(
            playbook=playbook, name='Agent A', description='Handles code review tasks'
        )
        Agent.objects.create(
            playbook=playbook, name='Agent B', description='Writes documentation'
        )

        results = AgentService.search_agents('code review', user=user)
        assert len(results) == 1
        assert results[0].name == 'Agent A'

    def test_search_agents_empty_query_returns_all(self, playbook, user):
        """Empty query returns all agents for the user."""
        Agent.objects.create(playbook=playbook, name='Agent X')
        Agent.objects.create(playbook=playbook, name='Agent Y')

        results = AgentService.search_agents('', user=user)
        assert len(results) == 2

    def test_search_agents_user_filter(self, user, playbook):
        """User filter restricts results to owned playbooks only."""
        other = User.objects.create_user(username='other_search', password='pass')
        other_pb = Playbook.objects.create(
            name='Other Playbook', description='Other', category='other',
            author=other, source='owned'
        )
        Agent.objects.create(playbook=playbook, name='My Agent')
        Agent.objects.create(playbook=other_pb, name='Not My Agent')

        results = AgentService.search_agents('', user=user)
        names = [a.name for a in results]
        assert 'My Agent' in names
        assert 'Not My Agent' not in names


@pytest.mark.django_db
class TestUpdateAgent:
    """Test AgentService.update_agent()."""

    def test_update_agent_name(self, playbook):
        """Update agent name field."""
        agent = Agent.objects.create(playbook=playbook, name='Old Name')
        updated = AgentService.update_agent(agent.pk, name='New Name')
        assert updated.name == 'New Name'

    def test_update_agent_description(self, playbook):
        """Update agent description field."""
        agent = Agent.objects.create(playbook=playbook, name='Update Desc Agent')
        updated = AgentService.update_agent(agent.pk, description='New description')
        assert updated.description == 'New description'

    def test_update_agent_empty_name_fails(self, playbook):
        """Updating to empty name raises ValidationError."""
        agent = Agent.objects.create(playbook=playbook, name='Non-empty Name')
        with pytest.raises(ValidationError, match="cannot be empty"):
            AgentService.update_agent(agent.pk, name='')


@pytest.mark.django_db
class TestDeleteAgent:
    """Test AgentService.delete_agent()."""

    def test_delete_agent_success(self, playbook):
        """Delete an existing agent."""
        agent = Agent.objects.create(playbook=playbook, name='Deletable Agent')
        agent_id = agent.pk
        AgentService.delete_agent(agent_id)
        assert not Agent.objects.filter(pk=agent_id).exists()

    def test_delete_agent_not_found(self):
        """Raise Agent.DoesNotExist for non-existent ID."""
        with pytest.raises(Agent.DoesNotExist):
            AgentService.delete_agent(999999)
