# PIP Sub-Story 1: View and Filter PIPs (List Page)

**Feature file**: `docs/features/act-9-pips/pips-list.feature`  
**Scenarios**: FOB-PIP-LIST-01 … 21  
**Complexity**: hard — model foundation + service layer + list view  
**Branch**: `feature/act-9-pips/list`  
**Depends on**: nothing — this is the foundation  
**Blocks**: PIP-CREATE, PIP-VIEW, PIP-GALDR-ENGINE, PIP-ADMIN-REVIEW, PIP-MCP

---

## Overview

This sub-story establishes the **full data model and service foundation** for all PIP work, then delivers the PIP list page. Every subsequent sub-story reuses the models and `PIPService` created here.

**Scenarios covered:**
- LIST-01/02/03 — Nav pill, unread count, reset on visit / MCP call
- LIST-04/05/06/07 — Table, badge colours, blue dot, row actions by status
- LIST-08…14 — Status + playbook filters, combine, clear
- LIST-15/16/17 — Navigate to detail, edit, create
- LIST-18/19 — Empty states
- LIST-20/21 — Admin All PIPs tab visibility

---

## BPE-02: Backend Implementation

### Step 1 — Extend `ProcessImprovementProposal`

**File**: `methodology/models/process_improvement_proposal.py`

**Skeletons first — add, document, then implement each:**

```python
# Replace existing status field with full lifecycle choices
STATUS_DRAFT            = "draft"
STATUS_SUBMITTED        = "submitted"
STATUS_PROCESSING_GALDR = "processing_galdr"
STATUS_REVIEWED         = "reviewed"
STATUS_ACCEPTED         = "accepted"
STATUS_REJECTED         = "rejected"

STATUS_CHOICES = [
    (STATUS_DRAFT,            "Draft"),
    (STATUS_SUBMITTED,        "Submitted"),
    (STATUS_PROCESSING_GALDR, "Processing (Galdr)"),
    (STATUS_REVIEWED,         "Reviewed"),
    (STATUS_ACCEPTED,         "Accepted"),
    (STATUS_REJECTED,         "Rejected"),
]
```

New fields:
```python
summary           = models.TextField(blank=True)
submitted_at      = models.DateTimeField(null=True, blank=True)
reviewed_at       = models.DateTimeField(null=True, blank=True)
decided_at        = models.DateTimeField(null=True, blank=True)
status_changed_at = models.DateTimeField(null=True, blank=True,
    help_text="Updated on every status transition; drives unread count")
last_viewed_at    = models.DateTimeField(null=True, blank=True,
    help_text="When user last opened PIPs list; compared vs status_changed_at")
```

New property and helper:
```python
@property
def status_changed_since_last_view(self) -> bool:
    """
    True if this PIP changed status after the user last viewed the list.
    Returns True if last_viewed_at is None (never viewed).

    :returns: bool. Example: True when status_changed_at='2026-05-15' and last_viewed_at='2026-05-14'
    """

STATUS_BADGE_CLASS = {
    "draft":            "bg-secondary",
    "submitted":        "bg-primary",
    "processing_galdr": "bg-warning text-dark",
    "reviewed":         "pip-status-reviewed",
    "accepted":         "bg-success",
    "rejected":         "bg-danger",
}

def get_status_badge_class(self) -> str:
    """Return Bootstrap badge CSS class for current status."""
```

**Unit tests** (`tests/unit/test_pip_model.py`):
- [ ] `test_pip_default_status_is_draft`
- [ ] `test_status_changed_since_last_view_true` — changed_at after last_viewed_at
- [ ] `test_status_changed_since_last_view_false` — last_viewed_at after changed_at
- [ ] `test_status_changed_never_viewed` — last_viewed_at is None → True
- [ ] `test_get_status_badge_class_each_status` — all 6 map correctly
- [ ] `test_pip_str_format`

