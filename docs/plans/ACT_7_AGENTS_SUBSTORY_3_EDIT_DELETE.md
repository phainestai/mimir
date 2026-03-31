# Sub-Story 3: Agent Edit + Delete

**Parent Epic**: ACT 7 Agents CRUDLF  
**Date**: 2026-03-30  
**Type**: Feature Implementation  
**Complexity**: 2 classes, ~6 methods ✅  
**Status**: Ready for Copilot Implementation

## Overview

Implement agent editing and deletion functionality. This completes the CRUDLF pattern and enables users to modify existing agents and remove obsolete ones with proper cascade warnings.

## Feature Files Covered

### agents-edit.feature - **4 scenarios**:
- AGENT-EDIT-01: Open edit form
- AGENT-EDIT-02: Edit agent name
- AGENT-EDIT-03: Edit agent description
- AGENT-EDIT-04: Cancel editing

### agents-delete.feature - **5 scenarios**:
- AGENT-DELETE-01: Open delete confirmation
- AGENT-DELETE-02: Modal shows agent details
- AGENT-DELETE-03: Warning about assigned activities
- AGENT-DELETE-04: Confirm deletion
- AGENT-DELETE-05: Cancel deletion

**Total**: 9 scenarios

## Dependencies

**Requires**: 
- Sub-Story 1 (Agent model, AgentService)
- Sub-Story 2 (Detail view for navigation)

**Blocks**: None (final sub-story)

## Architecture References

**Edit Pattern**: Follow `methodology/skill_views.py` (skill_edit)  
**Delete Pattern**: Follow `methodology/artifact_views.py` (artifact_delete)  
**Template Pattern**: Follow `templates/skills/edit.html` and `templates/skills/_delete_modal.html`

## IA Guidelines Compliance

**Reference**: `docs/ux/IA_guidelines.md`

### Form Validation Pattern (§2.2.4, Lines 585-653)
**Pre-populated Form with Validation**:
```html
<input type="text" 
       class="form-control {% if errors.name %}is-invalid{% endif %}" 
       id="name"
       value="{{ agent.name }}"
       required>
<div class="invalid-feedback">
  <i class="fa-solid fa-circle-exclamation me-1"></i>
  {{ errors.name }}
</div>
```

### Delete Modal Pattern (Lines 2050-2150)
**Confirmation Modal with Warnings**:
- Show entity details (agent name, playbook)
- Display cascade warnings (activities affected)
- Danger button for destructive action
- Clear cancel option

### Icon System (§1.4, Lines 275-351)
- **Save Icon**: `fa-floppy-disk` or `fa-save`
- **Delete Icon**: `fa-trash-can` (Line 338)
- **Warning Icon**: `fa-triangle-exclamation` (Line 350)
- **Cancel Icon**: `fa-xmark` (Line 340)

### HTMX Integration (Behavior & Interactions)
- Modal loaded via `hx-get` on delete button click
- Form submission via `hx-post`
- Target: `#modal-container` for modal content
- Swap: `innerHTML` to replace modal content

## Detailed Implementation Plan

### Phase 1: Edit View

#### 1.1 Implement Edit View
**File**: `methodology/agent_views.py` (add to existing file)

**View to implement**:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from methodology.services.agent_service import get_agent, update_agent

@login_required
def agent_edit(request, pk):
    """
    Edit existing agent.
    
    GET: Display edit form with pre-populated data
    POST: Validate and update agent, redirect to detail view
    
    Template: templates/agents/edit.html
    Context (GET and POST on error):
        - agent: Agent - The agent being edited
        - form_data: dict - Form field values (current values on GET, user input on POST)
        - errors: dict - Validation errors (empty on GET, populated on POST if validation fails)
        - playbook: Playbook - Parent playbook (for breadcrumbs)
    
    URL: /agents/<pk>/edit/
    Redirects to: /agents/<pk>/ on success
    """
    # Get agent with permission check
    agent = get_agent(pk)
    
    # Check ownership
    if not agent.can_edit(request.user):
        messages.error(request, "You don't have permission to edit this agent.")
        return redirect('agent_detail', pk=pk)
    
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
            # Update agent via service
            updated_agent = update_agent(pk, name=name, description=description)
            
            # Success message and redirect
            messages.success(request, f'Agent "{updated_agent.name}" updated successfully.')
            return redirect('agent_detail', pk=pk)
            
        except ValidationError as e:
            # Extract error messages from ValidationError
            errors = {}
            if hasattr(e, 'message_dict'):
                errors = e.message_dict
            elif hasattr(e, 'messages'):
                errors = {'__all__': e.messages}
            
            # Re-render form with errors
            context = {
                'agent': agent,
                'form_data': form_data,
                'errors': errors,
                'playbook': agent.playbook,
            }
            return render(request, 'agents/edit.html', context)
    
    # GET request - render form with current values
    form_data = {
        'name': agent.name,
        'description': agent.description,
    }
    
    context = {
        'agent': agent,
        'form_data': form_data,
        'errors': {},
        'playbook': agent.playbook,
    }
    return render(request, 'agents/edit.html', context)
