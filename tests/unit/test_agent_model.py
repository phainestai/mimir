"""
Unit tests for Agent model.

Tests Agent model creation, validation, string representation,
uniqueness constraints, ownership, and serialisation.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from methodology.models import Agent, Playbook

User = get_user_model()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(username='maria_agent', password='testpass123')


@pytest.fixture
def playbook(user):
    """Create a test playbook."""
    return Playbook.objects.create(
        name='React Frontend v1.2',
        description='React methodology',
        category='development',
        status='draft',
        source='owned',
        author=user
    )


@pytest.mark.django_db
class TestAgentCreation:
    """Test Agent model creation and defaults."""

    def test_create_agent_success(self, playbook):
        """Create agent with valid data."""
        agent = Agent.objects.create(
            playbook=playbook,
            name='Code Reviewer',
            description='Reviews pull requests'
        )
        assert agent.pk is not None
        assert agent.name == 'Code Reviewer'
        assert agent.description == 'Reviews pull requests'
        assert agent.playbook == playbook

    def test_agent_str_representation(self, playbook):
        """__str__ returns the agent name."""
        agent = Agent.objects.create(playbook=playbook, name='Test Agent')
        assert str(agent) == 'Test Agent'

    def test_agent_description_defaults_to_empty(self, playbook):
        """Description field defaults to empty string."""
        agent = Agent.objects.create(playbook=playbook, name='Minimal Agent')
        assert agent.description == ''

    def test_agent_has_timestamps(self, playbook):
        """created_at and updated_at are set automatically."""
        agent = Agent.objects.create(playbook=playbook, name='Timestamped Agent')
        assert agent.created_at is not None
        assert agent.updated_at is not None


@pytest.mark.django_db
class TestAgentConstraints:
    """Test Agent uniqueness and validation constraints."""

    def test_agent_unique_per_playbook(self, playbook):
        """Two agents cannot have the same name within one playbook."""
        Agent.objects.create(playbook=playbook, name='Duplicate Agent')

        with pytest.raises(IntegrityError):
            Agent.objects.create(playbook=playbook, name='Duplicate Agent')

    def test_same_name_in_different_playbooks(self, user, playbook):
        """Same agent name is allowed in different playbooks."""
        playbook2 = Playbook.objects.create(
            name='Vue Frontend v1.0',
            description='Vue methodology',
            category='development',
            status='draft',
            source='owned',
            author=user
        )
        Agent.objects.create(playbook=playbook, name='Shared Name')
        agent2 = Agent.objects.create(playbook=playbook2, name='Shared Name')
        assert agent2.pk is not None

    def test_agent_name_required(self, playbook):
        """Name field is required (max_length enforced at DB level)."""
        with pytest.raises(Exception):
            Agent.objects.create(playbook=playbook, name=None)


@pytest.mark.django_db
class TestAgentPermissions:
    """Test Agent ownership and edit permission methods."""

    def test_agent_is_owned_by_author(self, playbook, user):
        """is_owned_by returns True for the playbook author."""
        agent = Agent.objects.create(playbook=playbook, name='Owned Agent')
        assert agent.is_owned_by(user) is True

    def test_agent_is_not_owned_by_other_user(self, playbook):
        """is_owned_by returns False for a different user."""
        other = User.objects.create_user(username='other_user_ag', password='pass')
        agent = Agent.objects.create(playbook=playbook, name='Other Agent')
        assert agent.is_owned_by(other) is False

    def test_agent_can_edit_draft_playbook(self, playbook, user):
        """can_edit returns True for draft playbook owned by user."""
        agent = Agent.objects.create(playbook=playbook, name='Editable Agent')
        assert agent.can_edit(user) is True

    def test_agent_cannot_edit_released_playbook(self, user):
        """can_edit returns False for released playbook."""
        from decimal import Decimal
        released_pb = Playbook.objects.create(
            name='Released PB',
            description='Released playbook',
            category='development',
            status='released',
            version=Decimal('1.0'),
            source='owned',
            author=user
        )
        agent = Agent.objects.create(playbook=released_pb, name='Released Agent')
        assert agent.can_edit(user) is False


@pytest.mark.django_db
class TestAgentToDict:
    """Test Agent.to_dict() serialisation."""

    def test_agent_to_dict_keys(self, playbook):
        """to_dict returns all expected keys."""
        agent = Agent.objects.create(
            playbook=playbook,
            name='Dict Agent',
            description='Dict description'
        )
        result = agent.to_dict()
        assert 'id' in result
        assert 'name' in result
        assert 'description' in result
        assert 'playbook_id' in result
        assert 'created_at' in result
        assert 'updated_at' in result

    def test_agent_to_dict_values(self, playbook):
        """to_dict contains correct values."""
        agent = Agent.objects.create(
            playbook=playbook,
            name='Value Agent',
            description='Value description'
        )
        result = agent.to_dict()
        assert result['name'] == 'Value Agent'
        assert result['description'] == 'Value description'
        assert result['playbook_id'] == playbook.pk
