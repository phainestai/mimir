"""
Integration tests for Skill DELETE operation (playbook-scoped).

Tests skill deletion modal, confirmation flow, and activity FK clearing.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Skill

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

        self.skill = Skill.objects.create(
            playbook=self.playbook,
            title='Old Guide',
            capability_domain='GUI_FORM',
            technology_stack='React+Redux',
            content='Outdated content',
        )

    def _confirm_url(self):
        return reverse('skill_delete_confirm', kwargs={
            'playbook_pk': self.playbook.pk,
            'skill_pk': self.skill.pk,
        })

    def _delete_url(self):
        return reverse('skill_delete', kwargs={
            'playbook_pk': self.playbook.pk,
            'skill_pk': self.skill.pk,
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

    def test_skill_delete_02_modal_shows_metadata(self):
        """FOB-SKILLS-DELETE_SKILL-02: Modal shows capability_domain and technology_stack."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'GUI_FORM' in response.content
        assert b'React+Redux' in response.content

    def test_skill_delete_02_modal_shows_warning(self):
        """FOB-SKILLS-DELETE_SKILL-02: Modal shows warning about permanent deletion."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'cannot be undone' in response.content

    def test_skill_delete_03_modal_warns_about_linked_activities(self):
        """FOB-SKILLS-DELETE_SKILL-03: Modal warns when activities reference this skill."""
        activity = Activity.objects.create(
            name='Build Form',
            guidance='Uses form skill',
            workflow=self.workflow,
            order=1,
        )
        activity.skills.add(self.skill)
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert b'1 activity' in response.content

    def test_skill_delete_04_confirm_deletion(self):
        """FOB-SKILLS-DELETE_SKILL-04: Skill is deleted on confirmation."""
        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        assert not Skill.objects.filter(pk=self.skill.pk).exists()

    def test_skill_delete_04_redirects_to_playbook_skill_list(self):
        """FOB-SKILLS-DELETE_SKILL-04: After deletion, redirects to playbook skill list."""
        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        expected = reverse('skill_list_playbook', kwargs={'playbook_pk': self.playbook.pk})
        assert response.url == expected

    def test_skill_delete_04_clears_activity_m2m(self):
        """FOB-SKILLS-DELETE_SKILL-04: Deleting skill removes M2M links from activities."""
        activity = Activity.objects.create(
            name='Build Form',
            guidance='Uses form skill',
            workflow=self.workflow,
            order=1,
        )
        activity.skills.add(self.skill)
        self.client.post(self._delete_url())

        activity.refresh_from_db()
        assert activity.skills.count() == 0

    def test_skill_delete_05_cancel_does_not_delete(self):
        """FOB-SKILLS-DELETE_SKILL-05: Cancel link present; skill not deleted on GET."""
        response = self.client.get(self._confirm_url())

        assert response.status_code == 200
        assert Skill.objects.filter(pk=self.skill.pk).exists()
        assert b'Cancel' in response.content

    def test_skill_delete_requires_ownership(self):
        """Non-owner cannot delete another user's skill."""
        other_user = User.objects.create_user(username='other', password='pass123')
        self.client.login(username='other', password='pass123')

        response = self.client.post(self._delete_url())

        assert response.status_code == 302
        assert Skill.objects.filter(pk=self.skill.pk).exists()

    def test_skill_delete_detail_has_delete_button(self):
        """Skill detail page contains HTMX delete button pointing to confirm endpoint."""
        detail_url = reverse('skill_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'skill_pk': self.skill.pk,
        })
        response = self.client.get(detail_url)

        assert response.status_code == 200
        assert b'data-testid="delete-skill-btn"' in response.content
        confirm_url = self._confirm_url().encode()
        assert confirm_url in response.content
