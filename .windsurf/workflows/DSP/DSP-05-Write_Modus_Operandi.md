# Activity: Write Modus Operandi

**Activity ID**: TBD
**Order**: 5
**Phase**: Documentation
**Dependencies**: Predecessor: All DSP-01 through DSP-04

## Description

Write Modus Operandi

## Guidance

# Write Modus Operandi

## Objective

Compile all software process decisions from DSP-01 through DSP-04 into a single, authoritative document: `docs/process/MODUS_OPERANDI.md`.

---

## Process

### 1. Gather All Decisions

Collect the recorded decisions from each activity:
- DSP-01: Base Methodology choice and adjustments
- DSP-02: Lifecycle Model (phases, milestones, cadence, Phase × Artifact Matrix)
- DSP-03: WBS & Backlog Structure (hierarchy, tooling, estimation)
- DSP-04: Sample Iteration Plans (one per phase)

### 2. Write MODUS_OPERANDI.md

Structure:

```markdown
# {Project Name}: Modus Operandi

## 1. Introduction
- Purpose of this document
- Scope (which project/team this applies to)
- References (SAO.md, ESM artifacts, Playbook)

## 2. Overview
- Base methodology and rationale
- Key adjustments for this project
- Team structure and roles

## 3. Lifecycle Model
- Phases: Inception → Elaboration → Construction → Operation
- Milestones per phase
- Iteration cadence

## 4. Phase × Artifact Matrix
- Which workflows run in which phase
- Which artifacts are Must/Should/Could per phase
- Review levels per artifact

## 5. WBS & Backlog Structure
- Work breakdown hierarchy (Feature → Scenario → Task)
- Backlog tool configuration
- Estimation approach
- Feature file → backlog mapping rules

## 6. Sample Iteration Plans
- Inception iteration
- Elaboration iteration
- Construction iteration
- Operation iteration

## 7. Roles & Responsibilities
- Product Owner: vision, priorities, acceptance
- Tech Lead: architecture, code review, technical decisions
- AI Agent: implementation, testing, documentation
- Human Developer: review, approval, complex decisions

## 8. Tools
- Project management: [GitHub Issues / GitLab / etc.]
- Methodology: Mimir (playbooks, workflows, activities, skills)
- Code: [IDE, VCS, CI/CD platform]
- Communication: [Slack / Teams / etc.]
```

### 3. Review with User

- Present MODUS_OPERANDI.md for review
- Discuss any open questions
- Get explicit approval
- This document, together with SAO.md, forms the project's foundation

---

## Deliverables

- ✅ **MODUS_OPERANDI.md written** at `docs/process/MODUS_OPERANDI.md`
- ✅ **All process decisions** compiled into single document
- ✅ **User approval** obtained
- ✅ **Ready to proceed** to Bootstrap Project or Elaboration phase

## Artifacts Produced

- `docs/process/MODUS_OPERANDI.md`

## Artifacts Consumed

- All decision records from DSP-01 through DSP-04

## Notes

This is the final DSP activity. After MODUS_OPERANDI.md is approved, the Inception phase is complete (assuming ESM and DTA are also done). The project is ready to proceed to Elaboration — or to Bootstrap Project if the codebase doesn't exist yet.
