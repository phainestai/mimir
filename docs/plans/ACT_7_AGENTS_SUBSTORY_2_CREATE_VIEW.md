# Sub-Story 2: Agent Create + View

**Parent Epic**: ACT 7 Agents CRUDLF  
**Date**: 2026-03-30  
**Type**: Feature Implementation  
**Complexity**: 2 classes, ~8 methods ✅  
**Status**: Ready for Copilot Implementation

## Overview

Implement agent creation and detail viewing functionality. This builds on Sub-Story 1 (model must exist) and enables users to create new agents and view their details.

## Feature Files Covered

### agents-create.feature - **4 scenarios**:
- AGENT-CREATE-01: Open create agent form
- AGENT-CREATE-02: Create agent successfully
- AGENT-CREATE-03: Validate required fields
- AGENT-CREATE-04: Cancel agent creation

### agents-view.feature - **6 scenarios**:
- AGENT-VIEW-01: Open agent detail page
- AGENT-VIEW-02: View agent header
- AGENT-VIEW-03: View agent description
- AGENT-VIEW-04: View activities using this agent
- AGENT-VIEW-05: Edit agent button
- AGENT-VIEW-06: Delete agent button

**Total**: 10 scenarios

## Dependencies

**Requires**: Sub-Story 1 (Agent model, AgentService, list view)

**Blocks**: Sub-Story 3 (Edit/Delete views need detail view to exist)

## Architecture References

**Create Pattern**: Follow `methodology/artifact_views.py` (artifact_create)  
**View Pattern**: Follow `methodology/skill_views.py` (skill_detail)  
**Template Pattern**: Follow `templates/skills/create.html` and `templates/skills/detail.html`

## IA Guidelines Compliance

**Reference**: `docs/ux/IA_guidelines.md`

### Form Validation Pattern (§2.2.4, Lines 585-653)
**Field-Level Validation**:
```html
<input type="text" class="form-control is-invalid" id="name">
<div class="invalid-feedback">
  <i class="fa-solid fa-circle-exclamation me-1"></i>
  This field is required.
</div>
```

**Validation Messages** (Lines 633-639):
- Required fields: `"This field is required."`
- Unique constraint: `"An agent with this name already exists in this playbook"`
- Max length: `"Agent name cannot exceed 200 characters"`

### Icon System (§1.4, Lines 275-351)
- **Agent Icon**: `fa-brain` (Line 938)
- **Create Icon**: `fa-plus` (Line 339)
- **Save Icon**: `fa-save` or `fa-floppy-disk`
- **Cancel Icon**: `fa-xmark` (Line 340)
- **Edit Icon**: `fa-pen-to-square` (Line 337)
- **Delete Icon**: `fa-trash-can` (Line 338)

### Semantic HTML (§2.6, Lines 1040-1072)
- Use `<main>` for primary content
- Use `<form>` with proper `method="POST"` and CSRF token
- Use `<button type="submit">` not `<a>` styled as button
- Include ARIA labels for accessibility

### Responsive Behavior (§2.8, Lines 1123-1193)
- Forms stack vertically on mobile (default Bootstrap behavior)
- Touch-friendly button sizes (min 44x44px)
- Readable form labels on all screen sizes

## Detailed Implementation Plan

### Phase 1: Create View

#### 1.1 Implement Create View
**File**: `methodology/agent_views.py` (add to existing file)

