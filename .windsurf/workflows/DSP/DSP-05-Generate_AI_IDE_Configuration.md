# Activity: Generate AI IDE Configuration

**Activity ID**: TBD
**Order**: 5
**Phase**: Configuration
**Dependencies**: Predecessor: DSP-04 (Choose Target AI IDE)

## Description

Generate AI IDE Configuration

## Guidance

# Generate AI IDE Configuration

## Objective

Assemble a comprehensive configuration file for the chosen AI IDE target, pulling from SAO.md, ESM artifacts, available workflows, skills, artifact templates, and coding conventions. The output file gives the AI agent everything it needs to understand the project and start building features.

---

## Process

### 1. Gather Inputs

Collect all source material identified in DSP-01 through DSP-03:

| Source | What to Extract | Config Section |
|--------|----------------|----------------|
| `docs/architecture/SAO.md` | Executive summary, architecture, design principles, tech stack, directory layout | Sections 1-3 |
| `docs/features/user_journey.md` | Acts, user journey overview | Section 4 (Docs Map) |
| `docs/features/act-*/` | Feature file inventory | Section 4 (Docs Map) |
| `docs/ux/IA_guidelines.md` | UI patterns, design system | Section 4 (Docs Map) |
| `.windsurf/workflows/*/` | Workflow names, descriptions, activity counts | Section 5 (Workflows) |
| `.windsurf/workflows/*/skills/` | Skill titles, capability domains, tech stacks | Section 6 (Skills) |
| `.windsurf/workflows/*/artifacts/` | Template file names and descriptions | Section 7 (Artifact Templates) |
| `.windsurf/rules/*.md` | Coding conventions, testing discipline, commit format | Section 9 (Conventions) |

### 2. Assemble Config File

Use the appropriate template from `DSP/artifacts/` based on the target chosen in DSP-04.

The config file MUST contain these sections (section numbers vary by template):

#### Section: What Is {ProjectName}

Extract from SAO.md Executive Summary. One paragraph explaining what the project does and its key innovation.

#### Section: Architecture

Extract from SAO.md:
- High-level component diagram (ASCII or Mermaid)
- Directory layout (from Project Structure section)
- Data model hierarchy
- Key design decisions (top 3-5)

#### Section: Documentation Map

Point to all key docs with brief descriptions:

```markdown
| What | Where | When to Read |
|------|-------|--------------|
| System architecture | `docs/architecture/SAO.md` | Before big changes |
| User journey / all Acts | `docs/features/user_journey.md` | Feature planning |
| Feature specs (BDD) | `docs/features/act-*/` | Before implementing any feature |
| UI patterns & IA | `docs/ux/IA_guidelines.md` | Before building UI |
| Development rules | `.windsurf/rules/*.md` | Always active |
| Process workflows | `.windsurf/workflows/*/` | When running a workflow |
```

#### Section: Available Workflows

List each workflow with its purpose, activity count, and when to use it:

```markdown
| Workflow | Purpose | Activities | When to Use |
|----------|---------|------------|-------------|
| ESM | Envision the System | 7 | Defining what to build |
| DTA | Define Architecture | 18 | Making architectural decisions |
| DSP | Deploy Software Process | 6 | Setting up AI IDE |
| BSP | Bootstrap Project | 8 | Scaffolding new project |
| BPE | Build Feature | N | **Primary workflow for feature delivery** |
| EST | Estimate the Project | 8 | Estimation and planning |
```

#### Section: Available Skills

List skills found in workflow `skills/` directories:

```markdown
| Skill | Capability Domain | Tech Stack | Location |
|-------|-------------------|------------|----------|
| {SkillTitle} | {Domain} | {Stack} | `.windsurf/workflows/{WF}/skills/{file}` |
```

If no skills exist yet, note: "No skills defined yet. Skills provide technology-specific implementation guidance for workflow activities."

#### Section: Artifact Templates

List templates found in workflow `artifacts/` directories:

```markdown
| Template | Workflow | Purpose | Location |
|----------|----------|---------|----------|
| User Journey Template | ESM | Structure for user journey doc | `ESM/artifacts/user_journey_template.md` |
| Feature File Template | ESM | BDD scenario format | `ESM/artifacts/feature_file_template.feature` |
| SAO Template | DTA | Architecture document structure | `DTA/artifacts/sao_document_template.md` |
| CLAUDE.md Template | DSP | AI config for Claude Code | `DSP/artifacts/claude_md_template.md` |
```

