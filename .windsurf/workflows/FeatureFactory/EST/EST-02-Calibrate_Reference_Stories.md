# Activity: Calibrate Reference Stories

**Activity ID**: 67
**Order**: 2
**Phase**: Elaboration
**Dependencies**: None

## Description

Calibrate Reference Stories

## Guidance

## Purpose
Define concrete reference stories at each T-shirt size, assign K-token baselines (tokens per story point) to anchor token budget estimates, and assign FP weights to anchor client-facing AFP pricing. This calibration baseline governs both internal estimates and client quotes for the entire project.

## Prerequisites
- EST-01 complete
- Reference Table accessible (or being created for first time)

## Steps

### Step 1: Define Reference Stories

A reference story is a concrete, completed BDD scenario that the team agrees represents a given size. Every future scenario is sized *relative* to these anchors.

Populate the Setup tab of ESTIMATION_TEMPLATE.xlsx with reference stories:

| Size | SP (internal) | FP weight (client) | Example Reference Story | K Tokens (min) | K Tokens (exp) | K Tokens (max) |
|------|:-------------:|:------------------:|-------------------------|---------------:|---------------:|---------------:|
| XS   | 0.5           | 0.5                | Read-only list view, no filtering, single model | — | — | — |
| S    | 1             | 1                  | Single CRUD operation, one model, 3–5 scenarios | — | — | — |
| M    | 2             | 2                  | Feature with 2 models, service layer, 6–10 scenarios | — | — | — |
| L    | 5             | 3                  | Multi-model feature with integrations, 10–15 scenarios | — | — | — |
| XL   | 8             | 5                  | Complex subsystem, external API, >15 scenarios | — | — | — |

**SP vs FP — keep them separate:**
- **SP (Story Points)** — internal effort measure. Used to compute token budget and duration. Never on client quote.
- **FP (Function Points)** — client-facing deliverable measure. Used in AFP formula. Goes on the invoice.
- L and XL FP weights are lower than SP because complex internal effort does not translate 1:1 to delivered client value.

Reference stories must be real scenarios from either:
- This project's own backlog (preferred once Sprint 1 completes)
- The Reference Table from prior projects

### Step 2: Assign K-Token Baselines

K tokens = total tokens (input + output) consumed by the AI to implement one story point, across all BPE activities for that scenario size.

**If Reference Table has prior data:**
- Copy K-token values (min/expected/max) per size tier from Reference Table §1
- Note the project and sprint they came from
- Adjust if tech stack or AI model differs

**If no prior data (first project / calibration sprint):**
Use seed estimates from Reference Table §1:
- XS (0.5 SP): min=12K, expected=22K, max=36K tokens
- S (1 SP): min=25K, expected=45K, max=72K tokens
- M (2 SP): min=60K, expected=100K, max=160K tokens
- L (5 SP): min=155K, expected=250K, max=410K tokens
- XL (8 SP): min=275K, expected=440K, max=720K tokens

These are PERT seed values — mark as "uncalibrated" until Sprint 1 actuals are collected.

### Step 3: Document AI Productivity Adjustment Factor (PAF)

Record in Setup tab:
- AI Model in use (Claude Sonnet 4.x, GPT-4o, etc.)
- PAF: 1.3–1.6× speed gain over traditional (per Peng et al. 2023, GitHub 2024)
- Rework surcharge: +10–15% of coding tokens (41% higher churn rate, Ziegler 2024)
- Net PAF applied: ___

### Step 4: Define Sprint Parameters

In Setup tab, record:
- Sprint duration: ___ days (default: 1 day for AI-assisted development)
- Working hours per day: ___ (default: 8h)
- Token budget per sprint: ___ K (from stakeholder constraint or derived)
- Max SP per sprint: ___ (from capacity)

### Step 5: Record Pricing Calibration Status

In Setup tab, record:
- $/FP rate: ___  (SEED default: $250 — see Reference Table §6)
- Status: SEED / CALIBRATED (SEED until 3 sprints of actuals)
- Stack Factor selected: ___ (from Reference Table §4 — applies to AFP)
- Org Factor selected: ___ (from Reference Table §5 — applies to AFP)

These inputs feed the Client Quote tab (Tab 0).

### Step 6: Flag Calibration Status

Mark each K-token row in the Setup tab as one of:
- **CALIBRATED** — based on ≥3 actual sprints for this size tier
- **SEED** — using reference table baseline, not yet validated
- **BORROWED** — from Reference Table of a different project

Estimates from SEED or BORROWED sources carry wider PERT ranges. The Monte Carlo simulation will reflect this uncertainty.

## Rules to Follow

### I. Reference Stories Must Be Concrete
Vague reference stories produce vague estimates. If no suitable reference story exists, the first sprint is a calibration sprint — its primary output is validated K-token values, not features.

### II. Never Flatten to Single-Point Estimates
Always record min/expected/max. Single-point K-token values underestimate variance and defeat the purpose of Monte Carlo.

### III. SP and FP Are Different Units — Never Conflate
SP measures effort. FP measures deliverable capability. Both are needed: SP drives internal token budget, FP drives the client quote. Record both in the Setup tab.

### IV. Calibration Improves Sprint-by-Sprint
After each sprint close (EST-08), update K-token actuals and $/FP_actual. After 3+ sprints per size tier, mark as CALIBRATED and narrow the PERT range.

## Success Criteria
- Reference stories defined for all active size tiers
- Both SP and FP weight recorded per size tier
- K-token baselines populated (SEED or CALIBRATED) with min/expected/max
- AI productivity adjustment factor documented
- Sprint parameters set
- $/FP, Stack Factor, Org Factor recorded in Setup tab
- Setup tab of ESTIMATION_TEMPLATE.xlsx complete

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **GitHub Release** (Other, Optional) — produced by Close Iteration (#118).
- **Lessons Learned Document** (Document, Optional) — produced by Close Iteration (#118).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **Estimation Reference Table** (Document) - Required

## Artifacts Consumed

- **GitHub Release** (Other) - Optional
- **Lessons Learned Document** (Document) - Optional

## Notes

No additional notes.