**View to implement**:
```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from methodology.models import Playbook
from methodology.services.agent_service import create_agent

@login_required
def agent_create(request, playbook_pk):
    """
    Create new agent for playbook.
    
    GET: Display create form
    POST: Validate and create agent, redirect to playbook detail
    
    Template: templates/agents/create.html
    Context (GET and POST on error):
        - playbook: Playbook - The playbook to create agent for
        - form_data: dict - Form field values (empty on GET, populated on POST)
        - errors: dict - Validation errors (empty on GET, populated on POST if validation fails)
    
    URL: /agents/create/<playbook_pk>/
    Redirects to: /playbooks/<playbook_pk>/ on success
    """
    # Get playbook with permission check
    playbook = get_object_or_404(Playbook, pk=playbook_pk)
    
    # Check ownership
    if not playbook.is_owned_by(request.user):
        messages.error(request, "You don't have permission to add agents to this playbook.")
        return redirect('playbook_detail', pk=playbook_pk)
    
    if request.method == 'POST':
        # Extract form data
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Prepare form data for re-rendering on error
        form_data = {
            'name': name,
            'description': description,
        }
        
        try:
            # Create agent via service
            agent = create_agent(playbook, name, description)
            
            # Success message and redirect
            messages.success(request, f'Agent "{agent.name}" created successfully.')
            return redirect('playbook_detail', pk=playbook_pk)
            
        except ValidationError as e:
            # Extract error messages from ValidationError
            errors = {}
            if hasattr(e, 'message_dict'):
                errors = e.message_dict
            elif hasattr(e, 'messages'):
                errors = {'__all__': e.messages}
            
            # Re-render form with errors
            context = {
                'playbook': playbook,
                'form_data': form_data,
                'errors': errors,
            }
            return render(request, 'agents/create.html', context)
    
    # GET request - render empty form
    context = {
        'playbook': playbook,
        'form_data': {},
        'errors': {},
    }
    return render(request, 'agents/create.html', context)
```

**Template Context Contract**:
```python
# templates/agents/create.html expects:
context = {
    'playbook': Playbook,  # Playbook object with .id, .name, .get_absolute_url()
    'form_data': dict,     # Form field values: {'name': str, 'description': str}
    'errors': dict,        # Validation errors: {'name': str, 'description': str, '__all__': list}
}

# Error dictionary structure:
errors = {
    'name': 'Agent name cannot be empty',  # Field-specific error
    'description': 'Description too long',  # Field-specific error
    '__all__': ['General error message'],  # Form-level errors (list)
}

# Form data dictionary structure:
form_data = {
    'name': 'Cautious Developer',      # User-entered name (or empty string)
    'description': 'Expert coder',      # User-entered description (or empty string)
}
```

**Tests to create** (`tests/integration/test_agent_create.py`):
- `test_agent_create_01_open_form` - AGENT-CREATE-01
- `test_agent_create_02_success` - AGENT-CREATE-02
- `test_agent_create_03_validation` - AGENT-CREATE-03
- `test_agent_create_04_cancel` - AGENT-CREATE-04

**Additional tests**:
- `test_create_requires_login` - Redirect to login if not authenticated
- `test_create_requires_ownership` - Permission denied for non-owner
- `test_create_duplicate_name_fails` - Uniqueness validation

**Commit**: `feat(agents): add create view with validation`

---

#### 1.2 Create Template
**File**: `templates/agents/create.html`

**Template structure** (follow `templates/skills/create.html`):
- Breadcrumb: Playbook → Create Agent
- Form with fields:
  - Name (required, max 200 chars)
  - Description (textarea, optional)
- Buttons:
  - [Create Agent] - Primary button with icon and tooltip
  - [Cancel] - Secondary button, returns to playbook detail
- Form validation errors display
- All fields have `data-testid` attributes

**Key elements** (per IA Guidelines §4.4, Line 910):
- `data-testid="agent-create-form"` - Form
- `data-testid="agent-name-input"` - Name field
- `data-testid="agent-description-input"` - Description field
- `data-testid="create-agent-btn"` - Submit button
- `data-testid="cancel-btn"` - Cancel button

**Form Validation** (per IA Guidelines §2.2.4):
```html
<!-- Name field with validation -->
<div class="mb-3">
  <label for="name" class="form-label">
    Agent Name
    <span class="text-danger">*</span>
  </label>
  <input type="text" 
         class="form-control {% if errors.name %}is-invalid{% endif %}" 
         id="name"
         name="name"
         value="{{ form_data.name }}"
         required
         maxlength="200"
         data-testid="agent-name-input">
  {% if errors.name %}
  <div class="invalid-feedback">
    <i class="fa-solid fa-circle-exclamation me-1"></i>
    {{ errors.name }}
  </div>
  {% endif %}
  <div class="form-text">Choose a descriptive name (max 200 characters)</div>
</div>
```

