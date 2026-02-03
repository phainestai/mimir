"""
Integration tests for Playbook VIEW - Workflows Tab (Scenario 06).

Tests FOB-PLAYBOOKS-VIEW_PLAYBOOK-06: Navigate to Workflows tab
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow

User = get_user_model()


@pytest.fixture
def playbook_with_workflows(db):
    """Create test playbook with multiple workflows."""
    user = User.objects.create_user(username='maria', password='test123')
    playbook = Playbook.objects.create(
        name='React Development',
        description='Test playbook for workflows tab',
        category='development',
        status='active',
        source='owned',
        author=user
    )
    
    # Create 3 workflows with different characteristics
    Workflow.objects.create(
        name='Component Development',
        description='Build reusable components',
        playbook=playbook,
        order=1
    )
    Workflow.objects.create(
        name='State Management',
        description='Setup state management',
        playbook=playbook,
        order=2
    )
    Workflow.objects.create(
        name='Testing Strategy',
        description='Implement testing',
        playbook=playbook,
        order=3
    )
    
    return {'user': user, 'playbook': playbook}


@pytest.fixture
def playbook_no_workflows(db):
    """Create test playbook with no workflows."""
    user = User.objects.create_user(username='bob', password='test123')
    playbook = Playbook.objects.create(
        name='Empty Playbook',
        description='Playbook with no workflows',
        category='product',
        status='active',
        source='owned',
        author=user
    )
    return {'user': user, 'playbook': playbook}


@pytest.mark.django_db
class TestPlaybookViewWorkflowsTab:
    """Test Workflows tab in playbook detail page."""
    
    def test_workflows_tab_exists_in_navigation(self, playbook_with_workflows):
        """Workflows tab is visible in tab navigation."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        assert response.status_code == 200
        content = response.content.decode('utf-8')
        assert 'id="workflows-tab"' in content
        assert 'data-testid="tab-workflows"' in content
    
    def test_workflows_tab_content_area_exists(self, playbook_with_workflows):
        """Workflows tab content area is present."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'id="workflows-content"' in content
        assert 'role="tabpanel"' in content
    
    def test_workflows_tab_shows_workflows_table(self, playbook_with_workflows):
        """Workflows table is rendered with correct structure."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'id="workflows-table"' in content
        assert 'data-testid="workflows-table"' in content
        
        # Check table headers
        assert '>Order<' in content
        assert '>Name<' in content
        assert '>Description<' in content
        assert '>Activities<' in content
        assert '>Phases<' in content
        assert '>Actions<' in content
    
    def test_workflows_tab_shows_all_workflows(self, playbook_with_workflows):
        """All workflows are displayed in the table."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'Component Development' in content
        assert 'State Management' in content
        assert 'Testing Strategy' in content
    
    def test_workflows_tab_shows_search_box(self, playbook_with_workflows):
        """Search input is present for filtering."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'id="workflow-search"' in content
        assert 'data-testid="workflow-search-input"' in content
        assert 'Search workflows by name' in content
    
    def test_workflows_tab_shows_phase_filter(self, playbook_with_workflows):
        """Phase filter dropdown is present."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'id="filter-has-phases"' in content
        assert 'data-testid="workflow-phase-filter"' in content
        assert 'All Workflows' in content
        assert 'With Phases' in content
        assert 'No Phases' in content
    
    def test_workflows_tab_shows_filter_section(self, playbook_with_workflows):
        """Filter section is present with correct testid."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'data-testid="workflows-filter-section"' in content
    
    def test_workflows_tab_empty_state_for_no_workflows(self, playbook_no_workflows):
        """Empty state is shown when playbook has no workflows."""
        client = Client()
        user = playbook_no_workflows['user']
        playbook = playbook_no_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'data-testid="workflows-no-data"' in content
        assert 'No workflows yet' in content
        assert 'Create your first workflow' in content
    
    def test_workflows_tab_respects_edit_permissions(self, playbook_with_workflows):
        """Edit buttons only shown for owned playbooks."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        # Should have edit buttons since user owns playbook
        assert 'data-testid="edit-workflow-' in content
        assert 'fa-edit' in content
    
    def test_workflows_tab_shows_view_buttons(self, playbook_with_workflows):
        """View buttons are shown for all workflows."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'data-testid="view-workflow-' in content
        assert 'fa-eye' in content
    
    def test_workflows_tab_has_filtering_javascript(self, playbook_with_workflows):
        """Client-side filtering JavaScript is included."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'workflow-search' in content
        assert 'filterWorkflows' in content
        assert 'addEventListener' in content
    
    def test_workflows_tab_shows_workflow_data_attributes(self, playbook_with_workflows):
        """Workflow rows have correct data attributes for filtering."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'data-workflow-row' in content
        assert 'data-workflow-name' in content
        assert 'data-phase-count' in content
    
    def test_workflows_tab_has_empty_state_for_filtered_results(self, playbook_with_workflows):
        """Empty state element exists for filtered results (hidden by default)."""
        client = Client()
        user = playbook_with_workflows['user']
        playbook = playbook_with_workflows['playbook']
        
        client.force_login(user)
        response = client.get(reverse('playbook_detail', kwargs={'pk': playbook.pk}))
        
        content = response.content.decode('utf-8')
        assert 'id="empty-state"' in content
        assert 'data-testid="workflows-empty-state"' in content
        assert 'No workflows match your filters' in content
