"""
Integration tests for Skill CREATE operation.

Tests skill creation form, validation, and success scenarios.
Covers scenarios: FOB-SKILLS-CREATE_SKILL-01 through FOB-SKILLS-CREATE_SKILL-05.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestSkillCreate:
    """Integration tests for skill create functionality."""

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

    def _url(self):
        return reverse('skill_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })

    def test_skill_create_01_open_create_form(self):
        """FOB-SKILLS-CREATE_SKILL-01: Create skill form opens successfully."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'Create Skill' in response.content
        assert b'data-testid="skill-form"' in response.content
        assert b'data-testid="title-input"' in response.content
        assert b'data-testid="content-input"' in response.content

    def test_skill_create_02_create_skill_successfully(self):
        """FOB-SKILLS-CREATE_SKILL-02: Skill is created with valid data."""
        from methodology.models import Skill
        data = {
            'title': 'Setup React Component',
            'content': 'Step-by-step guide to create a new React component',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        skill = Skill.objects.get(activity=self.activity)
        assert skill.title == 'Setup React Component'
        assert 'Step-by-step' in skill.content

    def test_skill_create_02_redirects_to_detail_on_success(self):
        """FOB-SKILLS-CREATE_SKILL-02: Success redirects to skill detail page."""
        data = {
            'title': 'Setup React Component',
            'content': 'Step-by-step guide',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        expected_url = reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })
        assert response.url == expected_url

    def test_skill_create_03_validate_required_title(self):
        """FOB-SKILLS-CREATE_SKILL-03: Validation error when title is empty."""
        data = {
            'title': '',
            'content': 'Some content',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert b'data-testid="title-error"' in response.content

    def test_skill_create_03_prevent_duplicate_for_activity(self):
        """Cannot create a second skill for the same activity."""
        from methodology.models import Skill
        Skill.objects.create(
            activity=self.activity,
            title='Existing Skill',
            content='Already exists'
        )
        data = {
            'title': 'Another Skill',
            'content': 'Duplicate attempt',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 200
        assert Skill.objects.filter(activity=self.activity).count() == 1

    def test_skill_create_requires_authentication(self):
        """Skill create requires login."""
        self.client.logout()
        response = self.client.get(self._url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_skill_create_requires_ownership(self):
        """Non-owner cannot create skill for another user's activity."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')

        response = self.client.post(self._url(), {'title': 'Hack', 'content': 'x'})

        assert response.status_code == 302
        assert reverse('playbook_list') in response.url
