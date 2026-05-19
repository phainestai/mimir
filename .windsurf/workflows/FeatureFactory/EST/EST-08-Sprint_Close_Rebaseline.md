# Activity: Sprint Close & Rebaseline

**Activity ID**: 73
**Order**: 8
**Phase**: Elaboration
**Dependencies**: None

## Description

Sprint Close & Rebaseline

## Guidance

## Purpose
At the end of each sprint, collect actual token consumption, compute Velocity Factor (VF = actual FP delivered / estimated AFP), update K-token baselines, calibrate $/FP from actuals, and re-run Monte Carlo. This loop is the engine of estimate improvement and pricing calibration across the project.

**If scope changed during the sprint** (requirements modified, feature added/removed): run BPE-08 (Process Change Request) first. Do not blend scope-change overruns into calibration data.

## Prerequisites
- Sprint completed (or partially completed with clear scope boundary)
- Token consumption data available from AI model billing/usage logs
- Scenario completion status recorded
- No unresolved scope changes (BPE-08 completed if needed)

## Steps

### Step 1: Collect Sprint Actuals

For each scenario attempted in the sprint, record:
- Scenario ID
- Planned SP, planned FP weight
- Planned tokens (expected from estimate)
- Actual tokens consumed (from AI usage logs)
- Actual API cost ($) for this sprint
- Status: DONE / PARTIAL / BLOCKED / DEFERRED
- Notes (scope changes, surprises — flag any BPE-08 items)

Record in the Scenario List tab, "Sprint N Actuals" columns.

### Step 2: Compute Velocity Factor (Internal — Token-Based)

For each completed scenario:
```
Token VF = Actual Tokens / Estimated Tokens (expected)
```

Sprint-level VF:
```
Sprint Token VF = Σ Actual Tokens (completed) / Σ Estimated Tokens (same scenarios)
```

| VF Range | Meaning | Action |
|---|---|---|
| < 0.8 | AI performed faster than estimated | Reduce K_expected; tighten K_min |
| 0.8 – 1.2 | On target | Minor adjustment only |
| 1.2 – 1.5 | Slower than expected | Increase K_expected; widen K_max |
| > 1.5 | Significant overrun | Investigate root cause before adjusting |

### Step 3: Update K-Token Baselines

For each size tier with ≥ 1 completed actual:
1. Append actual to running history in Reference Table §11
2. Recompute: K_expected = weighted average last 3–5 actuals; K_min = 10th pct; K_max = 90th pct
3. Update Setup tab K values
4. Calibration status: 1 actual → SEED; 2 actuals → BORROWED; ≥3 actuals → CALIBRATED

### Step 4: Calibrate $/FP (Client Pricing — Critical)

Compute the actual cost per delivered FP for this sprint:

```
$/FP_actual_sprint = Actual API Cost ($) / Σ FP (completed scenarios)
```

Update the running $/FP calibration in Setup tab:
```
$/FP_calibrated = weighted average of $/FP_actual across last 3–5 sprints
```

Update $/FP in Client Quote tab with the calibrated rate. Change calibration status from SEED → CALIBRATED once 3+ sprint actuals are available.

**This is the feedback loop that keeps the AFP pricing model honest:** as the team gets faster (PAF improves), $/FP drops; as scope grows harder, $/FP rises. The client quote rate tracks reality, not seed assumptions.

### Step 5: Compute AFP VF (Client-Facing — Delivery Performance)

```
AFP VF = Σ FP (delivered this sprint) / AFP (estimated for this sprint in Client Quote)
```

| AFP VF | Meaning |
|---|---|
| > 1.0 | Delivered more FP value than quoted — favorable |
| = 1.0 | On target |
| < 1.0 | Delivered less FP value than quoted — investigate |

Record AFP VF in Reference Table sprint actuals section. This is the metric to show the client as a delivery health indicator.

### Step 6: Re-Rate ECF/TCF (If Warranted)

Review factors that may have changed:
- E6 (requirements stability) — did requirements churn this sprint?
- A3 (hallucination risk) — did AI quality improve as it learned the codebase?
- A2 (prompt maturity) — did new prompts prove more efficient?

Update ECF/TCF tabs if any factor changes by ≥ 1 point. Recompute internal combined multiplier.

### Step 7: Update Remaining Scenario Estimates

For remaining (not yet started) scenarios:
- Apply updated K baselines (token budget)
- If a class of scenarios ran significantly over/under, apply Token VF as correction factor
- Do not touch FP weights — FP is a client commitment, not an internal variable

