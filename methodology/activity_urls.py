"""URL configuration for activity views."""

from django.urls import path, include
from methodology import activity_views

# All URLs are scoped under /playbooks/<playbook_pk>/workflows/<workflow_pk>/activities/
urlpatterns = [
    path('', activity_views.activity_list, name='activity_list'),
    path('create/', activity_views.activity_create, name='activity_create'),
    path('<int:activity_pk>/', activity_views.activity_detail, name='activity_detail'),
    path('<int:activity_pk>/edit/', activity_views.activity_edit, name='activity_edit'),
    path('<int:activity_pk>/delete/', activity_views.activity_delete, name='activity_delete'),

]
