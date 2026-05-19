# Activity: Contract

**Activity ID**: 105
**Order**: 2
**Phase**: Construction
**Dependencies**: Predecessor: Activity 104 (Orient & Validate Scope)

## Description

Contract

## Guidance

## Purpose
For each selected scenario: run BPE-01 planning, create thorough code skeletons (public + private helpers), build the context map and do-not-do list, verify checkpoint commands. After all scenarios: derive the file-level conflict map from actual skeleton commits and write the execution manifest YAML.

This is a single-pass operation — there is no area-level pre-check. Conflict information comes from real skeleton commits only.

## Prerequisites
- Orient summary from PIT-01
- Access to `docs/architecture/SAO.md`
- Access to BDD feature specs in `docs/features/`

## Steps

### Step 1: Create Iteration Branch (once, first scenario only)
```bash
git checkout -b iteration/YYYYMMDD-goal-slug
```

---

### Steps 2–8 repeat for each scenario in selected_issues order

### Step 2: Read Specification and SAO.md
Read the BDD feature spec for this scenario. Identify the exact scenario(s) in scope.

Read `docs/architecture/SAO.md`. Note which sections govern this scenario — record section headings for the manifest.

### Step 3: Run BPE-01
Follow `BPE/BPE-01-Plan_Feature.md` for this scenario completely. The BPE-01 plan output must include all four of the following — do not proceed to skeletons without them:

**a) Context Map** — 3–5 existing `file:line_range` references. For each, one line: what pattern to follow, what to extend, or what NOT to touch:
```
| methodology/services/workflow_service.py | 45–80 | Follow this exact pattern for the new service |
| mcp_integration/tools.py | 120–145 | Append tool here, do NOT restructure existing tools |
| tests/integration/test_workflow_crud.py | 1–40 | Follow fixture setup pattern |
```

**b) Do-Not-Do List** — derived explicitly from the SAO.md sections identified in Step 2:
```
- Do NOT create a new Django app
- Do NOT add a manager/repository layer — services call ORM directly
- Do NOT modify existing service method signatures
- Do NOT add async
```

**c) Applicable SAO.md Sections** — list by heading name, e.g.:
```
- §Services Layer: shared by MCP and Web UI, no MCP-specific logic in services
- §MCP Access Rules: draft = full CRUD, released = read-only
```

**d) Checkpoint Command** — single pytest command that definitively proves the scenario done.

### Step 4: Create Thorough Skeleton
Write skeletons for every class and method — public AND private helpers. The skeleton is the complete architecture for this scenario. If an implementor cannot fill in the logic without adding new methods, the skeleton is underspecified.

**Production code:**
```python
class WorkflowExportService:
    def export_as_json(self, workflow_id: int, user) -> dict:
        """
        Export workflow to JSON-serializable dict.

        :param workflow_id: ID of workflow. Example: 42
        :param user: Requesting user for permission check.
        :return: Dict. Example: {"id": 42, "name": "BPE", "activities": [...]}
        :raises PermissionError: If user cannot access workflow
        :raises ValueError: If workflow not found
        """
        # 1. Look up workflow, check user permission via _check_permission
        # 2. Delegate serialization to _serialize_workflow
        # 3. Return dict
        raise NotImplementedError()

    def _serialize_workflow(self, workflow) -> dict:
        """Serialize workflow and its activities to dict."""
        # 1. Build base dict from workflow fields
        # 2. Serialize each activity via _serialize_activity
        # 3. Return assembled dict
        raise NotImplementedError()

    def _serialize_activity(self, activity) -> dict:
        """Serialize a single activity to dict."""
        raise NotImplementedError()

    def _check_permission(self, workflow, user) -> None:
        """Raise PermissionError if user cannot access workflow."""
        raise NotImplementedError()
```

**Test skeletons:**
```python
class TestWorkflowExportService:
    def test_export_as_json_with_valid_workflow_returns_complete_dict(self):
        """Exported dict contains workflow fields and all activities."""
        raise NotImplementedError()

    def test_export_as_json_with_unauthorized_user_raises_permission_error(self):
        raise NotImplementedError()

    def test_export_as_json_with_missing_workflow_raises_value_error(self):
        raise NotImplementedError()
```

