# {ProjectName} — AI Context

> **When to use**: At the start of every new conversation or task. This file provides the AI agent with a complete map of the project's documentation, workflows, skills, and artifact templates.

## Project Overview

{ExecutiveSummary}

## Architecture Quick Reference

- **Tech Stack**: {TechStack}
- **Key Design Decisions**: {KeyDesignDecisionsSummary}
- **Full details**: Read `docs/architecture/SAO.md`

## Documentation Map

| What | Where | When to Read |
|------|-------|--------------|
| System architecture | `docs/architecture/SAO.md` | Before big changes |
| User journey / all Acts | `docs/features/user_journey.md` | Feature planning |
| Feature specs (BDD) | `docs/features/act-*/` | Before implementing any feature |
| UI patterns & IA | `docs/ux/IA_guidelines.md` | Before building UI |
| Development rules | `.windsurf/rules/*.md` | Always active (auto-loaded) |
| Process workflows | `.windsurf/workflows/*/` | When running a workflow |

## Available Workflows

| Workflow | Purpose | Activities | Location |
|----------|---------|------------|----------|
{WorkflowTable}

**Primary feature delivery workflow**: BPE (Build Feature) — use this for all feature implementation.

## Available Skills

{SkillsTable}

## Artifact Templates

| Template | Workflow | Purpose | Location |
|----------|----------|---------|----------|
{ArtifactTemplateTable}

## AI/Human Collaboration Summary

**AI does**: Code generation, test implementation, documentation, refactoring within patterns.
**Human does**: Architecture decisions, code review, security-sensitive work, deployment.
**Escalate to human**: Ambiguous requirements, outside-pattern decisions, security code.
**Quality gates**: All tests pass → coverage threshold met → docs generated → human review → merge.

## Development Workflow (BPE Summary)

1. Read feature spec in `docs/features/act-*/`
2. Read `docs/architecture/SAO.md` for context
3. Backend: models → services → views
4. Frontend: templates + interactions
5. Tests: write before implementation, 100% pass rate
6. PR with all changes

## Existing Rules (auto-loaded)

The following rules in `.windsurf/rules/` are automatically active. Do NOT duplicate their content:

{ExistingRulesList}

## Placeholder Reference

- `{ProjectName}` — Name of the project
- `{ExecutiveSummary}` — From SAO.md Executive Summary
- `{TechStack}` — Languages, frameworks, databases
- `{KeyDesignDecisionsSummary}` — 1-2 sentence summary of top decisions
- `{WorkflowTable}` — Auto-generated from `.windsurf/workflows/*/`
- `{SkillsTable}` — Auto-generated from `.windsurf/workflows/*/skills/`
- `{ArtifactTemplateTable}` — Auto-generated from `.windsurf/workflows/*/artifacts/`
- `{ExistingRulesList}` — Auto-generated list of `.windsurf/rules/*.md` files with descriptions
