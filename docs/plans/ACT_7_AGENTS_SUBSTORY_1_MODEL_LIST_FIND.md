# Sub-Story 1: Agent Model + List/Find

**Parent Epic**: ACT 7 Agents CRUDLF  
**Date**: 2026-03-30  
**Type**: Feature Implementation  
**Complexity**: 3 classes, ~12 methods ✅  
**Status**: Ready for Copilot Implementation

## Overview

Implement the foundational Agent model and global list/search functionality. This is the first sub-story and establishes the data model and basic viewing capabilities.

## Feature Files Covered

`docs/features/act-7-agents/agents-list-find.feature` - **8 scenarios**:
- AGENT-LIST-01: Navigate to agents list from playbook
- AGENT-LIST-02: View agents table
- AGENT-LIST-03: Create new agent (navigation only)
- AGENT-LIST-04: Search agents by name
- AGENT-LIST-05: Filter by activity usage
- AGENT-LIST-06: View agent usage count
- AGENT-LIST-07: Navigate to view agent (navigation only)
- AGENT-LIST-08: Empty state display

## Architecture References

**Model Pattern**: Follow `methodology/models/skill.py` (simpler 1:1 relationship)  
**Service Pattern**: Follow `methodology/services/skill_service.py`  
**View Pattern**: Follow `methodology/skill_views.py` (global list)  
**Template Pattern**: Follow `templates/skills/list.html`

## IA Guidelines Compliance

**Reference**: `docs/ux/IA_guidelines.md`

### Icon System (§1.4, Lines 275-351)
- **Agent Icon**: `fa-brain` (Lines 938, 943) - "Emphasizes expertise and cognitive work"
- **Icon + Text Pattern**: Icon before text with `me-2` spacing (Line 311)
- **Action Icons**: Edit `fa-pen-to-square`, Delete `fa-trash-can`, Add `fa-plus`, Search `fa-magnifying-glass` (Lines 337-342)

### Semantic HTML (§2.6, Lines 1040-1072)
- Use `<main>` for primary content area
- Use `<section>` for thematic grouping
- Include ARIA landmarks: `role="search"` for search form
- All interactive elements keyboard accessible
- Focus indicators visible (Bootstrap default)

### Responsive Behavior (§2.8, Lines 1123-1193)
- **Mobile (xs)**: Stack all columns, full-width cards, touch targets min 44x44px
- **Tablet (md)**: 2-3 column layouts, collapsible sections
- **Desktop (lg+)**: Full feature set, hover states, tooltips
- Use Bootstrap responsive utilities: `.d-none .d-lg-block` for conditional display

### Data-TestID Pattern (§4.4, Line 910)
- All interactive elements: `data-testid="[element-type]-[identifier]"`
- Examples: `data-testid="agent-search"`, `data-testid="agent-row-42"`, `data-testid="view-agent-42"`

## Detailed Implementation Plan

### Phase 1: Model & Migration

#### 1.1 Create Agent Model
**File**: `methodology/models/agent.py`

**Model Structure**:
```python
class Agent(models.Model):
    """AI assistant that performs activities within methodologies."""
    
    # Core fields
    name = models.CharField(max_length=200, help_text="Agent name. Example: 'Cautious Developer (drdobbs-v2)'")
    description = models.TextField(blank=True, help_text="Agent capabilities and guidelines")
    
    # Relationship
    playbook = models.ForeignKey(
        'Playbook',
        on_delete=models.CASCADE,
        related_name='agents',
        help_text="Playbook containing this agent"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['playbook', 'name']
        verbose_name = 'Agent'
        verbose_name_plural = 'Agents'
        constraints = [
            models.UniqueConstraint(
                fields=['playbook', 'name'],
                name='unique_agent_per_playbook',
                violation_error_message="An agent with this name already exists in this playbook"
            )
        ]
        indexes = [
            models.Index(fields=['playbook']),
        ]
```

**Methods to implement** (complete signatures):

