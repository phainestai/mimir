# PIP Sub-Story 5: Administrator Reviews and Applies PIP

**Feature file**: `docs/features/act-9-pips/pips-admin-review.feature`  
**Scenarios**: FOB-PIP-ADMIN-01 … 17  
**Complexity**: hard — per-Change apply logic, version bump, atomic mutations, email  
**Branch**: `feature/act-9-pips/admin-review`  
**Depends on**: PIP-GALDR-ENGINE (Galdr output in Changes), PIP-VIEW (email service)  
**Blocks**: nothing — terminal sub-story for UI

---

## Overview

Implements the Administrator's PIP review interface (Django Admin changelist + custom FOB review view), per-Change accept/reject decisions, atomic application of accepted changes to the playbook, version bump, and submitter email.

**Scenarios covered:**
- ADMIN-01/02/03 — Django Admin sidebar, changelist, status filter
- ADMIN-04/05/06 — Open PIP, Change inline with Galdr output, expand reasoning
- ADMIN-07/08/09 — Finalize: all accept, partial, all reject
- ADMIN-10 — Finalize disabled until all decisions set
- ADMIN-11/12/13/14 — Apply changes: ADD insert, ADD append, ALTER, DROP
- ADMIN-15 — Version bump rule (one major increment per finalise)
- ADMIN-16/17 — Permission check, read-only after decision

---

## BPE-02: Backend Implementation

### Step 1 — `PIPAdminService`

**File**: `methodology/services/pip_admin_service.py`

```python
class PIPAdminService:
    """
    Orchestrates the final PIP review: validate decisions, apply accepted changes
    atomically, bump version, send notification.

    Usage:
        PIPAdminService().finalize_pip(pip, actor=mike)
    """

    def finalize_pip(self, pip, actor) -> "ProcessImprovementProposal":
        """
        Validate, apply, bump version, send email.

        :param pip: ProcessImprovementProposal — must be in 'reviewed' status
        :param actor: User — must be is_staff
        :returns: updated PIP with status 'accepted' or 'rejected'
        :raises PermissionError: if actor.is_staff is False
        :raises ValidationError: if pip.status != 'reviewed'
        :raises ValidationError: if any Change has no admin_decision set
        :example: PIPAdminService().finalize_pip(pip42, mike)
        """
        self._validate_finalize(pip, actor)
        accepted = self._get_accepted_changes(pip)
        rejected = self._get_rejected_changes(pip)
        if accepted:
            self._apply_accepted_changes(pip, accepted, actor)
        self._set_final_status(pip, accepted, rejected)
        send_decision_email(pip)
        return pip

    def _validate_finalize(self, pip, actor) -> None:
        """Check: actor.is_staff, pip.status=='reviewed', all Changes have admin_decision."""

    def _get_accepted_changes(self, pip) -> list:
        """Return Changes where admin_decision=='ACCEPT', ordered by order."""

    def _get_rejected_changes(self, pip) -> list:
        """Return Changes where admin_decision=='REJECT'."""

    @transaction.atomic
    def _apply_accepted_changes(self, pip, accepted_changes, actor) -> None:
        """
        Apply each accepted Change to the playbook in order.
        Wraps all mutations in a single DB transaction.
        Calls _apply_single_change for each.
        After all mutations: bump version via existing apply service.
        """

    def _apply_single_change(self, change, pip) -> None:
        """
        Route to the correct apply method based on change_type + entity_type.

        ADD Activity  → _add_activity(change, pip)
        ADD Workflow  → _add_workflow(change, pip)
        ADD Skill     → _add_skill(change, pip)
        ADD Agent     → _add_agent(change, pip)
        ALTER Activity → _alter_activity(change)
        ALTER Workflow → _alter_workflow(change)
        DROP Activity  → _drop_activity(change)
        DROP Workflow  → _drop_workflow(change)
        """

    def _add_activity(self, change, pip) -> None:
        """
        Create new Activity in the specified workflow.
        If insert_after_id set: insert after that activity (shift others).
        If insert_after_id is None: append at end of workflow.
        Logs: new activity.id, workflow.id, position.
        """

    def _alter_activity(self, change) -> None:
        """Update Activity.guidance to change.content. Update last_modified."""

    def _drop_activity(self, change) -> None:
        """Delete Activity. Remaining activities in workflow retain their order."""

    def _add_workflow(self, change, pip) -> None:
        """Create new Workflow in pip.playbook, appended at end."""

    def _alter_workflow(self, change) -> None:
        """Update Workflow.description to change.content."""

    def _drop_workflow(self, change) -> None:
        """Delete Workflow and all its Activities."""

    def _add_skill(self, change, pip) -> None:
        """Create new Skill in pip.playbook."""

    def _add_agent(self, change, pip) -> None:
        """Create new Agent in pip.playbook."""

    def _set_final_status(self, pip, accepted, rejected) -> None:
        """
        Set PIP status:
          any accepted → 'accepted'
          all rejected → 'rejected'
        Sets decided_at=now(), status_changed_at=now().
        """

    def _bump_version(self, pip, accepted_changes) -> str:
        """
        One major version increment per finalise (spec ADMIN-15):
          v1.0 → v2.0, v2.1 → v3.0, regardless of change count.
        Uses existing apply_approved_pip_aggregate with major flag.
        Returns new version string.
        """
```

