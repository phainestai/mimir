# Activity: Publish

**Activity ID**: 110
**Order**: 3
**Phase**: Construction
**Dependencies**: None

## Description

Publish

## Guidance

## Purpose
Create the GitHub Milestone and Issues from the execution manifest. The Milestone becomes MIT's operational ground truth — it must contain the full YAML manifest inline.

## Prerequisites
- Execution manifest YAML from PIT-02 (ITER-*.yaml, all scenarios with skeleton_commit, context_map, do_not_do, sao_sections)
- All skeleton commits on iteration branch
- GitHub CLI authenticated (`gh auth status`)

## Steps

### Step 1: Ensure Labels Exist
```bash
gh label create "status-queued"      --color "#e4e669" --description "Scenario waiting to start"     2>/dev/null || true
gh label create "status-in-progress" --color "#0075ca" --description "Scenario being executed"       2>/dev/null || true
gh label create "status-done"        --color "#0e8a16" --description "Scenario complete"              2>/dev/null || true
gh label create "parallel-group-A"   --color "#bfd4f2"                                                2>/dev/null || true
gh label create "parallel-group-B"   --color "#d4c5f9"                                                2>/dev/null || true
gh label create "parallel-group-C"   --color "#f9d0c4"                                                2>/dev/null || true
gh label create "drift-absorbed"     --color "#fef2c0"                                                2>/dev/null || true
gh label create "drift-escalated"    --color "#e11d48"                                                2>/dev/null || true
gh label create "backlog"            --color "#ededed"                                                 2>/dev/null || true
```

### Step 2: Create GitHub Milestone
```bash
gh api repos/{owner}/{repo}/milestones \
  --method POST \
  --field title="ITER-YYYYMMDD | {iteration_goal}" \
  --field description="$(cat <<'EOF'
<!-- MANIFEST -->
{paste full ITER-*.yaml content verbatim here}
<!-- /MANIFEST -->

## Iteration Goal
{iteration_goal}

## Scenarios
- S1: {title}
- S2: {title}
EOF
)"
```
Record the returned milestone number.

### Step 3: Create GitHub Issues (one per scenario)
For each scenario in manifest order, create an issue with the following body structure. All sections must be inline — do not link to external files:

```
<!-- SCENARIO -->
id: S1
parallel_group: A
skeleton_commit: {hash}
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
do_not_do:
  - "Do NOT create a new Django app"
  - "Do NOT add a manager layer between view and service"
rollback_point: "git stash"
<!-- /SCENARIO -->

## Context Map
| File | Lines | Note |
|------|-------|------|
| methodology/services/workflow_service.py | 45–80 | Follow this exact pattern |
| mcp_integration/tools.py | 120–145 | Append here, do NOT restructure |

## Do Not Do
- Do NOT create a new Django app
- Do NOT add a manager layer between view and service
- Do NOT modify existing service method signatures

## SAO.md Sections That Apply
- §Services Layer: shared by MCP and Web UI, no MCP-specific logic in services
- §MCP Access Rules: draft = full CRUD, released = read-only

## Implementation Plan
{BPE-01 plan content — full text, not a link}

## Acceptance Criteria
- [ ] `{checkpoint.command}` passes (exit code 0)
- [ ] No regressions: `pytest tests/ -x --ignore=tests/e2e` passes
- [ ] All changes committed with Angular convention message
```

Labels: `status-queued,parallel-group-{X}`
Milestone: the number from Step 2
For scenarios with dependencies, add in body: `Depends on #{issue_number} (S{N} must be done first)`

### Step 4: Update Manifest with Issue Numbers
Update ITER-*.yaml: add `github_issue` field for each scenario. Commit:
```bash
git add docs/plans/iterations/
git commit -m "chore(pit): add GitHub issue numbers to manifest ITER-YYYYMMDD"
```

### Step 5: Verify
```bash
gh milestone view {milestone_number}
# Expected: N open issues, 0% complete

gh issue list --milestone {milestone_number}
# Expected: all N issues with status-queued label
```

## Success Criteria
- Milestone created with full `<!-- MANIFEST -->` YAML block in description
- One Issue per scenario with inline `<!-- SCENARIO -->` YAML + context map + do-not-do + SAO sections + implementation plan
- All issues labelled `status-queued` + `parallel-group-{X}`
- Dependency issues reference each other correctly
- Local manifest YAML updated with github_issue numbers and committed

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Execution Manifest** (Document, Required) — produced by Contract (#105).

## Agent

None

## Skill

**Title**: GitHub Issue Operations
**Capability Domain**: GITHUB_ISSUE
**Technology Stack**: GitHub CLI

## Rules

None

## Artifacts Produced

- **GitHub Issues (Scenario Plans)** (Other) - Required
- **GitHub Milestone** (Other) - Required

## Artifacts Consumed

- **Execution Manifest** (Document) - Required

## Notes

No additional notes.
