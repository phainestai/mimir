"""
MCP Tool Definitions for Mimir.

Thin wrappers around existing service layer methods.
Adds: permission checks, user context, version incrementing.

Exception contract for MCP callers
---------------------------------
- ``ValueError``: not found, wrong owner, invalid arguments, and any
  ``django.core.exceptions.ValidationError`` raised by services (normalized
  via ``_handle_validation_error``) unless noted otherwise below.
- ``PermissionError``: attempts to mutate a released playbook (and similar
  guardrails).

Read-only tools (list/get) typically raise only ``ValueError`` for missing
entities or wrong ownership. Write tools may raise both.
"""
import os

# CRITICAL: Allow Django ORM in async context (FastMCP runs in async event loop)
# This must be set BEFORE any Django imports
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

import logging
from typing import Literal, Optional
from decimal import Decimal
from django.core.exceptions import ValidationError
from fastmcp import FastMCP
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("Mimir Methodology Assistant")


# Import user context management
from mcp_integration.context import get_current_user


def _handle_validation_error(e: ValidationError, tool_name: str) -> None:
    """
    Normalize Django ValidationError to ValueError for MCP callers.

    :param e: ValidationError from the service layer
    :param tool_name: MCP tool name for logging
    :raises ValueError: Always re-raises with the validation message
    """
    if hasattr(e, 'messages') and e.messages:
        msg = '; '.join(str(m) for m in e.messages)
    else:
        msg = str(e)
    logger.error(f'MCP Tool: {tool_name} validation error: {msg}')
    raise ValueError(msg)


async def _playbook_for_read(
    playbook_id: int, user, *, prefetch_workflows: bool = False
):
    """Resolve playbook if user may view it; normalize errors to ValueError."""
    from methodology.models import Playbook
    from methodology.services.playbook_service import PlaybookService

    def _run():
        try:
            return PlaybookService.get_playbook(
                playbook_id, user, prefetch_workflows=prefetch_workflows
            )
        except Playbook.DoesNotExist:
            raise ValueError(f'Playbook {playbook_id} not found') from None
        except PermissionError:
            raise ValueError(f'Playbook {playbook_id} not found') from None

    return await sync_to_async(_run)()


async def _playbook_for_write(playbook_id: int, user):
    """Resolve playbook if user owns it; normalize errors to ValueError."""
    from methodology.models import Playbook
    from methodology.services.playbook_service import PlaybookService

    def _run():
        try:
            return PlaybookService.get_owned_playbook(playbook_id, user)
        except Playbook.DoesNotExist:
            raise ValueError(f'Playbook {playbook_id} not found') from None

    return await sync_to_async(_run)()


# ============================================================================
# PLAYBOOK MCP TOOLS
# ============================================================================

