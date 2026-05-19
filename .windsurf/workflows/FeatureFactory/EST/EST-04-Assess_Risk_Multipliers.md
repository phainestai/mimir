# Activity: Assess Risk Multipliers

**Activity ID**: 69
**Order**: 4
**Phase**: Elaboration
**Dependencies**: None

## Description

Assess Risk Multipliers

## Guidance

## Purpose
Two separate multiplier assessments are performed here:

**Section A — Internal (ECF/TCF):** Rate Environmental and Technical Complexity Factors to produce the combined multiplier that adjusts raw SP-based token estimates. These factors also calibrate the $/FP rate. **Never shown to client.**

**Section B — Client-Facing (Stack Factor / Org Factor):** Select the Stack Factor and Org Factor that go into the AFP formula on the Client Quote. These encode the same real-world friction in commercially legible terms. **Shown on quote.**

The two assessments are done together because they are informed by the same project context, but they produce separate outputs.

## Prerequisites
- EST-03 complete (scenarios sized)
- Stakeholder available to validate risk ratings

---

## Section A — Internal: ECF / TCF

### Step A1: Rate ECF Factors

Open the ECF tab in ESTIMATION_TEMPLATE.xlsx. Rate each factor from 0 (no influence) to 5 (strong influence).

**Environmental Complexity Factors:**

| # | Factor | Weight | Rating (0–5) | Weighted |
|---|---|---|---|---|
| E1 | Familiarity with the AI model/tooling used | 1.5 | | |
| E2 | Part-time participation (interruptions, context switching) | -1.0 | | |
| E3 | Analyst / prompt engineering experience | 0.5 | | |
| E4 | Lead developer application experience | 0.5 | | |
| E5 | Motivation of team | 1.0 | | |
| E6 | Stability of requirements | 2.0 | | |
| E7 | Part-time users / product owners | -1.0 | | |
| E8 | Difficulty of programming language / stack | -1.0 | | |

**ECF Formula:** `ECF = 1.4 + (-0.03 × Σ(Weight × Rating))`

A value < 1.0 means favorable environment (fewer tokens). A value > 1.0 means challenging (more tokens).

**AI-Specific Extension (add to ECF tab):**

| # | Factor | Weight | Rating (0–5) | Weighted |
|---|---|---|---|---|
| A1 | AI model tier (Claude Opus=5, Sonnet=3, Haiku=1) | 0.8 | | |
| A2 | Prompt maturity (mature prompts=5, first use=1) | 0.6 | | |
| A3 | Hallucination risk (well-known domain=1, novel=5) | -0.5 | | |
| A4 | Context window pressure (small ctx=5, large=1) | -0.4 | | |
| A5 | AI-generated code rework rate (41% baseline = 3) | -0.6 | | |

`ECF_final = ECF_base × (1 + AI_adjustment)`

### Step A2: Rate TCF Factors

Open the TCF tab. Rate each factor 0–5.

**Technical Complexity Factors:**

| # | Factor | Weight | Rating (0–5) | Weighted |
|---|---|---|---|---|
| T1 | Distributed system / microservices | 2.0 | | |
| T2 | Response time / performance requirements | 1.0 | | |
| T3 | End-user efficiency (optimized UX needed) | 1.0 | | |
| T4 | Complex internal processing / algorithms | 1.0 | | |
| T5 | Code reusability requirement | 1.0 | | |
| T6 | Easy to install / deploy | 0.5 | | |
| T7 | Easy to use (usability) | 0.5 | | |
| T8 | Portability across platforms | 2.0 | | |
| T9 | Easy to change / maintainability | 1.0 | | |
| T10 | Concurrent use / multi-user | 1.0 | | |
| T11 | Security features | 1.0 | | |
| T12 | Direct access for third parties / APIs | 1.0 | | |
| T13 | Special user training required | 1.0 | | |

**TCF Formula:** `TCF = 0.6 + (0.01 × Σ(Weight × Rating))`

### Step A3: Compute Internal Combined Multiplier

`Internal Multiplier = ECF_final × TCF`

Record in Setup tab. Applied to all SP × K estimates in EST-05 to produce the token budget.

