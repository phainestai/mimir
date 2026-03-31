"""URL configuration for agent views.

Global agent list is available at /agents/.
Agent create is available at /agents/create/<playbook_pk>/.
Agent detail is available at /agents/<pk>/.
"""

from django.urls import path

from methodology import agent_views

urlpatterns = [
    path('', agent_views.agent_list_global, name='agent_list'),
    path('create/<int:playbook_pk>/', agent_views.agent_create, name='agent_create'),
    path('<int:pk>/', agent_views.agent_detail, name='agent_detail'),
    path('<int:pk>/edit/', agent_views.agent_edit, name='agent_edit'),
    path('<int:pk>/delete/', agent_views.agent_delete, name='agent_delete'),
]
