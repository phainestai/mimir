"""URL configuration for skill views.

All URLs are scoped under:
  /playbooks/<playbook_pk>/workflows/<workflow_pk>/activities/<activity_pk>/skill/
"""

from django.urls import path
from methodology import skill_views

urlpatterns = [
    path('', skill_views.skill_detail, name='skill_detail'),
    path('create/', skill_views.skill_create, name='skill_create'),
    path('edit/', skill_views.skill_edit, name='skill_edit'),
    path('delete/', skill_views.skill_delete, name='skill_delete'),
    path('delete/confirm/', skill_views.skill_delete_confirm, name='skill_delete_confirm'),
]
