"""
DRF Serializers for Mimir API.

Maps Django models to JSON representations for API requests/responses.
"""

from rest_framework import serializers
from methodology.models import (
    Playbook, Workflow, Activity, Skill, Agent, Artifact, 
    ArtifactInput, Phase, Rule
)


class PlaybookSerializer(serializers.ModelSerializer):
    """Serializer for Playbook model."""
    
    workflow_count = serializers.SerializerMethodField()
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    
    class Meta:
        model = Playbook
        fields = [
            'id', 'name', 'description', 'category', 'status', 'version',
            'author_id', 'created_at', 'updated_at', 'workflow_count'
        ]
        read_only_fields = ['id', 'status', 'version', 'author_id', 'created_at', 'updated_at']
    
    def get_workflow_count(self, obj):
        """Get count of workflows in playbook."""
        return obj.workflows.count()


class PlaybookListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for playbook lists."""
    
    workflow_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Playbook
        fields = ['id', 'name', 'status', 'version', 'category', 'workflow_count']
    
    def get_workflow_count(self, obj):
        """Get count of workflows in playbook."""
        return obj.workflows.count()


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow model."""
    
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'playbook_id', 'name', 'description', 'abbreviation',
            'order', 'activity_count'
        ]
        read_only_fields = ['id', 'order']
    
    def get_activity_count(self, obj):
        """Get count of activities in workflow."""
        return obj.activities.count()


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model."""
    
    predecessor_name = serializers.CharField(source='predecessor.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    
    class Meta:
        model = Activity
        fields = [
            'id', 'workflow_id', 'name', 'guidance', 'phase_id', 'order',
            'predecessor_id', 'predecessor_name', 'agent_id', 'agent_name',
            'skill_id', 'skill_title'
        ]
        read_only_fields = ['id', 'order', 'predecessor_name', 'agent_name', 'skill_title']


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for Skill model."""
    
    playbook_id = serializers.IntegerField()
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = [
            'id', 'playbook_id', 'title', 'content', 'capability_domain',
            'technology_stack', 'activity_count'
        ]
        read_only_fields = ['id', 'activity_count']
    
    def get_activity_count(self, obj):
        """Get count of activities using this skill."""
        return obj.activities.count()


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent model."""
    
    playbook_id = serializers.IntegerField()
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Agent
        fields = ['id', 'playbook_id', 'name', 'description', 'activity_count']
        read_only_fields = ['id', 'activity_count']
    
    def get_activity_count(self, obj):
        """Get count of activities assigned to this agent."""
        return obj.activities.count()


class ArtifactSerializer(serializers.ModelSerializer):
    """Serializer for Artifact model."""
    
    playbook_id = serializers.IntegerField()
    produced_by_id = serializers.IntegerField()
    consumer_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Artifact
        fields = [
            'id', 'playbook_id', 'produced_by_id', 'name', 'description',
            'type', 'is_required', 'consumer_count'
        ]
        read_only_fields = ['id', 'consumer_count']
    
    def get_consumer_count(self, obj):
        """Get count of activities consuming this artifact."""
        return obj.consumed_by.count()


class ArtifactInputSerializer(serializers.ModelSerializer):
    """Serializer for ArtifactInput (artifact-to-activity link)."""
    
    class Meta:
        model = ArtifactInput
        fields = ['id', 'artifact_id', 'activity_id', 'is_required']
        read_only_fields = ['id']


class PhaseSerializer(serializers.ModelSerializer):
    """Serializer for Phase model."""
    
    playbook_id = serializers.IntegerField()
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Phase
        fields = ['id', 'playbook_id', 'name', 'description', 'order', 'activity_count']
        read_only_fields = ['id', 'activity_count']
    
    def get_activity_count(self, obj):
        """Get count of activities in this phase."""
        return obj.activities.count()


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for Rule model."""
    
    playbook_id = serializers.IntegerField()
    
    class Meta:
        model = Rule
        fields = ['id', 'playbook_id', 'title', 'slug', 'content', 'always_apply']
        read_only_fields = ['id']
