# Activity: Human Acceptance Review

**Activity ID**: 111
**Order**: 8
**Phase**: Gate
**Dependencies**: Predecessor: Activity 110 (Publish to GitHub)

## Description

Human Acceptance Review

## Guidance

## Purpose
Obtain explicit human approval before Jedao begins MIT execution. This is the final quality gate. The human reviews everything produced in PIT and decides: go or no-go.

**This is a mandatory STOP. Do not proceed to PIT-09 without explicit human approval.**

## Prerequisites
- All scenario skeletons committed
- Execution manifest YAML finalized
- GitHub Milestone + Issues published

## Steps

### Step 1: Present the Review Checklist
Present the following to the human for review:

**Skeleton Review (per scenario):**
- [ ] Method contracts (signatures + docstrings) are architecturally sound
- [ ] Type hints are complete and correct
- [ ] Test stubs cover the right assertions (not just happy path)
- [ ] Skeletons fail with `NotImplementedError`, not import/syntax errors

**Manifest Review:**
- [ ] Conflict map correctly identifies all shared files
- [ ] Parallel groups are safe (no hidden conflicts)
- [ ] Time budgets are honest (not optimistic)
- [ ] Checkpoint commands will definitively prove done when green
- [ ] Drift thresholds match current doctrine

**GitHub Review:**
- [ ] Milestone goal sentence is clear and bounded
- [ ] All issues have correct labels and dependency references
- [ ] BPE-01 plans in issue bodies are complete and actionable

### Step 2: Present the Plan Summary
Show:
```
Iteration: {goal}
Scenarios: {N} | Critical path: {duration} min | Parallel groups: {A,B,C}

S1 [{group}] {title} — {budget}min — checkpoint: {command}
S2 [{group}] {title} — {budget}min — checkpoint: {command}

Conflict map: {file} → [S1, S2] (serialized)
No-conflict pairs: S1/S3, S2/S3 (parallel)

Drift thresholds: absorbed <120% | escalated >=200% or unexpected files
```

### Step 3: Await Human Decision
Human options:

**GO** — "Approved for MIT execution"
- Record approval timestamp
- Proceed to PIT-09

**NO-GO: Skeleton issue on S{N}**
- Return to PIT-04 for that scenario only
- Re-run BPE-01, recreate skeleton, recommit
- Return to PIT-08 after fix

**NO-GO: Re-sequencing needed**
- Return to PIT-05 to revise conflict map / parallel groups
- Update manifest and GitHub Milestone description
- Return to PIT-08 after fix

**NO-GO: Drop S{N}**
- Remove from manifest YAML
- Close GitHub Issue with label `won't-fix` and comment "Dropped from iteration in PIT-08 review"
- Update Milestone description
- Return to PIT-08 with reduced scope

### Step 4: Record Approval
Once human approves:
```bash
gh issue comment {first_issue_number} --body "PIT-08 approved by {username} at {timestamp}. MIT execution authorized."
```

## Success Criteria
- All checklist items reviewed by human
- Explicit go/no-go decision recorded
- If go: approval comment on GitHub
- If no-go: issues addressed and review repeated

## Rules
- Never skip this gate regardless of time pressure
- A hasty go is worse than a delayed start
- If human is unavailable: pause PIT, do not proceed to MIT

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
