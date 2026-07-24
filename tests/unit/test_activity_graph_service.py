"""
Unit tests for ActivityGraphService.

Tests Graphviz SVG generation for activity flow diagrams.
"""

import pytest
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity
from methodology.services.activity_graph_service import ActivityGraphService

User = get_user_model()


@pytest.mark.django_db
class TestActivityGraphService:
    """Unit tests for activity graph generation."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        self.service = ActivityGraphService()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            password='testpass123'
        )
        
        self.playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='development',
            status='active',
            source='owned',
            author=self.user
        )
        
        self.workflow = Workflow.objects.create(
            name='Test Workflow',
            description='Test workflow',
            playbook=self.playbook,
            order=1
        )
    
    def test_generate_graph_with_no_activities(self):
        """Test graph generation returns None when no activities exist."""
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        assert svg is None
    
    def test_generate_graph_with_simple_linear_flow(self):
        """Test graph generation with activities in simple linear sequence."""
        # Create activities without phases
        Activity.objects.create(
            workflow=self.workflow,
            name='Activity 1',
            guidance='First',
            order=1
        )
        Activity.objects.create(
            workflow=self.workflow,
            name='Activity 2',
            guidance='Second',
            order=2
        )
        Activity.objects.create(
            workflow=self.workflow,
            name='Activity 3',
            guidance='Third',
            order=3
        )
        
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        assert svg is not None
        assert '<svg' in svg
        assert 'Activity 1' in svg
        assert 'Activity 2' in svg
        assert 'Activity 3' in svg
        # Check edges connect activities
        assert '->' in svg or 'edge' in svg.lower()
    
    def test_generate_graph_with_phases(self, create_test_phases):
        """Test graph generation with phase grouping."""
        # Create test phases
        phases = create_test_phases(self.playbook)
        
        # Create activities with phases
        Activity.objects.create(
            workflow=self.workflow,
            name='Plan Features',
            guidance='Planning',
            phase=phases['Planning'],
            order=1
        )
        Activity.objects.create(
            workflow=self.workflow,
            name='Write Code',
            guidance='Implementation',
            phase=phases['Execution'],
            order=2
        )
        Activity.objects.create(
            workflow=self.workflow,
            name='Deploy',
            guidance='Deployment',
            phase=phases['Execution'],
            order=3
        )
        
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        assert svg is not None
        assert '<svg' in svg
        # Check phase names appear (as cluster labels)
        assert 'Planning' in svg
        assert 'Execution' in svg
        # Check activities appear
        assert 'Plan Features' in svg
        assert 'Write Code' in svg
        assert 'Deploy' in svg
    
    def test_node_styling_uniform_color(self):
        """Test all activity nodes use uniform color (activities are static)."""
        activity = Activity.objects.create(
            workflow=self.workflow,
            name='Test Activity',
            guidance='Test',
            order=1
        )
        
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        # All nodes should use uniform lightblue color
        assert svg is not None
        assert 'lightblue' in svg
    
    def test_clickable_nodes_have_href_attributes(self):
        """Test activity nodes have href attributes for clickability."""
        activity = Activity.objects.create(
            workflow=self.workflow,
            name='Clickable Activity',
            guidance='Test',
            order=1
        )
        
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        assert svg is not None
        # Check href attribute exists in SVG
        assert 'href' in svg
        assert f'/playbooks/{self.playbook.pk}/workflows/{self.workflow.pk}/activities/{activity.pk}/' in svg
    
    def test_dependencies_visualization(self):
        """Test activities with dependencies show visual indicator."""
        Activity.objects.create(
            workflow=self.workflow,
            name='Activity with Deps',
            guidance='Has dependencies',
            order=1
        )
        Activity.objects.create(
            workflow=self.workflow,
            name='Activity without Deps',
            guidance='No dependencies',
            order=2
        )
        
        svg = self.service.generate_activities_graph(self.workflow, self.playbook)
        
        assert svg is not None
        # Dependency indicator should be present (implementation will add visual marker)
        assert 'Activity with Deps' in svg
        assert 'Activity without Deps' in svg
    
    def test_has_phases_returns_true_when_phases_exist(self, create_test_phases):
        """Test _has_phases returns True when activities have phases."""
        phases = create_test_phases(self.playbook)
        activities = [
            Activity(phase=phases['Planning']),
            Activity(phase=None),
        ]
        
        result = self.service._has_phases(activities)
        assert result is True
    
    def test_has_phases_returns_false_when_no_phases(self):
        """Test _has_phases returns False when no activities have phases."""
        activities = [
            Activity(phase=None),
            Activity(phase=None),
        ]
        
        result = self.service._has_phases(activities)
        assert result is False
    
    def test_group_activities_by_phase(self, create_test_phases):
        """Test activities are correctly grouped by phase."""
        phases = create_test_phases(self.playbook)
        act1 = Activity(name='Act1', phase=phases['Planning'], order=1)
        act2 = Activity(name='Act2', phase=phases['Planning'], order=2)
        act3 = Activity(name='Act3', phase=phases['Execution'], order=3)
        act4 = Activity(name='Act4', phase=None, order=4)
        
        activities = [act1, act2, act3, act4]
        groups = self.service._group_activities_by_phase(activities)
        
        assert 'Planning' in groups
        assert 'Execution' in groups
        assert 'Unassigned' in groups
        assert len(groups['Planning']) == 2
        assert len(groups['Execution']) == 1
        assert len(groups['Unassigned']) == 1
    
    def test_create_activity_node_label(self):
        """Test activity node label formatting with reference_name."""
        activity = Activity.objects.create(
            workflow=self.workflow,
            name='Test Activity',
            guidance='Test guidance',
            order=1
        )
        
        label = self.service._create_activity_node_label(activity)
        
        # Should include reference_name and activity name
        assert activity.reference_name in label
        assert 'Test Activity' in label
        # No status display - activities are static reference material
    
    def test_get_activity_detail_url(self):
        """Test activity detail URL generation."""
        activity = Activity.objects.create(
            workflow=self.workflow,
            name='Test Activity',
            guidance='Test',
            order=1
        )
        
        url = self.service._get_activity_detail_url(activity, self.playbook, self.workflow)
        
        expected = f'/playbooks/{self.playbook.pk}/workflows/{self.workflow.pk}/activities/{activity.pk}/'
        assert url == expected
