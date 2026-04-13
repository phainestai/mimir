# Activity: Course Correct Manifest

**Activity ID**: 117
**Order**: 5
**Phase**: Course Correction
**Dependencies**: Predecessor: Activity 116 (Human Decision Sync)

## Description

Course Correct Manifest

## Guidance

## Purpose
Apply the human’s decision to the execution manifest and GitHub state. Re-validate the dependency chain for remaining scenarios. Resume MIT-02 with the updated plan.

**Only entered when human decision in MIT-04 requires manifest changes (resequence or scope reduce).**

## Prerequisites
- Human decision recorded in `<!-- DECISION -->` comment
- Decision is: `resequence` or `scope_reduce`

## Steps

### Decision: Resequence (Drop Scenario)

**Step 1: Close the GitHub Issue**
```bash
gh issue close {issue_number} \
  --comment "Dropped from iteration by human decision (MIT-05). Scenario returns to backlog label."
gh issue edit {issue_number} \
  --add-label "backlog" \
  --remove-label "status-in-progress,drift-escalated,parallel-group-{X}"
```

**Step 2: Update Milestone Manifest**
Read current milestone description. Remove the dropped scenario from `parallel_groups` and `scenarios` in the `<!-- MANIFEST -->` block. Update `iteration.target_duration_minutes` to subtract the dropped scenario’s budget.

```bash
# Update milestone description with revised YAML
gh api repos/{owner}/{repo}/milestones/{N} \
  --method PATCH \
  --field description="{updated_manifest_description}"
```

**Step 3: Update Local Manifest File**
```bash
# Update docs/plans/iterations/ITER-*.yaml
# Remove scenario entry, update parallel_groups, update target_duration_minutes
git add docs/plans/iterations/
git commit -m "chore(mit): drop S{N} from manifest — human decision MIT-05"
```

**Step 4: Re-validate Dependency Chain**
Check remaining scenarios: does any depend on the dropped scenario?
- If yes: those scenarios are now unblocked OR broken (depending on whether the dependency was structural)
- Log: "S{dep_scenario} depended on dropped S{N} — {unblocked/now invalid}"
- If now invalid: repeat MIT-04 for the dependent scenario immediately

---

### Decision: Scope Reduce

**Step 1: Update Issue YAML**
Edit the issue body to update the `<!-- SCENARIO -->` block:
- Reduce `codebase_footprint[]` to the trimmed scope
- Update `checkpoint.command` to match reduced scope
- Update `time_budget_minutes` to reflect reduced work

```bash
# Edit issue body via API
gh issue edit {issue_number} --body "{updated_body_with_revised_SCENARIO_block}"
```

**Step 2: Re-check Conflict Map**
With reduced footprint, does this scenario still conflict with others?
- If conflict resolved: potentially unblock parallelization
- Update `parallel_groups` in manifest if changed

**Step 3: Update Local Manifest**
```bash
git add docs/plans/iterations/
git commit -m "chore(mit): scope reduce S{N} — human decision MIT-05"
```

**Step 4: Reset Scenario for Retry**
```bash
gh issue edit {issue_number} \
  --remove-label "drift-escalated" \
  --add-label "status-queued"
gh issue reopen {issue_number}  # if it was closed
```

---

### Final Step (both decisions)

**Validate and Resume:**
- Verify remaining scenarios form a valid, executable sequence
- Log updated queue state
- Return to MIT-02 for next eligible scenario

```
=== MANIFEST UPDATED ===
Dropped/Reduced: S{N}
Remaining: {N} scenarios
Updated critical path: {duration} min
Next: S{N} [{group}] {title}
=======================
```

## Success Criteria
- GitHub issue updated (closed or scope-reduced)
- Milestone `<!-- MANIFEST -->` YAML updated
- Local manifest YAML committed
- Dependency chain re-validated
- Execution ready to resume from MIT-02

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
