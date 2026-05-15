"""
MCP HTTP facade tools.

53 synchronous functions, each mapping one MCP tool to one or more
REST API calls via httpx.  Same tool names, same parameter signatures,
same semantic return shapes as the ORM-based tools.py.

No Django, no ORM — only the standard library + httpx.
"""
import logging
import os
from typing import Literal, Optional

from mcp_integration.facade.client import get_client, check_response

logger = logging.getLogger(__name__)


# ============================================================================
# PLAYBOOK TOOLS (5)
# ============================================================================

def create_playbook(name: str, description: str, category: str) -> dict:
    """
    Create draft playbook.

    :param name: Playbook name. Example: "React Development"
    :param description: Description. Example: "Modern React patterns"
    :param category: Category. Example: "development"
    :return: Created playbook dict
    """
    logger.info(f'HTTP Tool: create_playbook name="{name}"')
    r = get_client().post("/api/playbooks/", json={
        "name": name, "description": description, "category": category
    })
    return check_response(r, "create_playbook")


def list_playbooks(status: Literal["draft", "released", "active", "all"] = "all") -> list:
    """
    List playbooks filtered by status.

    :param status: Filter by status or "all". Example: "draft"
    :return: List of playbook dicts
    """
    logger.info(f'HTTP Tool: list_playbooks status={status}')
    params = {} if status == "all" else {"status": status}
    r = get_client().get("/api/playbooks/", params=params)
    data = check_response(r, "list_playbooks")
    return data.get("results", data) if isinstance(data, dict) else data


def get_playbook(playbook_id: int) -> dict:
    """
    Get playbook details with workflows.

    :param playbook_id: Playbook ID. Example: 1
    :return: Playbook dict with nested workflows
    """
    logger.info(f'HTTP Tool: get_playbook id={playbook_id}')
    r = get_client().get(f"/api/playbooks/{playbook_id}/")
    return check_response(r, "get_playbook")


def update_playbook(
    playbook_id: int,
    name: str = None,
    description: str = None,
    category: str = None
) -> dict:
    """
    Update DRAFT playbook. Auto-increments version.

    :param playbook_id: Playbook ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param category: New category or None
    :return: Updated playbook dict
    """
    logger.info(f'HTTP Tool: update_playbook id={playbook_id}')
    payload = {k: v for k, v in {
        "name": name, "description": description, "category": category
    }.items() if v is not None}
    r = get_client().patch(f"/api/playbooks/{playbook_id}/", json=payload)
    return check_response(r, "update_playbook")


def delete_playbook(playbook_id: int) -> dict:
    """
    Delete DRAFT playbook.

    :param playbook_id: Playbook ID. Example: 1
    :return: Confirmation dict
    """
    logger.info(f'HTTP Tool: delete_playbook id={playbook_id}')
    r = get_client().delete(f"/api/playbooks/{playbook_id}/")
    return check_response(r, "delete_playbook")


# ============================================================================
# WORKFLOW TOOLS (5)
# ============================================================================

def create_workflow(playbook_id: int, name: str, description: str = "") -> dict:
    """
    Create workflow in DRAFT playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Workflow name. Example: "Design Phase"
    :param description: Workflow description (optional)
    :return: Created workflow dict
    """
    logger.info(f'HTTP Tool: create_workflow name="{name}" playbook={playbook_id}')
    r = get_client().post("/api/workflows/", json={
        "playbook_id": playbook_id, "name": name, "description": description
    })
    return check_response(r, "create_workflow")


def list_workflows(playbook_id: int) -> list:
    """
    List workflows for playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :return: List of workflow dicts
    """
    logger.info(f'HTTP Tool: list_workflows playbook={playbook_id}')
    r = get_client().get("/api/workflows/", params={"playbook_id": playbook_id})
    data = check_response(r, "list_workflows")
    return data.get("results", data) if isinstance(data, dict) else data


def get_workflow(workflow_id: int) -> dict:
    """
    Get workflow details with activities.

    :param workflow_id: Workflow ID. Example: 1
    :return: Workflow dict with nested activities
    """
    logger.info(f'HTTP Tool: get_workflow id={workflow_id}')
    r = get_client().get(f"/api/workflows/{workflow_id}/")
    return check_response(r, "get_workflow")


