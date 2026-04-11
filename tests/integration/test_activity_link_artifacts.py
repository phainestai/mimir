"""
Integration tests for Activity-Artifact linking functionality.

Tests artifact checkboxes on edit form and artifacts card on detail view.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Playbook, Workflow, Activity, Artifact, ArtifactInput

User = get_user_model()


@pytest.mark.django_db
class TestActivityLinkArtifacts:
    """Integration tests for linking artifacts to activities."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_artifact_link',
            email='maria@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_artifact_link', password='testpass123')

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
        
        self.producer_activity = Activity.objects.create(
            workflow=self.workflow,
            name='Design API',
            guidance='Design the API',
            order=1
        )
        
        self.consumer_activity = Activity.objects.create(
            workflow=self.workflow,
            name='Implement Backend',
            guidance='Backend implementation',
            order=2
        )

        self.artifact1 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.producer_activity,
            name='API Specification',
            type='Document',
            is_required=True
        )
        
        self.artifact2 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.producer_activity,
            name='Database Schema',
            type='Document',
            is_required=False
        )
        
        self.artifact3 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.producer_activity,
            name='Test Plan',
            type='Document',
            is_required=False
        )

    def test_edit_form_shows_artifact_checkboxes(self):
        """Checkbox list is present with playbook artifacts."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="artifact-inputs-list"' in response.content
        assert b'API Specification' in response.content
        assert b'Database Schema' in response.content
        assert b'Test Plan' in response.content

    def test_link_multiple_artifacts(self):
        """Check 3 artifacts, save, verify all linked."""
        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        
        response = self.client.post(url, {
            'name': self.consumer_activity.name,
            'guidance': self.consumer_activity.guidance,
            'order': self.consumer_activity.order,
            'artifact_inputs': [self.artifact1.id, self.artifact2.id, self.artifact3.id],
        })

        assert response.status_code == 302
        artifact_inputs = ArtifactInput.objects.filter(activity=self.consumer_activity)
        assert artifact_inputs.count() == 3
        artifact_ids = set(artifact_inputs.values_list('artifact_id', flat=True))
        assert artifact_ids == {self.artifact1.id, self.artifact2.id, self.artifact3.id}

    def test_unlink_artifacts(self):
        """Uncheck 2 artifacts, save, verify removed."""
        # First link all 3 artifacts
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact1)
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact2)
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact3)

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        
        # Only keep artifact1
        response = self.client.post(url, {
            'name': self.consumer_activity.name,
            'guidance': self.consumer_activity.guidance,
            'order': self.consumer_activity.order,
            'artifact_inputs': [self.artifact1.id],
        })

        assert response.status_code == 302
        artifact_inputs = ArtifactInput.objects.filter(activity=self.consumer_activity)
        assert artifact_inputs.count() == 1
        assert artifact_inputs.first().artifact_id == self.artifact1.id

    def test_cannot_link_self_produced_artifact(self):
        """Activity's own output not in checkbox list."""
        # Create an artifact produced by the consumer activity itself
        self_artifact = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.consumer_activity,
            name='Backend Code',
            type='Code'
        )

        url = reverse('activity_edit', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        # Should show artifacts from other activities
        assert b'API Specification' in response.content
        # Should NOT show artifact produced by this activity
        assert b'Backend Code' not in response.content

    def test_detail_shows_artifact_inputs(self):
        """Artifacts card shows all inputs."""
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact1, is_required=True)
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact2, is_required=False)

        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="artifacts-card"' in response.content
        assert b'API Specification' in response.content
        assert b'Database Schema' in response.content
        # Check for count badge
        assert b'<span class="badge bg-secondary ms-2">2</span>' in response.content

    def test_detail_shows_no_artifacts_state(self):
        """Empty state when no inputs."""
        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="artifacts-card"' in response.content
        assert b'data-testid="no-artifacts"' in response.content
        assert b'No input artifacts' in response.content

    def test_artifact_required_badge_displayed(self):
        """Required artifacts show badge."""
        ArtifactInput.objects.create(activity=self.consumer_activity, artifact=self.artifact1, is_required=True)

        url = reverse('activity_detail', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk,
            'activity_pk': self.consumer_activity.pk
        })
        response = self.client.get(url)

        assert response.status_code == 200
        # Check for required badge
        assert b'<span class="badge bg-danger ms-1">Required</span>' in response.content
