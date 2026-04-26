"""
Integration tests for Agent MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
Based on BDD scenarios from interact-with-agents-via-mcp.feature.
"""
import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Agent
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_agent,
    list_agents,
    get_agent,
    update_agent,
    delete_agent,
    link_agent_to_activity,
    unlink_agent_from_activity,
)

User = get_user_model()


@pytest.fixture
def maria(db):
    """Create test user maria."""
    return User.objects.create_user(username='maria', email='maria@test.com', password='test123')


@pytest.fixture
def setup_user_context(maria):
    """Set up MCP user context for maria."""
    set_current_user(maria)
    return maria


@pytest.fixture
def draft_playbook(maria):
    """Create draft playbook owned by maria."""
    return Playbook.objects.create(
        name='React Frontend v1.2', description='Frontend guide',
        category='frontend', status='draft', source='owned', author=maria,
    )


@pytest.fixture
def released_playbook(maria):
    """Create released playbook owned by maria."""
    return Playbook.objects.create(
        name='Production Guide', description='Released guide',
        category='ops', status='released', source='owned', author=maria,
    )


@pytest.fixture
def workflow_with_activities(draft_playbook):
    """Create workflow with 2 activities in draft playbook."""
    wf = Workflow.objects.create(
        name='WF1', description='d', playbook=draft_playbook, order=1,
    )
    act1 = Activity.objects.create(name='Act1', guidance='g', workflow=wf, order=1)
    act2 = Activity.objects.create(name='Act2', guidance='g', workflow=wf, order=2)
    return wf, act1, act2


