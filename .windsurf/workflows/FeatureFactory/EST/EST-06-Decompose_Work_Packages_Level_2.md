# Activity: Decompose Work Packages (Level 2)

**Activity ID**: 71
**Order**: 6
**Phase**: Elaboration
**Dependencies**: None

## Description

Decompose Work Packages (Level 2)

## Guidance

## Purpose

At Level 1 (EST-03) you sized features by T-shirt. That was good enough for a rough cut. Level 2 is different: you have the scenario, you have the screen, you have SAO.md describing exactly how the stack works. You don't need to guess which layers a feature touches — BPE-01 will tell you. EST-06 runs BPE-01 in dry-run/estimation mode on each work package to produce a bottom-up artifact list, then wraps each artifact with a PERT triplet from the Reference Table.

**This is the key idea:** BPE-01 Plan → exact artifact list → PERT triplets per artifact → sum = Function Point decomposition. No generic taxonomy lookup required.

## Prerequisites
- `docs/architecture/SAO.md` exists and is current
- EST-05 complete (Rough Estimates available as cross-check)
- Requirements stability ≥ 80% (McConnell prerequisite)

## Gating Condition
If SAO.MD does not exist, skip this activity. Return here after SAO.MD is produced (typically after ESM workflow completes). Record this as a gate condition in ESTIMATION_STRATEGY.md.

## Steps

### Step 1: Select the Work Package

Take the next undecomposed work package from the sprint plan (EST-05 output). You need three inputs:

1. **The scenario file** — `docs/features/{act}/{feature}.feature`
2. **The screen** — find the matching node in the dialogue map (`docs/architecture/screen-flow.drawio`)
3. **SAO.md** — the authoritative architecture and stack description

### Step 2: Run BPE-01 in Estimation Mode

Execute BPE-01 (Plan Feature) for this work package, treating it as if starting from scratch. BPE-01 will produce an Implementation Plan that lists every artifact needed:

```
→ Input:  feature file + screen name + SAO.md
→ Output: Implementation Plan listing every artifact:
          - Django Model + Admin (if new data shape)
          - Repository methods (which ones, for what queries)
          - Service layer (what business logic)
          - Django View + URL pattern (which views, GET/POST)
          - Unit + Integration tests (what to test)
          - Django Template + HTMX (which fragments/pages)
          - Feature Acceptance Tests (from scenario steps)
          - Journey Certification Tests (if cross-feature flow)
          - DoD checklist
          - E2E Playwright tests + PR
```

For each artifact, BPE-01 will also output its **reuse flag** based on codebase assessment:
- **NEW** — doesn't exist yet, build from scratch
- **EXTEND** — exists but needs significant modification
- **REUSE** — exists, minimal touch needed

> **Estimation mode means:** produce the plan but do not write any code. Stop after BPE-01 Plan and record the artifact list.

### Step 3: Assign PERT Triplets

For each artifact in the Implementation Plan, assign PERT triplets (min / expected / max tokens) from the Reference Table K ranges:

| Artifact | Small (K) | Medium (K) | Large (K) |
|---|---:|---:|---:|
| Django Model + Admin | 8 / 15 / 28 | | |
| Repository methods | 5 / 10 / 20 | | |
| Service layer | 8 / 18 / 35 | | |
| Django View + URL | 6 / 12 / 22 | | |
| Unit + Integration Tests | 10 / 20 / 40 | | |
| Django Template + HTMX | 8 / 16 / 30 | | |
| Template partials (reusable) | 4 / 8 / 15 | | |
| Feature Acceptance Tests | 8 / 15 / 28 | | |
| Journey Certification Tests | 5 / 10 / 18 | | |
| DoD checklist | 3 / 6 / 12 | | |
| E2E Playwright tests + PR | 6 / 12 / 22 | | |
| Implementation Plan (BPE-01) | 5 / 8 / 15 | | |

Apply reuse multipliers based on BPE-01 codebase assessment:
- **NEW**: 1.0× (full token range)
- **EXTEND**: 0.6× (reading + modifying existing code)
- **REUSE**: 0.3× (trivial wiring or config change)

### Step 4: Record the Work Package

Enter in the WBS Features tab:

