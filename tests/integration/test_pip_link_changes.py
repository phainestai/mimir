"""Integration tests for PIP LINK / UNLINK change types."""

from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from methodology.models import (
    Activity,
    ActivityWorkflowMembership,
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
    return User.objects.create_user(username="alice_link", password="pw", email="alice@link.test")


@pytest.fixture
def staff_bob(db):
    u = User.objects.create_user(username="bob_link", password="pw", email="bob@link.test")
    u.is_staff = True
    u.save(update_fields=["is_staff"])
    return u


@pytest.fixture
def playbook_bundle(db, alice):
    pb = Playbook.objects.create(
        name="Link PB",
        description="desc",
        category="development",
        author=alice,
        status="released",
        version=Decimal("1.0"),
    )
    wf1 = Workflow.objects.create(playbook=pb, name="Primary WF", description="w1", order=1)
    wf2 = Workflow.objects.create(playbook=pb, name="Secondary WF", description="w2", order=2)
    act = Activity.objects.create(workflow=wf1, name="Target Activity", guidance="body", order=1)
    skill = Skill.objects.create(playbook=pb, title="Existing Skill", content="skill body")
    rule = Rule.objects.create(playbook=pb, title="Lint Rule", slug="lint-rule", content="rule body")
    return pb, wf1, wf2, act, skill, rule


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
def test_link_skill_to_activity_via_pip(alice, staff_bob, playbook_bundle):
    pb, _wf1, _wf2, act, skill, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Link skill")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref=str(skill.pk),
        target_entity_ref=str(act.pk),
        content="Skill supports this activity",
    )
    assert not act.skills.filter(pk=skill.pk).exists()
    _finalize_all_accept(pip, alice, staff_bob)
    act.refresh_from_db()
    pb.refresh_from_db()
    assert act.skills.filter(pk=skill.pk).exists()
    assert pb.version == Decimal("2.0")


@pytest.mark.django_db
def test_unlink_skill_from_activity_via_pip(alice, staff_bob, playbook_bundle):
    pb, _wf1, _wf2, act, skill, _rule = playbook_bundle
    act.skills.add(skill)
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Unlink skill")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_UNLINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref=str(skill.pk),
        target_entity_ref=str(act.pk),
    )
    _finalize_all_accept(pip, alice, staff_bob)
    act.refresh_from_db()
    assert not act.skills.filter(pk=skill.pk).exists()


@pytest.mark.django_db
def test_link_activity_to_secondary_workflow(alice, staff_bob, playbook_bundle):
    pb, wf1, wf2, act, _skill, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Cross-list")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_ACTIVITY_WORKFLOW,
        source_entity_ref=str(act.pk),
        target_entity_ref=str(wf2.pk),
    )
    _finalize_all_accept(pip, alice, staff_bob)
    assert ActivityWorkflowMembership.objects.filter(activity=act, workflow=wf2).exists()
    assert act.workflow_id == wf1.pk


@pytest.mark.django_db
def test_add_skill_then_link_via_internal_ref(alice, staff_bob, playbook_bundle):
    pb, _wf1, _wf2, act, _skill, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="ADD+LINK")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ADD,
        entity_type=PipChange.ENTITY_SKILL,
        name="CDK Deployment",
        content="Deploy with CDK",
        internal_ref="#cdk-skill",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref="#cdk-skill",
        target_entity_ref=str(act.pk),
    )
    _finalize_all_accept(pip, alice, staff_bob)
    act.refresh_from_db()
    assert act.skills.filter(title="CDK Deployment").exists()


@pytest.mark.django_db
def test_duplicate_link_rejected_at_persist(alice, playbook_bundle):
    pb, _wf1, _wf2, act, skill, _rule = playbook_bundle
    act.skills.add(skill)
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Dup link")
    with pytest.raises(ValidationError, match="already exists"):
        PIPService.add_change(
            actor=alice,
            pip=pip,
            change_type=PipChange.CHANGE_LINK,
            relationship_type=PipChange.REL_SKILL_ACTIVITY,
            source_entity_ref=str(skill.pk),
            target_entity_ref=str(act.pk),
        )
    

@pytest.mark.django_db
def test_preview_includes_links_section(alice, playbook_bundle):
    pb, _wf1, _wf2, act, skill, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Preview")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref=str(skill.pk),
        target_entity_ref=str(act.pk),
    )
    rows = PIPService.summarize_preview_rows(pip)
    assert any(r["section"] == "Links Added" for r in rows)


@pytest.mark.django_db
def test_mix_add_and_link_single_major_bump(alice, staff_bob, playbook_bundle):
    pb, _wf1, _wf2, act, skill, _rule = playbook_bundle
    pip = PIPService.create_draft_for_playbook(actor=alice, playbook_id=pb.pk, title="Mix")
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_ALTER,
        entity_type=PipChange.ENTITY_ACTIVITY,
        target_id=act.pk,
        content="Updated guidance",
    )
    PIPService.add_change(
        actor=alice,
        pip=pip,
        change_type=PipChange.CHANGE_LINK,
        relationship_type=PipChange.REL_SKILL_ACTIVITY,
        source_entity_ref=str(skill.pk),
        target_entity_ref=str(act.pk),
    )
    _finalize_all_accept(pip, alice, staff_bob)
    pb.refresh_from_db()
    assert pb.version == Decimal("2.0")
