"""Legacy / anonymous expectations for ``/pip/`` URLs."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_legacy_pip_list_path_redirects_to_real_list(client):
    """GET /pip/list/ redirects to ``pip_list`` (Act 9 real implementation)."""

    response = client.get("/pip/list/", follow=False)
    assert response.status_code == 302
    assert reverse("pip_list") in response["Location"]


@pytest.mark.django_db
def test_pip_list_requires_login(client):
    """GET /pips/ for anonymous sends user to LOGIN_URL with next."""

    rsp = client.get(reverse("pip_list"))
    assert rsp.status_code == 302
    assert "login" in rsp["Location"].lower()