**Button Pattern** (per IA Guidelines §1.4, Line 311):
```html
<button type="submit" class="btn btn-primary" data-testid="create-agent-btn"
        data-bs-toggle="tooltip" title="Create new agent">
  <i class="fa-solid fa-plus me-2"></i>
  Create Agent
</button>
<a href="{% url 'playbook_detail' pk=playbook.pk %}" 
   class="btn btn-secondary" data-testid="cancel-btn"
   data-bs-toggle="tooltip" title="Return to playbook without saving">
  <i class="fa-solid fa-xmark me-2"></i>
  Cancel
</a>
```

**Commit**: `feat(agents): add create template with form validation`

---

### Phase 2: Detail View

#### 2.1 Implement Detail View
**File**: `methodology/agent_views.py` (add to existing file)

**View to implement**:
```python
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from methodology.services.agent_service import get_agent

@login_required
def agent_detail(request, pk):
    """
    Display agent details with activity usage.
    
    Shows agent info, activities using this agent, and action buttons.
    
    Template: templates/agents/detail.html
    Context:
        - agent: Agent - The agent to display
        - activities: QuerySet - Activities using this agent (ordered by name)
        - can_edit: bool - Whether user can edit this agent
        - playbook: Playbook - Parent playbook (for breadcrumbs)
    
    URL: /agents/<pk>/
    """
    # Get agent with related data
    agent = get_agent(pk)
    
    # Get activities using this agent
    activities = agent.activities.select_related('workflow').order_by('name')
    
    # Check if user can edit
    can_edit = agent.can_edit(request.user)
    
    # Render template
    context = {
        'agent': agent,
        'activities': activities,
        'can_edit': can_edit,
        'playbook': agent.playbook,
    }
    return render(request, 'agents/detail.html', context)
```

**Template Context Contract**:
```python
# templates/agents/detail.html expects:
context = {
    'agent': Agent,           # Agent object with .id, .name, .description, .playbook, .created_at, .updated_at
    'activities': QuerySet,   # Activities using this agent (may be empty)
    'can_edit': bool,         # True if user can edit, False otherwise
    'playbook': Playbook,     # Parent playbook for breadcrumbs
}

# Agent object provides:
agent.id                        # int - Primary key
agent.name                      # str - Agent name
agent.description               # str - Agent description (may be empty)
agent.playbook                  # Playbook - Parent playbook
agent.created_at                # datetime - Creation timestamp
agent.updated_at                # datetime - Last update timestamp
agent.get_absolute_url()        # str - URL to this detail page
agent.get_activity_count()      # int - Count of activities

# Each activity provides:
activity.id                     # int - Primary key
activity.name                   # str - Activity name
activity.workflow               # Workflow - Parent workflow (preloaded)
activity.workflow.name          # str - Workflow name
activity.get_absolute_url()     # str - URL to activity detail
```

**Tests to create** (`tests/integration/test_agent_view.py`):
- `test_agent_view_01_open_detail` - AGENT-VIEW-01
- `test_agent_view_02_header` - AGENT-VIEW-02
- `test_agent_view_03_description` - AGENT-VIEW-03
- `test_agent_view_04_activities` - AGENT-VIEW-04
- `test_agent_view_05_edit_button` - AGENT-VIEW-05
- `test_agent_view_06_delete_button` - AGENT-VIEW-06

**Additional tests**:
- `test_view_requires_login` - Redirect to login if not authenticated
- `test_view_agent_not_found` - 404 for non-existent agent
- `test_view_shows_empty_activities` - Empty state when no activities use agent

**Commit**: `feat(agents): add detail view with activity relationships`

---

#### 2.2 Create Detail Template
**File**: `templates/agents/detail.html`

**Template structure** (follow `templates/skills/detail.html`):
- Breadcrumb: Playbook → Agents → Agent Name
- Header section:
  - Agent name with icon
  - Playbook badge (clickable link)
  - Created/Updated timestamps
