"""
Integration tests for Skill LIST+FIND operation.

Tests skill list display, search, and navigation.
Covers scenarios: FOB-SKILLS-LIST+FIND-01 through FOB-SKILLS-LIST+FIND-08.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestSkillListFind:
    """Integration tests for skill list and find functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_test',
            email='maria@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_test', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Frontend v1.2',
            description='React methodology',
            category='development',
            status='active',
            source='owned',
            author=self.user
        )
        self.workflow = Workflow.objects.create(
            name='Component Development',
            description='Develop React components',
            playbook=self.playbook,
            order=1
        )
        self.activity = Activity.objects.create(
            name='Setup React Environment',
            guidance='Guide for setting up React',
            workflow=self.workflow,
            order=1
        )

    def test_skill_list_01_page_loads(self):
        """FOB-SKILLS-LIST+FIND-01: Skills list page loads successfully."""
        from methodology.models import Skill
        Skill.objects.create(
            activity=self.activity,
            title='Setup React Component',
            content='Step 1: Install deps'
        )
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Skills' in response.content

    def test_skill_list_02_shows_skills_table(self):
        """FOB-SKILLS-LIST+FIND-02: Skills table shows key columns."""
        from methodology.models import Skill
        Skill.objects.create(
            activity=self.activity,
            title='Setup React Component',
            content='Step-by-step guide'
        )
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'data-testid="skills-table"' in response.content

    def test_skill_list_03_create_button_present(self):
        """FOB-SKILLS-LIST+FIND-03: Create new skill button is present."""
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="create-skill-btn"' in response.content

    def test_skill_list_04_search_form_present(self):
        """FOB-SKILLS-LIST+FIND-04: Search input is present on the list page."""
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-search"' in response.content

    def test_skill_list_04_search_filters_results(self):
        """FOB-SKILLS-LIST+FIND-04: Search by name filters skills shown."""
        from methodology.models import Skill
        activity2 = Activity.objects.create(
            name='Deploy App',
            guidance='Deployment guide',
            workflow=self.workflow,
            order=2
        )
        Skill.objects.create(
            activity=self.activity,
            title='Setup React Component',
            content='Setup steps'
        )
        Skill.objects.create(
            activity=activity2,
            title='Deploy to Production',
            content='Deployment steps'
        )
        url = reverse('skill_list')
        response = self.client.get(url, {'q': 'Setup'})

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'Deploy to Production' not in response.content

    def test_skill_list_07_view_link_present(self):
        """FOB-SKILLS-LIST+FIND-07: Each skill row has a view action link."""
        from methodology.models import Skill
        skill = Skill.objects.create(
            activity=self.activity,
            title='Setup React Component',
            content='Steps'
        )
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert f'data-testid="view-skill-{skill.id}"'.encode() in response.content

    def test_skill_list_08_empty_state(self):
        """FOB-SKILLS-LIST+FIND-08: Empty state shown when no skills exist."""
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="empty-state"' in response.content
        assert b'No skills yet' in response.content

    def test_skill_list_requires_authentication(self):
        """Skills list requires login."""
        self.client.logout()
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 302
        assert '/auth/' in response.url
