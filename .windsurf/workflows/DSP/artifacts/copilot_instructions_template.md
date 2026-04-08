# GitHub Copilot Instructions — {ProjectName}

## Project Overview

{ExecutiveSummary}

## Architecture

### Tech Stack
{TechStack}

### Directory Layout
```
{DirectoryLayout}
```

### Data Model
```
{DataModelHierarchy}
```

### Key Design Decisions
{KeyDesignDecisions}

## Documentation Map

| What | Where | When to Read |
|------|-------|--------------|
| System architecture | `docs/architecture/SAO.md` | Before big changes |
| User journey / all Acts | `docs/features/user_journey.md` | Feature planning |
| Feature specs (BDD) | `docs/features/act-*/` | Before implementing any feature |
| UI patterns & IA | `docs/ux/IA_guidelines.md` | Before building UI |
| Development rules | `.windsurf/rules/*.md` | Always active |
| Process workflows | `.windsurf/workflows/*/` | When running a workflow |

## Available Workflows

| Workflow | Purpose | Activities | When to Use |
|----------|---------|------------|-------------|
{WorkflowTable}

## Available Skills

{SkillsTable}

## Artifact Templates

| Template | Workflow | Purpose | Location |
|----------|----------|---------|----------|
{ArtifactTemplateTable}

## Coding Conventions

### Commit Format (Angular Convention)
```
<type>(<scope>): <subject>
```
Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Code Style
{CodeStyleRules}

### Logging
{LoggingConventions}

### Testing
- Test runner: {TestRunner}
- Test-first: write test before implementation
- No mocks in integration tests
- 100% pass rate required
- Commands:
```bash
{TestCommands}
```

## AI/Human Collaboration

### What AI Should Do
- Code generation following established patterns from SAO.md
- Test implementation (unit, integration, e2e)
- Documentation generation (docstrings, README updates)
- Refactoring within architectural boundaries

### What AI Should NOT Do Without Human Approval
- Architectural decisions outside established patterns
- Security-sensitive implementations
- Production deployment decisions
- Deleting functions, classes, or files

### Quality Gates
1. All tests pass (unit, integration, linting)
2. Code coverage meets project threshold
3. Documentation generated for public APIs
4. Code follows patterns from SAO.md
5. Human review before merge

### Escalation
- Ambiguous requirements → ask human
- Outside architectural patterns → ask human
- Security-sensitive code → flag for review

## Development Workflow

### Implementation Order
1. Read feature spec in `docs/features/act-*/`
2. Read `docs/architecture/SAO.md` for context
3. Backend: models → services → views
4. Frontend: templates + interactions
5. Tests: write before implementation
6. PR with all changes

{AdditionalBPEDetails}

## Running Locally
```bash
{SetupCommands}
```

## Placeholder Reference

- `{ProjectName}` — Name of the project
- `{ExecutiveSummary}` — From SAO.md Executive Summary
- `{TechStack}` — Languages, frameworks, databases from SAO.md
- `{DirectoryLayout}` — From SAO.md Project Structure section
- `{DataModelHierarchy}` — From SAO.md or models
- `{KeyDesignDecisions}` — Top 3-5 decisions from SAO.md
- `{WorkflowTable}` — Auto-generated from `.windsurf/workflows/*/`
- `{SkillsTable}` — Auto-generated from `.windsurf/workflows/*/skills/`
- `{ArtifactTemplateTable}` — Auto-generated from `.windsurf/workflows/*/artifacts/`
- `{CodeStyleRules}` — From `.windsurf/rules/` or team conventions
- `{LoggingConventions}` — From logging rules
- `{TestRunner}` — pytest, jest, etc.
- `{TestCommands}` — Test execution commands
- `{AdditionalBPEDetails}` — Condensed BPE workflow steps
- `{SetupCommands}` — Setup, install, run commands
