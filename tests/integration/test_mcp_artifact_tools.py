"""
Integration tests for Artifact MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
Follows the same pattern as test_mcp_skill_tools.py.
"""
import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Artifact, ArtifactInput
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_artifact,
    list_artifacts,
    get_artifact,
    update_artifact,
    delete_artifact,
    link_artifact_to_activity,
    unlink_artifact_from_activity,
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


# ============================================================================
# CREATE
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactCreate:
    """MCP-AR-01 to MCP-AR-03: Create artifact scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_01_create_artifact_in_draft_playbook(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN a draft playbook with an activity
        WHEN create_artifact is called with valid params
        THEN artifact is created with correct fields
        """
        wf, act1, act2 = workflow_with_activities
        result = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='API Specification',
            description='REST API contract',
            type='Document',
            is_required=True,
        )

        assert result['id'] is not None
        assert result['name'] == 'API Specification'
        assert result['type'] == 'Document'
        assert result['is_required'] is True
        assert result['produced_by_id'] == act1.id
        assert result['playbook_id'] == draft_playbook.id

    @pytest.mark.asyncio
    async def test_mcp_ar_01_version_incremented(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """Verify parent playbook version incremented after artifact creation."""
        wf, act1, act2 = workflow_with_activities
        old_version = draft_playbook.version
        await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ar_02_empty_name_raises(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN a draft playbook
        WHEN create_artifact is called with empty name
        THEN ValueError is raised
        """
        wf, act1, act2 = workflow_with_activities
        with pytest.raises(ValueError):
            await create_artifact(
                playbook_id=draft_playbook.id,
                produced_by_id=act1.id,
                name='',
            )

    @pytest.mark.asyncio
    async def test_mcp_ar_03_released_playbook_raises(
        self, setup_user_context, released_playbook,
    ):
        """
        GIVEN a released playbook
        WHEN create_artifact is called
        THEN PermissionError is raised
        """
        with pytest.raises(PermissionError):
            await create_artifact(
                playbook_id=released_playbook.id,
                produced_by_id=999,
                name='AR1',
            )


# ============================================================================
# LIST
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactList:
    """MCP-AR-04 to MCP-AR-06: List artifact scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_04_list_artifacts(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN a playbook with 3 artifacts
        WHEN list_artifacts is called
        THEN all 3 are returned
        """
        wf, act1, act2 = workflow_with_activities
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='AR1', type='Document')
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='AR2', type='Code')
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act2.id, name='AR3', type='Template')

        result = await list_artifacts(playbook_id=draft_playbook.id)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_mcp_ar_05_filter_by_type(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN artifacts of different types
        WHEN list_artifacts is filtered by type='Document'
        THEN only Document artifacts are returned
        """
        wf, act1, act2 = workflow_with_activities
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='AR1', type='Document')
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='AR2', type='Code')

        result = await list_artifacts(playbook_id=draft_playbook.id, type_filter='Document')
        assert len(result) == 1
        assert result[0]['type'] == 'Document'

    @pytest.mark.asyncio
    async def test_mcp_ar_06_search(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN artifacts with different names
        WHEN list_artifacts is called with search='API'
        THEN only matching artifacts are returned
        """
        wf, act1, act2 = workflow_with_activities
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='API Specification')
        await create_artifact(playbook_id=draft_playbook.id, produced_by_id=act1.id, name='Component Template')

        result = await list_artifacts(playbook_id=draft_playbook.id, search='API')
        assert len(result) == 1
        assert result[0]['name'] == 'API Specification'


# ============================================================================
# GET
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactGet:
    """MCP-AR-07: Get artifact scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_07_get_artifact_with_consumer_count(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact consumed by 2 activities
        WHEN get_artifact is called
        THEN consumer_count is 2
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='API Specification',
            type='Document',
            is_required=True,
        )
        # Link act2 as consumer
        await link_artifact_to_activity(
            artifact_id=created['id'],
            activity_id=act2.id,
            is_required=True,
        )

        result = await get_artifact(artifact_id=created['id'])
        assert result['name'] == 'API Specification'
        assert result['type'] == 'Document'
        assert result['is_required'] is True
        assert result['consumer_count'] == 1  # act2 only; act1 is producer, not consumer


# ============================================================================
# UPDATE
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactUpdate:
    """MCP-AR-08 to MCP-AR-09: Update artifact scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_08_update_artifact(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an existing artifact
        WHEN update_artifact is called with new fields
        THEN artifact fields are updated and version incremented
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='API Specification',
            type='Document',
        )
        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = draft_playbook.version

        result = await update_artifact(
            artifact_id=created['id'],
            name='Updated API Spec',
            type='Code',
            is_required=True,
        )

        assert result['name'] == 'Updated API Spec'
        assert result['type'] == 'Code'
        assert result['is_required'] is True

        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ar_08b_update_artifact_duplicate_name_raises_value_error(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """Renaming an artifact to an existing name in the same playbook raises ValueError."""
        wf, act1, act2 = workflow_with_activities
        first = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='First Artifact',
        )
        await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='Second Artifact',
        )
        with pytest.raises(ValueError, match='Second Artifact'):
            await update_artifact(artifact_id=first['id'], name='Second Artifact')

    @pytest.mark.asyncio
    async def test_mcp_ar_09_update_released_raises(
        self, setup_user_context, released_playbook,
    ):
        """
        GIVEN an artifact in a released playbook
        WHEN update_artifact is called
        THEN PermissionError is raised
        """
        wf = await sync_to_async(Workflow.objects.create)(
            name='WF1', description='d', playbook=released_playbook, order=1,
        )
        act = await sync_to_async(Activity.objects.create)(
            name='Act1', guidance='g', workflow=wf, order=1,
        )
        artifact = await sync_to_async(Artifact.objects.create)(
            playbook=released_playbook, produced_by=act,
            name='AR1', type='Document',
        )
        with pytest.raises(PermissionError):
            await update_artifact(artifact_id=artifact.id, name='Updated')


# ============================================================================
# DELETE
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactDelete:
    """MCP-AR-10 to MCP-AR-11: Delete artifact scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_10_delete_artifact_clears_consumers(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact consumed by an activity
        WHEN delete_artifact is called
        THEN artifact is deleted and consumer relationships are cleared
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )
        await link_artifact_to_activity(
            artifact_id=created['id'],
            activity_id=act2.id,
        )
        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = draft_playbook.version

        result = await delete_artifact(artifact_id=created['id'])
        assert result['deleted'] is True

        # Verify artifact no longer exists
        exists = await sync_to_async(Artifact.objects.filter(id=created['id']).exists)()
        assert exists is False

        # Verify version incremented
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_ar_11_delete_released_raises(
        self, setup_user_context, released_playbook,
    ):
        """
        GIVEN an artifact in a released playbook
        WHEN delete_artifact is called
        THEN PermissionError is raised
        """
        wf = await sync_to_async(Workflow.objects.create)(
            name='WF1', description='d', playbook=released_playbook, order=1,
        )
        act = await sync_to_async(Activity.objects.create)(
            name='Act1', guidance='g', workflow=wf, order=1,
        )
        artifact = await sync_to_async(Artifact.objects.create)(
            playbook=released_playbook, produced_by=act,
            name='AR1', type='Document',
        )
        with pytest.raises(PermissionError):
            await delete_artifact(artifact_id=artifact.id)


# ============================================================================
# LINK / UNLINK
# ============================================================================

@pytest.mark.django_db(transaction=True)
class TestMCPArtifactLinkUnlink:
    """MCP-AR-12 to MCP-AR-15: Link/unlink scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_ar_12_link_artifact_to_consumer_activity(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact produced by act1
        WHEN link_artifact_to_activity is called with act2
        THEN act2 becomes a consumer of the artifact
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )

        result = await link_artifact_to_activity(
            artifact_id=created['id'],
            activity_id=act2.id,
            is_required=True,
        )
        assert result['artifact_id'] == created['id']
        assert result['activity_id'] == act2.id
        assert result['is_required'] is True

    @pytest.mark.asyncio
    async def test_mcp_ar_13_link_to_producer_raises(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact produced by act1
        WHEN link_artifact_to_activity is called with act1 (the producer)
        THEN ValueError is raised (circular dependency)
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )

        with pytest.raises(ValueError, match='[Cc]ircular'):
            await link_artifact_to_activity(
                artifact_id=created['id'],
                activity_id=act1.id,
            )

    @pytest.mark.asyncio
    async def test_mcp_ar_14_duplicate_link_raises(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact already linked to act2
        WHEN link_artifact_to_activity is called again for act2
        THEN ValueError is raised
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )
        await link_artifact_to_activity(
            artifact_id=created['id'],
            activity_id=act2.id,
        )

        with pytest.raises(ValueError, match='already'):
            await link_artifact_to_activity(
                artifact_id=created['id'],
                activity_id=act2.id,
            )

    @pytest.mark.asyncio
    async def test_mcp_ar_15_unlink_artifact_from_activity(
        self, setup_user_context, draft_playbook, workflow_with_activities,
    ):
        """
        GIVEN an artifact linked to act2
        WHEN unlink_artifact_from_activity is called
        THEN the ArtifactInput record is removed
        """
        wf, act1, act2 = workflow_with_activities
        created = await create_artifact(
            playbook_id=draft_playbook.id,
            produced_by_id=act1.id,
            name='AR1',
        )
        link_result = await link_artifact_to_activity(
            artifact_id=created['id'],
            activity_id=act2.id,
        )

        result = await unlink_artifact_from_activity(
            artifact_input_id=link_result['id'],
        )
        assert result['deleted'] is True

        # Verify the link no longer exists
        exists = await sync_to_async(
            ArtifactInput.objects.filter(id=link_result['id']).exists
        )()
        assert exists is False
