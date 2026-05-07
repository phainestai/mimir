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

from django.contrib import admin
from django.urls import path, include
from methodology import views as methodology_views
from methodology import workflow_views
from methodology import activity_views
from methodology import skill_views
from methodology import rule_views
from methodology import agent_views
from methodology import artifact_views
from methodology import phase_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("accounts.urls")),  # Changed from accounts/ per SAO.md URL convention
    path("dashboard/", methodology_views.dashboard, name="dashboard"),
    path("dashboard/activities/", methodology_views.dashboard_activities, name="dashboard_activities"),
    path("", methodology_views.index, name="index"),
    path("pip/list/", methodology_views.pip_list, name="pip_list"),
    path("search/", methodology_views.global_search, name="global_search"),
    path("search/suggestions/", methodology_views.global_search_suggestions, name="global_search_suggestions"),
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
