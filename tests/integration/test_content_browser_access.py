"""
Integration tests for Content Browser access and navigation.

Tests scenarios from docs/features/act-16-content-browser/01-access-and-nav.feature.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook, Team, TeamMembership, TeamPlaybook

User = get_user_model()


@pytest.mark.django_db
class TestContentBrowserServerSide:
    """S1 — Server-side scaffold: playbook entry, auth, views, template shell, 404.

    Covers: FOB-CONTENT-BROWSER-01, 01b, 02, 03, 03c
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = Client()
        self.maria = User.objects.create_user(
            username="maria_test", email="maria@test.com", password="testpass123"
        )
        self.bob = User.objects.create_user(
            username="bob_test", email="bob@test.com", password="testpass123"
        )
        self.public_playbook = Playbook.objects.create(
            name="FeatureFactory",
            description="Public playbook",
            category="development",
            author=self.maria,
            visibility="public",
        )
        self.private_playbook = Playbook.objects.create(
            name="Private Playbook",
            description="Private",
            category="development",
            author=self.maria,
            visibility="private",
        )
        self.client.login(username="maria_test", password="testpass123")

    # FOB-CONTENT-BROWSER-01
    def test_content_browser_button_on_playbook_detail_not_in_nav(self):
        """Playbook detail has Content Browser button; navbar does not."""
        detail_url = reverse(
            "playbook_detail", kwargs={"pk": self.public_playbook.pk}
        )
        response = self.client.get(detail_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-testid="playbook-content-browser"' in content
        assert f'href="/browser/{self.public_playbook.pk}/"' in content
        assert 'data-testid="nav-browser"' not in content

    # FOB-CONTENT-BROWSER-01b
    def test_unauthenticated_browser_playbook_redirects_to_login(self):
        """GET /browser/<pk>/ while logged out redirects to login with next= preserved."""
        self.client.logout()
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.status_code == 302
        location = response["Location"]
        assert "login" in location
        assert "next=" in location

    # FOB-CONTENT-BROWSER-02
    def test_browser_root_returns_404(self):
        """GET /browser/ without pk returns 404."""
        response = self.client.get("/browser/")
        assert response.status_code == 404
        assert 'data-testid="browser-canvas"' not in response.content.decode()

    # FOB-CONTENT-BROWSER-03
    def test_browser_playbook_returns_200_for_accessible_playbook(self):
        """GET /browser/<pk>/ returns 200 for a playbook accessible to the user."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.status_code == 200

    # FOB-CONTENT-BROWSER-03
    def test_browser_playbook_passes_pk_as_data_attribute(self):
        """Template contains data-playbook-pk={{ pk }} so JS can init the graph."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.status_code == 200
        assert (
            f'data-playbook-pk="{self.public_playbook.pk}"' in response.content.decode()
        )

    # FOB-CONTENT-BROWSER-03
    def test_browser_playbook_shows_playbook_name_in_left_panel(self):
        """Left panel heading shows the playbook name when pk is provided."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.status_code == 200
        assert "FeatureFactory" in response.content.decode()

    # FOB-CONTENT-BROWSER-03
    def test_browser_playbook_has_no_picker_controls(self):
        """Playbook-scoped browser has no Change/Select playbook controls."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        content = response.content.decode()
        assert 'data-testid="browser-change-playbook"' not in content
        assert 'data-testid="browser-select-playbook"' not in content
        assert 'data-testid="browser-picker"' not in content

    # FOB-CONTENT-BROWSER-03c
    def test_browser_playbook_returns_404_for_nonexistent_pk(self):
        """GET /browser/9999/ returns 404 for a playbook that does not exist."""
        response = self.client.get("/browser/9999/")
        assert response.status_code == 404

    # FOB-CONTENT-BROWSER-03c
    def test_browser_playbook_returns_404_for_inaccessible_private_playbook(self):
        """GET /browser/<pk>/ returns 404 for a private playbook owned by another user.

        Bob cannot access maria's private playbook — 404 does not reveal existence.
        """
        self.client.login(username="bob_test", password="testpass123")
        response = self.client.get(f"/browser/{self.private_playbook.pk}/")
        assert response.status_code == 404

    # FOB-CONTENT-BROWSER-03c
    def test_browser_playbook_404_does_not_render_browser_chrome(self):
        """The 404 response renders Django's standard 404, not the browser shell."""
        response = self.client.get("/browser/9999/")
        assert response.status_code == 404
        assert 'data-testid="browser-canvas"' not in response.content.decode()

    def test_non_owner_sees_content_browser_button_on_public_playbook(self):
        """Non-owner viewer sees Content Browser on accessible public playbook detail."""
        other = User.objects.create_user(
            username="viewer_cb",
            email="viewer_cb@test.com",
            password="testpass123",
        )
        released = Playbook.objects.create(
            name="Public Released CB",
            description="Readable",
            category="development",
            author=self.maria,
            visibility="public",
            status="released",
        )
        self.client.login(username="viewer_cb", password="testpass123")
        response = self.client.get(reverse("playbook_detail", kwargs={"pk": released.pk}))
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-testid="playbook-content-browser"' in content
        assert f'/browser/{released.pk}/' in content
        assert 'data-testid="delete-button"' not in content

    def test_browser_nav_section_highlights_playbooks(self):
        """nav_section == 'playbooks' on /browser/<pk>/ pages."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.context["nav_section"] == "playbooks"

    def test_accessible_public_released_playbook_renders_in_browser(self):
        """User can open /browser/<pk>/ for a public released playbook they do not own."""
        released = Playbook.objects.create(
            name="Others Public Released",
            description="",
            category="development",
            author=self.bob,
            visibility="public",
            status="released",
        )
        response = self.client.get(f"/browser/{released.pk}/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestTeamPlaybookBrowserAccess:
    """Act-16 Phase A1 — team member page access mirrors can_view()."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            username="team_owner", email="owner@test.com", password="testpass123"
        )
        self.member = User.objects.create_user(
            username="team_member", email="member@test.com", password="testpass123"
        )
        self.playbook = Playbook.objects.create(
            name="Team Private Playbook",
            description="Shared via team",
            category="development",
            author=self.owner,
            status="released",
            visibility="private",
        )
        team = Team.objects.create(
            name="Browser Team",
            visibility=Team.VISIBILITY_HIDDEN,
            admin=self.owner,
        )
        TeamMembership.objects.create(team=team, user=self.owner, role="admin")
        TeamMembership.objects.create(team=team, user=self.member, role="member")
        TeamPlaybook.objects.create(team=team, playbook=self.playbook)
        self.client.login(username="team_member", password="testpass123")

    def test_team_member_can_open_browser_for_team_playbook(self):
        """GET /browser/<pk>/ returns 200 for a team-shared private playbook."""
        response = self.client.get(f"/browser/{self.playbook.pk}/")
        assert response.status_code == 200
        assert "Team Private Playbook" in response.content.decode()
