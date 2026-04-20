# CLAUDE.md — Mimir Development Guide

## What Is Mimir

Mimir is a **self-evolving engineering playbook platform**. It lets teams document, evolve, and leverage software development methodologies through a Django web UI and an MCP (Model Context Protocol) server that AI assistants query directly.

**Two-part system:**
- **FOB (this repo)** — Django 5 app with SQLite, runs MCP server + web server concurrently
- **HOMEBASE** (separate repo) — Django + HTMX, eventing → Neo4j graph DB, aggregates PIPs from FOBs

**Key innovation:** AI assistants can propose playbook improvements (PIPs) that engineers review and approve.

**Current Status:** Production-ready MVP with full CRUDLF for Playbooks, Workflows, Activities, Agents, Skills, Phases (as modeled), Artifacts (partial), and **Rules** (playbook-scoped, Activity M2M). MCP integration includes 50+ tools (including rule CRUDLF and `set_activity_rules`).

---

## Architecture

### Directory Layout

```
mimir/                        # Django project config (settings, urls, wsgi)
methodology/                  # Core Django app (models, services, views, templates)
  models/                     # Playbook, Workflow, Phase, Activity, Artifact, Skill, Agent, Rule, …
  services/                   # Business logic (shared by UI and MCP)
  views/                      # Thin Django view controllers
  utils/                      # markdown_renderer.py (Markdown + Mermaid)
mcp_integration/              # MCP server (thin wrappers over services)
  tools.py                    # MCP tool definitions (playbooks, workflows, activities, skills, rules, …)
  context.py                  # User context
  management/commands/mcp_server.py
accounts/                     # User auth
tests/
  unit/                       # Model and service unit tests
  integration/                # MCP tools, multi-model workflows
  e2e/                        # Playwright browser tests
docs/
  features/act-*/             # BDD Gherkin specs (source of truth for features)
  architecture/SAO.md         # System architecture overview (read before big changes)
  plans/                      # Per-feature implementation plans
  ux/                         # Design system, IA guidelines, user journey
.windsurf/
  rules/                      # 38 development convention rules
  workflows/FeatureFactory/   # Complete product development playbook (6 workflows)
    ESM/                      # Envision the System (7 activities)
    DTA/                      # Define Architecture (18 activities)
    DSP/                      # Deploy Software Process (6 activities)
    EST/                      # Estimate the Project (8 activities)
    BSP/                      # Bootstrap Project (8 activities)
    BPE/                      # Build Feature (8 activities)
```

### Data Model Hierarchy

```
Playbook (status: draft/released/disabled; version: 0.x → 1.0+)
  └─ Workflow (name, abbreviation, order)
       ├─ Phase (optional; currently string field, not separate model)
       └─ Activity (name, guidance: Markdown+Mermaid, order)
            └─ Artifact (input/output, producer/consumer)
Playbook also has: Agent, Skill, **Rule** (IDE-style rules; many-to-many with Activities)
```

**Implementation status:**
| Entity | Status |
|--------|--------|
| Playbook | ✅ Full CRUDLF |
| Workflow | ✅ Full CRUDLF + export/import |
| Activity | ✅ Full CRUDLF |
| Phase | ⚠️ String field only |
| Artifact | ⚠️ Model exists, partial |
| Agent | ✅ Full CRUDLF (Act 7) |
| Skill | ✅ Full CRUDLF (Act 8) |
| Rule | ✅ Full CRUDLF + export to `rules/` |
| PIP | ❌ Not built in FOB UI (V2 / Homebase narrative retained in specs) |

### Services Pattern

Services in `methodology/services/` are **shared by both UI views and MCP tools** — never add MCP-specific logic to services. MCP tools only add: user context lookup, permission check, serialization.

Version auto-increment (Activity update → increments grandparent Playbook version) happens in the MCP tool wrapper, not the service.

### MCP Access Rules

- **Draft playbooks** (v0.x): Full CRUD via MCP
- **Released playbooks** (v≥1.0): Read-only via MCP; changes must go through PIPs

---

## Terminology

