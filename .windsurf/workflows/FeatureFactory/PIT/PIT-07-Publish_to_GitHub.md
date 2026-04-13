# Activity: Publish to GitHub

**Activity ID**: 110
**Order**: 7
**Phase**: Publication
**Dependencies**: Predecessor: Activity 109 (Define Checkpoints and Hooks)

## Description

Publish to GitHub

## Guidance

## Purpose
Create the GitHub Milestone (Iteration record) and Issues (ScenarioExecution records) from the execution manifest. The Milestone becomes Jedao’s operational ground truth during MIT.

## Prerequisites
- Finalized execution manifest YAML from PIT-06
- GitHub CLI authenticated (`gh auth status`)
- Required labels exist in repo (create if missing)

## Steps

### Step 1: Ensure Labels Exist
```bash
# Status labels
gh label create "status-queued" --color "#e4e669" --description "Scenario waiting to start" 2>/dev/null || true
gh label create "status-in-progress" --color "#0075ca" --description "Scenario being executed" 2>/dev/null || true
gh label create "status-done" --color "#0e8a16" --description "Scenario complete" 2>/dev/null || true
gh label create "status-failed" --color "#d93f0b" --description "Scenario failed" 2>/dev/null || true

# Parallel group labels
gh label create "parallel-group-A" --color "#bfd4f2" 2>/dev/null || true
gh label create "parallel-group-B" --color "#d4c5f9" 2>/dev/null || true
gh label create "parallel-group-C" --color "#f9d0c4" 2>/dev/null || true

# Drift labels
gh label create "drift-absorbed" --color "#fef2c0" 2>/dev/null || true
gh label create "drift-escalated" --color "#e11d48" 2>/dev/null || true
```

### Step 2: Create GitHub Milestone
```bash
gh api repos/{owner}/{repo}/milestones \
  --method POST \
  --field title="ITER-YYYYMMDD | {iteration_goal}" \
  --field description="$(cat <<'EOF'
<!-- MANIFEST -->
iteration:
  goal: "{iteration_goal}"
  target_duration_minutes: {N}
  doctrine_version: "1.0"
  created_at: "{timestamp}"

conflict_map:
  {file}: [{S1}, {S2}]

parallel_groups:
  A: [{S1}]
  B: [{S3}]
  C: [{S2}]
<!-- /MANIFEST -->

## Iteration Goal
{iteration_goal}

## Scenarios
- S1: {title} (#issue)
- S2: {title} (#issue)
EOF
)" \
  --field due_on="{YYYY-MM-DDT23:59:59Z}"
```

Record the returned milestone number.

### Step 3: Create GitHub Issues (one per scenario)
For each scenario in manifest order:

```bash
gh issue create \
  --title "[{SN}][{group}] {scenario_title}" \
  --label "status-queued,parallel-group-{X},{difficulty}" \
  --milestone "{milestone_number}" \
  --body "$(cat <<'EOF'
<!-- SCENARIO -->
id: S1
parallel_group: A
time_budget_minutes: 55
codebase_footprint:
  - mcp_integration/tools.py
  - methodology/services/workflow_export_service.py
  - tests/integration/test_mcp_export.py
checkpoint:
  command: "pytest tests/integration/test_mcp_export.py -x"
  expected_exit_code: 0
dependencies: []
rollback_point: "git stash"
<!-- /SCENARIO -->

## Plan
{BPE-01 plan content pasted here}

## Acceptance Criteria
- [ ] {checkpoint_command} passes (exit code 0)
- [ ] No regressions in existing tests (`pytest tests/ -x`)
- [ ] Changes committed with Angular convention message
EOF
)"
```

For scenarios with dependencies, add in body:
```
## Dependencies
Depends on #{issue_number} (S1 must be done first)
```

### Step 4: Verify Publication
```bash
gh milestone view {milestone_number}
# Should show: N issues, 0% complete

gh issue list --milestone {milestone_number}
# Should show all N issues with status-queued label
```

### Step 5: Update Manifest with Issue Numbers
Update the YAML manifest to add `github_issue` field for each scenario, then recommit:
```bash
git add docs/plans/iterations/
git commit -m "chore(pit): add GitHub issue numbers to manifest ITER-YYYYMMDD"
```

## Success Criteria
- Milestone created with `<!-- MANIFEST -->` YAML block in description
- One Issue created per scenario with `<!-- SCENARIO -->` YAML block + BPE-01 plan
- All issues labelled: `status-queued` + `parallel-group-{X}`
- Dependency issues reference each other correctly
- Milestone shows 0/{N} complete
- Local manifest YAML updated with github_issue numbers

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