This multiplier also feeds the $/FP calibration rate (EST-08): as ECF/TCF are refined by actuals, the effective cost per FP delivered changes, and $/FP is updated accordingly.

| Combined Multiplier | Meaning |
|---|---|
| < 0.8 | Highly favorable — experienced team, stable requirements, mature AI tooling |
| 0.8 – 1.0 | Normal — typical project |
| 1.0 – 1.3 | Moderate risk — some unknowns |
| 1.3 – 1.6 | High risk — unstable requirements or novel domain |
| > 1.6 | Very high risk — reconsider scope before estimating further |

---

## Section B — Client-Facing: Stack Factor and Org Factor

### Step B1: Select Stack Factor

From Reference Table §4, select the base tier that best describes the client's technology environment, then apply any additive modifiers:

**Base tiers:**

| Stack Factor | Select If... |
|:------------:|-------------|
| 0.85 | Greenfield, single clean modern stack, no legacy |
| 1.00 | Standard single stack (Django+HTMX, Rails, Node, FastAPI) |
| 1.25 | Two integrated stacks (React SPA + REST backend) |
| 1.50 | Legacy codebase integration required |
| 1.75 | Multi-cloud or platform-constrained |
| 2.00 | Enterprise platform (Salesforce, SAP, ServiceNow) |
| 2.50+ | Government / highly regulated (FedRAMP, ITAR) |

**Additive modifiers:** on-premises +0.10, legacy integration +0.15, multi-cloud +0.15, real-time +0.10, mobile +0.20.

Record: Stack Factor base + modifiers = **Stack Factor total: ___**

### Step B2: Select Org Factor

From Reference Table §5, select the tier that best describes the client's organizational friction:

| Org Factor | Select If... |
|:----------:|-------------|
| 0.80 | Startup — flat structure, one decision-maker, no formal process |
| 1.00 | Small team / SME — basic sprints, PM involved |
| 1.25 | Mid-size — defined SDLC, multiple stakeholders |
| 1.50 | Enterprise — formal change management, legal/security review gates |
| 2.00 | ITIL/ITSM — CAB approvals, change freeze windows |
| 2.50 | Regulated enterprise — SOX, PCI-DSS, HIPAA sign-off gates |
| 3.50 | Government — procurement gates, FISMA/FedRAMP, multi-agency review |

Record: **Org Factor: ___**

### Step B3: Confirm $/FP Rate

From Setup tab (populated in EST-02), confirm the $/FP rate applies:
- SEED: $250/FP (default until 3 sprints calibrated)
- CALIBRATED: actual $/FP from last sprint close (EST-08)

Record in Client Quote tab (Tab 0).

### Step B4: Preview AFP

With Stack Factor, Org Factor, and total FP from Scenario List, compute preview AFP:

```
Preview AFP = Total FP (from Scenario List) × Stack Factor × Org Factor
Preview Quote Total = Preview AFP × $/FP
```

This is a preview — the AFP on the Client Quote tab will use the final FP total from EST-05/EST-06. Present preview to user for a sanity check before proceeding.

---

## Rules to Follow

### I. Rate ECF/TCF Honestly, Not Optimistically
Optimistic risk ratings are the most common estimation failure. If in doubt between 3 and 4, choose 4.

### II. ECF/TCF Are Internal — Never on Client Quote
The client sees Stack Factor and Org Factor. ECF/TCF are calibration inputs for $/FP. Mixing them up produces misleading quotes.

### III. Re-Rate Each Sprint
ECF/TCF are not static. At each sprint close (EST-08), revisit factors that have changed. Stack Factor and Org Factor can also change if the project context changes — update and re-quote.

### IV. If AFP Preview Looks Wrong, Fix the Inputs — Not the Rate
If the preview AFP produces a surprising total, diagnose which input is off (FP count? Stack Factor? Org Factor?) — not pad or cut the $/FP rate to hit a target number.

## Success Criteria
- ECF and TCF factors rated with rationale for outliers (Section A)
- Internal combined multiplier computed and recorded in Setup tab
- Stack Factor and Org Factor selected and recorded (Section B)
- $/FP rate confirmed
- AFP preview computed and reviewed
- ECF, TCF tabs and Client Quote tab of ESTIMATION_TEMPLATE.xlsx updated

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