Write tests → run (fail) → implement → run (pass) → commit:
`feat(models): extend PIP with lifecycle statuses, unread-count fields and badge helper`

---

### Step 2 — Create `PIPChange` Model

**File**: `methodology/models/pip_change.py`

```python
class PIPChange(models.Model):
    """
    A single typed change within a PIP: ADD a new entity, ALTER existing content, or DROP an entity.

    Example:
        change = PIPChange(pip=pip, order=1, change_type="ADD", entity_type="Activity",
                           name="Accessibility Audit", parent_workflow_id=11,
                           content="Ensure WCAG 2.1 AA using axe-core.")
    """
    CHANGE_TYPE_CHOICES  = [("ADD","ADD"), ("ALTER","ALTER"), ("DROP","DROP")]
    ENTITY_TYPE_CHOICES  = [("Workflow","Workflow"), ("Activity","Activity"),
                             ("Skill","Skill"), ("Agent","Agent"), ("Artifact","Artifact")]
    GALDR_REC_CHOICES    = [("ACCEPT","ACCEPT"), ("REJECT","REJECT"),
                             ("NEEDS_CLARIFICATION","NEEDS_CLARIFICATION")]
    ADMIN_DECISION_CHOICES = [("ACCEPT","ACCEPT"), ("REJECT","REJECT")]

    pip             = models.ForeignKey("ProcessImprovementProposal",
                        related_name="changes", on_delete=models.CASCADE)
    order           = models.PositiveIntegerField(default=0)
    change_type     = models.CharField(max_length=8,  choices=CHANGE_TYPE_CHOICES)
    entity_type     = models.CharField(max_length=16, choices=ENTITY_TYPE_CHOICES)

    # ADD
    name               = models.CharField(max_length=200, blank=True)
    parent_workflow_id = models.IntegerField(null=True, blank=True)
    insert_after_id    = models.IntegerField(null=True, blank=True)

    # ALTER / DROP
    target_id          = models.IntegerField(null=True, blank=True)
    target_name        = models.CharField(max_length=200, blank=True)

    content = models.TextField(blank=True,
        help_text="New/replacement content (ADD/ALTER) or rationale (DROP)")

    # Galdr output
    galdr_recommendation = models.CharField(max_length=24, choices=GALDR_REC_CHOICES, blank=True)
    galdr_reasoning      = models.TextField(blank=True)

    # Admin decision
    admin_decision = models.CharField(max_length=8, choices=ADMIN_DECISION_CHOICES, blank=True)
    admin_note     = models.TextField(blank=True)

    class Meta:
        ordering = ["pip", "order"]

    def __str__(self) -> str:
        return f"Change #{self.order} {self.change_type} {self.entity_type} (PIP-{self.pip_id})"
```

Register in `methodology/models/__init__.py`.

**Unit tests** (`tests/unit/test_pip_change_model.py`):
- [ ] `test_pip_change_str`
- [ ] `test_pip_change_ordering_by_order`
- [ ] `test_pip_change_belongs_to_pip`

Write → test → commit: `feat(models): add PIPChange with ADD/ALTER/DROP fields and Galdr/Admin output`

---

### Step 3 — Migration

- [ ] `python manage.py makemigrations methodology`
- [ ] Verify both changes appear in migration file
- [ ] `python manage.py migrate`
- [ ] Run `pytest tests/integration/test_pip_implement.py` — must still pass

Commit: `feat(migrations): extend PIP and add PIPChange table`

---

### Step 4 — Django Admin

**File**: `methodology/admin.py`

```python
class PIPChangeInline(admin.TabularInline):
    model = PIPChange
    extra = 0
    readonly_fields = ["change_type", "entity_type", "name", "target_name",
                       "content", "galdr_recommendation", "galdr_reasoning", "order"]
    fields = readonly_fields + ["admin_decision", "admin_note"]

@admin.register(ProcessImprovementProposal)
class ProcessImprovementProposalAdmin(admin.ModelAdmin):
    list_display  = ["__str__", "playbook", "created_by", "status", "submitted_at"]
    list_filter   = ["status"]
    search_fields = ["title"]
    inlines       = [PIPChangeInline]
```

