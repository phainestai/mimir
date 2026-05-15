# PIP Sub-Story 2: Create PIP with Structured Changes

**Feature file**: `docs/features/act-9-pips/pips-create.feature`  
**Scenarios**: FOB-PIP-CREATE-01 … 19  
**Complexity**: hard — HTMX change management, dynamic form, preview diff  
**Branch**: `feature/act-9-pips/create`  
**Depends on**: PIP-LIST (model + `PIPService` foundation)  
**Blocks**: PIP-VIEW (submit action), PIP-GALDR-ENGINE (triggered on submit)

---

## Overview

Implements PIP creation with a two-part form: PIP header (title + summary + target playbook) and an HTMX-powered Change list (add/remove Changes with type-specific fields). Covers three entry points (from Released playbook detail, from PIPs list, from nav pill), form validation, all three change types (ADD / ALTER / DROP), diff preview, save as draft, and submit for review.

**Scenarios covered:**
- CREATE-01/02/03 — Entry points, target playbook pre-fill, draft exclusion
- CREATE-04/05 — Form validation (submit disabled until ready, title required)
- CREATE-06/07/08 — ADD changes (append/insert/workflow)
- CREATE-09/10 — ALTER changes (activity/skill)
- CREATE-11 — DROP change with rationale
- CREATE-12/13/14/15 — Change list management (order, remove, validation)
- CREATE-16 — Preview Diff
- CREATE-17/18 — Save as Draft, Submit for Review
- CREATE-19 — Cancel with confirmation modal

---

## BPE-02: Backend Implementation

### Step 1 — `PIPService` create & change methods

**File**: `methodology/services/pip_service.py` (extend from PIP-LIST)

Add skeletons → tests → implement:

```python
def create_pip(user, playbook, title: str, summary: str = "") -> "ProcessImprovementProposal":
    """
    Create a Draft PIP for the given Released playbook.

    :param user: User — submitter
    :param playbook: Playbook instance — must have status 'released'
    :param title: str, required. Example: "Add Accessibility Audit"
    :param summary: str, optional rationale. Example: "Playbook lacks WCAG 2.1 AA coverage"
    :returns: ProcessImprovementProposal with status='draft'
    :raises ValidationError: if title empty or playbook is not released
    :example: pip = create_pip(maria, playbook1, "Add Accessibility Audit")
    """
    # Log: user.id, playbook.id, title

def add_change(pip, change_type: str, entity_type: str, name: str = "",
               target_id: int = None, target_name: str = "", content: str = "",
               parent_workflow_id: int = None, insert_after_id: int = None) -> "PIPChange":
    """
    Add a typed Change to a Draft PIP. Auto-assigns order = count + 1.

    :param pip: ProcessImprovementProposal — must be Draft
    :raises ValidationError: if pip.status != 'draft'
    :raises ValidationError: if ADD and name empty
    :raises ValidationError: if ADD and content empty
    :raises ValidationError: if DROP and content (rationale) empty
    :raises ValidationError: if ALTER and target_id None
    :raises ValueError: if entity_type not in valid choices
    :example: add_change(pip, "ADD", "Activity", name="Accessibility Audit",
                         parent_workflow_id=11, content="Ensure WCAG 2.1 AA.")
    """
    # Log: pip.id, change_type, entity_type, name/target_id

def edit_change(change_id: int, pip, **kwargs) -> "PIPChange":
    """
    Update allowed fields on an existing Change. Only valid on Draft PIPs.

    :raises ValidationError: if pip.status != 'draft'
    :raises ValueError: if change_id does not belong to pip
    """

def remove_change(change_id: int, pip) -> None:
    """
    Delete a Change and renumber remaining changes by order.

    :raises ValidationError: if pip.status != 'draft'
    """
    # Log: pip.id, change_id, remaining count after deletion

def update_pip_header(pip, user, title: str = None, summary: str = None) -> "ProcessImprovementProposal":
    """
    Update title/summary on a Draft PIP.

    :raises ValidationError: if pip.status != 'draft'
    """

def submit_pip(pip, user) -> "ProcessImprovementProposal":
    """
    Transition pip from Draft → Submitted.

    :raises ValidationError: if pip.status != 'draft'
    :raises ValidationError: if pip has 0 Changes
    :raises PermissionError: if user != pip.created_by
    :returns: PIP with status='submitted', submitted_at=now(), status_changed_at=now()
    """
    # Log: pip.id, user.id, change count

def cancel_pip(pip, user) -> None:
    """
    Cancel (delete) a Draft PIP or reject a Submitted/Processing PIP.

    Draft → deleted. Submitted/Processing → status='rejected'.

    :raises PermissionError: if user != pip.created_by
    :raises ValidationError: if pip.status not in (draft, submitted, processing_galdr)
    """
    # Log: pip.id, user.id, prior status, action taken
```

