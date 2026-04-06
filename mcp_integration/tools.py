"""
MCP Tool Definitions for Mimir.

Thin wrappers around existing service layer methods.
Adds: permission checks, user context, version incrementing.
"""
import logging
from typing import Literal
from decimal import Decimal
from fastmcp import FastMCP
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Mimir Methodology Assistant")


# Import user context management
from mcp_integration.context import get_current_user


# ============================================================================
# PLAYBOOK MCP TOOLS
# ============================================================================

async def create_playbook(name: str, description: str, category: str) -> dict:
    """
    Create draft playbook.
    
    Thin wrapper over PlaybookService.create_playbook().
    
    :param name: Playbook name. Example: "React Development"
    :param description: Description. Example: "Modern React patterns"
    :param category: Category. Example: "development"
    :return: Created playbook dict with id, name, version, status
    :raises ValueError: if name empty or duplicate
    
    Example:
        >>> result = create_playbook_tool(
        ...     name="React Dev",
        ...     description="React patterns",
        ...     category="development"
        ... )
        >>> result['status']
        'draft'
        >>> result['version']
        '0.1'
    """
    logger.info(f'MCP Tool: create_playbook called - name="{name}", category={category}')
    
    # Phase 5: Get user from MCP context
    user = await sync_to_async(get_current_user)()
    
    # Call existing service
    from methodology.services.playbook_service import PlaybookService
    playbook = await sync_to_async(PlaybookService.create_playbook)(
        name=name,
        description=description,
        category=category,
        author=user,
        status='draft'  # MCP always creates drafts
    )
    
    result = {
        'id': playbook.id,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'status': playbook.status,
        'version': str(playbook.version),
    }
    logger.info(f'MCP Tool: Created playbook id={playbook.id}, version={playbook.version}')
    return result


