from django.urls import path

from methodology import browser_views

urlpatterns = [
    path("<int:pk>/", browser_views.browser_playbook, name="browser_playbook"),
]