**Unit tests** (`tests/unit/test_pip_service_create.py`):
- [ ] `test_create_pip_draft_status`
- [ ] `test_create_pip_validates_released_playbook`
- [ ] `test_create_pip_rejects_empty_title`
- [ ] `test_add_change_auto_assigns_order`
- [ ] `test_add_change_two_changes_ordered_1_2`
- [ ] `test_add_change_validates_draft_only`
- [ ] `test_add_change_add_requires_name`
- [ ] `test_add_change_add_requires_content`
- [ ] `test_add_change_drop_requires_rationale`
- [ ] `test_add_change_alter_requires_target_id`
- [ ] `test_add_change_invalid_entity_type`
- [ ] `test_remove_change_renumbers_remaining`
- [ ] `test_remove_change_validates_draft_only`
- [ ] `test_submit_pip_transitions_to_submitted`
- [ ] `test_submit_pip_requires_changes`
- [ ] `test_submit_pip_validates_owner`
- [ ] `test_cancel_pip_draft_deletes`
- [ ] `test_cancel_pip_submitted_rejects`

Write → test → implement each → commit:
`feat(services): add PIPService create_pip, add/edit/remove_change, submit_pip, cancel_pip`

---

### Step 2 — Views

**File**: `methodology/pip_views.py` (extend)

```python
@login_required
def pip_create(request):
    """
    GET: render empty PIP creation form.
    POST: create PIP header (title + summary + playbook); redirect to pip_detail.

    Pre-fills playbook from ?playbook_id= (locked) or shows Released dropdown.
    Template: templates/methodology/pips/create.html
    Context:
        released_playbooks — QuerySet
        locked_playbook    — Playbook or None (when pre-filled from detail page)
        entity_types       — choices list
        change_types       — choices list
        workflows          — Workflow QuerySet for selected playbook (for Add Change form)
        activities         — Activity QuerySet for selected playbook
    """

@login_required
def pip_change_add(request, pk):
    """
    POST only, HTMX. Add a Change to an existing Draft PIP.
    Returns partial: updated change table body.
    """

@login_required
def pip_change_delete(request, pk, chpk):
    """
    POST only, HTMX. Remove a Change from a Draft PIP.
    Returns partial: updated change table body.
    """

@login_required
def pip_edit(request, pk):
    """
    Edit header of a Draft PIP (title, summary).
    Same template as create but pre-populated.
    """

@login_required
def pip_submit(request, pk):
    """POST only. Submit a Draft PIP → Submitted, trigger Galdr."""

@login_required
def pip_cancel(request, pk):
    """POST only. Cancel/delete a Draft or Submitted PIP."""
```

**URL routes** (`mimir/urls.py`):
```python
path("pips/create/",                            pip_views.pip_create,       name="pip_create"),
path("pips/<int:pk>/edit/",                     pip_views.pip_edit,         name="pip_edit"),
path("pips/<int:pk>/submit/",                   pip_views.pip_submit,       name="pip_submit"),
path("pips/<int:pk>/cancel/",                   pip_views.pip_cancel,       name="pip_cancel"),
path("pips/<int:pk>/changes/add/",              pip_views.pip_change_add,   name="pip_change_add"),
path("pips/<int:pk>/changes/<int:chpk>/delete/",pip_views.pip_change_delete,name="pip_change_delete"),
```

