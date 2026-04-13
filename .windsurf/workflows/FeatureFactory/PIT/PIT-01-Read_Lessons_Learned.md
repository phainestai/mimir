# Activity: Read Lessons Learned

**Activity ID**: 104
**Order**: 1
**Phase**: Orientation
**Dependencies**: None

## Description

Read Lessons Learned

## Guidance

## Purpose
Orient the planning session by extracting patterns from past iterations before any planning decisions are made. This is the AI's primary O1 (Observe) input for the composite planning session.

## Prerequisites
- Access to `docs/lessons_learned/` directory
- If no files exist: first iteration — skip this activity and note it for PIT-02

## Steps

### Step 1: Locate Iteration Files
Read all files in `docs/lessons_learned/` sorted by filename descending (newest first). Take the most recent 3–5 files.

File naming convention: `ITER-YYYYMMDD-HHmm-goal-slug.md`

### Step 2: Parse YAML Blocks
For each file, extract the `<!-- LEARNING -->` YAML front-matter block:

```yaml
<!-- LEARNING -->
milestone: 15
goal: "Ship Workflow Export + Import via MCP"
velocity_ratio: 0.75
scenarios_completed: 3
scenarios_abandoned: 1
dominant_drift_cause: test_failure
conflict_map_accuracy: 0.60
files_with_unexpected_conflicts:
  - mcp_integration/tools.py
<!-- /LEARNING -->
```

### Step 3: Compute Trends
Across all parsed files compute:
- **velocity_ratio trend**: improving / stable / degrading
- **dominant_drift_causes**: rank by frequency across iterations
- **conflict hotspot files**: files appearing in `files_with_unexpected_conflicts` more than once
- **conflict_map_accuracy trend**: are footprint predictions getting more accurate?

### Step 4: Extract PIP Candidates
From each file's `## What to Change` section, collect any `- [ ] PIP:` items that are still unchecked.

### Step 5: Produce Orient Summary
Write a brief orient summary (5–10 lines) to carry forward into PIT-02:

```
Orient Summary:
- Last 3 velocity ratios: 0.75, 0.80, 0.67 — degrading
- Top drift cause: test_failure (3/3 iterations)
- Conflict hotspots: mcp_integration/tools.py (2x), methodology/services/workflow_service.py (1x)
- Conflict map accuracy: 60% — footprint estimation is loose
- Open PIP candidates: 2 unchecked items
- Watch for: MCP integration tests, tools.py conflicts
```

## Success Criteria
- Orient summary produced and available for PIT-02
- Conflict hotspot files identified (or noted as "none — first iteration")
- Dominant drift causes ranked
- Open PIP candidates listed

## Notes
If `docs/lessons_learned/` does not exist or is empty: create the directory and produce orient summary: "First iteration — no historical patterns. All baseline values unknown. Conflict map accuracy will be 0% until first iteration closes."

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