```
Scenario ID:    {ACT}-{ENTITY}-{OPERATION}-{NN}
Feature:        {Feature name from .feature file}
Screen:         {Screen name from dialogue map}
Sprint:         {Sprint number}
L1 Size:        M (2 SP)
BPE-01 run:     YES / ESTIMATION MODE

Artifacts from BPE-01 Plan:
  WP-01  Django Model (Widget)           NEW     min=12K  exp=16K  max=25K
  WP-02  Repository (WidgetRepo)         NEW     min=8K   exp=11K  max=18K
  WP-03  Service (WidgetService)         EXTEND  min=8K   exp=11K  max=19K  [×0.6]
  WP-04  View + URL                      NEW     min=10K  exp=14K  max=22K
  WP-05  Unit + Integration Tests        NEW     min=16K  exp=22K  max=38K
  WP-06  Template + HTMX                 REUSE   min=2K   exp=4K   max=8K   [×0.3]
  WP-07  Feature Acceptance Test         NEW     min=10K  exp=14K  max=22K
  WP-08  DoD checklist                   NEW     min=4K   exp=6K   max=10K
  WP-09  E2E test + PR                   NEW     min=8K   exp=11K  max=18K
  ────────────────────────────────────────────────────────────────────────
  TOTAL:                                          min=78K  exp=109K max=180K
```

### Step 5: Cross-Check Against Level 1 Rough Estimate

Compare Level 2 total to Level 1 estimate from EST-05:
- Within ±30% → consistent, proceed
- L2 > 30% higher than L1 → which artifact is driving the gap? Document it.
- L2 > 30% lower than L1 → check for missing artifacts. Common omissions: tests, DoD, E2E.

Record delta and rationale in the WBS Features tab notes column.

### Step 6: Repeat for All Work Packages

Work through all sprint work packages, highest priority first. After every sprint's worth, sum L2 totals and compare against the Monte Carlo seed in EST-07. If cumulative L2 is >25% outside L1 project total, update the Rough Estimates tab before proceeding.

## Rules to Follow

### I. BPE-01 Is the Decomposition Engine
Do not substitute a generic artifact checklist for BPE-01 Plan. The whole point of Level 2 is that you have the actual feature, screen, and architecture — use them. BPE-01 will produce a more accurate artifact list than any template can.

### II. DoD Is Fixed Overhead
The DoD checklist (BPE-06) applies to every work package. Never omit it. It is not optional.

### III. Tests Are Not Optional
Unit, integration, feature acceptance, and E2E tests are separate work packages. Omitting them produces a false low — the work still happens, it just becomes unplanned rework.

### IV. Decompose Before Estimating
Assigning a PERT triplet to a scenario as a whole without running BPE-01 first is a Level 1 estimate masquerading as Level 2. If you skip the BPE-01 step, mark confidence as LOW and document why.

### V. Reuse Is Not Free
Extending an existing component still consumes tokens for reading, understanding, and modifying existing code. Use 0.3× for trivial reuse, 0.6× for significant extension, 1.0× for new.

## Success Criteria
- BPE-01 Plan executed (estimation mode) for every Level 2 work package
- Each work package has a full artifact list with reuse flags
- PERT triplets assigned to every artifact
- L1/L2 cross-check performed and delta documented
- WBS Features and Detailed Estimates tabs complete

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **User Journey** (Document, Required) — produced by Define User Journey (#36).
- **Screen Flow / Dialogue Map** (Diagram, Required) — produced by Create Dialogue Maps (#38).
- **Feature Files** (Document, Required) — produced by Write Feature Files (#39).
- **HTML Mockups** (Code, Optional) — produced by Create Mockups (#40).
- **Estimation Reference Table** (Document, Required) — produced by Calibrate Reference Stories (#67).
- **Estimation Template (Excel)** (Document, Required) — produced by Size Scenarios (Level 1 SWAG) (#68).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **User Journey** (Document) - Required
- **Screen Flow / Dialogue Map** (Diagram) - Required
- **Feature Files** (Document) - Required
- **HTML Mockups** (Code) - Optional
- **Estimation Reference Table** (Document) - Required
- **Estimation Template (Excel)** (Document) - Required

## Notes

No additional notes.
