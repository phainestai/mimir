# Activity: Orient & Validate Scope

**Activity ID**: 104
**Order**: 1
**Phase**: Construction
**Dependencies**: None

## Description

Orient & Validate Scope

## Guidance

## Purpose
Validate the iteration scope decided by the human and orient the execution session using patterns from past iterations. This activity receives scope as input — it does not discover or propose scope.

**Entry criteria (must be met before PIT is invoked):**
- Human has provided: iteration goal sentence + list of GitHub issue numbers to include
- If either is missing: respond "Scope not defined. Provide goal sentence + issue numbers, then invoke PIT." and stop.

## Session Resume Check
If `docs/plans/iterations/pit-orient-{today's date}.md` already exists → skip this activity, load it as the orient summary, proceed to PIT-02.

## Prerequisites
- `docs/lessons_learned/log.yaml` (may not exist on first iteration)
- Access to GitHub issues for each selected scenario

## Steps

### Step 1: Confirm Scope Input
Extract from the human's invocation:
- `iteration_goal`: the goal sentence
- `selected_issues`: list of GitHub issue numbers

Verify each issue exists and is open:
```bash
gh issue view {N} --json number,title,state,labels
```
If any issue is closed or not found: report the discrepancy and stop.

### Step 2: Read Learning Log
```bash
cat docs/lessons_learned/log.yaml
```

If file does not exist → first iteration. Create:
```bash
mkdir -p docs/lessons_learned
cat > docs/lessons_learned/log.yaml << 'EOF'
# Iteration learning log — append only, newest entries last
# Schema: milestone, date, goal, velocity_ratio, dominant_drift, footprint_accuracy, pip_candidates
entries: []
EOF
```
Produce orient summary: "First iteration — no historical patterns."

If file exists → read last 5 entries from `entries:` array.

### Step 3: Compute Trends
From last 5 entries compute:
- **velocity_ratio trend**: improving / stable / degrading (compare last 3)
- **dominant_drift**: most frequent signal type across entries
- **footprint_accuracy trend**: improving / stable / degrading

### Step 4: Validate Scope Against History
For each selected scenario:
- If `dominant_drift` was `footprint_violation` in 2+ of last 5 iterations: flag scenarios touching areas with known complexity
- If `velocity_ratio` trend is degrading AND more than 2 scenarios selected: flag as scope risk

### Step 5: Write Orient Summary
Create `docs/plans/iterations/pit-orient-{YYYYMMDD}.md`:

```markdown
## Orient Summary — {date}

### Input Scope
Goal: {iteration_goal}
Scenarios: {issue_numbers and titles}

### Velocity Trend
Last 3 ratios: {v1}, {v2}, {v3} — {improving/stable/degrading}

### Dominant Drift
{signal_type} ({N}/{total} iterations)

### Footprint Accuracy
{pct}% — {improving/stable/degrading}

### Scope Validation
{per-scenario risk flags, or "No risks detected"}

### Watch For
- {risk from dominant drift, or "None — first iteration"}
```

## Success Criteria
- Scope input confirmed (goal sentence + issues present and open)
- `docs/plans/iterations/pit-orient-{date}.md` written
- Per-scenario risk flags computed (or noted as first iteration)
- Ready for PIT-02

## Agent

None

## Skill

None

## Rules

- **Github Issues** (`do-github-issues`)
- **Plan Before Doing** (`do-plan-before-doing`)
- **Pull Frequently** (`do-pull-frequently`)

## Artifacts Produced

None

## Artifacts Consumed

- **GitHub Release** (Other) - Optional
- **Lessons Learned Document** (Document) - Optional

## Notes

No additional notes.
