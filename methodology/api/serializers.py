"""
DRF Serializers for Mimir API.

Maps Django models to JSON representations for API requests/responses.
"""

from rest_framework import serializers
from methodology.models import (
    Playbook, Workflow, Activity, Skill, Agent, Artifact,
    ArtifactInput, Phase, Rule, ProcessImprovementProposal, PipChange,
    Team, JoinRequest, TeamMembership
)


class PlaybookSerializer(serializers.ModelSerializer):
    """Serializer for Playbook model."""
    
    workflow_count = serializers.SerializerMethodField()
    author_id = serializers.IntegerField(source='author.id', read_only=True)
    
    class Meta:
        model = Playbook
        fields = [
            'id', 'name', 'description', 'category', 'status', 'version',
            'visibility', 'author_id', 'created_at', 'updated_at', 'workflow_count'
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
        fields = ['id', 'name', 'status', 'version', 'category', 'visibility', 'workflow_count']
    
    def get_workflow_count(self, obj):
        """Get count of workflows in playbook."""
        return obj.workflows.count()


class WorkflowSerializer(serializers.ModelSerializer):
    """Serializer for Workflow model."""

    activity_count = serializers.SerializerMethodField()
    activities = serializers.SerializerMethodField()

    class Meta:
        model = Workflow
        fields = [
            'id', 'playbook_id', 'name', 'description', 'abbreviation',
            'order', 'activity_count', 'activities'
        ]
        read_only_fields = ['id', 'order']

    def get_activity_count(self, obj):
        """Get count of activities in workflow."""
        return obj.activities.count()

    def get_activities(self, obj):
        """Return minimal activity stubs (id, name, order) — no body fields."""
        return [
            {'id': a.id, 'name': a.name, 'order': a.order}
            for a in obj.activities.order_by('order')
        ]


class ActivitySkillSerializer(serializers.ModelSerializer):
    """Compact skill payload embedded on activity responses."""

    class Meta:
        model = Skill
        fields = ['id', 'title', 'capability_domain', 'technology_stack']


class ActivityListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for activity lists — guidance excluded to keep payloads small."""

    predecessor_name = serializers.CharField(source='predecessor.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    skills = ActivitySkillSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'workflow_id', 'name', 'phase_id', 'order',
            'predecessor_id', 'predecessor_name', 'agent_id', 'agent_name',
            'skills',
        ]
        read_only_fields = ['id', 'predecessor_name', 'agent_name', 'skills']


class ActivitySerializer(serializers.ModelSerializer):
    """Serializer for Activity model — full detail including guidance."""

    workflow_id = serializers.IntegerField()
    phase_id = serializers.IntegerField(allow_null=True, required=False)
    predecessor_id = serializers.IntegerField(allow_null=True, required=False)
    agent_id = serializers.IntegerField(allow_null=True, required=False)
    predecessor_name = serializers.CharField(source='predecessor.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    skills = ActivitySkillSerializer(many=True, read_only=True)

    class Meta:
        model = Activity
        fields = [
            'id', 'workflow_id', 'name', 'guidance', 'phase_id', 'order',
            'predecessor_id', 'predecessor_name', 'agent_id', 'agent_name',
            'skills',
        ]
        read_only_fields = ['id', 'predecessor_name', 'agent_name', 'skills']


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
        return obj.inputs.count()


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
    slug = serializers.SlugField(required=False, default='', allow_blank=True)

    class Meta:
        model = Rule
        fields = ['id', 'playbook_id', 'title', 'slug', 'content', 'always_apply']
        read_only_fields = ['id']


class PipChangeSerializer(serializers.ModelSerializer):
    """Serializer for PipChange model."""

    parent_workflow_id = serializers.IntegerField(source='parent_workflow.id', read_only=True)
    insert_after_activity_id = serializers.IntegerField(
        source='insert_after_activity.id', read_only=True
    )

    class Meta:
        model = PipChange
        fields = [
            'id', 'order', 'change_type', 'entity_type', 'name',
            'target_id', 'target_name_snapshot', 'content',
            'parent_workflow_id', 'insert_after_activity_id', 'append_to_playbook_end',
            'internal_ref', 'parent_workflow_ref', 'insert_after_activity_ref',
            'phase_ref', 'produced_by_activity_ref', 'artifact_type', 'artifact_is_required',
            'relationship_type', 'source_entity_type', 'source_entity_ref',
            'target_entity_type', 'target_entity_ref',
            'galdr_recommendation', 'galdr_reasoning',
            'admin_decision', 'admin_note',
        ]
        read_only_fields = ['id', 'order']


class PIPSerializer(serializers.ModelSerializer):
    """Serializer for ProcessImprovementProposal (PIP)."""

    submitted_by_username = serializers.CharField(
        source='created_by.username', read_only=True
    )
    changes_count = serializers.SerializerMethodField()
    changes = PipChangeSerializer(many=True, read_only=True)

    class Meta:
        model = ProcessImprovementProposal
        fields = [
            'id', 'playbook_id', 'title', 'summary', 'status',
            'submitted_by_username', 'submitted_at', 'status_changed_at',
            'changes_count', 'changes',
        ]
        read_only_fields = [
            'id', 'status', 'submitted_by_username',
            'submitted_at', 'status_changed_at', 'changes_count', 'changes',
        ]

    def get_changes_count(self, obj):
        """Return number of changes attached to this PIP."""
        return obj.changes.count()


class PIPListSerializer(serializers.ModelSerializer):
    """Lightweight PIP serializer for list views (no nested changes)."""

    submitted_by_username = serializers.CharField(
        source='created_by.username', read_only=True
    )
    changes_count = serializers.SerializerMethodField()

    class Meta:
        model = ProcessImprovementProposal
        fields = [
            'id', 'playbook_id', 'title', 'summary', 'status',
            'submitted_by_username', 'submitted_at', 'status_changed_at',
            'changes_count',
        ]

    def get_changes_count(self, obj):
        """Return number of changes (uses annotated field when available)."""
        if hasattr(obj, 'change_count'):
            return obj.change_count
        return obj.changes.count()


class TeamSerializer(serializers.ModelSerializer):
    """Full serializer for Team model."""
    
    admin_id = serializers.IntegerField(source='admin.id', read_only=True)
    admin_username = serializers.CharField(source='admin.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'visibility', 'join_policy', 'category',
            'admin_id', 'admin_username', 'member_count', 'created_at'
        ]
        read_only_fields = ['id', 'admin_id', 'admin_username', 'member_count', 'created_at']
    
    def get_member_count(self, obj):
        """Get count of team members."""
        return obj.memberships.count()


class TeamListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for team lists."""
    
    member_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'visibility', 'category', 'member_count']
    
    def get_member_count(self, obj):
        """Get count of team members."""
        return obj.memberships.count()


class JoinRequestSerializer(serializers.ModelSerializer):
    """Serializer for JoinRequest model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)
    
    class Meta:
        model = JoinRequest
        fields = [
            'id', 'team', 'team_name', 'user', 'user_email', 'user_username',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'team_name', 'user_email', 'user_username', 'created_at']
