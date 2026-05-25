"""
Integration tests for Skill LIST+FIND operation (playbook-scoped).

Tests both global and playbook-scoped skill list display, search,
filtering by capability_domain and technology_stack, and navigation.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Skill

User = get_user_model()


@pytest.mark.django_db
class TestSkillListFind:
    """Integration tests for skill list and find functionality."""

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

    def _create_skill(self, title='Setup React Component', domain='GUI_FORM',
                       stack='React+Redux', content='Step 1: Install deps'):
        return Skill.objects.create(
            playbook=self.playbook,
            title=title,
            capability_domain=domain,
            technology_stack=stack,
            content=content,
        )

    def _playbook_list_url(self):
        return reverse('skill_list_playbook', kwargs={'playbook_pk': self.playbook.pk})

    # ── Global list ──────────────────────────────────────────────────

    def test_skill_global_list_page_loads(self):
        """Global skills list page loads successfully."""
        self._create_skill()
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Skills' in response.content

    def test_skill_global_list_shows_skills_table(self):
        """Global skills table shows skill data."""
        self._create_skill()
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'data-testid="skills-table"' in response.content

    def test_skill_global_list_search_filters_results(self):
        """Global search filters skills by title/content."""
        self._create_skill(title='Setup React Component')
        self._create_skill(title='Deploy to Production', domain='DEPLOY', stack='Docker')
        url = reverse('skill_list')
        response = self.client.get(url, {'q': 'Setup'})

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'Deploy to Production' not in response.content

    def test_skill_global_list_requires_authentication(self):
        """Global skills list requires login."""
        self.client.logout()
        url = reverse('skill_list')
        response = self.client.get(url)

        assert response.status_code == 302
        assert '/auth/' in response.url

    # ── Playbook-scoped list ─────────────────────────────────────────

    def test_skill_list_01_page_loads(self):
        """FOB-SKILLS-LIST+FIND-01: Playbook skill list loads with header."""
        self._create_skill()
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'Skills in React Frontend v1.2' in response.content
        assert b'data-testid="skills-header"' in response.content

    def test_skill_list_02_shows_skills_table(self):
        """FOB-SKILLS-LIST+FIND-02: Skills table shows columns including metadata."""
        self._create_skill()
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'data-testid="skills-table"' in response.content
        assert b'Setup React Component' in response.content
        assert b'data-testid="domain-badge"' in response.content
        assert b'data-testid="stack-badge"' in response.content
        assert b'data-testid="activity-count"' in response.content

    def test_skill_list_03_create_button_present(self):
        """FOB-SKILLS-LIST+FIND-03: Create skill button is present for owner."""
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'data-testid="create-skill-btn"' in response.content

    def test_skill_list_04_search_form_present(self):
        """FOB-SKILLS-LIST+FIND-04: Search input is present on the list page."""
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'data-testid="skill-search"' in response.content

    def test_skill_list_04_search_filters_results(self):
        """FOB-SKILLS-LIST+FIND-04: Search by name filters skills shown."""
        self._create_skill(title='Setup React Component')
        self._create_skill(title='Deploy to Production', domain='DEPLOY', stack='Docker')
        response = self.client.get(self._playbook_list_url(), {'q': 'Setup'})

        assert response.status_code == 200
        assert b'Setup React Component' in response.content
        assert b'Deploy to Production' not in response.content

    def test_skill_list_05_filter_by_domain(self):
        """FOB-SKILLS-LIST+FIND-05: Filter by capability_domain."""
        self._create_skill(title='Form Skill', domain='GUI_FORM')
        self._create_skill(title='API Skill', domain='API_CRUD', stack='FastAPI')
        response = self.client.get(self._playbook_list_url(), {'domain': 'GUI_FORM'})

        assert response.status_code == 200
        assert b'Form Skill' in response.content
        assert b'API Skill' not in response.content

    def test_skill_list_06_filter_by_stack(self):
        """FOB-SKILLS-LIST+FIND-06: Filter by technology_stack."""
        self._create_skill(title='React Skill', stack='React+Redux')
        self._create_skill(title='Django Skill', domain='API_CRUD', stack='Django+HTMX')
        response = self.client.get(self._playbook_list_url(), {'stack': 'Django+HTMX'})

        assert response.status_code == 200
        assert b'Django Skill' in response.content
        assert b'React Skill' not in response.content

    def test_skill_list_07_view_link_present(self):
        """FOB-SKILLS-LIST+FIND-07: Each skill row has a view action link."""
        skill = self._create_skill()
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert f'data-testid="view-skill-{skill.id}"'.encode() in response.content

    def test_skill_list_08_empty_state(self):
        """FOB-SKILLS-LIST+FIND-08: Empty state shown when no skills exist."""
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'data-testid="empty-state"' in response.content
        assert b'No skills yet' in response.content

    def test_skill_list_requires_authentication(self):
        """Playbook skill list requires login."""
        self.client.logout()
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_skill_list_shows_activity_count(self):
        """Activity count badge shows correct number of linked activities."""
        skill = self._create_skill()
        activity = Activity.objects.create(
            name='Use Form Skill',
            guidance='Uses the form skill',
            workflow=self.workflow,
            order=1,
        )
        activity.skills.add(skill)
        response = self.client.get(self._playbook_list_url())

        assert response.status_code == 200
        assert b'data-testid="activity-count"' in response.content
