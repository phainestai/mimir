# PIP Sub-Story 6: MCP Tools for PIPs

**Feature file**: `docs/features/act-13-mcp/interact-with-pips-via-mcp.feature`  
**Scenarios**: MCP-PIP-01 … 39  
**Complexity**: medium — REST API viewset + FastMCP facade + MCP tool registration  
**Branch**: `feature/act-9-pips/mcp`  
**Depends on**: PIP-LIST (model + service foundation), PIP-CREATE (change service methods), PIP-GALDR-ENGINE (submit triggers Galdr)  
**Blocks**: nothing — terminal sub-story

---

## Overview

Adds 8 MCP tools (`list_pips`, `get_pip`, `create_pip`, `add_change`, `edit_change`, `remove_change`, `submit_pip`, `cancel_pip`) by implementing a REST API viewset backed by `PIPService`, and thin FastMCP facade functions that call it.

Pattern to follow: `mcp_integration/facade/tools_http.py` + `mcp_integration/tools.py` (see existing `list_activities`, `create_activity` etc.).

**Scenarios covered:**
- MCP-PIP-01..07 — `list_pips` (filters, unread reset, isolation)
- MCP-PIP-08..11 — `create_pip` (happy, draft playbook error, empty title, permission)
- MCP-PIP-12..19 — `add_change` (ADD/ALTER/DROP, non-draft guard, validation)
- MCP-PIP-20..23 — `edit_change`
- MCP-PIP-24..25 — `remove_change`
- MCP-PIP-26..30 — `submit_pip` (guards, owner check)
- MCP-PIP-31..34 — `cancel_pip` (Draft/Submitted allowed; Reviewed/Accepted blocked)
- MCP-PIP-35..38 — `get_pip` (full detail, Galdr output, not found, permission)
- MCP-PIP-39 — end-to-end workflow scenario

---

## BPE-02: Backend Implementation

### Step 1 — Serializers

**File**: `methodology/api/serializers.py` (extend)

```python
class PIPChangeSerializer(serializers.ModelSerializer):
    """
    Read serializer for PIPChange — includes Galdr output.
    Example output:
        {"id": 7, "order": 1, "change_type": "ADD", "entity_type": "Activity",
         "name": "Accessibility Audit", "content": "...",
         "galdr_recommendation": "ACCEPT", "galdr_reasoning": "..."}
    """
    class Meta:
        model = PIPChange
        fields = ["id", "order", "change_type", "entity_type",
                  "name", "target_id", "target_name", "content",
                  "parent_workflow_id", "insert_after_id",
                  "galdr_recommendation", "galdr_reasoning"]

class PIPSerializer(serializers.ModelSerializer):
    """
    Read serializer for ProcessImprovementProposal with nested changes.
    Example output:
        {"id": 42, "title": "Add Accessibility Audit", "status": "reviewed",
         "changes_count": 2, "changes": [...], "submitted_at": "2026-05-14T09:00:00Z"}
    """
    changes       = PIPChangeSerializer(many=True, read_only=True)
    changes_count = serializers.SerializerMethodField()
    submitted_by  = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = ProcessImprovementProposal
        fields = ["id", "title", "summary", "status", "playbook_id",
                  "submitted_by", "submitted_at", "status_changed_at",
                  "changes_count", "changes"]

    def get_changes_count(self, obj) -> int:
        return obj.changes.count()

class PIPCreateSerializer(serializers.Serializer):
    """Write serializer for creating a PIP."""
    playbook_id = serializers.IntegerField()
    title       = serializers.CharField(max_length=200)
    summary     = serializers.CharField(required=False, default="")

class PIPChangeCreateSerializer(serializers.Serializer):
    """Write serializer for adding a Change."""
    change_type        = serializers.ChoiceField(choices=["ADD","ALTER","DROP"])
    entity_type        = serializers.ChoiceField(choices=["Workflow","Activity","Skill","Agent","Artifact"])
    name               = serializers.CharField(required=False, default="")
    target_id          = serializers.IntegerField(required=False, allow_null=True)
    target_name        = serializers.CharField(required=False, default="")
    content            = serializers.CharField(required=False, default="")
    parent_workflow_id = serializers.IntegerField(required=False, allow_null=True)
    insert_after_id    = serializers.IntegerField(required=False, allow_null=True)
```

Commit: `feat(api): add PIP and PIPChange serializers`

---

### Step 2 — REST API ViewSet

**File**: `methodology/api/viewsets.py` (extend — add new viewset, do NOT modify legacy `create_pip` endpoint)

