# Activity: Choose Base Methodology

**Activity ID**: TBD
**Order**: 1
**Phase**: Decision
**Dependencies**: None (first activity — requires completed DTA workflow with SAO.md)

## Description

Choose Base Methodology

## Guidance

# Choose Base Methodology

## Objective

Assess team and project characteristics, choose a base software development methodology (XP, Scrum, Kanban, or hybrid), and document project-specific adjustments.

---

## Process

### 1. Assess Team & Project Characteristics

Evaluate the following factors:

| Factor | Options | Impact on Methodology |
|--------|---------|----------------------|
| **Team size** | 1-3 / 4-8 / 9+ | Small → XP/Kanban, Large → Scrum |
| **Team experience** | Junior / Mixed / Senior | Junior → more ceremony, Senior → lighter process |
| **Distribution** | Colocated / Remote / Hybrid | Remote → more async, more documentation |
| **Project type** | Greenfield / Brownfield / Maintenance | Greenfield → iterative, Maintenance → Kanban |
| **Customer availability** | Embedded / Weekly / Monthly / Absent | Embedded → XP, Absent → more upfront planning |
| **Regulatory constraints** | None / Light / Heavy | Heavy → more documentation, formal reviews |
| **AI copilot usage** | None / Moderate / Heavy | Heavy → smaller iterations, pair programming via AI |

### 2. Propose Base Methodology

Choose one:

- **XP-based** — Best for: small teams, high customer involvement, AI copilot pairing
  - Practices: pair programming (with AI), TDD, continuous integration, small releases
  - Cadence: 1-week iterations
  - Planning: story-level, lightweight

- **Scrum-based** — Best for: medium teams, regular stakeholder check-ins
  - Ceremonies: sprint planning, daily standup, review, retro
  - Cadence: 2-week sprints
  - Planning: sprint backlog, velocity tracking

- **Kanban-based** — Best for: maintenance, ops, unpredictable work
  - Practices: WIP limits, pull-based, continuous flow
  - Cadence: no fixed iterations, deploy when ready
  - Planning: just-in-time

- **Hybrid** — Combine elements from multiple approaches
  - Example: "XP-based with Scrum ceremonies and Kanban board"

### 3. Document Adjustments

For the chosen base, document project-specific adjustments:

```
Base Methodology: XP-based

Adjustments:
- Sprint cadence: 1-week sprints targeting full Act delivery
- Pair programming: Human + AI copilot (Windsurf/Cursor)
- Continuous integration: Trunk-based development, merge to main daily
- Test-first: BDD scenarios assembled before coding, TDD for implementation
- Planning: Feature files as backlog, scenarios as work items
- Review: AI-generated PR reviewed by human before merge
- Retrospective: After each Act completion, review velocity and adjust
```

### 4. Present to User for Approval

- Show assessment results
- Present recommended methodology with rationale
- Discuss adjustments
- Get explicit approval before proceeding

---

## Deliverables

- ✅ **Team & project assessment** completed
- ✅ **Base methodology** chosen with rationale
- ✅ **Project-specific adjustments** documented
- ✅ **User approval** obtained
- ✅ **Ready to proceed** with DSP-02 (Define Lifecycle Model)

## Artifacts Produced

- Base methodology decision (section for MODUS_OPERANDI.md)

## Artifacts Consumed

- `docs/architecture/SAO.md` (from DTA workflow)
- Team/project context (from user discussion)

## Notes

No additional notes.
