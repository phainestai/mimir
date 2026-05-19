# Activity: Produce Rough Estimates + AFP

**Activity ID**: 70
**Order**: 5
**Phase**: Elaboration
**Dependencies**: None

## Description

Produce Rough Estimates + AFP

## Guidance

## Purpose
Produce two parallel outputs from the Level 1 sizing:

1. **Internal token budget** — SP × K-token baselines × ECF × TCF → token estimates per sprint and project total. Used for sprint planning and AI cost forecasting.
2. **AFP (Adjusted Function Points)** — Σ FP × Stack Factor × Org Factor → the client-facing deliverable measure that feeds the quote. Populated in the Client Quote tab.

Both outputs come from the same Level 1 sizing. Token budget stays internal; AFP goes on the invoice.

## Prerequisites
- EST-03 complete (SP and FP totals per sprint in Scenario List)
- EST-04 complete (internal multiplier in Setup tab; Stack Factor + Org Factor in Client Quote tab)
- K-token baselines in Setup tab (SEED or CALIBRATED)

## Steps

### Step 1: Compute Internal Token Estimates Per Scenario

For each scenario in the Scenario List tab, compute using SP:

```
Raw Tokens (min)      = SP × K_min
Raw Tokens (expected) = SP × K_expected
Raw Tokens (max)      = SP × K_max
```

Where K values are the K-token-per-SP baselines from the Setup tab for the assigned size tier.

### Step 2: Apply Internal Risk Multiplier

```
Adjusted Tokens (min)      = Raw Tokens (min)      × Internal Multiplier × 0.85
Adjusted Tokens (expected) = Raw Tokens (expected) × Internal Multiplier
Adjusted Tokens (max)      = Raw Tokens (max)      × Internal Multiplier × 1.15
```

The 0.85/1.15 asymmetric adjustment preserves PERT shape after multiplier application.

### Step 3: Aggregate Token Budget to Sprint Level

In the Rough Estimates tab, for each sprint:
- Sum adjusted token estimates (min/expected/max) across all scenarios in that sprint
- Record sprint token budget (expected)
- Record sprint token range (min → max)

### Step 4: Derive Duration

```
Duration (days) = Sprint Token Budget (expected) / Daily Token Throughput
```

Where Daily Token Throughput = tokens the AI processes per working day (from Setup tab, typically 500K–2M depending on model and workflow).

For the project total, also compute with McConnell's schedule formula:
```
Duration (days) = 3.0 × (Total Effort Person-Months)^(1/3)
```
(For solo AI development, use sprint-by-sprint approach instead.)

### Step 5: Apply COCOMO Convergence Ranges

Adjust estimate ranges according to current phase:

| Phase | Min Multiplier | Max Multiplier |
|---|---|---|
| Initial Concept (vision only) | × 0.25 | × 4.0 |
| Approved Concept (scenarios exist) | × 0.5 | × 2.0 |
| Requirements Spec (≥80% complete) | × 0.67 | × 1.5 |
| Architecture (SAO.MD complete) | × 0.80 | × 1.25 |

Mark which phase applies.

### Step 6: Compute AFP (Client-Facing)

In the Client Quote tab, compute AFP using FP weights (not SP):

```
AFP = Σ FP × Stack Factor × Org Factor
```

Where:
- **Σ FP** = total FP from Scenario List tab (feature delivery FPs only)
- **Stack Factor** = from EST-04 Section B (Reference Table §4)
- **Org Factor** = from EST-04 Section B (Reference Table §5)

Add Sprint 0 overhead separately:
```
Sprint 0 AFP = BSP+DSP FP × Stack Factor × Org Factor
              = 15 FP × Stack × Org  (if bootstrap included)
```

Compute total quote:
```
Quote Total = (Feature AFP + Sprint 0 AFP) × $/FP
```

### Step 7: Populate Rough Estimates Tab

For each sprint, record:
- Sprint #, scenarios included, SP total, FP total
- Token budget: min / expected / max (in K tokens) — internal
- Duration: min / expected / max (in days) — internal
- Phase (convergence range applied)
- Status: SEED / CALIBRATED / BORROWED

For project total: total token budget, total duration, number of sprints, estimated completion date range.

### Step 8: Prepare Two Summaries

**Internal summary (for sprint planning):**
```
Token Budget:  P50 = ___ K tokens  (range: ___ to ___)
Duration:      ___ sprints / ___ days (range: ___ to ___)
Calibration:   {SEED / CALIBRATED}
```

**Client summary (for quote communication):**
```
Feature delivery:  ___ FP → AFP = ___  → $___
Sprint 0 setup:    15 FP → AFP = ___   → $___
─────────────────────────────────────────────
Total AFP: ___    Total Quote: $___
Stack Factor: ___    Org Factor: ___    $/FP: $___
```

Present both to user for review.

## Rules to Follow

### I. Always Show Ranges for Token Budget
Never present a single-point token estimate. Always present min/expected/max.

### II. AFP Is the Client Unit — Token Budget Is Not
The client receives AFP and the $ total. The token budget is an internal planning tool. Do not show K-token numbers in the client summary.

### III. Token Budget Is a Constraint, Not Just an Output
If expected token budget exceeds the team's capacity, that is a scope/priority conversation.

### IV. AFP Drives Billing — SP Does Not
Billing is always AFP × $/FP. Never invoice on SP or raw tokens.

### V. Label the Convergence Phase
Every token estimate must declare its convergence phase. An "initial concept" estimate with ±400% uncertainty is not a commitment.

## Success Criteria
- Token estimates (min/expected/max) computed for all scenarios (internal)
- AFP computed from FP × Stack Factor × Org Factor (client-facing)
- Sprint 0 overhead AFP included if bootstrap was flagged in EST-01
- Quote Total = AFP × $/FP computed
- COCOMO convergence phase labeled
- Rough Estimates tab and Client Quote tab of ESTIMATION_TEMPLATE.xlsx complete
- Internal summary and client summary prepared and reviewed

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Estimation Reference Table** (Document, Required) — produced by Calibrate Reference Stories (#67).
- **Estimation Template (Excel)** (Document, Required) — produced by Size Scenarios (Level 1 SWAG) (#68).
- **Lessons Learned Document** (Document, Optional) — produced by Close Iteration (#118).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **Estimation Reference Table** (Document) - Required
- **Estimation Template (Excel)** (Document) - Required
- **Lessons Learned Document** (Document) - Optional

## Notes

No additional notes.
