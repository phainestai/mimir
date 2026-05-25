# Mimir: System Architecture Overview

## Executive Summary

Mimir is a self-contained platform for managing and evolving software development methodologies through AI-driven continuous improvement. Everything lives in the **FOB (Forward Operating Base)** — a single Django application that provides both the Web UI for humans and an MCP server for AI assistants.

**Key Design Decisions**:
- **FastMCP as API Wrapper**: FastMCP exposes MCP tools that call Mimir's own REST API endpoints — decoupled from the service layer, authenticated via token
- **Repository Pattern**: Storage-agnostic architecture (SQLite for current FOB)
- **Galdr AI Review**: All PIPs are pre-assessed by Galdr before human (Admin) review — reduces review burden and provides structured reasoning
- **Structured PIPs**: Changes are typed (ADD / ALTER / DROP / LINK / UNLINK) per entity or relationship, enabling automated application upon approval
- **PIP LINK dispatch**: On finalization, `LINK` / `UNLINK` changes route to existing services — `ActivityService.add_activity_skill`, `add_activity_rule`, `set_activity_agent` / `clear_activity_agent`, and `WorkflowService.add_activity_to_workflow` / `remove_activity_from_workflow`. Cross-workflow listing uses `ActivityWorkflowMembership` (secondary appearances; `Activity.workflow` FK remains primary).
- **Shared Services Layer**: Business logic lives in `services/` and is consumed two ways: (1) by Django views + templates for the Web UI, and (2) exposed as REST API endpoints consumed by FastMCP tools wrapped with `@tool`
- **HTMX + Graphviz for FOB**: Server-rendered UI with minimal JS — testable with standard Django tests, no browser automation needed

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────┐
│   FOB — Forward Operating Base (Django 5)           │
│                                                     │
│   Process 1: Web Server (HTTP :8000)                │
│   ├─ python manage.py runserver 8000                │
│   ├─ Django views + HTMX UI                         │
│   ├─ REST API endpoints  (/api/…)                   │
│   ├─ Django Admin (PIP review, Galdr output)        │
│   └─ Playbook authoring, PIP management             │
│                                                     │
│   Process 2: MCP Server (FastMCP → REST)            │
│   ├─ FastMCP wraps /api/… endpoints                 │
│   ├─ Config: BASE_URL + TOKEN                       │
│   ├─ Authenticated via Authorization: Token <token> │
│   ├─ Playbook/workflow/activity queries             │
│   └─ PIP submission                                 │
│                                                     │
│   Process 3: Galdr AI (background worker)           │
│   ├─ Triggered on PIP submission                    │
│   ├─ Reads full Playbook context                    │
│   ├─ Assesses each Change (ADD/ALTER/DROP)          │
│   └─ Writes ACCEPT/REJECT + reasoning to PIP       │
│                                                     │
│   Shared Layer:                                     │
│   ├─ SQLite database                                │
│   ├─ Repository pattern (abstraction)               │
│   ├─ Services (business logic)                      │
│   └─ Models (Playbook, Workflow, Activity, …, PIP)  │
└─────────────────────────────────────────────────────┘
         ↑ MCP calls (FastMCP)
┌────────────────────────────┐
│   AI Assistant (IDE)       │
│   Cursor / Windsurf / etc. │
└────────────────────────────┘
```

### Platform Components (Quick Reference)

**FOB Web GUI** (`http://localhost:8000`)
Custom Django application: full UI for Playbook authoring, Workflow/Activity/Skill/Agent management, PIP creation and tracking.

