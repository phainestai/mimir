"""
Integration tests for Activity MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
"""
import pytest
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Phase, Agent, Skill, Artifact, ArtifactInput
from mcp_integration.context import set_current_user
from mcp_integration.tools import create_activity, update_activity, get_activity

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
        name='Test Playbook', description='For testing',
        category='test', status='draft', source='owned', author=maria,
    )


@pytest.fixture
def workflow(draft_playbook):
    """Create workflow in draft playbook."""
    return Workflow.objects.create(
        name='Test Workflow',
        description='For testing',
        playbook=draft_playbook,
        order=1
    )


@pytest.fixture
def activity(workflow):
    """Create activity in workflow."""
    return Activity.objects.create(
        name='Test Activity',
        guidance='Test guidance',
        workflow=workflow,
        order=1
    )


@pytest.fixture
def phase(draft_playbook):
    """Create phase in draft playbook."""
    return Phase.objects.create(
        name='Inception',
        description='Test phase',
        playbook=draft_playbook,
        order=1
    )


@pytest.mark.django_db(transaction=True)
class TestMCPActivityCreate:
    """Test create_activity MCP tool."""

    @pytest.mark.asyncio
    async def test_create_activity_happy_path(self, setup_user_context, workflow, draft_playbook):
        """Create activity returns correct fields and increments playbook version."""
        version_before = await sync_to_async(lambda: draft_playbook.version)()

        result = await create_activity(workflow_id=workflow.id, name='New Activity')

        assert result['name'] == 'New Activity'
        assert result['workflow_id'] == workflow.id
        assert result['order'] == 1
        assert result['phase_id'] is None
        assert 'id' in result

        # Verify persisted in DB
        activity = await sync_to_async(Activity.objects.get)(pk=result['id'])
        assert activity.name == 'New Activity'

        # Playbook version should have incremented
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version > version_before

    @pytest.mark.asyncio
    async def test_create_activity_phase_id_persisted(self, setup_user_context, workflow, phase):
        """phase_id is wired through to the service and persisted on the activity."""
        result = await create_activity(
            workflow_id=workflow.id,
            name='Phase Activity',
            phase_id=phase.id,
        )
        assert result['name'] == 'Phase Activity'
        assert result['phase_id'] == phase.id

        created = await sync_to_async(Activity.objects.get)(pk=result['id'])
        assert created.phase_id == phase.id

    @pytest.mark.asyncio
    async def test_create_activity_with_predecessor(self, setup_user_context, workflow, activity):
        """Predecessor wiring is persisted correctly."""
        result = await create_activity(
            workflow_id=workflow.id,
            name='Follow-up Activity',
            predecessor_id=activity.id,
        )

        assert result['name'] == 'Follow-up Activity'
        follow_up = await sync_to_async(Activity.objects.get)(pk=result['id'])
        assert follow_up.predecessor_id == activity.id

    @pytest.mark.asyncio
    async def test_create_activity_invalid_phase_id_raises_value_error(self, setup_user_context, workflow):
        """Non-existent phase_id raises ValueError, not a raw Django ValidationError."""
        with pytest.raises(ValueError, match='Phase'):
            await create_activity(
                workflow_id=workflow.id,
                name='Bad Phase Activity',
                phase_id=99999,
            )

    @pytest.mark.asyncio
    async def test_create_activity_phase_from_different_playbook_raises_value_error(
        self, setup_user_context, workflow, maria
    ):
        """phase_id from a different playbook raises ValueError."""
        other_playbook = await sync_to_async(Playbook.objects.create)(
            name='Other Playbook', description='', category='test',
            status='draft', source='owned', author=maria,
        )
        other_phase = await sync_to_async(Phase.objects.create)(
            name='Foreign Phase', playbook=other_playbook, order=1,
        )
        with pytest.raises(ValueError, match='Phase'):
            await create_activity(
                workflow_id=workflow.id,
                name='Wrong Phase Activity',
                phase_id=other_phase.id,
            )

    @pytest.mark.asyncio
    async def test_create_activity_duplicate_name_raises_value_error(self, setup_user_context, workflow, activity):
        """Duplicate activity name in same workflow raises ValueError."""
        with pytest.raises(ValueError, match=activity.name):
            await create_activity(
                workflow_id=workflow.id,
                name=activity.name,
            )

    @pytest.mark.asyncio
    async def test_create_activity_released_playbook_raises_permission_error(self, setup_user_context, maria):
        """Creating activity in a released playbook raises PermissionError."""
        released = await sync_to_async(Playbook.objects.create)(
            name='Released Playbook', description='', category='test',
            status='released', source='owned', author=maria,
        )
        workflow = await sync_to_async(Workflow.objects.create)(
            name='Released Workflow', description='', playbook=released, order=1,
        )
        with pytest.raises(PermissionError, match='released'):
            await create_activity(workflow_id=workflow.id, name='Blocked Activity')

    @pytest.mark.asyncio
    async def test_create_activity_predecessor_in_different_workflow_raises_value_error(
        self, setup_user_context, draft_playbook, workflow, activity
    ):
        """Predecessor from a different workflow raises ValueError."""
        other_workflow = await sync_to_async(Workflow.objects.create)(
            name='Other Workflow', description='', playbook=draft_playbook, order=2,
        )
        with pytest.raises(ValueError, match=str(activity.id)):
            await create_activity(
                workflow_id=other_workflow.id,
                name='Cross-workflow Activity',
                predecessor_id=activity.id,
            )