Commit: `feat(admin): register PIP with PIPChange inline`

---

### Step 5 — `PIPService` list methods

**File**: `methodology/services/pip_service.py`

Skeletons with full docstrings → tests → implement each method:

```python
def list_pips(user, status: str = None, playbook_id: int = None):
    """
    Return PIPs owned by user, optionally filtered.

    :param user: User instance — owner filter
    :param status: Optional status string. Example: "reviewed"
    :param playbook_id: Optional int. Example: 1
    :returns: QuerySet[ProcessImprovementProposal] ordered by -status_changed_at
    :example: list_pips(maria, status="reviewed") → [PIP-42]
    """
    # Log: user.id, status filter, playbook_id filter

def list_all_pips(admin_user, status: str = None, playbook_id: int = None):
    """
    Admin-only: return all users' PIPs.

    :raises PermissionError: if admin_user.is_staff is False
    :example: list_all_pips(mike) → [PIP-42, PIP-38, PIP-35, ...]
    """

def unread_count(user) -> int:
    """
    Count PIPs where status changed after last_viewed_at (or never viewed).

    :returns: int. Example: 2
    """

def mark_viewed(user) -> None:
    """
    Set last_viewed_at = now() on all of user's PIPs, clearing unread state.
    """
    # Log: user.id, count of PIPs updated
```

**Unit tests** (`tests/unit/test_pip_service_list.py`):
- [ ] `test_list_pips_returns_only_user_pips`
- [ ] `test_list_pips_filter_by_status`
- [ ] `test_list_pips_filter_by_playbook`
- [ ] `test_list_pips_combined_filters`
- [ ] `test_list_pips_empty`
- [ ] `test_list_all_pips_requires_staff`
- [ ] `test_list_all_pips_returns_all_users`
- [ ] `test_unread_count_counts_changed_since_last_view`
- [ ] `test_unread_count_zero_when_viewed_after`
- [ ] `test_mark_viewed_resets_unread_count`

Write → test → implement each → commit:
`feat(services): add PIPService list, list_all, unread_count, mark_viewed`

---

### Step 6 — Nav Count Pill (Context Processor)

**File**: `methodology/context_processors.py`

```python
def pip_unread_count(request):
    """
    Inject pip_unread_count into every template context for the PIPs nav pill.

    :returns: dict with key "pip_unread_count" (int, 0 if not authenticated)
    """
    if not request.user.is_authenticated:
        return {"pip_unread_count": 0}
    from methodology.services.pip_service import unread_count
    count = unread_count(request.user)
    logger.debug("pip_unread_count for user %s: %d", request.user.id, count)
    return {"pip_unread_count": count}
```

Register in `mimir/settings.py` → `TEMPLATES[0]["OPTIONS"]["context_processors"]`.

Commit: `feat(context): pip_unread_count context processor for nav pill`

---

### Step 7 — `pip_list` View

**File**: `methodology/pip_views.py` (create)

```python
@login_required
def pip_list(request):
    """
    PIP list page — My PIPs tab + All PIPs tab (staff only).
    Computes unread count BEFORE calling mark_viewed.

    Template: templates/methodology/pips/list.html
    Context:
        pips               — QuerySet (user's PIPs, filtered)
        all_pips           — QuerySet or None (staff only)
        unread_count       — int (before mark_viewed)
        is_admin           — bool
        statuses           — list[(value, label)]
        released_playbooks — QuerySet for filter dropdown
        active_status      — str or None
        active_playbook_id — int or None
    """
    # Log entry: user.id, GET params
    # 1. Capture unread count BEFORE mark_viewed
    # 2. mark_viewed
    # 3. Build filtered querysets
    # 4. Build filter options
    # 5. Render
```

