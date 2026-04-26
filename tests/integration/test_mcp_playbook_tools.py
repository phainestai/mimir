"""
Integration tests for Playbook MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
Based on BDD scenarios from interact-with-playbooks-via-mcp.feature.
"""
import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_playbook,
    list_playbooks,
    get_playbook,
    update_playbook,
    delete_playbook
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


@pytest.mark.django_db(transaction=True)
class TestMCPPlaybookCreate:
    """MCP-PB-01 to MCP-PB-03: Create playbook scenarios."""
    
    @pytest.mark.asyncio
    async def test_mcp_pb_01_create_draft_playbook_via_mcp_tool(self, setup_user_context):
        """
        Scenario: MCP-PB-01 Create draft playbook via MCP tool
        Given Cascade receives user request
        When Cascade calls create_playbook
        Then playbook created with version 0.1, status draft
        """
        result = await create_playbook(
            name="React Component Development",
            description="Best practices for building reusable React components",
            category="frontend"
        )
        
        assert result['id'] is not None
        assert result['version'] == '0.1'
        assert result['status'] == 'draft'
        
        # Verify in database
        playbook = await sync_to_async(Playbook.objects.select_related('author').get)(id=result['id'])
        assert playbook.author == setup_user_context
        assert playbook.name == "React Component Development"
    
    @pytest.mark.asyncio
    async def test_mcp_pb_02_create_playbook_with_duplicate_name_raises_error(self, setup_user_context):
        """Scenario: MCP-PB-02 Create playbook with duplicate name raises error"""
        await create_playbook(name="React Component Development", description="Test", category="frontend")
        
        with pytest.raises(ValueError):
            await create_playbook(name="React Component Development", description="Different", category="frontend")


@pytest.mark.django_db(transaction=True)
class TestMCPPlaybookUpdate:
    """MCP-PB-10 to MCP-PB-13: Update playbook scenarios."""
    
    @pytest.mark.asyncio
    async def test_mcp_pb_10_update_draft_playbook_increments_version(self, setup_user_context):
        """Scenario: MCP-PB-10 Update draft playbook increments version"""
        created = await create_playbook(name="Original Name", description="Original Description", category="development")
        
        result = await update_playbook(playbook_id=created['id'], name="Updated Name")
        
        assert result['name'] == "Updated Name"
        assert result['version'] == '0.2'
        # Version incremented

    @pytest.mark.asyncio
    async def test_mcp_pb_11_update_playbook_duplicate_name_raises_value_error(self, setup_user_context):
        """Renaming a playbook to an existing name raises ValueError."""
        first = await create_playbook(name='Alpha Playbook', description='a', category='test')
        await create_playbook(name='Beta Playbook', description='b', category='test')
        with pytest.raises(ValueError, match='Beta'):
            await update_playbook(playbook_id=first['id'], name='Beta Playbook')


@pytest.mark.django_db(transaction=True)
class TestMCPPlaybookDelete:
    """MCP-PB-14: Delete playbook scenarios."""
    
    @pytest.mark.asyncio
    async def test_mcp_pb_14_delete_draft_playbook_success(self, setup_user_context):
        """Scenario: MCP-PB-14 Delete draft playbook removes from database"""
        created = await create_playbook(name="To Delete", description="Will be deleted", category="test")
        
        result = await delete_playbook(playbook_id=created['id'])
        
        assert result['deleted'] is True
        exists = await sync_to_async(Playbook.objects.filter(id=created['id']).exists)()
        assert not exists
