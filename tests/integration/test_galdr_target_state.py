"""Integration tests for Galdr v2 target-state holistic assessment."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from methodology.models import Activity, PipChange, Playbook, ProcessImprovementProposal, Workflow
from methodology.services.pip_service import PIPService

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="galdr_v2", password="pw")


@pytest.fixture
def playbook_bundle(db, alice):
    pb = Playbook.objects.create(
        name="EKS Deploy PB",
        description="desc",
        category="development",
        author=alice,
        status="released",
        version=Decimal("1.0"),
    )
    wf = Workflow.objects.create(
        playbook=pb,
        name="Deploy Compute",
        description="EKS-only deployment workflow",
        order=1,
    )
    act74 = Activity.objects.create(
        workflow=wf, name="Choose deployment style", guidance="EKS path", order=1,
    )
    act77 = Activity.objects.create(
        workflow=wf, name="Build EKS Stack", guidance="EKS stack", order=2,
    )
    act82 = Activity.objects.create(
        workflow=wf, name="Create Helm Chart", guidance="Helm values", order=3,
    )
    return pb, wf, act74, act77, act82


@pytest.mark.django_db
def test_galdr_holistic_accepts_interdependent_changes(alice, playbook_bundle):
    """
    Regression for issue #129: ADD skill + LINK after ALTERs that make playbook
    deployment-style-agnostic should all ACCEPT under target-state evaluation.
    """
    pb, _wf, act74, act77, act82 = playbook_bundle
    pip = PIPService.create_draft_for_playbook(
        actor=alice,
        playbook_id=pb.pk,
        title="Deployment agnostic PIP",
        summary="Support EKS and EB",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act74.pk,
        content="Choose EKS or Elastic Beanstalk deployment style.",
        name="",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act77.pk,
        content="Fork guidance for EKS vs EB compute stack.",
        name="Build Compute & Container Registry Stack",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act82.pk,
        content="Fork Helm vs EB docker-compose manifest guidance.",
        name="Create Deployment Manifest",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL,
        name="AWS EB Blue/Green Deployment",
        content="Elastic Beanstalk blue/green patterns.",
        internal_ref="#eb-skill",
    )
    for act in (act77, act82):
        PIPService.add_change(
            actor=alice,
            pip=pip,
            change_type=PipChange.CHANGE_LINK,
            relationship_type=PipChange.REL_SKILL_ACTIVITY,
            source_entity_ref="#eb-skill",
            target_entity_ref=str(act.pk),
            content=f"Link EB skill to activity {act.pk}",
        )

    PIPService.submit_for_review(actor=alice, pip=pip)
    pip.refresh_from_db()

    assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED
    assert "COHERENT" in pip.galdr_holistic_assessment
    changes = list(pip.changes.order_by("order", "pk"))
    assert len(changes) == 6
    for ch in changes:
        assert ch.galdr_recommendation == PipChange.GALDR_ACCEPT, (
            f"Change {ch.pk} expected ACCEPT, got {ch.galdr_recommendation}"
        )
