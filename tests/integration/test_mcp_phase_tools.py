"""
Integration tests for Phase MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
"""
import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Phase
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_playbook,
    create_phase,
    list_phases,
    get_phase,
    update_phase,
    delete_phase,
    reorder_phases
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
async def test_playbook(setup_user_context):
    """Create a test playbook."""
    return await create_playbook(
        name="Test Playbook",
        description="For phase testing",
        category="test"
    )


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseCreate:
    """Test create_phase MCP tool."""
    
    @pytest.mark.asyncio
    async def test_create_phase_success(self, test_playbook):
        """Create phase via MCP tool."""
        result = await create_phase(
            playbook_id=test_playbook['id'],
            name="Inception",
            description="ESM & DTA & DSP focused",
            order=1
        )
        
        assert result['id'] is not None
        assert result['name'] == "Inception"
        assert result['description'] == "ESM & DTA & DSP focused"
        assert result['order'] == 1
        
        # Verify in database
        phase = await sync_to_async(Phase.objects.get)(id=result['id'])
        assert phase.playbook_id == test_playbook['id']
        assert phase.name == "Inception"
    
    @pytest.mark.asyncio
    async def test_create_phase_duplicate_name_raises_error(self, test_playbook):
        """Create phase with duplicate name raises error."""
        await create_phase(playbook_id=test_playbook['id'], name="Inception", description="First", order=1)
        
        with pytest.raises(ValueError, match='Inception'):
            await create_phase(playbook_id=test_playbook['id'], name="Inception", description="Duplicate", order=2)


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseList:
    """Test list_phases MCP tool."""
    
    @pytest.mark.asyncio
    async def test_list_phases_returns_all_phases(self, test_playbook):
        """List all phases for a playbook."""
        await create_phase(playbook_id=test_playbook['id'], name="Inception", description="Phase 1", order=1)
        await create_phase(playbook_id=test_playbook['id'], name="Elaboration", description="Phase 2", order=2)
        await create_phase(playbook_id=test_playbook['id'], name="Construction", description="Phase 3", order=3)
        
        result = await list_phases(playbook_id=test_playbook['id'])
        
        assert len(result) == 3
        assert result[0]['name'] == "Inception"
        assert result[1]['name'] == "Elaboration"
        assert result[2]['name'] == "Construction"


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseGet:
    """Test get_phase MCP tool."""
    
    @pytest.mark.asyncio
    async def test_get_phase_returns_details(self, test_playbook):
        """Get phase details with activities."""
        created = await create_phase(
            playbook_id=test_playbook['id'],
            name="Inception",
            description="ESM & DTA & DSP focused",
            order=1
        )
        
        result = await get_phase(phase_id=created['id'])
        
        assert result['id'] == created['id']
        assert result['name'] == "Inception"
        assert result['description'] == "ESM & DTA & DSP focused"
        assert 'activities' in result


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseUpdate:
    """Test update_phase MCP tool."""
    
    @pytest.mark.asyncio
    async def test_update_phase_changes_name(self, test_playbook):
        """Update phase name via MCP tool."""
        created = await create_phase(
            playbook_id=test_playbook['id'],
            name="Inception",
            description="Original",
            order=1
        )
        
        result = await update_phase(
            phase_id=created['id'],
            name="Updated Inception",
            description="Updated description"
        )
        
        assert result['name'] == "Updated Inception"
        assert result['description'] == "Updated description"
        
        # Verify in database
        phase = await sync_to_async(Phase.objects.get)(id=created['id'])
        assert phase.name == "Updated Inception"


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseDelete:
    """Test delete_phase MCP tool."""
    
    @pytest.mark.asyncio
    async def test_delete_phase_removes_from_database(self, test_playbook):
        """Delete phase via MCP tool."""
        created = await create_phase(
            playbook_id=test_playbook['id'],
            name="To Delete",
            description="Will be deleted",
            order=1
        )
        
        result = await delete_phase(phase_id=created['id'])
        
        assert result['deleted'] is True
        
        # Verify not in database
        exists = await sync_to_async(Phase.objects.filter(id=created['id']).exists)()
        assert not exists


@pytest.mark.django_db(transaction=True)
class TestMCPPhaseReorder:
    """Test reorder_phases MCP tool."""
    
    @pytest.mark.asyncio
    async def test_reorder_phases_changes_order(self, test_playbook):
        """Reorder phases via MCP tool."""
        phase1 = await create_phase(playbook_id=test_playbook['id'], name="First", description="1", order=1)
        phase2 = await create_phase(playbook_id=test_playbook['id'], name="Second", description="2", order=2)
        phase3 = await create_phase(playbook_id=test_playbook['id'], name="Third", description="3", order=3)
        
        # Reorder: 3, 1, 2
        result = await reorder_phases(
            playbook_id=test_playbook['id'],
            phase_order=[phase3['id'], phase1['id'], phase2['id']]
        )
        
        assert result['reordered'] is True
        assert result['count'] == 3
        
        # Verify new order in database
        phases = await sync_to_async(list)(Phase.objects.filter(playbook_id=test_playbook['id']).order_by('order'))
        assert phases[0].name == "Third"
        assert phases[1].name == "First"
        assert phases[2].name == "Second"
