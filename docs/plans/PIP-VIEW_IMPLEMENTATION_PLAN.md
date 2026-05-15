# PIP Sub-Story 3: View PIP Detail with Galdr Recommendations

**Feature file**: `docs/features/act-9-pips/pips-view.feature`  
**Scenarios**: FOB-PIP-DETAIL-01 … 19  
**Complexity**: medium — detail view, status banners, conditional actions, email  
**Branch**: `feature/act-9-pips/view`  
**Depends on**: PIP-LIST (model), PIP-CREATE (submit/cancel service methods), PIP-GALDR-ENGINE (Galdr output in Changes)  
**Blocks**: nothing directly (email tested here; admin review in PIP-ADMIN)

---

## Overview

Implements the PIP detail page: metadata header, Change cards with Galdr verdict badges (after review), status-specific banners, conditional action buttons per status, and submitter email notification content. This view is read-heavy — it mirrors what was in the Create flow but shows the state after processing.

**Scenarios covered:**
- DETAIL-01/02/03 — Load, header metadata, summary section
- DETAIL-04/05/06 — Change cards with Galdr output, banners while processing/draft
- DETAIL-07 — Expand Change content
- DETAIL-08/09/10/11 — Status banners (Reviewed, Accepted, Partial, Rejected)
- DETAIL-12/13/14 — Action buttons by status (Draft, Submitted, Reviewed+)
- DETAIL-15/16 — Cancel draft (delete), submit from detail
- DETAIL-17/18/19 — Email notification content (all accept, partial, all reject)

---

## BPE-02: Backend Implementation

### Step 1 — `PIPService.get_pip`

**File**: `methodology/services/pip_service.py` (extend)

```python
def get_pip(pip_id: int, user) -> "ProcessImprovementProposal":
    """
    Fetch a PIP with all Changes prefetched. Enforces owner-or-staff access.

    :param pip_id: int. Example: 42
    :param user: User instance — must be pip.created_by or is_staff
    :returns: ProcessImprovementProposal with changes prefetched
    :raises ObjectDoesNotExist: if pip not found
    :raises PermissionError: if user is not owner and not staff
    :example: pip = get_pip(42, maria)  # pip.changes.all() is preloaded
    """
    # Log: pip_id, user.id, access granted/denied
```

**Unit tests** (`tests/unit/test_pip_service_view.py`):
- [ ] `test_get_pip_returns_pip_with_changes`
- [ ] `test_get_pip_owner_can_access`
- [ ] `test_get_pip_staff_can_access_any`
- [ ] `test_get_pip_other_user_raises_permission_error`
- [ ] `test_get_pip_not_found_raises`

Commit: `feat(services): add PIPService.get_pip with owner/staff access guard`

---

### Step 2 — Email notification service

**File**: `methodology/services/pip_notification_service.py`

```python
def send_decision_email(pip) -> None:
    """
    Send decision email to pip.created_by.email after admin finalises.

    Subject examples:
      - 'Your PIP "Add Accessibility Audit" — Accepted ✓'
      - 'Your PIP "Add Accessibility Audit" — Partially Accepted'
      - 'Your PIP "Drop Legacy IE Support" — Rejected ✗'

    :param pip: ProcessImprovementProposal with changes + admin_decision populated
    """
    # Log: pip.id, recipient email, verdict
    # Determine verdict: all ACCEPT → Accepted, all REJECT → Rejected, mixed → Partially Accepted
    # Build per-change summary lines
    # Use Django send_mail with DEFAULT_FROM_EMAIL
```

**Email template**: `templates/methodology/pips/email_decision.txt`

```
Hi {{ pip.created_by.get_full_name }},

Your PIP "{{ pip.title }}" has been reviewed.

{% for change in changes %}
Change {{ forloop.counter }}: {{ change.change_type }} {{ change.entity_type }} "{{ change.name|default:change.target_name }}"
  Decision: {{ change.admin_decision }}
  Reasoning: {{ change.galdr_reasoning }}

{% endfor %}

Overall: {{ verdict }}. {% if version_bump %}{{ pip.playbook.name }} is now v{{ new_version }}.{% endif %}
```

**Unit tests** (`tests/unit/test_pip_notification_service.py`):
- [ ] `test_email_subject_all_accepted`
- [ ] `test_email_subject_partially_accepted`
- [ ] `test_email_subject_all_rejected`
- [ ] `test_email_body_contains_per_change_lines`
- [ ] `test_email_sent_to_submitter`

Commit: `feat(services): add PIPNotificationService.send_decision_email`

---

### Step 3 — `pip_detail` View

