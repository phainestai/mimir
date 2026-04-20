"""Unit tests for RuleService and activity rule linking."""

import pytest
from django.core.exceptions import ValidationError

from methodology.models import Playbook, Workflow, Activity, Rule
from methodology.services.rule_service import RuleService
from methodology.services.activity_service import ActivityService


@pytest.mark.django_db
class TestRuleService:
    """Rule CRUD and slug uniqueness."""

    @pytest.fixture
    def playbook(self, django_user_model):
        user = django_user_model.objects.create_user('u1', 'u@e.com', 'pw')
        return Playbook.objects.create(
            name='PB', description='', category='dev', author=user, status='draft', version='0.1'
        )

    def test_create_and_list(self, playbook):
        r = RuleService.create_rule(playbook=playbook, title='My Rule', content='Body')
        assert r.slug
        qs = RuleService.list_rules_for_playbook(playbook.id)
        assert qs.count() == 1

    def test_set_activity_rules_validates_playbook(self, playbook):
        wf = Workflow.objects.create(name='W', playbook=playbook, abbreviation='W', order=1)
        act = Activity.objects.create(workflow=wf, name='A', guidance='g', order=1)
        other_pb = Playbook.objects.create(
            name='PB2', description='', category='dev', author=playbook.author, status='draft', version='0.1'
        )
        bad = Rule.objects.create(playbook=other_pb, title='X', slug='x', content='')
        with pytest.raises(ValidationError):
            ActivityService.set_activity_rules(act.id, [bad.id])
