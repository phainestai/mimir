# Activity: Define WBS & Backlog Structure

**Activity ID**: TBD
**Order**: 3
**Phase**: Planning
**Dependencies**: Predecessor: DSP-02 (Define Lifecycle Model)

## Description

Define WBS & Backlog Structure

## Guidance

# Define WBS & Backlog Structure

## Objective

Define the Work Breakdown Structure hierarchy, map it to tooling, establish critical path management, choose estimation units, and define how .feature files map to backlog items.

---

## Decisions to Make

### 1. WBS Hierarchy

Define the work breakdown structure:

```
Feature (Act)
  └── Scenario (from .feature file)
       └── Task (implementation step)
            └── Subtask (optional, for complex tasks)
```

Example:
```
Act 3: Workflow Management
  ├── Scenario: WORKFLOW-LIST+FIND-01 Navigate to workflow list
  │   ├── Task: Implement workflow list view
  │   ├── Task: Implement workflow list template
  │   └── Task: Write integration tests
  ├── Scenario: WORKFLOW-CREATE-01 Create new workflow
  │   ├── Task: Implement create view + form
  │   ├── Task: Implement create template
  │   └── Task: Write integration tests
  └── ...
```

### 2. Backlog Tooling

Map WBS to issue tracker:
- **Tool**: GitHub Issues, GitLab Issues, Jira, Linear
- **Labels**: How are hierarchy levels identified?
  - e.g., `act:3`, `feature:workflow-management`, `scenario:WORKFLOW-LIST+FIND-01`
- **Milestones**: Map to phases or Acts?
- **Projects/Boards**: Kanban board per phase? Per Act?

### 3. Critical Path Management

- **Dependencies**: Predecessor/successor via Mimir Activity dependencies
- **Blocking items**: How are blockers identified and escalated?
- **Parallel work**: Which features can be built in parallel?
- **Cross-cutting concerns**: How are shared components (auth, nav, design system) prioritized?

### 4. Estimation Units

Choose one:
- **Story points** — Relative complexity, Fibonacci sequence
- **T-shirt sizes** — S/M/L/XL, mapped to time ranges
- **Token-spend-based** — Estimated AI token cost per feature (novel for AI-assisted dev)
- **Time-based** — Hours/days estimate
- **No estimation** — Just prioritize and measure velocity empirically

For chosen unit: how are estimates created? Who estimates? When are estimates updated?

### 5. Feature Files → Backlog Mapping

Define the conversion rules:
- Each `.feature` file → one or more GitHub Issues?
- Each `Scenario` → one GitHub Issue?
- Each `Act` → one GitHub Milestone?
- How are new scenarios (from change requests) added to the backlog?
- How are completed scenarios tracked?

---

## Deliverables

- ✅ **WBS hierarchy** defined with examples
- ✅ **Backlog tooling** configured (tool, labels, milestones, boards)
- ✅ **Critical path management** approach defined
- ✅ **Estimation units** chosen with process
- ✅ **Feature file → backlog mapping** rules established
- ✅ **Decision recorded** for inclusion in MODUS_OPERANDI.md (DSP-05)

## Artifacts Produced

- WBS & backlog structure decision (section for MODUS_OPERANDI.md)

## Artifacts Consumed

- Lifecycle model decision from DSP-02
- `.feature` files from ESM workflow

## Notes

No additional notes.
