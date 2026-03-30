"""
Integration tests for Agent LIST+FIND operation.

Tests agent list display, search, and navigation.
Covers scenarios: AGENT-LIST-01 through AGENT-LIST-08.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Agent, Playbook

User = get_user_model()


@pytest.mark.django_db
class TestAgentListFind:
    """Integration tests for agent list and find functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_agent_list',
            email='maria_agent@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_agent_list', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Frontend v1.2',
            description='React methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )

    def test_agent_list_01_page_loads(self):
        """AGENT-LIST-01: Agents list page loads successfully."""
        Agent.objects.create(playbook=self.playbook, name='Developer Agent')
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Agents' in response.content

    def test_agent_list_02_shows_agents_table(self):
        """AGENT-LIST-02: Agents table shows agents with key columns."""
        Agent.objects.create(
            playbook=self.playbook,
            name='Code Reviewer',
            description='Reviews code changes'
        )
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Code Reviewer' in response.content
        assert b'data-testid="agents-table"' in response.content

    def test_agent_list_03_create_button_navigation(self):
        """AGENT-LIST-03: Create First Agent button is present in empty state."""
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="create-first-agent-btn"' in response.content

    def test_agent_list_04_search_by_name(self):
        """AGENT-LIST-04: Search by name filters results."""
        Agent.objects.create(
            playbook=self.playbook,
            name='Developer Agent',
            description='Develops features'
        )
        Agent.objects.create(
            playbook=self.playbook,
            name='Reviewer Agent',
            description='Reviews code'
        )
        url = reverse('agent_list')
        response = self.client.get(url, {'q': 'Developer'})

        assert response.status_code == 200
        assert b'Developer Agent' in response.content
        assert b'Reviewer Agent' not in response.content

    def test_agent_list_04_search_input_present(self):
        """AGENT-LIST-04: Search input is present on the list page."""
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agent-search"' in response.content

    def test_agent_list_05_filter_by_activity_usage(self):
        """AGENT-LIST-05: Filter by activity usage (stub — page loads)."""
        Agent.objects.create(playbook=self.playbook, name='Used Agent')
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200

    def test_agent_list_06_view_usage_count(self):
        """AGENT-LIST-06: Agent usage count visible (stub — table renders)."""
        for i in range(3):
            Agent.objects.create(playbook=self.playbook, name=f'Agent {i}')

        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agents-table"' in response.content

    def test_agent_list_07_view_link_present(self):
        """AGENT-LIST-07: Each agent row has a view action link."""
        agent = Agent.objects.create(
            playbook=self.playbook,
            name='Viewable Agent'
        )
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert f'data-testid="view-agent-{agent.id}"'.encode() in response.content

    def test_agent_list_08_empty_state(self):
        """AGENT-LIST-08: Empty state shown when no agents exist."""
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="empty-state"' in response.content
        assert b'No agents yet' in response.content

    def test_agent_list_requires_authentication(self):
        """Agent list requires login."""
        self.client.logout()
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_agent_list_shows_playbook_name(self):
        """Agent table shows the parent playbook name."""
        Agent.objects.create(
            playbook=self.playbook,
            name='Playbook Agent',
            description='Belongs to a playbook'
        )
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content

    def test_agent_list_search_shows_query_in_input(self):
        """Search query value is preserved in the search input."""
        url = reverse('agent_list')
        response = self.client.get(url, {'q': 'myquery'})

        assert response.status_code == 200
        assert b'myquery' in response.content

    def test_agent_list_container_testid_present(self):
        """agents-list container has correct data-testid."""
        url = reverse('agent_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="agents-list"' in response.content
