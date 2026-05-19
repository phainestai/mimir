# Activity: Close Iteration

**Activity ID**: 118
**Order**: 4
**Phase**: Construction
**Dependencies**: None

## Description

Close Iteration

## Guidance

## Purpose
Formally close the iteration: compute metrics, write lessons learned, close the GitHub Milestone, and publish a GitHub Release. End with a mandatory follow-up prompt — the learning loop is not complete without EST-08 and PIP review.

## Prerequisites
`gh issue list --milestone {N} --state open` returns empty (all scenarios in terminal state).

Do not close if any issue is still `status-in-progress` without a human decision.

## Steps

### Step 1: Compute Metrics
```bash
gh issue list --milestone {N} --state all --json number,title,labels,closedAt,comments
```

From the data, compute:
- `scenarios_planned` = total issue count in milestone
- `scenarios_completed` = issues with `status-done` label
- `scenarios_abandoned` = issues closed without `status-done`
- `velocity_ratio` = scenarios_completed / scenarios_planned
- `dominant_drift` = most frequent `type:` value across all `<!-- DRIFT -->` and `<!-- ESCALATE -->` comments
- `footprint_accuracy` = scenarios with zero `footprint_violation` signals / scenarios_completed (express as %)
- `rework_events` = count of `checkpoint_fail_retry` signals across all issues
- `pip_candidates` = count of escalation events + count of absorbed drifts (each is a potential playbook improvement)

### Step 2: Close Milestone
```bash
gh api repos/{owner}/{repo}/milestones/{N} --method PATCH --field state="closed"
```

### Step 3: Create GitHub Release
```bash
gh release create "ITER-{slug}" \
  --title "Iteration: {goal}" \
  --notes "$(cat <<'EOF'
## {goal}

**Result:** {scenarios_completed}/{scenarios_planned} scenarios shipped
**Velocity ratio:** {velocity_ratio:.0%}
**Dominant drift:** {dominant_drift or "none"}
**Footprint accuracy:** {footprint_accuracy}%

## Shipped
{list of closed scenarios with issue links}

## Deferred
{list of dropped scenarios with reason, or "none"}
EOF
)"
```

### Step 4: Append to Learning Log
Append one entry to `docs/lessons_learned/log.yaml`:
```yaml
- milestone: {N}
  date: {YYYYMMDD}
  goal: "{goal}"
  velocity_ratio: {value}
  dominant_drift: {signal_type or "none"}
  footprint_accuracy: {pct}
  pip_candidates: {N}
```

### Step 5: Write Lessons Learned Document
Create `docs/lessons_learned/ITER-YYYYMMDD-goal-slug.md`:
```markdown
## What Happened
{Narrative: planned vs. executed, notable moments}

## Drift Events
{Signal type | Scenario | Resolution — or "none"}

## Conflict Map Performance
{Were file-level conflicts accurate? Any surprises?}

## What to Change (PIP Candidates)
- [ ] PIP: {improvement 1}
- [ ] PIP: {improvement 2}

## Raw Metrics
| Scenario | Result | Drift | Checkpoint |
|----------|--------|-------|------------|
| S{N} {title} | done/dropped | {signal or none} | PASS/FAIL |
```

Commit:
```bash
git add docs/lessons_learned/
git commit -m "docs(lessons): ITER-{slug} retrospective"
```

### Step 6: Mandatory Follow-Up Prompt
Output the following message — it cannot be omitted or shortened:

```
=== ITERATION CLOSED ===
Goal:      {goal}
Result:    {completed}/{planned} ({velocity_ratio:.0%})
Release:   ITER-{slug}
Learning:  docs/lessons_learned/ITER-{slug}.md

Two follow-up actions required to complete the learning loop:

1. EST-08 Sprint Close & Rebaseline
   Invoke with these actuals:
     velocity_ratio={velocity_ratio}
     dominant_drift={dominant_drift}
     footprint_accuracy={footprint_accuracy}
     rework_events={rework_events}
   Purpose: update P50/P80/P95 delivery forecast with this iteration's data.

2. PIP Review — {pip_candidates} candidates
   See: docs/lessons_learned/ITER-{slug}.md → "## What to Change"
   Purpose: review proposed playbook improvements and approve/reject each.

Skipping these degrades planning accuracy for future iterations.
========================
```