| Internal Code | User-Facing UI |
|---------------|----------------|
| `methodology` (app, models, services) | "playbooks" |
| `MethodologyRepository` | — |
| `manage.py mcp_server` | — |

Always use "playbooks" in UI text; always use `methodology` in code.

---

## FeatureFactory Workflows

Mimir development follows the **FeatureFactory v3.8** playbook — a complete product development methodology from idea to shipped feature.

### Inception Phase (run once per project)

1. **ESM — Envision the System** (7 activities)
   - User journey, screen flows, feature files (BDD), IA guidelines, mockups
   - Output: `docs/features/**`, `docs/ux/screen-flow.drawio`

2. **DTA — Define Architecture** (18 activities)
   - Technical decisions across 16 domains → System Architecture Overview
   - Output: `docs/architecture/SAO.md`

3. **DSP — Deploy Software Process** (6 activities)
   - AI IDE configuration for Windsurf/Cursor/Claude
   - Output: `CLAUDE.md`, `.windsurf/rules/`, `.cursor/rules/`

4. **EST — Estimate the Project** (8 activities)
   - Two-level estimates, Monte Carlo forecast, client quote
   - Output: `docs/plans/ESTIMATION_TEMPLATE.xlsx`

### Delivery Loop (repeats every sprint)

5. **BSP — Bootstrap Project** (Sprint 0 only, 8 activities)
   - Scaffold project structure, dependencies, Makefile
   - Output: Runnable project with welcome page

6. **BPE — Build Feature** (Every sprint, 8 activities)
   - **BPE-01**: Plan feature implementation
   - **BPE-02**: Implement backend (models → services → views)
   - **BPE-03**: Implement frontend (templates + HTMX)
   - **BPE-04**: Feature Acceptance Tests (Django test client)
   - **BPE-05**: Journey Certification Tests (Playwright E2E)
   - **BPE-06**: Check Definition of Done
   - **BPE-07**: Finalize feature (commit, PR)
   - **BPE-08**: Process change requests

**EST-08** runs at end of every sprint to rebaseline estimates.

### Before Implementing Any Feature

1. Read the relevant feature spec in `docs/features/act-*/`
2. Read `docs/architecture/SAO.md` for architectural context
3. Follow **BPE workflow** step-by-step (see `.windsurf/workflows/FeatureFactory/BPE/`)
4. Create implementation plan in `docs/plans/` (BPE-01)

### Skeleton-First Pattern

```python
def create_workflow(self, playbook, name, description):
    """Create a new workflow in the given playbook.

    Args:
        playbook: Playbook instance
        name: str workflow name
        description: str
    Returns:
        Workflow instance
    Example return: Workflow(id=1, name="Design Features", ...)
    """
    raise NotImplementedError()
```

Write stub → write test (red) → implement → test passes (green) → commit.

---

## Coding Conventions

### Commit Format (Angular Convention — strict)

```
<type>(<scope>): <subject>

<body — what changed and why>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
Example: `feat(workflows): add export to JSON via MCP tool`

### Code Style

- Top-level methods: **20-30 lines max**; extract helpers for supporting logic
- Imports at **module level** — never inside functions
- Single responsibility per method
- Black + Ruff for formatting/linting

### Logging

- INFO level; log what/why/where/when
- Output to `logs/app.log`
- Include request/correlation IDs for debugging

---

## Testing

```bash
# Run all tests
pytest tests/

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v         # requires Playwright setup

# With coverage
pytest tests/ --cov=methodology --cov=mcp_integration
```

**Key rules:**
- **Test-first**: write test before implementation
- **No mocks in integration tests**: use real objects/DB (rule: `do-not-mock-in-integration-tests.md`)
- Run tests after every change

---

## Running Locally

```bash
# Setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate

# Web server (terminal 1)
python manage.py runserver 8000

# MCP server (terminal 2)
python manage.py mcp_server --user=admin