def update_workflow(
    workflow_id: int,
    name: str = None,
    description: str = None,
    order: int = None
) -> dict:
    """
    Update workflow in DRAFT playbook. Increments parent version.

    :param workflow_id: Workflow ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param order: New order or None
    :return: Updated workflow dict
    """
    logger.info(f'HTTP Tool: update_workflow id={workflow_id}')
    payload = {k: v for k, v in {
        "name": name, "description": description, "order": order
    }.items() if v is not None}
    r = get_client().patch(f"/api/workflows/{workflow_id}/", json=payload)
    return check_response(r, "update_workflow")


def delete_workflow(workflow_id: int) -> dict:
    """
    Delete workflow in DRAFT playbook.

    :param workflow_id: Workflow ID. Example: 1
    :return: Confirmation dict
    """
    logger.info(f'HTTP Tool: delete_workflow id={workflow_id}')
    r = get_client().delete(f"/api/workflows/{workflow_id}/")
    return check_response(r, "delete_workflow")


# ============================================================================
# ACTIVITY TOOLS (6)
# ============================================================================

def create_activity(
    workflow_id: int,
    name: str,
    guidance: str = "",
    phase_id: int = None,
    predecessor_id: int = None
) -> dict:
    """
    Create activity in workflow (DRAFT playbook).

    :param workflow_id: Parent workflow ID. Example: 1
    :param name: Activity name. Example: "Design Component"
    :param guidance: Rich Markdown guidance (optional)
    :param phase_id: Phase ID to assign (optional)
    :param predecessor_id: Predecessor activity ID (optional)
    :return: Created activity dict
    """
    logger.info(f'HTTP Tool: create_activity name="{name}" workflow={workflow_id}')
    payload = {
        "workflow_id": workflow_id, "name": name, "guidance": guidance
    }
    if phase_id is not None:
        payload["phase_id"] = phase_id
    if predecessor_id is not None:
        payload["predecessor_id"] = predecessor_id
    r = get_client().post("/api/activities/", json=payload)
    return check_response(r, "create_activity")


def list_activities(workflow_id: int) -> list:
    """
    List activities for workflow.

    :param workflow_id: Parent workflow ID. Example: 1
    :return: List of activity dicts
    """
    logger.info(f'HTTP Tool: list_activities workflow={workflow_id}')
    r = get_client().get("/api/activities/", params={"workflow_id": workflow_id})
    data = check_response(r, "list_activities")
    return data.get("results", data) if isinstance(data, dict) else data


def get_activity(activity_id: int) -> dict:
    """
    Get activity details with dependencies, agent, skill, and artifacts.

    :param activity_id: Activity ID. Example: 1
    :return: Activity dict with predecessor/successor, agent, skill, artifacts
    """
    logger.info(f'HTTP Tool: get_activity id={activity_id}')
    r = get_client().get(f"/api/activities/{activity_id}/")
    return check_response(r, "get_activity")


def update_activity(
    activity_id: int,
    name: str = None,
    guidance: str = None,
    phase_id: int = None,
    order: int = None
) -> dict:
    """
    Update activity in DRAFT playbook.

    :param activity_id: Activity ID. Example: 1
    :param name: New name or None
    :param guidance: New guidance or None
    :param phase_id: New phase ID or None
    :param order: New order or None
    :return: Updated activity dict
    """
    logger.info(f'HTTP Tool: update_activity id={activity_id}')
    payload = {k: v for k, v in {
        "name": name, "guidance": guidance, "phase_id": phase_id, "order": order
    }.items() if v is not None}
    r = get_client().patch(f"/api/activities/{activity_id}/", json=payload)
    return check_response(r, "update_activity")


def delete_activity(activity_id: int) -> dict:
    """
    Delete activity in DRAFT playbook.

    :param activity_id: Activity ID. Example: 1
    :return: Confirmation dict
    """
    logger.info(f'HTTP Tool: delete_activity id={activity_id}')
    r = get_client().delete(f"/api/activities/{activity_id}/")
    return check_response(r, "delete_activity")