```python
def __str__(self) -> str:
    """
    String representation.
    
    :returns: Agent name as str. Example: "Cautious Developer (drdobbs-v2)"
    """
    return self.name

def clean(self):
    """
    Model-level validation.
    
    :raises ValidationError: If name is empty or whitespace-only
    """
    if not self.name or not self.name.strip():
        raise ValidationError({"name": "Agent name cannot be empty"})

def save(self, *args, **kwargs):
    """
    Override save to run validation.
    
    :param args: Positional arguments
    :param kwargs: Keyword arguments
    """
    self.full_clean()
    super().save(*args, **kwargs)

def get_absolute_url(self) -> str:
    """
    Get URL for agent detail page.
    
    :returns: URL path as str. Example: "/agents/123/"
    """
    from django.urls import reverse
    return reverse("agent_detail", kwargs={"pk": self.pk})

def is_owned_by(self, user) -> bool:
    """
    Check if user owns parent playbook.
    
    :param user: User instance to check
    :returns: bool. Example: True if user owns playbook, False otherwise
    """
    return self.playbook.is_owned_by(user)

def can_edit(self, user) -> bool:
    """
    Check if user can edit this agent.
    
    :param user: User instance to check
    :returns: bool. Example: True if user can edit, False otherwise
    """
    return self.is_owned_by(user)

def get_activity_count(self) -> int:
    """
    Get count of activities using this agent.
    
    :returns: int count. Example: 3
    """
    return self.activities.count()

def to_dict(self) -> dict:
    """
    Convert to dictionary for API/MCP responses.
    
    :returns: Dict representation. Example:
        {
            "id": 1,
            "name": "Cautious Developer (drdobbs-v2)",
            "description": "Defensive programming specialist",
            "playbook_id": 5,
            "playbook_name": "React Frontend v1.2",
            "activity_count": 3,
            "created_at": "2026-03-30T18:00:00Z",
            "updated_at": "2026-03-30T18:00:00Z"
        }
    """
    return {
        "id": self.id,
        "name": self.name,
        "description": self.description,
        "playbook_id": self.playbook_id,
        "playbook_name": self.playbook.name,
        "activity_count": self.get_activity_count(),
        "created_at": self.created_at.isoformat(),
        "updated_at": self.updated_at.isoformat(),
    }
```

**Tests to create** (`tests/unit/test_agent_model.py`):
- `test_create_agent_success` - Create agent with valid data
- `test_agent_str_representation` - Verify __str__ returns name
- `test_agent_unique_per_playbook` - Verify uniqueness constraint
- `test_agent_name_required` - Verify validation error on empty name
- `test_agent_is_owned_by` - Verify ownership check
- `test_agent_can_edit` - Verify edit permission check
- `test_agent_to_dict` - Verify dict conversion

#### 1.2 Create Migration
**File**: `methodology/migrations/000X_agent.py`

Run: `python manage.py makemigrations`

**Test migration**:
- `test_migration_creates_agent_table` - Verify table created
- `test_migration_creates_indexes` - Verify indexes created

#### 1.3 Register with Admin
**File**: `methodology/admin.py`

Add:
```python
from methodology.models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'playbook', 'created_at']
    list_filter = ['playbook', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['playbook', 'name']
```

**Manual verification**: Access `/admin/methodology/agent/` and verify CRUD works

**Commit**: `feat(agents): add Agent model with migration and admin registration`

---

### Phase 2: Service Layer

#### 2.1 Create AgentService
**File**: `methodology/services/agent_service.py`

**Methods to implement** (complete signatures):

