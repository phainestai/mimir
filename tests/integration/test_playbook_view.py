"""Integration tests for Playbook VIEW operations."""

from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow

User = get_user_model()


@pytest.mark.django_db
class TestPlaybookView:
    """Integration tests for playbook detail view - 24 scenarios."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_test',
            email='maria@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_test', password='testpass123')
        
        self.playbook = Playbook.objects.create(
            name='React Frontend Development',
            description='A comprehensive methodology',
            category='development',
            tags=['react', 'frontend'],
            status='active',
            version=2,
            author=self.user
        )
    
    def test_pb_view_01_open_playbook_detail_page(self):
        """PB-VIEW-01: Open playbook detail page."""
        response = self.client.get(reverse('playbook_detail', kwargs={'pk': self.playbook.id}))
        assert response.status_code == 200
    
    def test_pb_view_02_view_header_information(self):
        """PB-VIEW-02: View header with name, version, status, author, timestamps."""
        response = self.client.get(reverse('playbook_detail', kwargs={'pk': self.playbook.id}))
        
        assert response.status_code == 200
        assert b'React Frontend Development' in response.content
        assert b'v2' in response.content
        assert b'Active' in response.content or b'active' in response.content
        assert b'data-testid="playbook-header"' in response.content
        assert b'data-testid="version-badge"' in response.content
        assert b'data-testid="status-badge"' in response.content
        assert b'data-testid="playbook-content-browser"' in response.content
    
    def test_pb_view_03_view_overview_tab_default(self):
        """PB-VIEW-03: Overview tab selected by default with quick stats."""
        response = self.client.get(reverse('playbook_detail', kwargs={'pk': self.playbook.id}))
        
        assert response.status_code == 200
        # Check Overview tab is default/active
        assert b'data-testid="tab-overview"' in response.content
        assert b'Quick Stats' in response.content
        # Check stats are displayed
        assert b'Workflows' in response.content
        assert b'data-testid="stat-workflows"' in response.content
    
    def test_pb_view_04_view_metadata_in_overview(self):
        """PB-VIEW-04: View metadata (category, tags, created, source)."""
        response = self.client.get(reverse('playbook_detail', kwargs={'pk': self.playbook.id}))
        
        assert response.status_code == 200
        assert b'development' in response.content.lower() or b'Development' in response.content
        assert b'react' in response.content
        assert b'frontend' in response.content
        assert b'data-testid="metadata-section"' in response.content
    
    def test_pb_view_05_view_workflows_list_in_overview(self):
        """PB-VIEW-05: View workflows list in Overview tab."""
        response = self.client.get(reverse('playbook_detail', kwargs={'pk': self.playbook.id}))
        
        assert response.status_code == 200
        assert b'data-testid="workflows-section"' in response.content


@pytest.mark.django_db
class TestPlaybookViewVisibility:
    """Cross-user read access for public vs private playbooks."""

    def test_non_owner_can_view_public_playbook(self):
        mike = User.objects.create_user(username="mike_view", password="x")
        maria = User.objects.create_user(username="maria_view", password="x")
        pb = Playbook.objects.create(
            name="Public Detail PB",
            description="Readable by any authenticated user member",
            category="development",
            author=mike,
            visibility="public",
            status="released",
            version=Decimal("1.0"),
        )
        client = Client()
        client.force_login(maria)
        response = client.get(reverse("playbook_detail", kwargs={"pk": pb.pk}))
        assert response.status_code == 200
        content = response.content.decode("utf-8")
        assert 'data-testid="visibility-badge"' in content
        assert "Public" in content
        assert 'data-testid="delete-button"' not in content
        assert 'data-testid="playbook-content-browser"' in content
        assert f'/browser/{pb.pk}/' in content

    def test_non_owner_gets_404_for_draft_public_playbook(self):
        mike = User.objects.create_user(username="mike_draft_pub", password="x")
        maria = User.objects.create_user(username="maria_draft_pub", password="x")
        pb = Playbook.objects.create(
            name="Draft Public Detail PB",
            description="Draft public stays owner-only for non-owners",
            category="development",
            author=mike,
            visibility="public",
            status="draft",
            version=Decimal("0.1"),
        )
        client = Client()
        client.force_login(maria)
        response = client.get(reverse("playbook_detail", kwargs={"pk": pb.pk}))
        assert response.status_code == 404

    def test_non_owner_gets_404_for_private_playbook(self):
        mike = User.objects.create_user(username="mike_priv", password="x")
        maria = User.objects.create_user(username="maria_priv", password="x")
        pb = Playbook.objects.create(
            name="Private Detail PB",
            description="Only owner should open this playbook ok",
            category="development",
            author=mike,
            visibility="private",
            status="draft",
            version=Decimal("0.1"),
        )
        client = Client()
        client.force_login(maria)
        response = client.get(reverse("playbook_detail", kwargs={"pk": pb.pk}))
        assert response.status_code == 404