URL (`mimir/urls.py`): replace placeholder `pip_list` route:
```python
path("pips/", pip_views.pip_list, name="pip_list"),
```

---

## BPE-03: Frontend Implementation

### Step 1 — Template from mockup

**Source**: `templates/mockups/pips/list.html`  
**Destination**: `templates/methodology/pips/list.html`

**Rewiring map:**

| Mockup | Real |
|---|---|
| `{% url 'mockup_pip_list' %}` | `{% url 'pip_list' %}` |
| `{% url 'mockup_pip_create' %}` | `{% url 'pip_create' %}` |
| `{% url 'mockup_pip_detail' pip_id=pip.id %}` | `{% url 'pip_detail' pk=pip.pk %}` |
| `pip.status_css` | `pip.get_status_badge_class` |
| `pip.status_changed` | `pip.status_changed_since_last_view` |
| `pip.changes_count` | `pip.changes.count` |
| Mock loop | `{% for pip in pips %}` |
| Remove mockup nav `alert alert-light border small` | — |

### Step 2 — Nav link in `base.html`

```html
<a class="nav-link {% if active_page == 'pips' %}active{% endif %}"
   href="{% url 'pip_list' %}" data-testid="nav-pips">
  PIPs
  {% if pip_unread_count %}
  <span class="badge bg-primary ms-1" data-testid="pip-nav-count">{{ pip_unread_count }}</span>
  {% endif %}
</a>
```

### Step 3 — CSS for Reviewed badge

Add to `static/css/design-system.css`:
```css
.pip-status-reviewed { background-color: var(--bs-purple); color: #fff; }
```

### Step 4 — Browser validation

- [ ] `/pips/` loads, shows My PIPs rows
- [ ] Nav pill shows count; disappears after visiting list
- [ ] Status filters update table
- [ ] Blue dot appears on changed rows
- [ ] Admin user sees All PIPs tab; regular user does not
- [ ] Empty state renders when no PIPs
- [ ] All `data-testid` attributes present (inspect in DevTools)
- [ ] Console has no JS errors

Commit: `feat(templates): pip list template wired to real context`

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_pip_list_view.py`

One test per scenario, no mocking, Django test client:

- [ ] `test_pip_list_01_nav_clears_count_pill` — GET /pips/ → pill gone, unread_count=0
- [ ] `test_pip_list_02_count_pill_shows_since_last_view` — set status_changed_at > last_viewed_at → pill shows 2
- [ ] `test_pip_list_04_shows_my_pips_by_default` — 6 rows, correct columns
- [ ] `test_pip_list_05_status_badge_colours` — HTML contains correct CSS classes per status
- [ ] `test_pip_list_06_blue_dot_on_changed_rows` — row with changed pip has `pip-changed` class
- [ ] `test_pip_list_07_row_actions_draft` — Draft row has View, Edit, Cancel
- [ ] `test_pip_list_07_row_actions_submitted` — Submitted row has View, Cancel only
- [ ] `test_pip_list_07_row_actions_accepted` — Accepted row has View only
- [ ] `test_pip_list_08_filter_by_reviewed` — ?status=reviewed → 1 row
- [ ] `test_pip_list_09_filter_by_multiple_statuses` — ?status=draft&status=submitted → 2 rows
- [ ] `test_pip_list_10_filter_by_playbook` — ?playbook_id=2 → 3 rows
- [ ] `test_pip_list_13_clear_filters` — no params → all 6 rows
- [ ] `test_pip_list_14_combined_status_and_playbook_filter`
- [ ] `test_pip_list_17_new_pip_button_present` — [+ New PIP] link exists
- [ ] `test_pip_list_18_empty_state_no_pips` — correct empty message
- [ ] `test_pip_list_19_empty_state_filter_no_results` — filter returns no results message
- [ ] `test_pip_list_20_admin_sees_all_pips_tab` — staff user sees All PIPs tab + Submitted by column
- [ ] `test_pip_list_21_non_admin_no_all_tab` — regular user has no All PIPs tab

Run: `pytest tests/integration/test_pip_list_view.py -v`  
Target: 100% pass, < 5s

Commit: `test(pips): feature acceptance tests for pip list — all 19 scenarios`

---

## BPE-05: Journey Certification Test

**File**: `tests/e2e/test_pip_journey_list.py`

Critical path to certify (Playwright + LiveServer):

```
Journey: Author sees unread pill → opens list → pill clears → filters → navigates to create
  1. Log in as maria
  2. Assert PIPs nav pill shows "1" (1 PIP changed since last view)
  3. Click PIPs nav link
  4. Assert pill is gone (unread reset)
  5. Assert 6 rows visible in table
  6. Select "Reviewed" in Status filter
  7. Assert 1 row visible, status badge is purple
  8. Click Clear Filters
  9. Assert 6 rows again
  10. Click [+ New PIP]
  11. Assert redirected to /pips/create/
