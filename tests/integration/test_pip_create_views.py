"""PIP create view (prefill from playbook detail — FOB-PIP-CREATE-01)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook, ProcessImprovementProposal

User = get_user_model()


@pytest.fixture
def maria(db):
    return User.objects.create_user(username="maria_create_pip", password="pwCREATE")


@pytest.fixture
def released_pb(db, maria):
    return Playbook.objects.create(
        name="Released PB Create",
        description="d" * 30,
        category="development",
        author=maria,
        status="released",
        version=Decimal("1.0"),
    )


@pytest.mark.django_db
def test_pip_create_prefill_locks_playbook_dropdown(maria, released_pb):
    """Opening create with ?playbook= locks selector and submits target via hidden input."""
    client = Client()
    client.force_login(maria)
    url = f"{reverse('pip_create')}?playbook={released_pb.pk}"
    rsp = client.get(url)
    assert rsp.status_code == 200
    body = rsp.content.decode()
    assert 'data-testid="pip-create-playbook-hidden"' in body
    assert 'input type="hidden" name="playbook"' in body
    assert 'opened this form from the playbook' in body
    assert '<select class="form-select" id="id_playbook" disabled' in body


@pytest.mark.django_db
def test_pip_create_prefill_post_creates_draft(maria, released_pb):
    client = Client(enforce_csrf_checks=False)
    client.force_login(maria)
    url = f"{reverse('pip_create')}?playbook={released_pb.pk}"
    rsp = client.post(
        url,
        {"playbook": str(released_pb.pk), "title": "From playbook flow", "summary": ""},
    )
    assert rsp.status_code == 302
    assert "/edit/" in rsp.url
    pip = ProcessImprovementProposal.objects.get(title="From playbook flow")
    assert pip.playbook_id == released_pb.pk