@pytest.mark.django_db(transaction=True)
class TestMCPActivityUpdate:
    """Test update_activity MCP tool."""
    
    @pytest.mark.asyncio
    async def test_update_activity_with_phase_id(self, setup_user_context, activity, phase):
        """Update activity with phase_id parameter."""
        result = await update_activity(
            activity_id=activity.id,
            phase_id=phase.id
        )
        
        assert result['id'] == activity.id
        assert result['phase_id'] == phase.id
        
        # Verify in database
        await sync_to_async(activity.refresh_from_db)()
        assert activity.phase_id == phase.id
        
        # Access phase relationship using sync_to_async
        phase_obj = await sync_to_async(lambda: activity.phase)()
        assert phase_obj.name == 'Inception'

    @pytest.mark.asyncio
    async def test_update_activity_invalid_phase_id_raises_value_error(self, setup_user_context, activity):
        """Non-existent phase_id raises ValueError, not a raw Django ValidationError."""
        with pytest.raises(ValueError, match='Phase'):
            await update_activity(activity_id=activity.id, phase_id=99999)

    @pytest.mark.asyncio
    async def test_update_activity_phase_from_different_playbook_raises_value_error(
        self, setup_user_context, activity, maria
    ):
        """phase_id from a different playbook raises ValueError."""
        other_playbook = await sync_to_async(Playbook.objects.create)(
            name='Other Playbook', description='', category='test',
            status='draft', source='owned', author=maria,
        )
        other_phase = await sync_to_async(Phase.objects.create)(
            name='Foreign Phase', playbook=other_playbook, order=1,
        )
        with pytest.raises(ValueError, match='Phase'):
            await update_activity(activity_id=activity.id, phase_id=other_phase.id)

    @pytest.mark.asyncio
    async def test_update_activity_duplicate_name_raises_value_error(
        self, setup_user_context, workflow, activity
    ):
        """Renaming to an existing activity name in the same workflow raises ValueError."""
        other = await sync_to_async(Activity.objects.create)(
            name='Other Activity', workflow=workflow, order=2,
        )
        with pytest.raises(ValueError, match='Other Activity'):
            await update_activity(activity_id=activity.id, name=other.name)

    @pytest.mark.asyncio
    async def test_update_activity_released_playbook_raises_permission_error(self, setup_user_context, maria):
        """Updating activity in a released playbook raises PermissionError."""
        released = await sync_to_async(Playbook.objects.create)(
            name='Released Playbook', description='', category='test',
            status='released', source='owned', author=maria,
        )
        wf = await sync_to_async(Workflow.objects.create)(
            name='Released Workflow', description='', playbook=released, order=1,
        )
        act = await sync_to_async(Activity.objects.create)(
            name='Locked Activity', workflow=wf, order=1,
        )
        with pytest.raises(PermissionError, match='released'):
            await update_activity(activity_id=act.id, name='New Name')


