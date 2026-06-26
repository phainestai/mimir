.DEFAULT_GOAL := help
PYTHON  := .venv/bin/python
PIP     := .venv/bin/pip
PYTEST  := .venv/bin/pytest
RUFF    := .venv/bin/ruff

##@ General

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Provision

.PHONY: provision
provision: ## Python venv + deps, migrations, dark-factory CLI tools, verify
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@cp -n .env.example .env 2>/dev/null && echo "Created .env from .env.example — fill in your values" || echo ".env already exists"
	$(PYTHON) manage.py migrate --noinput
	@bash scripts/provision-factory-deps.sh
	@bash scripts/check-factory-prereqs.sh
	@echo ""
	@echo "Provision complete."
	@echo "  App:  make run"
	@echo "  MCP:  make mcp"
	@echo "  Personal DB (once): make dev-db-init   # needs MIMIR_DB_PATH in .env"
	@echo "  Factory: scripts/preflight.sh '<milestone>' then scripts/factory.sh '<slug>'"

.PHONY: factory-check
factory-check: ## Re-verify all factory prereqs (includes gh auth + cursor-agent)
	@bash scripts/check-factory-prereqs.sh --strict

.PHONY: provision-factory
provision-factory: ## Alias: re-install factory CLI deps only (full setup: make provision)
	@bash scripts/provision-factory-deps.sh
	@bash scripts/check-factory-prereqs.sh

##@ Development

.PHONY: run
run: ## Start Django web server (port 8000)
	$(PYTHON) manage.py runserver 8000

.PHONY: mcp
mcp: ## Start MCP server for the default admin user
	$(PYTHON) manage.py mcp_server --user=admin

.PHONY: shell
shell: ## Open Django shell
	$(PYTHON) manage.py shell

.PHONY: migrate
migrate: ## Run pending migrations
	$(PYTHON) manage.py migrate --noinput

.PHONY: makemigrations
makemigrations: ## Generate new migrations
	$(PYTHON) manage.py makemigrations

.PHONY: createsuperuser
createsuperuser: ## Create a Django superuser
	$(PYTHON) manage.py createsuperuser

.PHONY: demo
demo: ## Load demo FeatureFactory data
	$(PYTHON) manage.py create_demo_fdd

##@ Testing
# Test settings only for test targets — do not export globally (breaks make run → mimir_test.db).

.PHONY: test
test: export DJANGO_SETTINGS_MODULE := mimir.settings.test
test: ## Run all tests (mirrors CI)
	$(PYTEST) tests/ \
	  --ignore=tests/e2e \
	  --ignore=tests/integration/test_mcp_server_acceptance.py \
	  --ignore=tests/integration/test_mcp_facade.py \
	  --ignore=tests/integration/test_mcp_e2e_all_tools.py \
	  --ignore=tests/unit/test_activity_graph_service.py

.PHONY: test-unit
test-unit: export DJANGO_SETTINGS_MODULE := mimir.settings.test
test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/

.PHONY: test-integration
test-integration: export DJANGO_SETTINGS_MODULE := mimir.settings.test
test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ \
	  --ignore=tests/integration/test_mcp_server_acceptance.py \
	  --ignore=tests/integration/test_mcp_facade.py \
	  --ignore=tests/integration/test_mcp_e2e_all_tools.py

.PHONY: test-e2e
test-e2e: export DJANGO_SETTINGS_MODULE := mimir.settings.test
test-e2e: ## Run Playwright E2E tests (requires running server)
	$(PYTEST) tests/e2e/

##@ Code Quality

.PHONY: lint
lint: ## Run ruff linter + format check
	$(RUFF) check .
	$(RUFF) format --check .

.PHONY: format
format: ## Auto-format code with ruff
	$(RUFF) format .

.PHONY: lint-fix
lint-fix: ## Run ruff linter with auto-fix
	$(RUFF) check --fix .

