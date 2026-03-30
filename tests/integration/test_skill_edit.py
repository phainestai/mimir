"""
Integration tests for Skill EDIT operation.

Tests skill edit form, field pre-population, and save behavior.
Covers scenarios: FOB-SKILLS-EDIT_SKILL-01 through FOB-SKILLS-EDIT_SKILL-04.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestSkillEdit:
    """Integration tests for skill edit functionality."""

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
            content='Original content'
        )

    def _url(self):
        return reverse('skill_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })

    def test_skill_edit_01_open_edit_form(self):
        """FOB-SKILLS-EDIT_SKILL-01: Edit form opens with pre-populated fields."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        assert b'data-testid="skill-form"' in response.content
        assert b'Setup React Component' in response.content
        assert b'Original content' in response.content

    def test_skill_edit_01_fields_prepopulated(self):
        """FOB-SKILLS-EDIT_SKILL-01: All fields are pre-populated on GET."""
        response = self.client.get(self._url())

        content = response.content.decode()
        assert 'Setup React Component' in content
        assert 'Original content' in content

    def test_skill_edit_02_update_title(self):
        """FOB-SKILLS-EDIT_SKILL-02: Title can be updated successfully."""
        from methodology.models import Skill
        data = {
            'title': 'Advanced React Component Setup',
            'content': 'Original content',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        self.skill.refresh_from_db()
        assert self.skill.title == 'Advanced React Component Setup'

    def test_skill_edit_03_update_content(self):
        """FOB-SKILLS-EDIT_SKILL-03: Content can be updated successfully."""
        from methodology.models import Skill
        data = {
            'title': 'Setup React Component',
            'content': 'Updated content with new steps',
        }
        response = self.client.post(self._url(), data)

        assert response.status_code == 302
        self.skill.refresh_from_db()
        assert 'Updated content with new steps' in self.skill.content

    def test_skill_edit_04_cancel_redirects_to_detail(self):
        """FOB-SKILLS-EDIT_SKILL-04: Cancel link points back to skill detail."""
        response = self.client.get(self._url())

        assert response.status_code == 200
        detail_url = reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })
        assert detail_url.encode() in response.content

    def test_skill_edit_redirects_to_detail_on_save(self):
        """Saving edit redirects to skill detail page."""
        data = {
            'title': 'Updated Title',
            'content': 'Updated content',
        }
        response = self.client.post(self._url(), data)

        expected_url = reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })
        assert response.status_code == 302
        assert response.url == expected_url

    def test_skill_edit_requires_ownership(self):
        """Non-owner cannot edit skill."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')

        response = self.client.post(self._url(), {'title': 'Hack', 'content': 'x'})

        assert response.status_code == 302
        assert reverse('playbook_list') in response.url
