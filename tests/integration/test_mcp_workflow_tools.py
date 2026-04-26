"""Integration tests for Workflow MCP tools."""
import pytest
import pytest_asyncio
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow
from mcp_integration.context import set_current_user
from mcp_integration.tools import create_playbook, create_workflow, update_workflow, delete_workflow

User = get_user_model()

@pytest.fixture
def maria(db):
    return User.objects.create_user(username='maria', email='maria@test.com', password='test123')

@pytest.fixture
def setup_user_context(maria):
    set_current_user(maria)
    return maria

@pytest_asyncio.fixture
async def draft_playbook(setup_user_context):
    return await create_playbook(name="Test Playbook", description="Test", category="dev")

@pytest.mark.django_db(transaction=True)
class TestMCPWorkflowCreate:
    @pytest.mark.asyncio
    async def test_mcp_wf_01_create_workflow_increments_parent_version(self, setup_user_context, draft_playbook):
        """Scenario: MCP-WF-01 Create workflow increments parent playbook version"""
        result = await create_workflow(playbook_id=draft_playbook['id'], name="Design Phase", description="Test")
        
        assert result['id'] is not None
        assert result['playbook_id'] == draft_playbook['id']
        
        playbook = await sync_to_async(Playbook.objects.get)(id=draft_playbook['id'])
        assert playbook.version > Decimal('0.1')  # Version incremented
    
    @pytest.mark.asyncio
    async def test_mcp_wf_02_create_workflow_duplicate_name_raises_error(self, setup_user_context, draft_playbook):
        """Scenario: MCP-WF-02 Duplicate workflow name raises ValueError"""
        await create_workflow(playbook_id=draft_playbook['id'], name="Design Phase", description="Test")
        
        with pytest.raises(ValueError):
            await create_workflow(playbook_id=draft_playbook['id'], name="Design Phase", description="Different")

@pytest.mark.django_db(transaction=True)
class TestMCPWorkflowUpdate:
    @pytest.mark.asyncio
    async def test_mcp_wf_11_update_workflow_duplicate_name_raises_value_error(
        self, setup_user_context, draft_playbook,
    ):
        """Renaming a workflow to an existing name in the same playbook raises ValueError."""
        wf1 = await create_workflow(
            playbook_id=draft_playbook['id'], name='First', description='a',
        )
        await create_workflow(
            playbook_id=draft_playbook['id'], name='Second', description='b',
        )
        with pytest.raises(ValueError, match='Second'):
            await update_workflow(workflow_id=wf1['id'], name='Second')


@pytest.mark.django_db(transaction=True)
class TestMCPWorkflowDelete:
    @pytest.mark.asyncio
    async def test_mcp_wf_13_delete_workflow_success(self, setup_user_context, draft_playbook):
        """Scenario: MCP-WF-13 Delete workflow removes from database"""
        workflow = await create_workflow(playbook_id=draft_playbook['id'], name="To Delete", description="Test")
        
        result = await delete_workflow(workflow_id=workflow['id'])
        
        assert result['deleted'] is True
        exists = await sync_to_async(Workflow.objects.filter(id=workflow['id']).exists)()
        assert not exists
