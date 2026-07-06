---

name: Fix export_workflow_to_local
overview: "Split the export into two concerns: the server generates file contents (no I/O), returns them as JSON, and the local MCP facade writes the files to the user's machine."
todos:

- id: add-generate-method
content: "Add WorkflowExportService.generate_workflow_files() — pure content generation, no filesystem I/O"
status: completed
- id: fix-viewset
content: "Update viewsets.py export action to call generate_workflow_files() and return JSON"
status: completed
- id: fix-facade
content: "Update tools_http.py export_workflow_to_local() to write files locally from JSON response"
status: completed
- id: unit-tests
content: "Add unit tests for generate_workflow_files() in test_workflow_export_service.py"
status: completed
- id: integration-tests
content: "Add integration tests for the new API endpoint shape in test_workflow_export_import_mcp.py"
status: completed
- id: e2e-tool-test
content: "Strengthen test_48_export_workflow_to_local in test_mcp_e2e_all_tools.py to verify local file writes"
status: completed
- id: bdd-scenarios
content: "Update workflows-export-import.feature scenario FOB-WORKFLOWS-EXPORT_IMPORT-01 to reflect local file writes via facade"
status: completed
isProject: false

---



# Fix `export_workflow_to_local` — server writes locally



## Root cause

`tools_http.py::export_workflow_to_local` POSTs to `/api/workflows/{id}/export/`.
The Django viewset calls `WorkflowExportService.export_workflow_to_markdown()`, which calls `export_path.mkdir()` and `file.write_text()` on the **hosted server's** filesystem — never reaching the user's machine.
The viewset even has a dead-end 501 fallback for exactly this failure (`'Export to filesystem not supported on hosted server'`).

## Implementation — three production files

**Repo for edits and tests:** `Z:\Documents\GitHub\mimir` (Mac host share, has `.env`).
**MCP server process** runs from `C:\Users\denispetelin\mimir` (Windows-local clone) — it must be restarted after changes are deployed there, but editing happens in Z:.

Run tests with: `.venv/Scripts/pytest tests/unit/test_workflow_export_service.py tests/integration/test_workflow_export_import_mcp.py` (no `.env` needed — test settings use SQLite).

---



### 1. `[methodology/services/workflow_export_service.py](Z:\Documents\GitHub\mimir\methodology\services\workflow_export_service.py)`

Add `generate_workflow_files()` as a new static method. Reuses all existing private `_generate_*` methods but does zero filesystem I/O — returns file contents as plain lists.

Return shape:

```python
{
    "workflow_id": 42,
    "workflow_name": "My Workflow",
    "folder_name": "My_Workflow",
    "workflow_files": [
        {"filename": "_workflow.md", "content": "..."},
        {"filename": "My_Workflow-01-First_Step.md", "content": "..."},
    ],
    "rule_files": [
        {"filename": "my-rule.mdc", "content": "..."},
    ],
}
```

The existing `export_workflow_to_markdown()` is kept unchanged — still used by the Django-embedded ORM server (`mcp_integration/tools.py`).

### 2. `[methodology/api/viewsets.py](Z:\Documents\GitHub\mimir\methodology\api\viewsets.py)` — `export` action (~line 533)

Replace body to call `generate_workflow_files()` and return 200 JSON directly. Remove the now-dead `PermissionError/OSError` try/except.

```python
@action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
def export(self, request, pk=None):
    self.get_object()  # permission check
    folder_name = request.data.get('folder_name')
    from methodology.services.workflow_export_service import WorkflowExportService
    result = WorkflowExportService.generate_workflow_files(
        workflow_id=pk,
        folder_name=folder_name,
    )
    return Response(result)
```



### 3. `[mcp_integration/facade/tools_http.py](Z:\Documents\GitHub\mimir\mcp_integration\facade\tools_http.py)` — `export_workflow_to_local()` (~line 306)

Receive JSON, write files locally using `pathlib`. Add `from pathlib import Path` at top of file.