### Step 8: Re-Run Monte Carlo

Run EST-07 over remaining scenarios only:
- Completed scenarios: replace with actuals (fixed values, no simulation)
- Remaining scenarios: re-simulate with updated PERT distributions
- Output: new P50/P80/P95 for token budget, duration, AFP, and $

Compare to previous MC_SNAPSHOT:
- Is P80 completion date improving sprint-over-sprint? (healthy)
- Is P80 drifting outward? (scope growth or systematic under-estimation — investigate)

Save new `docs/plans/MC_SNAPSHOT_{DATE}.md`.

### Step 9: Update Reference Table

Append to `docs/plans/REFERENCE_TABLE.md` §11:

```
## Sprint {N} Actuals — {Date}

| Scenario | Size | SP | FP | Est. Tokens | Actual Tokens | Token VF | Est. AFP | Actual FP | AFP VF |
|---|---|---|---|---|---|---|---|---|---|
| FOB-X-Y-01 | M | 2 | 2 | 110K | 127K | 1.15 | 2 AFP | 2 FP | 1.0 |

$/FP this sprint: $___ (API cost $___  / ___ FP delivered)
$/FP calibrated: $___  (was: $___) — status: SEED / CALIBRATED
Updated K baselines: {list tiers updated}
Combined multiplier: {value} (was: {previous})
```

### Step 10: Publish Sprint Report

```
Sprint {N} Estimation Report — {Date}

Completed: {N} scenarios ({SP} SP / {FP} FP), {actual K}K tokens
Planned:   {N} scenarios ({SP} SP / {FP} FP), {planned K}K tokens
Token VF:  {value}    AFP VF: {value}

API Cost This Sprint: $___    $/FP This Sprint: $___    $/FP Calibrated: $___

Deferred: {list deferred scenarios and reason}

Revised Forecast (remaining work):
  Internal:  P50 = {K tokens / days}  P80 = {K tokens / days}
  Client:    P80 AFP = ___   →  $___

Token Budget Status:
  Consumed to date: {K} tokens
  Remaining P80:    {K} tokens
  Total P80:        {K} tokens ({% of original P80})

Next sprint: {N} scenarios ({SP} SP / {FP} FP)
```

Present to user/stakeholder. Save to `docs/plans/`.

## Rules to Follow

### I. Actuals Are Sacred
Never retroactively adjust planned estimates to match actuals. Both must be preserved as separate columns.

### II. BPE-08 Before Calibration Data
Any scope change must be processed through BPE-08 first. Do not blend scope-change overruns into K-token calibration — they will corrupt future baselines.

### III. $/FP Updates Require ≥ 3 Sprints to CALIBRATE
1–2 sprints → BORROWED rate. 3+ sprints → CALIBRATED. Do not price future work off a single sprint anomaly.

### IV. FP Weights Are Fixed — SP Can Move
FP weights represent the client-committed value per scenario. Do not retroactively change FP weights after quoting. SP values and K-token baselines are internal calibration variables and can be updated freely.

### V. Investigate AFP VF < 0.8
A sprint where significantly less FP was delivered than quoted is a scope or quality signal. Before re-quoting remaining work, understand why: deferred features? Failed DoD? Unexpected complexity?

### VI. The 20-Data-Point Threshold
Monte Carlo achieves MMRE ~20% only after ~20 data points (ACM SAC 2021). Before that, keep PERT ranges wide.

## Success Criteria
- Sprint actuals collected (tokens, FP delivered, API cost)
- Token VF and AFP VF computed
- K-token baselines updated in Setup tab
- $/FP calibrated from actuals; status updated (SEED → CALIBRATED after 3 sprints)
- Reference Table §11 appended
- ECF/TCF re-rated if warranted
- Remaining scenario token estimates updated
- Monte Carlo re-run, new P50/P80/P95 for tokens and AFP/$
- MC_SNAPSHOT saved, sprint report produced and reviewed
- Client Quote tab $/FP updated

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Estimation Reference Table** (Document, Required) — produced by Calibrate Reference Stories (#67).
- **Estimation Template (Excel)** (Document, Required) — produced by Size Scenarios (Level 1 SWAG) (#68).
- **Execution Manifest** (Document, Required) — produced by Contract (#105).
- **GitHub Release** (Other, Required) — produced by Close Iteration (#118).
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
- **Execution Manifest** (Document) - Required
- **GitHub Release** (Other) - Required
- **Lessons Learned Document** (Document) - Optional

## Notes

No additional notes.
