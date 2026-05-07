"""
Unit tests for ActivityService.
"""

import pytest
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity
from methodology.services.activity_service import ActivityService

User = get_user_model()


@pytest.mark.django_db
class TestActivityService:
    """Test ActivityService methods."""
    
    def test_get_recent_activities_returns_user_activities(self):
        """Test get_recent_activities returns activities from user's playbooks."""
        # Create user
        user = User.objects.create_user(username='testuser', password='testpass123')
        
        # Create playbook with workflow and activities
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test description',
            category='development',
            author=user
        )
        
        workflow = Workflow.objects.create(
            playbook=playbook,
            name='Test Workflow',
            description='Test workflow'
        )
        
        activity1 = Activity.objects.create(
            workflow=workflow,
            name='Activity 1',
            guidance='Test guidance 1',
            order=1
        )
        
        activity2 = Activity.objects.create(
            workflow=workflow,
            name='Activity 2',
            guidance='Test guidance 2',
            order=2
        )
        
        # Get recent activities
        recent = ActivityService.get_recent_activities(user, limit=10)
        
        # Assertions
        assert recent.count() == 2
        assert activity1 in recent
        assert activity2 in recent
    
    def test_get_recent_activities_only_returns_user_owned_activities(self):
        """Test get_recent_activities filters by user ownership."""
        # Create two users
        user1 = User.objects.create_user(username='user1', password='pass123')
        user2 = User.objects.create_user(username='user2', password='pass123')
        
        # Create playbook for user1
        playbook1 = Playbook.objects.create(
            name='User1 Playbook',
            description='User1 description',
            category='development',
            author=user1
        )
        
        workflow1 = Workflow.objects.create(
            playbook=playbook1,
            name='User1 Workflow',
            description='Test'
        )
        
        activity1 = Activity.objects.create(
            workflow=workflow1,
            name='User1 Activity',
            guidance='Test',
            order=1
        )
        
        # Create playbook for user2
        playbook2 = Playbook.objects.create(
            name='User2 Playbook',
            description='User2 description',
            category='development',
            author=user2
        )
        
        workflow2 = Workflow.objects.create(
            playbook=playbook2,
            name='User2 Workflow',
            description='Test'
        )
        
        activity2 = Activity.objects.create(
            workflow=workflow2,
            name='User2 Activity',
            guidance='Test',
            order=1
        )
        
        # Get user1's activities
        user1_activities = ActivityService.get_recent_activities(user1, limit=10)
        
        # Assertions
        assert user1_activities.count() == 1
        assert activity1 in user1_activities
        assert activity2 not in user1_activities
    
    def test_get_recent_activities_respects_limit(self):
        """Test get_recent_activities respects the limit parameter."""
        # Create user with many activities
        user = User.objects.create_user(username='testuser', password='pass123')
        
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='development',
            author=user
        )
        
        workflow = Workflow.objects.create(
            playbook=playbook,
            name='Test Workflow',
            description='Test'
        )
        
        # Create 15 activities
        for i in range(15):
            Activity.objects.create(
                workflow=workflow,
                name=f'Activity {i}',
                guidance='Test',
                order=i+1
            )
        
        # Get with limit=5
        recent = ActivityService.get_recent_activities(user, limit=5)
        
        # Assertions
        assert recent.count() == 5
    
    def test_get_recent_activities_ordered_by_updated_at(self):
        """Test get_recent_activities orders by updated_at descending."""
        # Create user
        user = User.objects.create_user(username='testuser', password='pass123')
        
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='development',
            author=user
        )
        
        workflow = Workflow.objects.create(
            playbook=playbook,
            name='Test Workflow',
            description='Test'
        )
        
        activity1 = Activity.objects.create(
            workflow=workflow,
            name='First Activity',
            guidance='Test',
            order=1
        )
        
        activity2 = Activity.objects.create(
            workflow=workflow,
            name='Second Activity',
            guidance='Test',
            order=2
        )
        
        # Update activity1 to make it more recent
        activity1.guidance = 'Updated guidance'
        activity1.save()
        
        # Get recent activities
        recent = list(ActivityService.get_recent_activities(user, limit=10))
        
        # Assertions - activity1 should be first (most recent)
        assert recent[0] == activity1
        assert recent[1] == activity2
    
    def test_touch_activity_access_updates_timestamp(self):
        """Test touch_activity_access updates last_accessed_at timestamp."""
        from django.utils import timezone
        
        # Create user and activity
        user = User.objects.create_user(username='testuser', password='pass123')
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='development',
            author=user
        )
        workflow = Workflow.objects.create(
            playbook=playbook,
            name='Test Workflow',
            description='Test'
        )
        activity = Activity.objects.create(
            workflow=workflow,
            name='Test Activity',
            guidance='Test',
            order=1
        )
        
        # Verify initially None
        assert activity.last_accessed_at is None
        
        # Call touch_activity_access
        before_time = timezone.now()
        ActivityService.touch_activity_access(activity.id)
        
        # Refresh from DB
        activity.refresh_from_db()
        
        # Assertions
        assert activity.last_accessed_at is not None
        assert activity.last_accessed_at >= before_time
    
    def test_touch_activity_access_raises_for_invalid_id(self):
        """Test touch_activity_access raises Activity.DoesNotExist for invalid ID."""
        # Attempt to touch non-existent activity
        with pytest.raises(Activity.DoesNotExist):
            ActivityService.touch_activity_access(99999)
    
    def test_get_recent_activities_sorts_by_access_time(self):
        """Test get_recent_activities sorts by MAX(last_accessed_at, updated_at)."""
        from django.utils import timezone
        from datetime import timedelta
        
        # Create user with activities
        user = User.objects.create_user(username='testuser', password='pass123')
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='development',
            author=user
        )
        workflow = Workflow.objects.create(
            playbook=playbook,
            name='Test Workflow',
            description='Test'
        )
        
        activity1 = Activity.objects.create(
            workflow=workflow,
            name='Activity 1',
            guidance='Test',
            order=1
        )
        
        activity2 = Activity.objects.create(
            workflow=workflow,
            name='Activity 2',
            guidance='Test',
            order=2
        )
        
        # Set activity2's last_accessed_at to future (making it more recent)
        activity2.last_accessed_at = timezone.now() + timedelta(hours=1)
        activity2.save()
        
        # Get recent activities
        recent = list(ActivityService.get_recent_activities(user, limit=10))
        
        # Assertions - activity2 should be first (most recently accessed)
        assert recent[0] == activity2
        assert recent[1] == activity1


