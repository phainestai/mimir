"""
Integration tests for Skill MCP tools.

Tests MCP tool wrappers with real database, real services, NO MOCKING.
Based on BDD scenarios from interact-with-skills-via-mcp.feature.
"""
import pytest
from decimal import Decimal
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from methodology.models import Playbook, Workflow, Activity, Skill
from mcp_integration.context import set_current_user
from mcp_integration.tools import (
    create_skill,
    list_skills,
    get_skill,
    update_skill,
    delete_skill,
    link_skill_to_activity,
    unlink_skill_from_activity,
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
class TestMCPSkillCreate:
    """MCP-SK-01 to MCP-SK-03: Create skill scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_01_create_skill_in_draft_playbook(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-01 Create skill in draft playbook."""
        result = await create_skill(
            playbook_id=draft_playbook.id,
            title='Build Login Form',
            content='## Steps\n1. Create component',
            capability_domain='GUI_FORM',
            technology_stack='React+Redux',
        )

        assert result['id'] is not None
        assert result['title'] == 'Build Login Form'
        assert result['capability_domain'] == 'GUI_FORM'
        assert result['technology_stack'] == 'React+Redux'
        assert result['playbook_id'] == draft_playbook.id

    @pytest.mark.asyncio
    async def test_mcp_sk_01_version_incremented(self, setup_user_context, draft_playbook):
        """Verify parent playbook version incremented after skill creation."""
        old_version = Decimal(str(draft_playbook.version))
        await create_skill(playbook_id=draft_playbook.id, title='SK1')
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_sk_02_empty_title_raises(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-02 Create skill with empty title raises error."""
        with pytest.raises(ValueError):
            await create_skill(playbook_id=draft_playbook.id, title='')

    @pytest.mark.asyncio
    async def test_mcp_sk_03_released_playbook_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-SK-03 Create skill in released playbook raises error."""
        with pytest.raises(PermissionError):
            await create_skill(playbook_id=released_playbook.id, title='SK1')


@pytest.mark.django_db(transaction=True)
class TestMCPSkillList:
    """MCP-SK-04 to MCP-SK-07: List skill scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_04_list_skills(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-04 List skills for playbook."""
        await create_skill(playbook_id=draft_playbook.id, title='SK1', capability_domain='GUI_FORM')
        await create_skill(playbook_id=draft_playbook.id, title='SK2', capability_domain='API_CRUD')
        await create_skill(playbook_id=draft_playbook.id, title='SK3', capability_domain='GUI_FORM')

        result = await list_skills(playbook_id=draft_playbook.id)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_mcp_sk_05_filter_by_domain(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-05 List skills filtered by capability domain."""
        await create_skill(playbook_id=draft_playbook.id, title='SK1', capability_domain='GUI_FORM')
        await create_skill(playbook_id=draft_playbook.id, title='SK2', capability_domain='API_CRUD')

        result = await list_skills(playbook_id=draft_playbook.id, domain='GUI_FORM')
        assert len(result) == 1
        assert result[0]['capability_domain'] == 'GUI_FORM'

    @pytest.mark.asyncio
    async def test_mcp_sk_06_filter_by_stack(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-06 List skills filtered by technology stack."""
        await create_skill(playbook_id=draft_playbook.id, title='SK1', technology_stack='React+Redux')
        await create_skill(playbook_id=draft_playbook.id, title='SK2', technology_stack='Django+HTMX')

        result = await list_skills(playbook_id=draft_playbook.id, stack='React+Redux')
        assert len(result) == 1
        assert result[0]['technology_stack'] == 'React+Redux'

    @pytest.mark.asyncio
    async def test_mcp_sk_07_search(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-07 List skills with search query."""
        await create_skill(playbook_id=draft_playbook.id, title='Build Login Form')
        await create_skill(playbook_id=draft_playbook.id, title='API Authentication')

        result = await list_skills(playbook_id=draft_playbook.id, search='Login')
        assert len(result) == 1
        assert result[0]['title'] == 'Build Login Form'


@pytest.mark.django_db(transaction=True)
class TestMCPSkillGet:
    """MCP-SK-08: Get skill scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_08_get_skill_with_activity_count(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-SK-08 Get skill details with activity count."""
        wf, act1, act2 = workflow_with_activities
        created = await create_skill(
            playbook_id=draft_playbook.id, title='Build Login Form',
            capability_domain='GUI_FORM', technology_stack='React+Redux',
        )
        # Link both activities to this skill
        await link_skill_to_activity(act1.id, created['id'])
        await link_skill_to_activity(act2.id, created['id'])

        result = await get_skill(skill_id=created['id'])
        assert result['title'] == 'Build Login Form'
        assert result['capability_domain'] == 'GUI_FORM'
        assert result['activity_count'] == 2


@pytest.mark.django_db(transaction=True)
class TestMCPSkillUpdate:
    """MCP-SK-09 to MCP-SK-10: Update skill scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_09_update_skill(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-09 Update skill title and metadata."""
        created = await create_skill(
            playbook_id=draft_playbook.id, title='Build Login Form',
            capability_domain='GUI_FORM', technology_stack='React+Redux',
        )
        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = Decimal(str(draft_playbook.version))

        result = await update_skill(
            skill_id=created['id'],
            title='Build Auth Form',
            capability_domain='GUI_AUTH',
            technology_stack='React+Redux+Formik',
        )

        assert result['title'] == 'Build Auth Form'
        assert result['capability_domain'] == 'GUI_AUTH'
        assert result['technology_stack'] == 'React+Redux+Formik'

        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_sk_09b_update_skill_empty_title_raises_value_error(
        self, setup_user_context, draft_playbook,
    ):
        """Updating a skill to an empty title raises ValueError (service ValidationError normalized)."""
        created = await create_skill(playbook_id=draft_playbook.id, title='Valid Title')
        with pytest.raises(ValueError, match='title'):
            await update_skill(skill_id=created['id'], title='')

    @pytest.mark.asyncio
    async def test_mcp_sk_10_update_released_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-SK-10 Update skill in released playbook raises error."""
        skill = await sync_to_async(Skill.objects.create)(
            playbook=released_playbook, title='SK1',
        )
        with pytest.raises(PermissionError):
            await update_skill(skill_id=skill.id, title='Updated')


@pytest.mark.django_db(transaction=True)
class TestMCPSkillDelete:
    """MCP-SK-11 to MCP-SK-12: Delete skill scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_11_delete_skill_clears_fks(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-SK-11 Delete skill clears activity FKs."""
        wf, act1, act2 = workflow_with_activities
        created = await create_skill(playbook_id=draft_playbook.id, title='SK1')
        await link_skill_to_activity(act1.id, created['id'])
        await link_skill_to_activity(act2.id, created['id'])

        await sync_to_async(draft_playbook.refresh_from_db)()
        old_version = Decimal(str(draft_playbook.version))

        result = await delete_skill(skill_id=created['id'])
        assert result['deleted'] is True

        # Verify activities have NULL skill FK
        await sync_to_async(act1.refresh_from_db)()
        await sync_to_async(act2.refresh_from_db)()
        assert act1.skill_id is None
        assert act2.skill_id is None

        # Verify version incremented
        await sync_to_async(draft_playbook.refresh_from_db)()
        assert draft_playbook.version == old_version + Decimal('0.1')

    @pytest.mark.asyncio
    async def test_mcp_sk_12_delete_released_raises(self, setup_user_context, released_playbook):
        """Scenario: MCP-SK-12 Delete skill in released playbook raises error."""
        skill = await sync_to_async(Skill.objects.create)(
            playbook=released_playbook, title='SK1',
        )
        with pytest.raises(PermissionError):
            await delete_skill(skill_id=skill.id)


@pytest.mark.django_db(transaction=True)
class TestMCPSkillLinkUnlink:
    """MCP-SK-13 to MCP-SK-15: Link/unlink scenarios."""

    @pytest.mark.asyncio
    async def test_mcp_sk_13_link_same_playbook(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-SK-13 Link skill to activity in same playbook."""
        wf, act1, act2 = workflow_with_activities
        created = await create_skill(playbook_id=draft_playbook.id, title='SK1')

        result = await link_skill_to_activity(act1.id, created['id'])
        assert result['skill_id'] == created['id']

    @pytest.mark.asyncio
    async def test_mcp_sk_14_link_cross_playbook_raises(self, setup_user_context, draft_playbook):
        """Scenario: MCP-SK-14 Link skill to activity in different playbook raises error."""
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
        created = await create_skill(playbook_id=draft_playbook.id, title='SK1')

        with pytest.raises(ValueError, match='same playbook'):
            await link_skill_to_activity(other_act.id, created['id'])

    @pytest.mark.asyncio
    async def test_mcp_sk_15_unlink(self, setup_user_context, draft_playbook, workflow_with_activities):
        """Scenario: MCP-SK-15 Unlink skill from activity."""
        wf, act1, act2 = workflow_with_activities
        created = await create_skill(playbook_id=draft_playbook.id, title='SK1')
        await link_skill_to_activity(act1.id, created['id'])

        result = await unlink_skill_from_activity(act1.id)
        assert result['skill_id'] is None