```python
class PIPViewSet(viewsets.ViewSet):
    """
    REST API for PIPs. All endpoints require authentication.
    Delegates business logic to PIPService — no ORM calls in this class.
    """
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """
        GET /api/pips/
        Query params: status, playbook_id
        Returns: list of user's PIPs (serialized).
        Also calls PIPService.mark_viewed to reset unread count.
        """

    def retrieve(self, request, pk):
        """GET /api/pips/{pk}/ — returns full PIP with changes."""

    def create(self, request):
        """POST /api/pips/ — body: {playbook_id, title, summary}"""

    @action(detail=True, methods=["post"])
    def submit(self, request, pk):
        """POST /api/pips/{pk}/submit/"""

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk):
        """POST /api/pips/{pk}/cancel/"""


class PIPChangeViewSet(viewsets.ViewSet):
    """Nested viewset for PIPChanges under a PIP."""
    permission_classes = [IsAuthenticated]

    def create(self, request, pip_pk):
        """POST /api/pips/{pip_pk}/changes/"""

    def partial_update(self, request, pip_pk, pk):
        """PATCH /api/pips/{pip_pk}/changes/{pk}/"""

    def destroy(self, request, pip_pk, pk):
        """DELETE /api/pips/{pip_pk}/changes/{pk}/"""
```

**URL registration** (`methodology/api/urls.py` or `mimir/urls.py`):
```python
path("api/pips/",                                    PIPViewSet.as_view({"get":"list","post":"create"})),
path("api/pips/<int:pk>/",                           PIPViewSet.as_view({"get":"retrieve"})),
path("api/pips/<int:pk>/submit/",                    PIPViewSet.as_view({"post":"submit"})),
path("api/pips/<int:pk>/cancel/",                    PIPViewSet.as_view({"post":"cancel"})),
path("api/pips/<int:pip_pk>/changes/",               PIPChangeViewSet.as_view({"post":"create"})),
path("api/pips/<int:pip_pk>/changes/<int:pk>/",      PIPChangeViewSet.as_view({"patch":"partial_update","delete":"destroy"})),
```

**Unit tests** (`tests/unit/test_pip_api_serializers.py`):
- [ ] `test_pip_serializer_includes_changes`
- [ ] `test_pip_create_serializer_validates_required_fields`
- [ ] `test_pip_change_create_serializer_validates_choice_fields`

Commit: `feat(api): add PIPViewSet and PIPChangeViewSet REST endpoints`

---

### Step 3 — FastMCP Facade Functions

**File**: `mcp_integration/facade/tools_http.py` (extend)

Each function: build URL, call `self._get`/`_post`, return dict/list. Follow existing pattern for `list_activities`, `create_activity` etc.

```python
def list_pips(ctx, status: str = None, playbook_id: int = None) -> list[dict]:
    """
    GET /api/pips/?status=…&playbook_id=…
    Also triggers mark_viewed on server side.

    :param ctx: UserContext
    :param status: Optional status filter. Example: "reviewed"
    :param playbook_id: Optional int filter. Example: 1
    :returns: list of PIP dicts ordered by -status_changed_at
    """

def get_pip(ctx, pip_id: int) -> dict:
    """GET /api/pips/{pip_id}/ — full PIP with changes array."""

def create_pip(ctx, playbook_id: int, title: str, summary: str = "") -> dict:
    """POST /api/pips/ {playbook_id, title, summary} → new Draft PIP dict."""

def add_change(ctx, pip_id: int, change_type: str, entity_type: str,
               name: str = "", target_id: int = None, target_name: str = "",
               content: str = "", parent_workflow_id: int = None,
               insert_after_id: int = None) -> dict:
    """POST /api/pips/{pip_id}/changes/ → created PIPChange dict."""

def edit_change(ctx, pip_id: int, change_id: int, **kwargs) -> dict:
    """PATCH /api/pips/{pip_id}/changes/{change_id}/ → updated PIPChange dict."""

def remove_change(ctx, pip_id: int, change_id: int) -> dict:
    """DELETE /api/pips/{pip_id}/changes/{change_id}/ → {deleted: True}."""

def submit_pip(ctx, pip_id: int) -> dict:
    """POST /api/pips/{pip_id}/submit/ → updated PIP dict with new status."""

def cancel_pip(ctx, pip_id: int) -> dict:
    """POST /api/pips/{pip_id}/cancel/ → {success: True}."""
```

Commit: `feat(mcp-facade): add 8 PIP facade functions wrapping REST API`

---

### Step 4 — MCP Tool Registration