```

**Template Context Contract**:
```python
# templates/agents/edit.html expects:
context = {
    'agent': Agent,        # Agent object being edited
    'form_data': dict,     # Form field values: {'name': str, 'description': str}
    'errors': dict,        # Validation errors: {'name': str, 'description': str, '__all__': list}
    'playbook': Playbook,  # Parent playbook for breadcrumbs
}

# Form data dictionary (pre-populated with current values on GET):
form_data = {
    'name': 'Cautious Developer',      # Current or user-entered name
    'description': 'Expert coder',      # Current or user-entered description
}
```

**Tests to create** (`tests/integration/test_agent_edit.py`):
- `test_agent_edit_01_open_form` - AGENT-EDIT-01
- `test_agent_edit_02_edit_name` - AGENT-EDIT-02
- `test_agent_edit_03_edit_description` - AGENT-EDIT-03
- `test_agent_edit_04_cancel` - AGENT-EDIT-04

**Additional tests**:
- `test_edit_requires_login` - Redirect to login if not authenticated
- `test_edit_requires_ownership` - Permission denied for non-owner
- `test_edit_duplicate_name_fails` - Uniqueness validation
- `test_edit_empty_name_fails` - Required field validation
- `test_edit_agent_not_found` - 404 for non-existent agent

**Commit**: `feat(agents): add edit view with validation`

---

#### 1.2 Create Edit Template
**File**: `templates/agents/edit.html`

**Template structure** (follow `templates/skills/edit.html`):
- Breadcrumb: Playbook → Agents → Agent Name → Edit
- Form with pre-populated fields:
  - Name (required, max 200 chars, current value)
  - Description (textarea, optional, current value)
- Buttons:
  - [Save Changes] - Primary button with icon and tooltip
  - [Cancel] - Secondary button, returns to detail view
- Form validation errors display
- All fields have `data-testid` attributes

**Key elements** (per IA Guidelines §4.4, Line 910):
- `data-testid="agent-edit-form"` - Form
- `data-testid="agent-name-input"` - Name field
- `data-testid="agent-description-input"` - Description field
- `data-testid="save-changes-btn"` - Submit button
- `data-testid="cancel-btn"` - Cancel button

**Form Validation** (per IA Guidelines §2.2.4):
```html
<div class="mb-3">
  <label for="name" class="form-label">
    Agent Name
    <span class="text-danger">*</span>
  </label>
  <input type="text" 
         class="form-control {% if errors.name %}is-invalid{% endif %}" 
         id="name"
         name="name"
         value="{{ agent.name }}"
         required
         maxlength="200"
         data-testid="agent-name-input">
  {% if errors.name %}
  <div class="invalid-feedback">
    <i class="fa-solid fa-circle-exclamation me-1"></i>
    {{ errors.name }}
  </div>
  {% endif %}
</div>
```

**Button Pattern** (per IA Guidelines §1.4):
```html
<button type="submit" class="btn btn-primary" 
        data-testid="save-changes-btn"
        data-bs-toggle="tooltip" title="Save changes to agent">
  <i class="fa-solid fa-floppy-disk me-2"></i>
  Save Changes
</button>
```

**Commit**: `feat(agents): add edit template with pre-populated form`

---

### Phase 2: Delete View & Modal

#### 2.1 Implement Delete View
**File**: `methodology/agent_views.py` (add to existing file)

**View to implement**:
```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from methodology.services.agent_service import get_agent, delete_agent