##@ Database
# Committed seed: mimir.db. Personal sandbox: mimir.dev.db via MIMIR_DB_PATH in .env.
# Production on EB uses Postgres (DATABASE_URL env var).

.PHONY: dev-db-init
dev-db-init: ## [local] Copy seed mimir.db → mimir.dev.db (first-time personal sandbox)
	@if [ -f mimir.dev.db ]; then \
	  echo "mimir.dev.db already exists — use 'make refresh-dev-db' to reset from seed."; \
	  exit 1; \
	fi
	cp mimir.db mimir.dev.db
	@echo "Created mimir.dev.db from mimir.db."
	@echo "Set MIMIR_DB_PATH=mimir.dev.db in .env (see .env.example), then: make run"

.PHONY: refresh-dev-db
refresh-dev-db: ## [local] Overwrite mimir.dev.db from seed mimir.db and run migrations
	cp mimir.db mimir.dev.db
	$(PYTHON) manage.py migrate --noinput
	@echo "mimir.dev.db refreshed from committed seed (mimir.db)."

.PHONY: dev-db-reset
dev-db-reset: ## [local] Delete mimir.dev.db and recreate from seed mimir.db
	@echo "WARNING: This will delete mimir.dev.db and all personal local data."
	@read -p "Continue? [y/N] " ans && [ "$$ans" = "y" ]
	rm -f mimir.dev.db mimir.dev.db-shm mimir.dev.db-wal
	cp mimir.db mimir.dev.db
	$(PYTHON) manage.py migrate --noinput
	@echo "mimir.dev.db recreated from seed."

.PHONY: db-reset
db-reset: ## [local] Delete mimir.db and re-run migrations (destroys committed seed file — rare)
	@echo "WARNING: This will delete mimir.db and all data in the seed database."
	@read -p "Continue? [y/N] " ans && [ "$$ans" = "y" ]
	rm -f mimir.db mimir.db-shm mimir.db-wal
	$(PYTHON) manage.py migrate --noinput
	@echo "Database reset. Run 'make demo' to reload demo data."

.PHONY: backup
backup: ## [prod] pg_dump + dumpdata to S3 — requires S3_BACKUP_BUCKET and DATABASE_URL
	@bash scripts/pre-deploy-backup.sh

##@ Deploy (AWS EB)

# Release flow (mirrors Huginn):
#   gh release create vX.Y.Z
#     → CI: test → build → deploy-idle.sh (dynamically resolves idle env) → staging smoke
#   make swap   (after human review of idle URL)
#     → promote-prod.sh: resolves live/idle, revision guard (/health/ or VersionLabel), swap, smoke
#
# Two physical EB envs whose CNAMEs rotate on every swap:
#   mimir-prod  /  mimir-idle
# Route53 CNAME → mimir-prod.eba-… (stable label; follows the swap automatically).
EB_APP    ?= mimir
EB_ENV_A  ?= mimir-prod
EB_ENV_B  ?= mimir-idle
AWS_REGION ?= us-east-1

.PHONY: swap
swap: ## [prod] Promote idle → prod: resolve live/idle, SHA guard, CNAME swap, smoke prod
	@EB_APP=$(EB_APP) EB_ENV_A=$(EB_ENV_A) EB_ENV_B=$(EB_ENV_B) \
	  AWS_DEFAULT_REGION=$(AWS_REGION) bash scripts/promote-prod.sh

.PHONY: eb-status
eb-status: ## Show health, CNAME, and version of both EB environments
	@aws elasticbeanstalk describe-environments \
	  --application-name $(EB_APP) \
	  --environment-names $(EB_ENV_A) $(EB_ENV_B) \
	  --query "Environments[*].{Env:EnvironmentName,Status:Status,Health:Health,Version:VersionLabel,CNAME:CNAME}" \
	  --output table --region $(AWS_REGION)

##@ Cleanup

.PHONY: clean
clean: ## Remove Python bytecode and pytest cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml report.html
