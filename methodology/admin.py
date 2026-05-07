"""Admin configuration for methodology models."""

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from methodology.models import (
    Activity,
    Agent,
    Artifact,
    ArtifactInput,
    Playbook,
    PlaybookVersion,
    ProcessImprovementProposal,
    Rule,
    Skill,
    Workflow,
)


@admin.register(Playbook)
class PlaybookAdmin(admin.ModelAdmin):
    """Admin configuration for Playbook model."""

    list_display = ('name', 'author', 'category', 'status', 'source', 'version', 'created_at')
    list_filter = ('status', 'category', 'source', 'visibility')
    search_fields = ('name', 'description', 'tags')
    readonly_fields = ('created_at', 'updated_at')
    actions = ('revert_released_playbooks_to_draft',)

    @admin.action(description="Revert Released → Draft (keeps numeric version)")
    def revert_released_playbooks_to_draft(self, request, queryset):
        from methodology.services.playbook_service import PlaybookService

        for playbook in queryset:
            try:
                PlaybookService.revert_released_playbook_to_draft(
                    playbook.pk,
                    actor=request.user,
                    reason=f"Admin revert (user id={request.user.pk}, playbook id={playbook.pk})",
                )
            except (ValidationError, PermissionError) as exc:
                self.message_user(request, f"{playbook.name}: {exc}", level=messages.ERROR)
            else:
                self.message_user(
                    request, f'Reverted "{playbook.name}" to draft.', level=messages.SUCCESS
                )


@admin.register(PlaybookVersion)
class PlaybookVersionAdmin(admin.ModelAdmin):
    """Admin configuration for PlaybookVersion model."""

    list_display = (
        "playbook",
        "version_number",
        "is_major",
        "source",
        "pip",
        "created_at",
    )
    list_filter = ("is_major", "source", "created_at")
    search_fields = ("playbook__name", "change_summary", "description")
    readonly_fields = ("created_at",)
    raw_id_fields = ("pip",)


@admin.register(ProcessImprovementProposal)
class ProcessImprovementProposalAdmin(admin.ModelAdmin):
    list_display = ("title", "playbook", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("title", "playbook__name")
    readonly_fields = ("created_at",)
    raw_id_fields = ("playbook",)


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
    filter_horizontal = ('rules',)
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
    list_display = ('title', 'playbook', 'capability_domain', 'technology_stack', 'created_at')
    search_fields = ('title', 'content', 'capability_domain', 'technology_stack')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('playbook',)


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    """Admin configuration for Rule model."""
    list_display = ('title', 'slug', 'playbook', 'always_apply', 'created_at')
    search_fields = ('title', 'slug', 'content')
    list_filter = ('always_apply', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('playbook',)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    """Admin configuration for Agent model."""
    list_display = ('name', 'playbook', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'playbook__name')
    list_filter = ('created_at', 'playbook')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('playbook',)