@login_required
def agent_delete(request, pk):
    """
    Delete agent with confirmation modal.
    
    GET: Render delete confirmation modal (HTMX partial)
    POST: Delete agent and cascade, redirect to playbook detail
    
    Template: templates/agents/_delete_modal.html (GET only)
    Context (GET):
        - agent: Agent - The agent to delete
        - activity_count: int - Number of activities using this agent
        - activities: QuerySet - Activities using this agent (limited to 5 for display)
    
    URL: /agents/<pk>/delete/
    HTMX: GET loads modal, POST deletes and redirects
    Redirects to: /playbooks/<playbook_pk>/ on success (POST)
    """
    # Get agent with permission check
    agent = get_agent(pk)
    
    # Check ownership
    if not agent.can_edit(request.user):
        messages.error(request, "You don't have permission to delete this agent.")
        return redirect('agent_detail', pk=pk)
    
    if request.method == 'POST':
        # Store playbook_id for redirect
        playbook_id = agent.playbook_id
        agent_name = agent.name
        
        # Delete agent
        delete_agent(pk)
        
        # Success message
        messages.success(request, f'Agent "{agent_name}" deleted successfully.')
        
        # Redirect to playbook detail (HTMX will follow redirect)
        return redirect('playbook_detail', pk=playbook_id)
    
    # GET request - render modal partial
    # Get activities using this agent
    activities = agent.activities.select_related('workflow').order_by('name')[:5]
    activity_count = agent.get_activity_count()
    
    context = {
        'agent': agent,
        'activity_count': activity_count,
        'activities': activities,
    }
    return render(request, 'agents/_delete_modal.html', context)
```

**Template Context Contract**:
```python
# templates/agents/_delete_modal.html expects:
context = {
    'agent': Agent,           # Agent to delete
    'activity_count': int,    # Total count of activities using this agent
    'activities': QuerySet,   # First 5 activities (for display in modal)
}

# Agent object provides:
agent.id                  # int - Primary key
agent.name                # str - Agent name
agent.playbook.name       # str - Playbook name

# Each activity provides:
activity.name             # str - Activity name
activity.workflow.name    # str - Workflow name
```

**HTMX Integration Specification**:
```html
<!-- In templates/agents/detail.html -->
<!-- Delete button triggers modal load -->
<button class="btn btn-danger" 
        hx-get="{% url 'agent_delete' pk=agent.pk %}"
        hx-target="#modal-container"
        hx-swap="innerHTML"
        data-testid="delete-agent-btn"
        data-bs-toggle="tooltip" 
        title="Delete this agent permanently">
  <i class="fa-solid fa-trash-can me-2"></i>
  Delete Agent
</button>

<!-- Modal container (in base.html or detail.html) -->
<div id="modal-container"></div>

<!-- In templates/agents/_delete_modal.html -->
<!-- Modal with form for deletion -->
<div class="modal fade show" style="display: block;" tabindex="-1">
  <div class="modal-dialog" data-testid="delete-modal">
    <div class="modal-content">
      <form method="POST" action="{% url 'agent_delete' pk=agent.pk %}">
        {% csrf_token %}
        <!-- Modal content -->
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" 
                  data-bs-dismiss="modal"
                  onclick="document.getElementById('modal-container').innerHTML=''"
                  data-testid="cancel-delete-btn">
            <i class="fa-solid fa-xmark me-2"></i>
            Cancel
          </button>
          <button type="submit" class="btn btn-danger" 
                  data-testid="confirm-delete-btn">
            <i class="fa-solid fa-trash-can me-2"></i>
            Delete Agent
          </button>
        </div>
      </form>
    </div>
  </div>