**File**: `methodology/pip_views.py` (extend)

```python
@login_required
def pip_detail(request, pk):
    """
    PIP detail page. Shows metadata, Change cards with Galdr output, status banner,
    and conditional action buttons.

    Template: templates/methodology/pips/detail.html
    Context:
        pip         — ProcessImprovementProposal (changes prefetched)
        can_edit    — bool (status==draft and user==owner)
        can_submit  — bool (status==draft and has changes)
        can_cancel  — bool (status in draft/submitted/processing_galdr)
        status_banner — str: the exact banner text from feature spec
        admin_review_url — str or None (staff only, status==reviewed)
    """
    # Log: pip_id, user.id, pip.status
```

Status banner map (exact wording per pips-view.feature):
```python
BANNER = {
    "draft":            "Draft — not yet submitted for review.",
    "submitted":        "Submitted — awaiting Galdr processing.",
    "processing_galdr": "Galdr is reviewing your changes — check back shortly.",
    "reviewed":         "Reviewed — awaiting Administrator decision.",
    # accepted / rejected banners are dynamic — built in view based on change decisions
}
```

For accepted/rejected, build dynamically:
- All accepted → `"Accepted — all changes applied. {playbook.name} is now v{new_version}."`
- Partial → `"Partially accepted — {n} of {total} changes applied. {playbook.name} is now v{new_version}."`
- All rejected → `"Rejected — no changes were applied."`

URL: already registered in PIP-CREATE plan (`pips/<int:pk>/`).

---

## BPE-03: Frontend Implementation

### Step 1 — Detail template (rewire from mockup)

**Source**: `templates/mockups/pips/detail.html`  
**Destination**: `templates/methodology/pips/detail.html`

**Rewiring map:**

| Mockup | Real |
|---|---|
| `{% url 'mockup_pip_list' %}` | `{% url 'pip_list' %}` |
| `{% url 'mockup_pip_create' %}` | `{% url 'pip_edit' pk=pip.pk %}` |
| `{% url 'mockup_pip_admin_review' pip_id=pip.id %}` | `{% url 'pip_admin_review' pk=pip.pk %}` |
| Hardcoded status banner text | `{{ status_banner }}` |
| Hardcoded Galdr verdict | `{{ change.galdr_recommendation }}` / `{{ change.galdr_reasoning }}` |
| Hardcoded action visibility | `{% if can_submit %}` / `{% if can_edit %}` / `{% if can_cancel %}` |
| `pip.status_css` | `pip.get_status_badge_class` |
| Remove mockup nav bar | — |

### Step 2 — Galdr verdict badges

For each Change card:
```html
{% if change.galdr_recommendation %}
<span class="badge {% if change.galdr_recommendation == 'ACCEPT' %}bg-success
                   {% elif change.galdr_recommendation == 'REJECT' %}bg-danger
                   {% else %}bg-warning text-dark{% endif %}"
      data-testid="galdr-verdict-{{ change.order }}">
  {{ change.galdr_recommendation }}
</span>
{% endif %}
```

### Step 3 — Admin decision badges (shown after finalise)

```html
{% if change.admin_decision %}
<span class="badge {% if change.admin_decision == 'ACCEPT' %}bg-success{% else %}bg-danger{% endif %}"
      data-testid="admin-verdict-{{ change.order }}">
  {% if change.admin_decision == 'ACCEPT' %}ACCEPTED{% else %}REJECTED{% endif %}
</span>
{% endif %}
```

### Step 4 — Cancel confirmation modal

```html
<div class="modal fade" id="cancelPipModal" data-testid="cancel-pip-modal">
  <div class="modal-dialog">
    <div class="modal-body">Cancel PIP-{{ pip.pk }} permanently?</div>
    <div class="modal-footer">
      <button class="btn btn-secondary" data-bs-dismiss="modal">Keep PIP</button>
      <form method="post" action="{% url 'pip_cancel' pk=pip.pk %}">
        {% csrf_token %}
        <button type="submit" class="btn btn-danger" data-testid="confirm-cancel-pip-btn">Confirm</button>
      </form>
    </div>
  </div>
</div>
```

### Step 5 — Browser validation

- [ ] `/pips/42/` loads, shows metadata header
- [ ] Status banner shows correct wording per status
- [ ] Draft PIP shows [Edit PIP], [Cancel], [Submit for Review]
- [ ] Submitted PIP shows [Cancel PIP] only
- [ ] Reviewed PIP shows no action buttons
- [ ] Accepted PIP shows banner with version number
- [ ] Galdr ACCEPT badge is green, REJECT is red
- [ ] Admin ACCEPTED badge is green, REJECTED is red
- [ ] Change expand/collapse shows full content
- [ ] Cancel modal appears on click, Confirm deletes and redirects
- [ ] No JS console errors