Also add `[Submit PIP]` button to Released playbook detail template (`templates/methodology/playbooks/detail.html`):
```html
{% if playbook.status == 'released' %}
<a href="{% url 'pip_create' %}?playbook_id={{ playbook.pk }}"
   class="btn btn-outline-primary btn-sm" data-testid="submit-pip-btn">
  <i class="fa-solid fa-file-pen me-1"></i> Submit PIP
</a>
{% endif %}
```

---

## BPE-03: Frontend Implementation

### Step 1 — Main create template (rewire from mockup)

**Source**: `templates/mockups/pips/create.html`  
**Destination**: `templates/methodology/pips/create.html`

**Rewiring map:**

| Mockup | Real |
|---|---|
| `{% url 'mockup_pip_list' %}` | `{% url 'pip_list' %}` |
| `{% url 'mockup_pip_detail' pip_id=pip.id %}` | `{% url 'pip_detail' pk=pip.pk %}` |
| Hardcoded playbook options | `{% for pb in released_playbooks %}` |
| Hardcoded workflow options | `{% for wf in workflows %}` |
| Hardcoded activity options | `{% for act in activities %}` |
| Remove mockup nav bar | — |

Wire HTMX on the Add Change form:
```html
<form id="add-change-form"
      hx-post="{% url 'pip_change_add' pip.pk %}"
      hx-target="#change-table-body"
      hx-swap="innerHTML">
```

Wire change delete buttons:
```html
<button hx-post="{% url 'pip_change_delete' pip.pk change.pk %}"
        hx-target="#change-table-body"
        hx-swap="innerHTML"
        data-testid="remove-change-{{ change.order }}">
```

Wire Submit for Review (JS: disable until title + ≥1 change):
```javascript
// Enable/disable [Submit for Review] based on title + change count
function updateSubmitButton() {
    const hasTitle   = document.getElementById('id_title').value.trim().length > 0;
    const hasChanges = document.querySelectorAll('#change-table-body tr').length > 0;
    document.getElementById('submit-pip-btn').disabled = !(hasTitle && hasChanges);
}
document.getElementById('id_title').addEventListener('input', updateSubmitButton);
document.body.addEventListener('htmx:afterSwap', updateSubmitButton);
```

### Step 2 — HTMX partial: change table body

**File**: `templates/methodology/pips/_change_table_rows.html`

Returns only `<tbody>` content with all current changes. Used as `hx-target` for add/remove operations.

### Step 3 — Dynamic field visibility (JS)

Type-specific fields (shown/hidden based on selected change_type):
- ADD: show Name, Parent Workflow, Position, Content
- ALTER: show Target (dropdown), Content
- DROP: show Target (dropdown), Rationale (content label changes)

```javascript
document.getElementById('id_change_type').addEventListener('change', function() {
    const type = this.value;
    document.getElementById('add-fields').style.display   = type === 'ADD'   ? '' : 'none';
    document.getElementById('alter-fields').style.display = type === 'ALTER' ? '' : 'none';
    document.getElementById('drop-fields').style.display  = type === 'DROP'  ? '' : 'none';
});
```

### Step 4 — Cancel confirmation modal

Use Bootstrap modal (already in base.html):
```html
<div class="modal fade" id="cancelConfirmModal" tabindex="-1" data-testid="cancel-confirm-modal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-body">Cancel this PIP?</div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Keep editing</button>
        <a href="{% url 'pip_list' %}" class="btn btn-danger" data-testid="confirm-cancel-btn">
          Cancel PIP
        </a>
      </div>
    </div>
  </div>
</div>
```

### Step 5 — Browser validation

- [ ] Open `/pips/create/` — form renders
- [ ] [Submit for Review] disabled until title + 1 change filled
- [ ] Add Change (ADD type) — row appears in table without page reload
- [ ] Remove Change — row disappears without page reload
- [ ] Switching change type shows/hides correct fields
- [ ] Cancel → modal appears → confirm → redirected to `/pips/`
- [ ] Save as Draft → redirected to `/pips/<id>/`
- [ ] Open from playbook detail (`/playbooks/1/`) → Target Playbook pre-filled + locked
- [ ] Console has no JS errors

