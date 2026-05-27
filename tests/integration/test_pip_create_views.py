"""PIP create view (prefill from playbook detail — FOB-PIP-CREATE-01)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Activity, PipChange, Playbook, ProcessImprovementProposal, Workflow
from methodology.services.pip_service import PIPService

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


@pytest.mark.django_db
def test_pip_create_workflow_prefill_shows_hidden_focus_field(maria, released_pb):
    wf = Workflow.objects.create(name="Scoped WF", playbook=released_pb, order=1)
    client = Client()
    client.force_login(maria)
    url = f"{reverse('pip_create')}?playbook={released_pb.pk}&workflow={wf.pk}"
    rsp = client.get(url)
    assert rsp.status_code == 200
    body = rsp.content.decode()
    assert 'data-testid="pip-create-focus-workflow"' in body
    assert "Workflow context:" in body
    assert str(wf.pk) in body


@pytest.mark.django_db
def test_pip_create_activity_prefill_adds_hidden_fields(maria, released_pb):
    wf = Workflow.objects.create(name="W2", playbook=released_pb, order=1)
    act = Activity.objects.create(
        workflow=wf, name="Act A", guidance="g" * 20, order=1
    )
    client = Client()
    client.force_login(maria)
    url = (
        f"{reverse('pip_create')}?playbook={released_pb.pk}"
        f"&workflow={wf.pk}&activity={act.pk}"
    )
    rsp = client.get(url)
    assert rsp.status_code == 200
    body = rsp.content.decode()
    assert 'data-testid="pip-create-focus-activity"' in body
    assert "Activity context:" in body


@pytest.mark.django_db
def test_pip_add_change_accepts_parent_workflow_ref_via_gui(maria, released_pb):
    """Draft editor POST can chain ADD Workflow → ADD Activity via #refs."""
    pip = PIPService.create_draft_for_playbook(
        actor=maria, playbook_id=released_pb.pk, title="GUI ref subtree",
    )
    client = Client(enforce_csrf_checks=False)
    client.force_login(maria)
    add_url = reverse("pip_add_change", kwargs={"pk": pip.pk})

    rsp_wf = client.post(
        add_url,
        {
            "change_type": "ADD",
            "entity_type": "Workflow",
            "name": "New WF",
            "content": "Workflow body",
            "internal_ref": "#wf1",
        },
    )
    assert rsp_wf.status_code == 302

    rsp_act = client.post(
        add_url,
        {
            "change_type": "ADD",
            "entity_type": "Activity",
            "name": "First step",
            "content": "Activity guidance text",
            "parent_workflow_ref": "#wf1",
            "internal_ref": "#act1",
        },
    )
    assert rsp_act.status_code == 302

    wf_change = PipChange.objects.get(pip=pip, internal_ref="#wf1")
    act_change = PipChange.objects.get(pip=pip, internal_ref="#act1")
    assert wf_change.entity_type == PipChange.ENTITY_WORKFLOW
    assert act_change.parent_workflow_ref == "#wf1"
    assert act_change.parent_workflow_id is None

