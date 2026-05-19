# Activity: Assess Estimation Readiness

**Activity ID**: 66
**Order**: 1
**Phase**: Elaboration
**Dependencies**: None

## Description

Assess Estimation Readiness

## Guidance

## Purpose
Determine what inputs are available, choose the appropriate estimation level (Level 1 SWAG vs. Level 2 Detailed), and produce an Estimation Strategy document that governs the rest of the workflow.

## Prerequisites
- Project idea, vision document, or feature files exist
- Stakeholder available to answer risk-profile questions

## Steps

### Step 1: Inventory Available Inputs

Check which artifacts exist and record their status:

| Artifact | Location | Status |
|---|---|---|
| BDD Feature Files | `docs/features/` | exists / partial / missing |
| Software Architecture Overview | `docs/architecture/SAO.md` | exists / missing |
| User Journey | `docs/features/user_journey.md` | exists / missing |
| Previous Sprint Actuals | Reference Table | exists / missing |
| Reference Story Calibration | Reference Table | calibrated / uncalibrated |

### Step 1.5: Check Project Bootstrap and Process Setup Status

Verify whether the project has been bootstrapped (BSP workflow) and whether the AI IDE has been configured (DSP workflow):

**BSP check — is the project runnable?**

| Check | What to Look For | Status |
|-------|------------------|--------|
| **Git repository** | `.git/` directory exists | exists / missing |
| **Project entry point** | `manage.py`, `package.json`, `Cargo.toml`, etc. | exists / missing |
| **Dependency file** | `requirements.txt`, `package.json`, `Cargo.toml` | exists / missing |
| **Makefile** | `Makefile` with `provision`, `run`, `test` targets | exists / missing |
| **Source directories** | Application code directories per SAO.md structure | exists / missing |

**If 3+ BSP checks are missing** → project is **not bootstrapped**.

**Action for non-bootstrapped projects:**

Ask user: "Project is not bootstrapped. Include BSP + DSP setup in the estimate as Sprint 0 overhead?"

- **Yes** → Add Sprint 0 overhead to estimation:
  - Create a "Sprint 0: Project Setup" line item in the WBS and Client Quote
  - BSP overhead: **10 FP** (8 activities — see REFERENCE_TABLE §7)
  - DSP overhead: **5 FP** (6 activities — see REFERENCE_TABLE §7)
  - **Total Sprint 0: ~15 FP** (before Stack × Org adjustment)
  - Record in ESTIMATION_STRATEGY.md: "Sprint 0 bootstrap overhead included: 15 FP"

- **No** → Redirect to BSP workflow:
  - Stop EST workflow
  - Direct user: "Please run BSP (Bootstrap Project) workflow first, then return to EST"
  - Record in ESTIMATION_STRATEGY.md: "Bootstrap deferred — not included in estimates"

**DSP check — is the AI IDE configured?**

| Check | What to Look For | Status |
|-------|------------------|--------|
| **CLAUDE.md** | `CLAUDE.md` exists in project root | exists / missing |
| **Copilot instructions** | `.github/copilot-instructions.md` exists | exists / missing |
| **Windsurf/Cursor rules** | `.windsurf/rules/` or `.cursor/rules/` exists | exists / missing |

If DSP artifacts are missing and BSP is being quoted: include DSP FP in the Sprint 0 overhead (already in the 15 FP above).
If BSP is done but DSP is missing: add DSP as a 5 FP line item in Sprint 1.

**If project is fully bootstrapped and DSP is done** → proceed to Step 2 (no action needed).

### Step 2: Run Boehm & Turner 5-Factor Risk Assessment

Rate each factor on the appropriate scale. Circle the home ground that applies.

| Factor | Agile Home Ground | Plan-Driven Home Ground | This Project |
|---|---|---|---|
| Team Size | ≤10 | ≥20 | ___ |
| Criticality | Low (comfort) | High (money/life) | ___ |
| Requirements Dynamism | High change rate | Stable | ___ |
| Culture | Chaos-tolerant | Order-preferring | ___ |
| Personnel | All senior/CRACK | Mixed skill levels | ___ |

Identify dominant risk type:
- **A-risks dominate** (too agile) → lean toward more process/Level 2
- **P-risks dominate** (too plan-driven) → stay Level 1, iterate fast
- **Mixed** → Level 1 now, schedule Level 2 after Sprint 1

### Step 3: Select Estimation Level

**Level 1 SWAG** — use when:
- Feature files exist but SAO.MD is absent
- Project is in early discovery
- Team size ≤ 5, low criticality
- First sprint (always start here)

**Level 1 + Level 2 Detailed** — use when:
- `docs/architecture/SAO.md` exists and is current
- Requirements stability ≥ 80% (McConnell prerequisite)
- Team size > 10 or criticality is high
- Stakeholder requires commitment-quality estimates

**Both levels produce** the same Excel output; Level 2 simply populates additional tabs (WBS Features + Detailed Estimates) and enables the Client Quote tab (AFP pricing).

### Step 4: Document Estimation Strategy

Create or update `docs/plans/ESTIMATION_STRATEGY.md` with:
- Estimation level chosen and rationale
- Risk profile summary (5-factor ratings)
- Sprint 0 overhead included? (BSP/DSP FP count)
- Gate condition for upgrading to Level 2 (e.g., "after SAO.MD is complete")
- Sprint refinement cadence (default: every sprint close)
- Reference Table location

### Step 5: Open Excel Estimation Template

Open `docs/plans/ESTIMATION_TEMPLATE.xlsx`. Verify all tabs are present:
0. Client Quote
1. Setup
2. Scenario List
3. ECF
4. TCF
5. Rough Estimates
6. Monte Carlo
7. WBS Features
8. Detailed Estimates

If file does not exist, copy from `forge/templates/ESTIMATION_TEMPLATE.xlsx`.

## Rules to Follow

### I. Prerequisites Before Estimating
Never produce token or duration estimates without first completing Steps 1–3. An estimate produced without a risk assessment is a guess, not engineering.

### II. Level Decision is Reversible
Choosing Level 1 does not prevent upgrading to Level 2 later. Record the upgrade gate condition explicitly so it is not forgotten.

### III. McConnell Prerequisite Checklist
Before Level 2: confirm problem definition is documented, requirements are ≥ 80% complete, and architecture is sketched. Without these, Level 2 adds false precision, not real accuracy.

### IV. Sprint 0 Is Always Quoted Separately
BSP and DSP overhead FP must appear as a separate line item on the Client Quote — never blended into feature delivery FPs. The client must see the setup cost explicitly.

## Success Criteria
- Input inventory complete
- Bootstrap and DSP status checked; Sprint 0 overhead FP recorded if applicable
- 5-factor risk assessment documented
- Estimation level selected with rationale
- ESTIMATION_STRATEGY.md created/updated
- Excel template open and verified

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
