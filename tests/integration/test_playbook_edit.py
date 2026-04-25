"""
Integration tests for Playbook EDIT operation.

Covers the edit form GET/POST lifecycle, including tags_string context
presence, tags persistence on save, and the ValidationError render path.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Playbook

User = get_user_model()


@pytest.mark.django_db
class TestPlaybookEdit:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='edit_user', password='testpass123'
        )
        self.client.force_login(self.user)

    def _make_playbook(self, tags=None):
        return Playbook.objects.create(
            name='Test Playbook',
            description='Desc',
            category='development',
            author=self.user,
            tags=tags or [],
        )

    # --- GET ---

    def test_edit_get_renders_200(self):
        """GET /playbooks/<pk>/edit/ returns 200."""
        pb = self._make_playbook()
        response = self.client.get(reverse('playbook_edit', kwargs={'pk': pb.pk}))
        assert response.status_code == 200

    def test_edit_get_tags_string_in_context_no_tags(self):
        """tags_string is empty string when playbook has no tags."""
        pb = self._make_playbook(tags=[])
        response = self.client.get(reverse('playbook_edit', kwargs={'pk': pb.pk}))
        assert response.status_code == 200
        assert 'tags_string' in response.context
        assert response.context['tags_string'] == ''

    def test_edit_get_tags_string_in_context_with_tags(self):
        """tags_string is comma-joined when playbook has tags."""
        pb = self._make_playbook(tags=['product', 'discovery'])
        response = self.client.get(reverse('playbook_edit', kwargs={'pk': pb.pk}))
        assert response.status_code == 200
        assert response.context['tags_string'] == 'product, discovery'

    # --- POST: empty name (validation error path) ---

    def test_edit_post_empty_name_tags_string_in_context(self):
        """tags_string is preserved in context when POST fails due to empty name."""
        pb = self._make_playbook()
        response = self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb.pk}),
            {'name': '', 'tags': 'ux, research'},
        )
        assert response.status_code == 200
        assert 'tags_string' in response.context
        assert response.context['tags_string'] == 'ux, research'

    def test_edit_post_empty_name_tags_string_empty_when_not_submitted(self):
        """tags_string is empty string when tags not included in failing POST."""
        pb = self._make_playbook()
        response = self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb.pk}),
            {'name': ''},
        )
        assert response.status_code == 200
        assert response.context['tags_string'] == ''

    # --- POST: ValidationError path (duplicate name) ---

    def test_edit_post_duplicate_name_tags_string_in_context(self):
        """tags_string is preserved in context when POST fails due to duplicate name."""
        self._make_playbook()
        pb2 = Playbook.objects.create(
            name='Other Playbook',
            description='Another one',
            category='development',
            author=self.user,
            tags=[],
        )
        response = self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb2.pk}),
            {
                'name': 'Test Playbook',
                'description': 'Updated',
                'category': 'development',
                'visibility': 'private',
                'tags': 'ux, research',
            },
        )
        assert response.status_code == 200
        assert 'tags_string' in response.context
        assert response.context['tags_string'] == 'ux, research'

    # --- POST: success ---

    def test_edit_post_success_redirects(self):
        """Valid POST updates playbook and redirects to detail."""
        pb = self._make_playbook()
        response = self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb.pk}),
            {
                'name': 'Updated Name',
                'description': 'Updated',
                'category': 'development',
                'visibility': 'private',
            },
        )
        assert response.status_code == 302
        assert response['Location'] == reverse('playbook_detail', kwargs={'pk': pb.pk})
        pb.refresh_from_db()
        assert pb.name == 'Updated Name'

    def test_edit_post_tags_are_persisted(self):
        """Tags submitted in POST are saved to the playbook."""
        pb = self._make_playbook(tags=[])
        self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb.pk}),
            {
                'name': 'Test Playbook',
                'description': 'Desc',
                'category': 'development',
                'visibility': 'private',
                'tags': 'ux, research',
            },
        )
        pb.refresh_from_db()
        assert pb.tags == ['ux', 'research']

    def test_edit_post_tags_cleared_when_empty(self):
        """Submitting empty tags clears the playbook tags."""
        pb = self._make_playbook(tags=['ux', 'research'])
        self.client.post(
            reverse('playbook_edit', kwargs={'pk': pb.pk}),
            {
                'name': 'Test Playbook',
                'description': 'Desc',
                'category': 'development',
                'visibility': 'private',
                'tags': '',
            },
        )
        pb.refresh_from_db()
        assert pb.tags == []
