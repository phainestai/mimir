"""
Unit tests for Playbook model methods.

Tests the Playbook model's business logic methods including
quick stats retrieval and status badge color mapping.
"""

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
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
        assert stats['rules'] == 0
    
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
        required_keys = ['workflows', 'phases', 'activities', 'artifacts', 'agents', 'skills', 'rules']
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


@pytest.mark.django_db
class TestPlaybookCanView:
    """Test Playbook.can_view() access rules, including Django Group sharing."""

    def test_group_member_can_view_group_shared_playbook(self):
        """A user in a group the playbook is shared with can view it.

        Regression test: get_accessible_playbook_ids() (used to filter API
        list/detail responses) already treats shared_with_groups as granting
        access; can_view() (used to gate direct page views like /browser/<pk>/
        and /playbooks/<pk>/) must agree, or group members see a playbook in
        listings but hit a 404 opening it directly.
        """
        owner = User.objects.create_user(username='owner', password='testpass')
        member = User.objects.create_user(username='member', password='testpass')
        group = Group.objects.create(name='shared-group')
        member.groups.add(group)

        playbook = Playbook.objects.create(
            name='Group Shared Playbook',
            description='Test',
            category='product',
            author=owner,
            status='draft',
            visibility='private',
        )
        playbook.shared_with_groups.add(group)

        assert playbook.can_view(member) is True

    def test_non_group_member_cannot_view_private_playbook(self):
        """A user outside the shared group still cannot view a private playbook."""
        owner = User.objects.create_user(username='owner2', password='testpass')
        outsider = User.objects.create_user(username='outsider', password='testpass')
        group = Group.objects.create(name='other-group')

        playbook = Playbook.objects.create(
            name='Private Playbook',
            description='Test',
            category='product',
            author=owner,
            status='draft',
            visibility='private',
        )
        playbook.shared_with_groups.add(group)

        assert playbook.can_view(outsider) is False
