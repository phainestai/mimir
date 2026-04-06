#!/usr/bin/env python3
"""
Script to safely insert artifact MCP tools into tools.py.
Avoids edit tool corruption issues.
"""

ARTIFACT_TOOLS = '''
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

'''

ARTIFACT_REGISTRATIONS = '''    # Register artifact tools
    mcp.tool()(create_artifact)
    mcp.tool()(list_artifacts)
    mcp.tool()(get_artifact)
    mcp.tool()(update_artifact)
    mcp.tool()(delete_artifact)
    mcp.tool()(link_artifact_to_activity)
    mcp.tool()(unlink_artifact_from_activity)

'''

def main():
    tools_path = '/Users/denispetelin/GitHub/mimir/mcp_integration/tools.py'
    
    with open(tools_path, 'r') as f:
        content = f.read()
    
    # Insert artifact tools before "# ============================================================================\n# SHARED HELPERS"
    marker = '# ============================================================================\n# SHARED HELPERS'
    if marker not in content:
        print("ERROR: SHARED HELPERS marker not found")
        return 1
    
    content = content.replace(marker, ARTIFACT_TOOLS + '\n' + marker)
    
    # Update tool count from 34 to 41
    content = content.replace('Registers all 34 tools', 'Registers all 41 tools')
    content = content.replace("'MCP: Initializing FastMCP server with 34 tools'", 
                              "'MCP: Initializing FastMCP server with 41 tools'")
    content = content.replace("logger.info('MCP: All 34 tools registered')",
                              ARTIFACT_REGISTRATIONS + "    logger.info('MCP: All 41 tools registered')")
    
    with open(tools_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Inserted artifact tools into {tools_path}")
    print(f"✓ Updated tool count from 34 to 41")
    return 0

if __name__ == '__main__':
    exit(main())