```python
from django.db.models import QuerySet
from django.core.exceptions import ValidationError
from methodology.models import Agent, Playbook
from django.contrib.auth.models import User

def create_agent(playbook: Playbook, name: str, description: str = '') -> Agent:
    """
    Create agent with validation.
    
    :param playbook: Playbook object (not ID) - the playbook containing this agent
    :param name: Agent name (max 200 chars, required). Example: "Cautious Developer (drdobbs-v2)"
    :param description: Agent description (optional). Example: "Defensive programming specialist"
    :returns: Created Agent instance
    :raises ValidationError: If name is empty, exceeds 200 chars, or duplicate in playbook
    
    Example:
        playbook = Playbook.objects.get(pk=5)
        agent = create_agent(playbook, "Developer", "Writes clean code")
    """
    agent = Agent(playbook=playbook, name=name, description=description)
    agent.full_clean()  # Raises ValidationError if invalid
    agent.save()
    return agent

def get_agent(agent_id: int) -> Agent:
    """
    Get agent by ID with related data preloaded.
    
    :param agent_id: Agent primary key. Example: 123
    :returns: Agent instance with playbook preloaded
    :raises Agent.DoesNotExist: If agent not found
    
    Example:
        agent = get_agent(123)
        print(agent.playbook.name)  # No additional query
    """
    return Agent.objects.select_related('playbook').get(pk=agent_id)

def list_agents_for_playbook(playbook_id: int) -> QuerySet[Agent]:
    """
    List all agents in a playbook.
    
    :param playbook_id: Playbook primary key. Example: 5
    :returns: QuerySet of Agent instances, ordered by name
    
    Example:
        agents = list_agents_for_playbook(5)
        for agent in agents:
            print(agent.name)
    """
    return Agent.objects.filter(playbook_id=playbook_id).select_related('playbook').order_by('name')

def search_agents(query: str = '', user: User = None) -> QuerySet[Agent]:
    """
    Search agents by name or description.
    
    :param query: Search string (searches name and description, case-insensitive). Example: "developer"
    :param user: Filter to agents in user's playbooks (optional). Example: maria
    :returns: QuerySet of Agent instances, ordered by playbook, name
    
    Example:
        # Global search
        agents = search_agents("developer")
        
        # User-scoped search
        agents = search_agents("developer", user=maria)
    """
    from django.db.models import Q
    
    queryset = Agent.objects.select_related('playbook').all()
    
    # Filter by user ownership if provided
    if user:
        queryset = queryset.filter(playbook__owner=user)
    
    # Search by query if provided
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    return queryset.order_by('playbook', 'name')

def update_agent(agent_id: int, **kwargs) -> Agent:
    """
    Update agent fields.
    
    :param agent_id: Agent primary key. Example: 123
    :param kwargs: Fields to update. Valid keys: 'name', 'description'
    :returns: Updated Agent instance
    :raises Agent.DoesNotExist: If agent not found
    :raises ValidationError: If validation fails (empty name, duplicate, etc.)
    
    Example:
        agent = update_agent(123, name="Senior Developer")
        agent = update_agent(123, description="Expert in React")
    """
    agent = get_agent(agent_id)
    
    # Update only allowed fields
    for key in ['name', 'description']:
        if key in kwargs:
            setattr(agent, key, kwargs[key])
    
    agent.full_clean()  # Raises ValidationError if invalid
    agent.save()
    return agent

def delete_agent(agent_id: int) -> None:
    """
    Delete agent.
    
    :param agent_id: Agent primary key. Example: 123
    :raises Agent.DoesNotExist: If agent not found
    
    Note: Related activities will have their agent field set to NULL (on_delete=SET_NULL)
    
    Example:
        delete_agent(123)
    """
    agent = get_agent(agent_id)
    agent.delete()
```

**Tests to create** (`tests/unit/test_agent_service.py`):
- `test_create_agent_success` - Create with valid data
- `test_create_agent_empty_name_fails` - Validation error on empty name
- `test_create_agent_duplicate_name_fails` - Uniqueness validation
- `test_get_agent_success` - Retrieve existing agent
- `test_get_agent_not_found` - DoesNotExist exception
- `test_list_agents_for_playbook` - List all agents in playbook
- `test_search_agents_by_name` - Search functionality
- `test_search_agents_by_description` - Search in description
- `test_search_agents_user_filter` - Filter by user ownership
- `test_update_agent_name` - Update name field
- `test_update_agent_description` - Update description field
- `test_delete_agent_success` - Delete agent

**Commit**: `feat(agents): add AgentService with CRUD operations`

---

### Phase 3: Views & URLs

#### 3.1 Create Global List View
**File**: `methodology/agent_views.py`