- Description section:
  - Full description (Markdown-rendered if needed)
- Activities section (AGENT-VIEW-04):
  - "Used in Activities" heading
  - List of activities using this agent
  - Empty state if no activities
  - Each activity is clickable link
- Action buttons:
  - [Edit Agent] - Navigate to edit view (Sub-Story 3)
  - [Delete Agent] - Open delete modal (Sub-Story 3)
  - Both buttons have icons and tooltips

**Key elements** (per IA Guidelines §4.4, Line 910):
- `data-testid="agent-detail"` - Container
- `data-testid="agent-name"` - Name heading
- `data-testid="agent-description"` - Description section
- `data-testid="agent-activities"` - Activities list
- `data-testid="edit-agent-btn"` - Edit button
- `data-testid="delete-agent-btn"` - Delete button
- `data-testid="activity-link-{{ activity.id }}"` - Activity links

**Semantic Structure** (per IA Guidelines §2.6):
```html
<main class="container mt-4" data-testid="agent-detail">
  <nav aria-label="breadcrumb">
    <!-- Breadcrumbs -->
  </nav>
  
  <article>
    <header>
      <h1 data-testid="agent-name">
        <i class="fa-solid fa-brain me-2"></i>
        {{ agent.name }}
      </h1>
    </header>
    
    <section data-testid="agent-description">
      <h2>Description</h2>
      {{ agent.description }}
    </section>
    
    <section data-testid="agent-activities">
      <h2>Used in Activities</h2>
      <!-- Activity list -->
    </section>
  </article>
</main>
```

**Action Buttons** (per IA Guidelines §1.4):
```html
<button class="btn btn-primary" data-testid="edit-agent-btn"
        data-bs-toggle="tooltip" title="Edit agent details">
  <i class="fa-solid fa-pen-to-square me-2"></i>
  Edit Agent
</button>
<button class="btn btn-danger" data-testid="delete-agent-btn"
        data-bs-toggle="tooltip" title="Delete this agent permanently">
  <i class="fa-solid fa-trash-can me-2"></i>
  Delete Agent
</button>
```

**Commit**: `feat(agents): add detail template with activity relationships`

---

### Phase 3: URL Configuration

#### 3.1 Update URL Patterns
**File**: `methodology/agent_urls.py`

Add routes:
```python
urlpatterns = [
    path('', agent_views.agent_list_global, name='agent_list'),
    path('create/<int:playbook_pk>/', agent_views.agent_create, name='agent_create'),
    path('<int:pk>/', agent_views.agent_detail, name='agent_detail'),
    # Placeholders for edit/delete (Sub-Story 3)
]
```

**Test URL resolution**:
- `/agents/` → agent_list
- `/agents/create/1/` → agent_create
- `/agents/42/` → agent_detail

**Commit**: `feat(agents): add create and detail URL routes`

---

### Phase 4: Navigation Integration

#### 4.1 Add Create Button to List View
**File**: `templates/agents/list.html` (modify existing)

Add "Create New Agent" button to header (visible when viewing from playbook context).

**Note**: Global list doesn't have create button (needs playbook context).

#### 4.2 Add Agents Tab to Playbook Detail
**File**: `templates/playbooks/detail.html` (modify existing)

Add "Agents" tab to playbook detail navigation (similar to Workflows, Activities, Artifacts, Skills tabs).

**Tab content**:
- Shows agent count badge
- Links to filtered agent list for this playbook
- [Create New Agent] button

**Commit**: `feat(agents): integrate navigation into playbook detail`

---

### Phase 5: Activity Relationship (Stub)

#### 5.1 Add Agent Field to Activity Model (Stub)
**File**: `methodology/models/activity.py` (modify existing)

**Note**: This is a stub for AGENT-VIEW-04 testing. Full implementation comes later.

Add field:
```python
agent = models.ForeignKey(
    'Agent',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='activities',
    help_text="AI agent that performs this activity"
)
```

Create migration: `python manage.py makemigrations`

**Purpose**: Enables testing of "activities using this agent" display.

**Commit**: `feat(agents): add agent relationship to Activity model (stub)`

