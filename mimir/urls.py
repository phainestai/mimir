"""
URL configuration for mimir project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from methodology import views as methodology_views
from methodology import workflow_views
from methodology import activity_views
from methodology import skill_views
from methodology import rule_views
from methodology import agent_views
from methodology import artifact_views
from methodology import phase_views
from methodology import pip_views
from mimir import health_views
from methodology.api.viewsets import (
    PlaybookViewSet, WorkflowViewSet, ActivityViewSet
)
from methodology.api.viewsets_resources import (
    SkillViewSet, AgentViewSet, ArtifactViewSet,
    ArtifactInputViewSet, PhaseViewSet, RuleViewSet, PIPViewSet, TeamViewSet
)
from methodology.api.bug_report_views import BugReportSubmitView
from methodology import feedback_views
from accounts import legal_views

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'playbooks', PlaybookViewSet, basename='api-playbook')
router.register(r'workflows', WorkflowViewSet, basename='api-workflow')
router.register(r'activities', ActivityViewSet, basename='api-activity')
router.register(r'skills', SkillViewSet, basename='api-skill')
router.register(r'agents', AgentViewSet, basename='api-agent')
router.register(r'artifacts', ArtifactViewSet, basename='api-artifact')
router.register(r'artifact-inputs', ArtifactInputViewSet, basename='api-artifact-input')
router.register(r'phases', PhaseViewSet, basename='api-phase')
router.register(r'rules', RuleViewSet, basename='api-rule')
router.register(r'pips', PIPViewSet, basename='api-pip')
router.register(r'teams', TeamViewSet, basename='api-team')

urlpatterns = [
    path("health/", health_views.health_check, name="health_check"),
    path(
        "feedback/report/",
        feedback_views.submit_feedback,
        name="feedback_report",
    ),
    path("admin/", admin.site.urls),
    # API endpoints
    path("api/", include(router.urls)),
    path("api/auth/token/", obtain_auth_token, name="api_token_auth"),
    path(
        "api/feedback/report/",
        BugReportSubmitView.as_view(),
        name="api_feedback_report",
    ),
    path("api/auth/", include("accounts.api_urls")),  # Registration, token refresh, etc.
    path("auth/", include("accounts.urls")),  # Changed from accounts/ per SAO.md URL convention
    path("notifications/", include("methodology.notification_urls")),
    # Legal documents (public, no login required)
    path("legal/privacy/", legal_views.privacy_policy, name="privacy_policy"),
    path("legal/privacy/pdf/", legal_views.privacy_policy_pdf, name="privacy_policy_pdf"),
    path("legal/terms/", legal_views.user_agreement, name="user_agreement"),
    path("legal/terms/pdf/", legal_views.user_agreement_pdf, name="user_agreement_pdf"),
    path("dashboard/", methodology_views.dashboard, name="dashboard"),
    path("dashboard/activities/", methodology_views.dashboard_activities, name="dashboard_activities"),
    path("", methodology_views.index, name="index"),
    path("use-cases/", methodology_views.use_cases, name="use_cases"),
    path("pip/list/", pip_views.PipListLegacyRedirect.as_view()),
    path("pips/", pip_views.pip_list, name="pip_list"),
    path("pips/create/", pip_views.pip_create, name="pip_create"),
    path("pips/<int:pk>/", pip_views.pip_detail, name="pip_detail"),
    path("pips/<int:pk>/edit/", pip_views.pip_draft_editor, name="pip_edit"),
    path("pips/<int:pk>/changes/add/", pip_views.pip_add_change, name="pip_add_change"),
    path(
        "pips/<int:pk>/changes/<int:change_id>/remove/",
        pip_views.pip_remove_change,
        name="pip_remove_change",
    ),
    path("pips/<int:pk>/preview/", pip_views.pip_preview, name="pip_preview"),
    path("pips/<int:pk>/submit/", pip_views.pip_submit_review, name="pip_submit_review"),
    path("pips/<int:pk>/withdraw/", pip_views.pip_withdraw, name="pip_withdraw"),
    path("pips/<int:pk>/admin-review/", pip_views.pip_admin_review, name="pip_admin_review"),
    path("search/", methodology_views.global_search, name="global_search"),
    path("search/suggestions/", methodology_views.global_search_suggestions, name="global_search_suggestions"),
    path("teams/", include("methodology.team_urls")),
    path("playbooks/", include("methodology.playbook_urls")),
    path("playbooks/", include("methodology.workflow_urls")),  # Workflow URLs scoped to playbook
    path("playbooks/<int:playbook_pk>/workflows/<int:workflow_pk>/activities/", include("methodology.activity_urls")),  # Activity URLs scoped to workflow
    path("playbooks/<int:playbook_pk>/phases/", include("methodology.phase_urls")),  # Phase URLs scoped to playbook
    path("playbooks/<int:playbook_pk>/skills/", include("methodology.skill_urls")),  # Skill URLs scoped to playbook
    path("playbooks/<int:playbook_pk>/rules/", include("methodology.rule_urls")),  # Rule URLs scoped to playbook
    path(
        "playbooks/<int:playbook_pk>/activities/",
        activity_views.activity_list_for_playbook,
        name="activity_list_for_playbook",
    ),
    path(
        "playbooks/<int:playbook_pk>/agents/",
        agent_views.agent_list_for_playbook,
        name="agent_list_for_playbook",
    ),
    path("", include("methodology.artifact_urls")),  # Artifact URLs
    path("workflows/", workflow_views.workflow_global_list, name="workflow_global_list"),  # Global workflows view
    path("phases/", phase_views.phase_list_global, name="phase_list_global"),  # Global phases view
    path("activities/", activity_views.activity_global_list, name="activity_global_list"),  # Global activities view
    path("skills/", skill_views.skill_list_global, name="skill_list"),  # Global skills view
    path("rules/", rule_views.rule_list_global, name="rule_list"),  # Global rules view
    path("agents/", include("methodology.agent_urls")),  # Agent views (list, create, detail)
    path("artifacts/", artifact_views.artifact_list_global, name="artifact_list_global"),  # Global artifacts view
]

if settings.DEBUG:
    urlpatterns.append(
        path("mockups/", include("mockups.urls")),
    )
