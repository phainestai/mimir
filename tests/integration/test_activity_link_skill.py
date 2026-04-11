"""
Integration tests for Activity-Skill linking functionality.

Tests skill dropdown on edit form and skill card on detail view.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Playbook, Workflow, Activity, Skill

User = get_user_model()


@pytest.mark.django_db
class TestActivityLinkSkill:
    """Integration tests for linking skills to activities."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_skill_link',
            email='maria@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_skill_link', password='testpass123')

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

        self.skill = Skill.objects.create(
            playbook=self.playbook,
            title='React Development',
            content='React development skills',
            capability_domain='GUI_FORM',
            technology_stack='React+Redux'
        )

    def test_edit_form_shows_skill_dropdown(self):
        """Skill dropdown is present with playbook skills."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-select"' in response.content
        assert b'React Development' in response.content

    def test_link_skill_to_activity(self):
        """Select skill and save, verify link created."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        
        response = self.client.post(url, {
            'name': self.activity.name,
            'guidance': self.activity.guidance,
            'order': self.activity.order,
            'skill': self.skill.id,
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert self.activity.skill_id == self.skill.id

    def test_unlink_skill_from_activity(self):
        """Select 'None' and save, verify link removed."""
        # First link a skill
        self.activity.skill = self.skill
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
            'skill': '',  # Empty = None
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert self.activity.skill_id is None

    def test_skill_dropdown_only_shows_playbook_skills(self):
        """No cross-playbook skills in dropdown."""
        other_playbook = Playbook.objects.create(
            name='Other Playbook',
            description='Other',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        other_skill = Skill.objects.create(
            playbook=other_playbook,
            title='Other Skill',
            content='From other playbook'
        )

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'React Development' in response.content
        assert b'Other Skill' not in response.content

    def test_detail_shows_linked_skill(self):
        """Skill card displays linked skill."""
        self.activity.skill = self.skill
        self.activity.save()

        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-card"' in response.content
        assert b'React Development' in response.content
        assert b'data-testid="skill-link"' in response.content
        assert b'GUI_FORM' in response.content
        assert b'React+Redux' in response.content

    def test_detail_shows_no_skill_state(self):
        """Empty state when no skill linked."""
        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-card"' in response.content
        assert b'data-testid="no-skill"' in response.content
        assert b'No skill required' in response.content
