"""URL configuration for skill views.

All skill URLs are playbook-scoped:
  /playbooks/<playbook_pk>/skills/
"""

from django.urls import path
from methodology import skill_views

urlpatterns = [
    path('', skill_views.skill_list, name='skill_list_playbook'),
    path('create/', skill_views.skill_create, name='skill_create'),
    path('<int:skill_pk>/', skill_views.skill_detail, name='skill_detail'),
    path('<int:skill_pk>/edit/', skill_views.skill_edit, name='skill_edit'),
    path('<int:skill_pk>/delete/', skill_views.skill_delete, name='skill_delete'),
    path('<int:skill_pk>/delete/confirm/', skill_views.skill_delete_confirm, name='skill_delete_confirm'),
]
