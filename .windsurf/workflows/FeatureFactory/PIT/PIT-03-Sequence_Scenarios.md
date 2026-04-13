# Activity: Sequence Scenarios

**Activity ID**: 106
**Order**: 3
**Phase**: Planning
**Dependencies**: Predecessor: Activity 105 (Select Iteration Goal)

## Description

Sequence Scenarios

## Guidance

## Purpose
Build a rough conflict-aware execution sequence before running BPE-01. This is an area-level estimate — not file-level. PIT-05 will refine with actual file lists from skeleton commits. The goal here is to avoid obviously serial work being scheduled in parallel.

## Prerequisites
- Iteration goal and selected scenarios from PIT-02
- Orient summary (conflict hotspot files) from PIT-01

## Steps

### Step 1: Map Scenarios to Codebase Areas
For each selected scenario, identify the codebase areas it is likely to touch (area = module/app, not individual files):

| Scenario | Likely Areas |
|---|---|
| S1: Export workflow as JSON | `mcp_integration/`, `methodology/services/` |
| S2: Import workflow from JSON | `mcp_integration/`, `methodology/services/` |
| S3: Add Agent CRUD to web UI | `methodology/views/`, `methodology/templates/` |

### Step 2: Build Conflict Matrix
For each pair of scenarios, mark conflict if they share any area:

| | S1 | S2 | S3 |
|---|---|---|---|
| S1 | — | CONFLICT | ok |
| S2 | CONFLICT | — | ok |
| S3 | ok | ok | — |

### Step 3: Check Against Hotspot Files
If any scenario touches a known hotspot file (from PIT-01 orient summary), flag it:
```
S1 touches mcp_integration/ — hotspot: tools.py appears here. Serialize S1 before S2 regardless of conflict matrix.
```

### Step 4: Assign Parallel Groups
Group non-conflicting scenarios together. Conflicting scenarios must be serialized:

```
Group A: [S1]           ← starts first (hotspot risk: serialize with S2)
Group B: [S3]           ← can run in parallel with Group A
Group C: [S2]           ← depends on S1 (conflict)
```

### Step 5: Produce Rough Critical Path
```
Critical path: A(S1) → C(S2)
Parallel:      B(S3) runs alongside A
Estimated total: 3 hours (longest path: S1 + S2)
```

### Step 6: Validate Against Doctrine
- Is estimated total duration within iteration target? If not: drop lowest-priority scenario.
- Does any scenario have an unresolved external dependency? Mark it as `blocked` and remove from this iteration.

## Success Criteria
- All scenarios assigned to a parallel group (A, B, C…)
- Conflicting scenarios are serialized
- Hotspot-adjacent scenarios are flagged
- Rough critical path duration computed
- Duration fits iteration target (or scope reduced)

## Notes
This is orientation-level sequencing. Expect PIT-05 to adjust group assignments after skeleton commits reveal exact file-level conflicts. The value here is catching obvious parallelism mistakes before investing in BPE-01.

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
