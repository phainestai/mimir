"""S03-S05 playbook release flows (VERSIONING-07 / 20 / 21)."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import Playbook, PlaybookVersion, Workflow

User = get_user_model()


@pytest.fixture
def release_owner(db):
    return User.objects.create_user(username="rel_owner", password="pwrel")


@pytest.fixture
def release_client(db, release_owner):
    client = Client()
    client.force_login(release_owner)
    return client


@pytest.fixture
def draft_pb_before_first_major(release_owner):
    """Draft at 0.8 + default workflow bump → 0.9; first release lands at v1.0."""
    pb = Playbook.objects.create(
        name="Rel Draft PB",
        description="desc " * 5,
        category="product",
        status="draft",
        version=Decimal("0.8"),
        author=release_owner,
    )
    Workflow.objects.create(
        playbook=pb,
        name="Workflow One",
        description="w",
        order=1,
    )
    pb.refresh_from_db()
    assert pb.version == Decimal("0.9")
    return pb


@pytest.fixture
def released_pb_13(release_owner):
    pb = Playbook.objects.create(
        name="Rel Released PB",
        description="desc " * 5,
        category="product",
        status="released",
        version=Decimal("1.3"),
        author=release_owner,
    )
    Workflow.objects.create(
        playbook=pb,
        name="Workflow R",
        description="w",
        order=1,
    )
    return pb


@pytest.mark.django_db
def test_release_creates_major_version_with_description(release_client, draft_pb_before_first_major):
    url = reverse("playbook_release", kwargs={"pk": draft_pb_before_first_major.pk})
    response = release_client.post(
        url, {"release_description": "Initial GA release"}, follow=True
    )
    assert response.status_code == 200
    draft_pb_before_first_major.refresh_from_db()
    assert draft_pb_before_first_major.status == "released"
    assert draft_pb_before_first_major.version == Decimal("1.0")
    pv = PlaybookVersion.objects.get(
        playbook=draft_pb_before_first_major, version_number=Decimal("1.0")
    )
    assert pv.description == "Initial GA release"
    assert pv.change_summary == "Initial GA release"
    assert pv.is_major is True


@pytest.mark.django_db
def test_release_without_description_blocked(release_client, draft_pb_before_first_major):
    url = reverse("playbook_release", kwargs={"pk": draft_pb_before_first_major.pk})
    response = release_client.post(
        url,
        {"release_description": ""},
        follow=True,
    )
    assert response.status_code == 200
    msgs = [m.message for m in response.context["messages"]]
    assert any("release description is required" in str(m).lower() for m in msgs)
    draft_pb_before_first_major.refresh_from_db()
    assert draft_pb_before_first_major.status == "draft"


@pytest.mark.django_db
def test_release_whitespace_description_blocked(release_client, draft_pb_before_first_major):
    url = reverse("playbook_release", kwargs={"pk": draft_pb_before_first_major.pk})
    response = release_client.post(url, {"release_description": "  \t  "}, follow=True)
    msgs = [m.message for m in response.context["messages"]]
    assert any("release description is required" in str(m).lower() for m in msgs)


@pytest.mark.django_db
def test_re_release_bumps_next_major(release_client, released_pb_13):
    url = reverse("playbook_release", kwargs={"pk": released_pb_13.pk})
    response = release_client.post(
        url, {"release_description": "Minor line capped; next major milestone"}, follow=True
    )
    assert response.status_code == 200
    released_pb_13.refresh_from_db()
    assert released_pb_13.status == "released"
    assert released_pb_13.version == Decimal("2.0")
    assert PlaybookVersion.objects.filter(
        playbook=released_pb_13, version_number=Decimal("2.0")
    ).exists()
