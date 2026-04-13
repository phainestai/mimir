# Activity: Define Checkpoints and Hooks

**Activity ID**: 109
**Order**: 6
**Phase**: Planning
**Dependencies**: Predecessor: Activity 108 (Revise Conflict Map and Build Manifest)

## Description

Define Checkpoints and Hooks

## Guidance

## Purpose
Verify every checkpoint command is meaningful and runnable (fails correctly with NotImplementedError). Define drift thresholds per doctrine. Finalize the manifest with these values before publishing to GitHub.

## Prerequisites
- Execution manifest YAML from PIT-05
- All skeleton commits on the iteration branch

## Steps

### Step 1: Verify Each Checkpoint Command
For every scenario in the manifest, run its checkpoint command:
```bash
pytest tests/integration/test_mcp_export.py -x 2>&1 | tail -5
```

Expected outcomes (all acceptable at this stage):
- `FAILED ... NotImplementedError` ✔ skeleton is in place
- `ERROR ... collected 0 items` ✔ test file exists but has no runnable tests yet

Not acceptable:
- `ImportError` or `ModuleNotFoundError` ✘ — fix the skeleton import before proceeding
- `SyntaxError` ✘ — fix the skeleton syntax before proceeding

For any failing checkpoint: fix the skeleton, recommit, update `codebase_footprint` if new files added.

### Step 2: Define Drift Thresholds
Add a `drift_thresholds` block to the manifest YAML:

```yaml
drift_thresholds:
  absorbed:
    time_overrun_max_pct: 120      # up to 20% over budget: absorb and log
    checkpoint_fail_retry: 1       # retry once before escalating
  escalated:
    time_overrun_pct: 200          # >= 2x budget: stop and surface to human
    unexpected_files: true         # any file outside codebase_footprint: escalate
    repeated_checkpoint_fail: 2    # fail after retry: escalate
  doctrine_version: "1.0"
```

### Step 3: Define Rollback Points
For each scenario, verify the `rollback_point` is actionable:
- `git stash` — safe for uncommitted work
- `git reset --hard {commit_hash}` — for committed but broken state
- Migration name — if scenario includes database migrations

Update manifest if any rollback_point needs refinement.

### Step 4: Final Manifest Validation
Validate the complete manifest against this checklist:
- [ ] Every scenario has `checkpoint.command`
- [ ] Every `checkpoint.command` runs without import/syntax errors
- [ ] `drift_thresholds` block present with both `absorbed` and `escalated` sections
- [ ] Every scenario has `rollback_point`
- [ ] `doctrine_version` matches current doctrine
- [ ] `target_duration_minutes` = sum of critical path `time_budget_minutes`

### Step 5: Commit Updated Manifest
```bash
git add docs/plans/iterations/
git commit -m "chore(pit): finalize checkpoints and drift thresholds for ITER-YYYYMMDD"
```

## Success Criteria
- All checkpoint commands verified (run without import/syntax errors)
- `drift_thresholds` block in manifest YAML
- All rollback points actionable
- Manifest passes validation checklist

## Notes
The checkpoint command is the single source of truth for whether a scenario is done. If you cannot define a meaningful checkpoint, that is a planning signal: the scenario is not well enough specified to execute. Return to PIT-04 and sharpen the BPE-01 plan.

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
