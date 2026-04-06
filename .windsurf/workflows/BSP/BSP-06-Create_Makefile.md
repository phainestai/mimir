# Activity: Create Makefile

**Activity ID**: TBD
**Order**: 6
**Phase**: Configure
**Dependencies**: Predecessor: BSP-05 (Configure Dev Tooling)

## Description

Create Makefile

## Guidance

# Create Makefile

## Objective

Create a comprehensive Makefile that serves as the single entry point for all development operations: provisioning, running, testing, linting, formatting, and cleanup. All targets must be idempotent and well-documented.

---

## Process

### 1. Makefile Structure

```makefile
.PHONY: help provision run test test-unit test-integration test-e2e lint format clean

# Default target
.DEFAULT_GOAL := help

# Variables
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MANAGE := $(PYTHON) manage.py
PORT := 8000

##@ General

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Provision

provision: _check-prereqs _venv _pip-install _npm-install _db-init ## Install all prerequisites & dependencies
	@echo "✅ Provisioning complete. Run 'make run' to start."

_check-prereqs:
	@echo "Checking prerequisites..."
	@command -v python3 >/dev/null 2>&1 || { echo "❌ python3 not found"; exit 1; }
	@command -v git >/dev/null 2>&1 || { echo "❌ git not found"; exit 1; }
	@echo "✅ Prerequisites OK"

_venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
	else \
		echo "✅ Virtual environment exists"; \
	fi

_pip-install:
	@echo "Installing Python dependencies..."
	@$(PIP) install -r requirements.txt -q

_npm-install:
	@if [ -f "package.json" ]; then \
		echo "Installing Node.js dependencies..."; \
		npm install; \
	fi

_db-init:
	@echo "Running database migrations..."
	@$(MANAGE) migrate --run-syncdb

##@ Development

run: ## Start development server
	@$(MANAGE) runserver 0.0.0.0:$(PORT)

shell: ## Open Django shell
	@$(MANAGE) shell

dbshell: ## Open database shell
	@$(MANAGE) dbshell

##@ Testing

test: ## Run all tests
	@$(PYTEST) tests/ -v --tb=short 2>&1 | tee tests.log

test-unit: ## Run unit tests only
	@$(PYTEST) tests/unit/ -v --tb=short

test-integration: ## Run integration tests only
	@$(PYTEST) tests/integration/ -v --tb=short

test-e2e: ## Run E2E tests only
	@$(PYTEST) tests/e2e/ -v --tb=short

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@$(VENV)/bin/ptw tests/ -- -v --tb=short

coverage: ## Run tests with coverage report
	@$(PYTEST) tests/ --cov --cov-report=html --cov-report=term-missing

##@ Code Quality

lint: ## Run linter (ruff check)
	@$(VENV)/bin/ruff check .

format: ## Auto-format code (ruff format)
	@$(VENV)/bin/ruff format .
	@$(VENV)/bin/ruff check --fix .

typecheck: ## Run type checker (if configured)
	@$(VENV)/bin/mypy . || echo "mypy not configured — skipping"

precommit: ## Run all pre-commit hooks
	@$(VENV)/bin/pre-commit run --all-files

##@ Database

migrate: ## Run database migrations
	@$(MANAGE) migrate

makemigrations: ## Create new migrations
	@$(MANAGE) makemigrations

##@ Cleanup

clean: ## Remove build artifacts, caches, logs
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage coverage.xml
	@rm -rf node_modules
	@rm -f tests.log
	@echo "✅ Cleaned"

clean-all: clean ## Remove everything including venv
	@rm -rf $(VENV)
	@echo "✅ Cleaned all (including venv)"
```

### 2. Adapt to Stack

- If no Node.js in stack: remove `_npm-install` and `package.json` check
- If no Django: replace `manage.py` commands with framework equivalents
- If additional tools (e.g., Docker): add `docker-up`, `docker-down` targets
- All targets should follow the pattern: verb-noun (e.g., `test-unit`, `db-init`)

### 3. Verify All Targets

Run each target and verify it works:
```bash
make help        # Should show formatted help
make provision   # Should complete without errors
make lint        # Should run (may report issues — that's OK)
make format      # Should run
make test        # Should run (may have 0 tests — that's OK)
make clean       # Should clean up
```

### 4. Commit Makefile

```bash
git add Makefile
git commit -m "chore(make): create Makefile with provision, run, test, lint, format, clean targets"
```

---

## Deliverables

- ✅ **Makefile** created with all standard targets
- ✅ **`make help`** shows all targets with descriptions
- ✅ **`make provision`** installs everything from scratch
- ✅ **All targets** verified as functional
- ✅ **Makefile committed**

## Artifacts Produced

- `Makefile`

## Artifacts Consumed

- `docs/architecture/SAO.md` — Technology Stack Table (for tool paths)
- `docs/architecture/SAO.md` — § Test Strategy (DTA-06) for test targets
- `docs/architecture/SAO.md` — § Developer Experience (DTA-16) for quality targets

## Notes

The Makefile is the **single source of truth** for all dev operations. README.md references it. CI/CD pipelines call its targets. New developers only need to know `make provision && make run`.
