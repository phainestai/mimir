"""Admin configuration for methodology models."""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from methodology.models import (
    Activity,
    Agent,
    Artifact,
    ArtifactInput,
    JoinRequest,
    Playbook,
    PlaybookVersion,
    PipChange,
    ProcessImprovementProposal,
    Rule,
    Skill,
    Team,
    TeamMembership,
    TeamPlaybook,
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


def _pip_admin_exc_text(exc: ValidationError | Exception) -> str:
    """Render admin action errors cleanly."""
    if isinstance(exc, ValidationError):
        msg_dict = getattr(exc, "message_dict", None)
        if msg_dict:
            return str(msg_dict)
        msgs = getattr(exc, "messages", None)
        if msgs:
            return "; ".join(str(m) for m in msgs)
    return str(exc)


_PIP_INLINE_FREEZE_AFTER = frozenset(
    {
        ProcessImprovementProposal.STATUS_ACCEPTED,
        ProcessImprovementProposal.STATUS_ACCEPTED_PARTIAL,
        ProcessImprovementProposal.STATUS_REJECTED,
    }
)


class PipChangeInlineForm(forms.ModelForm):
    """Custom form for PipChange inline to make admin_note compact."""

    class Meta:
        model = PipChange
        fields = "__all__"
        widgets = {
            "admin_note": forms.Textarea(
                attrs={
                    "rows": 2,
                    "cols": 30,
                    "placeholder": "accepted — fits strategy; rejected — conflicts with…",
                }
            ),
        }


class PipChangeInline(admin.TabularInline):
    """Inline editor for structured PIP deltas."""

    model = PipChange
    form = PipChangeInlineForm
    extra = 0
    show_change_link = True
    fields = (
        "change_type",
        "entity_type",
        "name",
        "target_id",
        "target_name_snapshot",
        "content",
        "galdr_recommendation",
        "galdr_reasoning",
        "admin_decision",
        "admin_note",
        "order",
        "internal_ref",
        "relationship_type",
        "source_entity_type",
        "source_entity_ref",
        "target_entity_type",
        "target_entity_ref",
        "parent_workflow",
        "parent_workflow_ref",
        "insert_after_activity",
        "insert_after_activity_ref",
        "phase_ref",
        "produced_by_activity_ref",
        "artifact_type",
        "artifact_is_required",
        "append_to_playbook_end",
        "created_at",
        "updated_at",
    )

    def get_readonly_fields(self, request, obj=None):
        audit_always = frozenset(
            {
                "galdr_recommendation",
                "galdr_reasoning",
                "created_at",
                "updated_at",
            }
        )
        field_names = [f.name for f in PipChange._meta.fields if not f.primary_key]
        if obj is None:
            return tuple(sorted(audit_always))
        if obj.status == ProcessImprovementProposal.STATUS_REVIEWED:
            return tuple(n for n in field_names if n not in {"admin_decision", "admin_note"})
        if obj.status in _PIP_INLINE_FREEZE_AFTER:
            return tuple(field_names)
        return tuple(sorted(audit_always))


@admin.register(ProcessImprovementProposal)
class ProcessImprovementProposalAdmin(admin.ModelAdmin):
    inlines = (PipChangeInline,)
    list_display = (
        "title",
        "playbook",
        "status",
        "created_by",
        "change_count_column",
        "submitted_at",
        "updated_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "playbook__name", "summary")
    readonly_fields = (
        "created_at",
        "updated_at",
        "status_changed_at",
    )
    raw_id_fields = ("playbook", "created_by")
    actions = ("finalize_reviewed_pips",)

    @admin.action(description="Finalize reviewed PIPs (apply accepted changes + notify)")
    def finalize_reviewed_pips(self, request, queryset):
        """Admin queue action — thin wrapper around :class:`PIPAdminService`."""

        from methodology.services.pip_admin_service import PIPAdminService

        ok = skipped = failed = 0
        for row in queryset.iterator():
            if row.status != ProcessImprovementProposal.STATUS_REVIEWED:
                skipped += 1
                continue
            try:
                PIPAdminService.finalize_pip(row, request.user)
                ok += 1
                self.message_user(
                    request,
                    f'Finalised "{row.title}" (PIP-{row.pk}).',
                    level=messages.SUCCESS,
                )
            except ValidationError as exc:
                failed += 1
                self.message_user(
                    request,
                    f"PIP-{row.pk}: {_pip_admin_exc_text(exc)}",
                    level=messages.ERROR,
                )
        if skipped:
            self.message_user(
                request,
                f"Skipped {skipped} proposal(s) not in Reviewed state.",
                level=messages.WARNING,
            )
        if ok == 0 and failed == 0 and not skipped:
            self.message_user(request, "No proposals selected.", level=messages.WARNING)

    @staticmethod
    def change_count_column(obj):
        return obj.changes.count()

    change_count_column.short_description = "Changes"


@admin.register(PipChange)
class PipChangeAdmin(admin.ModelAdmin):
    list_display = ("id", "pip", "change_type", "entity_type", "order", "name")
    list_filter = ("change_type", "entity_type")
    raw_id_fields = ("pip", "parent_workflow", "insert_after_activity")


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


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    """Admin configuration for Team model."""

    list_display = ["name", "visibility", "join_policy", "category", "admin", "created_at"]
    search_fields = ["name", "description"]
    list_filter = ["visibility", "category", "join_policy"]
    readonly_fields = ("created_at", "updated_at")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    """Admin configuration for TeamMembership model."""

    list_display = ["team", "user", "role", "joined_at"]
    list_filter = ["role"]
    readonly_fields = ("joined_at",)


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    """Admin configuration for JoinRequest model."""

    list_display = ["team", "user", "source", "status", "requested_at"]
    list_filter = ["status", "source"]
    readonly_fields = ("requested_at",)


@admin.register(TeamPlaybook)
class TeamPlaybookAdmin(admin.ModelAdmin):
    """Admin configuration for TeamPlaybook model."""

    list_display = ["team", "playbook", "added_by", "added_at"]
    readonly_fields = ("added_at",)
