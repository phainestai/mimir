"""Integration tests for Rule MCP tools (real DB, no mocks)."""

import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Rule
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_rule,
    list_rules,
    get_rule,
    set_activity_rules,
    get_activity,
)

User = get_user_model()


@pytest.fixture
def maria(db):
    return User.objects.create_user(username='maria', email='m@test.com', password='x')


@pytest.fixture
def setup_user_context(maria):
    set_current_user(maria)
    return maria


@pytest.fixture
def draft_pb(maria):
    return Playbook.objects.create(
        name='PB', description='', category='d', status='draft',
        source='owned', author=maria, version=Decimal('0.1'),
    )


@pytest.mark.django_db(transaction=True)
class TestMCPRules:
    @pytest.mark.asyncio
    async def test_create_list_get_activity(self, setup_user_context, draft_pb):
        wf = await sync_to_async(Workflow.objects.create)(
            name='W', description='', playbook=draft_pb, order=1,
        )
        act = await sync_to_async(Activity.objects.create)(
            name='A', guidance='g', workflow=wf, order=1,
        )
        r = await create_rule(
            playbook_id=draft_pb.id,
            title='Always pytest',
            content='Use pytest.',
            slug='pytest',
            always_apply=True,
        )
        assert r['slug'] == 'pytest'

        lst = await list_rules(playbook_id=draft_pb.id)
        assert len(lst) == 1

        await sync_to_async(Activity.objects.get)(pk=act.id)
        await set_activity_rules(act.id, [r['id']])

        detail = await get_activity(act.id)
        assert len(detail['rules']) == 1
        assert detail['rules'][0]['slug'] == 'pytest'

    @pytest.mark.asyncio
    async def test_get_rule(self, setup_user_context, draft_pb):
        await create_rule(playbook_id=draft_pb.id, title='R1', slug='r1')
        rid = (await list_rules(playbook_id=draft_pb.id))[0]['id']
        g = await get_rule(rid)
        assert g['title'] == 'R1'