**Unit tests** (`tests/unit/test_pip_admin_service.py`):
- [ ] `test_finalize_validates_reviewed_status`
- [ ] `test_finalize_validates_staff_actor`
- [ ] `test_finalize_validates_all_decisions_set`
- [ ] `test_finalize_all_accept_status_accepted`
- [ ] `test_finalize_all_reject_status_rejected`
- [ ] `test_finalize_partial_status_accepted`
- [ ] `test_add_activity_insert_after_shifts_order`
- [ ] `test_add_activity_append_at_end`
- [ ] `test_alter_activity_replaces_guidance`
- [ ] `test_drop_activity_deleted`
- [ ] `test_version_bump_major_increment`
- [ ] `test_apply_is_atomic_rolls_back_on_error`

Commit: `feat(services): add PIPAdminService.finalize_pip with atomic apply and version bump`

---

### Step 2 — Django Admin customization

**File**: `methodology/admin.py` (extend existing PIPChangeInline)

Django Admin is the primary interface for Scenario ADMIN-01..06 and ADMIN-16/17.

Extend `ProcessImprovementProposalAdmin`:
```python
@admin.register(ProcessImprovementProposal)
class ProcessImprovementProposalAdmin(admin.ModelAdmin):
    list_display  = ["__str__", "playbook", "created_by", "status", "submitted_at"]
    list_filter   = ["status"]  # Default to 'Reviewed' via get_queryset override
    search_fields = ["title"]
    inlines       = [PIPChangeInline]

    def get_queryset(self, request):
        """Default to showing Reviewed PIPs (status filter)."""
        qs = super().get_queryset(request)
        if not request.GET.get("status__exact"):
            return qs.filter(status="reviewed")
        return qs

    def has_change_permission(self, request, obj=None):
        """Read-only if PIP already decided (Accepted/Rejected)."""
        if obj and obj.status in ("accepted", "rejected"):
            return False
        return super().has_change_permission(request, obj)
```

Extend `PIPChangeInline` for ADMIN-05:
- Make `galdr_recommendation` display as coloured badge (via `readonly_fields` + custom method)
- Editable `admin_decision` (dropdown) and `admin_note`
- Read-only if `pip.status in (accepted, rejected)`

Commit: `feat(admin): extend PIP admin — default reviewed filter, read-only after decision`

---

### Step 3 — Custom FOB Admin Review View

The feature spec says "Django Admin at /admin/methodology/pip/42/change/" for the review form. The mockup at `/mockups/pips/<id>/admin-review/` matches this flow as a custom FOB page. Implement as a **staff-only FOB view** (not overriding Django Admin change_view) for better testability and HTMX support.

**File**: `methodology/pip_views.py` (extend)

