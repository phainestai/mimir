# Activity: Define Application Blocks

**Activity ID**: TBD
**Order**: 2
**Phase**: Design
**Dependencies**: Predecessor: DTA-01 (Analyze ESM Artifacts)

## Description

Define Application Blocks

## Guidance

# Define Application Blocks

## Objective

Identify bounded contexts, domain packages, module boundaries, and dependency rules. Choose the foundational architectural pattern (MVC, event-driven, modular monolith, microservices, etc.).

---

## Internal Process

Every domain activity follows this structure:

1. **Identify needs** — what does ESM require for this domain?
2. **Scan Skills** — query Playbook Skills by `capability_domain` for this domain
3. **Propose options** — 2-3 approaches with Skill coverage, cost, risk
4. **Record decision** — user picks, rationale documented

---

## Decisions to Make

### 1. Bounded Contexts / Domain Packages

- Review ESM entities and their relationships
- Group entities into cohesive domain packages
- Define which entities belong together (high cohesion) vs. which are separate concerns (loose coupling)
- Example groupings:
  - `auth/` — User, Session, Permissions
  - `methodology/` — Playbook, Workflow, Activity, Skill
  - `planning/` — WorkPlan, Task, Estimation
  - `mcp/` — MCP protocol, tools, stdio interface

### 2. Module Boundaries & Dependency Rules

- Define what can import what (dependency direction)
- Identify shared kernel vs. independent modules
- Example rules:
  - `planning` → depends on `methodology` (reads playbook structure)
  - `mcp` → depends on `methodology` (exposes methodology as tools)
  - `auth` → independent (no methodology dependency)
  - No circular dependencies allowed

### 3. Foundational Architectural Pattern

Choose one:
- **MVC / MTV** — Model-Template-View (Django default). Best for: server-rendered web apps with moderate complexity.
- **Event-Driven** — Publish/subscribe, event sourcing. Best for: highly decoupled systems, real-time requirements.
- **Modular Monolith** — Single deployable unit with strict module boundaries. Best for: starting simple with clear growth path.
- **Microservices** — Independent deployable services. Best for: large teams, independent scaling needs.
- **Batch Processing** — Scheduled jobs processing data in bulk. Best for: data pipelines, ETL.
- **Hybrid** — Combine patterns (e.g., MVC for web + event-driven for async).

### 4. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `APP_STRUCTURE`
- `DOMAIN_MODELING`

Report coverage:
```
Skill Coverage for Application Blocks:
  APP_STRUCTURE  | [Skill Name] ✅  or  ❌ No Skill
  DOMAIN_MODELING| [Skill Name] ✅  or  ❌ No Skill
```

If gaps exist: "No Skill for APP_STRUCTURE — will need to create one or rely on general guidance. Estimated impact: +N iterations for bootstrapping."

---

## Deliverables

- ✅ **Bounded contexts / domain packages** identified and documented
- ✅ **Module dependency rules** defined (what imports what)
- ✅ **Foundational pattern** chosen with rationale
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Application blocks decision (section for SAO.md)

## Artifacts Consumed

- Structured requirements list from DTA-01

## Notes

No additional notes.
