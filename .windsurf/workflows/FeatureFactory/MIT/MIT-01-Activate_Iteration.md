# Activity: Activate Iteration

**Activity ID**: 113
**Order**: 1
**Phase**: Activation
**Dependencies**: None

## Description

Activate Iteration

## Guidance

## Purpose
Bootstrap Jedao’s operational state from the GitHub Milestone manifest. Establish the execution queue and verify all pre-conditions are met before the first scenario starts.

## Prerequisites
- GitHub Milestone exists with `<!-- MANIFEST -->` YAML block
- All issues have `status-queued` label
- Human activation: "Work on Milestone #{N}"
- CLAUDE.md iteration protocol section is current

## Steps

### Step 1: Read and Parse Manifest
```bash
# Get milestone description
gh api repos/{owner}/{repo}/milestones/{N} --jq '.description'
```

Extract the `<!-- MANIFEST -->` block and parse the YAML. Validate:
- `iteration.goal` is present
- `iteration.target_duration_minutes` is set
- `iteration.doctrine_version` matches CLAUDE.md
- `parallel_groups` has at least one group
- Each scenario has: id, title, github_issue, parallel_group, time_budget_minutes, codebase_footprint, checkpoint, dependencies

If manifest is missing or invalid: STOP. Report to human: "Milestone #{N} manifest is malformed. Run PIT before starting MIT."

### Step 2: Verify Issues Exist
For every scenario in manifest:
```bash
gh issue view {github_issue} --json number,title,labels,state
```

Verify:
- Issue exists and is open
- Has label `status-queued`
- Title matches scenario title in manifest

If any issue is missing or already closed: report discrepancy to human before proceeding.

### Step 3: Build Execution Queue
Order scenarios by:
1. Parallel group order (A before B before C, etc.)
2. Within a group: by `time_budget_minutes` descending (longest first)
3. Dependency check: scenario cannot start until all `dependencies[]` are `status-done`

Produce the queue:
```
Execution Queue:
[READY]  S1 [A] Export workflow as JSON — 55 min — issue #142
[READY]  S3 [B] Manage Agents via web UI — 45 min — issue #144 (parallel with S1)
[BLOCKED] S2 [C] Import workflow from JSON — 55 min — issue #143 (waits for S1)
```

### Step 4: Record Activation
```bash
gh issue comment {first_issue_number} --body "<!-- ACTIVATION -->
Jedao activated at {timestamp}
Iteration: {goal}
Queue: {N} scenarios | Critical path: {duration} min
First scenario: S{N} — #{issue}
<!-- /ACTIVATION -->"
```

### Step 5: Log Activation State
Log to console/output:
```
=== MIT ACTIVATION ===
Milestone: #{N} | {goal}
Doctr version: {v} | Target: {duration} min
Scenarios: {N} total | {ready} ready | {blocked} blocked
First: S{N} [{group}] {title}
=====================
```

## Success Criteria
- Manifest parsed and validated
- All issues verified as open with `status-queued`
- Execution queue built and logged
- Activation timestamp recorded on GitHub
- Ready to proceed to MIT-02

## Notes
If this is a **session resume** (an issue already has `status-in-progress`): do NOT re-activate. Instead, proceed directly to MIT-02 for that scenario (re-run checkpoint first). See CLAUDE.md Session Resume Protocol.

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
