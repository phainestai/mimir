"""URL configuration for accounts app."""
from django.urls import path
from .views import (
    login_view, 
    custom_logout_view, 
    profile_view,
    profile_edit_view,
    profile_regenerate_token,
    onboarding, 
    register,
    password_reset_request,
    password_reset_confirm,
    skip_onboarding,
)

# URL convention: /auth/user/{action}/
urlpatterns = [
    path('user/login/', login_view, name='login'),
    path('user/logout/', custom_logout_view, name='logout'),
    path('user/register/', register, name='register'),
    path('user/profile/', profile_view, name='profile'),
    path('user/profile/edit/', profile_edit_view, name='profile_edit'),
    path(
        'user/profile/regenerate-token/',
        profile_regenerate_token,
        name='profile_regenerate_token',
    ),
    path('user/onboarding/', onboarding, name='onboarding'),
    path('user/onboarding/skip/', skip_onboarding, name='onboarding_skip'),
    path('user/password-reset/', password_reset_request, name='password_reset'),
    path('user/password-reset-confirm/<uidb64>/<token>/', password_reset_confirm, name='password_reset_confirm'),
]
