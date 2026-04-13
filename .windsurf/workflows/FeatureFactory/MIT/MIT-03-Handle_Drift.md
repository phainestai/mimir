# Activity: Handle Drift

**Activity ID**: 115
**Order**: 3
**Phase**: Course Correction
**Dependencies**: Predecessor: Activity 114 (Execute Scenario)

## Description

Handle Drift

## Guidance

## Purpose
Classify a detected deviation from the plan, determine severity, and respond according to doctrine. Absorbed signals: Jedao handles autonomously and continues. Escalated signals: Jedao stops and surfaces to human via MIT-04.

**This activity is conditional — only entered when a drift event is detected during MIT-02.**

## Signal Types

| Signal Type | Trigger | Description |
|---|---|---|
| `time_overrun` | actual > budget × threshold | Scenario taking longer than planned |
| `test_failure` | checkpoint returns non-zero | Tests fail on first or retry run |
| `scope_expansion` | unexpected file touched | File outside `codebase_footprint[]` was modified |
| `integration_conflict` | two scenarios shared a file not in conflict map | Runtime conflict not caught by PIT |
| `checkpoint_fail_retry` | second consecutive checkpoint failure | Retry didn’t fix it |

## Steps

### Step 1: Classify the Signal
Determine signal type from evidence:

```
time_overrun:         actual_elapsed > time_budget_minutes × 1.2
test_failure:         checkpoint exit code != 0 (first occurrence)
scope_expansion:      git diff --name-only HEAD shows file NOT in codebase_footprint[]
integration_conflict: another in-progress issue also touched this file (check git log)
checkpoint_fail_retry: second checkpoint failure after one retry attempt
```

### Step 2: Determine Severity

**ABSORBED** (Jedao handles, continues autonomously):
- `time_overrun` AND actual < budget × 2.0
- `test_failure` (first occurrence only — one retry allowed)
- `scope_expansion` of a test or config file (low risk)

**ESCALATED** (stop, surface to human → MIT-04):
- `time_overrun` AND actual >= budget × 2.0
- `checkpoint_fail_retry` (second failure after retry)
- `scope_expansion` of a production source file
- `integration_conflict` (runtime conflict not in manifest)
- Any combination of 2+ absorbed signals on the same scenario

### Step 3: Record Drift Signal
Post comment on the scenario’s GitHub issue:

**Absorbed:**
```bash
gh issue comment {issue_number} --body "<!-- DRIFT absorbed -->
type: {signal_type}
severity: absorbed
detected_at: {timestamp}
elapsed: {N} min (budget: {budget} min, {pct}% of budget)
action: {what Jedao did to address it}
<!-- /DRIFT -->"
gh issue edit {issue_number} --add-label "drift-absorbed"
```

**Escalated:**
```bash
gh issue comment {issue_number} --body "<!-- ESCALATE -->
type: {signal_type}
severity: escalated
detected_at: {timestamp}
evidence: {specific evidence}
jedao_recommendation: {recommended action}
await_human_decision: true
<!-- /ESCALATE -->"
gh issue edit {issue_number} \
  --add-label "drift-escalated" \
  --remove-label "status-in-progress"
```

### Step 4: Act on Severity

**If absorbed:**
- For `time_overrun`: log and continue executing
- For `test_failure` (first): apply targeted fix, re-run checkpoint once
  - If retry passes: continue (record retry in comment)
  - If retry fails: reclassify as `checkpoint_fail_retry` → ESCALATED
- For `scope_expansion` (test/config): add file to `codebase_footprint[]` in issue YAML, continue

**If escalated:** STOP current scenario execution. → Go to MIT-04.

## Success Criteria
- Signal type correctly classified
- Severity correctly determined per doctrine thresholds
- Drift comment posted on GitHub issue with full evidence
- Absorbed: Jedao continues with recorded action
- Escalated: Jedao stops, human notified via MIT-04

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
