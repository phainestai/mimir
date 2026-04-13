# Activity: Prepare Jedao Brief

**Activity ID**: 112
**Order**: 9
**Phase**: Handoff
**Dependencies**: Predecessor: Activity 111 (Human Acceptance Review)

## Description

Prepare Jedao Brief

## Guidance

## Purpose
Verify CLAUDE.md iteration protocol is current, then hand off to Jedao with enough context for autonomous MIT execution. The human activates MIT with a single instruction.

## Prerequisites
- Human approval from PIT-08
- CLAUDE.md with iteration protocol section
- GitHub Milestone published

## Steps

### Step 1: Verify CLAUDE.md Iteration Protocol
Read the `## Iteration Protocol` section of CLAUDE.md. Verify it matches the current doctrine version from the manifest:

Required sections in CLAUDE.md:
- `## Iteration Protocol` — the step-by-step loop Jedao follows
- `## Session Resume Protocol` — what to do when session restarts mid-iteration
- `## Escalation Thresholds` — absorbed vs. escalated criteria (must match manifest `drift_thresholds`)

If any section is missing or outdated:
1. Update CLAUDE.md with current values from manifest `drift_thresholds`
2. Commit: `docs(claude): update iteration protocol to doctrine v{N}`

**CLAUDE.md Iteration Protocol template:**
```markdown
## Iteration Protocol

When tasked with "Work on Milestone #{N}":
1. Read milestone description — parse `<!-- MANIFEST -->` YAML block
2. Verify all `status-queued` issues exist for each scenario in manifest
3. Find next eligible scenario: `status-queued` + all dependencies `status-done`
4. Apply `status-in-progress` label
5. Follow BPE-02 → BPE-05 to fill the skeleton
6. Monitor files touched vs `codebase_footprint` in issue `<!-- SCENARIO -->` block
7. Run `checkpoint.command` from issue YAML
8. If PASS: close issue, comment actual_duration, apply `status-done`, go to step 3
9. If FAIL: go to drift handling

## Drift Handling
- time_overrun < 120%: log `<!-- DRIFT absorbed -->` comment, continue
- checkpoint fail (first time): retry once with targeted fix
- time_overrun >= 200% OR unexpected files OR second checkpoint fail: post `<!-- ESCALATE -->` comment, STOP, await human

## Session Resume Protocol
On every session start for an active iteration:
1. Read the active milestone
2. Find any issue with `status-in-progress` — that is where you left off
3. Re-run `checkpoint.command` first
4. If PASS: close issue, continue. If FAIL: treat as drift.

## Authority Model
Can decide without asking: reorder within same parallel group, absorb drift below threshold, retry once
Must escalate: checkpoint fail after retry, unexpected files, time >= 2x budget
Cannot do: drop scenario, add scope, merge to main, create release without human review
```

### Step 2: Post Jedao Activation Note
```bash
gh issue comment {first_issue_number} \
  --body "$(cat <<'EOF'
## Jedao Brief

Iteration: {goal}
Doctrine version: {version}
Manifest: docs/plans/iterations/ITER-{slug}.yaml

Orient context from lessons learned:
{orient_summary_from_PIT-01}

Watch for:
{top_risk_1}
{top_risk_2}

Activation: Human will task Jedao with "Work on Milestone #{N}"
EOF
)"
```

### Step 3: Final Pre-Flight
```bash
# Verify branch is clean
git status
# Expected: clean working tree (all skeletons committed)

# Verify milestone is open with correct issue count  
gh milestone view {N}
# Expected: {N} open issues, 0% complete

# Verify CLAUDE.md is committed
git log --oneline -3
```

### Step 4: Signal Ready
Report to human:
```
PIT complete. Ready for MIT execution.
Milestone #{N}: {goal}
Scenarios: {N} ({groups})
Critical path: {duration} min

Activate with: "Work on Milestone #{N}"
```

## Success Criteria
- CLAUDE.md iteration protocol section is current with doctrine version in manifest
- Activation note posted on GitHub
- Branch is clean (all skeletons committed)
- Human knows the single activation instruction

## Notes
After PIT-09 completes, PIT is done. The next human action is simply: "Work on Milestone #N". Jedao reads everything else from CLAUDE.md and the manifest.

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
