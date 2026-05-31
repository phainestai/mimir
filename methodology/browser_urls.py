from django.urls import path

from methodology import browser_views

urlpatterns = [
    path("", browser_views.browser_root, name="browser_root"),
    path("<int:pk>/", browser_views.browser_playbook, name="browser_playbook"),
]