---

### Phase 6: Integration & Testing

#### 6.1 Run All Tests
```bash
pytest tests/integration/test_agent_create.py -v
pytest tests/integration/test_agent_view.py -v
```

**Success Criteria**: 100% pass rate (17 tests green)

#### 6.2 Manual Testing Checklist
- [ ] Navigate to playbook detail → Click "Create Agent" → Form loads
- [ ] Fill form with valid data → Submit → Agent created, redirected
- [ ] Try to create agent with empty name → Validation error shown
- [ ] Click Cancel → Returns to playbook detail
- [ ] View agent detail → All sections display correctly
- [ ] Agent with no activities → Empty state displays
- [ ] Agent with activities → Activity list displays
- [ ] All tooltips appear on hover
- [ ] All buttons have icons

#### 6.3 Test Data Setup
Create test fixtures for integration tests:
- Playbook with 2-3 agents
- Activities with/without agent assignments
- Multiple users for permission testing

**Commit**: `test(agents): add integration test fixtures`

---

## Test Coverage Summary

**Integration Tests**: 17 tests
- Create scenarios: 7 tests (4 scenarios + 3 additional)
- View scenarios: 9 tests (6 scenarios + 3 additional)
- Navigation: 1 test

**Total**: 17 tests (all must pass)

## Definition of Done Checklist

### Code Quality
- [ ] All methods have docstrings with :param:, :returns:, :raises:, examples
- [ ] All public methods are 20-30 lines max
- [ ] No `NotImplementedError` stubs remain
- [ ] Logging added at INFO level for create/view operations
- [ ] All validation errors have clear messages

### Testing
- [ ] 100% test pass rate (17/17 tests green)
- [ ] All tests use pytest
- [ ] Integration tests use real objects (no mocking)
- [ ] All `data-testid` attributes tested
- [ ] Manual testing checklist completed

### UI/UX
- [ ] All buttons have Font Awesome icons
- [ ] All buttons have Bootstrap tooltips
- [ ] Form validation displays clearly
- [ ] Empty states display correctly
- [ ] Breadcrumbs work correctly
- [ ] Responsive design (mobile-friendly)

### Documentation
- [ ] View functions documented
- [ ] Templates have semantic HTML
- [ ] Form fields have help text

### Integration
- [ ] URLs accessible and resolve correctly
- [ ] Navigation from playbook detail works
- [ ] Create button appears in correct contexts
- [ ] Activity relationship displays (even if stub)
- [ ] No broken links or 404s

### Git
- [ ] All commits follow Angular convention
- [ ] Commit messages are descriptive
- [ ] Branch: `feature/act-7-agents/create-view`
- [ ] Ready to merge into `feature/act-7-agents`

## Files to Create/Modify

**New Files** (3):
1. `templates/agents/create.html`
2. `templates/agents/detail.html`
3. `tests/integration/test_agent_create.py`
4. `tests/integration/test_agent_view.py`

**Modified Files** (5):
1. `methodology/agent_views.py` - Add create and detail views
2. `methodology/agent_urls.py` - Add create and detail routes
3. `templates/agents/list.html` - Add create button
4. `templates/playbooks/detail.html` - Add Agents tab
5. `methodology/models/activity.py` - Add agent field (stub)
6. `methodology/migrations/000X_activity_agent_field.py` - Migration

## Dependencies

**Requires**: Sub-Story 1 completed and merged
- Agent model exists
- AgentService has CRUD methods
- List view functional

## Blocked By

Sub-Story 1 must be completed first

## Blocks

Sub-Story 3 (Edit/Delete) - Needs detail view and navigation

## Estimated Complexity

- **Classes**: 2 (Create View, Detail View)
- **Methods**: ~8
- **Tests**: 17
- **Templates**: 2

**Within Copilot threshold**: ✅

## Next Steps After Completion

1. Create PR from `feature/act-7-agents/create-view` to `feature/act-7-agents`
2. Review via `@cp-2-review-copilot-work.md`
3. Merge after approval
4. Proceed to Sub-Story 3 (Edit + Delete)
