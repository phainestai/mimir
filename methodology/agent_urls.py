"""URL configuration for agent views.

Global agent list is available at /agents/.
"""

from django.urls import path

from methodology import agent_views

urlpatterns = [
    path('', agent_views.agent_list_global, name='agent_list'),
]
