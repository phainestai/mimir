# CLAUDE.md — {ProjectName} Codebase Guide

## What Is {ProjectName}

{ExecutiveSummary}

---

## Architecture

### Directory Layout

```
{DirectoryLayout}
```

### Data Model Hierarchy

```
{DataModelHierarchy}
```

### Key Design Decisions

{KeyDesignDecisions}

### Services Pattern

{ServicesPattern}

---

## Documentation Map

| What | Where | When to Read |
|------|-------|--------------|
| System architecture | `docs/architecture/SAO.md` | Before big changes |
| User journey / all Acts | `docs/features/user_journey.md` | Feature planning |
| Feature specs (BDD) | `docs/features/act-*/` | Before implementing any feature |
| UI patterns & IA | `docs/ux/IA_guidelines.md` | Before building UI |
| Development rules | `.windsurf/rules/*.md` | Always active |
| Process workflows | `.windsurf/workflows/*/` | When running a workflow |

---

## Available Workflows

| Workflow | Purpose | Activities | When to Use |
|----------|---------|------------|-------------|
{WorkflowTable}

---

## Available Skills

{SkillsTable}

---

## Artifact Templates

| Template | Workflow | Purpose | Location |
|----------|----------|---------|----------|
{ArtifactTemplateTable}

---

## AI/Human Collaboration

### AI Agent Responsibilities
- Code generation following established patterns
- Test implementation (unit, integration, e2e)
- Documentation generation (docstrings, README updates)
- Refactoring within architectural boundaries
- Routine CRUD implementations

### Human Developer Responsibilities
- Architectural decisions and boundary setting
- Code review and quality validation
- Security-sensitive implementations
- Production deployment decisions

### Quality Gates for AI-Generated Code
1. All tests pass (unit, integration, linting)
2. Code coverage meets project threshold
3. Documentation generated for public APIs
4. Code follows established patterns from SAO.md
5. Human review and approval before merge

### Escalation Rules
- Ambiguous requirements → ask human
- Architectural decisions outside established patterns → ask human
- Security-sensitive code → flag for human review
- Complex business logic with edge cases → discuss before implementing

---

## Coding Conventions

### Commit Format (Angular Convention — strict)

```
<type>(<scope>): <subject>

<body — what changed and why>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Code Style

{CodeStyleRules}

### Logging

{LoggingConventions}

---

## Development Workflow (How to Build Features)

### Before Implementing Any Feature

1. Read the relevant feature spec in `docs/features/act-*/`
2. Read `docs/architecture/SAO.md` for architectural context

### Implementation Order

1. **Backend**: models → services → views (thin controllers)
2. **Frontend**: templates + interactions
3. **Tests**: write before implementation, 100% pass rate required
4. Check Definition of Done → PR

{AdditionalBPEDetails}

---

## Testing

```bash
{TestCommands}
```

**Key rules:**
- **Test-first**: write test before implementation
- **No mocks in integration tests**: use real objects/DB
- Run tests after every change
- Only 100% pass rate counts as success

---

## Running Locally

```bash
{SetupCommands}
```

---

## Placeholder Reference

- `{ProjectName}` — Name of the project
- `{ExecutiveSummary}` — From SAO.md Executive Summary
- `{DirectoryLayout}` — From SAO.md Project Structure section
- `{DataModelHierarchy}` — From SAO.md or models
- `{KeyDesignDecisions}` — Top 3-5 decisions from SAO.md Design Principles
- `{ServicesPattern}` — How services are structured (from SAO.md)
- `{WorkflowTable}` — Auto-generated from `.windsurf/workflows/*/`
- `{SkillsTable}` — Auto-generated from `.windsurf/workflows/*/skills/`
- `{ArtifactTemplateTable}` — Auto-generated from `.windsurf/workflows/*/artifacts/`
- `{CodeStyleRules}` — From `.windsurf/rules/` or team conventions
- `{LoggingConventions}` — From logging rules
- `{AdditionalBPEDetails}` — Condensed BPE workflow steps
- `{TestCommands}` — pytest commands for the project
- `{SetupCommands}` — venv, install, migrate, runserver commands