### Step 5: Verify Checkpoint Command
Run the checkpoint command:
```bash
{checkpoint_command} 2>&1 | tail -5
```

Acceptable outcomes:
- `FAILED ... NotImplementedError` ✔ skeleton in place
- `collected 0 items` ✔ test file exists, no runnable tests yet

Not acceptable (fix before proceeding):
- `ImportError` or `ModuleNotFoundError` ✘
- `SyntaxError` ✘

### Step 6: Commit Skeleton
```bash
git add -A
git commit -m "chore(pit): skeleton S{N} — {scenario title}

Checkpoint: {command}"
```

### Step 7: Record Footprint
```bash
git diff HEAD~1 --name-only
```
Record as `codebase_footprint[]` for this scenario. Record `skeleton_commit` hash.

### Step 8: Repeat for Next Scenario

---

### After All Scenarios:

### Step 9: Build File-Level Conflict Map
For each pair of scenarios, check footprint intersection:
```
S1 ∩ S2 = {mcp_integration/tools.py} → CONFLICT → serialize
S1 ∩ S3 = {} → no conflict → can parallel
```

### Step 10: Assign Parallel Groups
Non-conflicting scenarios → same group (can run in parallel).
Conflicting scenarios → different groups, later group depends on earlier.
```
Group A: [S1]
Group B: [S3]   ← parallel with A, no shared files
Group C: [S2]   ← depends on S1 (shared tools.py)
```

### Step 11: Write Execution Manifest
Create `docs/plans/iterations/ITER-YYYYMMDD-HHmm-goal-slug.yaml`:

```yaml
iteration:
  goal: "{iteration_goal}"
  doctrine_version: "2.0"
  created_at: "{ISO8601 timestamp}"

conflict_map:
  mcp_integration/tools.py: [S1, S2]

parallel_groups:
  A: [S1]
  B: [S3]
  C: [S2]

drift_thresholds:
  absorbed:
    checkpoint_fail_retry: 1        # retry once before escalating
  escalated:
    footprint_violation: true       # any file outside codebase_footprint[]
    method_explosion: true          # unplanned public method vs skeleton
    sao_violation: true             # compliance check finds architectural breach
    checkpoint_fail_after_retry: true

scenarios:
  S1:
    title: "User can export workflow as JSON"
    github_issue: TBD
    parallel_group: A
    skeleton_commit: "{hash}"
    codebase_footprint:
      - mcp_integration/tools.py
      - methodology/services/workflow_export_service.py
      - tests/integration/test_mcp_export.py
    checkpoint:
      command: "pytest tests/integration/test_mcp_export.py -x"
      expected_exit_code: 0
    dependencies: []
    sao_sections:
      - "§Services Layer"
      - "§MCP Access Rules"
    context_map:
      - file: "methodology/services/workflow_service.py"
        lines: "45-80"
        note: "Follow this exact pattern for the new export service"
      - file: "mcp_integration/tools.py"
        lines: "120-145"
        note: "Append new tool here, do NOT restructure existing tools"
    do_not_do:
      - "Do NOT create a new Django app"
      - "Do NOT add a manager layer between view and service"
      - "Do NOT modify existing service method signatures"
    rollback_point: "git stash"
```

### Step 12: Commit Manifest
```bash
git add docs/plans/iterations/
git commit -m "chore(pit): execution manifest ITER-YYYYMMDD"
```

## Success Criteria
- BPE-01 plan exists for every scenario (with context map, do-not-do list, SAO sections, checkpoint command)
- Skeleton committed per scenario — public AND private helpers, all with NotImplementedError
- All checkpoint commands verified (NotImplementedError or 0 items — not import/syntax errors)
- File-level conflict map built from actual `git diff --name-only` per skeleton commit
- ITER-*.yaml manifest written with sao_sections, context_map, do_not_do, skeleton_commit per scenario

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **GitHub Release** (Other, Optional) — produced by Close Iteration (#118).
- **Lessons Learned Document** (Document, Optional) — produced by Close Iteration (#118).

## Agent

None

## Skill

None

## Rules

- **Github Issues** (`do-github-issues`)

## Artifacts Produced

- **Execution Manifest** (Document) - Required

## Artifacts Consumed

- **GitHub Release** (Other) - Optional
- **Lessons Learned Document** (Document) - Optional

## Notes

No additional notes.