```python
@login_required
def pip_admin_review(request, pk):
    """
    Staff-only PIP review page: shows Galdr output + editable admin decisions per Change.
    GET: render review form.
    POST: save per-Change decisions, or finalize if all set.

    Template: templates/methodology/pips/admin_review.html
    Context:
        pip        — PIP with changes prefetched
        can_finalize — bool: all Changes have admin_decision set
        is_decided — bool: pip.status in (accepted, rejected)
    :raises PermissionDenied: if request.user.is_staff is False
    """
    # Log: user.id, pip.id, pip.status
```

**URL**: `path("pips/<int:pk>/admin-review/", pip_views.pip_admin_review, name="pip_admin_review")`

---

## BPE-03: Frontend Implementation

### Step 1 — Admin review template (rewire from mockup)

**Source**: `templates/mockups/pips/admin_review.html`  
**Destination**: `templates/methodology/pips/admin_review.html`

**Rewiring map:**

| Mockup | Real |
|---|---|
| `{% url 'mockup_pip_detail' pip_id=pip.id %}` | `{% url 'pip_detail' pk=pip.pk %}` |
| `{% url 'mockup_pip_admin_review' pip_id=pip.id %}` | `{% url 'pip_admin_review' pk=pip.pk %}` |
| Hardcoded Galdr reasoning | `{{ change.galdr_reasoning }}` |
| Hardcoded admin_decision dropdown | `<select name="decision_{{ change.order }}">` |
| `disabled` on Finalize button | JS enables when all decisions set |
| Remove mockup nav bar | — |

### Step 2 — JS: enable Finalize when all decisions set

```javascript
function updateFinalizeButton() {
    const selects = document.querySelectorAll('[data-decision-select]');
    const allSet  = Array.from(selects).every(s => s.value !== '');
    document.getElementById('finalize-btn').disabled = !allSet;
}
document.querySelectorAll('[data-decision-select]').forEach(s =>
    s.addEventListener('change', updateFinalizeButton)
);
updateFinalizeButton(); // run on load
```

### Step 3 — Confirmation modal for Finalize

```html
<div class="modal fade" id="finalizeConfirmModal" data-testid="finalize-confirm-modal">
  <div class="modal-body">
    You are accepting {{ accepted_count }} of {{ total_count }} changes.
    {% if accepted_count > 0 %}{{ pip.playbook.name }} will be updated to v{{ new_version }}.{% endif %}
    This action cannot be undone.
  </div>
  <div class="modal-footer">
    <button class="btn btn-secondary" data-bs-dismiss="modal">Go back</button>
    <form method="post" action="{% url 'pip_admin_review' pk=pip.pk %}">
      {% csrf_token %}
      <input type="hidden" name="action" value="finalize">
      {% for change in pip.changes.all %}
      <input type="hidden" name="decision_{{ change.order }}" value="{{ change.admin_decision }}">
      <input type="hidden" name="note_{{ change.order }}" value="{{ change.admin_note }}">
      {% endfor %}
      <button type="submit" class="btn btn-primary" data-testid="confirm-finalize-btn">Confirm</button>
    </form>
  </div>
</div>
```

### Step 4 — Read-only banner when already decided

```html
{% if is_decided %}
<div class="alert alert-warning" data-testid="already-decided-banner">
  This PIP has already been decided and cannot be modified.
</div>
{% endif %}
```

### Step 5 — Browser validation

- [ ] `/pips/<id>/admin-review/` loads for staff user, 403 for regular user
- [ ] Galdr ACCEPT shows green badge, REJECT shows red badge
- [ ] Admin decision dropdowns editable for Reviewed PIP
- [ ] Finalize button disabled until all dropdowns set
- [ ] Clicking Finalize → confirmation modal with correct counts
- [ ] After Finalize: PIP status changes, redirect to detail with banner
- [ ] Accepted changes reflected in playbook (spot-check an Activity)
- [ ] Already-decided PIP shows read-only banner, no Finalize button

