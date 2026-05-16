"""S06–S08 PIP apply: single aggregated minor bump per approved PIP."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from methodology.models import Activity, Playbook, PlaybookVersion, ProcessImprovementProposal, Workflow
from methodology.models.playbook_version import VersionSource
from methodology.services.pip_apply_service import apply_approved_pip_aggregate

User = get_user_model()


@pytest.fixture
def pip_owner(db):
    return User.objects.create_user(username="pip_owner", password="pwPIP")


@pytest.fixture
def released_with_activities(db, pip_owner):
    pb = Playbook.objects.create(
        name="PIP Target PB",
        description="desc " * 8,
        category="product",
        status="released",
        version=Decimal("1.0"),
        author=pip_owner,
    )
    wf = Workflow.objects.create(
        playbook=pb,
        name="Workflow PIP",
        description="w",
        order=1,
    )
    a1 = Activity.objects.create(
        workflow=wf,
        name="Activity A",
        guidance="guide A body text here",
        order=1,
    )
    a2 = Activity.objects.create(
        workflow=wf,
        name="Activity B",
        guidance="guide B body text here",
        order=2,
    )
    return pb, wf, a1, a2


@pytest.mark.django_db
def test_pip_with_n_changes_produces_single_minor_bump(pip_owner, released_with_activities):
    pb, _wf, a1, a2 = released_with_activities
    pip = ProcessImprovementProposal.objects.create(
        playbook=pb,
        title="Batch rename",
        status=ProcessImprovementProposal.STATUS_ACCEPTED,
        created_by=pip_owner,
    )

    def mutations():
        a1.name = "Activity A prime"
        a1.save()
        a2.name = "Activity B prime"
        a2.save()

    apply_approved_pip_aggregate(
        pip=pip,
        actor=pip_owner,
        aggregated_description="Two activity renames in one PIP",
        apply_mutations=mutations,
    )

    pb.refresh_from_db()
    assert pb.status == "released"
    assert pb.version == Decimal("1.1")

    rows = PlaybookVersion.objects.filter(playbook=pb, version_number=Decimal("1.1"))
    assert rows.count() == 1
    row = rows.get()
    assert row.source == VersionSource.PIP_SOURCE
    assert row.pip_id == pip.pk
    assert row.is_major is False

    pip.refresh_from_db()
    assert pip.status == ProcessImprovementProposal.STATUS_ACCEPTED


@pytest.mark.django_db
def test_sequential_pips_increment_minor(pip_owner, released_with_activities):
    pb, _wf, a1, _a2 = released_with_activities

    for i, expected in enumerate(
        [Decimal("1.1"), Decimal("1.2"), Decimal("1.3")], start=1
    ):
        pip = ProcessImprovementProposal.objects.create(
            playbook=pb,
            title=f"Sequential {i}",
            status=ProcessImprovementProposal.STATUS_ACCEPTED,
            created_by=pip_owner,
        )

        def make_mut(n=i):
            def _inner():
                a1.guidance = f"Updated guidance wave {n}"
                a1.save()

            return _inner

        apply_approved_pip_aggregate(
            pip=pip,
            actor=pip_owner,
            aggregated_description=f"PIP wave {i}",
            apply_mutations=make_mut(),
        )
        pb.refresh_from_db()
        assert pb.version == expected
        assert pb.status == "released"


@pytest.mark.django_db
def test_pip_manage_05_minor_bump_contract(pip_owner, released_with_activities):
    """Released playbook stays released; major line is unchanged (1.x); history links PIP."""
    pb, _wf, a1, _a2 = released_with_activities
    pip = ProcessImprovementProposal.objects.create(
        playbook=pb,
        title="Manage flow PIP",
        status=ProcessImprovementProposal.STATUS_ACCEPTED,
        created_by=pip_owner,
    )

    def mutations():
        a1.name = "Contract check name"
        a1.save()

    apply_approved_pip_aggregate(
        pip=pip,
        actor=pip_owner,
        aggregated_description="PIP-MANAGE-05 single minor",
        apply_mutations=mutations,
    )

    pb.refresh_from_db()
    assert pb.status == "released"
    assert pb.version == Decimal("1.1")
    assert int(pb.version) == 1

    v = PlaybookVersion.objects.get(playbook=pb, version_number=Decimal("1.1"))
    assert v.pip_id == pip.pk
    assert v.is_major is False