Commit: `feat(templates): pip detail template with status banners, Galdr/admin verdicts`

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_pip_detail_view.py`

- [ ] `test_detail_01_loads_from_list` (DETAIL-01)
- [ ] `test_detail_02_header_shows_all_metadata` (DETAIL-02)
- [ ] `test_detail_03_summary_section` (DETAIL-03)
- [ ] `test_detail_04_change_cards_with_galdr_output` (DETAIL-04)
- [ ] `test_detail_05_processing_banner_no_verdicts` (DETAIL-05)
- [ ] `test_detail_06_draft_banner_no_verdicts` (DETAIL-06)
- [ ] `test_detail_08_reviewed_banner` (DETAIL-08)
- [ ] `test_detail_09_accepted_banner_all_accepted` (DETAIL-09)
- [ ] `test_detail_10_partial_accepted_banner` (DETAIL-10)
- [ ] `test_detail_11_rejected_banner` (DETAIL-11)
- [ ] `test_detail_12_draft_shows_edit_cancel_submit` (DETAIL-12)
- [ ] `test_detail_13_submitted_shows_cancel_only` (DETAIL-13)
- [ ] `test_detail_14_reviewed_no_action_buttons` (DETAIL-14)
- [ ] `test_detail_15_cancel_draft_deletes_pip` (DETAIL-15)
- [ ] `test_detail_16_submit_from_detail_transitions_status` (DETAIL-16)
- [ ] `test_detail_17_email_all_accepted` (DETAIL-17) — check Django `mail.outbox`
- [ ] `test_detail_18_email_partially_accepted` (DETAIL-18)
- [ ] `test_detail_19_email_all_rejected` (DETAIL-19)

Run: `pytest tests/integration/test_pip_detail_view.py -v`

Commit: `test(pips): acceptance tests for pip detail — 17 scenarios`

---

## BPE-05: Journey Certification Test

**File**: `tests/e2e/test_pip_journey_view.py`

```
Journey: Author submits PIP → Galdr reviews → Author views recommendations
  1. Log in as maria
  2. Navigate to /pips/30/ (Draft with 3 changes)
  3. Verify [Submit for Review] button visible
  4. Click [Submit for Review]
  5. Verify status banner "Submitted — awaiting Galdr processing."
  6. (Use StubGaldrClient or wait for processing)
  7. Refresh page — verify status banner "Reviewed — awaiting Administrator decision."
  8. Verify Change cards show ACCEPT/REJECT verdict badges
  9. Verify no action buttons visible (read-only state)
```

Commit: `test(e2e): pip view journey certification — submit → galdr → read-only`

---

## BPE-06: Definition of Done

- [ ] All 17 acceptance tests pass
- [ ] E2E journey test passes
- [ ] `get_pip` enforces owner-or-staff access
- [ ] Status banners match feature spec exact wording
- [ ] Action buttons conditional per status (Draft=3 buttons, Submitted=1, Reviewed+=0)
- [ ] Galdr verdict badges: green=ACCEPT, red=REJECT, yellow=NEEDS_CLARIFICATION
- [ ] Admin decision badges shown after finalise
- [ ] Cancel draft deletes PIP, redirect to list
- [ ] Submit from detail triggers status transition
- [ ] Email sent with correct subject and per-change body
- [ ] `django.test.mail.outbox` tested in acceptance tests
- [ ] INFO logging on all service and view methods

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Visual spot-check: open PIP in various statuses
- [ ] Update `pips-view.feature` — add ✅ per passing scenario
- [ ] Final commit: `feat(pips): PIP detail view complete — banners, verdicts, actions, email (FOB-PIP-DETAIL-01..19)`
- [ ] Close GitHub issue, `status-done`
- [ ] PR → `main`

---

## Files Created / Modified

**New (5):**
1. `templates/methodology/pips/detail.html`
2. `templates/methodology/pips/email_decision.txt`
3. `methodology/services/pip_notification_service.py`
4. `tests/unit/test_pip_service_view.py`
5. `tests/unit/test_pip_notification_service.py`
6. `tests/integration/test_pip_detail_view.py`
7. `tests/e2e/test_pip_journey_view.py`

**Modified (2):**
1. `methodology/services/pip_service.py`
2. `methodology/pip_views.py`

## Mockup Reference

`templates/mockups/pips/detail.html` — rewire to `templates/methodology/pips/detail.html`. Keep mockup routes alive.
