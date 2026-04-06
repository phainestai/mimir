# Activity: Write Modus Operandi

**Activity ID**: TBD
**Order**: 6
**Phase**: Documentation
**Dependencies**: Predecessor: All DSP-01 through DSP-05

## Description

Write Modus Operandi

## Guidance

# Write Modus Operandi

## Objective

Compile all software process decisions from DSP-01 through DSP-05 into a single, authoritative document: `docs/process/MODUS_OPERANDI.md`.

---

## Process

### 1. Gather All Decisions

Collect the recorded decisions from each activity:
- DSP-01: Base Methodology choice and adjustments
- DSP-02: Lifecycle Model (phases, milestones, cadence, Phase × Artifact Matrix)
- DSP-03: WBS & Backlog Structure (hierarchy, tooling, estimation)
- DSP-04: Sample Iteration Plans (one per phase)
- DSP-05: AI/Human Collaboration Patterns (responsibilities, quality gates, workflows)

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

## 7. AI/Human Collaboration Patterns
- Responsibility matrix (AI vs Human responsibilities)
- Quality gates for AI-generated code
- Context management strategy
- Communication and escalation patterns
- Collaboration workflows per development phase

## 8. Roles & Responsibilities
- Product Owner: vision, priorities, acceptance
- Tech Lead: architecture, code review, technical decisions
- AI Agent: implementation, testing, documentation (following collaboration patterns)
- Human Developer: review, approval, complex decisions (following collaboration patterns)

## 9. Tools
- Project management: [GitHub Issues / GitLab / etc.]
- Methodology: Mimir (playbooks, workflows, activities, skills)
- Code: [IDE, VCS, CI/CD platform]
- Communication: [Slack / Teams / etc.]
- AI Collaboration: Context templates, quality dashboards
```

### 3. Review with User

- Present MODUS_OPERANDI.md for review
- Discuss any open questions about AI/human collaboration patterns
- Get explicit approval on collaboration workflows
- This document, together with SAO.md, forms the project's foundation

---

## Deliverables

- ✅ **MODUS_OPERANDI.md written** at `docs/process/MODUS_OPERANDI.md`
- ✅ **All process decisions** compiled into single document including AI collaboration patterns
- ✅ **User approval** obtained
- ✅ **Ready to proceed** to Bootstrap Project or Elaboration phase

## Artifacts Produced

- Complete MODUS_OPERANDI.md document

## Artifacts Consumed

- Base methodology decisions from DSP-01
- Lifecycle model from DSP-02
- WBS structure from DSP-03
- Sample iteration plans from DSP-04
- AI/Human collaboration patterns from DSP-05

## Notes

The inclusion of AI/Human collaboration patterns in this document is critical for modern development teams. These patterns should be actively referenced and refined throughout the project lifecycle.