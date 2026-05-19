# Activity: Size Scenarios (Level 1 SWAG)

**Activity ID**: 68
**Order**: 3
**Phase**: Elaboration
**Dependencies**: None

## Description

Size Scenarios (Level 1 SWAG)

## Guidance

## Purpose
Assign a T-shirt size (XS → XL) to every BDD scenario using the reference stories as anchors. Record both SP (for token budget) and FP weight (for client AFP). Produce story point totals per feature and per sprint. Populate the Scenario List tab of ESTIMATION_TEMPLATE.xlsx.

## Prerequisites
- EST-02 complete (reference stories defined, K-token baselines set, SP and FP weights recorded)
- BDD feature files exist in `docs/features/`

## Steps

### Step 1: Enumerate All Scenarios

Read all `.feature` files in `docs/features/`. For each scenario, record:
- Scenario ID (e.g., `FOB-PLAYBOOKS-LIST+FIND-01`)
- Feature name
- Act/group
- One-line description (from Scenario title)

Paste the list into the Scenario List tab, one row per scenario.

### Step 2: Size Each Scenario Against Reference Stories

For each scenario, compare to the reference stories defined in EST-02:

**Sizing heuristics:**

| Ask This | Size | SP | FP |
|----------|------|:--:|:--:|
| Single read-only view, no writes? | XS | 0.5 | 0.5 |
| One model, one CRUD operation, happy path? | S | 1 | 1 |
| Two models or one model with complex logic? | M | 2 | 2 |
| Multiple models, service layer, or external call? | L | 5 | 3 |
| Multi-subsystem, external API, complex orchestration? | XL | 8 | 5 |
| Clearly larger than XL? | Split first | — | — |

For each scenario, record: assigned size, SP value, FP weight, and a one-line sizing rationale.

**Anti-patterns — never do these:**

| Anti-pattern | Why Wrong | Correct Approach |
|---|---|---|
| Size by scenario count (10 scenarios → L or XL) | Scenario count measures test breadth, not implementation effort | Size by *code complexity and reuse*, not test count |
| Size 2nd/3rd CRUD entity same as 1st | Pattern reuse cuts effort 3–5× | Downgrade reused entities: first entity S→M, 2nd+ XS→S |
| Size all config/bootstrap steps as S or M | Config-heavy work is code-light | Config work is XS; infrastructure overhead goes in Sprint 0 |
| Treat reuse as free | EXTEND still consumes tokens to read/modify | Apply 0.6× EXTEND multiplier in Level 2 (EST-06) |

### Step 3: Challenge Outliers

Before finalizing, review:
- Any scenario sized XL → can it be split into two L scenarios?
- Any scenario sized > XL → must be split (McConnell rule: no single unit > 1.5× reference L)
- Any cluster of XS scenarios that share a model → consider whether they belong to one M

Propose splits/merges to user for approval before proceeding.

### Step 4: Group by Feature and Sprint

In the Scenario List tab:
1. Group rows by Feature (sub-total SP and FP per feature)
2. Assign scenarios to sprints based on:
   - Dependencies (parent model before child, auth before protected endpoints)
   - Priority (must-have before nice-to-have)
   - Sprint capacity (SP per sprint from Setup tab)
3. Record: Sprint #, SP allocated, FP allocated, cumulative SP, cumulative FP

### Step 5: Compute Totals

In the Scenario List tab, compute and record:
- Total scenarios: ___
- Total SP: ___ (drives token budget in EST-05)
- Total FP: ___ (drives AFP quote in Client Quote tab)
- SP per sprint (sum per sprint column)
- FP per sprint (sum per sprint column)
- Estimated number of sprints

### Step 6: Flag Assumptions

For any scenario where sizing is uncertain, add a flag column entry:
- `ASSUMPTION: sized M because requirements unclear for error handling`
- `ASSUMPTION: sized L but may be M if third-party API has SDK`

These assumptions become the first risk items to address in Sprint 1.

## Rules to Follow

### I. Size Relative to Reference, Not Absolute
Never size in hours or days. Size by comparing to the reference story. The reference story is the unit of measure.

### II. One Scenario Per Row
Do not aggregate scenarios into epics in this tab. The Monte Carlo simulation operates at the scenario level. Aggregation happens only in the sprint grouping columns.

### III. Record Both SP and FP
Every row must have both SP (for internal token budget) and FP weight (for client quote). They differ for L and XL — do not conflate them.

### IV. Scenario Must Be Independently Executable
If a scenario cannot be tested in isolation, split it or make the dependency explicit.

### V. No Hidden Work
Every piece of work that will consume tokens must map to a scenario. Infrastructure, CI/CD, devops scaffolding → Sprint 0 overhead line item (BSP/DSP FPs from EST-01).

## Success Criteria
- All BDD scenarios enumerated and sized
- Both SP and FP weight recorded per scenario
- No unresolved XL+ scenarios (all split or explicitly approved)
- Scenarios grouped into sprints respecting dependencies and capacity
- SP and FP totals computed per feature, per sprint, project total
- Assumptions flagged
- Scenario List tab of ESTIMATION_TEMPLATE.xlsx complete

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **Estimation Template (Excel)** (Document) - Required

## Artifacts Consumed

- **Feature Files** (Document) - Required
- **Estimation Reference Table** (Document) - Required

## Notes

No additional notes.