@pytest.mark.django_db(transaction=True)
class TestMCPAgentCreate:
    """MCP-AG-01 to MCP-AG-03: Create agent scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_01_create_agent_in_draft_playbook(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-01 Create agent in draft playbook."""
        result = await create_agent(
            playbook_id=draft_playbook.id,
            name='Code Reviewer',
            description='Reviews PRs and suggests improvements',
        )

        assert result['id'] is not None
        assert result['name'] == 'Code Reviewer'
        assert result['playbook_id'] == draft_playbook.id

    @pytest.mark.asyncio
    async def test_mcp_ag_01_version_incremented(self, setup_user_context, draft_playbook):
        """Verify parent playbook version incremented after agent creation."""
        old_version = Decimal(str(draft_playbook.version))
        await create_agent(playbook_id=draft_playbook.id, name='AG1')
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ag_02_empty_name_raises(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-02 Create agent with empty name raises error."""
        with pytest.raises(ValueError):
            await create_agent(playbook_id=draft_playbook.id, name='')

    @pytest.mark.asyncio
    async def test_mcp_ag_03_released_playbook_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-AG-03 Create agent in released playbook raises error."""
        with pytest.raises(PermissionError):
            await create_agent(playbook_id=released_playbook.id, name='AG1')


@pytest.mark.django_db(transaction=True)
class TestMCPAgentList:
    """MCP-AG-04 to MCP-AG-05: List agent scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_04_list_agents(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-04 List agents for playbook."""
        await create_agent(playbook_id=draft_playbook.id, name='AG1')
        await create_agent(playbook_id=draft_playbook.id, name='AG2')
        await create_agent(playbook_id=draft_playbook.id, name='AG3')

        result = await list_agents(playbook_id=draft_playbook.id)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_mcp_ag_05_search(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-05 List agents with search query."""
        await create_agent(playbook_id=draft_playbook.id, name='Code Reviewer')
        await create_agent(playbook_id=draft_playbook.id, name='Test Generator')

        result = await list_agents(playbook_id=draft_playbook.id, search='Reviewer')
        assert len(result) == 1
        assert result[0]['name'] == 'Code Reviewer'


@pytest.mark.django_db(transaction=True)
class TestMCPAgentGet:
    """MCP-AG-06: Get agent scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_06_get_agent_with_activity_count(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-AG-06 Get agent details with activity count."""
        wf, act1, act2 = workflow_with_activities
        created = await create_agent(
            playbook_id=draft_playbook.id, name='Code Reviewer',
            description='Reviews PRs',
        )
        await link_agent_to_activity(act1.id, created['id'])
        await link_agent_to_activity(act2.id, created['id'])

        result = await get_agent(agent_id=created['id'])
        assert result['name'] == 'Code Reviewer'
        assert result['activity_count'] == 2


@pytest.mark.django_db(transaction=True)
class TestMCPAgentUpdate:
    """MCP-AG-07 to MCP-AG-08: Update agent scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_07_update_agent(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-07 Update agent name and description."""
        created = await create_agent(
            playbook_id=draft_playbook.id, name='Code Reviewer',
            description='Reviews PRs',
        )
        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = draft_playbook.version

        result = await update_agent(
            agent_id=created['id'],
            name='Senior Reviewer',
            description='Updated desc',
        )

        assert result['name'] == 'Senior Reviewer'
        assert result['description'] == 'Updated desc'

        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ag_07b_update_agent_duplicate_name_raises_value_error(
        self, setup_user_context, draft_playbook,
    ):
        """Renaming an agent to an existing name in the same playbook raises ValueError."""
        a = await create_agent(playbook_id=draft_playbook.id, name='Agent A')
        b = await create_agent(playbook_id=draft_playbook.id, name='Agent B')
        with pytest.raises(ValueError, match='Agent B'):
            await update_agent(agent_id=a['id'], name='Agent B')

    @pytest.mark.asyncio
    async def test_mcp_ag_08_update_released_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-AG-08 Update agent in released playbook raises error."""
        agent = await sync_to_async(Agent.objects.create)(
            playbook=released_playbook, name='AG1',
        )
        with pytest.raises(PermissionError):
            await update_agent(agent_id=agent.id, name='Updated')


@pytest.mark.django_db(transaction=True)
class TestMCPAgentDelete:
    """MCP-AG-09 to MCP-AG-10: Delete agent scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_09_delete_agent_clears_fks(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-AG-09 Delete agent clears activity FKs."""
        wf, act1, act2 = workflow_with_activities
        created = await create_agent(playbook_id=draft_playbook.id, name='AG1')
        await link_agent_to_activity(act1.id, created['id'])
        await link_agent_to_activity(act2.id, created['id'])

        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = draft_playbook.version

        result = await delete_agent(agent_id=created['id'])
        assert result['deleted'] is True

        await sync_to_async(act1.refresh_from_db)()
        await sync_to_async(act2.refresh_from_db)()
        assert act1.agent_id is None
        assert act2.agent_id is None

        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ag_10_delete_released_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-AG-10 Delete agent in released playbook raises error."""
        agent = await sync_to_async(Agent.objects.create)(
            playbook=released_playbook, name='AG1',
        )
        with pytest.raises(PermissionError):
            await delete_agent(agent_id=agent.id)


@pytest.mark.django_db(transaction=True)
class TestMCPAgentLinkUnlink:
    """MCP-AG-11 to MCP-AG-13: Link/unlink scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ag_11_link_same_playbook(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-AG-11 Link agent to activity in same playbook."""
        wf, act1, act2 = workflow_with_activities
        created = await create_agent(playbook_id=draft_playbook.id, name='AG1')

        result = await link_agent_to_activity(act1.id, created['id'])
        assert result['agent_id'] == created['id']

    @pytest.mark.asyncio
    async def test_mcp_ag_12_link_cross_playbook_raises(self, setup_user_context, draft_playbook):
        """Scenario: MCP-AG-12 Link agent to activity in different playbook raises error."""
        other_pb = await sync_to_async(Playbook.objects.create)(
            name='Other PB', description='d', category='ops',
            status='draft', source='owned', author=setup_user_context,
        )
        other_wf = await sync_to_async(Workflow.objects.create)(
            name='OtherWF', description='d', playbook=other_pb, order=1,
        )
        other_act = await sync_to_async(Activity.objects.create)(
            name='OtherAct', guidance='g', workflow=other_wf, order=1,
        )
        created = await create_agent(playbook_id=draft_playbook.id, name='AG1')

        with pytest.raises(ValueError, match='same playbook'):
            await link_agent_to_activity(other_act.id, created['id'])

    @pytest.mark.asyncio
    async def test_mcp_ag_13_unlink(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-AG-13 Unlink agent from activity."""
        wf, act1, act2 = workflow_with_activities
        created = await create_agent(playbook_id=draft_playbook.id, name='AG1')
        await link_agent_to_activity(act1.id, created['id'])

        result = await unlink_agent_from_activity(act1.id)
        assert result['agent_id'] is None
