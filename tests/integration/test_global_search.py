import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook, Workflow, Activity


@pytest.mark.django_db
class TestGlobalSearchView:
    """Integration tests for NAV-06 Global search endpoint and navbar wiring."""

    def _create_sample_data(self, user: User):
        playbook = Playbook.objects.create(
            name="Component Development Playbook",
            description="Playbook for components",
            category="development",
            author=user,
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

    def test_global_search_page_shows_results_for_query(self):
        """NAV-06: Global search page returns results across Playbooks, Workflows, Activities."""
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        client.force_login(user)

        self._create_sample_data(user)

        url = reverse("global_search")
        response = client.get(url, {"q": "Component"})

        assert response.status_code == 200
        html = response.content.decode("utf-8")

        assert "Component Development Playbook" in html
        assert "Component Workflow" in html
        assert "Create Component" in html

    def test_global_search_type_filter_playbooks_only(self):
        """Type filter should allow showing only playbooks in the results page."""
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        client.force_login(user)

        self._create_sample_data(user)

        url = reverse("global_search")
        response = client.get(url, {"q": "Component", "type": "playbooks"})

        assert response.status_code == 200
        html = response.content.decode("utf-8")

        # Playbook should still be visible
        assert "Component Development Playbook" in html
        # Workflow and activity names should be hidden when filtered by playbooks
        assert "Component Workflow" not in html
        assert "Create Component" not in html

    def test_navbar_contains_global_search_form_for_authenticated_user(self):
        """Navbar should contain global search form when user is authenticated."""
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        client.force_login(user)

        response = client.get("/")
        assert response.status_code == 200
        html = response.content.decode("utf-8")

        assert 'data-testid="global-search-form"' in html
        assert 'data-testid="global-search-input"' in html
        assert 'name="q"' in html

    def test_navbar_does_not_show_global_search_for_anonymous_user(self):
        """Navbar should not show global search form for anonymous user."""
        client = Client()

        response = client.get("/")
        assert response.status_code == 200
        html = response.content.decode("utf-8")

        assert 'data-testid="global-search-form"' not in html
        assert 'data-testid="global-search-input"' not in html

    def test_global_search_suggestions_returns_results_fragment(self):
        """Suggestions endpoint should return HTML fragment with matching entities."""
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        client.force_login(user)

        self._create_sample_data(user)

        url = reverse("global_search_suggestions")
        response = client.get(url, {"q": "Component"})

        assert response.status_code == 200
        html = response.content.decode("utf-8")

        assert "Component Development Playbook" in html
        assert "Component Workflow" in html
        assert "Create Component" in html

    def test_global_search_suggestions_requires_authentication(self):
        """Suggestions endpoint should redirect anonymous users to login."""
        client = Client()

        url = reverse("global_search_suggestions")
        response = client.get(url, {"q": "Component"})

        assert response.status_code in (302, 301)

    def test_global_search_suggestions_empty_query_returns_empty_fragment(self):
        """Empty or whitespace-only query should return an empty suggestions fragment."""
        client = Client()
        user = User.objects.create_user(
            username="maria",
            email="maria@example.com",
            password="SecurePass123",
        )
        client.force_login(user)

        url = reverse("global_search_suggestions")
        response = client.get(url, {"q": " "})

        assert response.status_code == 200
        html = response.content.decode("utf-8")

        assert "Component Development Playbook" not in html
        assert "Component Workflow" not in html
        assert "Create Component" not in html
