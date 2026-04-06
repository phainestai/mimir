# Activity: Define Lifecycle Model

**Activity ID**: TBD
**Order**: 2
**Phase**: Planning
**Dependencies**: Predecessor: DSP-01 (Choose Base Methodology)

## Description

Define Lifecycle Model

## Guidance

# Define Lifecycle Model

## Objective

Define project phases (Inception → Elaboration → Construction → Operation), milestones, iteration cadence, and the Phase × Artifact Matrix that maps Mimir Workflows to phases with artifact rigor levels.

---

## Decisions to Make

### 1. Define Phases & Milestones

Standard four-phase lifecycle:

| Phase | Purpose | Exit Milestone |
|-------|---------|----------------|
| **Inception** | Understand what to build, how to build it, how to run the project | Architecture validated, estimates feasible, process defined |
| **Elaboration** | Build foundational features, establish velocity, de-risk the stack | CI/CD pipeline working, 2-3 features deployed, velocity baseline established |
| **Construction** | Build all remaining features at proven velocity | All features implemented, 100% test pass rate, ready for operation |
| **Operation** | Deploy to production, monitor, support, continuously improve | System stable in production, observability in place, handover complete |

Customize if needed:
- Add/remove phases
- Adjust milestones to project specifics
- Define phase duration estimates

### 2. Define Iteration Cadence

- **Iteration length**: 1 week / 2 weeks / continuous flow
- **Iteration alignment**: Aligned to Acts? To features? To sprints?
- **Planning ceremony**: When? How long? Who participates?
- **Review ceremony**: Demo at end of iteration? To whom?
- **Retrospective**: After each iteration? After each phase?

### 3. Phase × Artifact Matrix

Map Mimir Workflows to phases and define artifact rigor:

```
Phase: Inception
  Workflow: ESM (Envision the System)
    User Journey            | Must  | Informal review
    Screen Flow             | Must  | Informal review
    Feature Files           | Must  | Formal review
    IA Guidelines           | Must  | Informal review
  Workflow: DTA (Define Architecture)
    SAO.md                  | Must  | Formal review
  Workflow: DSP (Define Software Process)
    MODUS_OPERANDI.md       | Must  | Formal review

Phase: Elaboration
  Workflow: BPE (Build Feature) — for foundational features
    Working features        | Must  | Code review + CI gate
    Test coverage           | Must  | 100% pass rate
    CI/CD pipeline          | Must  | Automated test→deploy
    Velocity baseline       | Must  | Token spend + duration per feature

Phase: Construction
  Workflow: BPE (Build Feature) — for all remaining features
    All Act features        | Must  | Code review + CI gate
    Test coverage           | Must  | 100% pass rate
    Performance targets     | Should| Load test verification

Phase: Operation
  Workflow: (Observability/DevOps — if exists)
    Dashboards & alerts     | Must  | Operational review
    Runbooks                | Must  | Operational review
    Handover documentation  | Should| Informal review
```

For each artifact, define:
- **Must/Should/Could/Won't** — MoSCoW priority per phase
- **Review level** — Formal (explicit approval) / Informal (FYI) / None
- **Tool** — Where is it produced/stored?

### 4. Map to SAO.md Decisions

Connect lifecycle decisions to architecture:
- "Elaboration builds Auth + first CRUD to de-risk the Django+HTMX stack"
- "Construction leverages proven BPE velocity from Elaboration"
- "Operation phase covers DTA-12 (Observability) decisions in practice"

---

## Deliverables

- ✅ **Phases & milestones** defined
- ✅ **Iteration cadence** set
- ✅ **Phase × Artifact Matrix** completed (workflows → phases → artifacts → rigor)
- ✅ **SAO.md mapping** documented
- ✅ **Decision recorded** for inclusion in MODUS_OPERANDI.md (DSP-05)

## Artifacts Produced

- Lifecycle model decision (section for MODUS_OPERANDI.md)

## Artifacts Consumed

- Base methodology decision from DSP-01
- `docs/architecture/SAO.md` (from DTA workflow)
- ESM artifact list (from ESM workflow)

## Notes

The Phase × Artifact Matrix replaces the former "Configure Disciplines" activity. It serves the same purpose — defining what's produced when and at what rigor — but organized by phase rather than by discipline, which is more intuitive for iteration planning.
