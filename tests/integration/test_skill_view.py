"""
Integration tests for Skill VIEW operation.

Tests skill detail page display and navigation.
Covers scenarios: FOB-SKILLS-VIEW_SKILL-01 through FOB-SKILLS-VIEW_SKILL-06.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestSkillView:
    """Integration tests for skill detail view functionality."""

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

        from methodology.models import Skill
        self.skill = Skill.objects.create(
            activity=self.activity,
            title='Setup React Component',
            content='## Steps\n\n1. Install dependencies\n2. Create component'
        )

    def _url(self):
        return reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })

    def test_skill_view_01_page_loads(self):
        """FOB-SKILLS-VIEW_SKILL-01: Skill detail page loads with correct breadcrumb."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'data-testid="skill-detail"' in response.content

    def test_skill_view_01_breadcrumb_contains_playbook(self):
        """FOB-SKILLS-VIEW_SKILL-01: Breadcrumb shows playbook and activity names."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content
        assert b'breadcrumb' in response.content

    def test_skill_view_02_shows_skill_title(self):
        """FOB-SKILLS-VIEW_SKILL-02: Skill title is displayed in header."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'data-testid="skill-title"' in response.content

    def test_skill_view_03_shows_skill_content(self):
        """FOB-SKILLS-VIEW_SKILL-03: Skill content is rendered (Markdown)."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="skill-content"' in response.content

    def test_skill_view_05_edit_button_present_for_owner(self):
        """FOB-SKILLS-VIEW_SKILL-05: Edit button is visible for the skill owner."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="edit-skill-btn"' in response.content

    def test_skill_view_06_delete_button_present_for_owner(self):
        """FOB-SKILLS-VIEW_SKILL-06: Delete button is visible for the skill owner."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="delete-skill-btn"' in response.content

    def test_skill_view_no_skill_shows_create_cta(self):
        """When activity has no skill, detail page shows create CTA."""
        from methodology.models import Skill
        self.skill.delete()
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="create-skill-cta"' in response.content

    def test_skill_view_requires_authentication(self):
        """Skill detail requires login."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_skill_view_requires_ownership(self):
        """Non-owner cannot view skill of another user's playbook."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')

        response = self.client.get(self._url())

        assert response.status_code == 302
        assert reverse('playbook_list') in response.url
