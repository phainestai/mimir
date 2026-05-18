from django.urls import path
from . import views

urlpatterns = [
    # ── Auth flow ──────────────────────────────────────────────────────────
    path("auth/register/", views.auth_register, name="mockup_auth_register"),
    path("auth/login/", views.auth_login, name="mockup_auth_login"),
    # ── Profile ───────────────────────────────────────────────────────────
    path("profile/", views.profile_view, name="mockup_profile"),
    path("profile/edit/", views.profile_edit, name="mockup_profile_edit"),
    # ── PIPs ──────────────────────────────────────────────────────────────
    path("pips/", views.pip_list, name="mockup_pip_list"),
    path("pips/create/", views.pip_create, name="mockup_pip_create"),
    path("pips/<int:pip_id>/", views.pip_detail, name="mockup_pip_detail"),
    path("pips/<int:pip_id>/admin-review/", views.pip_admin_review, name="mockup_pip_admin_review"),
]
