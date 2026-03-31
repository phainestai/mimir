"""
Integration tests for Agent VIEW (detail) operation.

Tests agent detail page display, activity relationships, and navigation.
Covers scenarios: AGENT-VIEW-01 through AGENT-VIEW-06.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Agent, Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestAgentView:
    """Integration tests for agent detail view functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_view',
            email='maria_agent_view@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_view', password='testpass123')

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
        self.workflow = Workflow.objects.create(
            name='Component Development',
            description='Develop React components',
            playbook=self.playbook,
            order=1
        )

    def _url(self, pk=None):
        return reverse('agent_detail', kwargs={'pk': pk or self.agent.pk})

    def test_agent_view_01_open_detail(self):
        """AGENT-VIEW-01: Agent detail page loads with breadcrumb."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-detail"' in response.content
        assert b'breadcrumb' in response.content

    def test_agent_view_01_breadcrumb_contains_playbook(self):
        """AGENT-VIEW-01: Breadcrumb includes playbook and agent names."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content
        assert b'Code Reviewer' in response.content

    def test_agent_view_02_header(self):
        """AGENT-VIEW-02: Agent header shows name and playbook badge."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-header"' in response.content
        assert b'data-testid="agent-name"' in response.content
        assert b'Code Reviewer' in response.content

    def test_agent_view_03_description(self):
        """AGENT-VIEW-03: Agent description section is present."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-description"' in response.content
        assert b'Reviews pull requests' in response.content

    def test_agent_view_04_activities(self):
        """AGENT-VIEW-04: Activities section shows activities using this agent."""
        activity = Activity.objects.create(
            name='Review PR',
            guidance='Review pull request guidance',
            workflow=self.workflow,
            order=1,
            agent=self.agent,
        )
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-activities"' in response.content
        assert b'Review PR' in response.content
        assert f'data-testid="activity-link-{activity.id}"'.encode() in response.content

    def test_agent_view_05_edit_button(self):
        """AGENT-VIEW-05: Edit button is visible for the agent owner."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="edit-agent-btn"' in response.content

    def test_agent_view_06_delete_button(self):
        """AGENT-VIEW-06: Delete button is visible for the agent owner."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="delete-agent-btn"' in response.content

    def test_view_requires_login(self):
        """Redirect to login if not authenticated."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_view_agent_not_found(self):
        """404 for non-existent agent."""
        response = self.client.get(self._url(pk=99999))

        assert response.status_code == 404

    def test_view_shows_empty_activities(self):
        """Empty state displays when no activities use this agent."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-activities-empty"' in response.content

    def test_view_requires_ownership(self):
        """Non-owner is redirected when viewing another user's agent."""
        other = User.objects.create_user(username='other_view', password='pass123')
        self.client.login(username='other_view', password='pass123')

        response = self.client.get(self._url())

        assert response.status_code == 302
        assert reverse('agent_list') in response.url