Commit: `feat(templates): pip admin review template with JS decision tracking`

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_pip_admin_review_view.py`

- [ ] `test_admin_01_pip_in_django_admin_sidebar` (ADMIN-01) — check `/admin/` renders link
- [ ] `test_admin_02_changelist_shows_reviewed_by_default` (ADMIN-02)
- [ ] `test_admin_04_open_pip_shows_review_form` (ADMIN-04)
- [ ] `test_admin_05_change_inline_shows_galdr_output` (ADMIN-05)
- [ ] `test_admin_07_finalize_all_accept_bumps_version` (ADMIN-07)
- [ ] `test_admin_08_finalize_partial_applies_only_accepted` (ADMIN-08)
- [ ] `test_admin_09_finalize_all_reject_no_change` (ADMIN-09)
- [ ] `test_admin_10_finalize_disabled_until_all_set` (ADMIN-10)
- [ ] `test_admin_11_add_activity_insert_after` (ADMIN-11)
- [ ] `test_admin_12_add_activity_append` (ADMIN-12)
- [ ] `test_admin_13_alter_activity_updates_guidance` (ADMIN-13)
- [ ] `test_admin_14_drop_activity_deleted` (ADMIN-14)
- [ ] `test_admin_15_version_bump_major` (ADMIN-15)
- [ ] `test_admin_16_regular_user_gets_403` (ADMIN-16)
- [ ] `test_admin_17_already_decided_readonly` (ADMIN-17)

Run: `pytest tests/integration/test_pip_admin_review_view.py -v`

Commit: `test(pips): acceptance tests for admin review — 15 scenarios`

---

## BPE-05: Journey Certification Test

**File**: `tests/e2e/test_pip_journey_admin.py`

```
Journey: Admin reviews Galdr output, accepts partial, playbook updated
  1. Log in as mike (staff)
  2. Navigate to /pips/<id>/admin-review/ for a Reviewed PIP
  3. Verify Change cards show Galdr ACCEPT/REJECT badges
  4. Set Change #1 decision to ACCEPT
  5. Verify Finalize button still disabled (Change #2 unset)
  6. Set Change #2 decision to REJECT
  7. Verify Finalize button now enabled
  8. Click Finalize → confirm modal appears
  9. Click Confirm
  10. Verify redirected to /pips/<id>/ with "Partially accepted" banner
  11. Navigate to playbook — verify new Activity exists (Change #1 applied)
  12. Verify playbook version bumped to v2.0
```

Commit: `test(e2e): pip admin review journey certification`

---

## BPE-06: Definition of Done

- [ ] All 15 acceptance tests pass
- [ ] E2E journey test passes
- [ ] `PIPAdminService.finalize_pip` validates staff + reviewed status + all decisions set
- [ ] Accepted changes applied atomically (one DB transaction)
- [ ] ADD Activity: correct position (insert_after or append)
- [ ] ALTER Activity: guidance replaced
- [ ] DROP Activity: entity deleted
- [ ] Version bumped by exactly one major increment (v1.0 → v2.0)
- [ ] `PlaybookVersion` record created linking to PIP
- [ ] Email sent via `PIPNotificationService`
- [ ] Regular user gets 403 on admin review URL
- [ ] Already-decided PIP shows read-only banner
- [ ] Django Admin changelist defaults to Reviewed status
- [ ] Finalize button disabled until all admin_decision dropdowns set

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Submit + review + finalize a PIP end-to-end in browser
- [ ] Update `pips-admin-review.feature` — add ✅ per passing scenario
- [ ] Final commit: `feat(pips): admin review view complete — decisions, apply, version bump, email (FOB-PIP-ADMIN-01..17)`
- [ ] Close GitHub issue, `status-done`
- [ ] PR → `main`

---

## Files Created / Modified

**New (5):**
1. `methodology/services/pip_admin_service.py`
2. `templates/methodology/pips/admin_review.html`
3. `tests/unit/test_pip_admin_service.py`
4. `tests/integration/test_pip_admin_review_view.py`
5. `tests/e2e/test_pip_journey_admin.py`

**Modified (3):**
1. `methodology/admin.py`
2. `methodology/pip_views.py`
3. `mimir/urls.py`

## Mockup Reference

`templates/mockups/pips/admin_review.html` — rewire to `templates/methodology/pips/admin_review.html`. Keep mockup routes alive.
