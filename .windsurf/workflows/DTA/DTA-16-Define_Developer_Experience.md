# Activity: Define Developer Experience

**Activity ID**: TBD
**Order**: 16
**Phase**: Support
**Dependencies**: Predecessor: DTA-04 (Define Code Organization)

## Description

Define Developer Experience

## Guidance

# Define Developer Experience

## Objective

Define IDE setup, code quality tooling, local debugging approach, onboarding flow, and inner loop speed targets.

---

## Decisions to Make

### 1. IDE Setup

- **Recommended IDE**: VS Code, PyCharm, Cursor, Windsurf, etc.
- **Extensions/plugins**: Which are required? Which are recommended?
- **Workspace settings**: Shared `.vscode/settings.json` or `.idea/` config
- **Debug configurations**: Launch configs for backend, frontend, tests
- **AI assistant config**: MCP server configuration for Mimir integration

### 2. Code Quality Tooling

- **Linter**: flake8, ruff, pylint, eslint
- **Formatter**: black, ruff format, prettier
- **Type checker**: mypy, pyright
- **Pre-commit hooks**: Which checks run before commit?
- **Configuration files**: `pyproject.toml`, `.flake8`, `.prettierrc`
- **Makefile targets**: `make lint`, `make format`, `make typecheck`

### 3. Local Debugging

- **Breakpoint debugging**: IDE debugger, pdb, ipdb
- **Log tailing**: How to watch logs in real-time during development
- **DB inspection**: Django admin, DB browser, management commands
- **Network inspection**: How to inspect HTTP requests (Django Debug Toolbar)
- **Test debugging**: How to run and debug individual tests

### 4. Onboarding

- **README**: What must be in the root README for a new developer?
- **`make provision`**: Single command to install all prerequisites
- **`make run`**: Single command to start the full application
- **Time-to-first-feature target**: "New developer ships first feature within X hours"
- **Onboarding checklist**: Step-by-step from `git clone` to running tests

### 5. Inner Loop Speed

- **Hot reload**: Auto-restart on file changes (Django runserver, webpack HMR)
- **Incremental builds**: Only rebuild what changed
- **Test watch mode**: Auto-run affected tests on save
- **Build performance**: Target build times per operation

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `DEVEX_IDE`
- `DEVEX_QUALITY`
- `DEVEX_ONBOARD`

Report coverage and gaps.

---

## Deliverables

- ✅ **IDE setup** documented with recommended extensions and debug configs
- ✅ **Code quality tooling** configured (linter, formatter, pre-commit)
- ✅ **Local debugging** approach defined
- ✅ **Onboarding flow** documented with time-to-first-feature target
- ✅ **Inner loop speed** targets set
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Developer experience decision → contributes to `artifacts/sao_document_template.md` § "15. Developer Experience"

## Artifacts Consumed

- Code organization decision from DTA-04
- Test strategy decision from DTA-06

## Notes

No additional notes.
