# Activity: Close Iteration

**Activity ID**: 118
**Order**: 6
**Phase**: Closure
**Dependencies**: Predecessor: Activity 117 (Course Correct Manifest)

## Description

Close Iteration

## Guidance

## Purpose
Close the iteration formally: publish a GitHub Release, write the Lessons Learned document, and run EST-08 Sprint Close & Rebaseline to feed actuals back into the estimation model.

## Prerequisites
- All scenarios in terminal state (done/failed/skipped)
- `gh issue list --milestone {N} --state open` returns empty
- Human review completed (optional but recommended before release)

## Steps

### Step 1: Compute Iteration Metrics
From GitHub milestone issues and comments, compute:

```bash
# Get all issues for this milestone
gh issue list --milestone {N} --state all --json number,title,labels,closedAt,body,comments
```

From the data, compute:
- `scenarios_planned` = total issue count in milestone
- `scenarios_completed` = issues with `status-done` label
- `scenarios_abandoned` = issues closed without `status-done` (dropped)
- `velocity_ratio` = scenarios_completed / scenarios_planned
- `actual_duration_per_scenario` = from `<!-- CHECKPOINT_PASS -->` comments: `actual_duration` field
- `dominant_drift_cause` = most frequent signal_type in `<!-- DRIFT -->` comments
- `conflict_map_accuracy` = scenarios with NO unexpected files / scenarios_completed
- `rework_events` = count of `checkpoint_fail_retry` signals

### Step 2: Close GitHub Milestone
```bash
gh api repos/{owner}/{repo}/milestones/{N} \
  --method PATCH \
  --field state="closed"
```

### Step 3: Create GitHub Release
```bash
gh release create "ITER-{slug}" \
  --title "Iteration: {goal}" \
  --notes "$(cat <<'EOF'
## Iteration: {goal}

**Completed:** {scenarios_completed}/{scenarios_planned} scenarios  
**Velocity ratio:** {velocity_ratio}  
**Duration:** {actual_total} min (target: {target_duration} min)  

## Scenarios Shipped
{list of closed scenarios with links}

## Deferred
{list of dropped scenarios and reason}

## Key Learnings
{1-3 bullet points from lessons learned}
EOF
)"
```

### Step 4: Write Lessons Learned Document
Create `docs/lessons_learned/ITER-YYYYMMDD-HHmm-goal-slug.md`:

```markdown
<!-- LEARNING -->
milestone: {N}
goal: "{goal}"
velocity_ratio: {value}
scenarios_planned: {N}
scenarios_completed: {N}
scenarios_abandoned: {N}
dominant_drift_cause: {signal_type}
conflict_map_accuracy: {value}
files_with_unexpected_conflicts:
  - {file1}
  - {file2}
rework_events: {N}
<!-- /LEARNING -->

## What Happened
{Narrative of the iteration: what was planned, what was executed, how it went}

## Drift Events
{List of drift signals: type, scenario, resolution}

## Conflict Map Performance
{Were predicted conflicts accurate? Any surprises?}

## What to Change
- [ ] PIP: {proposed playbook improvement 1}
- [ ] PIP: {proposed playbook improvement 2}

## Raw Metrics
| Scenario | Budget | Actual | Overrun | Checkpoint |
|---|---|---|---|---|
| S1 {title} | {N} min | {N} min | {pct}% | PASS |
| S2 {title} | {N} min | {N} min | {pct}% | PASS |
```

Commit:
```bash
git add docs/lessons_learned/
git commit -m "docs(lessons): ITER-{slug} retrospective"
```

### Step 5: Run EST-08 Sprint Close & Rebaseline
Follow `.windsurf/workflows/FeatureFactory/EST/EST-08-Sprint_Close_Rebaseline.md` using this iteration’s actuals.

**Input mapping from iteration to EST-08:**

| MIT Metric | EST-08 Input | EST-08 Step |
|---|---|---|
| `velocity_ratio` | Velocity Factor (VF) | Step 2: Compute VF |
| `actual_duration_per_scenario` | Token consumption proxy | Step 1: Collect Sprint Actuals |
| `scenarios_completed × FP_weight` | AFP delivered | Step 5: Compute AFP VF |
| `dominant_drift_cause` | ECF/TCF re-rating signal | Step 6: Re-Rate ECF/TCF |
| `rework_events > 0` | Scope change flag | Step 2 rule: run BPE-08 first |

After EST-08:
- Save `docs/plans/MC_SNAPSHOT_{DATE}.md`
- Update `ESTIMATION_TEMPLATE.xlsx`

### Step 6: Signal Iteration Complete
```
=== ITERATION CLOSED ===
Goal:     {goal}
Result:   {scenarios_completed}/{scenarios_planned} ({velocity_ratio:.0%})
Release:  {release_tag}
Learning: docs/lessons_learned/ITER-{slug}.md
EST-08:   complete — new P80: {value}
=======================

Next: Run PIT for next iteration.
```

## Success Criteria
- GitHub Milestone closed
- GitHub Release created with scenario summary
- `docs/lessons_learned/ITER-*.md` written with `<!-- LEARNING -->` YAML block
- `velocity_ratio`, `dominant_drift_cause`, `conflict_map_accuracy` computed
- PIP candidates listed in `## What to Change`
- EST-08 completed with iteration actuals
- MC_SNAPSHOT saved

## Rules
- Do not close milestone if any issue is still `status-in-progress` without a human decision
- EST-08 is mandatory — do not skip even if iteration had low activity
- PIP candidates are proposals only — do not modify any workflow/activity without formal PIP approval

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
