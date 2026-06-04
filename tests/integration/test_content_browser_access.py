"""
Integration tests for Content Browser access and navigation.

Tests scenarios from docs/features/act-16-content-browser/01-access-and-nav.feature.
Following TDD: tests FAIL until implementation is complete (NotImplementedError stubs).
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook

User = get_user_model()


@pytest.mark.django_db
class TestContentBrowserServerSide:
    """S1 — Server-side scaffold: nav, auth, views, template shell, 404.

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
    def test_content_browser_link_in_nav(self):
        """Content Browser nav link is present and positioned after Home."""
        response = self.client.get("/browser/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-testid="nav-browser"' in content
        dashboard_pos = content.index('data-testid="nav-dashboard"')
        browser_pos = content.index('data-testid="nav-browser"')
        playbooks_pos = content.index('data-testid="nav-playbooks"')
        assert dashboard_pos < browser_pos < playbooks_pos

    # FOB-CONTENT-BROWSER-01b
    def test_unauthenticated_browser_root_redirects_to_login(self):
        """GET /browser/ while logged out redirects to login with next= preserved."""
        self.client.logout()
        response = self.client.get("/browser/")
        assert response.status_code == 302
        location = response["Location"]
        assert "login" in location
        assert "next=" in location

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
    def test_browser_root_returns_200_with_three_panel_shell(self):
        """GET /browser/ returns 200 with correct template and empty-state elements."""
        response = self.client.get("/browser/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-testid="browser-left-panel"' in content
        assert 'data-testid="browser-canvas"' in content
        assert 'data-testid="browser-detail-panel"' in content

    # FOB-CONTENT-BROWSER-02
    def test_browser_root_shows_no_playbook_selected_heading(self):
        """Left panel heading shows '(No playbook selected)' when no pk in URL."""
        response = self.client.get("/browser/")
        assert "(No playbook selected)" in response.content.decode()

    # FOB-CONTENT-BROWSER-02
    def test_browser_root_shows_select_playbook_button_not_change(self):
        """Empty state shows [Select Playbook], not [Change Playbook]."""
        response = self.client.get("/browser/")
        content = response.content.decode()
        assert 'data-testid="browser-select-playbook"' in content
        assert 'data-testid="browser-change-playbook"' not in content

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
        assert f'data-playbook-pk="{self.public_playbook.pk}"' in response.content.decode()

    # FOB-CONTENT-BROWSER-03
    def test_browser_playbook_shows_playbook_name_in_left_panel(self):
        """Left panel heading shows the playbook name when pk is provided."""
        response = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response.status_code == 200
        assert "FeatureFactory" in response.content.decode()

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

    # FOB-CONTENT-BROWSER-01 (nav_section active state)
    def test_browser_nav_section_is_active_on_browser_pages(self):
        """nav_section == 'browser' is set in context for both /browser/ routes."""
        response = self.client.get("/browser/")
        assert response.context["nav_section"] == "browser"
        response2 = self.client.get(f"/browser/{self.public_playbook.pk}/")
        assert response2.context["nav_section"] == "browser"


@pytest.mark.django_db
class TestPickerAccessControl:
    """S2 — Picker access control.

    Covers: FOB-CONTENT-BROWSER-03e
    """

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = Client()
        self.maria = User.objects.create_user(
            username="maria_picker", email="maria_p@test.com", password="testpass123"
        )
        self.other = User.objects.create_user(
            username="other_user", email="other@test.com", password="testpass123"
        )
        # Playbooks with varied visibility/ownership
        self.marias_private = Playbook.objects.create(
            name="Maria Private", description="", category="development",
            author=self.maria, visibility="private",
        )
        self.others_private = Playbook.objects.create(
            name="Others Private", description="", category="development",
            author=self.other, visibility="private",
        )
        self.others_public_draft = Playbook.objects.create(
            name="Others Public Draft", description="", category="development",
            author=self.other, visibility="public",
        )
        self.others_public_released = Playbook.objects.create(
            name="Others Public Released", description="", category="development",
            author=self.other, visibility="public",
        )
        # Mark released
        self.others_public_released.status = "released"
        self.others_public_released.save()

        self.client.login(username="maria_picker", password="testpass123")

    # FOB-CONTENT-BROWSER-03e
    def test_picker_includes_own_playbooks_of_any_status(self):
        """Picker includes playbooks owned by the user regardless of status."""
        response = self.client.get("/browser/")
        assert response.status_code == 200
        names = [pb.name for pb in response.context["accessible_playbooks"]]
        assert "Maria Private" in names

    # FOB-CONTENT-BROWSER-03e
    def test_picker_includes_public_non_draft_playbooks_from_others(self):
        """Picker includes public released/active/disabled playbooks from other users."""
        response = self.client.get("/browser/")
        names = [pb.name for pb in response.context["accessible_playbooks"]]
        assert "Others Public Released" in names

    # FOB-CONTENT-BROWSER-03e
    def test_picker_excludes_private_playbooks_from_others(self):
        """Picker does NOT include private playbooks owned by other users."""
        response = self.client.get("/browser/")
        names = [pb.name for pb in response.context["accessible_playbooks"]]
        assert "Others Private" not in names

    # FOB-CONTENT-BROWSER-03e
    def test_picker_excludes_public_draft_playbooks_from_others(self):
        """Picker does NOT include public draft playbooks owned by other users."""
        response = self.client.get("/browser/")
        names = [pb.name for pb in response.context["accessible_playbooks"]]
        assert "Others Public Draft" not in names

    # FOB-CONTENT-BROWSER-03e
    def test_accessible_public_released_playbook_renders_in_browser(self):
        """Maria can open /browser/<pk>/ for a public released playbook she does not own."""
        response = self.client.get(f"/browser/{self.others_public_released.pk}/")
        assert response.status_code == 200