async def create_playbook(
    name: str,
    description: str,
    category: str,
    visibility: Literal["private", "public"] = "private",
) -> dict:
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
    logger.info(
        f'MCP Tool: create_playbook called - name="{name}", category={category}, '
        f'visibility={visibility}'
    )
    
    # Phase 5: Get user from MCP context
    user = await sync_to_async(get_current_user)()
    
    # Call existing service
    from methodology.services.playbook_service import PlaybookService
    try:
        playbook = await sync_to_async(PlaybookService.create_playbook)(
            name=name,
            description=description,
            category=category,
            author=user,
            status='draft',  # MCP always creates drafts
            visibility=visibility,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_playbook')
    
    result = {
        'id': playbook.id,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'status': playbook.status,
        'version': str(playbook.version),
        'visibility': playbook.visibility,
    }
    logger.info(f'MCP Tool: Created playbook id={playbook.id}, version={playbook.version}')
    return result


async def list_playbooks(status: Literal["draft", "released", "active", "all"] = "all") -> list:
    """
    List playbooks filtered by status (owned + public + team-shared).
    
    :param status: Filter by status or "all". Example: "draft"
    :return: List of playbook dicts
    """
    logger.info(f'MCP Tool: list_playbooks called - status={status}')
    
    user = await sync_to_async(get_current_user)()
    
    from methodology.services.playbook_service import PlaybookService
    status_filter = None if status == "all" else status
    owned = await sync_to_async(PlaybookService.list_playbooks)(user, status=status_filter)
    public_others = await sync_to_async(PlaybookService.list_public_playbooks)(user)
    team_playbooks = await sync_to_async(PlaybookService.list_team_playbooks_for_user)(user)
    
    # Apply status filter to public and team playbooks if needed
    if status_filter:
        public_others = [p for p in public_others if p.status == status_filter]
        team_playbooks = [p for p in team_playbooks if p.status == status_filter]
    
    combined = list(owned) + public_others + team_playbooks

    def sort_key(p):
        return (p.updated_at is None, p.updated_at or p.created_at)

    combined.sort(key=sort_key, reverse=True)

    result = [
        {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'category': p.category,
            'status': p.status,
            'version': str(p.version),
            'visibility': p.visibility,
        }
        for p in combined
    ]
    logger.info(f'MCP Tool: Returning {len(result)} playbooks (owned + public + team)')
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

    playbook = await _playbook_for_read(playbook_id, user, prefetch_workflows=True)

    workflows = await sync_to_async(list)(playbook.workflows.all())
    result = {
        'id': playbook.id,
        'name': playbook.name,
        'description': playbook.description,
        'category': playbook.category,
        'status': playbook.status,
        'version': str(playbook.version),
        'visibility': playbook.visibility,
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


async def update_playbook(
    playbook_id: int,
    name: str = None,
    description: str = None,
    category: str = None,
    visibility: Optional[Literal["private", "public"]] = None,
) -> dict:
    """
    Update DRAFT playbook. Auto-increments version.
    
    :param playbook_id: Playbook ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param category: New category or None
    :return: Updated playbook dict
    :raises PermissionError: if playbook is released
    :raises ValueError: if not found, not owned, or validation fails (e.g. duplicate name)
    """
    logger.info(f'MCP Tool: update_playbook called - id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()

    playbook = await _playbook_for_write(playbook_id, user)

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
    if visibility is not None:
        update_data['visibility'] = visibility

    if update_data:
        from methodology.services.playbook_service import PlaybookService
        old_version = playbook.version

        # Update playbook
        try:
            playbook = await sync_to_async(PlaybookService.update_playbook)(playbook_id, **update_data)
        except ValidationError as e:
            _handle_validation_error(e, 'update_playbook')

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
        'visibility': playbook.visibility,
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

    playbook = await _playbook_for_write(playbook_id, user)

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

    playbook = await _playbook_for_write(playbook_id, user)

    # Permission check
    if playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot add workflow to released playbook id={playbook_id}')
        raise PermissionError(f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.')
    
    # Call existing service
    from methodology.services.workflow_service import WorkflowService
    old_version = playbook.version
    try:
        workflow = await sync_to_async(WorkflowService.create_workflow)(playbook, name, description)
    except ValidationError as e:
        _handle_validation_error(e, 'create_workflow')
    
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

    await _playbook_for_read(playbook_id, user)

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
    from methodology.services.workflow_service import WorkflowService

    def _load():
        try:
            return WorkflowService.get_workflow_for_user(
                workflow_id,
                user,
                write=False,
                prefetch_activities=True,
            )
        except Workflow.DoesNotExist:
            raise ValueError(f'Workflow {workflow_id} not found') from None
        except PermissionError:
            raise ValueError(f'Workflow {workflow_id} not found') from None

    workflow = await sync_to_async(_load)()

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
    :raises ValueError: if not found or validation fails (e.g. duplicate workflow name)
    """
    logger.info(f'MCP Tool: update_workflow called - id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Workflow
    from methodology.services.workflow_service import WorkflowService

    def _load():
        try:
            return WorkflowService.get_workflow_for_user(
                workflow_id, user, write=True, prefetch_activities=False
            )
        except Workflow.DoesNotExist:
            raise ValueError(f'Workflow {workflow_id} not found') from None
        except PermissionError:
            raise ValueError(f'Workflow {workflow_id} not found') from None

    workflow = await sync_to_async(_load)()

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
        try:
            workflow = await sync_to_async(WorkflowService.update_workflow)(workflow_id, **update_data)
        except ValidationError as e:
            _handle_validation_error(e, 'update_workflow')
        
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
    from methodology.services.workflow_service import WorkflowService

    def _load():
        try:
            return WorkflowService.get_workflow_for_user(
                workflow_id, user, write=True, prefetch_activities=False
            )
        except Workflow.DoesNotExist:
            raise ValueError(f'Workflow {workflow_id} not found') from None
        except PermissionError:
            raise ValueError(f'Workflow {workflow_id} not found') from None

    workflow = await sync_to_async(_load)()

    # Permission check
    if workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot delete workflow in released playbook')
        raise PermissionError(f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.')

    workflow_name = workflow.name
    playbook = workflow.playbook
    activity_count = await sync_to_async(workflow.activities.count)()
    old_version = playbook.version

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
                        phase_id: int = None, predecessor_id: int = None) -> dict:
    """
    Create activity in workflow (DRAFT playbook). Increments grandparent version.

    :param workflow_id: Parent workflow ID. Example: 1
    :param name: Activity name. Example: "Design Component"
    :param guidance: Rich Markdown guidance (optional)
    :param phase_id: Phase ID to assign (optional, must belong to same playbook). Example: 3
    :param predecessor_id: Predecessor activity ID (optional, must be in same workflow)
    :return: Created activity dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if workflow not found or validation fails
    """
    logger.info(f'MCP Tool: create_activity called - workflow_id={workflow_id}, name="{name}"')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Activity, Workflow
    from methodology.services.workflow_service import WorkflowService
    from methodology.services.activity_service import ActivityService

    def _load_wf():
        try:
            return WorkflowService.get_workflow_for_user(
                workflow_id, user, write=True, prefetch_activities=False
            )
        except Workflow.DoesNotExist:
            raise ValueError(f'Workflow {workflow_id} not found') from None
        except PermissionError:
            raise ValueError(f'Workflow {workflow_id} not found') from None

    workflow = await sync_to_async(_load_wf)()

    # Permission check on grandparent playbook
    if workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot add activity to workflow in released playbook')
        raise PermissionError(f'Cannot modify released playbook "{workflow.playbook.name}". Use create_pip instead.')

    # Get predecessor if specified
    predecessor = None
    if predecessor_id:
        try:
            predecessor = await sync_to_async(ActivityService.get_activity_in_workflow_for_owner)(
                workflow, predecessor_id
            )
        except Activity.DoesNotExist:
            logger.error(f'MCP Tool: Predecessor id={predecessor_id} not found in workflow {workflow_id}')
            raise ValueError(f'Predecessor activity {predecessor_id} not found in workflow')

    # Call existing service
    old_version = workflow.playbook.version
    try:
        activity = await sync_to_async(ActivityService.create_activity)(
            workflow=workflow,
            name=name,
            guidance=guidance,
            phase_id=phase_id,
            predecessor=predecessor
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_activity')

    # Increment grandparent version
    workflow.playbook.version += Decimal('0.1')
    await sync_to_async(workflow.playbook.save)()
    
    logger.info(f'MCP Tool: Created activity id={activity.id}, grandparent version {old_version} → {workflow.playbook.version}')
    
    return {
        'id': activity.id,
        'name': activity.name,
        'guidance': activity.guidance,
        'phase_id': activity.phase_id,
        'order': activity.order,
        'workflow_id': workflow.id,
        'predecessor_id': predecessor.id if predecessor else None,
    }


async def list_activities(workflow_id: int) -> list:
    """
    List activities for workflow.
    
    Returns basic activity info (id, name, phase_id, order, etc.) without guidance.
    Use get_activity(id) to retrieve full details including guidance, agent, skill, and artifacts.
    
    :param workflow_id: Parent workflow ID. Example: 1
    :return: List of activity dicts (without guidance field)
    :raises ValueError: if workflow not found
    """
    logger.info(f'MCP Tool: list_activities called - workflow_id={workflow_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Workflow
    from methodology.services.workflow_service import WorkflowService
    from methodology.services.activity_service import ActivityService

    def _load_wf():
        try:
            return WorkflowService.get_workflow_for_user(
                workflow_id, user, write=False, prefetch_activities=False
            )
        except Workflow.DoesNotExist:
            raise ValueError(f'Workflow {workflow_id} not found') from None
        except PermissionError:
            raise ValueError(f'Workflow {workflow_id} not found') from None

    workflow = await sync_to_async(_load_wf)()

    activities_qs = await sync_to_async(ActivityService.get_activities_for_workflow)(workflow)
    
    # Convert QuerySet to list
    activities = await sync_to_async(list)(activities_qs)
    
    result = [
        {
            'id': a.id,
            'name': a.name,
            'phase_id': a.phase_id,
            'order': a.order,
            'workflow_id': a.workflow_id,
            'predecessor_id': a.predecessor_id,
            'successor_id': a.successor_id,
        }
        for a in activities
    ]
    logger.info(f'MCP Tool: Returning {len(result)} activities (guidance excluded - use get_activity for details)')
    return result


async def get_activity(activity_id: int) -> dict:
    """
    Get activity details with dependencies, agent, skill, and artifacts.
    
    Tracks activity access by updating last_accessed_at timestamp for
    the "Recently Used" dashboard section.
    
    :param activity_id: Activity ID. Example: 1
    :return: Activity dict with predecessor/successor, agent, skill, and artifacts
    :raises ValueError: if not found or not owned
    """
    logger.info(f'MCP Tool: get_activity called - id={activity_id}')
    
    user = await sync_to_async(get_current_user)()
    
    # Run all database access in a single sync function
    def get_activity_data():
        from methodology.models import Activity
        from methodology.services.activity_service import ActivityService

        try:
            activity = ActivityService.get_activity_for_user(
                activity_id, user, write=False, with_full_detail=True
            )
        except Activity.DoesNotExist:
            logger.error(f'MCP Tool: Activity id={activity_id} not found for user')
            raise ValueError(f'Activity {activity_id} not found')
        except PermissionError:
            logger.error(f'MCP Tool: Activity id={activity_id} not found for user')
            raise ValueError(f'Activity {activity_id} not found')
        
        # Build agent dict
        agent_dict = None
        if activity.agent:
            agent_dict = {
                'id': activity.agent.id,
                'name': activity.agent.name,
                'description': activity.agent.description,
            }
        
        # Build skills list
        skills_list = [
            {
                'id': s.id,
                'title': s.title,
                'capability_domain': s.capability_domain,
                'technology_stack': s.technology_stack,
            }
            for s in sorted(activity.skills.all(), key=lambda x: x.title.lower())
        ]

        rules_list = [
            {
                'id': r.id,
                'title': r.title,
                'slug': r.slug,
                'always_apply': r.always_apply,
            }
            for r in sorted(activity.rules.all(), key=lambda x: x.slug)
        ]

        # Build output artifacts list
        output_artifacts = list(activity.output_artifacts.all())
        output_artifacts_list = [
            {
                'id': artifact.id,
                'name': artifact.name,
                'type': artifact.type,
                'is_required': artifact.is_required,
            }
            for artifact in output_artifacts
        ]
        
        # Build input artifacts list
        input_artifact_inputs = list(activity.input_artifacts.all())
        input_artifacts_list = []
        for ai in input_artifact_inputs:
            input_artifacts_list.append({
                'id': ai.artifact.id,
                'name': ai.artifact.name,
                'type': ai.artifact.type,
                'is_required': ai.is_required,
            })
        
        # Build predecessor dict
        predecessor_dict = None
        if activity.predecessor:
            predecessor_dict = {
                'id': activity.predecessor.id,
                'name': activity.predecessor.name,
            }
        
        # Build successor dict
        successor_dict = None
        if activity.successor:
            successor_dict = {
                'id': activity.successor.id,
                'name': activity.successor.name,
            }
        
        # Build phase dict
        phase_dict = None
        if activity.phase:
            phase_dict = {
                'id': activity.phase.id,
                'name': activity.phase.name,
            }
        
        result = {
            'id': activity.id,
            'name': activity.name,
            'guidance': activity.guidance,
            'phase': phase_dict,
            'order': activity.order,
            'workflow_id': activity.workflow_id,
            'predecessor': predecessor_dict,
            'successor': successor_dict,
            'agent': agent_dict,
            'skills': skills_list,
            'rules': rules_list,
            'output_artifacts': output_artifacts_list,
            'input_artifacts': input_artifacts_list,
        }
        
        logger.info(
            f'MCP Tool: Activity with predecessor={activity.predecessor_id}, '
            f'successor={activity.successor_id}, agent={activity.agent_id}, '
            f'skills={len(skills_list)}, rules={len(rules_list)}, outputs={len(output_artifacts_list)}, '
            f'inputs={len(input_artifacts_list)}'
        )
        
        return result
    
    # Execute all database operations in sync context
    result = await sync_to_async(get_activity_data)()
    
    # Track access for "Recently Used" dashboard section (non-critical)
    try:
        from methodology.services.activity_service import ActivityService
        await sync_to_async(ActivityService.touch_activity_access)(activity_id)
    except Exception as e:
        logger.warning(f'Failed to track access for activity {activity_id}: {e}')
    
    return result


async def update_activity(activity_id: int, name: str = None, guidance: str = None,
                        phase_id: int = None, order: int = None) -> dict:
    """
    Update activity in DRAFT playbook. Increments grandparent version.
    
    Note: Use set_predecessor_tool() to change dependencies.
    
    :param activity_id: Activity ID. Example: 1
    :param name: New name or None
    :param guidance: New guidance or None
    :param phase_id: New phase ID or None
    :param order: New order or None
    :return: Updated activity dict
    :raises PermissionError: if grandparent playbook is released
    :raises ValueError: if not found or validation fails (duplicate name, invalid phase_id, cross-playbook phase)
    """
    logger.info(f'MCP Tool: update_activity called - id={activity_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Activity
    from methodology.services.activity_service import ActivityService

    def _load():
        try:
            return ActivityService.get_activity_for_user(
                activity_id, user, write=True, with_full_detail=False
            )
        except Activity.DoesNotExist:
            raise ValueError(f'Activity {activity_id} not found') from None
        except PermissionError:
            raise ValueError(f'Activity {activity_id} not found') from None

    activity = await sync_to_async(_load)()

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
    if phase_id is not None:
        update_data['phase_id'] = phase_id
    if order is not None:
        update_data['order'] = order
    
    if update_data:
        from methodology.services.activity_service import ActivityService
        old_version = activity.workflow.playbook.version

        try:
            activity = await sync_to_async(ActivityService.update_activity)(activity_id, **update_data)
        except ValidationError as e:
            _handle_validation_error(e, 'update_activity')

        # Increment grandparent version
        activity.workflow.playbook.version += Decimal('0.1')
        await sync_to_async(activity.workflow.playbook.save)()

        logger.info(f'MCP Tool: Updated activity, grandparent version {old_version} → {activity.workflow.playbook.version}')
    
    return {
        'id': activity.id,
        'name': activity.name,
        'guidance': activity.guidance,
        'phase_id': activity.phase_id,
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
    from methodology.services.activity_service import ActivityService

    def _load():
        try:
            return ActivityService.get_activity_for_user(
                activity_id, user, write=True, with_full_detail=False
            )
        except Activity.DoesNotExist:
            raise ValueError(f'Activity {activity_id} not found') from None
        except PermissionError:
            raise ValueError(f'Activity {activity_id} not found') from None

    activity = await sync_to_async(_load)()

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
    from methodology.services.activity_service import ActivityService

    def _load():
        try:
            act = ActivityService.get_activity_for_user(
                activity_id, user, write=True, with_full_detail=False
            )
            pred = ActivityService.get_activity_in_workflow_for_owner(
                act.workflow, predecessor_id
            )
            return act, pred
        except Activity.DoesNotExist:
            raise ValueError('Activity or predecessor not found') from None
        except PermissionError:
            raise ValueError('Activity or predecessor not found') from None

    activity, predecessor = await sync_to_async(_load)()

    # Permission check
    if activity.workflow.playbook.status == 'released':
        logger.error(f'MCP Tool: Cannot modify dependencies in released playbook')
        raise PermissionError(f'Cannot modify released playbook. Use create_pip instead.')
    
    # Call service (validates circular dependencies)
    from methodology.services.activity_service import ActivityService
    old_version = activity.workflow.playbook.version
    try:
        await sync_to_async(ActivityService.set_predecessor)(activity, predecessor)
    except ValidationError as e:
        _handle_validation_error(e, 'set_predecessor')
    
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
    try:
        result = await sync_to_async(WorkflowExportService.export_workflow_to_markdown)(
            workflow_id=workflow_id,
            target_directory=target_directory,
            folder_name=folder_name,
            user=user,
        )
    except PermissionError as exc:
        raise ValueError(f'Workflow {workflow_id} not found') from exc
    
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
    try:
        result = await sync_to_async(WorkflowImportService.import_workflow_from_markdown)(
            workflow_id=workflow_id,
            source_directory=source_directory
        )
    except ValidationError as e:
        _handle_validation_error(e, 'import_workflow_from_local')
    
    if auto_apply and result['playbook_status'] == 'draft':
        from methodology.services.workflow_protocol_service import WorkflowProtocolService
        import os
        protocol_file = os.path.join(source_directory, '_Upload_Protocol.md')
        try:
            apply_result = await sync_to_async(WorkflowProtocolService.apply_upload_protocol)(
                protocol_file=protocol_file
            )
        except ValidationError as e:
            _handle_validation_error(e, 'import_workflow_from_local')
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
    try:
        result = await sync_to_async(WorkflowProtocolService.apply_upload_protocol)(
            protocol_file=protocol_file
        )
    except ValidationError as e:
        _handle_validation_error(e, 'apply_upload_protocol')
    
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
    try:
        result = await sync_to_async(WorkflowProtocolService.create_pip_from_protocol)(
            protocol_file=protocol_file,
            pip_title=pip_title
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_pip_from_protocol')
    
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
    try:
        skill = await sync_to_async(SkillService.create_skill)(
            playbook=playbook,
            title=title,
            content=content,
            capability_domain=capability_domain,
            technology_stack=technology_stack,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_skill')

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

    await _playbook_for_read(playbook_id, user)

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

    from methodology.models import Skill
    from methodology.services.skill_service import SkillService

    try:
        skill = await sync_to_async(SkillService.get_skill_for_user)(
            skill_id, user, write=False
        )
    except Skill.DoesNotExist:
        raise ValueError(f'Skill {skill_id} not found')
    except PermissionError:
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

    from methodology.models import Skill
    from methodology.services.skill_service import SkillService

    try:
        skill = await sync_to_async(SkillService.get_skill_for_user)(
            skill_id, user, write=True
        )
    except Skill.DoesNotExist:
        raise ValueError(f'Skill {skill_id} not found')
    except PermissionError:
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

    try:
        updated = await sync_to_async(SkillService.update_skill)(skill_id, **kwargs)
    except ValidationError as e:
        _handle_validation_error(e, 'update_skill')

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

    from methodology.models import Skill
    from methodology.services.skill_service import SkillService

    try:
        skill = await sync_to_async(SkillService.get_skill_for_user)(
            skill_id, user, write=True
        )
    except Skill.DoesNotExist:
        raise ValueError(f'Skill {skill_id} not found')
    except PermissionError:
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

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    try:
        updated = await sync_to_async(ActivityService.add_activity_skill)(activity_id, skill_id)
    except ValidationError as e:
        _handle_validation_error(e, 'link_skill_to_activity')

    skill_ids = list(updated.skills.values_list('id', flat=True))
    return {'activity_id': updated.id, 'skill_id': skill_id, 'skill_ids': skill_ids}


async def unlink_skill_from_activity(activity_id: int, skill_id: int) -> dict:
    """
    Unlink a specific skill from an activity.

    :param activity_id: Activity ID. Example: 1
    :param skill_id: Skill ID to remove. Example: 5
    :return: Dict with updated activity_id and remaining skill_ids
    :raises ValueError: If activity not found or not owned
    """
    logger.info(
        f'MCP Tool: unlink_skill_from_activity called - activity_id={activity_id}, skill_id={skill_id}'
    )

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    updated = await sync_to_async(ActivityService.remove_activity_skill)(activity_id, skill_id)
    skill_ids = list(updated.skills.values_list('id', flat=True))
    return {'activity_id': updated.id, 'skill_id': skill_id, 'skill_ids': skill_ids}


async def set_activity_skills(activity_id: int, skill_ids: list) -> dict:
    """
    Replace all skills linked to an activity.

    :param activity_id: Activity ID. Example: 1
    :param skill_ids: List of skill IDs (empty list clears all). Example: [5, 7]
    :return: Dict with activity_id and skill_ids
    """
    logger.info(
        f'MCP Tool: set_activity_skills called - activity_id={activity_id}, skill_ids={skill_ids}'
    )

    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    try:
        updated = await sync_to_async(ActivityService.set_activity_skills)(activity_id, skill_ids)
    except ValidationError as e:
        _handle_validation_error(e, 'set_activity_skills')

    result_ids = list(updated.skills.values_list('id', flat=True))
    return {'activity_id': updated.id, 'skill_ids': result_ids}


# ============================================================================
# RULE MCP TOOLS
# ============================================================================

async def create_rule(
    playbook_id: int,
    title: str,
    content: str = '',
    slug: str = '',
    always_apply: bool = True,
) -> dict:
    """Create playbook rule (.mdc export). Increments playbook version on draft."""
    logger.info(f'MCP Tool: create_rule called - playbook_id={playbook_id}, title={title!r}')
    user = await sync_to_async(get_current_user)()
    playbook = await _get_draft_playbook(playbook_id, user)

    from methodology.services.rule_service import RuleService

    try:
        rule = await sync_to_async(RuleService.create_rule)(
            playbook=playbook,
            title=title,
            content=content,
            slug=slug,
            always_apply=always_apply,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_rule')
    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Created rule id={rule.id}, version {old_version} → {playbook.version}')
    return {
        'id': rule.id,
        'title': rule.title,
        'slug': rule.slug,
        'content': rule.content,
        'always_apply': rule.always_apply,
        'playbook_id': playbook.id,
    }


async def list_rules(
    playbook_id: int,
    search: str = '',
    unlinked_only: bool = False,
) -> list:
    """List rules for playbook."""
    logger.info(f'MCP Tool: list_rules playbook_id={playbook_id}')
    user = await sync_to_async(get_current_user)()

    await _playbook_for_read(playbook_id, user)

    from methodology.services.rule_service import RuleService

    qs = await sync_to_async(RuleService.list_rules_for_playbook)(
        playbook_id, search=search, unlinked_only=unlinked_only
    )
    rules = await sync_to_async(list)(qs)
    return [
        {
            'id': r.id,
            'title': r.title,
            'slug': r.slug,
            'always_apply': r.always_apply,
            'activity_count': getattr(r, 'activity_count', 0),
            'playbook_id': r.playbook_id,
        }
        for r in rules
    ]


async def get_rule(rule_id: int) -> dict:
    """Get rule by ID."""
    logger.info(f'MCP Tool: get_rule rule_id={rule_id}')
    user = await sync_to_async(get_current_user)()

    from methodology.models import Rule
    from methodology.services.rule_service import RuleService

    try:
        rule = await sync_to_async(RuleService.get_rule_for_user)(
            rule_id, user, write=False
        )
    except Rule.DoesNotExist:
        raise ValueError(f'Rule {rule_id} not found')
    except PermissionError:
        raise ValueError(f'Rule {rule_id} not found')
    ac = await sync_to_async(rule.activities.count)()
    return {
        'id': rule.id,
        'title': rule.title,
        'slug': rule.slug,
        'content': rule.content,
        'always_apply': rule.always_apply,
        'playbook_id': rule.playbook_id,
        'activity_count': ac,
    }


async def update_rule(
    rule_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    slug: Optional[str] = None,
    always_apply: Optional[bool] = None,
) -> dict:
    """Update rule in draft playbook."""
    logger.info(f'MCP Tool: update_rule rule_id={rule_id}')
    user = await sync_to_async(get_current_user)()

    from methodology.models import Rule
    from methodology.services.rule_service import RuleService

    try:
        rule = await sync_to_async(RuleService.get_rule_for_user)(
            rule_id, user, write=True
        )
    except Rule.DoesNotExist:
        raise ValueError(f'Rule {rule_id} not found')
    except PermissionError:
        raise ValueError(f'Rule {rule_id} not found')
    if rule.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{rule.playbook.name}".')

    kwargs = {}
    if title is not None:
        kwargs['title'] = title
    if content is not None:
        kwargs['content'] = content
    if slug is not None:
        kwargs['slug'] = slug
    if always_apply is not None:
        kwargs['always_apply'] = always_apply

    if not kwargs:
        raise ValueError('No fields to update')

    try:
        updated = await sync_to_async(RuleService.update_rule)(rule_id, **kwargs)
    except ValidationError as e:
        _handle_validation_error(e, 'update_rule')
    playbook = rule.playbook
    old_version = playbook.version
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    logger.info(f'MCP Tool: Updated rule {rule_id}, version {old_version} → {playbook.version}')
    return {
        'id': updated.id,
        'title': updated.title,
        'slug': updated.slug,
        'content': updated.content,
        'always_apply': updated.always_apply,
        'playbook_id': updated.playbook_id,
    }


async def delete_rule(rule_id: int) -> dict:
    """Delete rule from draft playbook."""
    logger.info(f'MCP Tool: delete_rule rule_id={rule_id}')
    user = await sync_to_async(get_current_user)()

    from methodology.models import Rule
    from methodology.services.rule_service import RuleService

    try:
        rule = await sync_to_async(RuleService.get_rule_for_user)(
            rule_id, user, write=True
        )
    except Rule.DoesNotExist:
        raise ValueError(f'Rule {rule_id} not found')
    except PermissionError:
        raise ValueError(f'Rule {rule_id} not found')
    if rule.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{rule.playbook.name}".')

    playbook = rule.playbook
    old_version = playbook.version
    await sync_to_async(RuleService.delete_rule)(rule_id)
    playbook.version += Decimal('0.1')
    await sync_to_async(playbook.save)()

    return {'deleted': True, 'rule_id': rule_id}


async def set_activity_rules(activity_id: int, rule_ids: list) -> dict:
    """Replace activity's linked rules (same playbook only)."""
    logger.info(f'MCP Tool: set_activity_rules activity_id={activity_id}, rule_ids={rule_ids}')
    user = await sync_to_async(get_current_user)()

    from methodology.services.activity_service import ActivityService

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
    if activity.workflow.playbook.status == 'released':
        raise PermissionError('Cannot modify released playbook.')

    try:
        await sync_to_async(ActivityService.set_activity_rules)(activity_id, rule_ids)
    except ValidationError as e:
        _handle_validation_error(e, 'set_activity_rules')
    updated = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=True
    )
    ids = await sync_to_async(lambda: list(updated.rules.values_list('id', flat=True)))()
    return {'activity_id': activity_id, 'rule_ids': ids}


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
    try:
        agent = await sync_to_async(AgentService.create_agent)(
            playbook=playbook,
            name=name,
            description=description,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_agent')

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

    await _playbook_for_read(playbook_id, user)

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

    from methodology.models import Agent
    from methodology.services.agent_service import AgentService
    try:
        agent = await sync_to_async(AgentService.get_agent_for_user)(
            agent_id, user, write=False
        )
    except Agent.DoesNotExist:
        raise ValueError(f'Agent {agent_id} not found')
    except PermissionError:
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

    from methodology.models import Agent
    from methodology.services.agent_service import AgentService
    try:
        agent = await sync_to_async(AgentService.get_agent_for_user)(
            agent_id, user, write=True
        )
    except Agent.DoesNotExist:
        raise ValueError(f'Agent {agent_id} not found')
    except PermissionError:
        raise ValueError(f'Agent {agent_id} not found')
    if agent.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook "{agent.playbook.name}".')

    kwargs = {}
    if name is not None:
        kwargs['name'] = name
    if description is not None:
        kwargs['description'] = description

    try:
        updated = await sync_to_async(AgentService.update_agent)(agent_id, **kwargs)
    except ValidationError as e:
        _handle_validation_error(e, 'update_agent')

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

    from methodology.models import Agent
    from methodology.services.agent_service import AgentService
    try:
        agent = await sync_to_async(AgentService.get_agent_for_user)(
            agent_id, user, write=True
        )
    except Agent.DoesNotExist:
        raise ValueError(f'Agent {agent_id} not found')
    except PermissionError:
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

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
    if activity.workflow.playbook.status == 'released':
        raise PermissionError(f'Cannot modify released playbook.')

    try:
        updated = await sync_to_async(ActivityService.set_activity_agent)(activity_id, agent_id)
    except ValidationError as e:
        _handle_validation_error(e, 'link_agent_to_activity')

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

    activity = await sync_to_async(ActivityService.get_activity_for_user)(
        activity_id, user, write=True, with_full_detail=False
    )
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
    :raises ValueError: If playbook or activity not found, or validation fails
    """
    logger.info(
        f'MCP Tool: create_artifact called - playbook_id={playbook_id}, '
        f'produced_by_id={produced_by_id}, name="{name}"'
    )

    user = await sync_to_async(get_current_user)()
    playbook = await _get_draft_playbook(playbook_id, user)

    from methodology.models import Activity
    from methodology.services.activity_service import ActivityService

    try:
        produced_by = await sync_to_async(ActivityService.get_activity_for_user)(
            produced_by_id, user, write=True, with_full_detail=False
        )
    except Activity.DoesNotExist:
        raise ValueError(
            f'Activity {produced_by_id} not found in playbook {playbook_id}'
        )
    except PermissionError:
        raise ValueError(
            f'Activity {produced_by_id} not found in playbook {playbook_id}'
        )
    if produced_by.workflow.playbook_id != playbook.id:
        raise ValueError(
            f'Activity {produced_by_id} not found in playbook {playbook_id}'
        )

    from methodology.services.artifact_service import ArtifactService
    try:
        artifact = await sync_to_async(ArtifactService.create_artifact)(
            playbook=playbook,
            produced_by=produced_by,
            name=name,
            description=description,
            type=type,
            is_required=is_required,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_artifact')

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

    playbook = await _playbook_for_read(playbook_id, user)

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

    from methodology.models import Artifact
    from methodology.services.artifact_service import ArtifactService
    try:
        artifact = await sync_to_async(ArtifactService.get_artifact_for_user)(
            artifact_id, user, write=False
        )
    except Artifact.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')
    except PermissionError:
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
    :raises ValueError: If not found or validation fails
    """
    logger.info(f'MCP Tool: update_artifact called - artifact_id={artifact_id}')

    user = await sync_to_async(get_current_user)()

    from methodology.models import Artifact
    from methodology.services.artifact_service import ArtifactService
    try:
        artifact = await sync_to_async(ArtifactService.get_artifact_for_user)(
            artifact_id, user, write=True
        )
    except Artifact.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')
    except PermissionError:
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
    try:
        updated = await sync_to_async(ArtifactService.update_artifact)(
            artifact_id, **kwargs,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'update_artifact')

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

    from methodology.models import Artifact
    from methodology.services.artifact_service import ArtifactService
    try:
        artifact = await sync_to_async(ArtifactService.get_artifact_for_user)(
            artifact_id, user, write=True
        )
    except Artifact.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')
    except PermissionError:
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
    :raises ValueError: If not found, circular dependency, or duplicate link
    """
    logger.info(
        f'MCP Tool: link_artifact_to_activity called - '
        f'artifact_id={artifact_id}, activity_id={activity_id}'
    )

    user = await sync_to_async(get_current_user)()

    from methodology.models import Activity, Artifact
    from methodology.services.activity_service import ActivityService
    from methodology.services.artifact_service import ArtifactService

    try:
        artifact = await sync_to_async(ArtifactService.get_artifact_for_user)(
            artifact_id, user, write=True
        )
    except Artifact.DoesNotExist:
        raise ValueError(f'Artifact {artifact_id} not found')
    except PermissionError:
        raise ValueError(f'Artifact {artifact_id} not found')

    try:
        activity = await sync_to_async(ActivityService.get_activity_for_user)(
            activity_id, user, write=True, with_full_detail=False
        )
    except Activity.DoesNotExist:
        raise ValueError(f'Activity {activity_id} not found')
    except PermissionError:
        raise ValueError(f'Activity {activity_id} not found')

    if activity.workflow.playbook_id != artifact.playbook_id:
        raise ValueError(
            'Artifact and activity must be in the same playbook'
        )

    from methodology.services.artifact_service import ArtifactService
    try:
        artifact_input = await sync_to_async(ArtifactService.add_artifact_input)(
            artifact=artifact,
            activity=activity,
            is_required=is_required,
        )
    except ValidationError as e:
        _handle_validation_error(e, 'link_artifact_to_activity')

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

    from methodology.models import ArtifactInput, Playbook
    from methodology.services.artifact_service import ArtifactService
    try:
        await sync_to_async(ArtifactService.get_artifact_input_for_owner)(
            artifact_input_id, user
        )
    except (ArtifactInput.DoesNotExist, Playbook.DoesNotExist):
        raise ValueError(f'ArtifactInput {artifact_input_id} not found')

    await sync_to_async(ArtifactService.remove_artifact_input)(artifact_input_id)

    logger.info(
        f'MCP Tool: Unlinked artifact input {artifact_input_id}'
    )
    return {'deleted': True}


# ============================================================================
# PHASE MCP TOOLS
# ============================================================================

def _phase_to_dict(phase):
    """Convert Phase model instance to dict."""
    return {
        'id': phase.id,
        'name': phase.name,
        'description': phase.description,
        'order': phase.order,
        'playbook_id': phase.playbook_id,
        'created_at': phase.created_at.isoformat() if phase.created_at else None,
        'updated_at': phase.updated_at.isoformat() if phase.updated_at else None,
    }


async def create_phase(
    playbook_id: int,
    name: str,
    description: str = '',
    order: int | None = None
) -> dict:
    """
    Create phase in draft playbook. Increments parent version.
    
    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Phase name (required, unique per playbook). Example: "Planning"
    :param description: Description (optional). Example: "Initial planning phase"
    :param order: Display order (optional, auto-assigned if None). Example: 1
    :return: Created phase dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If playbook not found or validation fails
    """
    logger.info(f'MCP Tool: create_phase called - playbook_id={playbook_id}, name="{name}"')
    
    user = await sync_to_async(get_current_user)()

    playbook = await _playbook_for_write(playbook_id, user)

    if playbook.status == 'released':
        raise PermissionError('Cannot create phases in released playbook')
    
    from methodology.services.phase_service import PhaseService
    try:
        phase = await sync_to_async(PhaseService.create_phase)(
            playbook_id=playbook_id,
            name=name,
            description=description,
            order=order,
            user=user
        )
    except ValidationError as e:
        _handle_validation_error(e, 'create_phase')
    
    phase_dict = _phase_to_dict(phase)
    logger.info(f'MCP Tool: Phase {phase_dict["id"]} created in playbook {playbook_id}')
    return phase_dict


async def list_phases(playbook_id: int) -> list[dict]:
    """
    List all phases for a playbook.
    
    :param playbook_id: Playbook ID. Example: 1
    :return: List of phase dicts with activity counts
    :raises ValueError: If playbook not found
    """
    logger.info(f'MCP Tool: list_phases called - playbook_id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()

    await _playbook_for_read(playbook_id, user)

    from methodology.services.phase_service import PhaseService
    phases = await sync_to_async(PhaseService.list_phases)(playbook_id, user)
    
    # Convert QuerySet to list of dicts
    phases_list = await sync_to_async(list)(phases)
    phases_dicts = [_phase_to_dict(p) for p in phases_list]
    
    logger.info(f'MCP Tool: Retrieved {len(phases_dicts)} phases for playbook {playbook_id}')
    return phases_dicts


async def get_phase(phase_id: int) -> dict:
    """
    Get phase details with activities.
    
    :param phase_id: Phase ID. Example: 1
    :return: Phase dict with activities list
    :raises ValueError: If phase not found or not owned
    """
    logger.info(f'MCP Tool: get_phase called - phase_id={phase_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.services.phase_service import PhaseService
    from django.core.exceptions import PermissionDenied

    try:
        phase_data = await sync_to_async(PhaseService.get_phase_with_activities)(phase_id, user)
    except ValidationError:
        raise ValueError(f'Phase {phase_id} not found')
    except PermissionDenied:
        raise ValueError(f'Phase {phase_id} not found')
    
    # Convert phase object to dict — serialize ORM objects to JSON-safe primitives
    raw_activities = phase_data['workflow_activities']
    serialized_activities = [
        {
            'workflow_id': wf.id,
            'workflow_name': wf.name,
            'activities': [
                {'id': a.id, 'name': a.name, 'order': a.order}
                for a in acts
            ]
        }
        for wf, acts in raw_activities.items()
    ] if isinstance(raw_activities, dict) else list(raw_activities)

    raw_artifacts = phase_data['artifacts']
    serialized_artifacts = [
        {'id': a.id, 'name': a.name, 'type': a.type}
        for a in raw_artifacts
    ]

    result = {
        **_phase_to_dict(phase_data['phase']),
        'activities': serialized_activities,
        'artifacts': serialized_artifacts,
    }
    
    logger.info(f'MCP Tool: Retrieved phase {phase_id}')
    return result


async def update_phase(
    phase_id: int,
    name: str | None = None,
    description: str | None = None,
    order: int | None = None
) -> dict:
    """
    Update phase in draft playbook. Increments parent version.
    
    :param phase_id: Phase ID. Example: 1
    :param name: New name (optional). Example: "Execution"
    :param description: New description (optional)
    :param order: New order (optional). Example: 2
    :return: Updated phase dict
    :raises PermissionError: If playbook is released
    :raises ValueError: If phase not found or validation fails
    """
    logger.info(f'MCP Tool: update_phase called - phase_id={phase_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Phase
    from methodology.services.phase_service import PhaseService

    try:
        phase = await sync_to_async(PhaseService.get_phase_for_user)(phase_id, user, write=True)
    except Phase.DoesNotExist:
        raise ValueError(f'Phase {phase_id} not found')
    except PermissionError:
        raise ValueError(f'Phase {phase_id} not found')

    if phase.playbook.status == 'released':
        raise PermissionError('Cannot update phases in released playbook')

    try:
        updated_phase = await sync_to_async(PhaseService.update_phase)(
            phase_id=phase_id,
            name=name,
            description=description,
            order=order,
            user=user
        )
    except ValidationError as e:
        _handle_validation_error(e, 'update_phase')
    
    phase_dict = _phase_to_dict(updated_phase)
    logger.info(f'MCP Tool: Phase {phase_id} updated')
    return phase_dict


async def delete_phase(phase_id: int) -> dict:
    """
    Delete phase in draft playbook. Clears phase from activities. Increments parent version.
    
    :param phase_id: Phase ID. Example: 1
    :return: Dict with deleted=True
    :raises PermissionError: If playbook is released
    :raises ValueError: If phase not found or not owned
    """
    logger.info(f'MCP Tool: delete_phase called - phase_id={phase_id}')
    
    user = await sync_to_async(get_current_user)()

    from methodology.models import Phase
    from methodology.services.phase_service import PhaseService

    try:
        phase = await sync_to_async(PhaseService.get_phase_for_user)(phase_id, user, write=True)
    except Phase.DoesNotExist:
        raise ValueError(f'Phase {phase_id} not found')
    except PermissionError:
        raise ValueError(f'Phase {phase_id} not found')

    if phase.playbook.status == 'released':
        raise PermissionError('Cannot delete phases in released playbook')

    try:
        await sync_to_async(PhaseService.delete_phase)(phase_id, user)
    except ValidationError as e:
        _handle_validation_error(e, 'delete_phase')
    
    logger.info(f'MCP Tool: Phase {phase_id} deleted')
    return {'deleted': True}


async def reorder_phases(playbook_id: int, phase_order: list[int]) -> dict:
    """
    Reorder phases in draft playbook. Increments parent version.
    
    :param playbook_id: Playbook ID. Example: 1
    :param phase_order: List of phase IDs in desired order. Example: [3, 1, 2]
    :return: Dict with reordered=True and count
    :raises PermissionError: If playbook is released
    :raises ValueError: If playbook not found or validation fails
    """
    logger.info(f'MCP Tool: reorder_phases called - playbook_id={playbook_id}')
    
    user = await sync_to_async(get_current_user)()

    playbook = await _playbook_for_write(playbook_id, user)

    if playbook.status == 'released':
        raise PermissionError('Cannot reorder phases in released playbook')
    
    from methodology.services.phase_service import PhaseService
    # Convert list of IDs to list of (id, order) tuples
    phase_order_list = [(phase_id, idx + 1) for idx, phase_id in enumerate(phase_order)]
    try:
        updated_phases = await sync_to_async(PhaseService.reorder_phases)(
            playbook_id=playbook_id,
            phase_order_list=phase_order_list,
            user=user
        )
    except ValidationError as e:
        _handle_validation_error(e, 'reorder_phases')
    
    result = {
        'reordered': True,
        'count': len(updated_phases)
    }
    
    logger.info(f'MCP Tool: Reordered {result["count"]} phases in playbook {playbook_id}')
    return result




# ============================================================================
# PROCESS IMPROVEMENT PROPOSALS (PIP) — Act 9
# ============================================================================


def _serialize_pip_change(ch) -> dict:
    """Map :class:`~methodology.models.PipChange` to JSON-friendly dict."""

    return {
        "id": ch.id,
        "order": ch.order,
        "change_type": ch.change_type,
        "entity_type": ch.entity_type,
        "name": ch.name or "",
        "target_id": ch.target_id,
        "target_name_snapshot": ch.target_name_snapshot or "",
        "content": ch.content or "",
        "parent_workflow_id": ch.parent_workflow_id,
        "parent_workflow_ref": ch.parent_workflow_ref or "",
        "insert_after_activity_id": ch.insert_after_activity_id,
        "insert_after_activity_ref": ch.insert_after_activity_ref or "",
        "phase_ref": ch.phase_ref or "",
        "produced_by_activity_ref": ch.produced_by_activity_ref or "",
        "artifact_type": ch.artifact_type or "",
        "artifact_is_required": bool(ch.artifact_is_required),
        "append_to_playbook_end": bool(ch.append_to_playbook_end),
        "internal_ref": ch.internal_ref or "",
        "relationship_type": ch.relationship_type or "",
        "source_entity_ref": ch.source_entity_ref or "",
        "target_entity_ref": ch.target_entity_ref or "",
        "galdr_recommendation": ch.galdr_recommendation or "",
        "galdr_reasoning": ch.galdr_reasoning or "",
        "admin_decision": ch.admin_decision or "",
        "admin_note": ch.admin_note or "",
    }


def _serialize_pip_summary(pip) -> dict:
    """Shallow playbook improvement proposal row."""

    return {
        "id": pip.id,
        "title": pip.title,
        "summary": pip.summary or "",
        "status": pip.status,
        "playbook_id": pip.playbook_id,
        "submitted_by_username": getattr(pip.created_by, "username", "") or "",
        "submitted_at": pip.submitted_at.isoformat()
        if pip.submitted_at
        else "",
        "status_changed_at": pip.status_changed_at.isoformat()
        if pip.status_changed_at
        else "",
        "changes_count": getattr(pip, "change_count", None)
        if hasattr(pip, "change_count")
        else pip.changes.count(),
    }


async def list_pips(
    scope: str = "mine",
    status_codes: Optional[str] = None,
    playbook_id: Optional[int] = None,
) -> list[dict]:
    """
    List PIPs for the current user (staff may request ``scope=all``).

    :param status_codes: comma-separated statuses (draft,reviewed,…); empty=all
    """

    logger.info(f"MCP Tool: list_pips scope={scope} status_codes={status_codes}")
    user = await sync_to_async(get_current_user)()
    status_list = []
    if status_codes and str(status_codes).strip():
        status_list = [s.strip() for s in str(status_codes).split(",") if s.strip()]

    from methodology.services.pip_service import PIPService

    def _inner():
        qs = PIPService.list_queryset_for_user(
            actor=user,
            scope=scope,
            status_filters=status_list or None,
            playbook_id=playbook_id,
        )
        rows = list(qs)
        PIPService.mark_list_viewed(user)
        return rows

    try:
        rows = await sync_to_async(_inner)()
    except PermissionError as exc:
        raise ValueError(str(exc)) from exc
    payload = [_serialize_pip_summary(p) for p in rows]
    logger.info(f"MCP Tool: list_pips returned={len(payload)}")
    return payload


async def get_pip(pip_id: int) -> dict:
    """Return a single proposal with nested change rows."""

    user = await sync_to_async(get_current_user)()

    def _fetch():
        from methodology.models import ProcessImprovementProposal as Pipo
        from methodology.services.pip_service import PIPService

        try:
            return PIPService.get_pip_with_changes(int(pip_id), user)
        except Pipo.DoesNotExist as exc:
            raise ValueError(f"PIP {pip_id} not found") from exc
        except PermissionError as exc:
            raise ValueError(str(exc)) from exc

    pip = await sync_to_async(_fetch)()
    summary = _serialize_pip_summary(pip)
    summary["changes"] = [
        _serialize_pip_change(c) for c in pip.changes.order_by("order", "pk")
    ]
    return summary


async def create_pip(playbook_id: int, title: str, summary: str = "") -> dict:
    """Create a Draft PIP on a Released playbook."""

    user = await sync_to_async(get_current_user)()

    def _mk():
        from methodology.services.pip_service import PIPService

        return PIPService.create_draft_for_playbook(
            actor=user,
            playbook_id=int(playbook_id),
            title=title,
            summary=summary or "",
        )


    try:
        pip = await sync_to_async(_mk)()
    except ValidationError as e:
        _handle_validation_error(e, "create_pip")

    def _reload():
        from methodology.services.pip_service import PIPService

        return PIPService.get_pip(pip.pk, user)

    refreshed = await sync_to_async(_reload)()
    return {"pip": _serialize_pip_summary(refreshed)}


async def add_pip_change(
    pip_id: int,
    change_type: str,
    entity_type: str = "",
    name: str = "",
    content: str = "",
    target_id: Optional[int] = None,
    parent_workflow_id: Optional[int] = None,
    parent_workflow_ref: str = "",
    insert_after_activity_id: Optional[int] = None,
    insert_after_activity_ref: str = "",
    phase_ref: str = "",
    produced_by_activity_ref: str = "",
    artifact_type: str = "",
    artifact_is_required: bool = False,
    append_to_playbook_end: bool = False,
    internal_ref: str = "",
    relationship_type: str = "",
    source_entity_ref: str = "",
    target_entity_ref: str = "",
) -> dict:
    """Attach a typed change row to a Draft PIP.

    change_type values and required fields:
    - ADD   : entity_type + name + content required.
              ADD Activity: parent_workflow_id OR parent_workflow_ref (pk or #slug).
              ADD Artifact: produced_by_activity_ref required.
              Optionally set internal_ref="#slug" for later LINK/ref rows in this PIP.
    - ALTER : entity_type + target_id + at least one of name/content required.
              Activity: optional phase_ref (pk or #slug).
    - DROP  : entity_type + target_id + rationale in content.
    - LINK  : relationship_type + source_entity_ref + target_entity_ref (entity_type="").
    - UNLINK: same as LINK.

    entity_type (ADD/ALTER/DROP): Workflow, Activity, Phase, Skill, Agent, Rule, Artifact.

    relationship_type (LINK/UNLINK): skill_activity, rule_activity, agent_activity,
    activity_workflow, artifact_activity.

    Full subtree recipe (call add_pip_change in order):
      1. ADD Phase       internal_ref="#phase1"  name="Construction"
      2. ADD Workflow    internal_ref="#wf1"     name="Performance"
      3. ADD Activity    internal_ref="#act1"    parent_workflow_ref="#wf1"  phase_ref="#phase1"
      4. ADD Activity    name="Step 2"           parent_workflow_ref="#wf1"  insert_after_activity_ref="#act1"
      5. ADD Skill       internal_ref="#sk1"     ...
      6. LINK            relationship_type="skill_activity"  source_entity_ref="#sk1"  target_entity_ref="#act1"
    """

    user = await sync_to_async(get_current_user)()

    def _run():
        from methodology.services.pip_service import PIPService

        pip = PIPService.get_pip(pip_id, user)
        try:
            return PIPService.add_change(
                actor=user,
                pip=pip,
                change_type=change_type,
                entity_type=entity_type,
                name=name or "",
                content=content or "",
                target_id=target_id,
                parent_workflow_id=parent_workflow_id,
                parent_workflow_ref=parent_workflow_ref or "",
                insert_after_activity_id=insert_after_activity_id,
                insert_after_activity_ref=insert_after_activity_ref or "",
                phase_ref=phase_ref or "",
                produced_by_activity_ref=produced_by_activity_ref or "",
                artifact_type=artifact_type or "",
                artifact_is_required=artifact_is_required,
                append_to_playbook_end=append_to_playbook_end,
                internal_ref=internal_ref or "",
                relationship_type=relationship_type or "",
                source_entity_ref=source_entity_ref or "",
                target_entity_ref=target_entity_ref or "",
            )
        except ValidationError as e:
            _handle_validation_error(e, "add_pip_change")

    ch = await sync_to_async(_run)()
    return {"change_id": ch.pk}


async def remove_pip_change(pip_id: int, change_id: int) -> dict:
    """Remove change while draft."""

    user = await sync_to_async(get_current_user)()
    from methodology.services.pip_service import PIPService

    pip = await sync_to_async(PIPService.get_pip)(pip_id, user)

    try:
        await sync_to_async(PIPService.remove_change)(
            actor=user, pip=pip, change_id=int(change_id)
        )
    except ValidationError as e:
        _handle_validation_error(e, "remove_pip_change")
    return {"removed": True, "change_id": int(change_id)}


async def submit_pip(pip_id: int) -> dict:
    """Queue Galdr evaluation for Draft or retry row."""

    user = await sync_to_async(get_current_user)()
    from methodology.services.pip_service import PIPService

    pip = await sync_to_async(PIPService.get_pip)(pip_id, user)

    try:
        await sync_to_async(PIPService.submit_for_review)(actor=user, pip=pip)
    except ValidationError as e:
        _handle_validation_error(e, "submit_pip")
    updated = await sync_to_async(PIPService.get_pip)(pip_id, user)
    return {"pip": _serialize_pip_summary(updated)}


async def cancel_pip(pip_id: int) -> dict:
    """Withdraw / delete an in-flight PIP owned by caller."""

    user = await sync_to_async(get_current_user)()

    def _withdraw():
        from methodology.services.pip_service import PIPService

        pip = PIPService.get_pip(pip_id, user)
        try:
            PIPService.cancel_pip(pip, user)
        except ValidationError as e:
            _handle_validation_error(e, "cancel_pip")

    await sync_to_async(_withdraw)()
    return {"cancelled": True, "pip_id": int(pip_id)}


async def preview_pip_diff(pip_id: int) -> dict:
    """Return human-readable preview rows for diff-style inspection."""

    user = await sync_to_async(get_current_user)()

    def _preview():
        from methodology.services.pip_service import PIPService

        pip = PIPService.get_pip(pip_id, user)
        rows = PIPService.summarize_preview_rows(pip)
        return {"pip_id": int(pip_id), "rows": rows}

    return await sync_to_async(_preview)()


async def report_bug(
    description: str,
    page_context: str = "",
    reporter_email: str = "",
) -> dict:
    """File a GitHub Issue with structured environment and context (same backend as the web widget)."""

    user = await sync_to_async(get_current_user)()

    def _submit():
        from methodology.services.bug_report_service import BugReportService

        email = (reporter_email or "").strip() or (
            getattr(user, "email", None) or ""
        ).strip()
        if not email:
            raise ValueError(
                "reporter_email is required when the MCP user has no email."
            )
        logger.info(
            "MCP report_bug user_id=%s desc_len=%s has_context=%s",
            getattr(user, "id", None),
            len(description or ""),
            bool((page_context or "").strip()),
        )
        return BugReportService.submit_bug(
            description,
            email,
            source="mcp",
            page_context=(page_context or "").strip(),
        )

    return await sync_to_async(_submit)()


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
    from methodology.services.playbook_service import PlaybookService

    try:
        playbook = await sync_to_async(PlaybookService.get_owned_playbook)(
            playbook_id, user
        )
    except Playbook.DoesNotExist:
        raise ValueError(f'Playbook {playbook_id} not found')

    if playbook.status == 'released':
        raise PermissionError(
            f'Cannot modify released playbook "{playbook.name}". Use create_pip instead.'
        )
    return playbook


# ========================================
# TEAM TOOLS (7)
# ========================================


async def list_teams() -> list:
    """
    List all teams visible to the current user.

    Thin wrapper over TeamService.get_teams_visible_to(user).

    :return: List of team dicts with id, name, visibility, join_policy, category, admin_id, member_count
    :raises: None

    Example:
        >>> result = await list_teams()
        >>> result[0]['name']
        'Platform Engineering'
        >>> result[0]['member_count']
        5
    """
    logger.info("MCP Tool: list_teams called")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService

    service = TeamService()
    teams = await sync_to_async(service.get_teams_visible_to)(user)
    result = [
        {
            "id": team.id,
            "name": team.name,
            "description": team.description or "",
            "visibility": team.visibility,
            "join_policy": team.join_policy,
            "category": team.category,
            "admin_id": team.admin_id,
            "member_count": team.memberships.count(),
            "created_at": team.created_at.isoformat(),
        }
        for team in teams
    ]
    logger.info(f"MCP Tool: list_teams returned {len(result)} teams")
    return result


async def get_team(team_id: int) -> dict:
    """
    Get detailed information about a specific team.

    Thin wrapper over TeamService.get_team_or_404(pk, user).

    :param team_id: Team primary key. Example: 42
    :return: Team dict with id, name, description, visibility, join_policy, category, admin, members, playbooks
    :raises ValueError: if team not found or not visible to user

    Example:
        >>> result = await get_team(team_id=42)
        >>> result['name']
        'Platform Engineering'
        >>> len(result['members'])
        5
    """
    logger.info(f"MCP Tool: get_team called - team_id={team_id}")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService
    from methodology.models import Team

    from django.http import Http404 as _Http404

    service = TeamService()
    try:
        team = await sync_to_async(service.get_team_or_404)(team_id, user)
    except (Team.DoesNotExist, _Http404):
        raise ValueError(f"Team {team_id} not found or not accessible")

    # Get members
    memberships = await sync_to_async(list)(team.memberships.select_related("user"))
    members_data = [
        {
            "user_id": m.user_id,
            "username": m.user.username,
            "email": m.user.email,
            "joined_at": m.joined_at.isoformat(),
        }
        for m in memberships
    ]

    # Get playbooks
    from methodology.models import TeamPlaybook

    team_playbooks = await sync_to_async(list)(
        TeamPlaybook.objects.filter(team=team).select_related("playbook")
    )
    playbooks_data = [
        {
            "playbook_id": tp.playbook_id,
            "playbook_name": tp.playbook.name,
            "linked_at": tp.created_at.isoformat(),
        }
        for tp in team_playbooks
    ]

    result = {
        "id": team.id,
        "name": team.name,
        "description": team.description or "",
        "visibility": team.visibility,
        "join_policy": team.join_policy,
        "category": team.category,
        "admin": {
            "user_id": team.admin_id,
            "username": team.admin.username,
        },
        "member_count": len(members_data),
        "members": members_data,
        "playbooks": playbooks_data,
        "created_at": team.created_at.isoformat(),
    }

    logger.info(f"MCP Tool: get_team returned team_id={team_id} with {len(members_data)} members")
    return result


async def create_team(
    name: str,
    description: str = "",
    visibility: Literal["Public", "Hidden"] = "Public",
    join_policy: Literal["Auto-approve", "Requires Approval", "Invite Only"] = "Auto-approve",
    category: Literal["Engineering", "Design", "Research", "Product", "Private", "Other"] = "Engineering",
) -> dict:
    """
    Create a new team. Caller becomes admin and first member.

    Thin wrapper over TeamService.create_team().

    :param name: Team name (unique). Example: "Platform Engineering"
    :param description: Optional description. Example: "Core platform team"
    :param visibility: "Public" (discoverable) or "Hidden" (invite-only). Default "Public"
    :param join_policy: How new members join. Default "Auto-approve"
    :param category: Team category. Default "Engineering"
    :return: Created team dict with id, name, visibility, join_policy, category, admin_id, member_count
    :raises ValueError: if name is empty or already taken

    Example:
        >>> result = await create_team(name="Platform Eng", description="Core infra")
        >>> result['name']
        'Platform Eng'
        >>> result['member_count']
        1
    """
    logger.info(f'MCP Tool: create_team called - name="{name}", category={category}')
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService

    if not name or not name.strip():
        raise ValueError("Team name cannot be empty")

    service = TeamService()
    try:
        team = await sync_to_async(service.create_team)(
            user=user,
            name=name,
            description=description,
            visibility=visibility,
            join_policy=join_policy,
            category=category,
        )
    except ValidationError as e:
        _handle_validation_error(e, "create_team")

    result = {
        "id": team.id,
        "name": team.name,
        "description": team.description or "",
        "visibility": team.visibility,
        "join_policy": team.join_policy,
        "category": team.category,
        "admin_id": team.admin_id,
        "member_count": 1,
        "created_at": team.created_at.isoformat(),
    }
    logger.info(f"MCP Tool: Created team id={team.id}")
    return result


async def move_playbook_to_team(playbook_id: int, team_id: int) -> dict:
    """
    Add a playbook to a team (requires team admin).

    Thin wrapper over TeamService.add_playbook_to_team().

    :param playbook_id: Playbook primary key. Example: 12
    :param team_id: Team primary key. Example: 42
    :return: Dict with success=True, team_id, playbook_id, playbook_name
    :raises ValueError: if team or playbook not found
    :raises PermissionError: if user is not team admin

    Example:
        >>> result = await move_playbook_to_team(playbook_id=12, team_id=42)
        >>> result['success']
        True
        >>> result['playbook_name']
        'React Development'
    """
    logger.info(f"MCP Tool: move_playbook_to_team called - playbook_id={playbook_id}, team_id={team_id}")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService
    from methodology.services.playbook_service import PlaybookService
    from methodology.models import Team

    try:
        team = await sync_to_async(Team.objects.get)(pk=team_id)
    except Team.DoesNotExist:
        raise ValueError(f"Team {team_id} not found")

    if team.admin_id != user.id:
        raise PermissionError(f"Only team admin can add playbooks to team {team.name}")

    try:
        playbook = await sync_to_async(PlaybookService.get_playbook)(playbook_id, user)
    except:
        raise ValueError(f"Playbook {playbook_id} not found or not accessible")

    service = TeamService()
    await sync_to_async(service.add_playbook_to_team)(team, playbook, user)

    result = {
        "success": True,
        "team_id": team.id,
        "team_name": team.name,
        "playbook_id": playbook.id,
        "playbook_name": playbook.name,
    }
    logger.info(f"MCP Tool: Added playbook {playbook_id} to team {team_id}")
    return result


async def move_playbook_from_team(playbook_id: int, team_id: int) -> dict:
    """
    Remove a playbook from a team (requires team admin).

    Thin wrapper over TeamService.remove_playbook_from_team().

    :param playbook_id: Playbook primary key. Example: 12
    :param team_id: Team primary key. Example: 42
    :return: Dict with success=True, team_id, playbook_id
    :raises ValueError: if team or playbook not found
    :raises PermissionError: if user is not team admin

    Example:
        >>> result = await move_playbook_from_team(playbook_id=12, team_id=42)
        >>> result['success']
        True
    """
    logger.info(f"MCP Tool: move_playbook_from_team called - playbook_id={playbook_id}, team_id={team_id}")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService
    from methodology.services.playbook_service import PlaybookService
    from methodology.models import Team

    try:
        team = await sync_to_async(Team.objects.get)(pk=team_id)
    except Team.DoesNotExist:
        raise ValueError(f"Team {team_id} not found")

    if team.admin_id != user.id:
        raise PermissionError(f"Only team admin can remove playbooks from team {team.name}")

    try:
        playbook = await sync_to_async(PlaybookService.get_playbook)(playbook_id, user)
    except:
        raise ValueError(f"Playbook {playbook_id} not found or not accessible")

    service = TeamService()
    await sync_to_async(service.remove_playbook_from_team)(team, playbook, user)

    result = {
        "success": True,
        "team_id": team.id,
        "team_name": team.name,
        "playbook_id": playbook.id,
    }
    logger.info(f"MCP Tool: Removed playbook {playbook_id} from team {team_id}")
    return result


async def invite_to_team(team_id: int, emails: list[str], welcome_text: str = "") -> dict:
    """
    Invite users to join a team (requires team admin).

    Thin wrapper over TeamInviteService.send_invites().

    :param team_id: Team primary key. Example: 42
    :param emails: List of email addresses to invite. Example: ["user@example.com"]
    :param welcome_text: Optional custom welcome message. Example: "Join our platform team!"
    :return: Dict with success=True, team_id, invited_count, results (list of per-email status)
    :raises ValueError: if team not found or emails list empty
    :raises PermissionError: if user is not team admin

    Example:
        >>> result = await invite_to_team(team_id=42, emails=["new@example.com"])
        >>> result['success']
        True
        >>> result['invited_count']
        1
    """
    logger.info(f"MCP Tool: invite_to_team called - team_id={team_id}, emails={emails}")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_invite_service import TeamInviteService
    from methodology.models import Team

    try:
        team = await sync_to_async(Team.objects.get)(pk=team_id)
    except Team.DoesNotExist:
        raise ValueError(f"Team {team_id} not found")

    if team.admin_id != user.id:
        raise PermissionError(f"Only team admin can invite users to team {team.name}")

    if not emails or len(emails) == 0:
        raise ValueError("Emails list cannot be empty")

    invite_service = TeamInviteService()
    results = await sync_to_async(invite_service.send_invites)(team, user, emails, welcome_text)

    invited_count = results.get("sent", 0) + results.get("created", 0)
    result = {
        "success": True,
        "team_id": team.id,
        "team_name": team.name,
        "invited_count": invited_count,
        "results": results,
    }
    logger.info(f"MCP Tool: Invited {invited_count} users to team {team_id}")
    return result


async def manage_team_invite(
    team_id: int, request_id: int, action: Literal["approve", "reject"]
) -> dict:
    """
    Approve or reject a join request (requires team admin).

    Thin wrapper over TeamService.approve_join_request() or reject_join_request().

    :param team_id: Team primary key. Example: 42
    :param request_id: JoinRequest primary key. Example: 123
    :param action: "approve" or "reject". Example: "approve"
    :return: Dict with success=True, team_id, request_id, action, user_email
    :raises ValueError: if team or request not found, or invalid action
    :raises PermissionError: if user is not team admin

    Example:
        >>> result = await manage_team_invite(team_id=42, request_id=123, action="approve")
        >>> result['success']
        True
        >>> result['action']
        'approve'
    """
    logger.info(f"MCP Tool: manage_team_invite called - team_id={team_id}, request_id={request_id}, action={action}")
    user = await sync_to_async(get_current_user)()

    from methodology.services.team_service import TeamService
    from methodology.models import Team, JoinRequest

    try:
        team = await sync_to_async(Team.objects.get)(pk=team_id)
    except Team.DoesNotExist:
        raise ValueError(f"Team {team_id} not found")

    if team.admin_id != user.id:
        raise PermissionError(f"Only team admin can manage join requests for team {team.name}")

    try:
        join_request = await sync_to_async(JoinRequest.objects.select_related("user").get)(
            pk=request_id, team=team
        )
    except JoinRequest.DoesNotExist:
        raise ValueError(f"Join request {request_id} not found for team {team_id}")

    service = TeamService()
    if action == "approve":
        await sync_to_async(service.approve_join_request)(join_request, user)
    elif action == "reject":
        await sync_to_async(service.reject_join_request)(join_request, user)
    else:
        raise ValueError(f"Invalid action: {action}. Must be 'approve' or 'reject'")

    result = {
        "success": True,
        "team_id": team.id,
        "team_name": team.name,
        "request_id": request_id,
        "action": action,
        "user_email": join_request.user.email,
    }
    logger.info(f"MCP Tool: {action}d join request {request_id} for team {team_id}")
    return result


def initialize_mcp():
    """
    Initialize and return the FastMCP instance.

    Called by mcp_server management command.
    Registers MCP tools including PIP lifecycle helpers.

    :returns: FastMCP instance ready to run
    """
    logger.info("MCP: Initializing FastMCP server with 50 tools")

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

    # PIP lifecycle tools (structured proposals)
    mcp.tool()(list_pips)
    mcp.tool()(get_pip)
    mcp.tool()(create_pip)
    mcp.tool()(add_pip_change)
    mcp.tool()(remove_pip_change)
    mcp.tool()(submit_pip)
    mcp.tool()(cancel_pip)
    mcp.tool()(preview_pip_diff)
    mcp.tool()(report_bug)

    # Register skill tools
    mcp.tool()(create_skill)
    mcp.tool()(list_skills)
    mcp.tool()(get_skill)
    mcp.tool()(update_skill)
    mcp.tool()(delete_skill)
    mcp.tool()(link_skill_to_activity)
    mcp.tool()(unlink_skill_from_activity)
    mcp.tool()(set_activity_skills)

    # Register rule tools
    mcp.tool()(create_rule)
    mcp.tool()(list_rules)
    mcp.tool()(get_rule)
    mcp.tool()(update_rule)
    mcp.tool()(delete_rule)
    mcp.tool()(set_activity_rules)

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

    # Register phase tools
    mcp.tool()(create_phase)
    mcp.tool()(list_phases)
    mcp.tool()(get_phase)
    mcp.tool()(update_phase)
    mcp.tool()(delete_phase)
    mcp.tool()(reorder_phases)

    # Register team tools (7)
    mcp.tool()(list_teams)
    mcp.tool()(get_team)
    mcp.tool()(create_team)
    mcp.tool()(move_playbook_to_team)
    mcp.tool()(move_playbook_from_team)
    mcp.tool()(invite_to_team)
    mcp.tool()(manage_team_invite)

    logger.info("MCP: All tools registered (57 tools: 50 previous + 7 team tools)")
    return mcp

