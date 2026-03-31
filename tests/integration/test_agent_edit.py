"""
Integration tests for Agent EDIT operation.

Tests agent edit form, validation, and success scenarios.
Covers scenarios: AGENT-EDIT-01 through AGENT-EDIT-04.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Agent, Playbook

User = get_user_model()


@pytest.mark.django_db
class TestAgentEdit:
    """Integration tests for agent edit functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_edit',
            email='maria_agent_edit@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_edit', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Frontend v1.2',
            description='React methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        self.agent = Agent.objects.create(
            playbook=self.playbook,
            name='Code Reviewer',
            description='Reviews pull requests and suggests improvements'
        )

    def _url(self, pk=None):
        return reverse('agent_edit', kwargs={'pk': pk if pk is not None else self.agent.pk})

    def test_agent_edit_01_open_form(self):
        """AGENT-EDIT-01: Edit form opens with current agent values pre-populated."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-edit-form"' in response.content
        assert b'data-testid="agent-name-input"' in response.content
        assert b'data-testid="agent-description-input"' in response.content
        assert b'Code Reviewer' in response.content

    def test_agent_edit_01_breadcrumb(self):
        """AGENT-EDIT-01: Breadcrumb includes playbook name and agent name."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content
        assert b'breadcrumb' in response.content

    def test_agent_edit_02_edit_name(self):
        """AGENT-EDIT-02: Agent name can be updated successfully."""
        data = {
            'name': 'Senior Code Reviewer',
            'description': 'Reviews pull requests and suggests improvements',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        self.agent.refresh_from_db()
        assert self.agent.name == 'Senior Code Reviewer'

    def test_agent_edit_02_redirects_to_detail_on_success(self):
        """AGENT-EDIT-02: Success redirects to agent detail page."""
        data = {
            'name': 'Senior Code Reviewer',
            'description': 'Reviews code',
        }
        response = self.client.post(self._url(), data)

        expected_url = reverse('agent_detail', kwargs={'pk': self.agent.pk})
        assert response.status_code == 302
        assert response.url == expected_url

    def test_agent_edit_03_edit_description(self):
        """AGENT-EDIT-03: Agent description can be updated successfully."""
        data = {
            'name': 'Code Reviewer',
            'description': 'Updated description for this agent',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        self.agent.refresh_from_db()
        assert self.agent.description == 'Updated description for this agent'

    def test_agent_edit_04_cancel_button_links_to_detail(self):
        """AGENT-EDIT-04: Cancel button links back to agent detail view."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="cancel-btn"' in response.content
        expected_url = reverse('agent_detail', kwargs={'pk': self.agent.pk})
        assert expected_url.encode() in response.content

    def test_edit_requires_login(self):
        """Redirect to login if not authenticated."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_edit_requires_ownership(self):
        """Permission denied for non-owner."""
        other = User.objects.create_user(username='other_edit', password='pass123')
        self.client.login(username='other_edit', password='pass123')

        response = self.client.post(self._url(), {'name': 'Hacked', 'description': ''})

        assert response.status_code == 302
        self.agent.refresh_from_db()
        assert self.agent.name == 'Code Reviewer'

    def test_edit_duplicate_name_fails(self):
        """Uniqueness validation: duplicate agent name in same playbook is rejected."""
        Agent.objects.create(
            playbook=self.playbook,
            name='Existing Agent',
            description='Already here'
        )
        data = {'name': 'Existing Agent', 'description': ''}
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert b'data-testid="name-error"' in response.content
        self.agent.refresh_from_db()
        assert self.agent.name == 'Code Reviewer'

    def test_edit_empty_name_fails(self):
        """Required field validation: empty name is rejected."""
        data = {'name': '', 'description': 'Some description'}
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert b'data-testid="name-error"' in response.content

    def test_edit_agent_not_found(self):
        """404 for non-existent agent."""
        response = self.client.get(self._url(pk=99999))

        assert response.status_code == 404

    def test_edit_same_name_succeeds(self):
        """Editing an agent with its own current name (no name change) succeeds."""
        data = {
            'name': 'Code Reviewer',
            'description': 'Updated description only',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        self.agent.refresh_from_db()
        assert self.agent.description == 'Updated description only'
