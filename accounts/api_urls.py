"""
API URL configuration for accounts app.

Provides REST endpoints for user registration and token management.
"""

from django.urls import path
from accounts import api_views

urlpatterns = [
    path('register/', api_views.register_user, name='api_register'),
    path('token/refresh/', api_views.refresh_token, name='api_token_refresh'),
    path('token/revoke/', api_views.revoke_token, name='api_token_revoke'),
]