**Mimir MCP Server** (FastMCP)
A container that exposes Playbook context, guidance, and PIP submission to AI assistants. Makes authenticated REST calls to `BASE_URL/api/…` — no direct DB access from the MCP layer. **Requires a live FOB at all times**: `BASE_URL` points to either a local FOB (`http://localhost:8000`) or a hosted FOB (`https://mimir.featurefactory.io`). Configuration requires `BASE_URL` and `TOKEN` (user's FOB authentication token).

**Galdr AI Engine**
Background worker that processes each submitted PIP: reads the target Playbook in full, assesses each Change for consistency with Workflow goals and entity relationships, and writes a structured recommendation (`ACCEPT` / `REJECT` / `NEEDS_CLARIFICATION` + reasoning) per Change. Output is surfaced in Django Admin for the human Admin to review.

**LLM target: Anthropic — default model `claude-sonnet-4-5` (configurable via `GALDR_MODEL` env var).** Galdr uses the Anthropic Python SDK (`anthropic` package). The model is swappable for any Anthropic model via `.env`; a `StubGaldrClient` is used in tests to avoid real API calls. API key: `ANTHROPIC_API_KEY` in `.env`.

**Django Admin**
Used by Administrators (users with Accept/Reject PIP permissions) to review Galdr's recommendations and apply final Accept/Reject decisions per Change. Accepted Changes are applied atomically to the Playbook, publishing a new version.

**External Integrations**
Work item management is handled by external 3rd-party MCP servers (GitHub MCP, Jira MCP, GitLab MCP, etc.). Mimir MCP provides playbook context; external MCPs handle work item creation and tracking.

### Domain Model

**Core Entities**: Playbook, Workflow, Phase (optional), Activity, Artifact, Agent, Skill, **Rule** (playbook-scoped IDE rules; M2M with Activities; exported to `rules/*.mdc`)

**Phase is OPTIONAL**: Workflows MAY contain Phases for grouping Activities, but a Workflow can organize Activities without Phase grouping.

**Artifact** (formerly "Deliverable"):
- **Producer/Consumer Model**: Each artifact is produced by exactly one Activity (output) and may be consumed by multiple downstream Activities (inputs)
- **Flow Tracking**: Artifacts create dependencies between activities — an activity may require specific artifacts as inputs before it can execute
- Example: "API Specification" (produced by "Design API" → consumed by "Implement API", "Test API", "Document API")

**PIP (Playbook Improvement Proposal)**:
A versioned request to alter one specific Playbook, containing an ordered list of Changes. Each Change is typed:
- `ADD` — add a new Workflow / Activity / Skill / Agent / Artifact, appended or inserted after a named sibling
- `ALTER` — replace/update an existing entity
- `DROP` — remove an entity (with rationale)

Lifecycle: `Draft` → `Submitted` → `Processing (Galdr)` → `Reviewed` → `Accepted` / `Rejected`

## Design Principles

### 1. FOB-Centric Architecture

**FOB (Forward Operating Base)**
This is where Playbooks are authored, consumed, judged practical/impractical, refined, and expanded through a structured PIP process with AI-assisted review.

- Single-user (or team) Django application — all data lives locally in SQLite
- Provides three interfaces:
  - **Web UI**: For authoring Playbooks, creating and tracking PIPs, team management
  - **REST API** (`/api/…`): Serves the Web UI (HTMX), the MCP server, and future integrations
  - **MCP Interface** (FastMCP → REST): For AI assistants (Cursor, Windsurf) to query Playbooks and submit PIPs
- **Galdr AI**: Built-in AI engine (Anthropic Claude, default `claude-sonnet-4-5`) that pre-processes PIPs and provides Change-level recommendations before human Admin review
- Technology: Django 5 + SQLite + FastMCP (REST wrapper) + Galdr (background worker, Anthropic SDK)

### 2. Hybrid MCP Access: Draft CRUD + Released PIP Workflow

**Problem Solved**: Allows AI to rapidly build new methodologies while protecting stable/released content from unreviewed changes.

**Solution**: MCP provides full CRUD access to DRAFT playbooks (status='draft', version=0.x), but read-only access to RELEASED playbooks (status='released', version≥1.0). Changes to released playbooks require Process Improvement Proposals (PIPs).

**Workflow for DRAFT Playbooks** (AI can modify directly):
```
AI/Engineer via MCP
    ↓ building new methodology
Creates/Updates DRAFT Playbook (v0.x)
    ↓ adds workflows, activities, skills
Iterates freely until methodology is ready
    ↓ when complete and validated
Engineer reviews in Web UI and releases (v0.x → v1.0)
```

**Workflow for RELEASED Playbooks** (requires PIP):
```
AI/Engineer via MCP
    ↓ discovers issue during work
Creates PIP (Process Improvement Proposal)
    ↓ includes: what failed, why, proposed fix
Engineer reviews in Web UI
    ↓ approves or rejects with reasoning
If approved → New methodology version created (v1.0 → v1.1)
    ↓ optional
Transmit PIP to HOMEBASE for global consideration
```

**Benefits**:
- ✅ AI can rapidly build and iterate on new methodologies
- ✅ Released/stable playbooks protected from unreviewed changes
- ✅ No race conditions on production methodologies
- ✅ Complete audit trail of methodology evolution
- ✅ Human oversight of changes to released content
- ✅ AI learns from approval/rejection patterns
- ✅ Successful improvements can propagate globally

**Rules**:
- MCP can CREATE any playbook (starts as draft v0.1)
- MCP can UPDATE/DELETE playbooks with status='draft'
- MCP can READ any playbook (draft or released)
- MCP CANNOT UPDATE/DELETE playbooks with status='released' (must create PIP)
- Web UI can do anything (full control)

### 3. Repository Pattern for Storage Abstraction

**Goal**: Decouple business logic from storage implementation.

**Pattern**:
```python
class MethodologyRepository(ABC):
    """Abstract interface - storage agnostic"""
    @abstractmethod
    def get_activity(self, id: str) -> Activity:
        """
        Retrieve activity by ID.
        
        :param id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        :return: Activity instance. Example: Activity(id="a1b2c3d4", name="Design Component")
        :raises NotFoundError: If activity does not exist.
        """
        pass
    
    @abstractmethod
    def get_workflow(self, id: str) -> List[Activity]:
        """
        Retrieve all activities in a workflow.
        
        :param id: workflow UUID as str. Example: "b2c3d4e5-f6a7-8901-bcde-f1234567890a"
        :return: List of Activity instances. Example: [Activity(id="a1", name="Design"), Activity(id="a2", name="Implement")]
        :raises NotFoundError: If workflow does not exist.
        """
        pass
    
    @abstractmethod
    def get_predecessors(self, activity_id: str) -> List[Activity]:
        """
        Get all predecessor activities for an activity.
        
        :param activity_id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        :return: List of predecessor activities. Example: [Activity(id="p1", name="Design")]
        """
        pass
    
    # ... more methods

# FOB implementation
class DjangoORMRepository(MethodologyRepository):
    """Uses Django ORM + SQLite for FOB"""
    def get_activity(self, id: str) -> Activity:
        """
        Retrieve activity from SQLite database.
        
        :param id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        :return: Activity instance. Example: Activity(id="a1b2c3d4", name="Design Component")
        :raises NodeModel.DoesNotExist: If activity does not exist.
        """
        node = NodeModel.objects.get(id=id, type='activity')
        return Activity.from_orm(node)

# HOMEBASE implementation  
class Neo4jRepository(MethodologyRepository):
    """Uses Neo4j for HOMEBASE graph queries"""
    def get_activity(self, id: str) -> Activity:
        """
        Retrieve activity from Neo4j graph database.
        
        :param id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        :return: Activity instance. Example: Activity(id="a1b2c3d4", name="Design Component")
        :raises Neo4jError: If query fails or activity does not exist.
        """
        query = "MATCH (a:Activity {id: $id}) RETURN a"
        result = self.driver.execute_query(query, id=id)
        return Activity.from_neo4j(result)
```

**Services Layer**:
```python
class MethodologyService:
    def __init__(self, repo: MethodologyRepository):
        """
        Initialize methodology service with repository.
        
        :param repo: methodology repository instance. Example: DjangoORMRepository()
        """
        self.repo = repo
    
    def plan_feature(self, feature_spec: str) -> List[WorkOrders]:
        """
        Create work plan for feature implementation.
        
        :param feature_spec: feature specification as str. Example: "Implement user authentication with OAuth2"
        :return: List of work orders. Example: [WorkOrder(id=1, title="Design auth UI", artifacts=["Login mockup"]), WorkOrder(id=2, title="Implement OAuth", artifacts=["Auth service"])]
        """
        # Business logic independent of storage
        workflow = self.repo.get_workflow('Build feature')
        task_list = self.repo.get_activities_for_workflow(workflow.id)
        return self._create_work_plan(workflow, task_list, feature_spec)
```

**Benefits**:
- FOB uses lightweight SQLite
- HOMEBASE uses powerful Neo4j graph queries
- Same business logic works with both
- Easy to test with mock repositories
- Future-proof for storage changes

### 4. Version Management

**Every methodology entity is versioned**:

```
Methodology Node
    ↓ has_version
Version Node (v1.0)
    ↓ contains
Activity_A 
    ↓ has_successor
Activity_B 
Version Node (v1.0)
    ↓ contains
Activity_B:
    ↓ has_predecessor
Activity_A

# After PIP approval:
Methodology Node
    ↓ has_version
Version Node (v1.1) ← created_from_pip ← PIP #42
    ↓ contains
Activity_A (modified)
    ↓ has_predecessor
Activity_B (reused)
```

**Capabilities**:
- Track what changed between versions
- Link changes to specific PIPs (why it changed)
- Diff between any two versions
- Rollback to previous versions
- Work on multiple version branches concurrently

### 5. Hybrid Transport Layer

**Why Not HTTP for MCP?**
- MCP standard primarily uses stdio
- HTTP requires custom client implementation
- stdio provides process-level isolation (no auth complexity)

**Solution: Run Two Processes**

**Process 1: MCP Server (stdio)**
```bash
python manage.py mcp_server
```
- Launched by IDE (Claude Desktop, Cursor, Windsurf)
- Standard MCP protocol over stdin/stdout
- No authentication needed (process isolation)
- Read-only access to methodologies

**Process 2: Web Server (HTTP)**
```bash
python manage.py runserver 8000
```
- Launched separately by engineer
- Standard Django web interface
- Methodology viewing and editing
- PIP review and approval

**Shared SQLite Database**:
- Both processes connect to same `mimir.db`
- SQLite handles concurrent access (timeout: 20s)
- Minimal write conflicts (MCP reads, Web UI writes)
- No complex coordination needed

### 6. FastMCP Server Setup

**Complete MCP Server Implementation**:

```python
# mcp/tools.py
from fastmcp import FastMCP
from typing import Literal
from methodology.services import (
    MethodologyService, 
    PlanningService, 
    AssessmentService
)
from methodology.repository import DjangoORMRepository

# Initialize FastMCP
mcp = FastMCP("Mimir Methodology Assistant")

def get_repository():
    """
    Factory function for repository - returns Django ORM implementation.
    
    :return: Repository instance. Example: DjangoORMRepository()
    """
    return DjangoORMRepository()

@mcp.tool()
def query_methodology(
    question: str,
    methodology: str,
    context: str | None = None
) -> dict:
    """
    Query methodology for guidance on how to perform tasks.
    
    :param question: natural language question as str. Example: "How do I build a TSX component per FDD?"
    :param methodology: methodology name as str. Example: "FDD"
    :param context: current work context as str or None. Example: "Working on user profile feature"
    :return: Guidance dict with answer and resources. Example: {"answer": "To build a TSX component...", "relevant_activities": ["SE1"], "relevant_skills": ["skill-tsx"]}
    """
    service = MethodologyService(get_repository())
    return service.query_guidance(question, methodology, context)

@mcp.tool()
def plan_execution(
    methodology: str,
    scope: str,
    target_system: Literal["github", "jira"]
) -> dict:
    """
    Generate work plan from methodology and create tasks.
    
    :param methodology: methodology name as str. Example: "FDD"
    :param scope: feature/scenario scope as str. Example: "Implement user login with OAuth"
    :param target_system: task creation system as Literal. Example: "github"
    :return: Work plan dict with created issues. Example: {"workflow": "Build Feature", "tasks": [{"id": "#123", "title": "Design login UI"}]}
    """
    service = PlanningService(get_repository())
    return service.create_execution_plan(methodology, scope, target_system)

@mcp.tool()
def assess_progress(
    phase: str,
    methodology: str
) -> dict:
    """
    Assess project state against methodology phase requirements.
    
    :param phase: phase name as str. Example: "inception"
    :param methodology: methodology name as str. Example: "FDD"
    :return: Assessment dict with artifact status and gaps. Example: {"phase": "inception", "can_proceed": False, "gaps": ["Login screen missing"]}
    """
    service = AssessmentService(get_repository())
    return service.assess_phase_completion(phase, methodology)

# ============================================================================
# CRUD Tools for DRAFT Playbooks (status='draft', version=0.x)
# ============================================================================

@mcp.tool()
def create_playbook(
    name: str,
    description: str,
    category: str = "general"
) -> dict:
    """
    Create new DRAFT playbook (starts at v0.1).
    
    :param name: playbook name as str. Example: "React Component Development"
    :param description: playbook description as str. Example: "Best practices for building React components"
    :param category: playbook category as str. Example: "frontend"
    :return: Created playbook dict. Example: {"id": 1, "name": "React Component Development", "version": "0.1", "status": "draft"}
    :raises ValidationError: If name is empty or duplicate
    """
    service = PlaybookService(get_repository())
    return service.create_draft_playbook(name, description, category)

@mcp.tool()
def list_playbooks(
    status: Literal["draft", "released", "all"] = "all"
) -> list[dict]:
    """
    List playbooks filtered by status.
    
    :param status: filter by status as Literal. Example: "draft"
    :return: List of playbook dicts. Example: [{"id": 1, "name": "React Dev", "version": "0.2", "status": "draft"}]
    """
    service = PlaybookService(get_repository())
    return service.list_playbooks(status)

@mcp.tool()
def get_playbook(playbook_id: int) -> dict:
    """
    Get playbook details by ID.
    
    :param playbook_id: playbook ID as int. Example: 1
    :return: Playbook dict with workflows. Example: {"id": 1, "name": "React Dev", "workflows": [...]}
    :raises NotFoundError: If playbook does not exist
    """
    service = PlaybookService(get_repository())
    return service.get_playbook_detail(playbook_id)

@mcp.tool()
def update_playbook(
    playbook_id: int,
    name: str | None = None,
    description: str | None = None,
    category: str | None = None
) -> dict:
    """
    Update DRAFT playbook fields. Auto-increments version (0.1 → 0.2).
    
    :param playbook_id: playbook ID as int. Example: 1
    :param name: new name as str or None. Example: "Updated React Development"
    :param description: new description as str or None. Example: "Updated best practices"
    :param category: new category as str or None. Example: "frontend"
    :return: Updated playbook dict. Example: {"id": 1, "version": "0.2", "status": "draft"}
    :raises PermissionError: If playbook status is 'released' (use create_pip instead)
    :raises NotFoundError: If playbook does not exist
    """
    service = PlaybookService(get_repository())
    return service.update_draft_playbook(playbook_id, name, description, category)

@mcp.tool()
def delete_playbook(playbook_id: int) -> dict:
    """
    Delete DRAFT playbook (cascades to workflows/activities).
    
    :param playbook_id: playbook ID as int. Example: 1
    :return: Confirmation dict. Example: {"deleted": True, "playbook_id": 1}
    :raises PermissionError: If playbook status is 'released'
    :raises NotFoundError: If playbook does not exist
    """
    service = PlaybookService(get_repository())
    return service.delete_draft_playbook(playbook_id)

# Workflow CRUD Tools

@mcp.tool()
def create_workflow(
    playbook_id: int,
    name: str,
    description: str,
    abbreviation: str | None = None
) -> dict:
    """
    Create workflow in DRAFT playbook.
    
    :param playbook_id: parent playbook ID as int. Example: 1
    :param name: workflow name as str. Example: "Component Development"
    :param description: workflow description as str. Example: "Steps to build reusable components"
    :param abbreviation: short name as str or None. Example: "COMP-DEV"
    :return: Created workflow dict. Example: {"id": 1, "name": "Component Development", "playbook_id": 1}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If playbook does not exist
    """
    service = WorkflowService(get_repository())
    return service.create_workflow(playbook_id, name, description, abbreviation)

@mcp.tool()
def list_workflows(playbook_id: int) -> list[dict]:
    """
    List all workflows in playbook.
    
    :param playbook_id: playbook ID as int. Example: 1
    :return: List of workflow dicts. Example: [{"id": 1, "name": "Component Dev", "order": 1}]
    :raises NotFoundError: If playbook does not exist
    """
    service = WorkflowService(get_repository())
    return service.list_workflows(playbook_id)

@mcp.tool()
def get_workflow(workflow_id: int) -> dict:
    """
    Get workflow details with activities.
    
    :param workflow_id: workflow ID as int. Example: 1
    :return: Workflow dict with activities. Example: {"id": 1, "name": "Component Dev", "activities": [...]}
    :raises NotFoundError: If workflow does not exist
    """
    service = WorkflowService(get_repository())
    return service.get_workflow_detail(workflow_id)

@mcp.tool()
def update_workflow(
    workflow_id: int,
    name: str | None = None,
    description: str | None = None,
    abbreviation: str | None = None
) -> dict:
    """
    Update workflow in DRAFT playbook. Increments parent playbook version.
    
    :param workflow_id: workflow ID as int. Example: 1
    :param name: new name as str or None. Example: "Updated Component Development"
    :param description: new description as str or None
    :param abbreviation: new abbreviation as str or None
    :return: Updated workflow dict. Example: {"id": 1, "name": "Updated Component Development"}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If workflow does not exist
    """
    service = WorkflowService(get_repository())
    return service.update_workflow(workflow_id, name, description, abbreviation)

@mcp.tool()
def delete_workflow(workflow_id: int) -> dict:
    """
    Delete workflow from DRAFT playbook (cascades to activities).
    
    :param workflow_id: workflow ID as int. Example: 1
    :return: Confirmation dict. Example: {"deleted": True, "workflow_id": 1}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If workflow does not exist
    """
    service = WorkflowService(get_repository())
    return service.delete_workflow(workflow_id)

# Activity CRUD Tools

@mcp.tool()
def create_activity(
    workflow_id: int,
    name: str,
    guidance: str,
    order: int = 1,
    phase: str | None = None
) -> dict:
    """
    Create activity in workflow (DRAFT playbook only).
    
    :param workflow_id: parent workflow ID as int. Example: 1
    :param name: activity name as str. Example: "Design Component API"
    :param guidance: markdown guidance as str. Example: "## API Design\n\nDefine component props..."
    :param order: execution order as int. Example: 1
    :param phase: optional phase grouping as str or None. Example: "Planning"
    :return: Created activity dict. Example: {"id": 1, "name": "Design Component API", "workflow_id": 1}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If workflow does not exist
    """
    service = ActivityService(get_repository())
    return service.create_activity(workflow_id, name, guidance, order, phase)

@mcp.tool()
def list_activities(workflow_id: int) -> list[dict]:
    """
    List all activities in workflow, ordered by execution order.
    
    :param workflow_id: workflow ID as int. Example: 1
    :return: List of activity dicts. Example: [{"id": 1, "name": "Design API", "order": 1}, {"id": 2, "name": "Implement", "order": 2}]
    :raises NotFoundError: If workflow does not exist
    """
    service = ActivityService(get_repository())
    return service.list_activities(workflow_id)

@mcp.tool()
def get_activity(activity_id: int) -> dict:
    """
    Get activity details with dependencies.
    
    :param activity_id: activity ID as int. Example: 1
    :return: Activity dict with predecessors/successors. Example: {"id": 1, "name": "Design API", "predecessors": [], "successors": [{"id": 2}]}
    :raises NotFoundError: If activity does not exist
    """
    service = ActivityService(get_repository())
    return service.get_activity_detail(activity_id)

@mcp.tool()
def update_activity(
    activity_id: int,
    name: str | None = None,
    guidance: str | None = None,
    order: int | None = None,
    phase: str | None = None
) -> dict:
    """
    Update activity in DRAFT playbook. Increments parent playbook version.
    
    :param activity_id: activity ID as int. Example: 1
    :param name: new name as str or None
    :param guidance: new guidance as str or None
    :param order: new order as int or None
    :param phase: new phase as str or None
    :return: Updated activity dict. Example: {"id": 1, "name": "Updated Design API"}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If activity does not exist
    """
    service = ActivityService(get_repository())
    return service.update_activity(activity_id, name, guidance, order, phase)

@mcp.tool()
def delete_activity(activity_id: int) -> dict:
    """
    Delete activity from DRAFT playbook.
    
    :param activity_id: activity ID as int. Example: 1
    :return: Confirmation dict. Example: {"deleted": True, "activity_id": 1}
    :raises PermissionError: If parent playbook status is 'released'
    :raises NotFoundError: If activity does not exist
    """
    service = ActivityService(get_repository())
    return service.delete_activity(activity_id)

@mcp.tool()
def set_activity_predecessor(
    activity_id: int,
    predecessor_id: int
) -> dict:
    """
    Set predecessor dependency (DRAFT playbook only).
    
    :param activity_id: activity ID as int. Example: 2
    :param predecessor_id: predecessor activity ID as int. Example: 1
    :return: Updated activity dict. Example: {"id": 2, "predecessors": [{"id": 1}]}
    :raises PermissionError: If parent playbook status is 'released'
    :raises ValidationError: If creates circular dependency
    :raises NotFoundError: If either activity does not exist
    """
    service = ActivityService(get_repository())
    return service.set_predecessor(activity_id, predecessor_id)

@mcp.tool()
def set_activity_successor(
    activity_id: int,
    successor_id: int
) -> dict:
    """
    Set successor dependency (DRAFT playbook only).
    
    :param activity_id: activity ID as int. Example: 1
    :param successor_id: successor activity ID as int. Example: 2
    :return: Updated activity dict. Example: {"id": 1, "successors": [{"id": 2}]}
    :raises PermissionError: If parent playbook status is 'released'
    :raises ValidationError: If creates circular dependency
    :raises NotFoundError: If either activity does not exist
    """
    service = ActivityService(get_repository())
    return service.set_successor(activity_id, successor_id)
```

**Django Management Command**:

```python
# mcp/management/commands/mcp_server.py
import os
import django
from django.core.management.base import BaseCommand

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mimir.settings')
django.setup()

from mcp.tools import mcp

class Command(BaseCommand):
    help = 'Run the MCP server'
    
    def handle(self, *args, **options):
        # FastMCP handles everything
        mcp.run()
```

**Project Structure**:

```
mimir/
├── mimir/                      # Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── methodology/                # Core app
│   ├── models/
│   │   ├── __init__.py
│   │   ├── node.py
│   │   ├── edge.py
│   │   ├── version.py
│   │   └── pip.py
│   ├── repository/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract base
│   │   └── django_orm.py       # SQLite implementation
│   ├── services/
│   │   ├── __init__.py
│   │   ├── methodology_service.py
│   │   ├── planning_service.py
│   │   └── assessment_service.py
│   └── views/                  # Django web UI
│       ├── __init__.py
│       ├── methodology_views.py
│       └── pip_views.py
├── mcp/                        # MCP integration
│   ├── __init__.py
│   ├── tools.py                # FastMCP @tool decorators
│   └── management/
│       └── commands/
│           └── mcp_server.py   # Django command
├── manage.py
└── requirements.txt
```

**requirements.txt**:
```
django>=5.0
fastmcp>=0.1.0
graphviz>=0.20
python-dotenv>=1.0.0
# For AI features (optional)
openai>=1.0.0
```

**System dependency**:
```bash
# macOS
brew install graphviz

# Ubuntu/Debian
apt-get install graphviz
```

## Web UI Architecture

### UI Design Conventions

**Visual Identity**:
- **Primary Icon**: `fa-book-sparkles` (Font Awesome Pro) represents playbooks/methodologies throughout the application
- **Branding**: "Your Ever-Evolving Engineering Playbook" - emphasizes practical, modular, AI-enhanced approach
- **Terminology**: User-facing language uses "playbook" (accessible, modern) while internal code uses "Methodology" models (technical accuracy)

**Icon Usage**:
- **Playbook/Methodology**: `fa-book-sparkles` - primary identifier across nav, pages, footer
- **Process Improvements**: `fa-lightbulb` - for PIPs (Process Improvement Proposals)
- **Versions**: `fa-code-branch` - for version history and tracking
- **Actions**: All buttons/links include semantic Font Awesome icons per UI guidelines

### Django Implementation Details

**User Model**:
- Extends Django's standard User model (`AbstractUser`)
- **Username** is the primary login identifier (3–30 chars); email is stored separately and must be unique
- Additional custom fields:
  - `accepted_tos_at: DateTimeField (null, blank)` — timestamp recorded at registration when the user accepts ToS
- `UserEmailVerification` (one-to-one to `User`): `is_verified: bool`, `verification_token: str (64)`, `token_created_at: DateTimeField` — tracks whether the current email address has been verified; staff/superuser accounts are auto-verified
- Password hashing via Django's built-in PBKDF2 algorithm

**Forms and Templates**:
- **No Django Forms**: We build custom views and templates following `docs/ux/IA_guidelines.md`
- Direct template rendering with manual field handling
- Server-side validation in views
- Bootstrap components styled per IA guidelines
- HTMX for dynamic form interactions

**URL Routing Convention**:

Format: `/{system-part}/{entity}/{action}/{id}`

**Examples**:
```python
# Pattern: /{system-part}/{entity}/{action}/{id}
/playbooks/playbook/list/              # List all playbooks
/playbooks/playbook/create/            # Create new playbook
/playbooks/playbook/view/abc-123/      # View specific playbook
/playbooks/playbook/edit/abc-123/      # Edit specific playbook
/playbooks/playbook/delete/abc-123/    # Delete specific playbook

/workflows/workflow/list/
/workflows/workflow/view/xyz-789/

/activities/activity/create/
/activities/activity/edit/def-456/

/auth/user/login/                      # Authentication endpoints
/auth/user/logout/
/auth/user/register/
/auth/user/verify-email/<token>/       # Email verification one-click link
/auth/user/profile/                    # View profile (name, email+badge, token, PIPs, playbooks)
/auth/user/profile/edit/               # Edit first name, last name, email
/auth/user/profile/regenerate-token/  # POST — rotate API token (requires current password)
```

**URL Structure Rules**:
- System part: Plural form (e.g., "playbooks", "workflows", "activities")
- Entity: Singular form (e.g., "playbook", "workflow", "activity")
- Action: Lowercase verb (e.g., "list", "create", "view", "edit", "delete")
- ID: UUID or slug (optional, depends on action)

**Testing Infrastructure**:
- All tests located in `tests/` directory
- Test runner: **pytest** (not Django's default `unittest`)
- Configuration: `pytest.ini` or `pyproject.toml`
- Django integration: `pytest-django` plugin
- Fixtures: Shared test data in `tests/fixtures/`
- Test database: SQLite in-memory for speed

**Testing Structure**:
```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── fixtures/                # Shared test data
│   ├── users.py
│   ├── methodologies.py
│   └── workflows.py
├── unit/                    # Unit tests for services, repositories
│   ├── test_methodology_service.py
│   └── test_repository.py
├── integration/             # Integration tests for views, HTMX
│   ├── test_playbook_views.py
│   ├── test_workflow_views.py
│   └── test_auth_views.py
└── e2e/                     # End-to-end scenarios (if needed)
    └── test_user_journeys.py
```

**Test Execution**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=methodology --cov-report=html

# Run specific test file
pytest tests/integration/test_playbook_views.py

# Run tests matching pattern
pytest -k "test_playbook"

# Run with verbose output
pytest -v
```

### Technology Choice: HTMX + Graphviz

**Motivation**: 

The FOB web UI needs to display complex graph structures (workflows, activity dependencies, goal hierarchies) while remaining:
1. **Easy to test** - Standard Django test framework without browser automation
2. **Simple to maintain** - Minimal JavaScript, no build toolchain
3. **Server-rendered** - Fast initial load, SEO-friendly
4. **Interactive** - Dynamic updates without full page reloads

**Solution**: HTMX for interactivity + Graphviz for graph visualization

### Why Not JavaScript Frameworks?

**Rejected: React/Vue/Svelte**
- ❌ Requires complex build toolchain (webpack, vite)
- ❌ Testing requires browser automation (Playwright, Selenium)
- ❌ State management complexity
- ❌ Hydration and SSR complexity
- ❌ Large bundle sizes

**Rejected: Plain JavaScript + D3.js/Cytoscape.js**
- ❌ Still requires significant JS code
- ❌ Testing graph interactions complex
- ❌ Layout algorithms need manual tuning
- ❌ Accessibility harder to implement

**Chosen: HTMX + Graphviz**
- ✅ Zero build step - just include HTMX script tag
- ✅ Standard Django tests work (no browser needed)
- ✅ Server-side graph layout (Graphviz)
- ✅ Progressive enhancement
- ✅ 14KB library (HTMX), very stable

### Architecture Pattern

```
User Action (click, select)
    ↓
HTMX intercepts → Makes HTTP request
    ↓
Django View (standard Django code)
    ↓
Service Layer (business logic)
    ↓
Repository (data access)
    ↓
Django Template (renders HTML fragment)
    ↓
HTMX swaps fragment into DOM
```

**Key Insight**: From testing perspective, HTMX endpoints are just Django views returning HTML. Test them like any Django view.

### Component Patterns

#### Pattern 1: Navigation with HTMX

**Use Case**: Methodology/version selector, tree navigation

```python
# views.py
def methodology_version_view(request, methodology_id, version_id):
    """
    HTMX endpoint - returns version content HTML fragment.
    
    :param request: Django request object. Example: HttpRequest(method='GET')
    :param methodology_id: methodology UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    :param version_id: version UUID as str. Example: "b2c3d4e5-f6a7-8901-bcde-f1234567890a"
    :return: Rendered HTML response. Example: HttpResponse(status=200, content="<div>...</div>")
    :raises Http404: If version does not exist.
    """
    version = get_object_or_404(Version, id=version_id)
    workflows = version.workflows.all()
    goals = version.goals.filter(parent__isnull=True)
    
    return render(request, 'methodology/partials/version_view.html', {
        'version': version,
        'workflows': workflows,
        'goals': goals
    })
```

```html
<!-- Template -->
<select hx-get="/methodology/{{ methodology.id }}/version/" 
        hx-target="#content"
        hx-swap="innerHTML">
    {% for version in versions %}
    <option value="{{ version.id }}">{{ version.version_number }}</option>
    {% endfor %}
</select>

<div id="content">
    <!-- HTMX replaces this content -->
</div>
```

**Testing**:
```python
def test_version_view(self):
    url = reverse('version_view', args=[self.methodology.id, self.version.id])
    response = self.client.get(url)
    
    self.assertEqual(response.status_code, 200)
    self.assertContains(response, self.version.version_number)
    self.assertTemplateUsed(response, 'methodology/partials/version_view.html')
```

#### Pattern 2: Graph Visualization with Graphviz

**Use Case**: Workflow diagrams, activity dependencies, goal hierarchies

```python
# services/graph_service.py
import graphviz

class GraphService:
    def __init__(self, repo):
        """
        Initialize graph service with repository.
        
        :param repo: methodology repository instance. Example: DjangoORMRepository()
        """
        self.repo = repo
    
    def generate_workflow_graph(self, workflow_id):
        """
        Generate SVG graph of workflow activities using Graphviz.
        
        :param workflow_id: workflow UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        :return: SVG markup as str. Example: "<svg width='500' height='300'>...</svg>"
        :raises NotFoundError: If workflow does not exist.
        """
        workflow = self.repo.get_workflow(workflow_id)
        activities = self.repo.get_activities_for_workflow(workflow_id)
        
        # Create directed graph
        dot = graphviz.Digraph(comment=workflow.name)
        dot.attr(rankdir='TB')  # Top to bottom layout
        dot.attr('node', shape='box', style='filled', fillcolor='lightblue')
        
        # Add activity nodes
        for activity in activities:
            label = f"{activity.name}\\n({activity.agent.name})"
            dot.node(
                str(activity.id), 
                label,
                href=f'/activity/{activity.id}/',  # Clickable in SVG
                target='_top'
            )
        
        # Add dependency edges
        for activity in activities:
            for successor in activity.get_successors():
                # Label edge with artifact
                artifacts = activity.get_artifacts_to(successor)
                label = ', '.join(d.name for d in artifacts[:2])
                dot.edge(str(activity.id), str(successor.id), label=label)
        
        # Generate SVG
        svg_bytes = dot.pipe(format='svg')
        return svg_bytes.decode('utf-8')

# views.py
def workflow_detail(request, workflow_id):
    """
    Show workflow with graph visualization.
    
    :param request: Django request object. Example: HttpRequest(method='GET')
    :param workflow_id: workflow UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    :return: Rendered HTML response with SVG graph. Example: HttpResponse(status=200, content="<div><h2>Build Feature</h2><svg>...</svg></div>")
    :raises Http404: If workflow does not exist.
    """
    graph_service = GraphService(DjangoORMRepository())
    svg = graph_service.generate_workflow_graph(workflow_id)
    
    workflow = get_object_or_404(Workflow, id=workflow_id)
    
    return render(request, 'methodology/partials/workflow_detail.html', {
        'workflow': workflow,
        'svg': svg
    })
```

```html
<!-- Template -->
<div class="workflow-detail">
    <h2>{{ workflow.name }}</h2>
    
    <div class="graph-container">
        {{ svg|safe }}
    </div>
</div>

<style>
.graph-container svg {
    max-width: 100%;
    height: auto;
}
/* SVG links work with HTMX */
.graph-container svg a {
    cursor: pointer;
}
</style>
```

**Testing**:
```python
def test_workflow_graph_generation(self):
    # Create test data
    workflow = Workflow.objects.create(name="Build Feature")
    activity1 = Activity.objects.create(name="Design", workflow=workflow)
    activity2 = Activity.objects.create(name="Implement", workflow=workflow)
    activity1.successors.add(activity2)
    
    # Test view
    url = reverse('workflow_detail', args=[workflow.id])
    response = self.client.get(url)
    
    self.assertEqual(response.status_code, 200)
    self.assertIn(b'<svg', response.content)  # Contains SVG
    self.assertContains(response, 'Design')
    self.assertContains(response, 'Implement')
```

**No browser needed - just check HTML/SVG content!**

#### Pattern 3: Detail Views with HTMX

**Use Case**: Activity detail, showing all links (predecessors, successors, skills)

```python
def activity_detail(request, activity_id):
    """
    HTMX endpoint - returns activity detail HTML fragment.
    
    :param request: Django request object. Example: HttpRequest(method='GET')
    :param activity_id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    :return: Rendered HTML response with activity details. Example: HttpResponse(status=200, content="<div data-testid='activity-detail'>...</div>")
    :raises Http404: If activity does not exist.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    
    context = {
        'activity': activity,
        'predecessors': activity.get_predecessors(),
        'successors': activity.get_successors(),
        'skills': activity.skills.all(),
        'artifacts_produced': activity.artifacts_produced.all(),
        'artifacts_consumed': activity.artifacts_consumed.all(),
        'agent': activity.agent
    }
    
    return render(request, 'methodology/partials/activity_detail.html', context)
```

```html
<!-- Clicking node in graph loads detail -->
<div id="detail-panel">
    <!-- HTMX loads content here -->
</div>

<script>
// Minimal JS to make SVG links work with HTMX
document.body.addEventListener('htmx:afterSettle', function(evt) {
    // Make SVG links trigger HTMX
    document.querySelectorAll('.graph-container svg a').forEach(link => {
        link.setAttribute('hx-get', link.href.pathname);
        link.setAttribute('hx-target', '#detail-panel');
        link.setAttribute('hx-swap', 'innerHTML');
        link.removeAttribute('href');
        htmx.process(link);
    });
});
</script>
```

#### Pattern 4: Forms with HTMX

**Use Case**: Add/edit/delete activities, workflows, skills

```python
def activity_edit(request, activity_id):
    """
    Edit activity - returns form or updated detail view.
    
    :param request: Django request object. Example: HttpRequest(method='POST', POST={'name': 'Design Component'})
    :param activity_id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    :return: Form HTML on GET or detail HTML on successful POST. Example: HttpResponse(status=200, content="<form>...</form>")
    :raises Http404: If activity does not exist.
    """
    activity = get_object_or_404(Activity, id=activity_id)
    
    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            # Return updated detail view (not form)
            return activity_detail(request, activity_id)
    else:
        form = ActivityForm(instance=activity)
    
    return render(request, 'methodology/partials/activity_form.html', {
        'form': form,
        'activity': activity
    })

def activity_delete(request, activity_id):
    """
    Delete activity and trigger workflow refresh.
    
    :param request: Django request object. Example: HttpRequest(method='POST')
    :param activity_id: activity UUID as str. Example: "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    :return: Empty response with HTMX trigger header. Example: HttpResponse(status=200, content='', headers={'HX-Trigger': 'workflowChanged'})
    :raises Http404: If activity does not exist.
    """
    if request.method == 'POST':
        activity = get_object_or_404(Activity, id=activity_id)
        workflow_id = activity.workflow.id
        activity.delete()
        
        # Return empty with trigger to refresh workflow
        response = HttpResponse('')
        response['HX-Trigger'] = 'workflowChanged'
        return response
```

```html
<!-- Edit button -->
<button hx-get="/activity/{{ activity.id }}/edit/"
        hx-target="#detail-panel"
        hx-swap="innerHTML">
    Edit Activity
</button>

<!-- Form template -->
<form hx-post="/activity/{{ activity.id }}/edit/"
      hx-target="#detail-panel"
      hx-swap="innerHTML">
    {% csrf_token %}
    {{ form.as_p }}
    <button type="submit">Save</button>
    <button hx-get="/activity/{{ activity.id }}/"
            hx-target="#detail-panel">
        Cancel
    </button>
</form>
```

**Testing**:
```python
def test_activity_edit(self):
    url = reverse('activity_edit', args=[self.activity.id])
    response = self.client.post(url, {
        'name': 'Updated Activity',
        'description': 'New description',
        'role': self.role.id
    })
    
    self.activity.refresh_from_db()
    self.assertEqual(self.activity.name, 'Updated Activity')
    # Check it returns detail view, not form
    self.assertTemplateUsed(response, 'methodology/partials/activity_detail.html')
```

### Three-Panel Layout

```
┌─────────────────────────────────────────────┐
│  Navigation Panel   │  Main Content  │ Detail │
│                     │                │        │
│  - Methodology      │  Graph or      │Activity│
│    selector         │  Tree view     │details │
│  - Version select   │                │        │
│  - Goal tree        │  [SVG Graph]   │Links:  │
│    • Goal 1         │                │- Preds │
│      • Goal 1.1     │                │- Succs │
│    • Goal 2         │                │- Skills│
│                     │                │        │
│                     │                │[Edit]  │
└─────────────────────────────────────────────┘
```

Each panel updates independently via HTMX.

### Testing Strategy

**Core Principle**: Test server-side behavior, not browser behavior.

```python
class MethodologyUITest(TestCase):
    """Test methodology UI without browser"""
    
    def test_navigation_returns_correct_content(self):
        """Test HTMX navigation endpoint"""
        response = self.client.get(f'/version/{self.version.id}/')
        self.assertContains(response, self.version.version_number)
    
    def test_graph_contains_all_activities(self):
        """Test graph generation includes all activities"""
        response = self.client.get(f'/workflow/{self.workflow.id}/')
        svg_content = response.content.decode('utf-8')
        
        for activity in self.workflow.activities.all():
            self.assertIn(activity.name, svg_content)
    
    def test_activity_edit_updates_and_returns_detail(self):
        """Test edit form saves and returns detail view"""
        response = self.client.post(
            f'/activity/{self.activity.id}/edit/',
            {'name': 'New Name', 'role': self.role.id}
        )
        
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.name, 'New Name')
        self.assertTemplateUsed(response, 'partials/activity_detail.html')
```

**No Selenium, no Playwright, no browser - just Django test client!**

### File Organization

```
methodology/
├── views/
│   ├── __init__.py
│   ├── methodology_views.py    # Methodology CRUD
│   ├── activity_views.py        # Activity CRUD
│   ├── workflow_views.py        # Workflow + graphs
│   └── htmx_views.py           # HTMX-specific endpoints
├── services/
│   ├── graph_service.py        # Graphviz graph generation
│   └── methodology_service.py  # Business logic
├── templates/
│   └── methodology/
│       ├── explorer.html       # Main page
│       └── partials/           # HTMX fragments
│           ├── version_view.html
│           ├── workflow_detail.html
│           ├── activity_detail.html
│           ├── activity_form.html
│           └── goal_tree.html
└── static/
    └── css/
        └── methodology.css
```

### Progressive Enhancement

The UI works without JavaScript:
- Regular links instead of HTMX (full page loads)
- Forms submit normally
- Graphs still render (static SVG)

With HTMX:
- Smooth partial updates
- No page flicker
- Better UX

**This means graceful degradation is built-in.**

## BDD Feature Files & UI Specifications

**Location**: `docs/features/act-*/`

The FOB Web UI is comprehensively documented through **62 BDD-style Gherkin feature files** organized by user journey Acts (0-15). These serve as both specifications and test scenarios.

### Feature File Organization

```
docs/features/
├── act-0-auth/              # Authentication, Registration, Email Verification, Onboarding, Navigation (4 files)
├── act-2-playbooks/         # Playbooks CRUDLF (5 files)
├── act-3-workflows/         # Workflows CRUDLF (5 files)
├── act-4-phases/            # Phases CRUDLF (5 files) - OPTIONAL entity
├── act-5-activities/        # Activities CRUDLF (5 files)
├── act-6-artifacts/         # Artifacts CRUDLF (5 files)
├── act-7-agents/            # Agents CRUDLF (5 files)
├── act-8-skills/            # Skills CRUDLF (5 files)
├── act-9-pips/              # PIPs Create & Manage (2 files)
├── act-10-import-export/    # Import/Export (1 file)
├── act-11-family/           # Family Management (1 file)
├── act-12-sync/             # Sync Scenarios (1 file)
├── act-13-mcp/              # MCP Integration (1 file)
├── act-14-profile/          # User profile — view + edit/token (2 files)
└── act-15-errors/           # Error Recovery (1 file)
```

### CRUDLF Pattern

**Core entities follow CRUDLF pattern** (5 operations per entity):
- **C**reate - `FOB-{ENTITY}-CREATE_{ENTITY}-1`
- **R**ead/View - `FOB-{ENTITY}-VIEW_{ENTITY}-1`
- **U**pdate/Edit - `FOB-{ENTITY}-EDIT_{ENTITY}-1`
- **D**elete - `FOB-{ENTITY}-DELETE_{ENTITY}-1`
- **L**ist + **F**ind - `FOB-{ENTITY}-LIST+FIND-1`

**Example**: Playbooks (Act 2)
- `playbooks-list-find.feature` - Browse and search playbooks
- `playbooks-create.feature` - Create new playbook with metadata
- `playbooks-view.feature` - View playbook details, workflows, versioning
- `playbooks-edit.feature` - Edit playbook properties
- `playbooks-delete.feature` - Delete with confirmation and cascade handling

### Screen Naming Convention

All screens follow: **`FOB-{ENTITY}-{ACTION}-{VERSION}`**

Examples:
- `FOB-PLAYBOOKS-LIST+FIND-1` - Playbooks list/search page
- `FOB-ACTIVITIES-CREATE_ACTIVITY-1` - Activity creation form
- `FOB-WORKFLOWS-VIEW_WORKFLOW-1` - Workflow detail page
- `FOB-PIPS-CREATE_PIP-1` - PIP creation modal
- `FOB-SETTINGS-1` - Settings page

### Feature File Coverage

**Total Coverage**: 47 feature files, ~3,500 lines of Gherkin
- **Acts 0-1**: Foundation (auth, onboarding, dashboard, navigation)
- **Acts 2-8**: Full CRUDLF for 7 core entities (35 files)
- **Acts 9-15**: Supporting features (PIPs, import/export, family, sync, MCP, settings, errors)

**Scenario Types**:
- Happy path workflows
- Form validation and error handling
- Navigation and state transitions
- Edge cases and empty states
- Permission checks
- Cascade operations (e.g., delete with dependencies)

### Integration with Architecture

**Feature files define**:
- All UI screens and modals
- User interactions and workflows
- Form fields and validation rules
- Navigation patterns
- HTMX endpoints (partial updates)
- Success/error states

**Architecture implements**:
- Django views returning HTML fragments (HTMX)
- Service layer for business logic
- Repository pattern for data access
- Graphviz for visualizations

**Testing approach**:
- Feature files → BDD specifications
- Django test client → Verify HTML responses
- No browser automation needed (server-side testing)

### Reference Documents

- **User Journey**: `docs/ux/user_journey.md` - Complete Acts 0-15 narrative
- **Screen Flow**: `docs/ux/2_dialogue-maps/screen-flow.drawio` - Visual flow diagram
- **Feature Files**: `docs/features/act-*/` - Detailed BDD specifications

## Data Model

### Core Entities

**Node Model**
```python
class Node(models.Model):
    """Base for all methodology entities"""
    id = models.UUIDField(primary_key=True)
    type = models.CharField(max_length=50)
    # 7 Core Entities: 'playbook', 'workflow', 'phase', 'activity', 
    # 'artifact', 'agent', 'skill'
    # Note: 'phase' is OPTIONAL for grouping activities within workflows
    version = models.ForeignKey('Version', on_delete=models.CASCADE)
    attributes = models.JSONField()
    # Flexible schema for type-specific properties
    created_at = models.DateTimeField(auto_now_add=True)
```

**Edge Model**
```python
class Edge(models.Model):
    """Relationships between nodes"""
    id = models.UUIDField(primary_key=True)
    from_node = models.ForeignKey(Node, related_name='outgoing')
    to_node = models.ForeignKey(Node, related_name='incoming')
    relationship_type = models.CharField(max_length=50)
    # 'has_predecessor', 'has_successor', 'produces_artifact', 
    # 'requires_artifact', 'performed_by_agent', 'guided_by_skill', 
    # 'belongs_to_phase', 'part_of_workflow'
    version = models.ForeignKey('Version', on_delete=models.CASCADE)
    attributes = models.JSONField(default=dict)
```

**Version Model**
```python
class Version(models.Model):
    """Tracks methodology versions"""
    id = models.UUIDField(primary_key=True)
    methodology = models.ForeignKey('Methodology')
    version_number = models.CharField(max_length=20)  # "1.0", "1.1"
    parent_version = models.ForeignKey('self', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_from_pip = models.ForeignKey('PIP', null=True)
    description = models.TextField()
```

**Methodology Model**
```python
class Methodology(models.Model):
    """Top-level methodology container"""
    id = models.UUIDField(primary_key=True)
    name = models.CharField(max_length=100)  # "FDD", "Scrum", "BDD"
    family = models.CharField(max_length=100)  # "Software Engineering"
    access_level = models.CharField(max_length=20)  # "LITE", "FULL"
    current_version = models.ForeignKey('Version')
    source_methodology_id = models.UUIDField(null=True)
    # Links to HOMEBASE methodology
    last_synced = models.DateTimeField(null=True)
```

### Evolution Tracking

**PIP Model (Process Improvement Proposal)**
```python
class PIP(models.Model):
    """Tracks proposed methodology changes"""
    id = models.UUIDField(primary_key=True)
    methodology = models.ForeignKey('Methodology')
    version = models.ForeignKey('Version')
    
    # Trigger
    trigger_type = models.CharField(
        choices=[('ai_suggestion', 'AI'), ('manual', 'Manual')]
    )
    trigger_context = models.JSONField()
    # Work order ID, files involved, errors encountered, etc.
    
    # Proposal
    change_type = models.CharField(
        choices=[('modify', 'Modify'), ('add', 'Add'), ('delete', 'Delete')]
    )
    target_node = models.ForeignKey(Node, null=True)
    proposed_changes = models.JSONField()
    reasoning = models.TextField()
    
    # Review
    status = models.CharField(
        choices=[
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected')
        ],
        default='pending'
    )
    reviewer = models.CharField(max_length=100, blank=True)
    reviewer_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True)
    
    # Propagation
    transmitted_to_source = models.BooleanField(default=False)
    transmitted_at = models.DateTimeField(null=True)
    source_pip_id = models.UUIDField(null=True)
    source_status = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
```

## MCP Interface (FastMCP)

**Implementation**: Mimir uses [FastMCP](https://github.com/jlowin/fastmcp) as a wrapper around Mimir's own REST API endpoints. MCP tools make authenticated HTTP calls to `BASE_URL/api/…` rather than importing services directly — this decouples the MCP layer from the Django ORM and allows the MCP server to run as a fully independent process.

**Configuration** (in Cursor / Windsurf MCP settings):
```json
{
  "mimir": {
    "command": "python",
    "args": ["-m", "mcp_integration.server"],
    "env": {
      "BASE_URL": "http://localhost:8000",
      "TOKEN": "<your-FOB-auth-token>"
    }
  }
}
```

**Architecture Benefits**:
- No direct DB access from MCP — all reads/writes go through validated API endpoints
- MCP server can run in any process without Django ORM setup
- `BASE_URL` + `TOKEN` are the only configuration required
- Type-safe — Python type hints → JSON Schema automatically via FastMCP
- Testable — MCP tools tested against real API responses, not mocked services

### Tool 1: query_methodology

**Purpose**: Answer questions about how to perform tasks according to methodology.

**Use Cases**:
- "How do I build a TSX component per FDD methodology?"
- "What are the acceptance criteria for a screen mockup?"
- "What skills are available for unit testing React components?"

**Implementation**:
```python
from fastmcp import FastMCP
from methodology.services import MethodologyService
from methodology.repository import DjangoORMRepository

mcp = FastMCP("Mimir Methodology Assistant")

@mcp.tool()
def query_methodology(
    question: str,
    methodology: str,
    context: str | None = None
) -> dict:
    """
    Query methodology for guidance on how to perform tasks.
    
    :param question: natural language question as str. Example: "How do I build a TSX component per FDD?"
    :param methodology: methodology name as str. Example: "FDD"
    :param context: current work context as str or None. Example: "Working on user profile feature"
    :return: Guidance dict with answer and resources. Example: {"answer": "To build a TSX component...", "relevant_activities": ["SE1: Create Component Structure"], "relevant_skills": ["skill-tsx-component-setup"], "related_artifacts": ["Component Specification", "Unit Tests"]}
    """
    service = MethodologyService(DjangoORMRepository())
    return service.query_guidance(question, methodology, context)
```

**Output Example**:
```python
{
  "answer": "To build a TSX component per FDD...",
  "relevant_activities": ["SE1: Create Component Structure"],
  "relevant_skills": ["skill-tsx-component-setup"],
  "related_artifacts": ["Component Specification", "Unit Tests"]
}
```

### Tool 2: plan_execution

**Purpose**: Generate work plan from methodology and create tasks in issue tracker.

**Use Cases**:
- "Plan implementation of scenario LOG1.1 and Screen LOG per FDD"
- "Create inception phase tasks for user profile feature"

**Implementation**:
```python
from typing import Literal

@mcp.tool()
def plan_execution(
    methodology: str,
    scope: str,
    target_system: Literal["github", "jira"]
) -> dict:
    """
    Generate work plan from methodology and create tasks in issue tracker.
    
    :param methodology: methodology name as str. Example: "FDD"
    :param scope: feature/scenario scope as str. Example: "Plan implementation of scenario LOG1.1 and Screen LOG per FDD"
    :param target_system: issue tracker system as Literal. Example: "github"
    :return: Work plan dict with created issues. Example: {"workflow": "Build Feature", "tasks": [{"id": "#123", "title": "SE1: Create Component Structure", "url": "https://github.com/user/repo/issues/123"}], "summary": "Created 5 tasks for FDD workflow"}
    """
    service = PlanningService(DjangoORMRepository())
    return service.create_execution_plan(methodology, scope, target_system)
```

**Behavior**:
1. Query methodology for relevant workflow
2. Extract activities and their dependencies
3. Generate work orders with artifacts
4. Use GitHub/Jira MCP to create issues
5. Return work plan summary

**Note**: Depends on 3rd party MCPs (GitHub, Atlassian) being available.

### Tool 3: assess_progress

**Purpose**: Evaluate project state against methodology phase requirements.

**Use Cases**:
- "I'm supposed to finish inception phase. Did I produce all required artifacts?"
- "Assess readiness to move from construction to validation phase"

**Implementation**:
```python
@mcp.tool()
def assess_progress(
    phase: str,
    methodology: str
) -> dict:
    """
    Assess project state against methodology phase requirements.
    
    :param phase: phase name as str. Example: "inception"
    :param methodology: methodology name as str. Example: "FDD"
    :return: Assessment dict with artifact status, gaps, and recommendations. Example: {"phase": "inception", "required_artifacts": [{"name": "Feature List", "status": "complete", "quality": "good"}, {"name": "Screen Mockups", "status": "partial", "quality": "needs_review", "gaps": ["Login screen missing"]}], "recommendations": ["Complete Login screen mockup"], "can_proceed": False}
    """
    service = AssessmentService(DjangoORMRepository())
    return service.assess_phase_completion(phase, methodology)
```

**Output Example**:
```python
{
  "phase": "inception",
  "required_artifacts": [
    {
      "name": "Feature List",
      "status": "complete",
      "quality": "good"
    },
    {
      "name": "Screen Mockups",
      "status": "partial",
      "quality": "needs_review",
      "gaps": ["Login screen missing"]
    }
  ],
  "recommendations": [
    "Complete Login screen mockup",
    "Review Security screen for accessibility"
  ],
  "can_proceed": False
}
```

**Behavior**:
1. Query methodology for phase artifacts
2. Scan project (files, issues, PRs) for artifacts
3. Assess completeness and quality
4. Generate recommendations

### Services Layer

**Key Insight**: The `@mcp.tool()` functions are thin wrappers around services. All business logic lives in services, which are shared between MCP and Web UI.

```python
# methodology/services/methodology_service.py
class MethodologyService:
    def __init__(self, repo: MethodologyRepository):
        """
        Initialize methodology service with repository.
        
        :param repo: methodology repository instance. Example: DjangoORMRepository()
        """
        self.repo = repo
    
    def query_guidance(self, question: str, methodology: str, context: str = None) -> dict:
        """
        Query methodology for guidance on tasks - pure business logic.
        
        :param question: natural language question as str. Example: "How do I test a Django view?"
        :param methodology: methodology name as str. Example: "FDD"
        :param context: optional work context as str or None. Example: "Building user authentication"
        :return: Guidance dict with answer and related resources. Example: {"answer": "To test a Django view...", "relevant_activities": ["Write Unit Tests"], "relevant_skills": ["django-test-setup"], "related_artifacts": ["Test Suite"]}
        """
        # Load methodology
        method = self.repo.get_methodology(methodology)
        
        # Semantic search across activities, skills
        relevant_items = self._search_methodology(method, question, context)
        
        # Generate answer
        return {
            "answer": self._generate_answer(relevant_items, question),
            "relevant_activities": [a.name for a in relevant_items['activities']],
            "relevant_skills": [h.name for h in relevant_items['skills']],
            "related_artifacts": [d.name for d in relevant_items['artifacts']]
        }

# Can be called from MCP:
@mcp.tool()
def query_methodology(question, methodology, context=None):
    service = MethodologyService(DjangoORMRepository())
    return service.query_guidance(question, methodology, context)

# Or from Django view:
def query_view(request):
    service = MethodologyService(DjangoORMRepository())
    result = service.query_guidance(
        request.POST['question'],
        request.POST['methodology']
    )
    return JsonResponse(result)
```

### Global Search Service Pattern

**Purpose**: Provide unified search across all domain entities (Playbooks, Workflows, Activities, etc.) with consistent behavior and extensibility.

**MVP Implementation**: Basic text search using case-insensitive substring matching (`icontains`).

**Pattern**:

```python
# methodology/services/global_search_service.py
class GlobalSearchService:
    """Service for global search across methodology entities.
    
    Each domain object type registers itself by implementing search methods
    that define which fields are searchable.
    """
    
    def search(self, query: str, user, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        """Search across all registered entity types.
        
        :param query: Free-text search query. Example: "Component"
        :param user: User performing search. Example: User(username="maria")
        :param filters: Optional filters (type, status, source). Example: {"type": "playbooks", "status": "draft"}
        :return: Dict with entity type as key, list of results as value.
                 Example: {"playbooks": [Playbook(...)], "workflows": [...], "activities": [...]}
        """
        # Normalize query
        normalized_query = (query or "").strip()
        if not normalized_query:
            return {"playbooks": [], "workflows": [], "activities": []}
        
        # Search each entity type
        playbooks = self._search_playbooks(normalized_query, user, filters)
        workflows = self._search_workflows(normalized_query, user, filters)
        activities = self._search_activities(normalized_query, user, filters)
        
        # Apply type filter at aggregation layer
        type_filter = filters.get("type")
        if type_filter:
            return self._apply_type_filter(type_filter, playbooks, workflows, activities)
        
        return {
            "playbooks": list(playbooks),
            "workflows": list(workflows),
            "activities": list(activities),
        }
    
    def _search_playbooks(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Playbook]:
        """Search playbooks by name and description.
        
        Domain object registration: Playbook declares searchable fields.
        """
        base_qs = Playbook.objects.filter(author=user)
        
        # Apply entity-specific filters
        if filters.get("status"):
            base_qs = base_qs.filter(status=filters["status"])
        if filters.get("source"):
            base_qs = base_qs.filter(source=filters["source"])
        
        # Search across declared fields: name, description
        return base_qs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by("-updated_at")
    
    def _search_workflows(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Workflow]:
        """Search workflows by name and description.
        
        Domain object registration: Workflow declares searchable fields.
        """
        base_qs = Workflow.objects.filter(playbook__author=user)
        
        # Search across declared fields: name, description
        return base_qs.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).order_by("playbook", "order")
    
    def _search_activities(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Activity]:
        """Search activities by name and guidance.
        
        Domain object registration: Activity declares searchable fields.
        """
        base_qs = Activity.objects.filter(workflow__playbook__author=user)
        
        # Search across declared fields: name, guidance
        return base_qs.filter(
            Q(name__icontains=query) | Q(guidance__icontains=query)
        ).order_by("workflow", "order")
```

**Domain Object Registration Pattern**:

Each domain entity must:
1. **Declare searchable fields** - Which fields should be searched (name, description, guidance, etc.)
2. **Implement search method** - `_search_{entity_type}()` method in GlobalSearchService
3. **Define access rules** - Filter by user ownership/permissions
4. **Specify ordering** - Default sort order for results

**Example: Adding new entity type "Skill"**:

```python
# 1. Domain object declares searchable fields (implicit via implementation)
class Skill(models.Model):
    name = models.CharField(max_length=200)          # Searchable
    content = models.TextField()                      # Searchable
    tool_specific = models.CharField(max_length=100)  # Not searchable
    author = models.ForeignKey(User)                  # Access control

# 2. Register in GlobalSearchService
class GlobalSearchService:
    def search(self, query, user, filters=None):
        # ... existing code ...
        skills = self._search_skills(normalized_query, user, filters)

        return {
            "playbooks": list(playbooks),
            "workflows": list(workflows),
            "activities": list(activities),
            "skills": list(skills),  # New entity type
        }

    def _search_skills(self, query: str, user, filters: Dict[str, Any]) -> QuerySet[Skill]:
        """Search skills by name and content.

        Domain object registration: Skill declares searchable fields.
        """
        base_qs = Skill.objects.filter(author=user)

        # Search across declared fields: name, content
        return base_qs.filter(
            Q(name__icontains=query) | Q(content__icontains=query)
        ).order_by("name")
```

**Future Enhancement: Semantic Search**:

The MVP uses basic substring matching (`icontains`). Future versions can upgrade to semantic search:

1. **Add embeddings** - Generate vector embeddings for searchable fields
2. **Vector database** - Store embeddings in pgvector, Pinecone, or similar
3. **Semantic matching** - Use cosine similarity instead of substring matching
4. **Hybrid search** - Combine keyword and semantic search with ranking

The service interface remains the same - only internal implementation changes.

**Benefits**:
- ✅ Consistent search behavior across all entity types
- ✅ Easy to add new searchable entities
- ✅ Respects user ownership and permissions
- ✅ Extensible to semantic search without API changes
- ✅ Type filtering at aggregation layer (can be optimized to DB level)

## Methodology Ontology

### Core Concepts

**Activity**: The *what* - a unit of work with generic guidance
- Example: "Create screen mockup"
- Properties: name, description, goals, required skills
- Produces: Artifacts
- Consumes: Artifacts (from predecessors)
- Guided by: Skills

**Skill**: The *how* - specific implementation instructions
- Example: "Creating mockups with Figma and Shadcn UI Kit"
- Properties: name, tool_specific, steps, examples
- Can be attached to multiple activities

**Workflow**: Sequence of activities for a process
- Example: "Implement the Feature"
- Properties: name, phases, entry/exit criteria
- Contains: Activities with dependency graph

**Artifact**: Output/input of activities
- Example: "Feature File", "Acceptance Test", "TSX Component"
- Properties: name, type, format, acceptance criteria, required status
- Purpose: Connect activities (output → input)

**Agent**: AI assistant that performs activities
- Example: "Cautious Developer (drdobbs-v2)", "UX Researcher Agent"
- Each agent has specific capabilities, guidelines, and behavioral patterns
- Reference: .github/agents/ for agent definitions

**Goal**: What an activity aims to achieve
- Example: "Ensure component meets design system"
- Fulfilled by: Activities

### Extensible Ontology

The ontology can be extended by users:

1. Define new node type in Web UI
2. Specify properties and relationships
3. System introspects new type
4. Auto-generates `/api/{new_type}/*` endpoints
5. New type available in methodology editor

Example: Add "Decision" type to track architectural decisions made during activities.

## AI-Driven Evolution

### Fitness Function

**Primary Metric**: Number of corrections required to complete work correctly (target: zero)

**What counts as a correction**:
- Code changes after review feedback
- Rework due to missing requirements
- Artifact doesn't meet acceptance criteria
- Downstream activity can't proceed

### Root Cause Analysis

When corrections occur, Saga AI analyzes:

1. **Activity definition**: Is the activity poorly defined? Ambiguous?
2. **Upstream gaps**: Are predecessor activities missing key outputs?
3. **Downstream needs**: Do successor activities need different inputs?
4. **Skill effectiveness**: Are the implementation instructions adequate?
5. **Environmental factors**: Are there external blockers?

### PIP Creation

Saga AI generates PIPs with:
- **Context**: What work was being done
- **Problem**: What correction was needed and why
- **Analysis**: Root cause identification
- **Proposal**: Specific methodology change to prevent recurrence
- **Expected impact**: Predicted fitness improvement

### Learning Loop

```
Work Execution
    ↓
Corrections tracked
    ↓
Saga analyzes root causes
    ↓
Saga proposes PIP
    ↓
Human reviews (approve/reject + reasoning)
    ↓
Saga learns from decision
    ↓
Improved PIP proposals next time
```

## Implementation Phases

### Phase 1: MVP - Stand-alone FOB
- Django project setup
- Install FastMCP: `pip install fastmcp`
- Node/Edge/Version/Methodology/PIP models
- Repository interface + Django ORM implementation
- Services layer (MethodologyService, PlanningService, AssessmentService)
- FastMCP tools module with `@mcp.tool()` decorators
- MCP server management command: `mcp.run()`
- Implement `query_methodology` tool
- Simple web UI for viewing Playbooks, Workflows, Activities, Skills, Artifacts, Agents

### Phase 2: Evolution Workflow
- PIP creation interface (manual)
- PIP review UI (approve/reject)
- Version creation on PIP approval
- Version diff viewer
- Methodology sync from source (management command)

### Phase 3: Advanced MCP Tools
- `plan_execution` tool
- Integration with GitHub/Jira MCPs
- `assess_progress` tool
- Project scanning and analysis
- AI-generated PIP creation from MCP

### Phase 4: HOMEBASE
- Neo4j repository implementation
- Django + HTMX web UI
- Eventing → Neo4j for methodology storage
- Access control system (Family + Level)
- Methodology distribution endpoints
- PIP aggregation from FOBs

### Phase 5: AI Evolution (Saga AI)
- Work order tracking integration
- Correction detection and logging
- Root cause analysis engine
- Automated PIP generation
- Learning from human feedback
- Fitness metric tracking and visualization

## Technology Stack

### FOB (Forward Operating Base)
- **Framework**: Django 5.x
- **Database**: SQLite 3
- **MCP Library**: FastMCP (stdio transport)
- **Web UI**: Django templates + HTMX + Graphviz
- **Graph Visualization**: Graphviz (server-side SVG generation)
- **Python Version**: 3.11+
- **Key Dependencies**: `fastmcp`, `django`, `graphviz`, `htmx` (CDN)

### HOMEBASE (Methodology Repository)
- **Database**: Neo4j 5.x
- **Web UI**: Django + HTMX (same stack as FOB)
- **Storage**: Eventing → Neo4j
- **Python Version**: 3.11+

### AI Components
- **Default Model**: GPT-4o (configurable)
- **Tyr AI**: Task planning and work order generation
- **Saga AI**: Retrospection and improvement suggestions

## Environment Variables Reference

Complete reference for all environment variables consumed by Mimir, grouped by environment. **Set all "Required" variables before starting any environment.** Variables marked "Optional" fall back to safe defaults.

> **Canonical source of truth:** `mimir/settings/base.py`, `mimir/settings/dev.py`, `mimir/settings/prod.py`.  
> **Local template:** `.env.example` (copy to `.env`, never commit `.env`).

---

### Local Development (`.env` loaded by `dev.py` via `python-dotenv`)

| Variable | Required | Example / Default | Notes |
|----------|----------|-------------------|-------|
| `DJANGO_SECRET_KEY` | No | insecure dev default | Override with any 50-char random string for local security |
| `DJANGO_DEBUG` | No | `True` | Set `False` to test production-like behaviour locally |
| `DJANGO_SETTINGS_MODULE` | No | `mimir.settings.dev` | Change to `mimir.settings.prod` to test prod settings |
| `MIMIR_USER` | No | `admin` | Django superuser username created on first migrate |
| `MIMIR_EMAIL` | No | `admin@localhost` | Superuser email |
| `MIMIR_PASSWORD` | No | `changeme` | Superuser password |
| `WEB_PORT` | No | `8000` | Port for `runserver` / Docker host mapping |
| `MCP_PORT` | No | `8001` | Port for MCP SSE facade |
| `ANTHROPIC_API_KEY` | **Yes** (Galdr) | `sk-ant-api03-…` | Required for Galdr AI PIP review. Without it Galdr is disabled (`GALDR_USE_ANTHROPIC=False`). |
| `GALDR_MODEL` | No | `claude-sonnet-4-5` | Any Anthropic model slug |
| `GITHUB_TOKEN` | No | `ghp_…` | GitHub PAT with **Issues: write** on `GITHUB_BUG_REPO`. **If absent**, `BUG_REPORT_DRY_RUN` is auto-set to `True` so the Feedback widget works without filing real issues. |
| `GITHUB_BUG_REPO` | No | `phainestai/mimir` | Target repo for bug reports |
| `BUG_REPORT_DRY_RUN` | No | auto | `1`/`true` to force dry-run even when token is present |
| `USE_SES_IN_DEV` | No | `1` (default on) | Set `0` to print emails to the terminal instead of SES delivery |
| `AWS_SES_REGION_NAME` | If SES | `us-east-1` | Required when `USE_SES_IN_DEV=1` |
| `DEFAULT_FROM_EMAIL` | If SES | `noreply@featurefactory.io` | Must be SES-verified |
| `AWS_SES_CONFIGURATION_SET` | No | `mimir-transactional` | SES configuration set for bounce/open tracking |
| `DATABASE_URL` | No | — | If set, uses Postgres via `dj-database-url`; otherwise SQLite at `mimir.db` |
| `MIMIR_DB_PATH` | No | — | Override SQLite path (used in Docker) |
| `FRONTEND_URL` | No | `http://localhost:8000` | Used in email links |
| `MIMIR_MCP_MODE` | No | `1` | Set by MCP server startup; suppresses console logging on stdio |

---

### Production / Elastic Beanstalk (`mimir.settings.prod`)

EB environment properties are set via the AWS Console, `aws elasticbeanstalk update-environment --option-settings`, or CI/CD (`deploy-idle.sh`). They **persist across deployments** — set once, update only when values change.

#### Core Application

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `DJANGO_SETTINGS_MODULE` | **Yes** | `mimir.settings.prod` | Selects prod settings |
| `DJANGO_SECRET_KEY` | **Yes** | 50-char random | Never reuse across envs; rotate on compromise |
| `DATABASE_URL` | **Yes** | `postgresql://mimir:…@huginn-db…:5432/mimir` | Postgres RDS with SSL |
| `MIMIR_ENV` | No | `prod` | Informational; used in bug report bodies |
| `DJANGO_ALLOWED_HOSTS` | No | `mimir.featurefactory.io,.elasticbeanstalk.com,…` | Comma-separated |
| `CSRF_TRUSTED_ORIGINS` | No | `https://mimir.featurefactory.io,…` | Comma-separated https:// origins |
| `FRONTEND_URL` | No | `https://mimir.featurefactory.io` | Used in email links and redirects |
| `COOKIE_SECURE` | No | `true` | Set `false` only for EB direct HTTP access during blue/green testing |

#### Galdr AI Engine

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `ANTHROPIC_API_KEY` | **Yes** (Galdr) | `sk-ant-api03-…` | Required for Galdr PIP review. Without it, Galdr is disabled. |
| `GALDR_MODEL` | No | `claude-sonnet-4-5` | Any Anthropic model slug |

#### Bug Reports (Feedback Widget → GitHub Issues)

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `GITHUB_TOKEN` | **Yes** | `ghp_…` or `gho_…` | Classic PAT or OAuth token with **Issues: write** on `GITHUB_BUG_REPO`. **Missing = Feedback widget returns "not configured" error.** |
| `GITHUB_BUG_REPO` | No | `phainestai/mimir` | Target repo; this is the default |
| `BUG_REPORT_DRY_RUN` | No | — | `1`/`true` to skip GitHub API (staging diagnostics only) |
| `MIMIR_GIT_REVISION` | No | `v0.0.41` | Set by CI (`deploy-idle.sh`); surfaced in `/health/` and bug report bodies |

> **CI/CD note:** `deploy-idle.sh` sets `MIMIR_GIT_REVISION` on every deploy. It also sets `GITHUB_TOKEN` if the `GH_BUG_REPORT_TOKEN` GitHub Actions secret is present — store it as a repo secret to ensure the token survives future deployments without manual console edits.

#### Email (AWS SES)

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `AWS_SES_REGION_NAME` | **Yes** | `us-east-1` | Must match verified SES identity region |
| `DEFAULT_FROM_EMAIL` | **Yes** | `noreply@featurefactory.io` | Must be SES-verified |
| `AWS_SES_CONFIGURATION_SET` | No | `mimir-transactional` | SES config set for CloudWatch bounce/complaint metrics |
| `AWS_ACCESS_KEY_ID` | If no IAM role | `AKIAxxxxxxxx` | Omit when using EB instance profile (preferred) |
| `AWS_SECRET_ACCESS_KEY` | If no IAM role | `…` | Pair for the above |

> **Best practice:** Attach an IAM instance profile with `ses:SendEmail` to the EB environment — then `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` are not needed.

---

### Quick "is the env healthy?" checklist

Run this to verify all critical variables are set before swap:

```bash
aws elasticbeanstalk describe-configuration-settings \
  --application-name mimir \
  --environment-name <ENV_NAME> \
  --region us-east-1 \
  --query 'ConfigurationSettings[0].OptionSettings[?Namespace==`aws:elasticbeanstalk:application:environment`].{Key:OptionName,Value:Value}' \
  --output table
```

Must-have keys: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, `AWS_SES_REGION_NAME`, `DEFAULT_FROM_EMAIL`, `DJANGO_SETTINGS_MODULE`.

---

## CI/CD Pipeline

### Overview

Mimir CI/CD mirrors the Huginn release model: the pipeline runs **only on published GitHub Releases**
(or `workflow_dispatch`). No push triggers — pushes to `main` produce no CI run.

```
gh release create vX.Y.Z          (sole trigger)
       │
       ▼
  ┌─────────┐     ┌──────────────────┐     ┌───────────────────────┐
  │  Tests  │────▶│ Build & Push     │────▶│ deploy-idle           │
  │ pytest  │     │ Docker images    │     │ (resolve idle by CNAME│
  └─────────┘     └──────────────────┘     │  deploy + smoke test) │
                                           └───────────────────────┘
                                                      │ human review
                                                      ▼
                                           make swap  (or promote.yml)
                                           → promote-prod.sh
                                           → CNAME swap + prod smoke
```

### Trigger Matrix

| Event | Tests | Docker build+push | EB deploy |
|-------|-------|-------------------|-----------|
| Push to `main` (or any branch) | ❌ | ❌ | ❌ |
| **GitHub Release published** | ✅ | ✅ | **✅ → idle** |
| `workflow_dispatch` | ✅ | ✅ | ✅ → idle |

### Docker Images

Two images are built on every release:

| Image | Registry | Purpose |
|-------|----------|---------|
| `featurefactory/mimir-mcp:<tag>` | Docker Hub (public) | MCP facade for end-users |
| `<ecr>/mimir:<tag>` | AWS ECR (private) | Web app deployed to EB |

Tag format: `{branch-slug}-{short-sha}` (e.g. `v0.0.41-abc1234`).
On release from `main`, images are also tagged `:latest`.

### Release Process

```bash
# Commit everything to main, then:
gh release create vX.Y.Z --title "..." --notes "..."

# CI runs: test → build → deploy to idle env → staging smoke
# Review: http://<idle-cname>.elasticbeanstalk.com/health/

# Promote to prod:
make swap
# → scripts/promote-prod.sh: resolves live/idle, SHA check, CNAME swap, prod smoke
```

### Elastic Beanstalk Deployment

- **Application**: `mimir`
- **Two physical environments**: `mimir-prod` and `mimir-idle` — names are fixed; **CNAME labels rotate on every swap**
- **Region**: `us-east-1`
- **Deploy target**: whichever env is currently **idle**, resolved dynamically by `scripts/deploy-idle.sh` (checks which env holds `mimir-prod.eba-…` CNAME — that's live; the other is idle)
- **Deploy mechanism**: docker-compose bundle uploaded to S3, applied via `update-environment`
- **Version label format**: `v-{branch}-{sha}-r{run_number}`
- **Staging smoke**: `deploy-idle.sh` hits the idle env's own CNAME at `/health/` and verifies `revision` matches `GIT_REVISION` before declaring success

The deploy job generates `docker-compose.yml` from `deploy/docker-compose.tmpl.yml` by
substituting `$IMAGE_WEB` (ECR) with the exact SHA-tagged image built in the preceding job.
The MCP facade (`featurefactory/mimir-mcp`) is a client-side component distributed via Docker Hub;
it is **not** deployed to EB.

### Blue/Green Promotion Workflow

```
gh release create vX.Y.Z
  → CI: test → build → deploy-idle.sh
      • resolves idle env (whichever doesn't hold mimir-prod CNAME)
      • deploys version, waits for Ready
      • smoke tests idle CNAME /health/ — verifies revision
  → human reviews idle URL
  → make swap
      • promote-prod.sh resolves live/idle by CNAME inspection
      • reads GIT_REVISION from idle /health/ (for prod smoke comparison)
      • aws elasticbeanstalk swap-environment-cnames
      • waits 90s for DNS TTL (Route53 TTL = 60s)
      • polls https://mimir.featurefactory.io/health/ until revision matches
  → new version is live; formerly-live env becomes idle for next release
```

**DNS**: `mimir.featurefactory.io` is a Route53 **CNAME** record (TTL 60s) pointing at
`mimir-prod.eba-8hqkems3.us-east-1.elasticbeanstalk.com` (the `mimir-prod` EB CNAME label).
HTTPS is terminated at the ALB inside the EB environment, which holds the
`*.featurefactory.io` wildcard cert (`arn:aws:acm:us-east-1:411113550285:certificate/9d3ca541-…`).
The record is managed by the `MimirDns` CDK stack (idempotent Lambda UPSERT).

**Why CNAME → EB environment CNAME label (not ALB ARN):**
`swap-environment-cnames` atomically rotates which physical env holds the `mimir-prod.eba-…` label.
Route53 resolves `mimir-prod.eba-…` → whichever env currently owns that label → live traffic
follows the swap automatically. No Route53 or CDK update needed on every promotion.

**After a swap** the env names appear "inverted" in `eb-status` — e.g. physical env `mimir-idle`
now holds `mimir-prod.eba-…` (serving traffic). This is correct and expected; `deploy-idle.sh`
always resolves the truly idle env by CNAME inspection, not by name.

**Makefile targets:**

| Target | What it does |
|--------|-------------|
| `make swap` | Runs `scripts/promote-prod.sh`: resolves live/idle, reads revision from idle `/health/`, swaps CNAMEs, waits 90s for DNS TTL, polls prod for revision match |
| `make eb-status` | Shows health, CNAME, and version label for both environments |

**GitHub workflow for promote (alternative to `make swap`):**
```bash
gh workflow run promote.yml -f expected_revision=vX.Y.Z
```
`.github/workflows/promote.yml` is a `workflow_dispatch`-only workflow that runs `promote-prod.sh`
in CI — GitHub equivalent of GitLab's `when: manual` promote stage.

### Known Operational Notes

| Issue | Root Cause | Fix applied |
|-------|-----------|-------------|
| ELB health checks returning 400 (Red for 8+ days) | Django `ALLOWED_HOSTS` did not include the EC2 instance's private IP; ELB target-group health checker uses `Host: <instance-ip>` | `prod.py` now fetches the private IP from IMDSv2 at startup and appends it to `ALLOWED_HOSTS` |
| `UpdateEnvironment: Must be Ready` on release runs | Push-triggered run and release-event run both reaching the deploy step at the same time | Removed all push triggers — pipeline runs only on `release: [published]` and `workflow_dispatch` |
| ALB-alias Route53 broke CNAME swap | Route53 pointed at ALB ARN directly; EB CNAME swap had no effect on live traffic | Replaced A-alias with CNAME to `mimir-prod.eba-…`; CDK-managed via `MimirDns` stack |
| CI hardcoded `mimir-idle` as deploy target | After a swap, `mimir-idle` holds the live CNAME — deploying to it by name would overwrite prod | `deploy-idle.sh` dynamically resolves the idle env by CNAME inspection before every deploy |
| `make swap` smoke test false-negative | 20s wait < 60s Route53 TTL — smoke hit a cached DNS resolver returning old env | `promote-prod.sh` now waits 90s before polling, then retries for up to 3 minutes |

## Email Architecture

### Overview

Mimir sends transactional emails on two paths:

| Path | Trigger | Template | Service |
|------|---------|----------|---------|
| PIP decision notification | Admin finalises a PIP (all accept / partial / reject) | `templates/pips/email_decision.txt` | `methodology/services/pip_notification_service.py` → `send_decision_email()` |
| Email verification | Registration; email address change on profile edit | `templates/accounts/email_verify.txt` + `.html` | `accounts/services/email_service.py` → `send_verification_email()` |
| Password reset | User clicks [Forgot password?] | Inline in `accounts/services/email_service.py` | `accounts/services/email_service.py` → `send_password_reset_email()` |

All paths need SES credentials at runtime. **Note:** `accounts/services/email_service.py` currently calls boto3 directly; it will be migrated to use Django's `EMAIL_BACKEND` (see Email Backend Strategy below) so that dev uses the console backend and tests use `locmem` without any AWS config.

### Email Backend Strategy

Django's `EMAIL_BACKEND` setting governs all `send_mail` / `send_mass_mail` calls (the PIP notification path and Django's own contrib.auth flows).

| Environment | Backend | Config |
|-------------|---------|--------|
| **test** | `django.core.mail.backends.locmem.EmailBackend` | No network; captured in `django.core.mail.outbox` |
| **dev** (default) | `django.core.mail.backends.console.EmailBackend` | Prints to stdout |
| **dev** with `USE_SES_IN_DEV=1` | `django_ses.SESBackend` | Live SES delivery for local smoke testing |
| **prod** | `django_ses.SESBackend` | AWS SES via `django-ses` + boto3 |

The `accounts/services/email_service.py` auth email path calls boto3 directly (pre-dates django-ses adoption) and is independent of `EMAIL_BACKEND`. It will be migrated to use `EMAIL_BACKEND` in a future cleanup ticket.

### AWS SES Setup Requirements

**Domain / address verification** (one-time, via AWS Console or CloudFormation):
1. Verify sending domain `featurefactory.io` in SES (DNS TXT + DKIM).
2. Move SES account out of sandbox: request production access (AWS Support ticket).
3. Create IAM user / role with `ses:SendEmail` on resource `arn:aws:ses:<region>:<account>:identity/<domain>`.

**Required environment variables for production:**

| Variable | Example | Notes |
|----------|---------|-------|
| `AWS_SES_REGION_NAME` | `us-east-1` | Must match verified identity region |
| `DEFAULT_FROM_EMAIL` | `noreply@featurefactory.io` | Must be SES-verified sender |
| `AWS_ACCESS_KEY_ID` | `AKIAxxxxxxxx` | Or use EB instance role (preferred) |
| `AWS_SECRET_ACCESS_KEY` | `…` | Pair for the above |
| `AWS_SES_CONFIGURATION_SET` | `mimir-transactional` | Optional; enables CloudWatch metrics |

**Elastic Beanstalk deployment:** Attach an IAM instance profile with `ses:SendEmail`; omit the key/secret env vars (boto3 picks up the instance role automatically).

### Bug reports — GitHub Issues

The web app can file structured issues from the global **Feedback** UI and from **`POST /api/feedback/report/`** (used by the MCP HTTP facade’s `report_bug` tool). Implementation: `methodology/services/bug_report_service.py` (PyGithub).

**Required for live issue creation (typical production):**

| Variable | Example | Notes |
|----------|---------|-------|
| `GITHUB_TOKEN` | `github_pat_…` or `ghp_…` | Classic PAT or fine-grained token with **Issues: write** on the repository below. Store as an EB environment property (plain or SSM-backed); **never** commit. |
| `GITHUB_BUG_REPO` | `phainestai/mimir` | Default if unset |

**Optional:**

| Variable | Notes |
|----------|--------|
| `BUG_REPORT_DRY_RUN` | `1` / `true` — skip GitHub API (staging diagnostics only). |

The **MCP facade** container talks to FOB over HTTP; it does **not** need `GITHUB_TOKEN`. Only the **web** service reads it.

### PIP Decision Email Content

The email body is rendered from `templates/pips/email_decision.txt` (plain text). It includes:
- PIP title and overall verdict (Accepted / Partially Accepted / Rejected)
- Per-change decision line: change type, entity, admin decision, Galdr reasoning
- New playbook version number (when applicable)

### Testing Strategy

| Layer | Approach |
|-------|----------|
| **Unit / integration** (CI) | `locmem` backend; assert on `django.core.mail.outbox` — subject, recipient, body keywords |
| **Live send smoke test** | Requires `USE_SES_IN_DEV=1` + real AWS creds + SES-verified `TEST_EMAIL_RECIPIENT` env var; skipped automatically when env var absent |
| **SES receipt / receive** | Not implemented — SES inbound requires MX record change; out of scope for MVP. Delivery confirmed by non-bounce of outbound message IDs. |

Integration tests for PIP decision email live in `tests/integration/test_pip_email.py`.

## MCP Integration: Implementation Patterns

### Critical Discovery: stdio Pollution Prevention

**Problem**: MCP servers communicate via JSON-RPC over stdio (stdin/stdout). Any logging, print statements, or warnings to stdout/stderr will corrupt the JSON protocol and cause Windsurf/Claude Desktop to timeout with "context deadline exceeded" errors.

**Solution**: Environment-aware logging configuration

```python
# mimir/settings.py
import os

# Detect MCP mode
_IS_MCP_SERVER = os.environ.get('MIMIR_MCP_MODE') == '1'

# Conditional handler list
_LOG_HANDLERS = ['file'] if _IS_MCP_SERVER else ['file', 'console']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'app.log',
            'mode': 'w',  # Overwrite on each restart
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': _LOG_HANDLERS,  # Conditional: file only in MCP mode
        'level': 'INFO',
    },
}
```

**MCP Server Startup** (extra defense):
```python
# mcp_integration/management/commands/mcp_server.py
def handle(self, *args, **options):
    # CRITICAL: Remove ALL console handlers IMMEDIATELY
    # Must be FIRST thing we do, before any logging
    import logging as logging_module
    import sys
    
    root_logger = logging_module.getLogger()
    console_handlers = [h for h in root_logger.handlers 
                       if isinstance(h, logging_module.StreamHandler) 
                       and not isinstance(h, logging_module.FileHandler)]
    for handler in console_handlers:
        root_logger.removeHandler(handler)
    
    # Flush any buffered output
    sys.stdout.flush()
    sys.stderr.flush()
    
    # NOW safe to proceed with MCP server
    # ...
```

**Windsurf Configuration**:
```json
{
  "mcpServers": {
    "mimir": {
      "command": "absolute/path/to/venv/bin/python",
      "args": ["absolute/path/to/manage.py", "mcp_server", "--user=admin"],
      "env": {
        "MIMIR_MCP_MODE": "1",  // Disables console logging
        "DJANGO_SETTINGS_MODULE": "mimir.settings",
        "PYTHONPATH": "absolute/path/to/project"
      }
    }
  }
}
```

**Key Lessons**:
1. **Never log to console** in MCP mode - use `app.log` exclusively
2. **Remove handlers early** - before Django initialization completes
3. **Flush stdio** - clear any buffered output before starting MCP
4. **Test manually** - `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python manage.py mcp_server --user=admin` should return clean JSON

---

### Critical Discovery: Django ORM in Async MCP Tools

**Problem**: FastMCP tools are async (`async def`), but Django ORM is synchronous. Direct ORM calls from async functions raise `SynchronousOnlyOperation` errors.

**Solution**: Use Django's `sync_to_async` wrapper

**Pattern 1: Simple Query**
```python
from asgiref.sync import sync_to_async
from methodology.models import Playbook

@tool()
async def get_playbook(playbook_id: int) -> dict:
    """Get playbook details."""
    # Wrap ORM call with sync_to_async
    playbook = await sync_to_async(Playbook.objects.get)(id=playbook_id)
    
    return {
        'id': playbook.id,
        'name': playbook.name,
        'version': str(playbook.version),
    }
```

**Pattern 2: Query with select_related (ForeignKey)**
```python
@tool()
async def get_playbook_with_author(playbook_id: int) -> dict:
    """Get playbook with author details."""
    # Use select_related to avoid lazy-loading in async context
    playbook = await sync_to_async(
        Playbook.objects.select_related('author').get
    )(id=playbook_id)
    
    return {
        'id': playbook.id,
        'name': playbook.name,
        'author': playbook.author.username,  # Already loaded, no DB hit
    }
```

**Pattern 3: Filter Queries**
```python
@tool()
async def list_playbooks(status: str = 'all') -> list[dict]:
    """List playbooks filtered by status."""
    # Wrap QuerySet evaluation
    def _get_playbooks():
        qs = Playbook.objects.all()
        if status != 'all':
            qs = qs.filter(status=status)
        return list(qs.values('id', 'name', 'status', 'version'))
    
    playbooks = await sync_to_async(_get_playbooks)()
    return playbooks
```

**Pattern 4: Existence Checks**
```python
@tool()
async def delete_playbook(playbook_id: int) -> dict:
    """Delete a playbook."""
    # Wrap exists() check
    exists = await sync_to_async(
        Playbook.objects.filter(id=playbook_id).exists
    )()
    
    if not exists:
        raise ValueError(f"Playbook {playbook_id} not found")
    
    # Wrap delete operation
    await sync_to_async(Playbook.objects.filter(id=playbook_id).delete)()
    return {'status': 'deleted', 'id': playbook_id}
```

**Testing Async MCP Tools**:
```python
import pytest
from asgiref.sync import sync_to_async

@pytest.mark.asyncio  # Mark test as async
@pytest.mark.django_db(transaction=True)  # Enable transaction mode for async
async def test_create_playbook():
    """Test async MCP tool with Django ORM."""
    from mcp_integration.tools import create_playbook
    
    # Call async MCP tool
    result = await create_playbook(
        name="Test Playbook",
        description="Test description",
        category="test"
    )
    
    # Verify in database (wrap ORM call)
    playbook = await sync_to_async(Playbook.objects.get)(id=result['id'])
    assert playbook.name == "Test Playbook"
```

**Key Lessons**:
1. **Always use sync_to_async** for ORM calls in async MCP tools
2. **Use select_related/prefetch_related** to avoid N+1 queries in async context
3. **Wrap entire queries** - don't try to await QuerySet methods directly
4. **Transaction mode in tests** - `@pytest.mark.django_db(transaction=True)` required for async DB access
5. **Test with pytest-asyncio** - mark tests with `@pytest.mark.asyncio`

**Dependencies Required**:
```txt
# requirements.txt
fastmcp>=0.1.0
django>=5.0
pytest-asyncio>=0.21.0  # For async test support
pytest-django>=4.5.0    # For Django integration
```

---

### Architecture Decision: Service Layer + MCP Tools

**Pattern**: Service layer handles sync business logic, MCP tools wrap it with async/await

```python
# methodology/services/playbook_service.py (SYNC)
class PlaybookService:
    @staticmethod
    def create_playbook(name: str, description: str, category: str, author):
        """Synchronous business logic."""
        if Playbook.objects.filter(name=name, author=author).exists():
            raise ValidationError(f"Playbook '{name}' already exists")
        
        playbook = Playbook.objects.create(
            name=name,
            description=description,
            category=category,
            author=author,
            version=Decimal('0.1'),
            status='draft'
        )
        return playbook

# mcp_integration/tools.py (ASYNC wrapper)
from asgiref.sync import sync_to_async
from methodology.services.playbook_service import PlaybookService

@tool()
async def create_playbook(name: str, description: str, category: str) -> dict:
    """MCP tool for creating playbooks."""
    user = get_current_user()  # From thread-local context
    
    # Wrap service call with sync_to_async
    playbook = await sync_to_async(PlaybookService.create_playbook)(
        name=name,
        description=description,
        category=category,
        author=user
    )
    
    return {
        'id': playbook.id,
        'name': playbook.name,
        'version': str(playbook.version),
        'status': playbook.status,
    }
```

**Benefits**:
- ✅ Service logic is reusable (web UI uses it directly, sync)
- ✅ MCP tools are thin async wrappers
- ✅ Business logic tested once, works in both contexts
- ✅ Type safety maintained throughout

## Security & Access Control

### HOMEBASE

**Authentication**: OAuth2 / API Keys

**Authorization Levels**:
- **Free**: Access to LITE versions of public methodologies
- **Basic**: Access to LITE versions of specific families
- **Standard**: Access to FULL versions
- **Premium**: Access to EXTENDED versions + custom methodologies

**Family-Based Access**:
- User granted access to families (e.g., "Software Engineering", "UX Design")
- Can download any methodology within granted families at their access level

### FOB

**Authentication**: Session-based (Django contrib.auth) for the web UI; DRF `TokenAuthentication` for REST API and MCP clients.

**Registration flow**:
1. User fills registration form (username, first/last name, email, password, ToS checkbox) → `accepted_tos_at` recorded
2. Verification email sent to provided address (SES in prod, console in dev, locmem in test)
3. User cannot log in until email is verified via one-click link (`/auth/user/verify-email/<token>/`, 24h expiry)
4. After first verified login → onboarding screen

**Email change flow**:
- On profile edit, changing email triggers: session termination + API token invalidation + new verification email
- User is locked out until the new address is verified
- Staff/superuser accounts bypass the verification lock entirely

**Authorization**:
- All web views require `@login_required`; unauthenticated requests redirect to `/auth/user/login/`
- Login view additionally checks `UserEmailVerification.is_verified`; unverified users are shown an error with a re-send link
- Staff/superuser: full access including Django Admin; bypass email-verification gate
- Regular users: access scoped to their own playbooks and PIPs (group-based visibility planned)

**PIP Transmission**: Uses DRF API token to transmit PIPs to HOMEBASE (future)

**API Token**: DRF `Token` — shown on the profile page; rotated via password-confirmed POST; invalidated on email change

## Activity Access Tracking

### Overview

The FOB dashboard "Recently Used" section shows activities (workflow tasks) that have been recently **accessed** (viewed via MCP) or **modified** (via GUI/MCP). This allows users to quickly return to activities they're actively working on.

### Implementation

**Activity Model Fields**:
```python
class Activity(models.Model):
    # ... existing fields ...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when activity was last accessed/viewed"
    )
```

**Display Properties**:
- `playbook`: Returns `workflow.playbook` for template display
- `timestamp`: Returns `MAX(last_accessed_at, updated_at)` for sorting
- `description`: Human-readable string with workflow context
- `get_icon_class()`: Font Awesome icon for activity feed

**Service Layer**:
```python
class ActivityService:
    @staticmethod
    def touch_activity_access(activity_id):
        """Update last_accessed_at when activity is viewed."""
        activity = Activity.objects.get(pk=activity_id)
        activity.last_accessed_at = timezone.now()
        activity.save(update_fields=['last_accessed_at'])
    
    @staticmethod
    def get_recent_activities(user, limit=10):
        """Get activities sorted by MAX(last_accessed_at, updated_at)."""
        return Activity.objects.filter(
            workflow__playbook__author=user
        ).annotate(
            recent_time=Greatest(
                Coalesce('last_accessed_at', 'updated_at'),
                'updated_at'
            )
        ).order_by('-recent_time')[:limit]
```

**MCP Integration**:
The `get_activity` MCP tool calls `touch_activity_access()` after fetching activity data:
```python
async def get_activity(activity_id: int) -> dict:
    activity = await fetch_activity(activity_id)
    
    # Track access (non-critical - don't fail main operation)
    try:
        await sync_to_async(ActivityService.touch_activity_access)(activity_id)
    except Exception as e:
        logger.warning(f'Failed to track access: {e}')
        # Continue - access tracking is non-critical
    
    return activity_dict
```

### Exception Handling Strategy

**Critical Operations** (must fail fast):
- Fetching activity data
- Updating activity content
- Validating activity dependencies

**Non-Critical Operations** (log and continue):
- Access tracking (`touch_activity_access`)
- Analytics/metrics collection
- UI enhancements

**Rationale**: Access tracking is a UX enhancement for the dashboard. If it fails, the main operation (viewing the activity) should still succeed. This prevents access tracking issues from breaking the core MCP functionality.

### Testing

Unit tests verify:
- Display properties return correct values
- `touch_activity_access` updates timestamp
- `get_recent_activities` sorts by MAX(last_accessed_at, updated_at)
- Exceptions are raised for invalid activity IDs
- MCP tool continues on access tracking failure

## E2E Testing with Playwright

### Architecture

Mimir uses **Playwright with sync API** for end-to-end testing, avoiding async context issues with Django ORM.

**Key Design Decision**: Disable pytest-playwright plugin and use Playwright's sync API directly to prevent `SynchronousOnlyOperation` errors in Django tests.

### Configuration

**pytest.ini**:
```ini
asyncio_mode = auto                    # Only explicit async tests
addopts = -p no:playwright            # Disable pytest-playwright plugin
```

**Test Structure**:
```
tests/
├── unit/              # Django ORM tests (sync)
├── integration/       # Django + MCP tests (sync/async)
└── e2e/              # Playwright tests (sync API)
    ├── conftest.py   # Manual Playwright fixtures
    └── test_*.py     # Browser-based tests
```

### E2E Fixtures

```python
# tests/e2e/conftest.py
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="module")
def playwright():
    """Use sync API - NOT async."""
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="module")
def browser(playwright):
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(context):
    """New page per test."""
    page = context.new_page()
    yield page
    page.close()
```

### E2E Test Example

```python
@pytest.mark.e2e
@pytest.mark.django_db(transaction=True)
class TestLoginE2E:
    def test_login_success(self, page, live_server_url):
        """No async def - standard sync function."""
        page.goto(f"{live_server_url}/auth/user/login/")
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        page.wait_for_load_state('networkidle')
        assert '/auth/user/login/' not in page.url
```

### Why This Works

| Component | Configuration | Effect |
|-----------|--------------|--------|
| `asyncio_mode = auto` | Only explicit async | Non-async tests stay sync |
| `-p no:playwright` | Disable plugin | No auto-async conversion |
| `sync_playwright()` | Use sync API | E2E tests run in sync mode |
| Manual fixtures | Full control | Proper scope and cleanup |

**Benefits**:
- ✅ Django ORM works in all tests (no async context issues)
- ✅ Full browser automation with Playwright
- ✅ Real Django server via `live_server` fixture
- ✅ 268+ tests passing (unit + integration + E2E)

**Known Limitation**: Minor teardown errors from pytest-django's `live_server` fixture - these are harmless and don't affect test results.

## Request ID Logging

### Overview

Every HTTP request gets a unique request ID tracked throughout the entire request lifecycle for debugging and tracing.

### Architecture

```
┌─────────────────────────────────────────┐
│   RequestIDMiddleware                   │
│   • Generates UUID per request          │
│   • Accepts X-Request-ID header         │
│   • Returns ID in response headers      │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│   Thread-Local Storage                  │
│   • Stores current request              │
│   • Accessible from anywhere            │
└─────────────────────────────────────────┘
            ↓
┌─────────────────────────────────────────┐
│   RequestIDFilter (Logging)             │
│   • Adds [REQ:uuid] to all logs         │
│   • Shows [REQ:NO_REQUEST] outside HTTP │
└─────────────────────────────────────────┘
```

### Log Format

**File logs (verbose)**:
```
[2025-11-28 10:30:45] [INFO] [REQ:a1b2c3d4-5678-90ef-ghij-klmnopqrstuv] [PID:12345:TID:67890] User maria attempting login
```

**Console logs (simple)**:
```
[REQ:a1b2c3d4-5678-90ef-ghij-klmnopqrstuv] INFO User maria logged in successfully
```

### Usage

**In Views**:
```python
def my_view(request):
    request_id = request.request_id  # Access directly
    logger.info(f"Processing for user {request.user.username}")
    # Log automatically includes request ID
```

**Client-Side Tracking**:
```bash
curl -I http://localhost:8000/dashboard/
# Response includes:
# X-Request-ID: a1b2c3d4-5678-90ef-ghij-klmnopqrstuv
```

**Propagating from Upstream**:
```bash
curl -H "X-Request-ID: my-custom-id" http://localhost:8000/api/
# Response echoes back: X-Request-ID: my-custom-id
```

**Searching Logs**:
```bash
# Trace specific request
grep "REQ:a1b2c3d4-5678-90ef-ghij-klmnopqrstuv" logs/app.log

# See request journey
grep "REQ:a1b2c3d4" logs/app.log | grep -E "(REQUEST_START|REQUEST_END|REQUEST_ERROR)"
```

### Benefits

1. **Easy Debugging**: Follow single request through multiple log statements
2. **Error Tracking**: Users can provide request ID from browser dev tools
3. **Performance Analysis**: Track how long specific requests take
4. **Distributed Tracing**: Compatible with upstream tracing systems
5. **User Support**: Request ID helps reproduce and diagnose issues

### Performance Impact

Minimal overhead:
- UUID generation: ~1-2μs per request
- Thread-local storage: ~0.1μs per log statement
- Header addition: ~0.1μs per request
- **Total: < 5μs per request (negligible)**

## Future Considerations

### Multi-FOB Collaboration
- Multiple engineers working on same methodology
- Conflict resolution for concurrent PIPs
- Shared version branches

### Marketplace
- Community-contributed methodologies
- Methodology ratings and reviews
- PIP effectiveness tracking across users

### Analytics
- Aggregate fitness metrics across projects
- Identify high-impact PIPs
- Methodology effectiveness benchmarking

### Advanced AI
- Proactive suggestion before failures occur
- Automated A/B testing of methodology variants
- Transfer learning across methodology families
### GlobalSearchService

**Purpose**: Provides unified search across Playbooks, Workflows, and Activities for NAV-06 Global Search feature.

**Pattern**: Service-layer search with user-scoped filtering and type-based result aggregation.

**Implementation**:

```python
# methodology/services/global_search_service.py
class GlobalSearchService:
    def search(self, query: str, user, filters: Optional[Dict[str, Any]] = None) -> Dict[str, List[Any]]:
        """
        Search across playbooks, workflows, and activities.
        
        :param query: Free-text query. Example: "Component"
        :param user: Django user performing search. Example: User(username="maria")
        :param filters: Optional filters dict. Example: {"type": "playbooks", "status": "active"}
        :return: Dict with entity lists. Example: {"playbooks": [...], "workflows": [...], "activities": [...]}
        """
        # Search playbooks owned by user
        playbooks = self._search_playbooks(query, user, filters)
        # Search workflows in user's playbooks
        workflows = self._search_workflows(query, user, filters)
        # Search activities in user's workflows
        activities = self._search_activities(query, user, filters)
        
        # Apply type filter at aggregation layer
        if filters.get("type") == "playbooks":
            workflows, activities = [], []
        elif filters.get("type") == "workflows":
            playbooks, activities = [], []
        elif filters.get("type") == "activities":
            playbooks, workflows = [], []
            
        return {
            "playbooks": playbooks,
            "workflows": workflows,
            "activities": activities
        }
```

**Features**:
- **User-scoped search**: Only searches entities owned by/accessible to the user
- **Multi-entity search**: Searches across Playbooks, Workflows, and Activities in single call
- **Filter support**: Type filter (playbooks/workflows/activities), status filter (draft/active/released), source filter (owned/downloaded)
- **Case-insensitive matching**: Uses Django's `icontains` for name/description/guidance fields
- **Ordered results**: Playbooks by updated_at DESC, Workflows/Activities by order ASC

**Usage in Views**:
```python
# methodology/views.py
from methodology.services.global_search_service import GlobalSearchService

@login_required
def global_search(request):
    service = GlobalSearchService()
    results = service.search(
        query=request.GET.get("q", "").strip(),
        user=request.user,
        filters={
            "type": request.GET.get("type"),
            "status": request.GET.get("status"),
            "source": request.GET.get("source")
        }
    )
    return render(request, "search/results.html", {
        "playbooks": results["playbooks"],
        "workflows": results["workflows"],
        "activities": results["activities"]
    })
```

**Testing**:
- Unit tests: `tests/unit/test_global_search_service.py` (3 scenarios)
- Integration tests: `tests/integration/test_global_search.py` (7 scenarios)
- Feature coverage: NAV-06 Global Search from `docs/features/act-0-auth/navigation.feature`

---

## REST API Specification (AWS Deployment)

### Overview

For AWS Elastic Beanstalk deployment at `mimir.featurefactory.io`, Mimir exposes a Django REST Framework (DRF) API that provides HTTP access to all MCP tool functionality. This enables:

1. **MCP Facade Container**: Lightweight MCP server that proxies stdio requests to HTTP API
2. **External Integrations**: Third-party tools can integrate via standard REST API
3. **Multi-user Access**: Token-based authentication with group-based visibility

**Architecture**:
```
AI Assistant (Claude Desktop, Cursor, Windsurf)
    ↓ stdio (MCP protocol)
MCP Facade Container (localhost)
    ↓ HTTPS + Token Auth
Django REST API (mimir.featurefactory.io)
    ↓
Business Logic (Services Layer)
    ↓
PostgreSQL RDS (huginn-db)
```

### API Design Principles

1. **1:1 MCP Tool Parity**: Every MCP tool has exactly one corresponding API endpoint
2. **RESTful Resource Mapping**: 8 primary resources (Playbooks, Workflows, Activities, Skills, Agents, Artifacts, Phases, Rules)
3. **Token Authentication**: DRF `TokenAuthentication` for all endpoints (except `/health/`)
4. **Group-Based Visibility**: Users only see playbooks owned by them or shared via group membership
5. **JSON Request/Response**: All payloads use `application/json`
6. **Consistent Error Format**: `{"error": "message", "code": "ERROR_CODE"}`

### Authentication

**Token Acquisition**:
```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response 200:
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 42,
  "username": "user@example.com"
}
```

**Using Token**:
```http
GET /api/playbooks/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
```

### Resource Endpoints

#### 1. Playbooks (`/api/playbooks/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_playbook` | POST | `/api/playbooks/` | Create new draft playbook (v0.1) |
| `list_playbooks` | GET | `/api/playbooks/` | List playbooks (filter by status) |
| `get_playbook` | GET | `/api/playbooks/{id}/` | Get playbook details with workflows |
| `update_playbook` | PATCH | `/api/playbooks/{id}/` | Update draft playbook (increments version) |
| `delete_playbook` | DELETE | `/api/playbooks/{id}/` | Delete draft playbook |

**Example: Create Playbook**
```http
POST /api/playbooks/
Authorization: Token {token}
Content-Type: application/json

{
  "name": "React Component Development",
  "description": "Best practices for building React components",
  "category": "frontend"
}

Response 201:
{
  "id": 1,
  "name": "React Component Development",
  "description": "Best practices for building React components",
  "category": "frontend",
  "status": "draft",
  "version": "0.1",
  "author_id": 42,
  "created_at": "2026-05-07T18:00:00Z",
  "updated_at": "2026-05-07T18:00:00Z"
}
```

**Example: List Playbooks**
```http
GET /api/playbooks/?status=draft
Authorization: Token {token}

Response 200:
[
  {
    "id": 1,
    "name": "React Component Development",
    "status": "draft",
    "version": "0.1",
    "category": "frontend",
    "workflow_count": 3
  },
  {
    "id": 2,
    "name": "API Design Patterns",
    "status": "draft",
    "version": "0.3",
    "category": "backend",
    "workflow_count": 5
  }
]
```

#### 2. Workflows (`/api/workflows/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_workflow` | POST | `/api/workflows/` | Create workflow in draft playbook |
| `list_workflows` | GET | `/api/workflows/?playbook_id={id}` | List workflows for playbook |
| `get_workflow` | GET | `/api/workflows/{id}/` | Get workflow details with activities |
| `update_workflow` | PATCH | `/api/workflows/{id}/` | Update workflow (increments parent version) |
| `delete_workflow` | DELETE | `/api/workflows/{id}/` | Delete workflow from draft playbook |

**Example: Create Workflow**
```http
POST /api/workflows/
Authorization: Token {token}
Content-Type: application/json

{
  "playbook_id": 1,
  "name": "Component Development",
  "description": "Steps to build reusable components"
}

Response 201:
{
  "id": 1,
  "playbook_id": 1,
  "name": "Component Development",
  "description": "Steps to build reusable components",
  "order": 1,
  "activity_count": 0
}
```

#### 3. Activities (`/api/activities/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_activity` | POST | `/api/activities/` | Create activity in workflow |
| `list_activities` | GET | `/api/activities/?workflow_id={id}` | List activities for workflow |
| `get_activity` | GET | `/api/activities/{id}/` | Get activity details with dependencies |
| `update_activity` | PATCH | `/api/activities/{id}/` | Update activity (increments grandparent version) |
| `delete_activity` | DELETE | `/api/activities/{id}/` | Delete activity from draft playbook |
| `set_predecessor` | PUT | `/api/activities/{id}/predecessor/` | Set predecessor dependency |

**Example: Create Activity**
```http
POST /api/activities/
Authorization: Token {token}
Content-Type: application/json

{
  "workflow_id": 1,
  "name": "Design Component API",
  "guidance": "## API Design\n\nDefine component props and events...",
  "phase_id": 3,
  "order": 1
}

Response 201:
{
  "id": 1,
  "workflow_id": 1,
  "name": "Design Component API",
  "guidance": "## API Design\n\nDefine component props and events...",
  "phase_id": 3,
  "order": 1,
  "predecessor_id": null,
  "agent_id": null,
  "skill_id": null
}
```

**Example: Set Predecessor**
```http
PUT /api/activities/2/predecessor/
Authorization: Token {token}
Content-Type: application/json

{
  "predecessor_id": 1
}

Response 200:
{
  "id": 2,
  "name": "Implement Component",
  "predecessor_id": 1,
  "predecessor_name": "Design Component API"
}
```

#### 4. Skills (`/api/skills/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_skill` | POST | `/api/skills/` | Create skill in draft playbook |
| `list_skills` | GET | `/api/skills/?playbook_id={id}` | List skills for playbook |
| `get_skill` | GET | `/api/skills/{id}/` | Get skill details with activity count |
| `update_skill` | PATCH | `/api/skills/{id}/` | Update skill (increments parent version) |
| `delete_skill` | DELETE | `/api/skills/{id}/` | Delete skill from draft playbook |
| `link_skill_to_activity` | PUT | `/api/activities/{id}/skill/` | Link skill to activity |
| `unlink_skill_from_activity` | DELETE | `/api/activities/{id}/skill/` | Unlink skill from activity |

**Example: Link Skill to Activity**
```http
PUT /api/activities/1/skill/
Authorization: Token {token}
Content-Type: application/json

{
  "skill_id": 5
}

Response 200:
{
  "activity_id": 1,
  "skill_id": 5,
  "skill_title": "Build Login Form"
}
```

#### 5. Agents (`/api/agents/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_agent` | POST | `/api/agents/` | Create agent in draft playbook |
| `list_agents` | GET | `/api/agents/?playbook_id={id}` | List agents for playbook |
| `get_agent` | GET | `/api/agents/{id}/` | Get agent details with activity count |
| `update_agent` | PATCH | `/api/agents/{id}/` | Update agent (increments parent version) |
| `delete_agent` | DELETE | `/api/agents/{id}/` | Delete agent from draft playbook |
| `link_agent_to_activity` | PUT | `/api/activities/{id}/agent/` | Link agent to activity |
| `unlink_agent_from_activity` | DELETE | `/api/activities/{id}/agent/` | Unlink agent from activity |

**Example: Link Agent to Activity**
```http
PUT /api/activities/1/agent/
Authorization: Token {token}
Content-Type: application/json

{
  "agent_id": 3
}

Response 200:
{
  "activity_id": 1,
  "agent_id": 3,
  "agent_name": "Code Reviewer"
}
```

#### 6. Artifacts (`/api/artifacts/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_artifact` | POST | `/api/artifacts/` | Create artifact in draft playbook |
| `list_artifacts` | GET | `/api/artifacts/?playbook_id={id}` | List artifacts for playbook |
| `get_artifact` | GET | `/api/artifacts/{id}/` | Get artifact details with consumer count |
| `update_artifact` | PATCH | `/api/artifacts/{id}/` | Update artifact (increments parent version) |
| `delete_artifact` | DELETE | `/api/artifacts/{id}/` | Delete artifact from draft playbook |
| `link_artifact_to_activity` | POST | `/api/artifacts/{id}/consumers/` | Link artifact as input to activity |
| `unlink_artifact_from_activity` | DELETE | `/api/artifact-inputs/{id}/` | Unlink artifact from activity |

**Example: Link Artifact to Activity**
```http
POST /api/artifacts/1/consumers/
Authorization: Token {token}
Content-Type: application/json

{
  "activity_id": 5,
  "is_required": true
}

Response 201:
{
  "id": 1,
  "artifact_id": 1,
  "activity_id": 5,
  "is_required": true
}
```

#### 7. Phases (`/api/phases/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_phase` | POST | `/api/phases/` | Create phase in draft playbook |
| `list_phases` | GET | `/api/phases/?playbook_id={id}` | List phases for playbook |
| `get_phase` | GET | `/api/phases/{id}/` | Get phase details with activities |
| `update_phase` | PATCH | `/api/phases/{id}/` | Update phase (increments parent version) |
| `delete_phase` | DELETE | `/api/phases/{id}/` | Delete phase from draft playbook |
| `reorder_phases` | PUT | `/api/playbooks/{id}/phases/reorder/` | Reorder phases in playbook |

**Example: Reorder Phases**
```http
PUT /api/playbooks/1/phases/reorder/
Authorization: Token {token}
Content-Type: application/json

{
  "phase_order": [3, 1, 2]
}

Response 200:
{
  "reordered": true,
  "count": 3
}
```

#### 8. Rules (`/api/rules/`)

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `create_rule` | POST | `/api/rules/` | Create rule in draft playbook |
| `list_rules` | GET | `/api/rules/?playbook_id={id}` | List rules for playbook |
| `get_rule` | GET | `/api/rules/{id}/` | Get rule details |
| `update_rule` | PATCH | `/api/rules/{id}/` | Update rule (increments parent version) |
| `delete_rule` | DELETE | `/api/rules/{id}/` | Delete rule from draft playbook |
| `set_activity_rules` | PUT | `/api/activities/{id}/rules/` | Replace activity's linked rules |

**Example: Set Activity Rules**
```http
PUT /api/activities/1/rules/
Authorization: Token {token}
Content-Type: application/json

{
  "rule_ids": [1, 3, 5]
}

Response 200:
{
  "activity_id": 1,
  "rule_ids": [1, 3, 5],
  "count": 3
}
```

### Workflow Import/Export

| MCP Tool | HTTP Method | Endpoint | Description |
|----------|-------------|----------|-------------|
| `export_workflow_to_local` | POST | `/api/workflows/{id}/export/` | Export workflow to markdown files |
| `import_workflow_from_local` | POST | `/api/workflows/{id}/import/` | Import workflow from markdown files |
| `apply_upload_protocol` | POST | `/api/workflows/{id}/apply-protocol/` | Apply upload protocol to draft |
| `create_pip_from_protocol` | POST | `/api/workflows/{id}/create-pip/` | Create PIP from protocol (released) |

### Error Responses

**Standard Error Format**:
```json
{
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

**Common Error Codes**:
- `NOT_FOUND`: Resource does not exist or user lacks access (404)
- `PERMISSION_DENIED`: Cannot modify released playbook (403)
- `VALIDATION_ERROR`: Invalid input data (400)
- `UNAUTHORIZED`: Missing or invalid token (401)
- `CIRCULAR_DEPENDENCY`: Activity dependency creates cycle (400)
- `CROSS_PLAYBOOK`: Cannot link resources across playbooks (400)

**Example Error**:
```http
PATCH /api/playbooks/1/
Authorization: Token {token}
Content-Type: application/json

{
  "name": "Updated Name"
}

Response 403:
{
  "error": "Cannot modify released playbook \"React Dev\". Use create_pip instead.",
  "code": "PERMISSION_DENIED"
}
```

### API Versioning

- **Current Version**: v1 (implicit in `/api/` prefix)
- **Future Versions**: `/api/v2/` when breaking changes needed
- **Deprecation Policy**: 6-month notice before removing endpoints

### Rate Limiting

- **Authenticated Requests**: 1000 requests/hour per token
- **Health Endpoint**: Unlimited (ALB health checks)
- **Response Header**: `X-RateLimit-Remaining: 987`

### CORS Policy

- **Allowed Origins**: `https://mimir.featurefactory.io`, `http://localhost:*` (dev)
- **Allowed Methods**: GET, POST, PUT, PATCH, DELETE, OPTIONS
- **Allowed Headers**: Authorization, Content-Type
- **Credentials**: Allowed

### Implementation Notes

**DRF ViewSets**:
```python
# methodology/api/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from methodology.services.playbook_service import PlaybookService

class PlaybookViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List playbooks (maps to list_playbooks MCP tool)."""
        service = PlaybookService()
        status_filter = request.query_params.get('status', 'all')
        playbooks = service.list_playbooks(request.user, status_filter)
        return Response(playbooks)
    
    def create(self, request):
        """Create playbook (maps to create_playbook MCP tool)."""
        service = PlaybookService()
        playbook = service.create_playbook(
            user=request.user,
            name=request.data['name'],
            description=request.data['description'],
            category=request.data['category']
        )
        return Response(playbook, status=status.HTTP_201_CREATED)
```

**URL Configuration**:
```python
# mimir/urls.py
from rest_framework.routers import DefaultRouter
from methodology.api.viewsets import (
    PlaybookViewSet, WorkflowViewSet, ActivityViewSet,
    SkillViewSet, AgentViewSet, ArtifactViewSet,
    PhaseViewSet, RuleViewSet
)

router = DefaultRouter()
router.register(r'playbooks', PlaybookViewSet, basename='playbook')
router.register(r'workflows', WorkflowViewSet, basename='workflow')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'skills', SkillViewSet, basename='skill')
router.register(r'agents', AgentViewSet, basename='agent')
router.register(r'artifacts', ArtifactViewSet, basename='artifact')
router.register(r'phases', PhaseViewSet, basename='phase')
router.register(r'rules', RuleViewSet, basename='rule')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls')),
]
```

### Testing Strategy

**API Parity Tests**:
```python
# tests/integration/test_api_mcp_parity.py
def test_all_mcp_tools_have_api_endpoints():
    """Verify every MCP tool has corresponding API endpoint."""
    mcp_tools = extract_mcp_tools('mcp_integration/tools.py')
    api_endpoints = extract_api_endpoints('methodology/api/viewsets.py')
    
    for tool in mcp_tools:
        assert tool in api_endpoints, f"MCP tool {tool} missing API endpoint"
```

**Parity Checker Script**:
```bash
# scripts/check_tool_api_parity.py
python scripts/check_tool_api_parity.py
# Output:
# ✓ create_playbook → POST /api/playbooks/
# ✓ list_playbooks → GET /api/playbooks/
# ✓ get_playbook → GET /api/playbooks/{id}/
# ...
# ✓ 53/53 MCP tools have API endpoints
```
