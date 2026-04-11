"""
Integration tests for Activity-Agent linking functionality.

Tests agent dropdown on edit form and agent card on detail view.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Playbook, Workflow, Activity, Agent

User = get_user_model()


@pytest.mark.django_db
class TestActivityLinkAgent:
    """Integration tests for linking agents to activities."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_link',
            email='maria@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_link', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Development',
            description='React methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        
        self.workflow = Workflow.objects.create(
            playbook=self.playbook,
            name='Build Feature',
            order=1
        )
        
        self.activity = Activity.objects.create(
            workflow=self.workflow,
            name='Implement Backend',
            guidance='Backend implementation',
            order=1
        )

        self.agent = Agent.objects.create(
            playbook=self.playbook,
            name='Code Reviewer',
            description='Reviews code changes'
        )

    def test_edit_form_shows_agent_dropdown(self):
        """Agent dropdown is present with playbook agents."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agent-select"' in response.content
        assert b'Code Reviewer' in response.content

    def test_link_agent_to_activity(self):
        """Select agent and save, verify link created."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        
        response = self.client.post(url, {
            'name': self.activity.name,
            'guidance': self.activity.guidance,
            'order': self.activity.order,
            'agent': self.agent.id,
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert self.activity.agent_id == self.agent.id

    def test_unlink_agent_from_activity(self):
        """Select 'None' and save, verify link removed."""
        # First link an agent
        self.activity.agent = self.agent
        self.activity.save()

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        
        response = self.client.post(url, {
            'name': self.activity.name,
            'guidance': self.activity.guidance,
            'order': self.activity.order,
            'agent': '',  # Empty = None
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert self.activity.agent_id is None

    def test_agent_dropdown_only_shows_playbook_agents(self):
        """No cross-playbook agents in dropdown."""
        other_playbook = Playbook.objects.create(
            name='Other Playbook',
            description='Other',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        other_agent = Agent.objects.create(
            playbook=other_playbook,
            name='Other Agent',
            description='From other playbook'
        )

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Code Reviewer' in response.content
        assert b'Other Agent' not in response.content

    def test_detail_shows_linked_agent(self):
        """Agent card displays linked agent."""
        self.activity.agent = self.agent
        self.activity.save()

        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agent-card"' in response.content
        assert b'Code Reviewer' in response.content
        assert b'data-testid="agent-link"' in response.content

    def test_detail_shows_no_agent_state(self):
        """Empty state when no agent linked."""
        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agent-card"' in response.content
        assert b'data-testid="no-agent"' in response.content
        assert b'No agent assigned' in response.content