Commit: `feat(templates): pip create template with HTMX change management`

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_pip_create_view.py`

- [ ] `test_create_01_from_released_playbook_prefills_target` (CREATE-01)
- [ ] `test_create_02_from_pip_list_empty_target` (CREATE-02)
- [ ] `test_create_03_draft_playbook_excluded_from_dropdown` (CREATE-03)
- [ ] `test_create_05_title_required_on_save_draft` (CREATE-05)
- [ ] `test_create_06_add_add_change_appended` (CREATE-06)
- [ ] `test_create_07_add_change_insert_after_sibling` (CREATE-07)
- [ ] `test_create_08_add_workflow_change` (CREATE-08)
- [ ] `test_create_09_add_alter_change_activity` (CREATE-09)
- [ ] `test_create_11_add_drop_change` (CREATE-11)
- [ ] `test_create_12_multiple_changes_ordered` (CREATE-12)
- [ ] `test_create_13_remove_change_renumbers` (CREATE-13)
- [ ] `test_create_14_add_change_requires_name` (CREATE-14)
- [ ] `test_create_15_drop_change_requires_rationale` (CREATE-15)
- [ ] `test_create_17_save_as_draft_status_draft` (CREATE-17)
- [ ] `test_create_18_submit_for_review_status_submitted` (CREATE-18)
- [ ] `test_create_19_cancel_no_pip_created` (CREATE-19)

Run: `pytest tests/integration/test_pip_create_view.py -v`

Commit: `test(pips): acceptance tests for pip create — 16 scenarios`

---

## BPE-05: Journey Certification Test

**File**: `tests/e2e/test_pip_journey_create.py`

```
Journey: Author creates and submits a PIP with two Changes
  1. Log in as maria
  2. Navigate to Released playbook detail
  3. Click [Submit PIP] → redirected to /pips/create/ with playbook pre-filled
  4. Enter title "Add Accessibility Audit"
  5. Verify [Submit for Review] still disabled (no changes)
  6. Click [+ Add Change], select ADD / Activity, fill name + content, click [Add Change]
  7. Verify change row appears in table
  8. Verify [Submit for Review] now enabled
  9. Click [Submit for Review]
  10. Verify redirected to /pips/<id>/ with status "Submitted" or "Processing (Galdr)"
```

Commit: `test(e2e): pip create journey certification`

---

## BPE-06: Definition of Done

- [ ] All 16 acceptance tests pass
- [ ] E2E journey test passes
- [ ] PIPService: `create_pip`, `add_change`, `edit_change`, `remove_change`, `submit_pip`, `cancel_pip` all implemented
- [ ] Add Change HTMX updates table without page reload
- [ ] Remove Change HTMX updates table without page reload
- [ ] Cancel shows confirmation modal
- [ ] Save as Draft → Draft PIP, redirect to detail
- [ ] Submit for Review → Submitted PIP, redirect to detail
- [ ] Entry from Released playbook pre-fills + locks target
- [ ] Entry from PIPs list shows Released dropdown only
- [ ] Validation errors shown inline (title required, name required for ADD, etc.)
- [ ] [Submit for Review] disabled until title + ≥1 change
- [ ] INFO logging on all service methods
- [ ] All `data-testid` attributes present

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Visual spot-check: create PIP end-to-end in browser
- [ ] Update `pips-create.feature` — add ✅ per passing scenario
- [ ] Final commit: `feat(pips): PIP create view complete — HTMX changes, save/submit (FOB-PIP-CREATE-01..19)`
- [ ] Close GitHub issue, `status-done`
- [ ] PR → `main`

---

## Files Created / Modified

**New (5):**
1. `templates/methodology/pips/create.html`
2. `templates/methodology/pips/_change_table_rows.html`
3. `tests/unit/test_pip_service_create.py`
4. `tests/integration/test_pip_create_view.py`
5. `tests/e2e/test_pip_journey_create.py`

**Modified (3):**
1. `methodology/services/pip_service.py`
2. `methodology/pip_views.py`
3. `mimir/urls.py`
4. `templates/methodology/playbooks/detail.html` (add Submit PIP button)

## Mockup Reference

`templates/mockups/pips/create.html` — rewire to `templates/methodology/pips/create.html`. Keep mockup routes alive.
