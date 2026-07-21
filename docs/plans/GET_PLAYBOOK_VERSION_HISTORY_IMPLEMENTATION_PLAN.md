# Implementation Plan: Extend `get_playbook` with Version History

**Feature**: FOB-MCP-VH — Playbook version history and point-in-time snapshots via MCP  
**GitHub Issue**: TBD  
**Branch**: `feature/get-playbook-version-history`  
**Spec**: `docs/features/act-13-mcp/mcp-integration.feature` (scenarios FOB-MCP-VH-01/02/03)  
**UAT**: `tests/uat/mcp-uat-flow.feature` (MCP-12)

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `mcp_integration/tools.py` | 203–237 | Extend `get_playbook()` here — add two optional params; no new tool |
| `methodology/services/playbook_history_service.py` | 1–51 | Use `list_playbook_version_rows()` and `get_playbook_version_by_number()` directly — do NOT re-implement |
| `methodology/models/playbook_version.py` | 1–71 | `PlaybookVersion` model: `snapshot_data` (JSONField), `change_summary`, `source`, `pip_id`, `created_at`, `is_major` |
| `mcp_integration/facade/tools_http.py` | 63–72 | HTTP facade `get_playbook()` — forward new params as query string to DRF API |
| `methodology/api/viewsets.py` | 53–94 | `PlaybookViewSet` — override `retrieve()` to read `include_history` and `version` query params |

---

## Do Not Do

- Do NOT create a new MCP tool (`list_playbook_versions`) — extend `get_playbook` as agreed
- Do NOT add a new service or model — `playbook_history_service.py` already exists and is correct
- Do NOT add MCP-specific logic to services — services are shared with the web UI
- Do NOT modify `PlaybookVersion` model or its migrations
- Do NOT change the signature of `list_playbook_version_rows()` or `get_playbook_version_by_number()`
- Do NOT add async to `playbook_history_service.py` functions — wrap with `sync_to_async` at the tool layer
- Do NOT return `versions` by default — only when `include_history=True` (keep default response lean)

---

## SAO.md Sections That Apply

- §Services Layer: shared by MCP and Web UI; no MCP-specific logic in services
- §MCP Access Rules: draft = full CRUD, released = read-only; version history is read-only for all
- §Phase 3 Advanced MCP Tools: version history retrieval falls under this roadmap item
- §DRF API: extend `PlaybookViewSet.retrieve()` with query params; do NOT add a new URL pattern

---

## Scenarios Covered

### S1 — FOB-MCP-VH-01: Get playbook version history list
**Call**: `get_playbook(playbook_id=X, include_history=True)`  
**Response**: standard playbook fields + `versions: [{version_number, source, pip_id, change_summary, created_at, is_major}, ...]` ordered newest-first  
**Default**: `include_history=False` → no `versions` key in response

### S2 — FOB-MCP-VH-02: Get playbook snapshot at specific version
**Call**: `get_playbook(playbook_id=X, version="1.0")`  
**Response**: `{version_number, snapshot_data: {...}, source, pip_id, change_summary, created_at, is_major}`  
**Error**: version not found → `ValueError: version 1.0 not found for playbook X`

### S3 — FOB-MCP-VH-03: Unknown version returns clear error
**Call**: `get_playbook(playbook_id=X, version="99.9")`  
**Response**: error payload with substring `99.9 not found`

---

## Implementation Steps

### Step 0: Branch
```bash
git checkout -b feature/get-playbook-version-history
```

---

### Step 1: Write integration tests (RED first)

**File**: `tests/integration/test_mcp_get_playbook_version_history.py`

Tests to write:
- `test_get_playbook_default_has_no_versions_key` — default call omits `versions`
- `test_get_playbook_include_history_returns_versions_list` — `include_history=True` returns non-empty list for a playbook with version rows; each row has required keys
- `test_get_playbook_include_history_empty_when_no_versions` — no `PlaybookVersion` rows → `versions: []`
- `test_get_playbook_version_snapshot_returns_snapshot_data` — `version="x.x"` returns `snapshot_data` and `version_number`
- `test_get_playbook_version_not_found_raises_error` — unknown version raises `ValueError` with version number in message
- `test_get_playbook_include_history_and_version_incompatible` — when both params set, `version` takes precedence (returns snapshot only)

Follow fixture pattern from `tests/integration/test_mcp_facade.py`.  
Use real `PlaybookVersion` objects — no mocking.

```bash
pytest tests/integration/test_mcp_get_playbook_version_history.py -x  # must fail (RED)
```

---

### Step 2: Extend `get_playbook` in `mcp_integration/tools.py`

Add two optional parameters to the `get_playbook` async function:

```python
async def get_playbook(
    playbook_id: int,
    include_history: bool = False,
    version: str | None = None,
) -> dict:
```

