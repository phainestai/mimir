"""Admin configuration for methodology models."""

from django.contrib import admin
from methodology.models import Playbook, PlaybookVersion, Workflow, Activity, Artifact, ArtifactInput, Skill, Agent


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    """Admin configuration for Playbook model."""
    list_display = ('name', 'author', 'category', 'status', 'source', 'version', 'created_at')
    list_filter = ('status', 'category', 'source', 'visibility')
    search_fields = ('name', 'description', 'tags')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PlaybookVersion)
class PlaybookVersionAdmin(admin.ModelAdmin):
    """Admin configuration for PlaybookVersion model."""
    list_display = ('playbook', 'version_number', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('playbook__name', 'change_summary')
    readonly_fields = ('created_at',)


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    """Admin configuration for Workflow model."""
    list_display = ('name', 'playbook', 'order', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'playbook__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('playbook', 'order')


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Admin configuration for Activity model."""
    list_display = ('name', 'workflow', 'phase', 'order', 'predecessor', 'successor')
    list_filter = ('phase', 'created_at')
    search_fields = ('name', 'guidance', 'workflow__name', 'workflow__playbook__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('workflow', 'order')
    fieldsets = (
        ('Basic Information', {
            'fields': ('workflow', 'name', 'guidance')
        }),
        ('Organization', {
            'fields': ('order', 'phase')
        }),
        ('Dependencies', {
            'fields': ('predecessor', 'successor')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    """Admin configuration for Artifact model."""
    list_display = ('name', 'type', 'produced_by', 'playbook', 'is_required', 'created_at')
    list_filter = ('type', 'is_required', 'playbook')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ArtifactInput)
class ArtifactInputAdmin(admin.ModelAdmin):
    """Admin configuration for ArtifactInput model."""
    list_display = ('artifact', 'activity', 'is_required', 'created_at')
    list_filter = ('is_required',)
    search_fields = ('artifact__name', 'activity__name')


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin configuration for Skill model."""
    list_display = ('title', 'activity', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'activity__name')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('activity',)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin configuration for Agent model."""
    list_display = ('name', 'playbook', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'playbook__name')
    list_filter = ('created_at', 'playbook')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('playbook',)
