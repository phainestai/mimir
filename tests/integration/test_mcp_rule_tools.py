"""Integration tests for Rule MCP tools (real DB, no mocks)."""

import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
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


@pytest.mark.django_db
class TestRuleAPISlug:
    """REST API slug auto-generation: POST /api/rules/ without slug."""

    def _client(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        return client

    def test_create_rule_api_without_slug(self, db):
        user = User.objects.create_user(username='carol', email='carol@test.com', password='x')
        pb = Playbook.objects.create(
            name='PB', description='', category='d', status='draft',
            source='owned', author=user, version=Decimal('0.1'),
        )
        client = self._client(user)
        resp = client.post('/api/rules/', {
            'playbook_id': pb.id,
            'title': 'Always Write Tests',
            'content': 'No code without tests.',
            'always_apply': True,
        }, format='json')
        assert resp.status_code == 201, resp.data
        assert resp.data['slug'] == 'always-write-tests'

    def test_create_rule_api_duplicate_title_unique_slugs(self, db):
        user = User.objects.create_user(username='dave', email='dave@test.com', password='x')
        pb = Playbook.objects.create(
            name='PB2', description='', category='d', status='draft',
            source='owned', author=user, version=Decimal('0.1'),
        )
        client = self._client(user)
        payload = {'playbook_id': pb.id, 'title': 'Dup Rule', 'always_apply': True}
        r1 = client.post('/api/rules/', payload, format='json')
        r2 = client.post('/api/rules/', payload, format='json')
        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.data['slug'] != r2.data['slug'], "duplicate titles must yield distinct slugs"


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

    @pytest.mark.asyncio
    async def test_create_rule_without_slug_auto_generates(self, setup_user_context, draft_pb):
        """MCP create_rule omitting slug must succeed and auto-generate a non-empty slug."""
        r = await create_rule(
            playbook_id=draft_pb.id,
            title='Always Use Type Hints',
        )
        assert r['slug'], "slug must be non-empty when not supplied"
        assert r['slug'] == 'always-use-type-hints'

    @pytest.mark.asyncio
    async def test_create_rule_duplicate_title_gets_unique_slug(self, setup_user_context, draft_pb):
        """Two rules with the same title auto-generate distinct slugs."""
        r1 = await create_rule(playbook_id=draft_pb.id, title='Duplicated')
        r2 = await create_rule(playbook_id=draft_pb.id, title='Duplicated')
        assert r1['slug'] != r2['slug'], "duplicate titles must yield distinct slugs"