Logic (inside the function, after fetching the playbook):

- **When `version` is provided**: call `sync_to_async(get_playbook_version_by_number)(playbook, Decimal(version))`; if `None` → raise `ValueError(f"Version {version} not found for playbook {playbook_id}")`; return `_serialize_version_snapshot(pv)`
- **When `include_history=True`** (and `version` is None): call `sync_to_async(list_playbook_version_rows)(playbook)`; add `"versions"` key to existing response
- **Default** (both False/None): existing behavior unchanged

Helper `_serialize_version_snapshot(pv: PlaybookVersion) -> dict` (private function at module level):
```python
{
    "version_number": str(pv.version_number),
    "source": pv.source,
    "pip_id": pv.pip_id,
    "change_summary": pv.change_summary,
    "created_at": pv.created_at.isoformat() if pv.created_at else None,
    "is_major": pv.is_major,
    "snapshot_data": pv.snapshot_data,
}
```

Helper `_serialize_version_row(row: dict) -> dict` — accepts a row from `list_playbook_version_rows()` and returns it as-is (already dict-friendly); verify date fields are serializable.

Import at top of `tools.py`:
```python
from methodology.services.playbook_history_service import (
    list_playbook_version_rows,
    get_playbook_version_by_number,
)
```

```bash
pytest tests/integration/test_mcp_get_playbook_version_history.py -x  # must pass (GREEN)
```

---

### Step 3: Extend DRF `PlaybookViewSet.retrieve()` in `methodology/api/viewsets.py`

Override `retrieve()` to handle `?include_history=true` and `?version=x.x` query params:

```python
def retrieve(self, request, pk=None):
    """GET /api/playbooks/{pk}/ with optional ?include_history=true or ?version=x.x"""
    ...
```

- Base response: serialize playbook with `PlaybookSerializer`
- If `?version=x.x`: look up `PlaybookVersion`; 404 if not found; return `_version_snapshot_response(pv)`
- If `?include_history=true`: add `versions` list from `list_playbook_version_rows()`

Keep existing tests passing — default `retrieve()` behavior must be unchanged.

```bash
pytest tests/integration/ -k "playbook" -x
```

---

### Step 4: Extend HTTP facade in `mcp_integration/facade/tools_http.py`

```python
def get_playbook(
    playbook_id: int,
    include_history: bool = False,
    version: str | None = None,
) -> dict:
    params = {}
    if include_history:
        params["include_history"] = "true"
    if version is not None:
        params["version"] = version
    r = get_client().get(f"/api/playbooks/{playbook_id}/", params=params)
    return check_response(r, "get_playbook")
```

---

### Step 5: Run full test suite

```bash
pytest tests/ -x --ignore=tests/e2e
```

All 1378+ tests must pass.

---

### Step 6: Update UAT tool coverage map

In `tests/uat/mcp-uat-flow.feature`, update the tool coverage count comment at top:
- Mark `get_playbook` as now covering `include_history` + `version` variants

---

### Step 7: Commit

```
feat(mcp): extend get_playbook with include_history and version params

Adds two optional parameters to the get_playbook MCP tool and HTTP API:
- include_history=True → returns versions list (version_number, source,
  pip_id, change_summary, created_at, is_major), newest-first
- version="x.x" → returns snapshot_data at that version; error if not found

Powered by existing PlaybookVersion model and playbook_history_service.
Covers scenarios FOB-MCP-VH-01/02/03. Closes #<issue>.
```

---

## Tests to Create (Summary)

| Test | File | Validates |
|------|------|-----------|
| `test_get_playbook_default_has_no_versions_key` | integration | default omits `versions` |
| `test_get_playbook_include_history_returns_versions_list` | integration | list with required fields |
| `test_get_playbook_include_history_empty_when_no_versions` | integration | empty list when no history |
| `test_get_playbook_version_snapshot_returns_snapshot_data` | integration | snapshot_data present |
| `test_get_playbook_version_not_found_raises_error` | integration | error contains version number |
| `test_get_playbook_version_takes_precedence_over_include_history` | integration | `version` wins when both set |

---

## Acceptance Criteria

- [ ] `pytest tests/integration/test_mcp_get_playbook_version_history.py -x` passes
- [ ] `pytest tests/ -x --ignore=tests/e2e` passes (no regressions)
- [ ] `get_playbook(playbook_id=X)` — response has NO `versions` key (default unchanged)
- [ ] `get_playbook(playbook_id=X, include_history=True)` — `versions` list present, correct keys
- [ ] `get_playbook(playbook_id=X, version="y.y")` — `snapshot_data` returned
- [ ] `get_playbook(playbook_id=X, version="99.9")` — error with `99.9` in message
- [ ] HTTP facade (`tools_http.py`) forwards params correctly
- [ ] DRF `retrieve()` supports same params via query string
