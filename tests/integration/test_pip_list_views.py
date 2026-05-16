"""Integration tests for PIP list (FOB-PIP-LIST subset, slice 1)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import (
    PipChange,
    Playbook,
    ProcessImprovementProposal,
    UserPIPListVisit,
)

User = get_user_model()


@pytest.fixture
def maria(db):
    return User.objects.create_user(username="maria_list", password="pwLIST")


@pytest.fixture
def alex(db):
    return User.objects.create_user(username="alex_list", password="pwLIST")


@pytest.fixture
def staff_mike(db):
    u = User.objects.create_user(username="mike_staff", password="pwLIST")
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def released_pb(db, maria):
    return Playbook.objects.create(
        name="Released PB",
        description="d" * 30,
        category="development",
        author=maria,
        status="released",
        version=Decimal("1.0"),
    )


@pytest.mark.django_db
def test_pip_list_login_required(db):
    client = Client()
    rsp = client.get(reverse("pip_list"))
    assert rsp.status_code == 302


@pytest.mark.django_db
def test_pip_list_empty_state(maria, client):
    client.force_login(maria)
    rsp = client.get(reverse("pip_list"))
    assert rsp.status_code == 200
    assert b"pip-empty-state" in rsp.content


@pytest.mark.django_db
def test_pip_list_shows_row_with_id(maria, released_pb, client):
    pip = ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Example",
        status=ProcessImprovementProposal.STATUS_DRAFT,
        created_by=maria,
    )
    client.force_login(maria)
    rsp = client.get(reverse("pip_list"))
    assert rsp.status_code == 200
    blob = rsp.content.decode()
    assert f'pip-row-{pip.pk}' in blob
    assert f"PIP-{pip.pk}" in blob


@pytest.mark.django_db
def test_staff_sees_all_pips_tab_and_rows(maria, alex, staff_mike, released_pb, client):
    ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Maria PIP",
        status=ProcessImprovementProposal.STATUS_DRAFT,
        created_by=maria,
    )
    ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Alex PIP",
        status=ProcessImprovementProposal.STATUS_REVIEWED,
        created_by=alex,
    )
    client.force_login(staff_mike)
    rsp = client.get(reverse("pip_list"), {"scope": "all"})
    assert rsp.status_code == 200
    assert b'tab-all-pips' in rsp.content
    body = rsp.content.decode()
    assert "Maria PIP" in body and "Alex PIP" in body


@pytest.mark.django_db
def test_non_staff_blocked_from_all_scope(maria, alex, released_pb, client):
    ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Alex only",
        status=ProcessImprovementProposal.STATUS_SUBMITTED,
        created_by=alex,
    )
    client.force_login(maria)
    rsp = client.get(reverse("pip_list"), {"scope": "all"})
    txt = rsp.content.decode()
    assert "permission" in txt.lower()
    assert "Alex only" not in txt


@pytest.mark.django_db
def test_change_count_in_table(maria, released_pb, client):
    pip = ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Two changes",
        status=ProcessImprovementProposal.STATUS_DRAFT,
        created_by=maria,
    )
    PipChange.objects.create(
        pip=pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY,
        order=1,
        name="One",
    )
    PipChange.objects.create(
        pip=pip,
        change_type=PipChange.CHANGE_DROP,
        entity_type=PipChange.ENTITY_SKILL,
        order=2,
        name="",
    )
    client.force_login(maria)
    rsp = client.get(reverse("pip_list"))
    assert rsp.status_code == 200
    assert b">2</td>" in rsp.content


@pytest.mark.django_db
def test_nav_unread_after_status_change_since_visit(maria, released_pb, client):
    pip = ProcessImprovementProposal.objects.create(
        playbook=released_pb,
        title="Unread badge",
        status=ProcessImprovementProposal.STATUS_DRAFT,
        created_by=maria,
    )
    client.force_login(maria)
    client.get(reverse("pip_list"))
    visit = UserPIPListVisit.objects.get(user=maria)
    visit.last_visited_at = pip.created_at
    visit.save(update_fields=["last_visited_at"])

    pip.status = ProcessImprovementProposal.STATUS_SUBMITTED
    pip.save()

    rsp = client.get(reverse("dashboard"))
    assert rsp.status_code == 200
    assert b"nav-pips-count" in rsp.content


@pytest.mark.django_db
def test_legacy_pip_list_redirects(db):
    client = Client()
    rsp = client.get("/pip/list/", follow=False)
    assert rsp.status_code == 302
    assert rsp.url.endswith(reverse("pip_list"))
