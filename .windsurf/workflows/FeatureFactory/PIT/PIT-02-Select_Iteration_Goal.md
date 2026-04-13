# Activity: Select Iteration Goal

**Activity ID**: 105
**Order**: 2
**Phase**: Orientation
**Dependencies**: Predecessor: Activity 104 (Read Lessons Learned)

## Description

Select Iteration Goal

## Guidance

## Purpose
Define what this iteration will accomplish. The iteration goal is the single sentence that bounds all subsequent planning decisions. This is a **human decision point** — the AI prepares the options, the human decides.

## Prerequisites
- Orient summary from PIT-01
- Access to GitHub Issues with label `backlog`

## Steps

### Step 1: Retrieve Backlog Candidates
List GitHub Issues with label `backlog`:
```bash
gh issue list --label backlog --json number,title,labels,body --limit 20
```
Filter to issues that are sized for ~1 hour execution (labels: `easy` or `medium`). List extras with `hard` label as candidates only if they can be decomposed.

### Step 2: Apply Iteration Constraints
For each candidate scenario, check:
- Does it fit the 1-hour doctrine? (scope is bounded, no unknown dependencies)
- Are there known conflicts with hotspot files from PIT-01 orient summary? Flag these.
- Does it depend on another backlog scenario that isn’t yet implemented?

### Step 3: Propose Goal Options
Present human with 2–3 iteration goal options. For each option:
- Goal sentence: `[Verb] [noun phrase] so that [success signal]`
- Scenarios included: list GitHub issue numbers + titles
- Estimated scope: N scenarios, ~N hours
- Risk flag if hotspot files are involved

Example:
```
Option A: Ship MCP workflow export+import so that AI-to-AI handoff works (2 scenarios, ~2h, hotspot risk: tools.py)
Option B: Add Agent CRUD to web UI so that agents are manageable via browser (3 scenarios, ~3h, no hotspot risk)
```

### Step 4: Human Selects Goal
**STOP. Present options to human. Do not proceed until human explicitly selects a goal and approves the scenario list.**

Record:
- `iteration_goal`: the selected goal sentence
- `selected_scenarios`: list of GitHub issue numbers
- `human_approved_at`: timestamp

### Step 5: Scope Boundary Note
Explicitly list what is NOT in scope for this iteration. This prevents scope creep during MIT execution.

## Success Criteria
- Single goal sentence defined
- 2–5 scenarios selected from backlog
- Each scenario fits ~1-hour execution cadence
- Scope boundary (in/out) documented
- Human explicitly approved before proceeding to PIT-03

## Rules
- Never select more scenarios than can be completed in the target duration
- If orient summary shows degrading velocity: reduce scope, not increase
- Hard scenarios must be decomposed into sub-scenarios before selection

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
