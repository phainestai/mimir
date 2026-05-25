"""
Integration tests for Activity-Skill linking functionality.

Tests multi-skill checkboxes on edit form and skills list on detail view.
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

        self.skill2 = Skill.objects.create(
            playbook=self.playbook,
            title='Deploy to AWS Beanstalk',
            content='Beanstalk deployment',
            capability_domain='DEPLOY',
            technology_stack='AWS+Beanstalk'
        )

    def test_edit_form_shows_skill_checkboxes(self):
        """Skill checkboxes are present with playbook skills."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="activity-skills-select"' in response.content
        assert b'React Development' in response.content
        assert b'Deploy to AWS Beanstalk' in response.content

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
            'skills': [self.skill.id],
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert list(self.activity.skills.values_list('id', flat=True)) == [self.skill.id]

    def test_link_multiple_skills_to_activity(self):
        """Select two skills and save, verify both linked."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })

        response = self.client.post(url, {
            'name': self.activity.name,
            'guidance': self.activity.guidance,
            'order': self.activity.order,
            'skills': [self.skill.id, self.skill2.id],
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert set(self.activity.skills.values_list('id', flat=True)) == {self.skill.id, self.skill2.id}

    def test_unlink_skill_from_activity(self):
        """Uncheck all skills and save, verify links removed."""
        self.activity.skills.set([self.skill, self.skill2])

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })

        response = self.client.post(url, {
            'name': self.activity.name,
            'guidance': self.activity.guidance,
            'order': self.activity.order,
        })

        assert response.status_code == 302
        self.activity.refresh_from_db()
        assert self.activity.skills.count() == 0

    def test_skill_checkboxes_only_show_playbook_skills(self):
        """No cross-playbook skills in checkbox list."""
        other_playbook = Playbook.objects.create(
            name='Other Playbook',
            description='Other',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        Skill.objects.create(
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

    def test_detail_shows_linked_skills(self):
        """Skills card displays all linked skills."""
        self.activity.skills.set([self.skill, self.skill2])

        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-card"' in response.content
        assert b'data-testid="activity-skills-list"' in response.content
        assert b'React Development' in response.content
        assert b'Deploy to AWS Beanstalk' in response.content
        assert b'data-testid="skill-link-' in response.content
        assert b'GUI_FORM' in response.content
        assert b'React+Redux' in response.content

    def test_detail_shows_no_skill_state(self):
        """Empty state when no skills linked."""
        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="skill-card"' in response.content
        assert b'data-testid="no-skill"' in response.content
        assert b'No skills linked' in response.content
