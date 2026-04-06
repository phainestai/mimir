# Activity: Define Code Organization

**Activity ID**: TBD
**Order**: 4
**Phase**: Design
**Dependencies**: Predecessor: DTA-02 (Define Application Blocks)

## Description

Define Code Organization

## Guidance

# Define Code Organization

## Objective

Define project layout, layer separation, naming conventions, and shared library approach. This translates the logical application blocks (DTA-02) into a physical directory and file structure.

---

## Decisions to Make

### 1. Repository Strategy

Choose one:
- **Monorepo** — Single repository, all code together. Best for: small teams, shared tooling.
- **Polyrepo** — Separate repos per service/component. Best for: independent teams, different release cycles.
- **Monorepo with packages** — Single repo with npm/pip workspaces. Best for: shared code with clear boundaries.

### 2. Directory Structure & Layer Separation

Define the top-level project layout:
- Where do models live?
- Where do services (business logic) live?
- Where do views/controllers live?
- Where do templates/frontend assets live?
- Where do tests live?
- Where do docs live?

Example (Django):
```
project/
├── app_name/
│   ├── models/          # Data layer
│   ├── services/        # Business logic
│   ├── views/           # HTTP interface (Django views)
│   └── templates/       # HTML templates
├── mcp/                 # MCP interface
├── tests/               # All tests
├── docs/                # Documentation
└── manage.py
```

### 3. Naming Conventions

Define rules for:
- **Files**: snake_case.py, kebab-case.html, PascalCase.tsx
- **Classes**: PascalCase
- **Functions/methods**: snake_case
- **URLs**: kebab-case (`/playbooks/playbook/list/`)
- **Database tables**: snake_case (auto from models)
- **Constants**: UPPER_SNAKE_CASE

### 4. Shared Libraries / Common Utilities

- Where do cross-cutting concerns live? (logging, error handling, decorators)
- How are shared types/interfaces defined?
- Import rules: what can import from `common/`?

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `CODE_ORG`
- `PROJECT_LAYOUT`

Report coverage and gaps.

---

## Deliverables

- ✅ **Repository strategy** chosen
- ✅ **Directory structure** defined with layer separation
- ✅ **Naming conventions** documented
- ✅ **Shared library approach** defined
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Code organization decision → contributes to `artifacts/sao_document_template.md` § "3. Code Organization"

## Artifacts Consumed

- Application blocks decision from DTA-02

## Notes

No additional notes.