**File**: `mcp_integration/tools.py` (extend)

Follow exact pattern of existing tools (e.g. `list_activities`, `create_activity`):

```python
@mcp.tool()
def list_pips(status: str = None, playbook_id: int = None) -> str:
    """
    List Playbook Improvement Proposals for the current user.

    Args:
        status: Filter by status. One of: draft, submitted, processing_galdr,
                reviewed, accepted, rejected. Example: "reviewed"
        playbook_id: Filter by playbook. Example: 1
    Returns:
        JSON list of PIPs. Each entry: {id, title, status, changes_count,
        submitted_at, last_updated_at, target_playbook_id, target_playbook_name}
    """
    ctx = get_user_context()
    return json.dumps(pip_facade.list_pips(ctx, status=status, playbook_id=playbook_id))

@mcp.tool()
def get_pip(pip_id: int) -> str:
    """
    Get full detail of a PIP including all Changes and Galdr recommendations.

    Args:
        pip_id: PIP primary key. Example: 42
    Returns:
        JSON PIP object with nested changes array.
        Each change includes galdr_recommendation and galdr_reasoning if Reviewed.
    Raises:
        ValueError if pip_id not found.
        PermissionError if PIP not owned by current user.
    """

@mcp.tool()
def create_pip(playbook_id: int, title: str, summary: str = "") -> str:
    """
    Create a Draft PIP targeting a Released playbook.

    Args:
        playbook_id: Released playbook to propose changes for. Example: 1
        title: Short description of the improvement. Example: "Add Accessibility Audit"
        summary: Optional extended rationale. Example: "Playbook lacks WCAG 2.1 AA coverage."
    Returns:
        JSON new PIP with status "Draft" and empty changes list.
    Raises:
        PermissionError if playbook is Draft or not accessible.
        ValueError if title is empty.
    """

@mcp.tool()
def add_change(pip_id: int, change_type: str, entity_type: str,
               name: str = "", target_id: int = None, content: str = "",
               parent_workflow_id: int = None, insert_after_id: int = None) -> str:
    """
    Add a typed Change to a Draft PIP.

    Args:
        pip_id: Draft PIP to add change to. Example: 42
        change_type: "ADD", "ALTER", or "DROP"
        entity_type: "Workflow", "Activity", "Skill", "Agent", or "Artifact"
        name: Required for ADD — name of new entity. Example: "Accessibility Audit"
        target_id: Required for ALTER/DROP — PK of existing entity. Example: 22
        content: Required for ADD (new content) and ALTER (replacement). For DROP = rationale.
        parent_workflow_id: For ADD Activity/Skill/Agent — workflow to place it under. Example: 11
        insert_after_id: For ADD Activity — insert after this activity id. Null = append. Example: 22
    Returns:
        JSON created PIPChange with id, order, change_type, entity_type.
    Raises:
        PermissionError if PIP not Draft.
        ValueError for missing required fields.
    """

@mcp.tool()
def edit_change(pip_id: int, change_id: int, content: str = None,
                name: str = None, insert_after_id: int = None) -> str:
    """Update a Change on a Draft PIP."""

@mcp.tool()
def remove_change(pip_id: int, change_id: int) -> str:
    """Remove a Change from a Draft PIP. Remaining changes are renumbered."""

@mcp.tool()
def submit_pip(pip_id: int) -> str:
    """
    Submit a Draft PIP for Galdr review. PIP must have at least 1 Change.
    Galdr begins processing immediately; status transitions to Processing (Galdr).
    """

@mcp.tool()
def cancel_pip(pip_id: int) -> str:
    """
    Cancel a Draft or Submitted PIP. Cannot cancel Reviewed, Accepted, or Rejected PIPs.
    """
```

Commit: `feat(mcp): register 8 PIP MCP tools — list, get, create, add_change, edit_change, remove_change, submit, cancel`

---

## BPE-03: Frontend Implementation

MCP tools have no UI. No frontend work needed.  
Verify via MCP client / curl that endpoints respond correctly (see manual test below).

---

## BPE-04: Feature Acceptance Tests

**File**: `tests/integration/test_pip_mcp_tools.py`

No mocking — use real `PIPService` + Django test DB + Django test client for API calls:

