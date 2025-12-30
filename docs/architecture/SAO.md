# Mimir: System Architecture Overview

## Executive Summary

Mimir is a two-part system for managing and evolving software development methodologies through AI-driven continuous improvement. It consists of:

1. **HOMEBASE**: Centralized methodology repository with access control for distribution
2. **FOB (Forward Operating Base)**: Django-based desktop application providing web UI and MCP interface for methodology consumption and evolution

**Key Design Decisions**:
- **FastMCP Integration**: Services map directly to MCP tools via `@tool` decorators - zero protocol boilerplate
- **Repository Pattern**: Storage-agnostic architecture (SQLite for FOB, Neo4j for HOMEBASE)
- **Read-Only MCP**: All changes via Process Improvement Proposals (PIPs) - prevents sync conflicts
- **Shared Services**: Same business logic serves both MCP and Web UI - DRY and type-safe
- **HTMX + Graphviz for FOB**: Server-rendered UI with minimal JS - testable with standard Django tests, no browser automation needed

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────┐
│   HOMEBASE (Methodology Repository)     │
│                                         │
│   ├─ Neo4J (graph database)            │
│   ├─ FastAPI + OpenAPI                 │
│   ├─ React + Vite + Tailwind UI        │
│   ├─ Access control (Family + Level)   │
│   └─ Methodology distribution           │
│       (e.g., SE/Basic → LITE version)   │
└─────────────────────────────────────────┘
              ↓ download/sync
┌─────────────────────────────────────────┐
│   FOB - Forward Operating Base (Django) │
│                                         │
│   Process 1: MCP Server (stdio)         │
│   ├─ python manage.py mcp_server        │
│   ├─ Standard MCP protocol              │
│   ├─ Read-only methodology access       │
│   └─ Creates PIPs (proposals)           │
│                                         │
│   Process 2: Web Server (HTTP)          │
│   ├─ python manage.py runserver 8000    │
│   ├─ Django views for UI                │
│   ├─ PIP review & approval              │
│   └─ Methodology editing/viewing        │
│                                         │
│   Shared Layer:                         │
│   ├─ SQLite database                    │
│   ├─ Repository pattern (abstraction)   │
│   ├─ Services (business logic)          │
│   └─ Models (Node, Edge, Version, PIP)  │
└─────────────────────────────────────────┘
```

## Design Principles

### 1. Two-Part Architecture

**HOMEBASE (Methodology Repository)**
Tried-and-true approaches accumulating most recent howtos and experiences from the boots on the ground.

- Centralized repository of methodologies
- Access control based on:
  - **Family**: Methodology category (e.g., "Software Engineering", "UX Design")
  - **Access Level**: Determines version tier (Basic → LITE, Standard → FULL, Premium → EXTENDED)
- Distribution point for methodology downloads
- Aggregates Process Improvement Proposals (PIPs) from FOBs
- Technology: Neo4j + FastAPI + React

**FOB (Forward Operating Base)**
This is where howtos are consumed, judged practical/impractical, refined, and expanded.

- Single-user desktop application
- Downloads methodologies from HOMEBASE
- Provides two interfaces:
  - **Web UI**: For viewing methodologies, reviewing PIPs, editing local customizations
  - **MCP Interface**: For AI assistants to query methodology and create work plans
- Technology: Django + SQLite + MCP (stdio)

### 2. Hybrid MCP Access: Draft CRUD + Released PIP Workflow

**Problem Solved**: Allows AI to rapidly build new methodologies while protecting stable/released content from unreviewed changes.

**Solution**: MCP provides full CRUD access to DRAFT playbooks (status='draft', version=0.x), but read-only access to RELEASED playbooks (status='released', version≥1.0). Changes to released playbooks require Process Improvement Proposals (PIPs).

**Workflow for DRAFT Playbooks** (AI can modify directly):
```
AI/Engineer via MCP
    ↓ building new methodology
Creates/Updates DRAFT Playbook (v0.x)
    ↓ adds workflows, activities, howtos
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
    :return: Guidance dict with answer and resources. Example: {"answer": "To build a TSX component...", "relevant_activities": ["SE1"], "relevant_howtos": ["howto-tsx"]}
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
- **Branding**: "Your Self-Evolving Engineering Playbook" - emphasizes practical, modular, AI-enhanced approach
- **Terminology**: User-facing language uses "playbook" (accessible, modern) while internal code uses "Methodology" models (technical accuracy)

**Icon Usage**:
- **Playbook/Methodology**: `fa-book-sparkles` - primary identifier across nav, pages, footer
- **Process Improvements**: `fa-lightbulb` - for PIPs (Process Improvement Proposals)
- **Versions**: `fa-code-branch` - for version history and tracking
- **Actions**: All buttons/links include semantic Font Awesome icons per UI guidelines

### Django Implementation Details

**User Model**:
- Extends Django's standard User model (`AbstractUser`)
- Custom fields added via `User` model extension
- Email used as primary identifier for authentication
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
            label = f"{activity.name}\\n({activity.role.name})"
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