@pytest.mark.django_db
class TestListActivitiesForPlaybook:
    """Tests for ActivityService.list_activities_for_playbook."""

    def test_returns_only_activities_for_given_playbook_and_author(self):
        u1 = User.objects.create_user(username='u1Acts', password='x')
        u2 = User.objects.create_user(username='u2Acts', password='x')
        pb1 = Playbook.objects.create(
            name='PB1Acts', description='d', category='development', author=u1, source='owned',
        )
        pb2 = Playbook.objects.create(
            name='PB2Acts', description='d', category='development', author=u2, source='owned',
        )
        wf1 = Workflow.objects.create(playbook=pb1, name='W1', description='d', order=1)
        wf2 = Workflow.objects.create(playbook=pb2, name='W2', description='d', order=1)
        a1 = Activity.objects.create(workflow=wf1, name='Only PB1', guidance='g', order=1)
        Activity.objects.create(workflow=wf2, name='Only PB2', guidance='g', order=1)

        qs = ActivityService.list_activities_for_playbook(pb1.pk, u1)
        assert list(qs) == [a1]
        assert ActivityService.list_activities_for_playbook(pb1.pk, u2).count() == 0

    def test_orders_by_workflow_order_then_activity_order(self):
        user = User.objects.create_user(username='ordUserActs', password='x')
        pb = Playbook.objects.create(
            name='PBOrd', description='d', category='development', author=user, source='owned',
        )
        wf_b = Workflow.objects.create(playbook=pb, name='Second WF', description='d', order=2)
        wf_a = Workflow.objects.create(playbook=pb, name='First WF', description='d', order=1)
        act_b2 = Activity.objects.create(workflow=wf_b, name='B2', guidance='g', order=2)
        act_b1 = Activity.objects.create(workflow=wf_b, name='B1', guidance='g', order=1)
        act_a2 = Activity.objects.create(workflow=wf_a, name='A2', guidance='g', order=2)
        act_a1 = Activity.objects.create(workflow=wf_a, name='A1', guidance='g', order=1)

        ordered = list(ActivityService.list_activities_for_playbook(pb.pk, user))
        assert ordered == [act_a1, act_a2, act_b1, act_b2]
