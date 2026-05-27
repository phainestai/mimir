"""Integration tests for PIP ADD/ALTER/DROP across all entity types and #ref subtrees."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from methodology.models import (
    Activity,
    Artifact,
    ArtifactInput,
    Phase,
    PipChange,
    Playbook,
    ProcessImprovementProposal,
    Rule,
    Skill,
    Workflow,
)
from methodology.services.pip_admin_service import PIPAdminService
from methodology.services.pip_service import PIPService

User = get_user_model()


@pytest.fixture
def alice(db):
    return User.objects.create_user(username="alice_entity", password="pw", email="alice@entity.test")


@pytest.fixture
def staff_bob(db):
    u = User.objects.create_user(username="bob_entity", password="pw", email="bob@entity.test")
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def playbook_bundle(db, alice):
    pb = Playbook.objects.create(
        name="Entity CRUD PB",
        description="desc",
        category="development",
        author=alice,
        status="released",
        version=Decimal("1.0"),
    )
    wf = Workflow.objects.create(playbook=pb, name="Main WF", description="w", order=1)
    act = Activity.objects.create(workflow=wf, name="Existing Activity", guidance="body", order=1)
    rule = Rule.objects.create(
        playbook=pb, title="Existing Rule", slug="existing-rule", content="rule body",
    )
    return pb, wf, act, rule


def _finalize_all_accept(pip, alice, staff):
    PIPService.submit_for_review(actor=alice, pip=pip)
    pip.refresh_from_db()
    assert pip.status == ProcessImprovementProposal.STATUS_REVIEWED
    for ch in pip.changes.all():
        ch.galdr_recommendation = PipChange.GALDR_ACCEPT
        ch.admin_decision = PipChange.ADMIN_ACCEPT
        ch.save(update_fields=["galdr_recommendation", "admin_decision", "updated_at"])
    PIPAdminService.finalize_pip(pip, staff)


@pytest.mark.django_db
def test_add_activity_rejects_missing_parent(alice, playbook_bundle):
    pb, _wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="No parent")
    with pytest.raises(Exception, match="parent_workflow"):
        PIPService.add_change(
            actor=alice,
            pip=pip,
            change_type=PipChange.CHANGE_ADD,
            entity_type=PipChange.ENTITY_ACTIVITY,
            name="Orphan",
            content="guidance",
        )


@pytest.mark.django_db
def test_add_activity_accepts_parent_workflow_ref(alice, playbook_bundle):
    pb, _wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Ref parent")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW, name="New WF", content="wf desc",
        internal_ref="#new-wf",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Child Act", content="act body",
        parent_workflow_ref="#new-wf", internal_ref="#act1",
    )
    ch = pip.changes.order_by("order").last()
    assert ch.parent_workflow_ref == "#new-wf"


@pytest.mark.django_db
def test_add_artifact_requires_producer_ref(alice, playbook_bundle):
    pb, _wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Art")
    with pytest.raises(Exception, match="produced_by_activity_ref"):
        PIPService.add_change(
            actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
            entity_type=PipChange.ENTITY_ARTIFACT, name="Spec", content="desc",
        )


@pytest.mark.django_db
def test_mutual_exclusion_parent_fk_and_ref(alice, playbook_bundle):
    pb, wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Both")
    with pytest.raises(Exception, match="not both"):
        PIPService.add_change(
            actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
            entity_type=PipChange.ENTITY_ACTIVITY, name="X", content="y",
            parent_workflow_id=wf.pk, parent_workflow_ref="#new-wf",
        )


@pytest.mark.django_db
def test_add_workflow_then_activity_via_parent_ref(alice, staff_bob, playbook_bundle):
    pb, _wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Subtree")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW, name="Performance", content="perf wf",
        internal_ref="#new-wf",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Step One", content="step 1",
        parent_workflow_ref="#new-wf", internal_ref="#act1",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    wf = Workflow.objects.get(playbook=pb, name="Performance")
    assert wf.activities.filter(name="Step One").exists()
    pb.refresh_from_db()
    assert pb.version == Decimal("2.0")


@pytest.mark.django_db
def test_three_activities_ordered_via_refs(alice, staff_bob, playbook_bundle):
    pb, _wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Ordered")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW, name="Ordered WF", content="",
        internal_ref="#owf",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="A1", content="a1",
        parent_workflow_ref="#owf", internal_ref="#a1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="A2", content="a2",
        parent_workflow_ref="#owf", insert_after_activity_ref="#a1", internal_ref="#a2",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="A3", content="a3",
        parent_workflow_ref="#owf", insert_after_activity_ref="#a2",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    wf = Workflow.objects.get(playbook=pb, name="Ordered WF")
    orders = list(wf.activities.order_by("order").values_list("name", "order"))
    assert orders == [("A1", 1), ("A2", 2), ("A3", 3)]


@pytest.mark.django_db
def test_add_phase_then_activity_with_phase_ref(alice, staff_bob, playbook_bundle):
    pb, wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Phase")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_PHASE, name="Construction", content="build phase",
        internal_ref="#phase1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Build Step", content="build",
        parent_workflow_id=wf.pk, phase_ref="#phase1",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    act = Activity.objects.get(workflow=wf, name="Build Step")
    assert act.phase is not None
    assert act.phase.name == "Construction"


@pytest.mark.django_db
def test_link_artifact_to_pending_activity(alice, staff_bob, playbook_bundle):
    pb, wf, _act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Art link")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Producer", content="prod",
        parent_workflow_id=wf.pk, internal_ref="#act-prod",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Consumer", content="cons",
        parent_workflow_id=wf.pk, internal_ref="#act-cons",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ARTIFACT, name="Deliverable", content="del",
        produced_by_activity_ref="#act-prod", internal_ref="#art1",
        artifact_type="Document",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_ARTIFACT_ACTIVITY,
        source_entity_ref="#art1", target_entity_ref="#act-cons",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    art = Artifact.objects.get(playbook=pb, name="Deliverable")
    consumer = Activity.objects.get(workflow=wf, name="Consumer")
    assert ArtifactInput.objects.filter(artifact=art, activity=consumer).exists()


@pytest.mark.django_db
def test_alter_and_drop_rule_via_pip(alice, staff_bob, playbook_bundle):
    pb, _wf, _act, rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Rule ops")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_RULE, target_id=rule.pk,
        content="updated rule content",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    rule.refresh_from_db()
    assert "updated rule content" in rule.content

    pip2 = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Drop rule")
    PIPService.add_change(
        actor=alice, pip=pip2, change_type=PipChange.CHANGE_DROP,
        entity_type=PipChange.ENTITY_RULE, target_id=rule.pk,
        content="obsolete",
    )
    _finalize_all_accept(pip2, alice, staff_bob)
    assert not Rule.objects.filter(pk=rule.pk).exists()


@pytest.mark.django_db
def test_alter_and_drop_phase_via_pip(alice, staff_bob, playbook_bundle):
    pb, wf, _act, _rule = playbook_bundle
    phase = Phase.objects.create(playbook=pb, name="Old Phase", description="old", order=1)
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Phase alter")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_PHASE, target_id=phase.pk,
        name="New Phase Name", content="new desc",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    phase.refresh_from_db()
    assert phase.name == "New Phase Name"

    pip2 = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Drop phase")
    PIPService.add_change(
        actor=alice, pip=pip2, change_type=PipChange.CHANGE_DROP,
        entity_type=PipChange.ENTITY_PHASE, target_id=phase.pk,
        content="unused",
    )
    _finalize_all_accept(pip2, alice, staff_bob)
    assert not Phase.objects.filter(pk=phase.pk).exists()


@pytest.mark.django_db
def test_full_subtree_all_entities_and_links(alice, staff_bob, playbook_bundle):
    pb, _wf, existing_act, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Full tree")
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_PHASE, name="Delivery", content="",
        internal_ref="#ph1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_WORKFLOW, name="New Delivery WF", content="",
        internal_ref="#wf1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_ACTIVITY, name="Act One", content="a1",
        parent_workflow_ref="#wf1", phase_ref="#ph1", internal_ref="#act1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL, name="Skill One", content="sk",
        internal_ref="#sk1",
    )
    PIPService.add_change(
        actor=alice, pip=pip, change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref="#sk1", target_entity_ref="#act1",
    )
    _finalize_all_accept(pip, alice, staff_bob)
    wf = Workflow.objects.get(playbook=pb, name="New Delivery WF")
    act = Activity.objects.get(workflow=wf, name="Act One")
    assert act.phase.name == "Delivery"
    assert act.skills.filter(title="Skill One").exists()
