# Activity: Execute Scenario

**Activity ID**: 114
**Order**: 2
**Phase**: Execution
**Dependencies**: Predecessor: Activity 113 (Activate Iteration)

## Description

Execute Scenario

## Guidance

## Purpose
Execute a single scenario by filling its skeleton, running the checkpoint, and recording the result. This activity loops — repeat for every scenario in the execution queue until all are in a terminal state (done/failed/skipped).

## Prerequisites
- Execution queue from MIT-01 (or current milestone state on resume)
- Next eligible scenario: `status-queued` + all `dependencies[]` are `status-done`

## Steps (repeat per scenario)

### Step 0: Pre-flight
Select next eligible scenario from queue:
```bash
gh issue list --milestone {N} --label status-queued --json number,title,labels,body
```

For the candidate: parse `<!-- SCENARIO -->` YAML from issue body. Check `dependencies[]`: for each dependency scenario ID, verify its GitHub issue is closed (status-done).

If dependency not met: skip this scenario for now, pick next eligible. Log:
```
S{N} BLOCKED — waiting for S{dep}. Picking next eligible.
```

### Step 1: Claim Scenario
```bash
gh issue edit {issue_number} --add-label "status-in-progress" --remove-label "status-queued"
gh issue comment {issue_number} --body "<!-- EXECUTION_START -->
Started at: {timestamp}
Time budget: {N} min
<!-- /EXECUTION_START -->"
```

### Step 2: Fill the Skeleton
Follow BPE-02 → BPE-05 to implement the scenario:
- **BPE-02**: Implement backend (fill skeleton methods, no more `raise NotImplementedError()`)
- **BPE-03**: Implement frontend (if applicable)
- **BPE-04**: Implement feature acceptance tests
- **BPE-05**: Implement journey certification tests (if applicable)

**During implementation, monitor the footprint:**
After each significant change, check if any new file was touched that isn’t in `codebase_footprint[]`:
```bash
git diff --name-only HEAD
```
If unexpected file appears: check severity — see MIT-03.

### Step 3: Run Checkpoint
```bash
# Run the checkpoint command from issue YAML
{checkpoint.command}
CHECKPOINT_EXIT=$?
echo "Checkpoint exit code: $CHECKPOINT_EXIT"
```

Also run full regression:
```bash
pytest tests/ -x --ignore=tests/e2e 2>&1 | tail -10
```

### Step 4: Evaluate Result

**If checkpoint passes (exit code 0) AND regression passes:**
```bash
# Record actual duration
ACTUAL_DURATION={minutes_elapsed}

# Commit the implementation
git add -A
git commit -m "feat({scope}): {scenario title}

Implements {scenario_id} from iteration ITER-{slug}
Checkpoint: {command} — PASSED
Actual duration: {N} min (budget: {budget} min)"

# Close the issue
gh issue close {issue_number} --comment "<!-- CHECKPOINT_PASS -->
Checkpoint passed at: {timestamp}
Actual duration: {N} min (budget: {budget} min)
Overrun: {pct}%
Command: {command}
<!-- /CHECKPOINT_PASS -->"

# Update label
gh issue edit {issue_number} --remove-label "status-in-progress" --add-label "status-done"
```

**If checkpoint fails:** → go to MIT-03 (Handle Drift)

### Step 5: Pull Next Scenario
Return to Step 0 for next eligible scenario. Continue until all scenarios are in terminal state.

**Iteration complete when:** `gh issue list --milestone {N} --state open` returns empty.

## Success Criteria
- Scenario checkpoint passes
- Full regression passes
- Implementation committed with Angular convention message
- Issue closed with `status-done` and actual_duration recorded
- Next eligible scenario identified

## Rules
- Never claim two scenarios simultaneously (single-threaded by default)
- Never touch files outside `codebase_footprint[]` without evaluating as scope_expansion
- If actual_duration exceeds budget by 20%: log absorbed drift comment before continuing
- If actual_duration exceeds budget by 100%: stop, escalate (MIT-03 → MIT-04)

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