# Load demo data
python manage.py create_demo_fdd
```

Both processes share the same SQLite DB with a 20-second timeout for concurrent access.

---

## Key Reference Files

| What | Where |
|------|-------|
| System architecture | `docs/architecture/SAO.md` |
| All Acts / user journey | `docs/features/user_journey.md` |
| MCP tool definitions | `mcp_integration/tools.py` |
| Design system / UI patterns | `docs/ux/IA_guidelines.md` |
| Development rules (38) | `.windsurf/rules/*.md` |
| FeatureFactory playbook | `.windsurf/workflows/FeatureFactory/playbook.md` |
| BPE workflow (primary) | `.windsurf/workflows/FeatureFactory/BPE/` |
| Available skills (12) | `.windsurf/workflows/FeatureFactory/*/skills/` |
| Artifact templates (13) | `.windsurf/workflows/FeatureFactory/*/artifacts/` |
| Feature specs | `docs/features/act-*/` |

---

## UI Patterns

- **No SPA / no React** — Django templates + HTMX only
- **Bootstrap 5.3+** for all styling; add CSS variables, not raw overrides
- **Graphviz** for workflow/activity diagrams
- **Mermaid.js** for inline diagrams in activity guidance (Markdown)
- Always add `data-testid` attributes to interactive elements for Playwright tests
- Tooltips on complex form fields (consistent pattern per `docs/ux/IA_guidelines.md`)

---

## Iteration Protocol

When tasked with **"Work on Milestone #N"**:

1. Read milestone description — parse `<!-- MANIFEST -->` YAML block
2. Verify all `status-queued` issues exist for each scenario in manifest
3. Find next eligible scenario: `status-queued` + all `dependencies[]` issues are closed (`status-done`)
4. Apply `status-in-progress` label, remove `status-queued`
5. Post `<!-- EXECUTION_START -->` comment with timestamp and time budget
6. Follow **BPE-02 → BPE-05** to fill the skeleton (implement the `raise NotImplementedError()` stubs)
7. Monitor files touched vs `codebase_footprint[]` from issue `<!-- SCENARIO -->` block
8. Run `checkpoint.command` from issue YAML
9. If **PASS**: commit, close issue, comment actual_duration + `status-done`, go to step 3
10. If **FAIL**: go to Drift Handling below

### Drift Handling

- `time_overrun` < 120% of budget: post `<!-- DRIFT absorbed -->` comment, continue
- `test_failure` (first time): apply targeted fix, retry checkpoint once
  - Retry passes → continue (record retry in comment)
  - Retry fails → reclassify as `checkpoint_fail_retry` → **ESCALATE**
- `scope_expansion` of test/config file: add to footprint in issue YAML, continue
- `scope_expansion` of production source file → **ESCALATE**
- `time_overrun` ≥ 200% of budget → **ESCALATE**
- `checkpoint_fail_retry` (second failure after retry) → **ESCALATE**
- 2+ absorbed signals on same scenario → **ESCALATE**

### Escalation

Post on the issue and stop:
```
<!-- ESCALATE -->
type: {signal_type}
severity: escalated
detected_at: {ISO8601}
evidence: {specific evidence}
jedao_recommendation: {A: fix and retry | B: resequence | C: scope reduce}
await_human_decision: true
<!-- /ESCALATE -->
```
Apply label `drift-escalated`, remove `status-in-progress`. **Do not touch code until human posts a decision comment.**

Human decision keywords: `fix and retry` / `resequence` / `scope reduce` / `pause`

### Session Resume Protocol

On every session start when an iteration is active:
1. `gh issue list --label status-in-progress --json number,title,milestone`
2. If an issue has `status-in-progress` → that is where you left off
3. Re-run `checkpoint.command` from the issue `<!-- SCENARIO -->` YAML first
4. PASS → close issue, `status-done`, pull next scenario
5. FAIL → treat as first `test_failure`, apply retry protocol
6. No `status-in-progress` issues → find next `status-queued` eligible scenario

### Authority Model (Jedao)

**Can decide without asking:** reorder within same parallel group, absorb drift below threshold, retry checkpoint once, add test/config file to footprint, skip blocked scenario and return later

**Must escalate:** checkpoint fail after retry, production file outside footprint, time ≥ 2× budget, integration conflict not in manifest, 2+ absorbed signals on same scenario

**Cannot do:** drop a scenario, add scope, modify manifest goal, merge to main, create release without human review
