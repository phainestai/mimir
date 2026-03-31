"""
Integration tests for Agent DELETE operation.

Tests agent delete modal, cascade warnings, and deletion confirmation.
Covers scenarios: AGENT-DELETE-01 through AGENT-DELETE-05.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Agent, Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestAgentDelete:
    """Integration tests for agent delete functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_delete',
            email='maria_agent_delete@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_delete', password='testpass123')

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
        return reverse('agent_delete', kwargs={'pk': pk if pk is not None else self.agent.pk})

    def test_agent_delete_01_open_modal(self):
        """AGENT-DELETE-01: Delete modal loads via GET request."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="delete-modal"' in response.content

    def test_agent_delete_02_shows_agent_details(self):
        """AGENT-DELETE-02: Modal shows agent name and playbook name."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="agent-name-display"' in response.content
        assert b'Code Reviewer' in response.content
        assert b'React Frontend v1.2' in response.content

    def test_agent_delete_03_activity_warning_shown(self):
        """AGENT-DELETE-03: Warning shown when agent has assigned activities."""
        Activity.objects.create(
            name='Review PR',
            guidance='Review pull request guidance',
            workflow=self.workflow,
            order=1,
            agent=self.agent,
        )
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="activity-count"' in response.content
        assert b'data-testid="activity-list"' in response.content
        assert b'Review PR' in response.content

    def test_agent_delete_03_no_activities_message(self):
        """AGENT-DELETE-03: Message shown when agent has no activities."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="no-activities-msg"' in response.content

    def test_agent_delete_04_confirm_deletion(self):
        """AGENT-DELETE-04: POST request deletes the agent."""
        agent_pk = self.agent.pk
        response = self.client.post(self._url())

        assert response.status_code == 302
        assert not Agent.objects.filter(pk=agent_pk).exists()

    def test_agent_delete_04_redirects_to_playbook(self):
        """AGENT-DELETE-04: After deletion, redirects to playbook detail."""
        response = self.client.post(self._url())

        expected_url = reverse('playbook_detail', kwargs={'pk': self.playbook.pk})
        assert response.status_code == 302
        assert response.url == expected_url

    def test_agent_delete_05_cancel_button_present(self):
        """AGENT-DELETE-05: Cancel button is present in modal."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="cancel-delete-btn"' in response.content
        assert b'data-testid="confirm-delete-btn"' in response.content

    def test_delete_requires_login(self):
        """Redirect to login if not authenticated."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_delete_requires_ownership(self):
        """Permission denied for non-owner."""
        other = User.objects.create_user(username='other_delete', password='pass123')
        self.client.login(username='other_delete', password='pass123')

        response = self.client.post(self._url())

        assert response.status_code == 302
        assert Agent.objects.filter(pk=self.agent.pk).exists()

    def test_delete_agent_not_found(self):
        """404 for non-existent agent."""
        response = self.client.get(self._url(pk=99999))

        assert response.status_code == 404

    def test_delete_cascades_to_activities(self):
        """Deleting agent sets activity.agent to NULL (not cascade delete)."""
        activity = Activity.objects.create(
            name='Review PR',
            guidance='Review pull request guidance',
            workflow=self.workflow,
            order=1,
            agent=self.agent,
        )
        self.client.post(self._url())

        activity.refresh_from_db()
        assert activity.agent is None
        assert Activity.objects.filter(pk=activity.pk).exists()
