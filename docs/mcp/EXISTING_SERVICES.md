# Existing Service Layer (Used by UI)

## WorkflowService

**File**: `methodology/services/workflow_service.py`

**Methods available for MCP**:
- `create_workflow(playbook, name, description='', order=None)` - Creates workflow with auto-ordering
- `get_workflow(workflow_id)` - Get workflow by ID
- `get_workflows_for_playbook(playbook_id)` - Get all workflows for a playbook, ordered
- `update_workflow(workflow_id, **data)` - Update workflow fields
- `delete_workflow(workflow_id)` - Delete workflow
- `duplicate_workflow(workflow_id, new_name)` - Duplicate workflow (shallow copy)

**What MCP needs to add**:
- Permission checking (verify playbook is draft, owned by user)
- Version incrementing on parent playbook
- User context from MCP session

## ActivityService  

**File**: `methodology/services/activity_service.py`

**Methods available for MCP**:
- `create_activity(workflow, name, description, ...)` - Create activity with validation
- `get_activity(activity_id)` - Get activity by ID
- `get_activities_for_workflow(workflow_id)` - Get all activities for workflow
- `update_activity(activity_id, **data)` - Update activity fields
- `delete_activity(activity_id)` - Delete activity
- `set_predecessor(activity, predecessor)` - Set activity predecessor
- `remove_predecessor(activity, predecessor)` - Remove predecessor
- `set_successor(activity, successor)` - Set activity successor
- `remove_successor(activity, successor)` - Remove successor
- `get_predecessors(activity)` - Get all predecessors
- `get_successors(activity)` - Get all successors
- `validate_dependencies(activity)` - Validate no circular dependencies

**What MCP needs to add**:
- Permission checking (verify parent playbook is draft, owned by user)
- Version incrementing on grandparent playbook
- User context from MCP session

## PlaybookService

**File**: DOES NOT EXIST

**Current UI implementation**: 
- Direct `Playbook.objects.create()` in `playbook_views.py:168`
- No service layer

**What needs to be created**:
- Generic `PlaybookService` with CRUD methods
- Used by BOTH UI and MCP
- Refactor UI views to use service layer

**Methods needed**:
- `create_playbook(name, description, category, author, status='draft', visibility='private')`
- `get_playbook(playbook_id)`
- `list_playbooks(author, status_filter=None)`
- `update_playbook(playbook_id, **data)`
- `delete_playbook(playbook_id)`
- `duplicate_playbook(playbook_id, new_name, author)`

## MCP Tool Architecture

```python
# mcp/tools.py - THIN WRAPPERS

@mcp.tool()
def create_workflow_tool(playbook_id: int, name: str, description: str = ""):
    """Create workflow in draft playbook."""
    # 1. Get user from MCP context
    user = get_current_user_from_mcp_context()
    
    # 2. Permission check
    playbook = Playbook.objects.get(id=playbook_id, author=user)
    if playbook.status == 'released':
        raise PermissionError("Cannot modify released playbook")
    
    # 3. Call EXISTING service method
    workflow = WorkflowService.create_workflow(playbook, name, description)
    
    # 4. Increment parent version
    playbook.version += Decimal('0.1')
    playbook.save()
    
    # 5. Return serialized data
    return {
        'id': workflow.id,
        'name': workflow.name,
        'order': workflow.order,
        'playbook_id': playbook.id
    }
```

## BugReportService

**File**: `methodology/services/bug_report_service.py`

**Purpose**: File GitHub Issues from the Feedback UI, `POST /api/feedback/report/` (MCP HTTP facade), and MCP `report_bug` (stdio server).

**Production configuration**: `GITHUB_TOKEN` (Issues: write) and optional `GITHUB_BUG_REPO` on the FOB host — see [README.md](../../README.md), [docs/architecture/SAO.md](../architecture/SAO.md), and [.env.example](../../.env.example).

## Key Principles

1. **No MCP-specific service methods** - Service layer is generic
2. **MCP tools are thin wrappers** - Add permission checks + user context
3. **Same service methods** - Used by both UI views and MCP tools
4. **Separation of concerns**:
   - Services: Business logic
   - UI Views: HTTP handling + template rendering  
   - MCP Tools: Permission + context + service calls