#### Section: AI/Human Collaboration Patterns

Absorbed from the former DSP-05 content. Include:

**AI Agent Responsibilities:**
- Code generation following established patterns
- Test implementation (unit, integration, e2e)
- Documentation generation (docstrings, README updates)
- Refactoring within architectural boundaries

**Human Developer Responsibilities:**
- Architectural decisions and boundary setting
- Code review and quality validation
- Security-sensitive implementations
- Production deployment decisions

**Quality Gates for AI-Generated Code:**
1. All tests pass (unit, integration, linting)
2. Code coverage meets project threshold
3. Documentation generated for public APIs
4. Code follows established patterns from SAO.md
5. Human review and approval before merge

**Escalation Rules:**
- Ambiguous requirements → ask human
- Architectural decisions outside patterns → ask human
- Security-sensitive code → flag for human review

#### Section: Coding Conventions

Extract from `.windsurf/rules/` or document directly:
- Commit format (Angular convention)
- Method size limits (20-30 lines max for public methods)
- Import organization (module-level only)
- Logging standards (INFO level, what/why/where/when)
- Testing discipline (test-first, pytest, no mocks in integration tests)

#### Section: Development Workflow (How to Build Features)

Reference the BPE workflow with a condensed summary:
1. Read the feature spec in `docs/features/act-*/`
2. Read SAO.md for architectural context
3. Backend: models → services → views
4. Frontend: templates + interactions
5. Tests: write before implementation, 100% pass rate required
6. PR with all changes

#### Section: Running Locally

Extract from SAO.md or document:
- Setup commands (venv, install, migrate)
- Start dev server
- Run tests
- Load demo data

### 3. Customize for Target Format

**Claude Code** (`CLAUDE.md`):
- Single file, flat Markdown sections with `---` separators
- Use `##` for main sections
- Keep under ~500 lines (Claude Code reads this on every conversation)

**GitHub Copilot** (`.github/copilot-instructions.md`):
- Single file, similar to CLAUDE.md but may use different heading conventions
- Focus on coding patterns and conventions (Copilot is code-completion oriented)

**Windsurf** (`.windsurf/rules/_ai-context.md`):
- Create a summary context rule that points to existing rules and workflows
- Do NOT duplicate content already in `.windsurf/rules/*.md`
- Focus on the docs map, workflow inventory, and skills inventory
- Add conditional trigger: "When starting a new conversation or task"

**Cursor** (`.cursor/rules/_ai-context.mdc`):
- Similar to Windsurf but uses MDC format with YAML frontmatter
- Mirror the Windsurf content adapted to Cursor conventions

### 4. Present to User

Show the generated config file to the user before writing it:
- Highlight any sections that are thin or missing source material
- Ask if any project-specific conventions should be added
- Confirm file location is correct

---

## Deliverables

- ✅ **AI IDE config file generated** for chosen target(s)
- ✅ **All 10 sections populated** from source material
- ✅ **User reviewed** the generated content
- ✅ **Ready to proceed** to DSP-06 (Review & Commit)

## Artifacts Produced

- AI IDE configuration file (one per selected target):
  - `CLAUDE.md` — uses `DSP/artifacts/claude_md_template.md`
  - `.github/copilot-instructions.md` — uses `DSP/artifacts/copilot_instructions_template.md`
  - `.windsurf/rules/_ai-context.md` — uses `DSP/artifacts/windsurf_cursor_rules_template.md`
  - `.cursor/rules/_ai-context.mdc` — adapted from Windsurf template

## Artifacts Consumed

- `docs/architecture/SAO.md`
- `docs/features/user_journey.md`
- `docs/features/act-*/` (inventory)
- `docs/ux/IA_guidelines.md`
- `.windsurf/workflows/*/` (all workflow metadata)
- `.windsurf/workflows/*/skills/` (all skills)
- `.windsurf/workflows/*/artifacts/` (all templates)
- `.windsurf/rules/*.md` (coding conventions)
- DSP-03 inventory report (workflows, skills, templates)
- DSP-04 target selection

## Notes

This is the core value-producing activity of the DSP workflow. The quality of the generated config directly determines how effectively the AI agent can work on the project. A well-crafted config means the AI can pick up any feature file and start building immediately, following the right patterns, using the right workflows, and producing the right artifacts.

The existing `CLAUDE.md` in the Mimir project itself serves as a **living example** of what this activity produces for the Claude Code target.