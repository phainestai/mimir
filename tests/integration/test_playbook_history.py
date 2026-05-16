"""S11–S15 playbook version history UI and snapshots."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from methodology.models import (
    Playbook,
    PlaybookVersion,
    ProcessImprovementProposal,
    VersionSource,
)

User = get_user_model()


@pytest.fixture
def hist_user(db):
    return User.objects.create_user(username="hist_u", password="pwh")


@pytest.fixture
def playbook_with_history(db, hist_user):
    pb = Playbook.objects.create(
        name="History PB",
        description="desc " * 30,
        category="product",
        status="released",
        version=Decimal("2.1"),
        author=hist_user,
    )
    PlaybookVersion.objects.create(
        playbook=pb,
        version_number=Decimal("2.0"),
        snapshot_data={"phase": "2.0"},
        change_summary="Major 2 line",
        description="Major two",
        is_major=True,
        source=VersionSource.RELEASE,
        created_by=hist_user,
    )
    pip = ProcessImprovementProposal.objects.create(
        playbook=pb,
        title="Adjust minor",
        status=ProcessImprovementProposal.STATUS_ACCEPTED,
        created_by=hist_user,
    )
    PlaybookVersion.objects.create(
        playbook=pb,
        version_number=Decimal("2.1"),
        snapshot_data={"phase": "2.1"},
        change_summary="PIP minor aggregation",
        description="PIP minor aggregation",
        is_major=False,
        source=VersionSource.PIP_SOURCE,
        pip=pip,
        created_by=hist_user,
    )
    return pb


@pytest.mark.django_db
def test_history_listing_endpoint(hist_user, playbook_with_history):
    client = Client()
    client.force_login(hist_user)
    url = reverse("playbook_detail", kwargs={"pk": playbook_with_history.pk})
    rsp = client.get(url)
    assert rsp.status_code == 200
    assert b'history-versions-table' in rsp.content
    assert b'history-version-row' in rsp.content


@pytest.mark.django_db
def test_major_minor_visual_distinction(hist_user, playbook_with_history):
    client = Client()
    client.force_login(hist_user)
    rsp = client.get(
        reverse("playbook_detail", kwargs={"pk": playbook_with_history.pk})
    )
    body = rsp.content.decode()
    assert 'bg-primary' in body or "major" in body
    assert "minor" in body


@pytest.mark.django_db
def test_view_historical_version(hist_user, playbook_with_history):
    client = Client()
    client.force_login(hist_user)
    url = reverse(
        "playbook_version_snapshot",
        kwargs={
            "pk": playbook_with_history.pk,
            "version_slug": "2_1",
        },
    )
    rsp = client.get(url)
    assert rsp.status_code == 200
    assert b"history-snapshot-json" in rsp.content
    assert b"phase" in rsp.content and b"2.1" in rsp.content


@pytest.mark.django_db
def test_compare_versions_split_pane(hist_user, playbook_with_history):
    client = Client()
    client.force_login(hist_user)
    url = (
        reverse(
            "playbook_versions_compare",
            kwargs={"pk": playbook_with_history.pk},
        )
        + "?left=2_0&right=2_1"
    )
    rsp = client.get(url)
    assert rsp.status_code == 200
    assert b"history-split-compare" in rsp.content
    assert b"history-compare-pane-left" in rsp.content
    assert b"history-compare-pane-right" in rsp.content


@pytest.mark.django_db
def test_pip_sourced_rows_link_to_pip(hist_user, playbook_with_history):
    client = Client()
    client.force_login(hist_user)
    rsp = client.get(
        reverse("playbook_detail", kwargs={"pk": playbook_with_history.pk})
    )
    assert b'data-testid="history-pip-link"' in rsp.content
    assert b"data-pip-id" in rsp.content