</div>
<div class="modal-backdrop fade show"></div>
```

**Tests to create** (`tests/integration/test_agent_delete.py`):
- `test_agent_delete_01_open_modal` - AGENT-DELETE-01
- `test_agent_delete_02_shows_details` - AGENT-DELETE-02
- `test_agent_delete_03_activity_warning` - AGENT-DELETE-03
- `test_agent_delete_04_confirm` - AGENT-DELETE-04
- `test_agent_delete_05_cancel` - AGENT-DELETE-05

**Additional tests**:
- `test_delete_requires_login` - Redirect to login if not authenticated
- `test_delete_requires_ownership` - Permission denied for non-owner
- `test_delete_agent_not_found` - 404 for non-existent agent
- `test_delete_cascades_to_activities` - Activity.agent set to NULL

**Commit**: `feat(agents): add delete view with cascade warnings`

---

#### 2.2 Create Delete Modal Template
**File**: `templates/agents/_delete_modal.html`

**Template structure** (follow `templates/skills/_delete_modal.html`):
- Modal header: "Delete Agent?"
- Agent details:
  - Agent name
  - Playbook name
- Warning section (AGENT-DELETE-03):
  - If agent has activities: "Used in X activities"
  - List of activities (up to 5, with "and X more" if >5)
  - Warning: "Agent assignments will be removed from these activities"
  - If no activities: "This agent is not currently assigned to any activities"
- Buttons:
  - [Delete Agent] - Danger button with icon and tooltip
  - [Cancel] - Secondary button, closes modal
- All elements have `data-testid` attributes

**Key elements** (per IA Guidelines §4.4, Line 910):
- `data-testid="delete-modal"` - Modal container
- `data-testid="agent-name-display"` - Agent name
- `data-testid="activity-count"` - Activity count warning
- `data-testid="activity-list"` - Activity list
- `data-testid="confirm-delete-btn"` - Delete button
- `data-testid="cancel-delete-btn"` - Cancel button

**Modal Structure** (per IA Guidelines Delete Modal Pattern):
```html
<div class="modal-dialog" data-testid="delete-modal">
  <div class="modal-content">
    <div class="modal-header">
      <h5 class="modal-title">
        <i class="fa-solid fa-triangle-exclamation text-danger me-2"></i>
        Delete Agent?
      </h5>
    </div>
    <div class="modal-body">
      <p>You are about to delete:</p>
      <p class="fw-bold" data-testid="agent-name-display">{{ agent.name }}</p>
      
      {% if activity_count > 0 %}
      <div class="alert alert-warning" data-testid="activity-count">
        <i class="fa-solid fa-triangle-exclamation me-2"></i>
        <strong>Used in {{ activity_count }} activities</strong>
      </div>
      <ul data-testid="activity-list">
        {% for activity in activities|slice:":5" %}
        <li>{{ activity.name }}</li>
        {% endfor %}
        {% if activity_count > 5 %}
        <li class="text-muted">...and {{ activity_count|add:"-5" }} more</li>
        {% endif %}
      </ul>
      <p class="text-danger">
        <i class="fa-solid fa-circle-exclamation me-1"></i>
        Agent assignments will be removed from these activities.
      </p>
      {% endif %}
    </div>
    <div class="modal-footer">
      <button type="button" class="btn btn-secondary" 
              data-bs-dismiss="modal"
              data-testid="cancel-delete-btn"
              data-bs-toggle="tooltip" title="Cancel deletion">
        <i class="fa-solid fa-xmark me-2"></i>
        Cancel
      </button>
      <button type="submit" class="btn btn-danger" 
              data-testid="confirm-delete-btn"
              data-bs-toggle="tooltip" title="Permanently delete this agent">
        <i class="fa-solid fa-trash-can me-2"></i>
        Delete Agent
      </button>
    </div>
  </div>
</div>
```

**HTMX Integration**:
- Modal loaded via HTMX when delete button clicked on detail page
- Form submission via HTMX POST
- On success: Redirect to playbook detail
- On cancel: Close modal (no page reload)

**Commit**: `feat(agents): add delete modal with activity warnings`

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
    path('<int:pk>/edit/', agent_views.agent_edit, name='agent_edit'),
    path('<int:pk>/delete/', agent_views.agent_delete, name='agent_delete'),
]
```

**Test URL resolution**:
- `/agents/42/edit/` → agent_edit
- `/agents/42/delete/` → agent_delete

**Commit**: `feat(agents): add edit and delete URL routes`

---

### Phase 4: Navigation Integration

#### 4.1 Update Detail Template
**File**: `templates/agents/detail.html` (modify existing)

Wire up action buttons:
- [Edit Agent] button → Links to `agent_edit` URL
- [Delete Agent] button → HTMX trigger to load delete modal

**HTMX attributes for delete button**:
```html
<button hx-get="{% url 'agent_delete' pk=agent.pk %}"
        hx-target="#modal-container"
        hx-swap="innerHTML"
        data-testid="delete-agent-btn">
```

**Commit**: `feat(agents): wire up edit and delete navigation`

---

### Phase 5: Cascade Behavior

#### 5.1 Update Activity Model Cascade
**File**: `methodology/models/activity.py` (verify existing)

Ensure agent field has correct cascade behavior:
```python
agent = models.ForeignKey(
    'Agent',
    on_delete=models.SET_NULL,  # ← Important: SET_NULL, not CASCADE
    null=True,
    blank=True,
    related_name='activities'
)
```

**Behavior**: When agent deleted, `activity.agent` set to NULL (not deleted).

**Test**: Verify in `test_delete_cascades_to_activities`

---

### Phase 6: Integration & Testing

#### 6.1 Run All Tests
```bash
pytest tests/integration/test_agent_edit.py -v
pytest tests/integration/test_agent_delete.py -v
```

**Success Criteria**: 100% pass rate (17 tests green)

#### 6.2 Manual Testing Checklist
- [ ] View agent detail → Click [Edit Agent] → Form loads with current values
- [ ] Edit name → Save → Agent updated, redirected to detail
- [ ] Edit description → Save → Description updated
- [ ] Try to save empty name → Validation error shown
- [ ] Click Cancel → Returns to detail view without saving
- [ ] View agent detail → Click [Delete Agent] → Modal appears
- [ ] Modal shows agent name and playbook
- [ ] Agent with activities → Warning and list displayed
- [ ] Agent without activities → "Not assigned" message shown
- [ ] Click [Delete Agent] in modal → Agent deleted, redirected to playbook
- [ ] Click [Cancel] in modal → Modal closes, agent not deleted
- [ ] Verify activities previously using agent now have agent=NULL
- [ ] All tooltips appear on hover
- [ ] All buttons have icons

