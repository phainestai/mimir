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



@pytest.mark.django_db(transaction=True)
class TestCreateActivityAutoOrder:
    """Auto-order assignment must be sequential even under concurrent calls."""

    def setup_method(self):
        self.user = User.objects.create_user(username="order_user", password="pass")
        pb = Playbook.objects.create(
            name="Order PB", description="", category="development", author=self.user
        )
        self.workflow = Workflow.objects.create(
            playbook=pb, name="Order WF", description=""
        )

    def test_sequential_creates_get_sequential_orders(self):
        """Four sequential create_activity calls must yield orders 1,2,3,4."""
        names = ["Alpha", "Beta", "Gamma", "Delta"]
        activities = [
            ActivityService.create_activity(workflow=self.workflow, name=n)
            for n in names
        ]
        orders = [a.order for a in activities]
        assert orders == [1, 2, 3, 4], f"Expected [1,2,3,4], got {orders}"

    def test_concurrent_creates_get_unique_orders(self):
        """Concurrent thread-pool calls must not produce duplicate order values.

        Simulates the MCP pattern where sync_to_async runs each call in a
        separate thread from the default executor.

        SQLite serialises writers via its busy-timeout; each thread retries on
        OperationalError (table/database locked) so the test stays deterministic.
        """
        import time
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from django.db import OperationalError, connection

        names = ["One", "Two", "Three", "Four"]

        def create(name):
            from django.db import connection as conn
            for attempt in range(10):
                try:
                    return ActivityService.create_activity(workflow=self.workflow, name=name)
                except OperationalError:
                    conn.close()
                    time.sleep(0.05 * (attempt + 1))
            return ActivityService.create_activity(workflow=self.workflow, name=name)

        # Close main-thread connection so each worker thread starts with a fresh one.
        connection.close()

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(create, n) for n in names]
            activities = [f.result() for f in as_completed(futures)]

        orders = sorted(a.order for a in activities)
        assert orders == [1, 2, 3, 4], (
            f"Concurrent creates produced duplicate/missing orders: {orders}"
        )


@pytest.mark.django_db
@pytest.mark.django_db
class TestSetPredecessorBidirectional:
    """set_predecessor must keep predecessor↔successor FKs in sync."""

    @pytest.fixture(autouse=True)
    def setup(self):
        user = User.objects.create_user(username='pred_test_user', password='x')
        pb = Playbook.objects.create(
            name='Pred PB', description='', category='test',
            status='draft', source='owned', author=user,
        )
        wf = Workflow.objects.create(playbook=pb, name='Pred WF', description='', order=1)
        self.act_a = Activity.objects.create(workflow=wf, name='A', guidance='', order=1)
        self.act_b = Activity.objects.create(workflow=wf, name='B', guidance='', order=2)
        self.act_c = Activity.objects.create(workflow=wf, name='C', guidance='', order=3)

    def test_sets_successor_on_predecessor(self):
        """set_predecessor(B, A) must also write A.successor = B."""
        ActivityService.set_predecessor(self.act_b, self.act_a)
        self.act_a.refresh_from_db()
        assert self.act_a.successor_id == self.act_b.pk

    def test_chain_a_b_c(self):
        """set_predecessor(B,A) then set_predecessor(C,B) builds A→B→C."""
        ActivityService.set_predecessor(self.act_b, self.act_a)
        ActivityService.set_predecessor(self.act_c, self.act_b)
        self.act_a.refresh_from_db()
        self.act_b.refresh_from_db()
        assert self.act_a.successor_id == self.act_b.pk
        assert self.act_b.successor_id == self.act_c.pk

    def test_replacing_predecessor_clears_old_successor(self):
        """Replacing B's predecessor from A to C must clear A.successor."""
        ActivityService.set_predecessor(self.act_b, self.act_a)   # A→B
        ActivityService.set_predecessor(self.act_b, self.act_c)   # C→B (A is now orphaned)
        self.act_a.refresh_from_db()
        self.act_c.refresh_from_db()
        assert self.act_a.successor_id is None   # A no longer points at B
        assert self.act_c.successor_id == self.act_b.pk


class TestListActivitiesForPlaybook:
    """Tests for ActivityService.list_activities_for_playbook."""

    def test_returns_activities_when_user_can_view_playbook(self):
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

    def test_public_playbook_lists_activities_for_non_owner(self):
        u1 = User.objects.create_user(username='u1PubActs', password='x')
        u2 = User.objects.create_user(username='u2PubActs', password='x')
        pb = Playbook.objects.create(
            name='PubPBActs',
            description='d',
            category='development',
            author=u1,
            source='owned',
            visibility='public',
            status='released',
        )
        wf = Workflow.objects.create(playbook=pb, name='W', description='d', order=1)
        a1 = Activity.objects.create(workflow=wf, name='SharedAct', guidance='g', order=1)
        qs = ActivityService.list_activities_for_playbook(pb.pk, u2)
        assert list(qs) == [a1]

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
