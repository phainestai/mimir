# Activity: Analyze ESM Artifacts

**Activity ID**: TBD
**Order**: 1
**Phase**: Analysis
**Dependencies**: None (first activity — requires completed ESM workflow)

## Description

Analyze ESM Artifacts

## Guidance

# Analyze ESM Artifacts

## Objective

Extract capability requirements per architectural domain from the ESM output artifacts (user journey, screen flows, .feature files, IA guidelines). This structured requirements list feeds all subsequent DTA activities (DTA-02 through DTA-17).

---

## Process

### 1. Read User Journey

- Extract **domain entities** (e.g., User, Playbook, Workflow, Activity, Skill)
- Identify **interaction patterns** (CRUD, search, import/export, real-time updates)
- Note **personas and roles** that imply auth/authorization requirements
- Flag **integration points** (external systems, APIs, data sources)

### 2. Read Screen Flows

- Identify **UI complexity** per screen type:
  - Simple: static content, read-only views
  - Moderate: forms, tables, filters, pagination
  - Complex: graphs, drag-and-drop, real-time, rich text editors
- Count screen types to estimate **frontend effort**
- Note **navigation patterns** (breadcrumbs, tabs, modals, wizards)

### 3. Read Feature Files (.feature)

- Extract **required capabilities** from scenario steps:
  - CRUD operations per entity
  - Search and filter requirements
  - Authentication and authorization scenarios
  - Error handling and edge cases
  - Data validation rules
- Map scenarios to **capability domains** (GUI_FORM, API_CRUD, AUTH_SESSION, etc.)

### 4. Read IA Guidelines

- Extract **design system requirements** (component library, theming)
- Note **accessibility requirements** (ARIA, keyboard navigation)
- Identify **responsive/multi-device** needs

### 5. Compile Requirements per Domain

Produce a structured list mapping ESM findings to the 16 architectural domains:

```
Domain: Application Blocks (DTA-02)
  - 5 bounded contexts identified: Auth, Methodology, Planning, MCP, Web UI
  - Dependency: Methodology → Planning (planning reads methodology)

Domain: Integration & API Design (DTA-03)
  - MCP stdio interface required (read-only)
  - Web UI HTTP interface required (full CRUD)
  - No external 3rd party integrations identified

Domain: Code Organization (DTA-04)
  - Monorepo structure implied (single Django project)
  - 3 layers visible: models, services, views

Domain: Data Architecture (DTA-05)
  - 6 entities with relationships (graph-like)
  - Version tracking required
  - Import/export functionality needed

... (continue for all 16 domains)
```

---

## Deliverables

- ✅ **Domain entities extracted** from user journey
- ✅ **UI complexity assessed** from screen flows
- ✅ **Capability domains mapped** from .feature files
- ✅ **Structured requirements list** produced for all 16 architectural domains
- ✅ **Ready to proceed** with DTA-02 through DTA-17

## Artifacts Produced

- Structured requirements list per domain (working document, not persisted — used as input to subsequent activities)

## Artifacts Consumed

- `docs/features/user_journey.md` (from ESM)
- `docs/ux/2_dialogue-maps/screen-flow.drawio` (from ESM)
- `docs/features/act-*/` .feature files (from ESM)
- `docs/ux/IA_guidelines.md` (from ESM)

## Notes

This activity is purely analytical — no architectural decisions are made here. Decisions happen in DTA-02 through DTA-17, each focused on a specific domain.
