# Activity: Human Decision Sync

**Activity ID**: 116
**Order**: 4
**Phase**: Course Correction
**Dependencies**: Predecessor: Activity 115 (Handle Drift)

## Description

Human Decision Sync

## Guidance

## Purpose
Present the escalated scenario state to the human as a compact orient brief. Await an explicit decision comment. Record the decision and hand off to MIT-05 if replanning is needed, or return to MIT-02 if retry is authorized.

**This activity is only entered from MIT-03 when severity = ESCALATED.**

## Prerequisites
- Escalated issue has `<!-- ESCALATE -->` comment and `drift-escalated` label
- Jedao has stopped execution of the affected scenario

## Steps

### Step 1: Compose Orient Brief
Present to human:

```
=== ESCALATION: S{N} — {scenario title} ===

Signal type: {signal_type}
Evidence:    {specific evidence}
Elapsed:     {N} min / {budget} min budget ({pct}%)
Progress:    {N}/{total} scenarios complete ({milestone_pct}% milestone)
Time left:   {target_duration} – {elapsed_total} = {remaining} min

Open drift signals (this iteration):
  - #{issue}: {signal} at {time}

Jedao recommendation: {recommendation}

Your options:
  A) Fix and retry S{N}: authorize Jedao to attempt a targeted fix
  B) Resequence: drop S{N} from this iteration (scenario stays in backlog)
  C) Scope reduce: trim S{N} scope, redefine checkpoint
  D) Pause iteration: stop MIT until further notice
```

### Step 2: Wait for Human Decision
Jedao waits. Do not take further action on the affected scenario until a decision comment appears on the issue.

Poll for human comment:
```bash
gh issue view {issue_number} --comments --json comments | \
  jq '.comments[-1].body'
```

Human decision comment must contain one of: `fix and retry`, `resequence`, `scope reduce`, `pause`.

### Step 3: Parse and Record Decision
```bash
gh issue comment {issue_number} --body "<!-- DECISION -->
decision: {fix_and_retry | resequence | scope_reduce | pause}
decided_by: {username}
decided_at: {timestamp}
notes: {any human notes}
<!-- /DECISION -->"
```

### Step 4: Route to Next Activity

**fix and retry → MIT-02:**
```bash
gh issue edit {issue_number} --remove-label "drift-escalated" --add-label "status-in-progress"
```
Return to MIT-02, Step 2 (fill skeleton) with escalation context.

**resequence → MIT-05:**
Proceed to MIT-05 to remove scenario from manifest and close issue.

**scope reduce → MIT-05:**
Proceed to MIT-05 to update scenario scope in manifest and issue YAML.

**pause:**
```bash
gh issue comment {issue_number} --body "MIT paused by human decision at {timestamp}. Awaiting further instruction."
```
Stop all activity. Do not resume until explicit human instruction.

## Success Criteria
- Orient brief presented with full context (signal type, evidence, progress, options)
- Human decision explicitly recorded as `<!-- DECISION -->` comment
- Routing to correct next activity based on decision
- No autonomous action taken while awaiting human decision

## Rules
- Never assume the human’s decision — wait for explicit comment
- Present orient brief once; do not repeat unless asked
- Do not touch code or GitHub state while awaiting decision

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
