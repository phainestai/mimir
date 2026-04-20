"""URL configuration for rule views — playbook-scoped /playbooks/<pk>/rules/."""

from django.urls import path

from methodology import rule_views

urlpatterns = [
    path('', rule_views.rule_list, name='rule_list_playbook'),
    path('create/', rule_views.rule_create, name='rule_create'),
    path('<int:rule_pk>/', rule_views.rule_detail, name='rule_detail'),
    path('<int:rule_pk>/edit/', rule_views.rule_edit, name='rule_edit'),
    path('<int:rule_pk>/delete/', rule_views.rule_delete, name='rule_delete'),
    path('<int:rule_pk>/delete/confirm/', rule_views.rule_delete_confirm, name='rule_delete_confirm'),
]
