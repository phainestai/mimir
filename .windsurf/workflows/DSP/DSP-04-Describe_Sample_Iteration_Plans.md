# Activity: Describe Sample Iteration Plans

**Activity ID**: TBD
**Order**: 4
**Phase**: Planning
**Dependencies**: Predecessor: DSP-03 (Define WBS & Backlog Structure)

## Description

Describe Sample Iteration Plans

## Guidance

# Describe Sample Iteration Plans

## Objective

Create at least one sample iteration plan per phase (Inception, Elaboration, Construction, Operation), showing what activities happen, in what order, what artifacts are produced, and who does what.

---

## Process

### 1. Inception Iteration Plan

```
Inception Iteration (typically 1-2 weeks)

Day 1-2: Envision the System (ESM)
  Activities: ESM-01 through ESM-07
  Artifacts:
    - User journey (docs/features/user_journey.md)
    - Screen flows (docs/ux/2_dialogue-maps/)
    - Feature files (docs/features/act-*/)
    - IA guidelines (docs/ux/IA_guidelines.md)
  Who: Product Owner + AI Agent

Day 3-4: Define Architecture (DTA)
  Activities: DTA-01 through DTA-18
  Artifacts:
    - SAO.md (docs/architecture/SAO.md)
  Who: Tech Lead + AI Agent

Day 5: Define Software Process (DSP)
  Activities: DSP-01 through DSP-05
  Artifacts:
    - MODUS_OPERANDI.md (docs/process/MODUS_OPERANDI.md)
  Who: Tech Lead + Product Owner

Exit: Architecture validated, estimates feasible, process defined
```

### 2. Elaboration Iteration Plan

```
Elaboration Iteration (typically 1 week, repeated 2-3 times)

Goal: Build 1 foundational feature end-to-end through the pipeline

Day 1: Plan Feature (BPE-01)
  - Select Act/Feature from backlog (e.g., Auth, first CRUD)
  - Create GitHub Issues from .feature scenarios
  - Identify tasks and dependencies

Day 2-3: Implement (BPE-02, BPE-03)
  - Backend: Models → Services → Views (BPE-02)
  - Frontend: Templates → HTMX interactions (BPE-03)
  - Test-first: Write tests before implementation

Day 4: Test & Verify (BPE-04, BPE-05, BPE-06)
  - Feature acceptance tests (BPE-04)
  - Journey certification tests (BPE-05)
  - Definition of Done check (BPE-06)

Day 5: Finalize & Measure (BPE-07)
  - Deploy through CI/CD pipeline
  - Measure: token spend, duration, test pass rate
  - Update velocity baseline

Exit: CI/CD working, 2-3 features deployed, velocity baseline established
```

### 3. Construction Iteration Plan

```
Construction Iteration (typically 1 week, repeated N times)

Goal: Deliver 1 full Act per iteration at proven velocity

Day 1: Plan Act (BPE-01)
  - Select next Act from prioritized backlog
  - All scenarios already have GitHub Issues (from Elaboration backlog setup)
  - Review dependencies and critical path

Day 2-4: Build All Scenarios (BPE-02 through BPE-05, repeated per scenario)
  - For each scenario in the Act:
    - Backend → Frontend → Tests → Verify
  - Use established BPE velocity from Elaboration

Day 5: Finalize Act (BPE-06, BPE-07)
  - All scenarios pass (100% test pass rate)
  - Deploy to production
  - Close GitHub Issues and Milestone
  - Retrospective: what to improve for next Act?

Exit: All features implemented, 100% test pass rate
```

### 4. Operation Iteration Plan

```
Operation Iteration (continuous, no fixed cadence)

Goal: Operate, monitor, and continuously improve

Ongoing:
  - Monitor dashboards and alerts (DTA-12 decisions in action)
  - Respond to incidents using runbooks
  - Process change requests (BPE-08)

Weekly:
  - Review SLI/SLO metrics
  - Triage bug reports and feature requests
  - Prioritize operational improvements

Monthly:
  - Blameless postmortem review (if incidents occurred)
  - Update runbooks based on learnings
  - Review and update SAO.md if architecture evolves

Exit: System stable, observability in place, handover complete
```

---

## Deliverables

- ✅ **Inception iteration plan** documented
- ✅ **Elaboration iteration plan** documented
- ✅ **Construction iteration plan** documented
- ✅ **Operation iteration plan** documented
- ✅ **Each plan shows**: activities, order, artifacts, roles
- ✅ **Decision recorded** for inclusion in MODUS_OPERANDI.md (DSP-05)

## Artifacts Produced

- Sample iteration plans (section for MODUS_OPERANDI.md)

## Artifacts Consumed

- Lifecycle model decision from DSP-02
- WBS & backlog structure from DSP-03
- Base methodology decision from DSP-01

## Notes

These are *sample* plans — actual iterations will be planned based on real backlog and velocity data. The purpose is to show a planner agent (or a new team member) what a typical iteration looks like in each phase.