- [ ] `test_mcp_01_list_pips_returns_user_pips` (MCP-PIP-01)
- [ ] `test_mcp_02_list_pips_filter_draft` (MCP-PIP-02)
- [ ] `test_mcp_04_list_pips_filter_by_playbook` (MCP-PIP-04)
- [ ] `test_mcp_05_list_pips_resets_unread` (MCP-PIP-05)
- [ ] `test_mcp_06_list_pips_empty` (MCP-PIP-06)
- [ ] `test_mcp_07_list_pips_isolation` (MCP-PIP-07)
- [ ] `test_mcp_08_create_pip_draft` (MCP-PIP-08)
- [ ] `test_mcp_09_create_pip_draft_playbook_error` (MCP-PIP-09)
- [ ] `test_mcp_10_create_pip_empty_title_error` (MCP-PIP-10)
- [ ] `test_mcp_12_add_change_add_append` (MCP-PIP-12)
- [ ] `test_mcp_14_add_change_alter` (MCP-PIP-14)
- [ ] `test_mcp_15_add_change_drop` (MCP-PIP-15)
- [ ] `test_mcp_16_add_change_non_draft_error` (MCP-PIP-16)
- [ ] `test_mcp_17_add_change_invalid_entity_type` (MCP-PIP-17)
- [ ] `test_mcp_18_add_change_add_missing_content` (MCP-PIP-18)
- [ ] `test_mcp_19_add_change_drop_missing_rationale` (MCP-PIP-19)
- [ ] `test_mcp_20_edit_change_updates_content` (MCP-PIP-20)
- [ ] `test_mcp_22_edit_change_non_draft_error` (MCP-PIP-22)
- [ ] `test_mcp_24_remove_change` (MCP-PIP-24)
- [ ] `test_mcp_26_submit_pip_transitions_submitted` (MCP-PIP-26)
- [ ] `test_mcp_27_submit_pip_no_changes_error` (MCP-PIP-27)
- [ ] `test_mcp_28_submit_pip_already_submitted_error` (MCP-PIP-28)
- [ ] `test_mcp_31_cancel_submitted_pip` (MCP-PIP-31)
- [ ] `test_mcp_33_cancel_reviewed_pip_error` (MCP-PIP-33)
- [ ] `test_mcp_35_get_pip_with_changes` (MCP-PIP-35)
- [ ] `test_mcp_36_get_pip_reviewed_includes_galdr` (MCP-PIP-36)
- [ ] `test_mcp_37_get_pip_not_found` (MCP-PIP-37)
- [ ] `test_mcp_38_get_pip_wrong_user_error` (MCP-PIP-38)
- [ ] `test_mcp_39_end_to_end_create_add_submit_review` (MCP-PIP-39)

Run: `pytest tests/integration/test_pip_mcp_tools.py -v`

Commit: `test(mcp): acceptance tests for all 8 PIP MCP tools — 29 scenarios`

---

## BPE-05: Journey Certification Test

No Playwright needed — MCP tools are API-level, no browser UI.  
MCP-PIP-39 (end-to-end) covered as an integration test above.

---

## BPE-06: Definition of Done

- [ ] All 29 acceptance tests pass
- [ ] `GET /api/pips/` returns only current user's PIPs
- [ ] `POST /api/pips/` creates Draft; returns serialized PIP
- [ ] `POST /api/pips/<id>/changes/` adds Change; returns serialized PIPChange
- [ ] `POST /api/pips/<id>/submit/` transitions to Submitted; triggers Galdr
- [ ] `POST /api/pips/<id>/cancel/` cancels; blocked on Reviewed/Accepted
- [ ] `GET /api/pips/<id>/` returns full PIP with changes + Galdr output
- [ ] All 8 MCP tools registered in `tools.py` with full docstrings
- [ ] Error messages match exact wording in feature file
- [ ] Existing MCP tests unaffected
- [ ] INFO logging on all API viewset methods

---

## BPE-07: Finalize

- [ ] `pytest tests/` — 100% pass
- [ ] Manual test: call `list_pips` via MCP client, verify returns correct user's PIPs
- [ ] Update `interact-with-pips-via-mcp.feature` — add ✅ per passing scenario
- [ ] Final commit: `feat(pips): PIP MCP tools complete — 8 tools, REST API (MCP-PIP-01..39)`
- [ ] Close GitHub issue, `status-done`
- [ ] PR → `main`

---

## Files Created / Modified

**New (3):**
1. `tests/unit/test_pip_api_serializers.py`
2. `tests/integration/test_pip_mcp_tools.py`
3. (no new E2E test — MCP-PIP-39 is integration-level)

**Modified (4):**
1. `methodology/api/serializers.py`
2. `methodology/api/viewsets.py`
3. `mcp_integration/facade/tools_http.py`
4. `mcp_integration/tools.py`
5. `mimir/urls.py`
