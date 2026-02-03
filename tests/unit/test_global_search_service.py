import pytest
from django.contrib.auth.models import User

from methodology.models import Playbook, Workflow, Activity
from methodology.services.global_search_service import GlobalSearchService


@pytest.mark.django_db
class TestGlobalSearchService:
    """Unit tests for GlobalSearchService search behavior."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        self.service = GlobalSearchService()

    def test_search_returns_playbooks_workflows_activities_for_query(self):
        """Search should return results across Playbooks, Workflows, Activities for matching query."""
        playbook = Playbook.objects.create(
            name="Component Development Playbook",
            description="Playbook for building components",
            category="development",
            author=self.user,
        )
        workflow = Workflow.objects.create(
            playbook=playbook,
            name="Component Workflow",
            description="Workflow for component work",
            order=1,
        )
        Activity.objects.create(
            workflow=workflow,
            name="Create Component",
            guidance="Do component work",
            order=1,
        )

        results = self.service.search(query="Component", user=self.user, filters=None)

        assert "playbooks" in results
        assert "workflows" in results
        assert "activities" in results

        assert any("Component" in pb.name for pb in results["playbooks"])
        assert any("Component" in wf.name for wf in results["workflows"])
        assert any("Component" in act.name for act in results["activities"])

    def test_search_with_no_matches_returns_empty_lists(self):
        """Search with no matches should return empty lists for all entity types."""
        results = self.service.search(query="NonExistingQuery", user=self.user, filters=None)

        assert results["playbooks"] == []
        assert results["workflows"] == []
        assert results["activities"] == []

    def test_search_with_type_filter_limits_entity_lists(self):
        """Type filter should limit which entity lists are populated in the result."""
        playbook = Playbook.objects.create(
            name="Component Development Playbook",
            description="Playbook for components",
            category="development",
            author=self.user,
        )
        workflow = Workflow.objects.create(
            playbook=playbook,
            name="Component Workflow",
            description="Workflow for components",
            order=1,
        )
        Activity.objects.create(
            workflow=workflow,
            name="Create Component",
            guidance="Do component work",
            order=1,
        )

        results = self.service.search(query="Component", user=self.user, filters={"type": "playbooks"})

        assert results["playbooks"], "Playbooks list should not be empty when type=playbooks"
        assert results["workflows"] == [], "Workflows list should be empty when type=playbooks"
        assert results["activities"] == [], "Activities list should be empty when type=playbooks"
