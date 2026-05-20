# Contributing to Mimir

Thank you for your interest in contributing to Mimir! This guide will help you understand our development workflow and quality standards.

## Prerequisites

1. **Set up your development environment** (see [README.md](README.md))
2. **Optional — bug reports:** To create real GitHub issues from the Feedback UI or MCP locally, set `GITHUB_TOKEN` and optional `GITHUB_BUG_REPO` (see [README.md](README.md) Quick Start → Bug reports).
3. **Configure Mimir MCP** in your IDE (Windsurf, Claude Desktop, or Cursor)
4. **Familiarize yourself with the FeatureFactory playbook** - it's already in the database!

## Development Workflow

Mimir was built using the **FeatureFactory** playbook, which is included in the database. All contributions should follow this same workflow.

### Overview: Build Page Workflow (BPE1-BPE7)

The FeatureFactory playbook provides a complete feature development workflow:

| Activity | Name | Purpose |
|----------|------|---------|
| **BPE1** | Plan Feature | Analyze requirements, assess codebase, create implementation plan |
| **BPE2** | Implement Backend | Build models, services, Django views with tests |
| **BPE3** | Implement Frontend | Create Django templates with HTMX interactions |
| **BPE4** | Feature Acceptance Tests | Write Django Test Client integration tests |
| **BPE5** | Journey Certification | Add Playwright E2E tests for critical paths |
| **BPE6** | Check Definition of Done | Validate compliance with all project rules |
| **BPE7** | Finalize Feature | Run full test suite, update dependencies, commit |

### Step-by-Step Process

#### 1. Plan Your Feature (BPE1)

Start by planning your implementation:

```
Mimir, plan [FEATURE-NAME] per BPE1 Plan Feature
```

Mimir will:
- Read architecture documentation
- Review feature specifications
- Assess existing codebase
- Ask clarification questions
- Create a detailed implementation plan
- Generate GitHub issues

**Wait for approval before proceeding!**

#### 2. Implement Backend (BPE2)

Once your plan is approved:

```
Mimir, implement backend per BPE2
```

This follows:
- **Skeleton-first**: Create classes/methods with full docstrings
- **Test-first**: Write tests before implementation
- **Small increments**: Method-by-method development
- **Comprehensive logging**: INFO-level logging for all operations
- **Commit often**: After each completed method

#### 3. Implement Frontend (BPE3)

Build the UI layer:

```
Mimir, implement frontend per BPE3
```

Requirements:
- Django templates (no React/Vue/Angular)
- HTMX for dynamic interactions
- Semantic `data-testid` attributes on all interactive elements
- Bootstrap tooltips on all buttons
- Font Awesome icons for actions
- Responsive design

#### 4. Write Feature Acceptance Tests (BPE4)

Add integration tests using Django Test Client:

```
Mimir, create acceptance tests per BPE4
```

Key rules:
- **No mocking** in integration tests
- One test per scenario
- Cover all paths (happy, error, edge cases)
- Tests must run in <5 seconds
- 100% pass rate required

#### 5. Add Journey Certification (BPE5)

For features with HTMX/JavaScript or critical user paths:

```
Mimir, add journey tests per BPE5
```

Uses Playwright for browser-based testing of complete user journeys.

#### 6. Check Definition of Done (BPE6)

**Before submitting your PR, always run:**

```
Mimir, run BPE6 on my code
```

This validates:
- ✅ Test-first development compliance
- ✅ All tests passing (100% pass rate)
- ✅ Concise methods (20-30 lines max)
- ✅ Comprehensive logging
- ✅ No mocking in integration tests
- ✅ Semantic `data-testid` attributes
- ✅ Angular commit convention
- ✅ Documentation updated
- ✅ No temporary files

**Any deviations must be approved by maintainers.**

#### 7. Finalize Feature (BPE7)

Complete the feature:

```
Mimir, finalize feature per BPE7
```

