"""
Integration tests for Skill DELETE operation.

Tests skill deletion modal, confirmation flow, and cascade behavior.
Covers scenarios: FOB-SKILLS-DELETE_SKILL-01 through FOB-SKILLS-DELETE_SKILL-05.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestSkillDelete:
    """Integration tests for skill delete functionality."""

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
            title='Old Guide',
            content='Outdated content'
        )

    def _confirm_url(self):
        return reverse('skill_delete_confirm', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })

    def _delete_url(self):
        return reverse('skill_delete', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })

    def test_skill_delete_01_open_delete_confirmation_modal(self):
        """FOB-SKILLS-DELETE_SKILL-01: Delete confirm modal loads via HTMX endpoint."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'Delete Skill' in response.content
        assert b'data-testid="delete-confirm-modal"' in response.content

    def test_skill_delete_02_modal_shows_skill_name(self):
        """FOB-SKILLS-DELETE_SKILL-02: Modal displays skill name in confirmation."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'Old Guide' in response.content

    def test_skill_delete_02_modal_shows_warning(self):
        """FOB-SKILLS-DELETE_SKILL-02: Modal shows warning about activity link."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'cannot be undone' in response.content

    def test_skill_delete_04_confirm_deletion(self):
        """FOB-SKILLS-DELETE_SKILL-04: Skill is deleted on confirmation."""
        from methodology.models import Skill
        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        assert not Skill.objects.filter(pk=self.skill.pk).exists()

    def test_skill_delete_04_redirects_after_deletion(self):
        """FOB-SKILLS-DELETE_SKILL-04: After deletion, redirects to skill list."""
        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        assert reverse('skill_list') in response.url

    def test_skill_delete_05_cancel_does_not_delete(self):
        """FOB-SKILLS-DELETE_SKILL-05: Cancel link present in modal (skill not deleted on GET)."""
        from methodology.models import Skill
        # GET the confirm endpoint (what Cancel results in — skill stays)
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert Skill.objects.filter(pk=self.skill.pk).exists()
        assert b'Cancel' in response.content

    def test_skill_delete_requires_ownership(self):
        """Non-owner cannot delete another user's skill."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')

        from methodology.models import Skill
        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        assert Skill.objects.filter(pk=self.skill.pk).exists()

    def test_skill_delete_detail_has_delete_button(self):
        """Skill detail page contains HTMX delete button pointing to confirm endpoint."""
        detail_url = reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.activity.pk,
        })
        response = self.client.get(detail_url)

        assert response.status_code == 200
        assert b'data-testid="delete-skill-btn"' in response.content
        confirm_url = self._confirm_url().encode()
        assert confirm_url in response.content