**Use Case**: Activity detail, showing all links (predecessors, successors, howtos)

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
        'howtos': activity.howtos.all(),
        'artifacts_produced': activity.artifacts_produced.all(),
        'artifacts_consumed': activity.artifacts_consumed.all(),
        'role': activity.role
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

**Use Case**: Add/edit/delete activities, workflows, howtos

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
│    • Goal 2         │                │- Howtos│
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

The FOB Web UI is comprehensively documented through **46 BDD-style Gherkin feature files** organized by user journey Acts (0-15). These serve as both specifications and test scenarios.

### Feature File Organization

```
docs/features/
├── act-0-auth/              # Authentication, Onboarding, Navigation (3 files)
├── act-2-playbooks/         # Playbooks CRUDLF (5 files)
├── act-3-workflows/         # Workflows CRUDLF (5 files)
├── act-4-phases/            # Phases CRUDLF (5 files) - OPTIONAL entity
├── act-5-activities/        # Activities CRUDLF (5 files)
├── act-6-artifacts/         # Artifacts CRUDLF (5 files)
├── act-7-roles/             # Roles CRUDLF (5 files)
├── act-8-howtos/            # Howtos CRUDLF (5 files)
├── act-9-pips/              # PIPs Create & Manage (2 files)
├── act-10-import-export/    # Import/Export (1 file)
├── act-11-family/           # Family Management (1 file)
├── act-12-sync/             # Sync Scenarios (1 file)
├── act-13-mcp/              # MCP Integration (1 file)
├── act-14-settings/         # Settings & Configuration (1 file)
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

**Total Coverage**: 46 feature files, ~3,200 lines of Gherkin
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
    # 'artifact', 'role', 'howto'
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
    # 'requires_artifact', 'performed_by_role', 'guided_by_howto', 
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

**Implementation**: Mimir uses [FastMCP](https://github.com/jlowin/fastmcp) for MCP server implementation. Services map directly to MCP tools via `@tool` decorators.

**Architecture Benefits**:
- Zero boilerplate - FastMCP handles protocol details
- Type-safe - Python type hints → JSON Schema automatically
- DRY - Services used by both MCP and Web UI
- Testable - Pure business logic, easily mocked

### Tool 1: query_methodology

**Purpose**: Answer questions about how to perform tasks according to methodology.

**Use Cases**:
- "How do I build a TSX component per FDD methodology?"
- "What are the acceptance criteria for a screen mockup?"
- "What howtos are available for unit testing React components?"

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
    :return: Guidance dict with answer and resources. Example: {"answer": "To build a TSX component...", "relevant_activities": ["SE1: Create Component Structure"], "relevant_howtos": ["howto-tsx-component-setup"], "related_artifacts": ["Component Specification", "Unit Tests"]}
    """
    service = MethodologyService(DjangoORMRepository())
    return service.query_guidance(question, methodology, context)
```

**Output Example**:
```python
{
  "answer": "To build a TSX component per FDD...",
  "relevant_activities": ["SE1: Create Component Structure"],
  "relevant_howtos": ["howto-tsx-component-setup"],
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
        :return: Guidance dict with answer and related resources. Example: {"answer": "To test a Django view...", "relevant_activities": ["Write Unit Tests"], "relevant_howtos": ["django-test-setup"], "related_artifacts": ["Test Suite"]}
        """
        # Load methodology
        method = self.repo.get_methodology(methodology)
        
        # Semantic search across activities, howtos
        relevant_items = self._search_methodology(method, question, context)
        
        # Generate answer
        return {
            "answer": self._generate_answer(relevant_items, question),
            "relevant_activities": [a.name for a in relevant_items['activities']],
            "relevant_howtos": [h.name for h in relevant_items['howtos']],
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

## Methodology Ontology

### Core Concepts

**Activity**: The *what* - a unit of work with generic guidance
- Example: "Create screen mockup"
- Properties: name, description, goals, required skills
- Produces: Artifacts
- Consumes: Artifacts (from predecessors)
- Guided by: Howtos

**Howto**: The *how* - specific implementation instructions
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

**Role**: Who performs activities
- Example: "Frontend Engineer", "UX Designer"
- Can be: Human, AI agent, or hybrid

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
4. **Howto effectiveness**: Are the implementation instructions adequate?
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
- Simple web UI for viewing Playbooks, Workflows, Activities, Howtos, Artifacts, Roles

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
- FastAPI endpoints for methodology CRUD
- Access control system (Family + Level)
- Methodology distribution endpoints
- PIP aggregation from FOBs
- React UI for HOMEBASE management

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
- **API**: FastAPI 0.104+
- **Web UI**: React 18 + Vite + Zustand + Tailwind + shadcn/ui
- **Python Version**: 3.11+

### AI Components
- **Default Model**: GPT-4o (configurable)
- **Tyr AI**: Task planning and work order generation
- **Saga AI**: Retrospection and improvement suggestions

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

**No Authentication**: Single-user desktop app

**PIP Transmission**: Uses API key to transmit PIPs to HOMEBASE

**Data Privacy**: All work orders and execution data stay local

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
