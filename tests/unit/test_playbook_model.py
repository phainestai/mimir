"""
Unit tests for Playbook model methods.

Tests the Playbook model's business logic methods including
quick stats retrieval and status badge color mapping.
"""

import pytest
from django.contrib.auth import get_user_model
from methodology.models.playbook import Playbook
from methodology.models.workflow import Workflow

User = get_user_model()


@pytest.mark.django_db
class TestPlaybookQuickStats:
    """Test Playbook.get_quick_stats() method."""
    
    def test_get_quick_stats_with_workflows(self):
        """Test quick stats returns correct workflow count."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test description',
            category='product',
            author=user,
            status='active'
        )
        
        # Create 3 workflows
        Workflow.objects.create(name='Workflow 1', playbook=playbook)
        Workflow.objects.create(name='Workflow 2', playbook=playbook)
        Workflow.objects.create(name='Workflow 3', playbook=playbook)
        
        stats = playbook.get_quick_stats()
        
        assert stats['workflows'] == 3
        assert 'phases' in stats
        assert 'activities' in stats
        assert 'artifacts' in stats
        assert 'agents' in stats
        assert 'skills' in stats
    
    def test_get_quick_stats_no_workflows(self):
        """Test quick stats with zero workflows."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Empty Playbook',
            description='No workflows',
            category='product',
            author=user
        )
        
        stats = playbook.get_quick_stats()
        
        assert stats['workflows'] == 0
        assert stats['phases'] == 0
        assert stats['activities'] == 0
        assert stats['artifacts'] == 0
        assert stats['agents'] == 0
        assert stats['skills'] == 0
    
    def test_get_quick_stats_structure(self):
        """Test quick stats returns proper dictionary structure."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Structure Test',
            description='Test structure',
            category='development',
            author=user
        )
        
        stats = playbook.get_quick_stats()
        
        # Verify it's a dictionary
        assert isinstance(stats, dict)
        
        # Verify all expected keys exist
        required_keys = ['workflows', 'phases', 'activities', 'artifacts', 'agents', 'skills']
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"
        
        # Verify integer types for counts
        for key in required_keys:
            assert isinstance(stats[key], int), f"{key} should be integer"


@pytest.mark.django_db
class TestPlaybookStatusBadgeColor:
    """Test Playbook.get_status_badge_color() method."""
    
    def test_status_badge_color_active(self):
        """Test active status returns success color."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Active Playbook',
            description='Test',
            category='product',
            author=user,
            status='active'
        )
        
        color = playbook.get_status_badge_color()
        
        assert color == 'success'
    
    def test_status_badge_color_draft(self):
        """Test draft status returns warning color."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Draft Playbook',
            description='Test',
            category='product',
            author=user,
            status='draft'
        )
        
        color = playbook.get_status_badge_color()
        
        assert color == 'warning'
    
    def test_status_badge_color_disabled(self):
        """Test disabled status returns secondary color."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Disabled Playbook',
            description='Test',
            category='product',
            author=user,
            status='disabled'
        )
        
        color = playbook.get_status_badge_color()
        
        assert color == 'secondary'
    
    def test_status_badge_color_returns_string(self):
        """Test method returns a string value."""
        user = User.objects.create_user(username='testuser', password='testpass')
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='product',
            author=user,
            status='active'
        )
        
        color = playbook.get_status_badge_color()
        
        assert isinstance(color, str)
        assert len(color) > 0