This will:
- Run full test suite (must be 100% pass)
- Update `requirements.txt`
- Make final commit
- Close GitHub issues

## Quick Reference Commands

```bash
# Plan new feature
Mimir, plan FOB-LOGIN-1 per BPE1 Plan Feature

# Get current playbook list
Mimir, list available playbooks

# View workflow details
Mimir, show me the Build Page workflow

# Check your code before PR
Mimir, run BPE6 on my code

# Process enhancement request
Mimir, process enhancement request per BPE8 Process Change Request
```

## Code Quality Standards

### Test Requirements

- **100% test pass rate** - no exceptions
- Use `pytest` for unit and integration tests
- Use Django Test Client for view tests
- Use Playwright for E2E tests
- No mocking in integration tests

### Code Style

- **Concise methods**: Top-level methods 20-30 lines max
- **Skeleton-first**: Full docstrings before implementation
- **Test-first**: Write tests before logic
- **Small increments**: Commit after each method
- **Informative logging**: INFO-level logging for all operations

### UI/Frontend

- **Django templates + HTMX** (no SPA frameworks)
- **Semantic test IDs**: `data-testid="feature-action"` format
- **Bootstrap tooltips**: On all buttons (explain action or why disabled)
- **Font Awesome icons**: On all action buttons
- **Accessibility**: Proper ARIA labels and semantic HTML

### Commit Messages

Follow Angular convention:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example:
```
feat(mcp): add workflow list command

Implement mcp1_list_workflows tool to retrieve workflows for a playbook.
Includes full workflow details with nested activities.

Closes #42
```

## Testing Your Changes

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/integration/test_playbook_crud.py -v

# Run with coverage
pytest tests/ --cov=mimir_mcp --cov-report=html

# Run E2E tests (headed mode for debugging)
pytest tests/e2e/ --headed
```

## Development Tools

### Start Web UI
```bash
python manage.py runserver 8000
# Open http://localhost:8000
# Ensure dev superuser: python manage.py create_default_admin
```

### Test MCP Server
```bash
python manage.py mcp_server --user=admin
# Press Ctrl+C to exit
```

### Database Management
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Open Django admin
# Navigate to http://localhost:8000/admin
```

## Project Structure

```
mimir/
├── docs/
│   ├── architecture/SAO.md      # System architecture
│   ├── features/                # BDD specifications
│   └── ux/                      # User journeys, flows
├── mimir/
│   ├── methodology/             # Core Django app
│   │   ├── models/              # Playbook, Workflow, Activity
│   │   ├── services/            # Business logic
│   │   ├── views/               # Django views (HTML)
│   │   └── templates/           # Django templates + HTMX
│   └── mimir_mcp/               # MCP server implementation
│       ├── server.py            # MCP server
│       └── tools/               # MCP tools (CRUD operations)
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests (no mocking)
│   ├── e2e/                     # Playwright E2E tests
│   └── fixtures/                # Test data
└── .windsurf/                   # Original workflows (reference)
```

## Getting Help

1. **Ask Mimir**: Use the MCP interface to ask questions about the codebase
2. **Read the docs**: Check `docs/architecture/SAO.md` for design patterns
3. **View feature files**: BDD specifications in `docs/features/`
4. **Check existing code**: Mimir was built with FeatureFactory - it's a working example!

## Pull Request Checklist

Before submitting a PR:

- [ ] Ran `Mimir, run BPE6 on my code` and resolved all issues
- [ ] All tests passing (100% pass rate)
- [ ] Feature acceptance tests added (BPE4)
- [ ] Journey certification tests added if needed (BPE5)
- [ ] Documentation updated
- [ ] Commit messages follow Angular convention
- [ ] No temporary files or debug code
- [ ] `requirements.txt` updated if dependencies added

## Questions?

Open an issue or ask Mimir directly through your IDE, or email denis@nyu.edu

---

**Remember:** Mimir was built using the FeatureFactory workflow. Follow the same process, and you'll maintain the same quality standards that created this system. 