def set_predecessor(activity_id: int, predecessor_id: int) -> dict:
    """
    Set activity predecessor (validates no circular dependencies).

    :param activity_id: Activity ID. Example: 2
    :param predecessor_id: Predecessor activity ID. Example: 1
    :return: Updated activity dict
    """
    logger.info(f'HTTP Tool: set_predecessor activity={activity_id} predecessor={predecessor_id}')
    r = get_client().put(f"/api/activities/{activity_id}/predecessor/", json={
        "predecessor_id": predecessor_id
    })
    return check_response(r, "set_predecessor")


# ============================================================================
# WORKFLOW EXPORT / IMPORT TOOLS (4)
# ============================================================================

def export_workflow_to_local(
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
    logger.info(f'HTTP Tool: export_workflow_to_local workflow={workflow_id}')
    payload = {"target_directory": target_directory}
    if folder_name:
        payload["folder_name"] = folder_name
    r = get_client().post(f"/api/workflows/{workflow_id}/export/", json=payload)
    return check_response(r, "export_workflow_to_local")


def import_workflow_from_local(
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
    logger.info(f'HTTP Tool: import_workflow_from_local workflow={workflow_id}')
    r = get_client().post(f"/api/workflows/{workflow_id}/import_workflow/", json={
        "source_directory": source_directory, "auto_apply": auto_apply
    })
    return check_response(r, "import_workflow_from_local")


def apply_upload_protocol(protocol_file: str) -> dict:
    """
    Apply upload protocol to draft playbook.

    :param protocol_file: Path to _Upload_Protocol.md
    :return: Application result with change counts
    """
    logger.info(f'HTTP Tool: apply_upload_protocol protocol_file={protocol_file}')
    r = get_client().post("/api/workflows/0/apply-protocol/", json={
        "protocol_file": protocol_file
    })
    return check_response(r, "apply_upload_protocol")


def create_pip_from_protocol(protocol_file: str, pip_title: str) -> dict:
    """
    Create PIP from upload protocol for released playbook.

    :param protocol_file: Path to _Upload_Protocol.md
    :param pip_title: PIP title. Example: "Improve workflow"
    :return: Created PIP dict with ID and status
    """
    logger.info(f'HTTP Tool: create_pip_from_protocol title="{pip_title}"')
    r = get_client().post("/api/workflows/0/create-pip/", json={
        "protocol_file": protocol_file, "pip_title": pip_title
    })
    return check_response(r, "create_pip_from_protocol")


# ============================================================================
# SKILL TOOLS (7)
# ============================================================================

def create_skill(
    playbook_id: int,
    title: str,
    content: str = "",
    capability_domain: str = "",
    technology_stack: str = ""
) -> dict:
    """
    Create skill in draft playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :param title: Skill title (required). Example: "Build Login Form"
    :param content: Markdown content (optional)
    :param capability_domain: What capability (optional). Example: "GUI_FORM"
    :param technology_stack: Tech stack (optional). Example: "React+Redux"
    :return: Created skill dict
    """
    logger.info(f'HTTP Tool: create_skill title="{title}"')
    r = get_client().post("/api/skills/", json={
        "playbook_id": playbook_id, "title": title, "content": content,
        "capability_domain": capability_domain, "technology_stack": technology_stack
    })
    return check_response(r, "create_skill")


def list_skills(
    playbook_id: int,
    domain: str = "",
    stack: str = "",
    search: str = ""
) -> list:
    """
    List skills for playbook with optional filters.

    :param playbook_id: Playbook ID. Example: 1
    :param domain: Filter by capability_domain. Example: "GUI_FORM"
    :param stack: Filter by technology_stack. Example: "React+Redux"
    :param search: Free-text search. Example: "login"
    :return: List of skill dicts
    """
    logger.info(f'HTTP Tool: list_skills playbook={playbook_id}')
    params = {"playbook_id": playbook_id}
    if domain:
        params["domain"] = domain
    if stack:
        params["stack"] = stack
    if search:
        params["search"] = search
    r = get_client().get("/api/skills/", params=params)
    data = check_response(r, "list_skills")
    return data.get("results", data) if isinstance(data, dict) else data


def get_skill(skill_id: int) -> dict:
    """
    Get skill details with activity count.

    :param skill_id: Skill ID. Example: 1
    :return: Skill dict with activity_count
    """
    logger.info(f'HTTP Tool: get_skill id={skill_id}')
    r = get_client().get(f"/api/skills/{skill_id}/")
    return check_response(r, "get_skill")


def update_skill(
    skill_id: int,
    title: str = None,
    content: str = None,
    capability_domain: str = None,
    technology_stack: str = None
) -> dict:
    """
    Update skill in draft playbook.

    :param skill_id: Skill ID. Example: 1
    :param title: New title (optional)
    :param content: New content (optional)
    :param capability_domain: New domain (optional)
    :param technology_stack: New stack (optional)
    :return: Updated skill dict
    """
    logger.info(f'HTTP Tool: update_skill id={skill_id}')
    payload = {k: v for k, v in {
        "title": title, "content": content,
        "capability_domain": capability_domain, "technology_stack": technology_stack
    }.items() if v is not None}
    r = get_client().patch(f"/api/skills/{skill_id}/", json=payload)
    return check_response(r, "update_skill")


def delete_skill(skill_id: int) -> dict:
    """
    Delete skill in draft playbook.

    :param skill_id: Skill ID. Example: 1
    :return: Dict with deleted=True
    """
    logger.info(f'HTTP Tool: delete_skill id={skill_id}')
    r = get_client().delete(f"/api/skills/{skill_id}/")
    return check_response(r, "delete_skill")


def link_skill_to_activity(activity_id: int, skill_id: int) -> dict:
    """
    Link a skill to an activity.

    :param activity_id: Activity ID. Example: 1
    :param skill_id: Skill ID. Example: 5
    :return: Dict with updated activity_id and skill_id
    """
    logger.info(f'HTTP Tool: link_skill_to_activity activity={activity_id} skill={skill_id}')
    r = get_client().put(f"/api/activities/{activity_id}/skill/", json={
        "skill_id": skill_id
    })
    return check_response(r, "link_skill_to_activity")


def unlink_skill_from_activity(activity_id: int) -> dict:
    """
    Unlink skill from an activity (set FK to NULL).

    :param activity_id: Activity ID. Example: 1
    :return: Dict with updated activity_id and skill_id=None
    """
    logger.info(f'HTTP Tool: unlink_skill_from_activity activity={activity_id}')
    r = get_client().delete(f"/api/activities/{activity_id}/skill/")
    return check_response(r, "unlink_skill_from_activity")


# ============================================================================
# RULE TOOLS (6)
# ============================================================================

def create_rule(
    playbook_id: int,
    title: str,
    content: str = "",
    slug: str = "",
    always_apply: bool = True
) -> dict:
    """
    Create playbook rule (.mdc export).

    :param playbook_id: Parent playbook ID. Example: 1
    :param title: Rule title (required)
    :param content: Rule content (optional)
    :param slug: Rule slug (optional)
    :param always_apply: Whether to always apply. Example: True
    :return: Created rule dict
    """
    logger.info(f'HTTP Tool: create_rule title="{title}"')
    r = get_client().post("/api/rules/", json={
        "playbook_id": playbook_id, "title": title, "content": content,
        "slug": slug, "always_apply": always_apply
    })
    return check_response(r, "create_rule")


def list_rules(
    playbook_id: int,
    search: str = "",
    unlinked_only: bool = False
) -> list:
    """
    List rules for playbook.

    :param playbook_id: Playbook ID. Example: 1
    :param search: Free-text search. Example: "reviewer"
    :param unlinked_only: Only return unlinked rules. Example: False
    :return: List of rule dicts
    """
    logger.info(f'HTTP Tool: list_rules playbook={playbook_id}')
    params = {"playbook_id": playbook_id}
    if search:
        params["search"] = search
    if unlinked_only:
        params["unlinked_only"] = "true"
    r = get_client().get("/api/rules/", params=params)
    data = check_response(r, "list_rules")
    return data.get("results", data) if isinstance(data, dict) else data


def get_rule(rule_id: int) -> dict:
    """
    Get rule by ID.

    :param rule_id: Rule ID. Example: 1
    :return: Rule dict
    """
    logger.info(f'HTTP Tool: get_rule id={rule_id}')
    r = get_client().get(f"/api/rules/{rule_id}/")
    return check_response(r, "get_rule")


def update_rule(
    rule_id: int,
    title: str = None,
    content: str = None,
    slug: str = None,
    always_apply: bool = None
) -> dict:
    """
    Update rule in draft playbook.

    :param rule_id: Rule ID. Example: 1
    :param title: New title (optional)
    :param content: New content (optional)
    :param slug: New slug (optional)
    :param always_apply: New always_apply (optional)
    :return: Updated rule dict
    """
    logger.info(f'HTTP Tool: update_rule id={rule_id}')
    payload = {k: v for k, v in {
        "title": title, "content": content, "slug": slug, "always_apply": always_apply
    }.items() if v is not None}
    r = get_client().patch(f"/api/rules/{rule_id}/", json=payload)
    return check_response(r, "update_rule")


def delete_rule(rule_id: int) -> dict:
    """
    Delete rule from draft playbook.

    :param rule_id: Rule ID. Example: 1
    :return: Dict with deleted=True
    """
    logger.info(f'HTTP Tool: delete_rule id={rule_id}')
    r = get_client().delete(f"/api/rules/{rule_id}/")
    return check_response(r, "delete_rule")


def set_activity_rules(activity_id: int, rule_ids: list) -> dict:
    """
    Replace activity's linked rules (same playbook only).

    :param activity_id: Activity ID. Example: 1
    :param rule_ids: List of rule IDs. Example: [1, 2, 3]
    :return: Dict with activity_id and rule_ids
    """
    logger.info(f'HTTP Tool: set_activity_rules activity={activity_id} rules={rule_ids}')
    r = get_client().put(f"/api/activities/{activity_id}/rules/", json={
        "rule_ids": rule_ids
    })
    return check_response(r, "set_activity_rules")


# ============================================================================
# AGENT TOOLS (7)
# ============================================================================

def create_agent(playbook_id: int, name: str, description: str = "") -> dict:
    """
    Create agent in draft playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Agent name (required, unique per playbook). Example: "Code Reviewer"
    :param description: Description (optional)
    :return: Created agent dict
    """
    logger.info(f'HTTP Tool: create_agent name="{name}"')
    r = get_client().post("/api/agents/", json={
        "playbook_id": playbook_id, "name": name, "description": description
    })
    return check_response(r, "create_agent")


def list_agents(playbook_id: int, search: str = "") -> list:
    """
    List agents for playbook with optional search.

    :param playbook_id: Playbook ID. Example: 1
    :param search: Free-text search. Example: "reviewer"
    :return: List of agent dicts
    """
    logger.info(f'HTTP Tool: list_agents playbook={playbook_id}')
    params = {"playbook_id": playbook_id}
    if search:
        params["search"] = search
    r = get_client().get("/api/agents/", params=params)
    data = check_response(r, "list_agents")
    return data.get("results", data) if isinstance(data, dict) else data


def get_agent(agent_id: int) -> dict:
    """
    Get agent details with activity count.

    :param agent_id: Agent ID. Example: 1
    :return: Agent dict with activity_count
    """
    logger.info(f'HTTP Tool: get_agent id={agent_id}')
    r = get_client().get(f"/api/agents/{agent_id}/")
    return check_response(r, "get_agent")


def update_agent(agent_id: int, name: str = None, description: str = None) -> dict:
    """
    Update agent in draft playbook.

    :param agent_id: Agent ID. Example: 1
    :param name: New name (optional)
    :param description: New description (optional)
    :return: Updated agent dict
    """
    logger.info(f'HTTP Tool: update_agent id={agent_id}')
    payload = {k: v for k, v in {
        "name": name, "description": description
    }.items() if v is not None}
    r = get_client().patch(f"/api/agents/{agent_id}/", json=payload)
    return check_response(r, "update_agent")


def delete_agent(agent_id: int) -> dict:
    """
    Delete agent in draft playbook.

    :param agent_id: Agent ID. Example: 1
    :return: Dict with deleted=True
    """
    logger.info(f'HTTP Tool: delete_agent id={agent_id}')
    r = get_client().delete(f"/api/agents/{agent_id}/")
    return check_response(r, "delete_agent")


def link_agent_to_activity(activity_id: int, agent_id: int) -> dict:
    """
    Link an agent to an activity.

    :param activity_id: Activity ID. Example: 1
    :param agent_id: Agent ID. Example: 3
    :return: Dict with updated activity_id and agent_id
    """
    logger.info(f'HTTP Tool: link_agent_to_activity activity={activity_id} agent={agent_id}')
    r = get_client().put(f"/api/activities/{activity_id}/agent/", json={
        "agent_id": agent_id
    })
    return check_response(r, "link_agent_to_activity")


def unlink_agent_from_activity(activity_id: int) -> dict:
    """
    Unlink agent from an activity (set FK to NULL).

    :param activity_id: Activity ID. Example: 1
    :return: Dict with updated activity_id and agent_id=None
    """
    logger.info(f'HTTP Tool: unlink_agent_from_activity activity={activity_id}')
    r = get_client().delete(f"/api/activities/{activity_id}/agent/")
    return check_response(r, "unlink_agent_from_activity")


# ============================================================================
# ARTIFACT TOOLS (7)
# ============================================================================

def create_artifact(
    playbook_id: int,
    produced_by_id: int,
    name: str,
    description: str = "",
    type: str = "Document",
    is_required: bool = False
) -> dict:
    """
    Create artifact in draft playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :param produced_by_id: Activity ID that produces this artifact. Example: 5
    :param name: Artifact name (required). Example: "API Specification"
    :param description: Description (optional)
    :param type: Artifact type. Example: "Document"
    :param is_required: Whether required. Example: True
    :return: Created artifact dict
    """
    logger.info(f'HTTP Tool: create_artifact name="{name}"')
    r = get_client().post("/api/artifacts/", json={
        "playbook_id": playbook_id, "produced_by_id": produced_by_id,
        "name": name, "description": description, "type": type, "is_required": is_required
    })
    return check_response(r, "create_artifact")


def list_artifacts(
    playbook_id: int,
    search: str = "",
    type_filter: str = "",
    required_filter: str = ""
) -> list:
    """
    List artifacts for playbook with optional filters.

    :param playbook_id: Playbook ID. Example: 1
    :param search: Free-text search in name/description. Example: "API"
    :param type_filter: Filter by type. Example: "Document"
    :param required_filter: Filter by required ("true"/"false"). Example: "true"
    :return: List of artifact dicts
    """
    logger.info(f'HTTP Tool: list_artifacts playbook={playbook_id}')
    params = {"playbook_id": playbook_id}
    if search:
        params["search"] = search
    if type_filter:
        params["type"] = type_filter
    if required_filter:
        params["is_required"] = required_filter
    r = get_client().get("/api/artifacts/", params=params)
    data = check_response(r, "list_artifacts")
    return data.get("results", data) if isinstance(data, dict) else data


def get_artifact(artifact_id: int) -> dict:
    """
    Get artifact details with consumer count.

    :param artifact_id: Artifact ID. Example: 1
    :return: Artifact dict with consumer_count
    """
    logger.info(f'HTTP Tool: get_artifact id={artifact_id}')
    r = get_client().get(f"/api/artifacts/{artifact_id}/")
    return check_response(r, "get_artifact")


def update_artifact(
    artifact_id: int,
    name: str = None,
    description: str = None,
    type: str = None,
    is_required: bool = None
) -> dict:
    """
    Update artifact in DRAFT playbook.

    :param artifact_id: Artifact ID. Example: 1
    :param name: New name or None
    :param description: New description or None
    :param type: New type or None
    :param is_required: New required flag or None
    :return: Updated artifact dict
    """
    logger.info(f'HTTP Tool: update_artifact id={artifact_id}')
    payload = {k: v for k, v in {
        "name": name, "description": description, "type": type, "is_required": is_required
    }.items() if v is not None}
    r = get_client().patch(f"/api/artifacts/{artifact_id}/", json=payload)
    return check_response(r, "update_artifact")


def delete_artifact(artifact_id: int) -> dict:
    """
    Delete artifact in DRAFT playbook.

    :param artifact_id: Artifact ID. Example: 1
    :return: Confirmation dict with deleted=True
    """
    logger.info(f'HTTP Tool: delete_artifact id={artifact_id}')
    r = get_client().delete(f"/api/artifacts/{artifact_id}/")
    return check_response(r, "delete_artifact")


def link_artifact_to_activity(
    artifact_id: int,
    activity_id: int,
    is_required: bool = True
) -> dict:
    """
    Link artifact as input to a consumer activity.

    :param artifact_id: Artifact ID. Example: 1
    :param activity_id: Consumer activity ID. Example: 5
    :param is_required: Whether input is required. Example: True
    :return: Dict with id, artifact_id, activity_id, is_required
    """
    logger.info(f'HTTP Tool: link_artifact_to_activity artifact={artifact_id} activity={activity_id}')
    r = get_client().post(f"/api/artifacts/{artifact_id}/consumers/", json={
        "activity_id": activity_id, "is_required": is_required
    })
    return check_response(r, "link_artifact_to_activity")


def unlink_artifact_from_activity(artifact_input_id: int) -> dict:
    """
    Remove artifact input relationship.

    :param artifact_input_id: ArtifactInput ID. Example: 1
    :return: Dict with deleted=True
    """
    logger.info(f'HTTP Tool: unlink_artifact_from_activity input={artifact_input_id}')
    r = get_client().delete(f"/api/artifact-inputs/{artifact_input_id}/")
    return check_response(r, "unlink_artifact_from_activity")


# ============================================================================
# PHASE TOOLS (6)
# ============================================================================

def create_phase(
    playbook_id: int,
    name: str,
    description: str = "",
    order: int = None
) -> dict:
    """
    Create phase in draft playbook.

    :param playbook_id: Parent playbook ID. Example: 1
    :param name: Phase name (required, unique per playbook). Example: "Planning"
    :param description: Description (optional)
    :param order: Display order (optional)
    :return: Created phase dict
    """
    logger.info(f'HTTP Tool: create_phase name="{name}"')
    payload = {"playbook_id": playbook_id, "name": name, "description": description}
    if order is not None:
        payload["order"] = order
    r = get_client().post("/api/phases/", json=payload)
    return check_response(r, "create_phase")


def list_phases(playbook_id: int) -> list:
    """
    List all phases for a playbook.

    :param playbook_id: Playbook ID. Example: 1
    :return: List of phase dicts with activity counts
    """
    logger.info(f'HTTP Tool: list_phases playbook={playbook_id}')
    r = get_client().get("/api/phases/", params={"playbook_id": playbook_id})
    data = check_response(r, "list_phases")
    return data.get("results", data) if isinstance(data, dict) else data


def get_phase(phase_id: int) -> dict:
    """
    Get phase details with activities.

    :param phase_id: Phase ID. Example: 1
    :return: Phase dict with activities list
    """
    logger.info(f'HTTP Tool: get_phase id={phase_id}')
    r = get_client().get(f"/api/phases/{phase_id}/")
    return check_response(r, "get_phase")


def update_phase(
    phase_id: int,
    name: str = None,
    description: str = None,
    order: int = None
) -> dict:
    """
    Update phase in draft playbook.

    :param phase_id: Phase ID. Example: 1
    :param name: New name (optional)
    :param description: New description (optional)
    :param order: New order (optional)
    :return: Updated phase dict
    """
    logger.info(f'HTTP Tool: update_phase id={phase_id}')
    payload = {k: v for k, v in {
        "name": name, "description": description, "order": order
    }.items() if v is not None}
    r = get_client().patch(f"/api/phases/{phase_id}/", json=payload)
    return check_response(r, "update_phase")


def delete_phase(phase_id: int) -> dict:
    """
    Delete phase in draft playbook.

    :param phase_id: Phase ID. Example: 1
    :return: Dict with deleted=True
    """
    logger.info(f'HTTP Tool: delete_phase id={phase_id}')
    r = get_client().delete(f"/api/phases/{phase_id}/")
    return check_response(r, "delete_phase")


def reorder_phases(playbook_id: int, phase_order: list) -> dict:
    """
    Reorder phases in draft playbook.

    :param playbook_id: Playbook ID. Example: 1
    :param phase_order: List of phase IDs in desired order. Example: [3, 1, 2]
    :return: Dict with reordered=True and count
    """
    logger.info(f'HTTP Tool: reorder_phases playbook={playbook_id}')
    r = get_client().put(f"/api/playbooks/{playbook_id}/phases/reorder/", json={
        "phase_order": phase_order
    })
    return check_response(r, "reorder_phases")