@pytest.mark.django_db(transaction=True)
class TestMCPActivityGet:
    """Test get_activity MCP tool - Issue #71."""
    
    @pytest.mark.asyncio
    async def test_get_activity_returns_agent_skill_artifacts(self, setup_user_context, draft_playbook):
        """Test get_activity returns agent, skill, and artifact information."""
        # Create workflow
        workflow = await sync_to_async(Workflow.objects.create)(
            name='Test Workflow',
            description='For testing',
            playbook=draft_playbook,
            order=1
        )
        
        # Create agent
        agent = await sync_to_async(Agent.objects.create)(
            playbook=draft_playbook,
            name='Code Reviewer',
            description='Reviews code for quality'
        )
        
        # Create skill
        skill = await sync_to_async(Skill.objects.create)(
            playbook=draft_playbook,
            title='React Development',
            capability_domain='GUI_FORM',
            technology_stack='React+Redux',
            content='React development guide'
        )
        
        # Create producer activity (for artifacts)
        producer = await sync_to_async(Activity.objects.create)(
            name='Design Component',
            guidance='Design guidance',
            workflow=workflow,
            order=1
        )
        
        # Create test activity with agent and skill
        activity = await sync_to_async(Activity.objects.create)(
            name='Implement Component',
            guidance='Implementation guidance',
            workflow=workflow,
            order=2,
            agent=agent,
            skill=skill
        )
        
        # Create output artifact (produced by this activity)
        output_artifact = await sync_to_async(Artifact.objects.create)(
            playbook=draft_playbook,
            produced_by=activity,
            name='Component Code',
            type='Code',
            is_required=True
        )
        
        # Create input artifact (consumed by this activity)
        input_artifact = await sync_to_async(Artifact.objects.create)(
            playbook=draft_playbook,
            produced_by=producer,
            name='Design Document',
            type='Document',
            is_required=True
        )
        
        # Link input artifact to activity
        await sync_to_async(ArtifactInput.objects.create)(
            artifact=input_artifact,
            activity=activity,
            is_required=True
        )
        
        # Call get_activity
        result = await get_activity(activity_id=activity.id)
        
        # Assert basic fields
        assert result['id'] == activity.id
        assert result['name'] == 'Implement Component'
        assert result['guidance'] == 'Implementation guidance'
        
        # Assert agent information (Issue #71)
        assert result['agent'] is not None
        assert result['agent']['id'] == agent.id
        assert result['agent']['name'] == 'Code Reviewer'
        assert result['agent']['description'] == 'Reviews code for quality'
        
        # Assert skill information (Issue #71)
        assert result['skill'] is not None
        assert result['skill']['id'] == skill.id
        assert result['skill']['title'] == 'React Development'
        assert result['skill']['capability_domain'] == 'GUI_FORM'
        assert result['skill']['technology_stack'] == 'React+Redux'
        
        # Assert output artifacts (Issue #71)
        assert 'output_artifacts' in result
        assert len(result['output_artifacts']) == 1
        assert result['output_artifacts'][0]['id'] == output_artifact.id
        assert result['output_artifacts'][0]['name'] == 'Component Code'
        assert result['output_artifacts'][0]['type'] == 'Code'
        assert result['output_artifacts'][0]['is_required'] is True
        
        # Assert input artifacts (Issue #71)
        assert 'input_artifacts' in result
        assert len(result['input_artifacts']) == 1
        assert result['input_artifacts'][0]['id'] == input_artifact.id
        assert result['input_artifacts'][0]['name'] == 'Design Document'
        assert result['input_artifacts'][0]['type'] == 'Document'
        assert result['input_artifacts'][0]['is_required'] is True
    
    @pytest.mark.asyncio
    async def test_get_activity_without_agent_skill_artifacts(self, setup_user_context, workflow):
        """Test get_activity returns null/empty when no agent, skill, or artifacts."""
        # Create simple activity without agent, skill, or artifacts
        activity = await sync_to_async(Activity.objects.create)(
            name='Simple Activity',
            guidance='Simple guidance',
            workflow=workflow,
            order=1
        )
        
        # Call get_activity
        result = await get_activity(activity_id=activity.id)
        
        # Assert agent is None
        assert result['agent'] is None
        
        # Assert skill is None
        assert result['skill'] is None
        
        # Assert output artifacts is empty list
        assert result['output_artifacts'] == []
        
        # Assert input artifacts is empty list
        assert result['input_artifacts'] == []