#### 6.3 Edge Cases to Test
- [ ] Edit agent to duplicate name in same playbook → Error
- [ ] Edit agent to name that exists in different playbook → Success
- [ ] Delete agent with 10+ activities → List truncated with "and X more"
- [ ] Delete agent while another user viewing → Graceful error handling

**Commit**: `test(agents): add comprehensive edit and delete tests`

---

## Test Coverage Summary

**Integration Tests**: 17 tests
- Edit scenarios: 9 tests (4 scenarios + 5 additional)
- Delete scenarios: 8 tests (5 scenarios + 3 additional)

**Total**: 17 tests (all must pass)

## Definition of Done Checklist

### Code Quality
- [ ] All methods have docstrings with :param:, :returns:, :raises:, examples
- [ ] All public methods are 20-30 lines max
- [ ] No `NotImplementedError` stubs remain
- [ ] Logging added at INFO level for edit/delete operations
- [ ] All validation errors have clear messages

### Testing
- [ ] 100% test pass rate (17/17 tests green)
- [ ] All tests use pytest
- [ ] Integration tests use real objects (no mocking)
- [ ] All `data-testid` attributes tested
- [ ] Cascade behavior tested
- [ ] Manual testing checklist completed

### UI/UX
- [ ] All buttons have Font Awesome icons
- [ ] All buttons have Bootstrap tooltips
- [ ] Form validation displays clearly
- [ ] Delete modal shows appropriate warnings
- [ ] Activity list in modal displays correctly
- [ ] HTMX interactions work smoothly
- [ ] Breadcrumbs work correctly
- [ ] Responsive design (mobile-friendly)

### Documentation
- [ ] View functions documented
- [ ] Templates have semantic HTML
- [ ] Form fields have help text
- [ ] Modal warnings are clear

### Integration
- [ ] URLs accessible and resolve correctly
- [ ] Navigation from detail view works
- [ ] Edit/Delete buttons appear in correct contexts
- [ ] Cascade behavior works as expected (SET_NULL)
- [ ] No broken links or 404s
- [ ] HTMX modal loads and submits correctly

### Git
- [ ] All commits follow Angular convention
- [ ] Commit messages are descriptive
- [ ] Branch: `feature/act-7-agents/edit-delete`
- [ ] Ready to merge into `feature/act-7-agents`

## Files to Create/Modify

**New Files** (3):
1. `templates/agents/edit.html`
2. `templates/agents/_delete_modal.html`
3. `tests/integration/test_agent_edit.py`
4. `tests/integration/test_agent_delete.py`

**Modified Files** (4):
1. `methodology/agent_views.py` - Add edit and delete views
2. `methodology/agent_urls.py` - Add edit and delete routes
3. `templates/agents/detail.html` - Wire up edit/delete buttons
4. `methodology/models/activity.py` - Verify cascade behavior

## Dependencies

**Requires**: 
- Sub-Story 1 completed (Agent model, AgentService)
- Sub-Story 2 completed (Detail view, navigation)

## Blocked By

Sub-Stories 1 & 2 must be completed first

## Blocks

None (final sub-story)

## Estimated Complexity

- **Classes**: 2 (Edit View, Delete View)
- **Methods**: ~6
- **Tests**: 17
- **Templates**: 2

**Within Copilot threshold**: ✅

## Epic Completion

After this sub-story is merged, the ACT 7 Agents CRUDLF epic is **COMPLETE**:
- ✅ Model + List/Find (Sub-Story 1)
- ✅ Create + View (Sub-Story 2)
- ✅ Edit + Delete (Sub-Story 3)

**Total**: 27 scenarios, 61 tests, full CRUDLF functionality

## Next Steps After Completion

1. Create PR from `feature/act-7-agents/edit-delete` to `feature/act-7-agents`
2. Review via `@cp-2-review-copilot-work.md`
3. Merge after approval
4. **Final Epic Review**:
   - Run all 61 tests across all 3 sub-stories
   - Verify 100% pass rate
   - Manual smoke test of complete CRUDLF flow
   - Check Definition of Done for entire epic
5. Create PR from `feature/act-7-agents` to `main`
6. Get user acceptance
7. Merge to main
8. **ACT 7 Agents COMPLETE** 🎉
