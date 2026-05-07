"""
Integration tests for Playbook CREATE operation (Wizard Flow).

Tests all 21 scenarios from playbooks-create.feature.
Following TDD: These tests should FAIL until implementation is complete.
"""

from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, PlaybookVersion

User = get_user_model()


@pytest.mark.django_db
class TestPlaybookCreateWizard:
    """Test playbook creation wizard (21 scenarios)."""
    
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
        
        # Create existing playbook for duplicate name testing
        Playbook.objects.create(
            name='React Frontend Development',
            description='Existing playbook for testing',
            category='development',
            author=self.user
        )
    
    # PB-CREATE-01: Open create playbook wizard
    def test_open_create_wizard(self):
        """Test opening the playbook creation wizard."""
        response = self.client.get(reverse('playbook_create'))
        
        assert response.status_code == 200
        assert b'Step 1: Basic Information' in response.content
        assert b'data-testid="wizard-step-1"' in response.content
        # Check for required field indicators
        assert response.content.count(b'*') >= 3  # At least 3 required fields
    
    # PB-CREATE-02: Complete Step 1 with valid data
    def test_complete_step1_valid_data(self):
        """Test completing Step 1 with all valid data."""
        data = {
            'name': 'Product Discovery Framework',
            'description': 'Comprehensive methodology for discovering and validating product opportunities',
            'category': 'product',
            'visibility': 'private',
            'tags': 'product management, discovery, validation, user research',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        # Should redirect to Step 2
        assert response.status_code == 302
        assert 'step2' in response.url or 'workflows' in response.url
        
        # Check session has saved data
        session = self.client.session
        assert 'wizard_data' in session
        assert session['wizard_data']['name'] == 'Product Discovery Framework'
    
    # PB-CREATE-03: Validate required fields on Step 1
    def test_validate_required_name(self):
        """Test validation when name is empty."""
        data = {
            'name': '',
            'description': 'Valid description here',
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200  # Stays on same page
        assert b'Name is required' in response.content
        assert b'data-testid="error-name"' in response.content
    
    def test_validate_required_description(self):
        """Test validation when description is empty."""
        data = {
            'name': 'Valid Name',
            'description': '',
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Description is required' in response.content
        assert b'data-testid="error-description"' in response.content
    
    def test_validate_required_category(self):
        """Test validation when category is empty."""
        data = {
            'name': 'Valid Name',
            'description': 'Valid description here',
            'category': ''
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Please select a category' in response.content
    
    # PB-CREATE-04: Duplicate playbook name validation
    def test_duplicate_playbook_name(self):
        """Test validation prevents duplicate playbook names."""
        data = {
            'name': 'React Frontend Development',  # Exists from setup
            'description': 'Different description but same name',
            'category': 'development',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'A playbook with this name already exists' in response.content
        assert b'data-testid="error-name"' in response.content
    
    # PB-CREATE-05: Name length validation
    def test_name_too_short(self):
        """Test name must be at least 3 characters."""
        data = {
            'name': 'AB',  # Too short
            'description': 'Valid description',
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Must be 3-100 characters' in response.content or b'at least 3 characters' in response.content
    
    def test_name_too_long(self):
        """Test name must not exceed 100 characters."""
        data = {
            'name': 'A' * 101,  # Too long
            'description': 'Valid description',
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Must be 3-100 characters' in response.content or b'100 characters' in response.content
    
    # PB-CREATE-06: Description length validation
    def test_description_too_short(self):
        """Test description must be at least 10 characters."""
        data = {
            'name': 'Valid Name',
            'description': 'Short',  # Too short
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Must be 10-500 characters' in response.content or b'at least 10 characters' in response.content
    
    def test_description_too_long(self):
        """Test description must not exceed 500 characters."""
        data = {
            'name': 'Valid Name',
            'description': 'A' * 501,  # Too long
            'category': 'product',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 200
        assert b'Must be 10-500 characters' in response.content or b'500 characters' in response.content
    
    # PB-CREATE-07: Select visibility options
    def test_select_visibility_private(self):
        """Test selecting private visibility."""
        data = {
            'name': 'Test Playbook',
            'description': 'Test description here',
            'category': 'product',
            'visibility': 'private',
            'visibility': 'private'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 302  # Success
        session = self.client.session
        assert session['wizard_data']['visibility'] == 'private'
    
    # PB-CREATE-08: Add optional tags
    def test_add_tags(self):
        """Test adding optional tags."""
        data = {
            'name': 'Test Playbook',
            'description': 'Test description here',
            'category': 'product',
            'visibility': 'private',
            'tags': 'tag1, tag2, tag3'
        }
        response = self.client.post(reverse('playbook_create'), data=data)
        
        assert response.status_code == 302
        session = self.client.session
        assert 'tags' in session['wizard_data']
    
    # PB-CREATE-09: Skip adding workflows in Step 2
    def test_skip_workflows_step2(self):
        """Test skipping workflow addition in Step 2."""
        # First complete Step 1
        step1_data = {
            'name': 'Test Playbook',
            'description': 'Test description here',
            'category': 'product',
            'visibility': 'private'
        }
        self.client.post(reverse('playbook_create'), data=step1_data)
        
        # Skip workflows in Step 2
        response = self.client.post(reverse('playbook_create_step2'), data={'skip': 'true'})
        
        assert response.status_code == 302
        assert 'step3' in response.url or 'publish' in response.url
    
    # PB-CREATE-10: Add first workflow inline in Step 2
    def test_add_workflow_step2(self):
        """Test adding first workflow in Step 2."""
        # First complete Step 1
        step1_data = {
            'name': 'Test Playbook',
            'description': 'Test description here',
            'category': 'product',
            'visibility': 'private'
        }
        self.client.post(reverse('playbook_create'), data=step1_data)
        
        # Add workflow in Step 2
        workflow_data = {
            'workflow_name': 'Discovery Phase',
            'workflow_description': 'Initial research and validation'
        }
        response = self.client.post(reverse('playbook_create_step2'), data=workflow_data)
        
        assert response.status_code == 302
        session = self.client.session
        assert 'workflows' in session['wizard_data']
    
    # PB-CREATE-11: Cancel adding workflow in Step 2
    def test_cancel_workflow_step2(self):
        """Test canceling workflow addition."""
        # Setup Step 1
        step1_data = {
            'name': 'Test Playbook',
            'description': 'Test description here',
            'category': 'product',
            'visibility': 'private'
        }
        self.client.post(reverse('playbook_create'), data=step1_data)
        
        # Get Step 2
        response = self.client.get(reverse('playbook_create_step2'))
        assert response.status_code == 200
        assert b'Skip' in response.content or b'Cancel' in response.content
    
    # PB-CREATE-12: Complete Step 3 with Active status
    def test_complete_step3_active_status(self):
        """Test publishing playbook as Active."""
        # Complete Steps 1 & 2
        self._complete_steps_1_and_2()
        
        # Publish as Active
        publish_data = {'status': 'active'}
        response = self.client.post(reverse('playbook_create_step3'), data=publish_data)
        
        assert response.status_code == 302
        # Check playbook was created
        playbook = Playbook.objects.get(name='Test Playbook')
        assert playbook.status == 'active'
        assert playbook.version == Decimal("1.0")
        # Check version history created
        assert PlaybookVersion.objects.filter(playbook=playbook).exists()
    
    # PB-CREATE-13: Complete Step 3 with Draft status
    def test_complete_step3_draft_status(self):
        """Test saving playbook as Draft."""
        self._complete_steps_1_and_2()
        
        publish_data = {'status': 'draft'}
        response = self.client.post(reverse('playbook_create_step3'), data=publish_data)
        
        assert response.status_code == 302
        playbook = Playbook.objects.get(name='Test Playbook')
        assert playbook.status == 'draft'
    
    # PB-CREATE-14: Review summary in Step 3
    def test_review_summary_step3(self):
        """Test reviewing playbook summary before publish."""
        self._complete_steps_1_and_2()
        
        response = self.client.get(reverse('playbook_create_step3'))
        
        assert response.status_code == 200
        assert b'Test Playbook' in response.content
        assert b'Test description' in response.content
        assert b'data-testid="summary-card"' in response.content
    
    # PB-CREATE-15: Cancel wizard at any step
    def test_cancel_wizard_step1(self):
        """Test canceling wizard from Step 1."""
        response = self.client.get(reverse('playbook_create'))
        assert b'Cancel' in response.content
        assert b'data-testid="cancel-wizard"' in response.content
    
    # PB-CREATE-16: Cancel wizard confirmation - keep editing
    def test_cancel_confirmation_keep_editing(self):
        """Test cancel confirmation modal allows continuing."""
        response = self.client.get(reverse('playbook_create'))
        assert b'modal' in response.content.lower() or b'confirm' in response.content.lower()
    
    # PB-CREATE-17: Navigate back to previous step
    def test_navigate_back_to_step1(self):
        """Test navigating back from Step 2 to Step 1."""
        self._complete_steps_1_and_2()
        
        response = self.client.get(reverse('playbook_create_step2'))
        assert b'Back' in response.content or b'\u2190' in response.content
        assert b'data-testid="back-button"' in response.content
    
    # PB-CREATE-18: Playbook appears in list after creation
    def test_playbook_appears_in_list(self):
        """Test created playbook appears in playbooks list."""
        self._complete_steps_1_and_2()
        
        publish_data = {'status': 'active'}
        self.client.post(reverse('playbook_create_step3'), data=publish_data)
        
        # Check list page
        response = self.client.get(reverse('playbook_list'))
        assert b'Test Playbook' in response.content
    
    # PB-CREATE-19: Create playbook with Family visibility (deferred)
    def test_family_visibility_option_deferred(self):
        """Test Family visibility option exists but is marked as TODO."""
        response = self.client.get(reverse('playbook_create'))
        # Should have family option but may be disabled or marked as coming soon
        assert b'family' in response.content.lower() or b'Family' in response.content
    
    # PB-CREATE-20: Create playbook with Local only visibility (deferred)
    def test_local_visibility_option_deferred(self):
        """Test Local only visibility option exists but is marked as TODO."""
        response = self.client.get(reverse('playbook_create'))
        assert b'local' in response.content.lower() or b'Local' in response.content
    
    # PB-CREATE-21: Auto-increment version on creation
    def test_version_auto_increment(self):
        """Test version starts at 1 on creation."""
        self._complete_steps_1_and_2()
        
        publish_data = {'status': 'active'}
        self.client.post(reverse('playbook_create_step3'), data=publish_data)
        
        playbook = Playbook.objects.get(name='Test Playbook')
        assert playbook.version == Decimal("1.0")
        
        # Check version history
        version = PlaybookVersion.objects.get(
            playbook=playbook, version_number=Decimal("1.0")
        )
        assert version.change_summary == 'Initial version'
    
    # Helper methods
    def _complete_steps_1_and_2(self):
        """Helper to complete Steps 1 and 2."""
        step1_data = {
            'name': 'Test Playbook',
            'description': 'Test description here with enough characters',
            'category': 'product',
            'visibility': 'private'
        }
        self.client.post(reverse('playbook_create'), data=step1_data)
        
        # Skip workflows
        self.client.post(reverse('playbook_create_step2'), data={'skip': 'true'})