```python
def export_workflow_to_local(workflow_id, target_directory=".windsurf/workflows", folder_name=None):
    payload = {}
    if folder_name:
        payload["folder_name"] = folder_name
    r = get_client().post(f"/api/workflows/{workflow_id}/export/", json=payload)
    data = check_response(r, "export_workflow_to_local")

    wf_dir = Path(target_directory) / data["folder_name"]
    wf_dir.mkdir(parents=True, exist_ok=True)
    for f in data["workflow_files"]:
        (wf_dir / f["filename"]).write_text(f["content"], encoding="utf-8")

    rule_files_written = []
    if data.get("rule_files"):
        rules_dir = Path(target_directory).resolve().parent / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        for f in data["rule_files"]:
            (rules_dir / f["filename"]).write_text(f["content"], encoding="utf-8")
            rule_files_written.append(f["filename"])

    return {
        "status": "exported",
        "workflow_id": data["workflow_id"],
        "workflow_name": data["workflow_name"],
        "export_path": str(wf_dir),
        "files_created": [f["filename"] for f in data["workflow_files"]],
        "rule_files_created": rule_files_written,
        "message": "Workflow exported successfully. Edit files locally and use import_workflow_from_local to apply changes.",
    }
```



## Tests — four levels (BPE-01 planning)



### Unit tests (thin) — `[tests/unit/test_workflow_export_service.py](Z:\Documents\GitHub\mimir\tests\unit\test_workflow_export_service.py)`

Add a new `TestGenerateWorkflowFiles` class:

- `test_generate_returns_file_contents` — result has `workflow_files`, `rule_files`, `folder_name`; `_workflow.md` content present; no filesystem side effects
- `test_generate_with_rules` — activities with linked rules produce `rule_files` entries with `.mdc` YAML front matter
- `test_generate_default_folder_name` — omitting `folder_name` uses slugified workflow name
- `test_generate_nonexistent_workflow_raises` — `ObjectDoesNotExist` propagates

Pure DB-read tests — no `tmp_path`, no `shutil`.

### Integration tests (thick — main bet) — `[tests/integration/test_workflow_export_import_mcp.py](Z:\Documents\GitHub\mimir\tests\integration\test_workflow_export_import_mcp.py)`

Add a new `TestWorkflowExportAPIShape` class using Django test client:

- `test_export_endpoint_returns_json_not_files` — POST `/api/workflows/{id}/export/` returns 200 with `workflow_files` list; confirms no `export_path` key (server doesn't write files)
- `test_export_endpoint_returns_correct_file_count` — `len(workflow_files)` == activity count + 1
- `test_export_endpoint_rule_files_in_response` — activities with rules → non-empty `rule_files` with correct `.mdc` content
- `test_export_endpoint_requires_auth` — unauthenticated POST → 401/403



### E2E / facade test strengthening — `[tests/integration/test_mcp_e2e_all_tools.py](Z:\Documents\GitHub\mimir\tests\integration\test_mcp_e2e_all_tools.py)`

Tighten `test_48_export_workflow_to_local` to assert that `tmp_path` actually contains a `_workflow.md` file after the call — not just "result is a dict".

### BDD acceptance scenarios — `[docs/features/act-3-workflows/workflows-export-import.feature](Z:\Documents\GitHub\mimir\docs\features\act-3-workflows\workflows-export-import.feature)`

Update scenario `FOB-WORKFLOWS-EXPORT_IMPORT-01`:

- `Then the MCP server exports the workflow` → `Then the MCP facade receives file contents from the server`
- Add: `And the facade writes files to the AI workspace at ".windsurf/workflows/FFE/"`

Add new scenario `FOB-WORKFLOWS-EXPORT_IMPORT-01c Hosted server returns file contents, not a path`:

- Server response contains `workflow_files` array with `filename`/`content` pairs but no `export_path`
- Facade computes the local path; that path appears in the tool's final return value



## No changes needed

- `facade/server.py` — tool registration unchanged
- `mcp_integration/tools.py` — ORM version keeps calling `export_workflow_to_markdown()` directly; writes locally as before
- `import_workflow_from_local` — symmetric hosted-write problem exists but is out of scope

