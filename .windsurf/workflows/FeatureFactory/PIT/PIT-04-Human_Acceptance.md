# Activity: Human Acceptance

**Activity ID**: 111
**Order**: 4
**Phase**: Construction
**Dependencies**: Predecessor: Activity 110 (Publish)

## Description

Human Acceptance

## Guidance

## Purpose
Verify CLAUDE.md iteration protocol is current, obtain explicit human approval, and deliver the single activation instruction for MIT. This is the final gate — do not proceed without explicit human go.

**STOP — mandatory human gate.**

## Prerequisites
- All skeleton commits on iteration branch
- Execution manifest YAML finalized (ITER-*.yaml)
- GitHub Milestone + Issues published (PIT-03 complete)

## Steps

### Step 1: Verify CLAUDE.md Iteration Protocol
Read the `## Iteration Protocol`, `## Drift Handling`, `## Session Resume Protocol`, and `## Authority Model` sections of CLAUDE.md. Verify they match `doctrine_version` in the manifest.

Required content in CLAUDE.md (must be present and current):

**Iteration Protocol** — must reference reading the `<!-- MANIFEST -->` block, finding next eligible `status-queued` issue, following BPE-02 → BPE-05 to fill the skeleton.

**Drift Handling** — must match manifest `drift_thresholds` exactly:
- Absorbed: `checkpoint_fail` (retry once)
- Escalated: `footprint_violation`, `method_explosion`, `sao_violation`, `checkpoint_fail_after_retry`

**Session Resume Protocol** — must say: find `status-in-progress` issue → re-run checkpoint → PASS: close and continue / FAIL: treat as first `checkpoint_fail`.

**Authority Model** — must list what MIT can decide autonomously vs. must escalate.

If any section is missing or its drift thresholds don't match the manifest: update CLAUDE.md and commit:
```bash
git commit -m "docs(claude): sync iteration protocol to doctrine v2.0"
```

### Step 2: Present Review Summary
Present the following to the human:

```
=== PIT COMPLETE — REVIEW REQUIRED ===

Iteration: {iteration_goal}
Scenarios: {N} | Groups: {A,B,...} | Critical path: {duration}

{for each scenario:}
  S{N} [{group}] {title}
    Checkpoint: {command}
    Footprint:  {N} files
    Depends on: {deps or "none"}

Conflict map:
  {file} → [{S_N}, {S_M}] (serialized)
  {or "No conflicts — all scenarios parallel"}

Drift signals that escalate (no time budget):
  footprint_violation  — file outside declared footprint
  method_explosion     — unplanned public method vs skeleton
  sao_violation        — SAO.md compliance check fails
  checkpoint_fail ×2   — retry didn't fix it

CLAUDE.md protocol: {current / updated at {timestamp}}

Activate MIT with: "Work on Milestone #{N}"
======================================
```

### Step 3: Await Human Decision
Human options:

**GO** — respond with "Approved" or "Work on Milestone #{N}"
- Record approval:
```bash
gh issue comment {first_issue_number} --body "PIT approved at {timestamp}. MIT authorized."
```

**NO-GO: skeleton issue on S{N}** — return to PIT-02 for that scenario only: re-run BPE-01, recreate skeleton, recommit. Return to PIT-04 after fix.

**NO-GO: re-sequencing needed** — return to PIT-02 Step 9–10 to revise conflict map and parallel groups. Update manifest and Milestone. Return to PIT-04.

**NO-GO: drop S{N}** — close the GitHub Issue (`won't-fix`), remove from manifest YAML, update Milestone description. Return to PIT-04 with reduced scope.

## Success Criteria
- CLAUDE.md iteration protocol is current (drift thresholds match manifest)
- Explicit human go/no-go decision obtained
- If go: approval comment posted on GitHub
- Human has the activation instruction: "Work on Milestone #{N}"

## Rules
- Never skip this gate regardless of time pressure
- If human is unavailable: pause PIT, do not proceed to MIT
- A no-go with a fix takes minutes; a bad MIT run wastes an hour

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Execution Manifest** (Document, Required) — produced by Contract (#105).
- **GitHub Issues (Scenario Plans)** (Other, Required) — produced by Publish (#110).
- **GitHub Milestone** (Other, Required) — produced by Publish (#110).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **Execution Manifest** (Document) - Required
- **GitHub Issues (Scenario Plans)** (Other) - Required
- **GitHub Milestone** (Other) - Required

## Notes

No additional notes.
