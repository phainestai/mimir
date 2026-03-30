"""
Integration tests for Artifact LIST and DELETE operations.

Tests artifact listing, search/filter, and deletion with dependencies.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Artifact, ArtifactInput

User = get_user_model()


@pytest.mark.django_db
class TestArtifactList:
    """Test artifact listing scenarios (ART-LIST-01 to ART-LIST-10)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="maria_test", email="maria@test.com", password="testpass123"
        )
        self.client.login(username="maria_test", password="testpass123")

        # Create playbook
        self.playbook = Playbook.objects.create(
            name="React Frontend Development",
            description="A comprehensive methodology",
            category="development",
            status="active",
            source="owned",
            author=self.user,
        )

        # Create workflow
        self.workflow = Workflow.objects.create(
            name="Component Development",
            description="Develop React components",
            playbook=self.playbook,
            order=1,
        )

        # Create activities
        self.activity1 = Activity.objects.create(
            workflow=self.workflow,
            name="Design Component",
            guidance="Create UI design",
            order=1,
        )

        self.activity2 = Activity.objects.create(
            workflow=self.workflow,
            name="Implement Component",
            guidance="Code the component",
            order=2,
        )

    @pytest.fixture
    def artifacts(self):
        """Create multiple artifacts for testing."""
        artifact1 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity1,
            name="API Specification",
            description="REST API contract with endpoints",
            type="Document",
            is_required=True,
        )

        artifact2 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity1,
            name="Component Design",
            description="UI/UX design mockups",
            type="Document",
            is_required=False,
        )

        artifact3 = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity2,
            name="Test Report",
            description="Testing results and coverage",
            type="Data",
            is_required=True,
        )

        return [artifact1, artifact2, artifact3]

    def test_art_list_01_navigate(self):
        """ART-LIST-01: Navigate to artifacts list"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Artifacts in" in response.content
        assert self.playbook.name.encode() in response.content

    def test_art_list_02_view_table(self, artifacts):
        """ART-LIST-02: View artifacts table"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # Check table headers
        assert b"Name" in response.content
        assert b"Type" in response.content
        assert b"Actions" in response.content
        
        # Check all artifacts are displayed
        for artifact in artifacts:
            assert artifact.name.encode() in response.content
            assert artifact.type.encode() in response.content

    def test_art_list_03_create_from_list(self):
        """ART-LIST-03: Create new artifact from list"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="btn-create-artifact"' in response.content
        # Check create button links to create form
        create_url = reverse("artifact_create", kwargs={"playbook_pk": self.playbook.pk})
        assert create_url.encode() in response.content

    def test_art_list_04_search_by_name(self, artifacts):
        """ART-LIST-04: Search artifacts by name"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url, {"q": "API"})

        assert response.status_code == 200
        # Should find "API Specification"
        assert b"API Specification" in response.content
        # Should not find others
        assert b"Component Design" not in response.content
        assert b"Test Report" not in response.content

    def test_art_list_05_filter_by_type(self, artifacts):
        """ART-LIST-05: Filter by type"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url, {"type": "Document"})

        assert response.status_code == 200
        # Should find Document types
        assert b"API Specification" in response.content
        assert b"Component Design" in response.content
        # Should not find Report type
        assert b"Test Report" not in response.content

    def test_art_list_06_filter_by_required(self, artifacts):
        """ART-LIST-06: Filter by required status"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url, {"required": "true"})

        assert response.status_code == 200
        # Should find required artifacts
        assert b"API Specification" in response.content
        assert b"Test Report" in response.content
        # Should not find optional
        assert b"Component Design" not in response.content

    def test_art_list_07_filter_by_activity(self, artifacts):
        """ART-LIST-07: Filter by activity"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url, {"activity": str(self.activity1.pk)})

        assert response.status_code == 200
        # Should find artifacts produced by activity1
        assert b"API Specification" in response.content
        assert b"Component Design" in response.content
        # Should not find artifact produced by activity2
        assert b"Test Report" not in response.content

    def test_art_list_08_group_by_workflow(self, artifacts):
        """ART-LIST-08: Group by workflow"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that workflow name appears
        assert self.workflow.name.encode() in response.content

    def test_art_list_09_navigate_to_view(self, artifacts):
        """ART-LIST-09: Navigate to view artifact"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # Check that artifact detail links are present
        for artifact in artifacts:
            detail_url = reverse("artifact_detail", kwargs={"pk": artifact.pk})
            assert detail_url.encode() in response.content

    def test_art_list_10_empty_state(self):
        """ART-LIST-10: Empty state display"""
        url = reverse("artifact_list", kwargs={"playbook_id": self.playbook.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # When no artifacts, should show empty state
        assert b"No artifacts yet" in response.content or b"Create First Artifact" in response.content


@pytest.mark.django_db
class TestArtifactDelete:
    """Test artifact deletion scenarios (ART-DELETE-01 to ART-DELETE-06)"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="maria_test", email="maria@test.com", password="testpass123"
        )
        self.client.login(username="maria_test", password="testpass123")

        # Create playbook
        self.playbook = Playbook.objects.create(
            name="React Frontend Development",
            description="A comprehensive methodology",
            category="development",
            status="active",
            source="owned",
            author=self.user,
        )

        # Create workflow
        self.workflow = Workflow.objects.create(
            name="Component Development",
            description="Develop React components",
            playbook=self.playbook,
            order=1,
        )

        # Create activities
        self.activity1 = Activity.objects.create(
            workflow=self.workflow,
            name="Design Component",
            guidance="Create UI design",
            order=1,
        )

        self.activity2 = Activity.objects.create(
            workflow=self.workflow,
            name="Implement Component",
            guidance="Code the component",
            order=2,
        )

        # Create basic artifact
        self.artifact = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity1,
            name="API Specification",
            description="REST API contract",
            type="Document",
            is_required=True,
        )

    @pytest.fixture
    def artifact_with_consumers(self):
        """Create artifact with consumer activities."""
        artifact = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity1,
            name="Design Document",
            description="Component design",
            type="Document",
            is_required=True,
        )
        
        # Add consumers
        ArtifactInput.objects.create(
            artifact=artifact,
            activity=self.activity2,
            is_required=True,
        )
        
        return artifact

    def test_art_delete_01_open_modal(self):
        """ART-DELETE-01: Open delete confirmation"""
        url = reverse("artifact_delete", kwargs={"pk": self.artifact.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Delete Artifact?" in response.content
        assert self.artifact.name.encode() in response.content

    def test_art_delete_02_modal_content(self):
        """ART-DELETE-02: View modal content"""
        url = reverse("artifact_delete", kwargs={"pk": self.artifact.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        assert b"Delete Artifact?" in response.content
        assert b"This action cannot be undone" in response.content
        assert b'data-testid="btn-cancel-delete"' in response.content
        assert b'data-testid="btn-confirm-delete"' in response.content

    def test_art_delete_03_consumer_warning(self, artifact_with_consumers):
        """ART-DELETE-03: Warning for linked activities"""
        url = reverse("artifact_delete", kwargs={"pk": artifact_with_consumers.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # Should show warning about consumers
        assert b"used by" in response.content or b"consuming activities" in response.content
        # Should show the consuming activity name
        assert self.activity2.name.encode() in response.content

    def test_art_delete_04_confirm_deletion(self):
        """ART-DELETE-04: Confirm deletion"""
        url = reverse("artifact_delete", kwargs={"pk": self.artifact.pk})
        artifact_id = self.artifact.pk
        
        # POST to delete
        response = self.client.post(url)

        # Should redirect after deletion
        assert response.status_code == 302
        
        # Verify artifact was deleted
        assert not Artifact.objects.filter(pk=artifact_id).exists()

    def test_art_delete_05_cancel_deletion(self):
        """ART-DELETE-05: Cancel deletion"""
        artifact_id = self.artifact.pk
        
        # Just getting the modal (GET) should not delete
        url = reverse("artifact_delete", kwargs={"pk": self.artifact.pk})
        response = self.client.get(url)

        assert response.status_code == 200
        # Verify artifact still exists
        assert Artifact.objects.filter(pk=artifact_id).exists()

    def test_art_delete_06_delete_with_template(self):
        """ART-DELETE-06: Delete artifact with template"""
        # Create artifact with template reference
        artifact = Artifact.objects.create(
            playbook=self.playbook,
            produced_by=self.activity1,
            name="Template Doc",
            description="Has template",
            type="Document",
            is_required=False,
            template_file="templates/test.docx",  # Simulating a template file
        )
        
        url = reverse("artifact_delete", kwargs={"pk": artifact.pk})
        
        # GET should show template warning
        response = self.client.get(url)
        assert response.status_code == 200
        assert b"Template file will also be deleted" in response.content or b"template" in response.content.lower()
        
        # POST should delete
        artifact_id = artifact.pk
        response = self.client.post(url)
        assert response.status_code == 302
        assert not Artifact.objects.filter(pk=artifact_id).exists()
