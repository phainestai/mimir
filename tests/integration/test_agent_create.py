"""
Integration tests for Agent CREATE operation.

Tests agent creation form, validation, and success scenarios.
Covers scenarios: AGENT-CREATE-01 through AGENT-CREATE-04.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Agent, Playbook

User = get_user_model()


@pytest.mark.django_db
class TestAgentCreate:
    """Integration tests for agent create functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_create',
            email='maria_agent_create@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_create', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Frontend v1.2',
            description='React methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )

    def _url(self):
        return reverse('agent_create', kwargs={'playbook_pk': self.playbook.pk})

    def test_agent_create_01_open_form(self):
        """AGENT-CREATE-01: Create agent form opens successfully."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'Create Agent' in response.content
        assert b'data-testid="agent-create-form"' in response.content
        assert b'data-testid="agent-name-input"' in response.content
        assert b'data-testid="agent-description-input"' in response.content

    def test_agent_create_01_breadcrumb_shows_playbook(self):
        """AGENT-CREATE-01: Breadcrumb includes playbook name."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content
        assert b'breadcrumb' in response.content

    def test_agent_create_02_success(self):
        """AGENT-CREATE-02: Agent is created with valid data."""
        data = {
            'name': 'Code Reviewer',
            'description': 'Reviews pull requests and suggests improvements',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        agent = Agent.objects.get(playbook=self.playbook, name='Code Reviewer')
        assert agent.description == 'Reviews pull requests and suggests improvements'

    def test_agent_create_02_redirects_to_detail_on_success(self):
        """AGENT-CREATE-02: Success redirects to agent detail page."""
        data = {
            'name': 'Code Reviewer',
            'description': 'Reviews code',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        agent = Agent.objects.get(playbook=self.playbook, name='Code Reviewer')
        expected_url = reverse('agent_detail', kwargs={'pk': agent.pk})
        assert response.url == expected_url

    def test_agent_create_03_validation_empty_name(self):
        """AGENT-CREATE-03: Validation error when name is empty."""
        data = {
            'name': '',
            'description': 'Some description',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert b'data-testid="name-error"' in response.content
        assert b'This field is required.' in response.content

    def test_agent_create_03_validation_name_too_long(self):
        """AGENT-CREATE-03: Validation error when name exceeds 200 characters."""
        data = {
            'name': 'A' * 201,
            'description': 'Some description',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert b'data-testid="name-error"' in response.content

    def test_agent_create_04_cancel_returns_to_playbook(self):
        """AGENT-CREATE-04: Cancel button links back to playbook detail."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="cancel-btn"' in response.content
        expected_url = reverse('playbook_detail', kwargs={'pk': self.playbook.pk})
        assert expected_url.encode() in response.content

    def test_create_requires_login(self):
        """Redirect to login if not authenticated."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_create_requires_ownership(self):
        """Non-owner is redirected away when attempting to create agent."""
        other = User.objects.create_user(username='other_create', password='pass123')
        self.client.login(username='other_create', password='pass123')

        response = self.client.post(self._url(), {'name': 'Hack', 'description': ''})

        assert response.status_code == 302
        assert Agent.objects.filter(playbook=self.playbook, name='Hack').count() == 0

    def test_create_duplicate_name_fails(self):
        """Uniqueness validation: duplicate agent name in same playbook is rejected."""
        Agent.objects.create(
            playbook=self.playbook,
            name='Existing Agent',
            description='Already here'
        )
        data = {'name': 'Existing Agent', 'description': 'Attempt duplicate'}
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert Agent.objects.filter(playbook=self.playbook, name='Existing Agent').count() == 1

    def test_create_description_is_optional(self):
        """Agent can be created without a description."""
        data = {'name': 'Minimal Agent', 'description': ''}
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        agent = Agent.objects.get(playbook=self.playbook, name='Minimal Agent')
        assert agent.description == ''