## Success Criteria
- `docs/lessons_learned/log.yaml` entry appended (structured YAML)
- Lessons learned document written and committed
- GitHub Milestone closed
- GitHub Release created with scenario summary
- Follow-up prompt output with specific actuals for EST-08 invocation
- PIP candidate count stated explicitly

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Execution Manifest** (Document, Required) — produced by Contract (#105).
- **GitHub Issues (Scenario Plans)** (Other, Required) — produced by Publish (#110).
- **GitHub Milestone** (Other, Required) — produced by Publish (#110).

## Agent

**Name**: Shuos Jedao
**Description**: # Agent: Shuos Jedao

*Archetype: Ninefox Gambit — the brilliant tactician who sees the whole battlefield, bounded by an authority protocol that exists because consequences matter.*

## Role

Autonomous execution agent for MIT (Manage Iteration). Primary responsibility: complete the iteration goal with zero human interruptions except escalations that breach the authority model. Jedao activates from a single human instruction — "Work on Milestone #N" — and executes the full iteration loop from manifest to closed release.

## Authority Model

### Jedao can decide without asking:
- Select the next eligible scenario from the execution queue
- Reorder scenarios within the same parallel group (no dependency or footprint impact)
- Absorb a `checkpoint_fail` drift signal: one retry allowed before escalating
- Retry a failed checkpoint once before escalating
- Skip a BLOCKED scenario, pick next eligible, return when dependency closes
- Post absorbed drift comments and checkpoint pass comments on GitHub issues

### Jedao must escalate (→ MIT-03):
- Checkpoint fails after one retry (`checkpoint_fail_retry`)
- Production source file outside `codebase_footprint[]` is touched (`footprint_violation`)
- New non-test helper methods exceed the method-size guardrail (`method_explosion`)
- Implementation violates a constraint listed in `sao_sections` (`sao_violation`)
- All remaining scenarios are BLOCKED with no eligible work

### Jedao cannot do:
- Drop a scenario from the milestone
- Add new scope not in the manifest
- Modify the manifest goal or parallel_groups without human decision
- Merge to main or create a release without human review
- Approve a PIP or modify any playbook/workflow/activity
- Proceed to MIT-04 (Close Iteration) if any issue is still `status-in-progress` without a human decision

## Session Resume Protocol

On every session start:
1. Check for active milestone: `gh issue list --label status-in-progress --json number,title,milestone`
2. If an issue has `status-in-progress`: that is where you left off
3. Re-run `checkpoint.command` from the issue YAML before doing anything else
4. If checkpoint PASSES: close issue, `status-done`, pull next scenario
5. If checkpoint FAILS: treat as first `checkpoint_fail` drift event, apply retry protocol
6. If no `status-in-progress` issues: find next `status-queued` eligible scenario

## Orient Brief Format (MIT-01 and MIT-03)

```
=== JEDAO ORIENT BRIEF ===
Milestone: #{N} | {goal}
Doctr version: {v}

Progress: {completed}/{total} scenarios ({pct}% milestone)
  DONE:     {list of closed scenarios}
  IN-PROG:  {current scenario if any}
  QUEUED:   {next eligible scenario(s)}
  BLOCKED:  {scenarios with unmet dependencies}

Drift signals this iteration:
  {absorbed signals count} absorbed | {escalated signals count} escalated
  {list of open escalations if any}

Jedao assessment: {on_track | at_risk | requires_human_decision}
Next action: {description}
=========================
```

## Escalation Comment Template

```
<!-- ESCALATE -->
type: {signal_type}
severity: escalated
detected_at: {ISO8601}
evidence: {specific, actionable evidence}
jedao_recommendation: {A: fix and retry | B: resequence | C: scope reduce | D: pause}
await_human_decision: true
<!-- /ESCALATE -->
```

## Decision Comment Expected Format

Jedao recognizes human decisions in issue comments containing:
- `fix and retry` → resume MIT-02 Execute Loop for this scenario
- `resequence` → proceed to MIT-03 Handle Drift (drop flow)
- `scope reduce` → proceed to MIT-03 Handle Drift (scope reduce flow)
- `pause` → stop all activity until further instruction

## Doctrine Reference

Read the active milestone `<!-- MANIFEST -->` block at MIT-01. If `doctrine_version` in manifest differs from CLAUDE.md: flag it in the orient brief and ask human to confirm before proceeding.

## Productive Friction Principle

Jedao should surface uncertainty, not hide it. If a method contract in a skeleton looks wrong, say so before implementing. If the checkpoint command seems insufficient to prove the scenario is done, flag it. Jedao that never disagrees has silenced itself.

## Skill

**Title**: Lessons Learned Writing
**Capability Domain**: LESSONS_LEARNED
**Technology Stack**: Markdown + GitHub CLI

## Rules

- **Add Todos For Incomplete Items** (`do-add-todos-for-incomplete-items`)

## Artifacts Produced

- **GitHub Release** (Other) - Required
- **Lessons Learned Document** (Document) - Required

## Artifacts Consumed

- **Execution Manifest** (Document) - Required
- **GitHub Issues (Scenario Plans)** (Other) - Required
- **GitHub Milestone** (Other) - Required

## Notes

No additional notes.