```

Fixture data: `tests/fixtures/journey_seed.json` — add 6 PIPs with various statuses for maria.

Run: `pytest tests/e2e/test_pip_journey_list.py -v --headed`

Commit: `test(e2e): pip list journey certification — nav pill, filters, navigation`

---

## BPE-06: Definition of Done

- [ ] All 19 acceptance tests pass
- [ ] E2E journey test passes
- [ ] Existing `test_pip_implement.py` still passes
- [ ] `ProcessImprovementProposal` has all 6 statuses, new fields, `status_changed_since_last_view`
- [ ] `PIPChange` model exists, migrated, in admin
- [ ] `PIPService` methods: `list_pips`, `list_all_pips`, `unread_count`, `mark_viewed`
- [ ] Nav pill shows/clears correctly
- [ ] Admin sees All PIPs tab; non-admin does not
- [ ] Status filters work (single, multi, combined with playbook)
- [ ] Row actions correct by status (Draft=View+Edit+Cancel, Submitted=View+Cancel, others=View)
- [ ] Blue dot on rows changed since last view
- [ ] Empty state messages per spec
- [ ] All methods ≤ 30 lines; helpers extracted
- [ ] INFO logging on all service methods
- [ ] All imports at module level
- [ ] All `data-testid` attributes present
- [ ] No `NotImplementedError` stubs remain
- [ ] CSS `.pip-status-reviewed` defined

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Start dev server, open `/pips/` — visual spot-check
- [ ] Run Playwright journey test
- [ ] `pip freeze > requirements.txt` if new packages added
- [ ] Update `docs/features/act-9-pips/pips-list.feature` — add ✅ to each passing scenario
- [ ] Update screen-flow diagram: mark PIP List screen green (`strokeColor=#22c55e`)
- [ ] Final commit: `feat(pips): PIP list view complete — model, service, nav pill, filters (FOB-PIP-LIST-01..21)`
- [ ] Close GitHub issue, add `status-done` label
- [ ] Open PR → `main`

---

## Files Created / Modified

**New (9):**
1. `methodology/models/pip_change.py`
2. `methodology/services/pip_service.py`
3. `methodology/pip_views.py`
4. `methodology/context_processors.py`
5. `templates/methodology/pips/list.html`
6. `tests/unit/test_pip_model.py`
7. `tests/unit/test_pip_change_model.py`
8. `tests/unit/test_pip_service_list.py`
9. `tests/integration/test_pip_list_view.py`
10. `tests/e2e/test_pip_journey_list.py`

**Modified (5):**
1. `methodology/models/process_improvement_proposal.py`
2. `methodology/models/__init__.py`
3. `methodology/admin.py`
4. `mimir/urls.py`
5. `templates/base.html`
6. `mimir/settings.py`
7. `static/css/design-system.css`

## Mockup Reference

`templates/mockups/pips/list.html` — **do not delete**; rewire to real template at `templates/methodology/pips/list.html`. Keep `/mockups/pips/` routes alive as design reference.
