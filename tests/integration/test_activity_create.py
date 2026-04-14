"""
Integration tests for Activity CREATE operation.

Tests activity creation form, validation, and success scenarios.
"""

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity

User = get_user_model()


@pytest.mark.django_db
class TestActivityCreate:
    """Integration tests for activity create functionality."""
    
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
        
        # Create playbook and workflow
        self.playbook = Playbook.objects.create(
            name='React Frontend Development',
            description='A comprehensive methodology',
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
    
    def test_act_create_01_open_create_form(self):
        """Test opening activity create form."""
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert b'Create Activity' in response.content
        assert b'data-testid="activity-form"' in response.content
        assert b'data-testid="name-input"' in response.content
        assert b'data-testid="guidance-input"' in response.content
        assert b'data-testid="save-btn"' in response.content
    
    def test_act_create_02_create_with_required_fields(self):
        """Test creating activity with only required fields."""
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        data = {
            'name': 'Design Component',
            'guidance': 'Create UI design for the component',
        }
        response = self.client.post(url, data)
        
        # Should redirect to list on success
        assert response.status_code == 302
        assert response.url == reverse('activity_list', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        # Verify activity was created
        activity = Activity.objects.get(name='Design Component')
        assert activity.workflow == self.workflow
        assert activity.guidance == 'Create UI design for the component'
        assert activity.order == 1  # Auto-assigned
    
    def test_act_create_03_validate_required_name(self):
        """Test validation error when name is missing."""
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        data = {
            'name': '',  # Empty name
            'guidance': 'Test description',
        }
        response = self.client.post(url, data)
        
        # Should stay on form with error
        assert response.status_code == 200
        assert b'Activity name cannot be empty' in response.content or b'This field is required' in response.content
        
        # Activity should not be created
        assert Activity.objects.count() == 0
    
    def test_act_create_04_duplicate_name_validation(self):
        """Test validation error for duplicate activity name in workflow."""
        # Create existing activity
        Activity.objects.create(
            workflow=self.workflow,
            name='Design Component',
            guidance='Existing',
            order=1
        )
        
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        data = {
            'name': 'Design Component',  # Duplicate
            'guidance': 'New description',
        }
        response = self.client.post(url, data)
        
        # Should stay on form with error
        assert response.status_code == 200
        assert b'already exists' in response.content
        
        # Only original activity should exist
        assert Activity.objects.count() == 1
    
    def test_act_create_05_auto_order_assignment(self):
        """Test automatic order assignment when not provided."""
        # Create existing activities
        Activity.objects.create(workflow=self.workflow, name='Act 1', guidance='D1', order=1)
        Activity.objects.create(workflow=self.workflow, name='Act 2', guidance='D2', order=2)
        
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        data = {
            'name': 'Act 3',
            'guidance': 'Third activity',
            # order not provided
        }
        response = self.client.post(url, data)
        
        assert response.status_code == 302
        
        # Verify auto-assigned order
        activity = Activity.objects.get(name='Act 3')
        assert activity.order == 3  # Should be next in sequence
    
    def test_act_create_06_create_with_phase(self, create_test_phases):
        """Test creating activity with phase assignment."""
        # Create test phases
        phases = create_test_phases(self.playbook)
        
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        
        data = {
            'name': 'Plan Features',
            'guidance': 'Feature planning',
            'phase': phases['Planning'].id,
        }
        response = self.client.post(url, data)
        
        assert response.status_code == 302
        
        # Verify phase was set
        activity = Activity.objects.get(name='Plan Features')
        assert activity.phase == phases['Planning']
    
    def test_act_create_07_cancel_redirects_to_list(self):
        """Test cancel button redirects to activities list."""
        url = reverse('activity_create', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        response = self.client.get(url)
        
        assert response.status_code == 200
        # Check cancel button exists with correct link
        list_url = reverse('activity_list', kwargs={
            'playbook_pk': self.playbook.pk,
            'workflow_pk': self.workflow.pk
        })
        assert list_url.encode() in response.content
        assert b'data-testid="cancel-btn"' in response.content