**View to implement**:
```python
@login_required
def agent_list_global(request):
    """
    Global agents list across all playbooks owned by user.
    Supports search via ?q= query parameter.
    
    Template: templates/agents/list.html
    Context:
        - agents: QuerySet[Agent] - Filtered/searched agents, ordered by playbook, name
        - query: str - Search query from ?q= parameter (empty string if not provided)
        - count: int - Total agent count for user (before search filter)
    
    Example URLs:
        /agents/ - List all agents
        /agents/?q=developer - Search for "developer"
    """
    from methodology.services.agent_service import search_agents
    
    # Get search query
    query = request.GET.get('q', '').strip()
    
    # Get total count (before search)
    from methodology.models import Agent
    total_count = Agent.objects.filter(playbook__owner=request.user).count()
    
    # Search agents (user-scoped)
    agents = search_agents(query=query, user=request.user)
    
    # Render template
    context = {
        'agents': agents,
        'query': query,
        'count': total_count,
    }
    return render(request, 'agents/list.html', context)
```

**Template Context Contract**:
```python
# templates/agents/list.html expects:
context = {
    'agents': QuerySet[Agent],  # Each agent has: .id, .name, .description, .playbook, .get_absolute_url()
    'query': str,                # Search query (may be empty)
    'count': int,                # Total agent count for user
}

# Each agent object provides:
agent.id                        # int - Primary key
agent.name                      # str - Agent name
agent.description               # str - Agent description (may be empty)
agent.playbook                  # Playbook - Related playbook (preloaded)
agent.playbook.name             # str - Playbook name
agent.playbook.get_absolute_url()  # str - URL to playbook detail
agent.get_absolute_url()        # str - URL to agent detail (/agents/{pk}/)
agent.get_activity_count()      # int - Count of activities using this agent
```

**Tests to create** (`tests/integration/test_agent_list_find.py`):
- `test_agent_list_01_navigate_from_playbook` - AGENT-LIST-01
- `test_agent_list_02_view_agents_table` - AGENT-LIST-02
- `test_agent_list_03_create_button_navigation` - AGENT-LIST-03
- `test_agent_list_04_search_by_name` - AGENT-LIST-04
- `test_agent_list_05_filter_by_activity_usage` - AGENT-LIST-05 (stub for now)
- `test_agent_list_06_view_usage_count` - AGENT-LIST-06 (stub for now)
- `test_agent_list_07_navigate_to_view` - AGENT-LIST-07
- `test_agent_list_08_empty_state` - AGENT-LIST-08

#### 3.2 Create URL Configuration
**File**: `methodology/agent_urls.py`

```python
from django.urls import path
from methodology import agent_views

urlpatterns = [
    path('', agent_views.agent_list_global, name='agent_list'),
    # Placeholders for create/view/edit/delete (Sub-Stories 2 & 3)
]
```

**File**: `mimir/urls.py` - Add agent URLs

**Commit**: `feat(agents): add global list view with search`

---

### Phase 4: Templates

#### 4.1 Create List Template
**File**: `templates/agents/list.html`

**Template structure** (follow `templates/skills/list.html`):
- Header with icon and description
- Search form with query input
- Agents table showing: Name, Description, Playbook, Actions
- Empty state with "No agents yet" message
- All interactive elements have `data-testid` attributes
- All buttons have Font Awesome icons and Bootstrap tooltips

**Key elements** (per IA Guidelines §4.4, Line 910):
- `data-testid="agents-list"` - Container
- `data-testid="agent-search"` - Search input
- `data-testid="agents-table"` - Table
- `data-testid="agent-row-{{ agent.id }}"` - Table rows
- `data-testid="view-agent-{{ agent.id }}"` - View button
- `data-testid="empty-state"` - Empty state div

**Semantic Structure** (per IA Guidelines §2.6):
```html
<main class="container mt-4" data-testid="agents-list">
  <section class="mb-4">
    <h2><i class="fa-solid fa-brain me-2"></i>Agents</h2>
  </section>
  <section class="card mb-4" role="search">
    <!-- Search form -->
  </section>
</main>
```

**Icon Usage** (per IA Guidelines §1.4):
- Agent icon: `<i class="fa-solid fa-brain"></i>` (Line 938)
- Search icon: `<i class="fa-solid fa-magnifying-glass"></i>` (Line 341)
- View icon: `<i class="fa-solid fa-eye"></i>`
- All icons with `me-2` spacing before text (Line 311)

