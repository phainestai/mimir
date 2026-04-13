# Activity: Run BPE-01 and Create Skeletons per Scenario

**Activity ID**: 107
**Order**: 4
**Phase**: Planning
**Dependencies**: Predecessor: Activity 106 (Sequence Scenarios)

## Description

Run BPE-01 and Create Skeletons per Scenario

## Guidance

## Purpose
For each scenario in parallel group order: run the full BPE-01 planning activity, then immediately create code skeletons from the plan. The skeleton commit produces the exact `codebase_footprint[]` that PIT-05 needs. This activity loops — repeat the full sequence for every scenario before proceeding to PIT-05.

## Prerequisites
- Scenario sequence from PIT-03
- Access to `BPE/BPE-01-Plan_Feature.md`
- Access to `.cursor/rules/do-skeletons-first.mdc`
- Working git branch for this iteration: `iteration/YYYYMMDD-goal-slug`

## Steps (repeat for each scenario)

### Step 1: Create Iteration Branch (first scenario only)
```bash
git checkout -b iteration/YYYYMMDD-goal-slug
```

### Step 2: Run BPE-01 in Full
Follow `.windsurf/workflows/FeatureFactory/BPE/BPE-01-Plan_Feature.md` completely for this scenario:
- Step 0: Reset task plan
- Step 1–2: Read SAO.md and user journey
- Step 3: Analyze feature specification for this scenario
- Step 4: Assess codebase state (reusable components, test coverage gaps)
- Step 5: Ask clarification questions if needed
- Step 6: Create implementation plan (backend + frontend + tests + commit strategy)
- Step 7–8: Add rule references, no time estimates
- Step 9: **Record but do not wait for approval** — approval happens at PIT-08
- Step 10: Create or update GitHub Issue with plan content

From the BPE-01 output, extract:
- List of classes and methods to create
- List of test files and test cases to create
- `time_budget_minutes`: estimate from plan complexity

### Step 3: Create Skeletons
For every class, method, and test identified in BPE-01:

**Production code skeletons** (per `do-skeletons-first.mdc`):
```python
class WorkflowExportService:
    def export_as_json(self, workflow_id: int, user) -> dict:
        """
        Export a workflow to a JSON-serializable dictionary.

        :param workflow_id: ID of workflow to export. Example: 42
        :param user: Requesting user for permission check. Example: User(id=1)
        :return: Dict with workflow data. Example: {"id": 42, "name": "BPE", "activities": [...]}
        :raises PermissionError: If user cannot access the workflow
        :raises ValueError: If workflow not found
        """
        # 1. Look up workflow, check user permission
        # 2. Serialize workflow + activities + artifacts
        # 3. Return dict
        raise NotImplementedError()
```

**Test skeletons**:
```python
class TestWorkflowExportService:
    def test_export_as_json_success(self):
        """Workflow exports to valid JSON dict with all activities."""
        raise NotImplementedError()

    def test_export_requires_permission(self):
        """Export raises PermissionError for unauthorized user."""
        raise NotImplementedError()
```

### Step 4: Verify Skeletons Fail Correctly
Run checkpoint command (to be defined in PIT-06) — it should fail with `NotImplementedError`, not with an import or syntax error:
```bash
pytest tests/integration/test_mcp_export.py -x 2>&1 | head -20
# Expected: NotImplementedError or collection passes with 0 tests
```

### Step 5: Commit Skeleton
```bash
git add -A
git commit -m "chore(pit): skeleton S{N} — {scenario title}

Files touched:
- methodology/services/workflow_export_service.py
- mcp_integration/tools.py
- tests/integration/test_mcp_export.py

Checkpoint: pytest tests/integration/test_mcp_export.py -x
Time budget: 55 min"
```

### Step 6: Record Footprint
After commit:
```bash
git diff HEAD~1 --name-only
```
Record the output as `codebase_footprint[]` for this scenario. Record `time_budget_minutes` from BPE-01 estimate.

### Step 7: Repeat for Next Scenario
Return to Step 2 for the next scenario in sequence order.

## Success Criteria
- BPE-01 plan exists for every scenario
- Skeleton committed for every scenario with descriptive commit message
- `codebase_footprint[]` recorded per scenario from `git diff --name-only`
- All skeletons fail with `NotImplementedError` (not syntax/import errors)
- `time_budget_minutes` recorded per scenario

## Rules
- Do not skip BPE-01 for any scenario — the plan is required before skeletons
- Commit one skeleton per scenario (not all at once) — this keeps footprints distinct
- If BPE-01 reveals a scenario is too large (> 90 min): stop, return to PIT-02 to split the scenario

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
