"""
Unit tests for Activity link/unlink service methods (skill + agent).

Tests ActivityService.set/clear_activity_skill and set/clear_activity_agent,
plus SkillService and AgentService facade methods.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from methodology.models import Playbook, Workflow, Activity, Skill, Agent
from methodology.services.activity_service import ActivityService
from methodology.services.skill_service import SkillService
from methodology.services.agent_service import AgentService

User = get_user_model()


@pytest.mark.django_db
class TestActivitySkillLink:
    """Tests for ActivityService.set/clear_activity_skill."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username='test', password='pass123')
        self.playbook = Playbook.objects.create(
            name='PB', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        self.workflow = Workflow.objects.create(
            name='WF', description='d', playbook=self.playbook, order=1,
        )
        self.activity = Activity.objects.create(
            name='Act1', guidance='g', workflow=self.workflow, order=1,
        )
        self.skill = Skill.objects.create(
            playbook=self.playbook, title='SK1',
            capability_domain='GUI_FORM', technology_stack='React',
        )

    def test_set_activity_skill_happy(self):
        """Link skill to activity in same playbook."""
        updated = ActivityService.set_activity_skill(self.activity.id, self.skill.id)
        assert updated.skill_id == self.skill.id

    def test_set_activity_skill_persists(self):
        """FK is persisted to DB."""
        ActivityService.set_activity_skill(self.activity.id, self.skill.id)
        self.activity.refresh_from_db()
        assert self.activity.skill_id == self.skill.id

    def test_set_activity_skill_cross_playbook_raises(self):
        """Cannot link skill from a different playbook."""
        other_pb = Playbook.objects.create(
            name='Other', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        other_skill = Skill.objects.create(
            playbook=other_pb, title='OtherSK',
        )
        with pytest.raises(ValidationError, match='same playbook'):
            ActivityService.set_activity_skill(self.activity.id, other_skill.id)

    def test_set_activity_skill_replaces_existing(self):
        """Setting a new skill replaces the old one."""
        skill2 = Skill.objects.create(
            playbook=self.playbook, title='SK2',
        )
        ActivityService.set_activity_skill(self.activity.id, self.skill.id)
        ActivityService.set_activity_skill(self.activity.id, skill2.id)
        self.activity.refresh_from_db()
        assert self.activity.skill_id == skill2.id

    def test_clear_activity_skill_happy(self):
        """Unlink skill from activity."""
        self.activity.skill = self.skill
        self.activity.save()
        updated = ActivityService.clear_activity_skill(self.activity.id)
        assert updated.skill_id is None

    def test_clear_activity_skill_persists(self):
        """NULL FK is persisted."""
        self.activity.skill = self.skill
        self.activity.save()
        ActivityService.clear_activity_skill(self.activity.id)
        self.activity.refresh_from_db()
        assert self.activity.skill_id is None

    def test_clear_activity_skill_already_null(self):
        """Clearing when already NULL is a no-op, no error."""
        updated = ActivityService.clear_activity_skill(self.activity.id)
        assert updated.skill_id is None


@pytest.mark.django_db
class TestActivityAgentLink:
    """Tests for ActivityService.set/clear_activity_agent."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username='test', password='pass123')
        self.playbook = Playbook.objects.create(
            name='PB', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        self.workflow = Workflow.objects.create(
            name='WF', description='d', playbook=self.playbook, order=1,
        )
        self.activity = Activity.objects.create(
            name='Act1', guidance='g', workflow=self.workflow, order=1,
        )
        self.agent = Agent.objects.create(
            playbook=self.playbook, name='AG1', description='agent',
        )

    def test_set_activity_agent_happy(self):
        """Link agent to activity in same playbook."""
        updated = ActivityService.set_activity_agent(self.activity.id, self.agent.id)
        assert updated.agent_id == self.agent.id

    def test_set_activity_agent_cross_playbook_raises(self):
        """Cannot link agent from a different playbook."""
        other_pb = Playbook.objects.create(
            name='Other', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        other_agent = Agent.objects.create(
            playbook=other_pb, name='OtherAG',
        )
        with pytest.raises(ValidationError, match='same playbook'):
            ActivityService.set_activity_agent(self.activity.id, other_agent.id)

    def test_clear_activity_agent_happy(self):
        """Unlink agent from activity."""
        self.activity.agent = self.agent
        self.activity.save()
        updated = ActivityService.clear_activity_agent(self.activity.id)
        assert updated.agent_id is None

    def test_clear_activity_agent_already_null(self):
        """Clearing when already NULL is a no-op."""
        updated = ActivityService.clear_activity_agent(self.activity.id)
        assert updated.agent_id is None


@pytest.mark.django_db
class TestSkillServiceActivities:
    """Tests for SkillService.get_activities_for_skill and facades."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username='test', password='pass123')
        self.playbook = Playbook.objects.create(
            name='PB', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        self.workflow = Workflow.objects.create(
            name='WF', description='d', playbook=self.playbook, order=1,
        )
        self.skill = Skill.objects.create(
            playbook=self.playbook, title='SK1',
            capability_domain='GUI_FORM', technology_stack='React',
        )
        self.act1 = Activity.objects.create(
            name='Act1', guidance='g', workflow=self.workflow, order=1, skill=self.skill,
        )
        self.act2 = Activity.objects.create(
            name='Act2', guidance='g', workflow=self.workflow, order=2,
        )

    def test_get_activities_for_skill(self):
        """Returns activities referencing the skill."""
        activities = SkillService.get_activities_for_skill(self.skill.id)
        assert list(activities) == [self.act1]

    def test_get_activities_for_skill_empty(self):
        """Returns empty QS when no activities reference the skill."""
        skill2 = Skill.objects.create(playbook=self.playbook, title='SK2')
        activities = SkillService.get_activities_for_skill(skill2.id)
        assert activities.count() == 0

    def test_link_skill_to_activity_facade(self):
        """Facade delegates to ActivityService."""
        SkillService.link_skill_to_activity(self.act2.id, self.skill.id)
        self.act2.refresh_from_db()
        assert self.act2.skill_id == self.skill.id

    def test_unlink_skill_from_activity_facade(self):
        """Facade delegates to ActivityService."""
        SkillService.unlink_skill_from_activity(self.act1.id)
        self.act1.refresh_from_db()
        assert self.act1.skill_id is None


@pytest.mark.django_db
class TestAgentServiceActivities:
    """Tests for AgentService.get_activities_for_agent and facades."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.user = User.objects.create_user(username='test', password='pass123')
        self.playbook = Playbook.objects.create(
            name='PB', description='d', category='development',
            status='draft', source='owned', author=self.user,
        )
        self.workflow = Workflow.objects.create(
            name='WF', description='d', playbook=self.playbook, order=1,
        )
        self.agent = Agent.objects.create(
            playbook=self.playbook, name='AG1', description='agent',
        )
        self.act1 = Activity.objects.create(
            name='Act1', guidance='g', workflow=self.workflow, order=1, agent=self.agent,
        )
        self.act2 = Activity.objects.create(
            name='Act2', guidance='g', workflow=self.workflow, order=2,
        )

    def test_get_activities_for_agent(self):
        """Returns activities referencing the agent."""
        activities = AgentService.get_activities_for_agent(self.agent.id)
        assert list(activities) == [self.act1]

    def test_get_activities_for_agent_empty(self):
        """Returns empty QS when no activities reference the agent."""
        agent2 = Agent.objects.create(playbook=self.playbook, name='AG2')
        activities = AgentService.get_activities_for_agent(agent2.id)
        assert activities.count() == 0

    def test_link_agent_to_activity_facade(self):
        """Facade delegates to ActivityService."""
        AgentService.link_agent_to_activity(self.act2.id, self.agent.id)
        self.act2.refresh_from_db()
        assert self.act2.agent_id == self.agent.id

    def test_unlink_agent_from_activity_facade(self):
        """Facade delegates to ActivityService."""
        AgentService.unlink_agent_from_activity(self.act1.id)
        self.act1.refresh_from_db()
        assert self.act1.agent_id is None