**Commit**: `feat(agents): add list template with search and empty state`

---

### Phase 5: Integration & Testing

#### 5.1 Run All Tests
```bash
pytest tests/unit/test_agent_model.py -v
pytest tests/unit/test_agent_service.py -v
pytest tests/integration/test_agent_list_find.py -v
```

**Success Criteria**: 100% pass rate (all tests green)

#### 5.2 Manual Testing Checklist
- [ ] Navigate to `/agents/` - list page loads
- [ ] Search for agent by name - results filter correctly
- [ ] Empty state displays when no agents exist
- [ ] All tooltips appear on hover
- [ ] All `data-testid` attributes present

#### 5.3 Update Playbook Stats
**File**: `methodology/models/playbook.py`

Update `get_stats()` method to include agent count:
```python
'agents': self.agents.count(),
```

**Test**: Verify playbook detail page shows agent count

**Commit**: `feat(agents): integrate agent count into playbook stats`

---

## Test Coverage Summary

**Unit Tests**: 19 tests
- Agent Model: 7 tests
- Agent Service: 12 tests

**Integration Tests**: 8 tests
- List/Find scenarios: 8 tests

**Total**: 27 tests (all must pass)

## Definition of Done Checklist

### Code Quality
- [ ] All methods have docstrings with :param:, :returns:, :raises:, and examples
- [ ] All public methods are 20-30 lines max (helpers for complex logic)
- [ ] No `NotImplementedError` stubs remain
- [ ] Logging added at INFO level for all CRUD operations
- [ ] All validation errors have clear messages

### Testing
- [ ] 100% test pass rate (27/27 tests green)
- [ ] All tests use pytest
- [ ] Integration tests use real objects (no mocking)
- [ ] All `data-testid` attributes tested
- [ ] Manual testing checklist completed

### UI/UX
- [ ] All buttons have Font Awesome icons
- [ ] All buttons have Bootstrap tooltips
- [ ] Empty state displays correctly
- [ ] Search functionality works
- [ ] Responsive design (mobile-friendly)

### Documentation
- [ ] Model fields documented in help_text
- [ ] Service methods have complete docstrings
- [ ] View functions documented
- [ ] Template has semantic HTML

### Integration
- [ ] Agent model registered in Django admin
- [ ] URLs configured and accessible
- [ ] Playbook stats include agent count
- [ ] No broken links or 404s

### Git
- [ ] All commits follow Angular convention
- [ ] Commit messages are descriptive
- [ ] Branch: `feature/act-7-agents/model-list-find`
- [ ] Ready to merge into `feature/act-7-agents`

## Files to Create/Modify

**New Files** (8):
1. `methodology/models/agent.py`
2. `methodology/migrations/000X_agent.py`
3. `methodology/services/agent_service.py`
4. `methodology/agent_views.py`
5. `methodology/agent_urls.py`
6. `templates/agents/list.html`
7. `tests/unit/test_agent_model.py`
8. `tests/unit/test_agent_service.py`
9. `tests/integration/test_agent_list_find.py`

**Modified Files** (3):
1. `methodology/admin.py` - Register Agent
2. `methodology/models/__init__.py` - Import Agent
3. `mimir/urls.py` - Include agent_urls
4. `methodology/models/playbook.py` - Add agent count to stats

## Dependencies

**None** - This is the foundation story

## Blocked By

**None**

## Blocks

- Sub-Story 2 (Create + View) - Requires Agent model
- Sub-Story 3 (Edit + Delete) - Requires Agent model

## Estimated Complexity

- **Classes**: 3 (Model, Service, View)
- **Methods**: ~12
- **Tests**: 27
- **Templates**: 1

**Within Copilot threshold**: ✅

## Next Steps After Completion

1. Create PR from `feature/act-7-agents/model-list-find` to `feature/act-7-agents`
2. Review via `@cp-2-review-copilot-work.md`
3. Merge after approval
4. Proceed to Sub-Story 2 (Create + View)