async def list_playbooks(status: Literal["draft", "released", "active", "all"] = "all") -> list:
    """
    List playbooks filtered by status.
    
    :param status: Filter by status or "all". Example: "draft"
    :return: List of playbook dicts
    """
    logger.info(f'MCP Tool: list_playbooks called - status={status}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.playbook_service import PlaybookService
    status_filter = None if status == "all" else status
    playbooks = await sync_to_async(PlaybookService.list_playbooks)(user, status=status_filter)
    
    result = [
        {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'category': p.category,
            'status': p.status,
            'version': str(p.version),
        }
        for p in playbooks
    ]
    logger.info(f'MCP Tool: Returning {len(result)} playbooks')
    return result


async def get_playbook(playbook_id: int) -> dict:
    """
    Get playbook details with workflows.
    
    :param playbook_id: Playbook ID. Example: 1
    :return: Playbook dict with nested workflows
    :raises ValueError: if not found or not owned by user
    """
    logger.info(f'MCP Tool: get_playbook called - id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.prefetch_related('workflows').get)(
            id=playbook_id,
            author=user
        )
    except Playbook.DoesNotExist:
        logger.error(f'MCP Tool: Playbook id={playbook_id} not found for user')
        raise ValueError(f'Playbook {playbook_id} not found')
    
    workflows = await sync_to_async(list)(playbook.workflows.all())
    result = {
        'id': playbook.id,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'status': playbook.status,
        'version': str(playbook.version),
        'workflows': [
            {
                'id': w.id,
                'name': w.name,
                'description': w.description,
                'order': w.order,
            }
            for w in workflows
        ]
    }
    logger.info(f'MCP Tool: Playbook has {len(result["workflows"])} workflows')
    return result


async def update_playbook(playbook_id: int, name: str = None,
                        description: str = None, category: str = None) -> dict:
    """
    Update DRAFT playbook. Auto-increments version.
    
    :param playbook_id: Playbook ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param category: New category or None
    :return: Updated playbook dict
    :raises PermissionError: if playbook is released
    :raises ValueError: if not found or not owned
    """
    logger.info(f'MCP Tool: update_playbook called - id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        logger.error(f'MCP Tool: Playbook id={playbook_id} not found for user')
        raise ValueError(f'Playbook {playbook_id} not found')
    
    # Permission check
    if playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot update released playbook id={playbook_id}')
        raise PermissionError(f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.')
    
    # Build update data
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if category is not None:
        update_data['category'] = category
    
    if update_data:
        from methodology.services.playbook_service import PlaybookService
        old_version = playbook.version
        
        # Update playbook
        playbook = await sync_to_async(PlaybookService.update_playbook)(playbook_id, **update_data)
        
        # Increment version
        playbook.version += Decimal('0.1')
        await sync_to_async(playbook.save)()
        
        logger.info(f'MCP Tool: Updated playbook, version {old_version} → {playbook.version}')
    
    return {
        'id': playbook.id,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'status': playbook.status,
        'version': str(playbook.version),
    }


async def delete_playbook(playbook_id: int) -> dict:
    """
    Delete DRAFT playbook (cascades to workflows/activities).
    
    :param playbook_id: Playbook ID. Example: 1
    :return: Confirmation dict
    :raises PermissionError: if playbook is released
    :raises ValueError: if not found or not owned
    """
    logger.info(f'MCP Tool: delete_playbook called - id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        logger.error(f'MCP Tool: Playbook id={playbook_id} not found for user')
        raise ValueError(f'Playbook {playbook_id} not found')
    
    # Permission check
    if playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot delete released playbook id={playbook_id}')
        raise PermissionError(f'Cannot delete released playbook "{playbook.name}"')
    
    playbook_name = playbook.name
    workflow_count = await sync_to_async(playbook.workflows.count)()
    
    from methodology.services.playbook_service import PlaybookService
    await sync_to_async(PlaybookService.delete_playbook)(playbook_id)
    
    logger.info(f'MCP Tool: Deleted playbook "{playbook_name}" with {workflow_count} workflows')
    return {'deleted': True, 'playbook_id': playbook_id}


# ============================================================================
# WORKFLOW MCP TOOLS
# ============================================================================

async def create_workflow(playbook_id: int, name: str, description: str = "") -> dict:
    """
    Create workflow in DRAFT playbook. Increments parent version.
    
    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Workflow name. Example: "Design Phase"
    :param description: Workflow description (optional)
    :return: Created workflow dict
    :raises PermissionError: if parent playbook is released
    :raises ValueError: if playbook not found or duplicate workflow name
    """
    logger.info(f'MCP Tool: create_workflow called - playbook_id={playbook_id}, name="{name}"')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        logger.error(f'MCP Tool: Playbook id={playbook_id} not found for user')
        raise ValueError(f'Playbook {playbook_id} not found')
    
    # Permission check
    if playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot add workflow to released playbook id={playbook_id}')
        raise PermissionError(f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.')
    
    # Call existing service
    from methodology.services.workflow_service import WorkflowService
    old_version = playbook.version
    workflow = await sync_to_async(WorkflowService.create_workflow)(playbook, name, description)
    
    # Increment parent version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()
    
    logger.info(f'MCP Tool: Created workflow id={workflow.id}, parent version {old_version} → {playbook.version}')
    
    return {
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'order': workflow.order,
        'playbook_id': playbook.id,
    }


async def list_workflows(playbook_id: int) -> list:
    """
    List workflows for playbook.
    
    :param playbook_id: Parent playbook ID. Example: 1
    :return: List of workflow dicts
    :raises ValueError: if playbook not found
    """
    logger.info(f'MCP Tool: list_workflows called - playbook_id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        logger.error(f'MCP Tool: Playbook id={playbook_id} not found for user')
        raise ValueError(f'Playbook {playbook_id} not found')
    
    from methodology.services.workflow_service import WorkflowService
    workflows = await sync_to_async(WorkflowService.get_workflows_for_playbook)(playbook_id)
    
    result = [
        {
            'id': w.id,
            'name': w.name,
            'description': w.description,
            'order': w.order,
            'playbook_id': w.playbook_id,
        }
        for w in workflows
    ]
    logger.info(f'MCP Tool: Returning {len(result)} workflows')
    return result


async def get_workflow(workflow_id: int) -> dict:
    """
    Get workflow details with activities.
    
    :param workflow_id: Workflow ID. Example: 1
    :return: Workflow dict with nested activities
    :raises ValueError: if not found or not owned
    """
    logger.info(f'MCP Tool: get_workflow called - id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Workflow
    try:
        workflow = await sync_to_async(Workflow.objects.prefetch_related('activities').get)(
            id=workflow_id,
            playbook__author=user
        )
    except Workflow.DoesNotExist:
        logger.error(f'MCP Tool: Workflow id={workflow_id} not found for user')
        raise ValueError(f'Workflow {workflow_id} not found')
    
    activities = await sync_to_async(list)(workflow.activities.all())
    result = {
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'order': workflow.order,
        'playbook_id': workflow.playbook_id,
        'activities': [
            {
                'id': a.id,
                'name': a.name,
                'order': a.order,
            }
            for a in activities
        ]
    }
    logger.info(f'MCP Tool: Workflow has {len(result["activities"])} activities')
    return result


async def update_workflow(workflow_id: int, name: str = None,
                        description: str = None, order: int = None) -> dict:
    """
    Update workflow in DRAFT playbook. Increments parent version.
    
    :param workflow_id: Workflow ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param order: New order or None
    :return: Updated workflow dict
    :raises PermissionError: if parent playbook is released
    :raises ValueError: if not found
    """
    logger.info(f'MCP Tool: update_workflow called - id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Workflow
    try:
        workflow = await sync_to_async(Workflow.objects.select_related('playbook').get)(
            id=workflow_id,
            playbook__author=user
        )
    except Workflow.DoesNotExist:
        logger.error(f'MCP Tool: Workflow id={workflow_id} not found for user')
        raise ValueError(f'Workflow {workflow_id} not found')
    
    # Permission check
    if workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot update workflow in released playbook')
        raise PermissionError(f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.')
    
    # Build update data
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if description is not None:
        update_data['description'] = description
    if order is not None:
        update_data['order'] = order
    
    if update_data:
        from methodology.services.workflow_service import WorkflowService
        old_version = workflow.playbook.version
        
        # Update workflow
        workflow = await sync_to_async(WorkflowService.update_workflow)(workflow_id, **update_data)
        
        # Increment parent version
        workflow.playbook.version += Decimal('0.1')
        await sync_to_async(workflow.playbook.save)()
        
        logger.info(f'MCP Tool: Updated workflow, parent version {old_version} → {workflow.playbook.version}')
    
    return {
        'id': workflow.id,
        'name': workflow.name,
        'description': workflow.description,
        'order': workflow.order,
        'playbook_id': workflow.playbook_id,
    }


async def delete_workflow(workflow_id: int) -> dict:
    """
    Delete workflow in DRAFT playbook. Increments parent version.
    
    :param workflow_id: Workflow ID. Example: 1
    :return: Confirmation dict
    :raises PermissionError: if parent playbook is released
    :raises ValueError: if not found
    """
    logger.info(f'MCP Tool: delete_workflow called - id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Workflow
    try:
        workflow = await sync_to_async(Workflow.objects.select_related('playbook').get)(
            id=workflow_id,
            playbook__author=user
        )
    except Workflow.DoesNotExist:
        logger.error(f'MCP Tool: Workflow id={workflow_id} not found for user')
        raise ValueError(f'Workflow {workflow_id} not found')
    
    # Permission check
    if workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot delete workflow in released playbook')
        raise PermissionError(f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.')
    
    workflow_name = workflow.name
    playbook = workflow.playbook
    activity_count = await sync_to_async(workflow.activities.count)()
    old_version = playbook.version
    
    from methodology.services.workflow_service import WorkflowService
    await sync_to_async(WorkflowService.delete_workflow)(workflow_id)
    
    # Increment parent version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()
    
    logger.info(f'MCP Tool: Deleted workflow "{workflow_name}" ({activity_count} activities), parent version {old_version} → {playbook.version}')
    return {'deleted': True, 'workflow_id': workflow_id}


# ============================================================================
# ACTIVITY MCP TOOLS
# ============================================================================

async def create_activity(workflow_id: int, name: str, guidance: str = "",
                        phase: str = None, predecessor_id: int = None) -> dict:
    """
    Create activity in workflow (DRAFT playbook). Increments grandparent version.
    
    :param workflow_id: Parent workflow ID. Example: 1
    :param name: Activity name. Example: "Design Component"
    :param guidance: Rich Markdown guidance (optional)
    :param phase: Phase grouping (optional)
    :param predecessor_id: Predecessor activity ID (optional, must be in same workflow)
    :return: Created activity dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if workflow not found or validation fails
    """
    logger.info(f'MCP Tool: create_activity called - workflow_id={workflow_id}, name="{name}"')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Workflow, Activity
    try:
        workflow = await sync_to_async(Workflow.objects.select_related('playbook').get)(
            id=workflow_id,
            playbook__author=user
        )
    except Workflow.DoesNotExist:
        logger.error(f'MCP Tool: Workflow id={workflow_id} not found for user')
        raise ValueError(f'Workflow {workflow_id} not found')
    
    # Permission check on grandparent playbook
    if workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot add activity to workflow in released playbook')
        raise PermissionError(f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.')
    
    # Get predecessor if specified
    predecessor = None
    if predecessor_id:
        try:
            predecessor = await sync_to_async(Activity.objects.get)(id=predecessor_id, workflow=workflow)
        except Activity.DoesNotExist:
            logger.error(f'MCP Tool: Predecessor id={predecessor_id} not found in workflow {workflow_id}')
            raise ValueError(f'Predecessor activity {predecessor_id} not found in workflow')
    
    # Call existing service
    from methodology.services.activity_service import ActivityService
    old_version = workflow.playbook.version
    activity = await sync_to_async(ActivityService.create_activity)(
        workflow=workflow,
        name=name,
        guidance=guidance,
        phase=phase,
        predecessor=predecessor
    )
    
    # Increment grandparent version
    workflow.playbook.version += Decimal('0.1')
    await sync_to_async(workflow.playbook.save)()
    
    logger.info(f'MCP Tool: Created activity id={activity.id}, grandparent version {old_version} → {workflow.playbook.version}')
    
    return {
        'id': activity.id,
        'name': activity.name,
        'guidance': activity.guidance,
        'phase': activity.phase,
        'order': activity.order,
        'workflow_id': workflow.id,
        'predecessor_id': predecessor.id if predecessor else None,
    }


async def list_activities(workflow_id: int) -> list:
    """
    List activities for workflow.
    
    :param workflow_id: Parent workflow ID. Example: 1
    :return: List of activity dicts
    :raises ValueError: if workflow not found
    """
    logger.info(f'MCP Tool: list_activities called - workflow_id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Workflow
    try:
        workflow = await sync_to_async(Workflow.objects.get)(id=workflow_id, playbook__author=user)
    except Workflow.DoesNotExist:
        logger.error(f'MCP Tool: Workflow id={workflow_id} not found for user')
        raise ValueError(f'Workflow {workflow_id} not found')
    
    from methodology.services.activity_service import ActivityService
    activities = await sync_to_async(ActivityService.get_activities_for_workflow)(workflow_id)
    
    result = [
        {
            'id': a.id,
            'name': a.name,
            'guidance': a.guidance,
            'phase': a.phase,
            'order': a.order,
            'workflow_id': a.workflow_id,
            'predecessor_id': a.predecessor_id,
            'successor_id': a.successor_id,
        }
        for a in activities
    ]
    logger.info(f'MCP Tool: Returning {len(result)} activities')
    return result


async def get_activity(activity_id: int) -> dict:
    """
    Get activity details with dependencies.
    
    Tracks activity access by updating last_accessed_at timestamp for
    the "Recently Used" dashboard section.
    
    :param activity_id: Activity ID. Example: 1
    :return: Activity dict with predecessor/successor info
    :raises ValueError: if not found or not owned
    """
    logger.info(f'MCP Tool: get_activity called - id={activity_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Activity
    try:
        activity = await sync_to_async(Activity.objects.select_related(
            'predecessor', 'successor', 'workflow__playbook'
        ).get)(
            id=activity_id,
            workflow__playbook__author=user
        )
    except Activity.DoesNotExist:
        logger.error(f'MCP Tool: Activity id={activity_id} not found for user')
        raise ValueError(f'Activity {activity_id} not found')
    
    # Track access for "Recently Used" dashboard section
    # Non-critical operation - log errors but don't fail the request
    try:
        from methodology.services.activity_service import ActivityService
        await sync_to_async(ActivityService.touch_activity_access)(activity_id)
    except Exception as e:
        logger.warning(f'Failed to track access for activity {activity_id}: {e}')
        # Continue - access tracking is non-critical
    
    result = {
        'id': activity.id,
        'name': activity.name,
        'guidance': activity.guidance,
        'phase': activity.phase,
        'order': activity.order,
        'workflow_id': activity.workflow_id,
        'predecessor': {
            'id': activity.predecessor.id,
            'name': activity.predecessor.name,
        } if activity.predecessor else None,
        'successor': {
            'id': activity.successor.id,
            'name': activity.successor.name,
        } if activity.successor else None,
    }
    logger.info(f'MCP Tool: Activity with predecessor={activity.predecessor_id}, successor={activity.successor_id}')
    return result


async def update_activity(activity_id: int, name: str = None, guidance: str = None,
                        phase: str = None, order: int = None) -> dict:
    """
    Update activity in DRAFT playbook. Increments grandparent version.
    
    Note: Use set_predecessor_tool() to change dependencies.
    
    :param activity_id: Activity ID. Example: 1
    :param name: New name or None
    :param guidance: New guidance or None
    :param phase: New phase or None
    :param order: New order or None
    :return: Updated activity dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if not found
    """
    logger.info(f'MCP Tool: update_activity called - id={activity_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Activity
    try:
        activity = await sync_to_async(Activity.objects.select_related('workflow__playbook').get)(
            id=activity_id,
            workflow__playbook__author=user
        )
    except Activity.DoesNotExist:
        logger.error(f'MCP Tool: Activity id={activity_id} not found for user')
        raise ValueError(f'Activity {activity_id} not found')
    
    # Permission check
    if activity.workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot update activity in released playbook')
        raise PermissionError(f'Cannot modify released playbook. Use create_pip instead.')
    
    # Build update data
    update_data = {}
    if name is not None:
        update_data['name'] = name
    if guidance is not None:
        update_data['guidance'] = guidance
    if phase is not None:
        update_data['phase'] = phase
    if order is not None:
        update_data['order'] = order
    
    if update_data:
        from methodology.services.activity_service import ActivityService
        old_version = activity.workflow.playbook.version
        
        # Update activity
        activity = await sync_to_async(ActivityService.update_activity)(activity_id, **update_data)
        
        # Increment grandparent version
        activity.workflow.playbook.version += Decimal('0.1')
        await sync_to_async(activity.workflow.playbook.save)()
        
        logger.info(f'MCP Tool: Updated activity, grandparent version {old_version} → {activity.workflow.playbook.version}')
    
    return {
        'id': activity.id,
        'name': activity.name,
        'guidance': activity.guidance,
        'phase': activity.phase,
        'order': activity.order,
        'workflow_id': activity.workflow_id,
    }


async def delete_activity(activity_id: int) -> dict:
    """
    Delete activity in DRAFT playbook. Increments grandparent version.
    
    :param activity_id: Activity ID. Example: 1
    :return: Confirmation dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if not found
    """
    logger.info(f'MCP Tool: delete_activity called - id={activity_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Activity
    try:
        activity = await sync_to_async(Activity.objects.select_related('workflow__playbook').get)(
            id=activity_id,
            workflow__playbook__author=user
        )
    except Activity.DoesNotExist:
        logger.error(f'MCP Tool: Activity id={activity_id} not found for user')
        raise ValueError(f'Activity {activity_id} not found')
    
    # Permission check
    if activity.workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot delete activity in released playbook')
        raise PermissionError(f'Cannot modify released playbook. Use create_pip instead.')
    
    activity_name = activity.name
    playbook = activity.workflow.playbook
    old_version = playbook.version
    
    from methodology.services.activity_service import ActivityService
    await sync_to_async(ActivityService.delete_activity)(activity_id)
    
    # Increment grandparent version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()
    
    logger.info(f'MCP Tool: Deleted activity "{activity_name}", grandparent version {old_version} → {playbook.version}')
    return {'deleted': True, 'activity_id': activity_id}


async def set_predecessor(activity_id: int, predecessor_id: int) -> dict:
    """
    Set activity predecessor (validates no circular dependencies).
    
    :param activity_id: Activity ID. Example: 2
    :param predecessor_id: Predecessor activity ID. Example: 1
    :return: Updated activity dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if validation fails or circular dependency detected
    """
    logger.info(f'MCP Tool: set_predecessor called - activity_id={activity_id}, predecessor_id={predecessor_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.models import Activity
    try:
        activity = await sync_to_async(Activity.objects.select_related('workflow__playbook').get)(
            id=activity_id,
            workflow__playbook__author=user
        )
        predecessor = await sync_to_async(Activity.objects.get)(id=predecessor_id, workflow=activity.workflow)
    except Activity.DoesNotExist as e:
        logger.error(f'MCP Tool: Activity not found or not in same workflow')
        raise ValueError('Activity or predecessor not found') from e
    
    # Permission check
    if activity.workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot modify dependencies in released playbook')
        raise PermissionError(f'Cannot modify released playbook. Use create_pip instead.')
    
    # Call service (validates circular dependencies)
    from methodology.services.activity_service import ActivityService
    old_version = activity.workflow.playbook.version
    await sync_to_async(ActivityService.set_predecessor)(activity, predecessor)
    
    # Increment grandparent version
    activity.workflow.playbook.version += Decimal('0.1')
    await sync_to_async(activity.workflow.playbook.save)()
    
    logger.info(f'MCP Tool: Set predecessor, grandparent version {old_version} → {activity.workflow.playbook.version}')
    
    return {
        'activity_id': activity.id,
        'predecessor_id': predecessor.id,
        'updated': True,
    }


# Phase 5: Register all tools with FastMCP
# Phase 5: Add initialize_mcp() function
# Phase 5: Add user context management


# ============================================================================
# WORKFLOW EXPORT/IMPORT MCP TOOLS
# ============================================================================

async def export_workflow_to_local(
    workflow_id: int,
    target_directory: str = ".windsurf/workflows",
    folder_name: str = None
) -> dict:
    """
    Export workflow to local AI workspace as markdown files.
    
    :param workflow_id: Workflow ID. Example: 42
    :param target_directory: Target directory. Example: ".windsurf/workflows"
    :param folder_name: Folder name. Example: "FFE" (defaults to workflow slug)
    :return: Export result with file paths and counts
    """
    logger.info(f'MCP Tool: export_workflow_to_local called - workflow_id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.workflow_export_service import WorkflowExportService
    result = await sync_to_async(WorkflowExportService.export_workflow_to_markdown)(
        workflow_id=workflow_id,
        target_directory=target_directory,
        folder_name=folder_name
    )
    
    logger.info(f'MCP Tool: Exported workflow {workflow_id} to {result["export_path"]}')
    return result


async def import_workflow_from_local(
    workflow_id: int,
    source_directory: str,
    auto_apply: bool = False
) -> dict:
    """
    Import workflow from local markdown files with change detection.
    
    :param workflow_id: Workflow ID. Example: 42
    :param source_directory: Source directory. Example: ".windsurf/workflows/FFE"
    :param auto_apply: Auto-apply for draft playbooks. Example: False
    :return: Change detection result with protocol path
    """
    logger.info(f'MCP Tool: import_workflow_from_local called - workflow_id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.workflow_import_service import WorkflowImportService
    result = await sync_to_async(WorkflowImportService.import_workflow_from_markdown)(
        workflow_id=workflow_id,
        source_directory=source_directory
    )
    
    if auto_apply and result['playbook_status'] == 'draft':
        from methodology.services.workflow_protocol_service import WorkflowProtocolService
        import os
        protocol_file = os.path.join(source_directory, '_Upload_Protocol.md')
        apply_result = await sync_to_async(WorkflowProtocolService.apply_upload_protocol)(
            protocol_file=protocol_file
        )
        result['auto_applied'] = True
        result['apply_result'] = apply_result
    
    logger.info(f'MCP Tool: Imported workflow {workflow_id}, changes detected: {result["changes_count"]}')
    return result


async def apply_upload_protocol(protocol_file: str) -> dict:
    """
    Apply upload protocol to draft playbook.
    
    :param protocol_file: Path to _Upload_Protocol.md
    :return: Application result with change counts
    """
    logger.info(f'MCP Tool: apply_upload_protocol called - protocol_file={protocol_file}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.workflow_protocol_service import WorkflowProtocolService
    result = await sync_to_async(WorkflowProtocolService.apply_upload_protocol)(
        protocol_file=protocol_file
    )
    
    logger.info(f'MCP Tool: Applied protocol, changes: {result["changes_applied"]}')
    return result


async def create_pip_from_protocol(protocol_file: str, pip_title: str) -> dict:
    """
    Create PIP from upload protocol for released playbook.
    
    :param protocol_file: Path to _Upload_Protocol.md
    :param pip_title: PIP title. Example: "Improve workflow"
    :return: Created PIP dict with ID and status
    """
    logger.info(f'MCP Tool: create_pip_from_protocol called - pip_title={pip_title}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.workflow_protocol_service import WorkflowProtocolService
    result = await sync_to_async(WorkflowProtocolService.create_pip_from_protocol)(
        protocol_file=protocol_file,
        pip_title=pip_title
    )
    
    logger.info(f'MCP Tool: Created PIP {result["pip_id"]}')
    return result

# ============================================================================
# SKILL MCP TOOLS
# ============================================================================

async def create_skill(
    playbook_id: int,
    title: str,
    content: str = '',
    capability_domain: str = '',
    technology_stack: str = '',
) -> dict:
    """
    Create skill in draft playbook. Increments parent version.

    :param playbook_id: Parent playbook ID. Example: 1
    :param title: Skill title (required). Example: "Build Login Form"
    :param content: Markdown content (optional). Example: "## Steps\\n1. ..."
    :param capability_domain: What capability (optional). Example: "GUI_FORM"
    :param technology_stack: Tech stack (optional). Example: "React+Redux"
    :return: Created skill dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If playbook not found or validation fails
    """
    logger.info(f'MCP Tool: create_skill called - playbook_id={playbook_id}, title="{title}"')

    user = await sync_to_async(get_current_user)()
    playbook = await _get_draft_playbook(playbook_id, user)

    from methodology.services.skill_service import SkillService
    skill = await sync_to_async(SkillService.create_skill)(
        playbook=playbook,
        title=title,
        content=content,
        capability_domain=capability_domain,
        technology_stack=technology_stack,
    )

    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Created skill id={skill.id}, version {old_version} → {playbook.version}')
    return {
        'id': skill.id,
        'title': skill.title,
        'content': skill.content,
        'capability_domain': skill.capability_domain,
        'technology_stack': skill.technology_stack,
        'playbook_id': playbook.id,
    }


async def list_skills(
    playbook_id: int,
    domain: str = '',
    stack: str = '',
    search: str = '',
) -> list:
    """
    List skills for playbook with optional filters.

    :param playbook_id: Playbook ID. Example: 1
    :param domain: Filter by capability_domain. Example: "GUI_FORM"
    :param stack: Filter by technology_stack. Example: "React+Redux"
    :param search: Free-text search. Example: "login"
    :return: List of skill dicts
    :raises ValueError: If playbook not found
    """
    logger.info(f'MCP Tool: list_skills called - playbook_id={playbook_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Playbook
    try:
        await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        raise ValueError(f'Playbook {playbook_id} not found')

    from methodology.services.skill_service import SkillService
    skills = await sync_to_async(list)(
        await sync_to_async(SkillService.list_skills_for_playbook)(
            playbook_id=playbook_id,
            capability_domain=domain,
            technology_stack=stack,
            search=search,
        )
    )

    result = [
        {
            'id': s.id,
            'title': s.title,
            'capability_domain': s.capability_domain,
            'technology_stack': s.technology_stack,
            'activity_count': s.activity_count,
            'playbook_id': playbook_id,
        }
        for s in skills
    ]
    logger.info(f'MCP Tool: Listed {len(result)} skills for playbook {playbook_id}')
    return result


async def get_skill(skill_id: int) -> dict:
    """
    Get skill details with activity count.

    :param skill_id: Skill ID. Example: 1
    :return: Skill dict with activity_count
    :raises ValueError: If skill not found or not owned
    """
    logger.info(f'MCP Tool: get_skill called - skill_id={skill_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.skill_service import SkillService
    try:
        skill = await sync_to_async(SkillService.get_skill)(skill_id)
    except Exception:
        raise ValueError(f'Skill {skill_id} not found')

    if skill.playbook.author_id != user.id:
        raise ValueError(f'Skill {skill_id} not found')

    activity_count = await sync_to_async(skill.activities.count)()

    return {
        'id': skill.id,
        'title': skill.title,
        'content': skill.content,
        'capability_domain': skill.capability_domain,
        'technology_stack': skill.technology_stack,
        'playbook_id': skill.playbook_id,
        'activity_count': activity_count,
    }


async def update_skill(
    skill_id: int,
    title: str = None,
    content: str = None,
    capability_domain: str = None,
    technology_stack: str = None,
) -> dict:
    """
    Update skill in draft playbook. Increments parent version.

    :param skill_id: Skill ID. Example: 1
    :param title: New title (optional). Example: "Build Auth Form"
    :param content: New content (optional)
    :param capability_domain: New domain (optional). Example: "GUI_AUTH"
    :param technology_stack: New stack (optional). Example: "React+Formik"
    :return: Updated skill dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If skill not found or validation fails
    """
    logger.info(f'MCP Tool: update_skill called - skill_id={skill_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.skill_service import SkillService
    skill = await sync_to_async(SkillService.get_skill)(skill_id)

    if skill.playbook.author_id != user.id:
        raise ValueError(f'Skill {skill_id} not found')
    if skill.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{skill.playbook.name}".')

    kwargs = {}
    if title is not None:
        kwargs['title'] = title
    if content is not None:
        kwargs['content'] = content
    if capability_domain is not None:
        kwargs['capability_domain'] = capability_domain
    if technology_stack is not None:
        kwargs['technology_stack'] = technology_stack

    updated = await sync_to_async(SkillService.update_skill)(skill_id, **kwargs)

    old_version = skill.playbook.version
    skill.playbook.version += Decimal('0.1')
    await sync_to_async(skill.playbook.save)()

    logger.info(f'MCP Tool: Updated skill {skill_id}, version {old_version} → {skill.playbook.version}')
    return {
        'id': updated.id,
        'title': updated.title,
        'content': updated.content,
        'capability_domain': updated.capability_domain,
        'technology_stack': updated.technology_stack,
        'playbook_id': updated.playbook_id,
    }


async def delete_skill(skill_id: int) -> dict:
    """
    Delete skill in draft playbook. Increments parent version. Activity FKs cleared.

    :param skill_id: Skill ID. Example: 1
    :return: Dict with deleted=True
    :raises PermissionError: If playbook is released
    :raises ValueError: If skill not found or not owned
    """
    logger.info(f'MCP Tool: delete_skill called - skill_id={skill_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.skill_service import SkillService
    skill = await sync_to_async(SkillService.get_skill)(skill_id)

    if skill.playbook.author_id != user.id:
        raise ValueError(f'Skill {skill_id} not found')
    if skill.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{skill.playbook.name}".')

    playbook = skill.playbook
    old_version = playbook.version

    await sync_to_async(SkillService.delete_skill)(skill_id)

    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Deleted skill {skill_id}, version {old_version} → {playbook.version}')
    return {'deleted': True, 'skill_id': skill_id}


async def link_skill_to_activity(activity_id: int, skill_id: int) -> dict:
    """
    Link a skill to an activity. Both must be in the same playbook.

    :param activity_id: Activity ID. Example: 1
    :param skill_id: Skill ID. Example: 5
    :return: Dict with updated activity_id and skill_id
    :raises ValueError: If not found or cross-playbook
    """
    logger.info(f'MCP Tool: link_skill_to_activity called - activity_id={activity_id}, skill_id={skill_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService
    from methodology.models import Activity, Skill

    activity = await sync_to_async(
        Activity.objects.select_related('workflow__playbook').get
    )(pk=activity_id)
    if activity.workflow.playbook.author_id != user.id:
        raise ValueError(f'Activity {activity_id} not found')
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    updated = await sync_to_async(ActivityService.set_activity_skill)(activity_id, skill_id)

    return {'activity_id': updated.id, 'skill_id': updated.skill_id}


async def unlink_skill_from_activity(activity_id: int) -> dict:
    """
    Unlink skill from an activity (set FK to NULL).

    :param activity_id: Activity ID. Example: 1
    :return: Dict with updated activity_id and skill_id=None
    :raises ValueError: If activity not found or not owned
    """
    logger.info(f'MCP Tool: unlink_skill_from_activity called - activity_id={activity_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService
    from methodology.models import Activity

    activity = await sync_to_async(
        Activity.objects.select_related('workflow__playbook').get
    )(pk=activity_id)
    if activity.workflow.playbook.author_id != user.id:
        raise ValueError(f'Activity {activity_id} not found')
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    updated = await sync_to_async(ActivityService.clear_activity_skill)(activity_id)

    return {'activity_id': updated.id, 'skill_id': None}


# ============================================================================
# AGENT MCP TOOLS
# ============================================================================

async def create_agent(
    playbook_id: int,
    name: str,
    description: str = '',
) -> dict:
    """
    Create agent in draft playbook. Increments parent version.

    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Agent name (required, unique per playbook). Example: "Code Reviewer"
    :param description: Description (optional). Example: "Reviews PRs"
    :return: Created agent dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If playbook not found or validation fails
    """
    logger.info(f'MCP Tool: create_agent called - playbook_id={playbook_id}, name="{name}"')

    user = await sync_to_async(get_current_user)()
    playbook = await _get_draft_playbook(playbook_id, user)

    from methodology.services.agent_service import AgentService
    agent = await sync_to_async(AgentService.create_agent)(
        playbook=playbook,
        name=name,
        description=description,
    )

    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Created agent id={agent.id}, version {old_version} → {playbook.version}')
    return {
        'id': agent.id,
        'name': agent.name,
        'description': agent.description,
        'playbook_id': playbook.id,
    }


async def list_agents(
    playbook_id: int,
    search: str = '',
) -> list:
    """
    List agents for playbook with optional search.

    :param playbook_id: Playbook ID. Example: 1
    :param search: Free-text search. Example: "reviewer"
    :return: List of agent dicts
    :raises ValueError: If playbook not found
    """
    logger.info(f'MCP Tool: list_agents called - playbook_id={playbook_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Playbook
    try:
        await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        raise ValueError(f'Playbook {playbook_id} not found')

    from methodology.services.agent_service import AgentService
    from django.db.models import Count, Q

    qs = await sync_to_async(AgentService.list_agents_for_playbook)(playbook_id)

    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(description__icontains=search))

    qs = qs.annotate(activity_count=Count('activities'))
    agents = await sync_to_async(list)(qs)

    result = [
        {
            'id': a.id,
            'name': a.name,
            'description': a.description,
            'activity_count': a.activity_count,
            'playbook_id': playbook_id,
        }
        for a in agents
    ]
    logger.info(f'MCP Tool: Listed {len(result)} agents for playbook {playbook_id}')
    return result


async def get_agent(agent_id: int) -> dict:
    """
    Get agent details with activity count.

    :param agent_id: Agent ID. Example: 1
    :return: Agent dict with activity_count
    :raises ValueError: If agent not found or not owned
    """
    logger.info(f'MCP Tool: get_agent called - agent_id={agent_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.agent_service import AgentService
    try:
        agent = await sync_to_async(AgentService.get_agent)(agent_id)
    except Exception:
        raise ValueError(f'Agent {agent_id} not found')

    if agent.playbook.author_id != user.id:
        raise ValueError(f'Agent {agent_id} not found')

    activity_count = await sync_to_async(agent.activities.count)()

    return {
        'id': agent.id,
        'name': agent.name,
        'description': agent.description,
        'playbook_id': agent.playbook_id,
        'activity_count': activity_count,
    }


async def update_agent(
    agent_id: int,
    name: str = None,
    description: str = None,
) -> dict:
    """
    Update agent in draft playbook. Increments parent version.

    :param agent_id: Agent ID. Example: 1
    :param name: New name (optional). Example: "Senior Reviewer"
    :param description: New description (optional)
    :return: Updated agent dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If agent not found or validation fails
    """
    logger.info(f'MCP Tool: update_agent called - agent_id={agent_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.agent_service import AgentService
    agent = await sync_to_async(AgentService.get_agent)(agent_id)

    if agent.playbook.author_id != user.id:
        raise ValueError(f'Agent {agent_id} not found')
    if agent.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{agent.playbook.name}".')

    kwargs = {}
    if name is not None:
        kwargs['name'] = name
    if description is not None:
        kwargs['description'] = description

    updated = await sync_to_async(AgentService.update_agent)(agent_id, **kwargs)

    old_version = agent.playbook.version
    agent.playbook.version += Decimal('0.1')
    await sync_to_async(agent.playbook.save)()

    logger.info(f'MCP Tool: Updated agent {agent_id}, version {old_version} → {agent.playbook.version}')
    return {
        'id': updated.id,
        'name': updated.name,
        'description': updated.description,
        'playbook_id': updated.playbook_id,
    }


async def delete_agent(agent_id: int) -> dict:
    """
    Delete agent in draft playbook. Increments parent version. Activity FKs cleared.

    :param agent_id: Agent ID. Example: 1
    :return: Dict with deleted=True
    :raises PermissionError: If playbook is released
    :raises ValueError: If agent not found or not owned
    """
    logger.info(f'MCP Tool: delete_agent called - agent_id={agent_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.agent_service import AgentService
    agent = await sync_to_async(AgentService.get_agent)(agent_id)

    if agent.playbook.author_id != user.id:
        raise ValueError(f'Agent {agent_id} not found')
    if agent.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{agent.playbook.name}".')

    playbook = agent.playbook
    old_version = playbook.version

    await sync_to_async(AgentService.delete_agent)(agent_id)

    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Deleted agent {agent_id}, version {old_version} → {playbook.version}')
    return {'deleted': True, 'agent_id': agent_id}


async def link_agent_to_activity(activity_id: int, agent_id: int) -> dict:
    """
    Link an agent to an activity. Both must be in the same playbook.

    :param activity_id: Activity ID. Example: 1
    :param agent_id: Agent ID. Example: 3
    :return: Dict with updated activity_id and agent_id
    :raises ValueError: If not found or cross-playbook
    """
    logger.info(f'MCP Tool: link_agent_to_activity called - activity_id={activity_id}, agent_id={agent_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService
    from methodology.models import Activity

    activity = await sync_to_async(
        Activity.objects.select_related('workflow__playbook').get
    )(pk=activity_id)
    if activity.workflow.playbook.author_id != user.id:
        raise ValueError(f'Activity {activity_id} not found')
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    updated = await sync_to_async(ActivityService.set_activity_agent)(activity_id, agent_id)

    return {'activity_id': updated.id, 'agent_id': updated.agent_id}


async def unlink_agent_from_activity(activity_id: int) -> dict:
    """
    Unlink agent from an activity (set FK to NULL).

    :param activity_id: Activity ID. Example: 1
    :return: Dict with updated activity_id and agent_id=None
    :raises ValueError: If activity not found or not owned
    """
    logger.info(f'MCP Tool: unlink_agent_from_activity called - activity_id={activity_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService
    from methodology.models import Activity

    activity = await sync_to_async(
        Activity.objects.select_related('workflow__playbook').get
    )(pk=activity_id)
    if activity.workflow.playbook.author_id != user.id:
        raise ValueError(f'Activity {activity_id} not found')
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    updated = await sync_to_async(ActivityService.clear_activity_agent)(activity_id)

    return {'activity_id': updated.id, 'agent_id': None}



# ============================================================================
# ARTIFACT MCP TOOLS
# ============================================================================

async def create_artifact(
    playbook_id: int,
    produced_by_id: int,
    name: str,
    description: str = '',
    type: str = 'Document',
    is_required: bool = False,
) -> dict:
    """
    Create artifact in draft playbook. Increments parent version.

    :param playbook_id: Parent playbook ID. Example: 1
    :param produced_by_id: Activity ID that produces this artifact. Example: 5
    :param name: Artifact name (required). Example: "API Specification"
    :param description: Description (optional). Example: "REST API contract"
    :param type: Artifact type. Example: "Document"
    :param is_required: Whether required. Example: True
    :return: Created artifact dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If playbook or activity not found
    :raises ValidationError: If validation fails
    """
    logger.info(
        f'MCP Tool: create_artifact called - playbook_id={playbook_id}, '
        f'produced_by_id={produced_by_id}, name="{name}"'
    )

    user = await sync_to_async(get_current_user)()
    playbook = await _get_draft_playbook(playbook_id, user)

    from methodology.models import Activity
    try:
        produced_by = await sync_to_async(
            Activity.objects.select_related('workflow').get
        )(pk=produced_by_id, workflow__playbook=playbook)
    except Activity.DoesNotExist:
        raise ValueError(
            f'Activity {produced_by_id} not found in playbook {playbook_id}'
        )

    from methodology.services.artifact_service import ArtifactService
    artifact = await sync_to_async(ArtifactService.create_artifact)(
        playbook=playbook,
        produced_by=produced_by,
        name=name,
        description=description,
        type=type,
        is_required=is_required,
    )

    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(
        f'MCP Tool: Created artifact id={artifact.id}, '
        f'version {old_version} → {playbook.version}'
    )
    return {
        'id': artifact.id,
        'name': artifact.name,
        'description': artifact.description,
        'type': artifact.type,
        'is_required': artifact.is_required,
        'produced_by_id': artifact.produced_by_id,
        'consumer_count': 0,
        'playbook_id': playbook.id,
    }


async def list_artifacts(
    playbook_id: int,
    search: str = '',
    type_filter: str = '',
    required_filter: str = '',
) -> list:
    """
    List artifacts for playbook with optional filters.

    :param playbook_id: Playbook ID. Example: 1
    :param search: Free-text search in name/description. Example: "API"
    :param type_filter: Filter by type. Example: "Document"
    :param required_filter: Filter by required ("true"/"false"). Example: "true"
    :return: List of artifact dicts
    :raises ValueError: If playbook not found
    """
    logger.info(f'MCP Tool: list_artifacts called - playbook_id={playbook_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(
            id=playbook_id, author=user,
        )
    except Playbook.DoesNotExist:
        raise ValueError(f'Playbook {playbook_id} not found')

    required = _parse_required_filter(required_filter)

    from methodology.services.artifact_service import ArtifactService
    artifacts = await sync_to_async(list)(
        await sync_to_async(ArtifactService.search_artifacts)(
            playbook=playbook,
            search_query=search or None,
            type_filter=type_filter or None,
            required_filter=required,
        )
    )

    result = [
        {
            'id': a.id,
            'name': a.name,
            'type': a.type,
            'is_required': a.is_required,
            'produced_by_id': a.produced_by_id,
            'playbook_id': playbook_id,
        }
        for a in artifacts
    ]
    logger.info(
        f'MCP Tool: Listed {len(result)} artifacts for playbook {playbook_id}'
    )
    return result


async def get_artifact(artifact_id: int) -> dict:
    """
    Get artifact details with consumer count.

    :param artifact_id: Artifact ID. Example: 1
    :return: Artifact dict with consumer_count
    :raises ValueError: If not found or not owned
    """
    logger.info(f'MCP Tool: get_artifact called - artifact_id={artifact_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.services.artifact_service import ArtifactService
    try:
        artifact = await sync_to_async(ArtifactService.get_artifact)(artifact_id)
    except Exception:
        raise ValueError(f'Artifact {artifact_id} not found')

    if artifact.playbook.author_id != user.id:
        raise ValueError(f'Artifact {artifact_id} not found')

    consumer_count = await sync_to_async(artifact.get_consumer_count)()

    logger.info(
        f'MCP Tool: Got artifact {artifact_id} "{artifact.name}" '
        f'(consumers={consumer_count})'
    )
    return {
        'id': artifact.id,
        'name': artifact.name,
        'description': artifact.description,
        'type': artifact.type,
        'is_required': artifact.is_required,
        'produced_by_id': artifact.produced_by_id,
        'produced_by_name': artifact.produced_by.name,
        'consumer_count': consumer_count,
        'playbook_id': artifact.playbook_id,
    }


async def update_artifact(
    artifact_id: int,
    name: str = None,
    description: str = None,
    type: str = None,
    is_required: bool = None,
) -> dict:
    """
    Update artifact in DRAFT playbook. Increments parent version.

    :param artifact_id: Artifact ID. Example: 1
    :param name: New name or None. Example: "Updated API Spec"
    :param description: New description or None
    :param type: New type or None. Example: "Code"
    :param is_required: New required flag or None
    :return: Updated artifact dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If not found
    """
    logger.info(f'MCP Tool: update_artifact called - artifact_id={artifact_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Artifact as ArtifactModel
    try:
        artifact = await sync_to_async(
            ArtifactModel.objects.select_related('playbook').get
        )(pk=artifact_id)
    except ArtifactModel.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')

    if artifact.playbook.author_id != user.id:
        raise ValueError(f'Artifact {artifact_id} not found')
    if artifact.playbook.status == 'released':
        raise PermissionError(
            f'Cannot modify released playbook "{artifact.playbook.name}".'
        )

    kwargs = {}
    if name is not None:
        kwargs['name'] = name
    if description is not None:
        kwargs['description'] = description
    if type is not None:
        kwargs['type'] = type
    if is_required is not None:
        kwargs['is_required'] = is_required

    from methodology.services.artifact_service import ArtifactService
    updated = await sync_to_async(ArtifactService.update_artifact)(
        artifact_id, **kwargs,
    )

    playbook = artifact.playbook
    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(
        f'MCP Tool: Updated artifact {artifact_id}, '
        f'version {old_version} → {playbook.version}'
    )
    return {
        'id': updated.id,
        'name': updated.name,
        'description': updated.description,
        'type': updated.type,
        'is_required': updated.is_required,
        'produced_by_id': updated.produced_by_id,
        'playbook_id': playbook.id,
    }


async def delete_artifact(artifact_id: int) -> dict:
    """
    Delete artifact in DRAFT playbook. Increments parent version.

    :param artifact_id: Artifact ID. Example: 1
    :return: Confirmation dict with deleted=True
    :raises PermissionError: If playbook is released
    :raises ValueError: If not found
    """
    logger.info(f'MCP Tool: delete_artifact called - artifact_id={artifact_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Artifact as ArtifactModel
    try:
        artifact = await sync_to_async(
            ArtifactModel.objects.select_related('playbook').get
        )(pk=artifact_id)
    except ArtifactModel.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')

    if artifact.playbook.author_id != user.id:
        raise ValueError(f'Artifact {artifact_id} not found')
    if artifact.playbook.status == 'released':
        raise PermissionError(
            f'Cannot modify released playbook "{artifact.playbook.name}".'
        )

    playbook = artifact.playbook

    from methodology.services.artifact_service import ArtifactService
    result = await sync_to_async(ArtifactService.delete_artifact)(artifact_id)

    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(
        f'MCP Tool: Deleted artifact {artifact_id}, '
        f'version {old_version} → {playbook.version}'
    )
    return {
        'deleted': True,
        'consumers_cleared': result.get('consumers_cleared', 0),
    }


async def link_artifact_to_activity(
    artifact_id: int,
    activity_id: int,
    is_required: bool = True,
) -> dict:
    """
    Link artifact as input to a consumer activity.

    The artifact and activity must be in the same playbook.
    Cannot link an artifact to its own producer (circular dependency).

    :param artifact_id: Artifact ID. Example: 1
    :param activity_id: Consumer activity ID. Example: 5
    :param is_required: Whether input is required. Example: True
    :return: Dict with id, artifact_id, activity_id, is_required
    :raises ValueError: If not found
    :raises ValidationError: If circular dependency or duplicate
    """
    logger.info(
        f'MCP Tool: link_artifact_to_activity called - '
        f'artifact_id={artifact_id}, activity_id={activity_id}'
    )

    user = await sync_to_async(get_current_user)()

    from methodology.models import Artifact as ArtifactModel, Activity
    try:
        artifact = await sync_to_async(
            ArtifactModel.objects.select_related('playbook').get
        )(pk=artifact_id)
    except ArtifactModel.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')

    if artifact.playbook.author_id != user.id:
        raise ValueError(f'Artifact {artifact_id} not found')

    try:
        activity = await sync_to_async(
            Activity.objects.select_related('workflow__playbook').get
        )(pk=activity_id)
    except Activity.DoesNotExist:
        raise ValueError(f'Activity {activity_id} not found')

    if activity.workflow.playbook_id != artifact.playbook_id:
        raise ValueError(
            'Artifact and activity must be in the same playbook'
        )

    from methodology.services.artifact_service import ArtifactService
    artifact_input = await sync_to_async(ArtifactService.add_artifact_input)(
        artifact=artifact,
        activity=activity,
        is_required=is_required,
    )

    logger.info(
        f'MCP Tool: Linked artifact {artifact_id} to activity {activity_id}'
    )
    return {
        'id': artifact_input.id,
        'artifact_id': artifact_id,
        'activity_id': activity_id,
        'is_required': artifact_input.is_required,
    }


async def unlink_artifact_from_activity(artifact_input_id: int) -> dict:
    """
    Remove artifact input relationship.

    :param artifact_input_id: ArtifactInput ID. Example: 1
    :return: Dict with deleted=True
    :raises ValueError: If not found or not owned
    """
    logger.info(
        f'MCP Tool: unlink_artifact_from_activity called - '
        f'artifact_input_id={artifact_input_id}'
    )

    user = await sync_to_async(get_current_user)()

    from methodology.models import ArtifactInput
    try:
        ai = await sync_to_async(
            ArtifactInput.objects.select_related('artifact__playbook').get
        )(pk=artifact_input_id)
    except ArtifactInput.DoesNotExist:
        raise ValueError(f'ArtifactInput {artifact_input_id} not found')

    if ai.artifact.playbook.author_id != user.id:
        raise ValueError(f'ArtifactInput {artifact_input_id} not found')

    from methodology.services.artifact_service import ArtifactService
    await sync_to_async(ArtifactService.remove_artifact_input)(artifact_input_id)

    logger.info(
        f'MCP Tool: Unlinked artifact input {artifact_input_id}'
    )
    return {'deleted': True}


def _parse_required_filter(value: str):
    """
    Parse required_filter string to bool or None.

    :param value: "true", "false", or empty string
    :return: True, False, or None
    """
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    return None


# ============================================================================
# SHARED HELPERS
# ============================================================================

async def _get_draft_playbook(playbook_id: int, user):
    """
    Retrieve playbook, verify ownership and draft status.

    :param playbook_id: Playbook primary key
    :param user: Authenticated user
    :returns: Playbook instance
    :raises ValueError: If playbook not found
    :raises PermissionError: If playbook is released
    """
    from methodology.models import Playbook
    try:
        playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id, author=user)
    except Playbook.DoesNotExist:
        raise ValueError(f'Playbook {playbook_id} not found')

    if playbook.status == 'released':
        raise PermissionError(
            f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.'
        )
    return playbook


def initialize_mcp():
    """
    Initialize and return the FastMCP instance.

    Called by mcp_server management command.
    Registers all 41 tools with FastMCP.

    :returns: FastMCP instance ready to run
    """
    logger.info('MCP: Initializing FastMCP server with 41 tools')

    # Register playbook tools
    mcp.tool()(create_playbook)
    mcp.tool()(list_playbooks)
    mcp.tool()(get_playbook)
    mcp.tool()(update_playbook)
    mcp.tool()(delete_playbook)

    # Register workflow tools
    mcp.tool()(create_workflow)
    mcp.tool()(list_workflows)
    mcp.tool()(get_workflow)
    mcp.tool()(update_workflow)
    mcp.tool()(delete_workflow)

    # Register activity tools
    mcp.tool()(create_activity)
    mcp.tool()(list_activities)
    mcp.tool()(get_activity)
    mcp.tool()(update_activity)
    mcp.tool()(delete_activity)
    mcp.tool()(set_predecessor)

    # Register workflow export/import tools
    mcp.tool()(export_workflow_to_local)
    mcp.tool()(import_workflow_from_local)
    mcp.tool()(apply_upload_protocol)
    mcp.tool()(create_pip_from_protocol)

    # Register skill tools
    mcp.tool()(create_skill)
    mcp.tool()(list_skills)
    mcp.tool()(get_skill)
    mcp.tool()(update_skill)
    mcp.tool()(delete_skill)
    mcp.tool()(link_skill_to_activity)
    mcp.tool()(unlink_skill_from_activity)

    # Register agent tools
    mcp.tool()(create_agent)
    mcp.tool()(list_agents)
    mcp.tool()(get_agent)
    mcp.tool()(update_agent)
    mcp.tool()(delete_agent)
    mcp.tool()(link_agent_to_activity)
    mcp.tool()(unlink_agent_from_activity)

        # Register artifact tools
    mcp.tool()(create_artifact)
    mcp.tool()(list_artifacts)
    mcp.tool()(get_artifact)
    mcp.tool()(update_artifact)
    mcp.tool()(delete_artifact)
    mcp.tool()(link_artifact_to_activity)
    mcp.tool()(unlink_artifact_from_activity)

    logger.info('MCP: All 41 tools registered')
    return mcp

