"""
Integration tests for Phase global LIST+FIND operation.

Tests global phase list display, search, and navigation.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from methodology.models import Phase, Playbook

User = get_user_model()


@pytest.mark.django_db
class TestPhaseListGlobal:
    """Integration tests for global phase list functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='maria_phase_global',
            email='maria_phase@test.com',
            password='testpass123'
        )
        self.client.login(username='maria_phase_global', password='testpass123')

        self.playbook = Playbook.objects.create(
            name='React Frontend v1.2',
            description='React methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )

    def test_global_list_page_loads(self):
        """Global phases list page loads successfully."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Inception',
            order=1
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Phases' in response.content

    def test_shows_phases_table(self):
        """Phases table shows phases with key columns."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Elaboration',
            description='Design and architecture phase',
            order=2
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Elaboration' in response.content
        assert b'data-testid="phases-table"' in response.content

    def test_search_by_name(self):
        """Search by name filters results."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Inception',
            description='Initial planning',
            order=1
        )
        Phase.objects.create(
            playbook=self.playbook,
            name='Construction',
            description='Build phase',
            order=2
        )
        url = reverse('phase_list_global')
        response = self.client.get(url, {'q': 'Inception'})

        assert response.status_code == 200
        assert b'Inception' in response.content
        assert b'Construction' not in response.content

    def test_search_by_description(self):
        """Search by description filters results."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Inception',
            description='Initial planning and requirements',
            order=1
        )
        Phase.objects.create(
            playbook=self.playbook,
            name='Construction',
            description='Build and test',
            order=2
        )
        url = reverse('phase_list_global')
        response = self.client.get(url, {'q': 'planning'})

        assert response.status_code == 200
        assert b'Inception' in response.content
        assert b'Construction' not in response.content

    def test_filter_by_playbook_query_param(self):
        """?playbook=<pk> limits rows to that playbook (owned by user)."""
        other = Playbook.objects.create(
            name='Other PB',
            description='x',
            category='development',
            status='draft',
            source='owned',
            author=self.user,
        )
        Phase.objects.create(playbook=self.playbook, name='Only Here', order=1)
        Phase.objects.create(playbook=other, name='Other Phase', order=1)

        url = reverse('phase_list_global')
        response = self.client.get(url, {'playbook': str(self.playbook.pk)})

        assert response.status_code == 200
        body = response.content.decode()
        assert 'Only Here' in body
        assert 'Other Phase' not in body
        assert 'data-testid="phase-global-playbook-filter"' in body
        assert 'React Frontend v1.2' in body

    def test_filter_by_playbook_unknown_id_ignored(self):
        """Invalid or not-owned playbook id does not 404; playbook filter is not applied."""
        Phase.objects.create(playbook=self.playbook, name='Mine', order=1)

        url = reverse('phase_list_global')
        r1 = self.client.get(url, {'playbook': '999999'})
        assert r1.status_code == 200
        assert b'Mine' in r1.content
        assert b'data-testid="phase-global-playbook-filter"' not in r1.content

        stranger = User.objects.create_user(username='stranger_pb', password='x')
        alien = Playbook.objects.create(
            name='Alien PB',
            description='x',
            category='development',
            status='draft',
            source='owned',
            author=stranger,
        )
        Phase.objects.create(playbook=alien, name='Not Yours', order=1)

        r2 = self.client.get(url, {'playbook': str(alien.pk)})
        assert r2.status_code == 200
        assert b'Mine' in r2.content
        assert b'Not Yours' not in r2.content
        assert b'data-testid="phase-global-playbook-filter"' not in r2.content


    def test_empty_state(self):
        """Empty state shown when no phases exist."""
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'data-testid="empty-state"' in response.content
        assert b'No phases yet' in response.content

    def test_requires_authentication(self):
        """Phase global list requires login."""
        self.client.logout()
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 302
        assert '/auth/' in response.url

    def test_shows_playbook_name(self):
        """Phase table shows the parent playbook name."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Test Phase',
            description='Test'
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'React Frontend v1.2' in response.content

    def test_shows_multiple_playbooks(self):
        """Global list shows phases from multiple playbooks."""
        playbook2 = Playbook.objects.create(
            name='Django Backend v2.0',
            description='Django methodology',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        Phase.objects.create(
            playbook=self.playbook,
            name='Inception',
            order=1
        )
        Phase.objects.create(
            playbook=playbook2,
            name='Planning',
            order=1
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'Inception' in response.content
        assert b'Planning' in response.content
        assert b'React Frontend v1.2' in response.content
        assert b'Django Backend v2.0' in response.content

    def test_only_shows_user_phases(self):
        """Global list only shows phases from user's playbooks."""
        other_user = User.objects.create_user(
            username='other_user',
            email='other@test.com',
            password='testpass123'
        )
        other_playbook = Playbook.objects.create(
            name='Other Playbook',
            description='Not mine',
            category='development',
            status='draft',
            source='owned',
            author=other_user
        )
        Phase.objects.create(
            playbook=self.playbook,
            name='My Phase',
            order=1
        )
        Phase.objects.create(
            playbook=other_playbook,
            name='Other Phase',
            order=1
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'My Phase' in response.content
        assert b'Other Phase' not in response.content

    def test_phases_ordered_by_playbook_and_order(self):
        """Phases are ordered by playbook name then order."""
        playbook_a = Playbook.objects.create(
            name='A Playbook',
            description='First',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        playbook_z = Playbook.objects.create(
            name='Z Playbook',
            description='Last',
            category='development',
            status='draft',
            source='owned',
            author=self.user
        )
        Phase.objects.create(playbook=playbook_z, name='Z Phase 1', order=1)
        Phase.objects.create(playbook=playbook_z, name='Z Phase 2', order=2)
        Phase.objects.create(playbook=playbook_a, name='A Phase 1', order=1)
        Phase.objects.create(playbook=playbook_a, name='A Phase 2', order=2)
        
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        content = response.content.decode('utf-8')
        # A Playbook phases should appear before Z Playbook phases
        a_phase_pos = content.find('A Phase 1')
        z_phase_pos = content.find('Z Phase 1')
        assert a_phase_pos < z_phase_pos

    def test_view_phase_link(self):
        """Each phase has a view link to phase detail."""
        phase = Phase.objects.create(
            playbook=self.playbook,
            name='Test Phase',
            order=1
        )
        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        detail_url = reverse('phase_detail', kwargs={
            'playbook_pk': self.playbook.id,
            'phase_pk': phase.id
        })
        assert detail_url.encode() in response.content

    def test_search_clear_button(self):
        """Clear button appears when search query is active."""
        Phase.objects.create(
            playbook=self.playbook,
            name='Test Phase',
            order=1
        )
        url = reverse('phase_list_global')
        response = self.client.get(url, {'q': 'test'})

        assert response.status_code == 200
        assert b'Clear' in response.content

    def test_total_count_in_header(self):
        """Page header subtitle shows total count of phases."""
        Phase.objects.create(playbook=self.playbook, name='Phase 1', order=1)
        Phase.objects.create(playbook=self.playbook, name='Phase 2', order=2)
        Phase.objects.create(playbook=self.playbook, name='Phase 3', order=3)

        url = reverse('phase_list_global')
        response = self.client.get(url)

        assert response.status_code == 200
        assert b'3 phases' in response.content
        assert b'data-testid="phases-list-header"' in response.content
