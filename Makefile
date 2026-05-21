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
provision: ## Create .venv, install deps, copy .env.example → .env
	python3 -m venv .venv
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt -q
	@cp -n .env.example .env 2>/dev/null && echo "Created .env from .env.example — fill in your values" || echo ".env already exists"
	$(PYTHON) manage.py migrate --noinput
	@echo "Provision complete. Run 'make run' to start the web server."

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

export DJANGO_SETTINGS_MODULE ?= mimir.settings.test

.PHONY: test
test: ## Run all tests (mirrors CI)
	$(PYTEST) tests/ \
	  --ignore=tests/e2e \
	  --ignore=tests/integration/test_mcp_server_acceptance.py \
	  --ignore=tests/integration/test_mcp_facade.py \
	  --ignore=tests/integration/test_mcp_e2e_all_tools.py \
	  --ignore=tests/unit/test_activity_graph_service.py

.PHONY: test-unit
test-unit: ## Run unit tests only
	$(PYTEST) tests/unit/

.PHONY: test-integration
test-integration: ## Run integration tests only
	$(PYTEST) tests/integration/ \
	  --ignore=tests/integration/test_mcp_server_acceptance.py \
	  --ignore=tests/integration/test_mcp_facade.py \
	  --ignore=tests/integration/test_mcp_e2e_all_tools.py

.PHONY: test-e2e
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
# Local dev uses SQLite (mimir.db). Production on EB uses Postgres (DATABASE_URL env var).

.PHONY: db-reset
db-reset: ## [local] Delete mimir.db and re-run migrations (destroys all local data)
	@echo "WARNING: This will delete mimir.db and all local data."
	@read -p "Continue? [y/N] " ans && [ "$$ans" = "y" ]
	rm -f mimir.db
	$(PYTHON) manage.py migrate --noinput
	@echo "Database reset. Run 'make demo' to reload demo data."

.PHONY: backup
backup: ## [prod] Dump prod Postgres to S3 — requires S3_BUCKET and DATABASE_URL env vars
	@[ -n "$$S3_BUCKET" ] || (echo "S3_BUCKET not set"; exit 1)
	@[ -n "$$DATABASE_URL" ] || (echo "DATABASE_URL not set"; exit 1)
	pg_dump "$$DATABASE_URL" | aws s3 cp - s3://$$S3_BUCKET/mimir-$(shell date +%Y%m%d-%H%M%S).sql
	@echo "Backup uploaded to s3://$$S3_BUCKET"

##@ Deploy (AWS EB)

# gh release → mimir-idle → make swap → mimir-prod (live)
# Route53 aliases the mimir-prod ALB directly, so promotion = deploy idle's
# version to mimir-prod (CNAME swap alone has no effect on live traffic).
EB_APP    ?= mimir
EB_IDLE   ?= mimir-idle
EB_PROD   ?= mimir-prod
AWS_REGION ?= us-east-1

.PHONY: swap
swap: ## [prod] Blue/green swap: exchange CNAMEs between mimir-idle and mimir-prod
	@echo "Swapping CNAMEs: mimir-idle ↔ mimir-prod"
	aws elasticbeanstalk swap-environment-cnames \
	  --source-environment-name $(EB_IDLE) \
	  --destination-environment-name $(EB_PROD) \
	  --region $(AWS_REGION)
	@echo "Waiting for mimir-prod to be Ready..."
	@until [ "$$(aws elasticbeanstalk describe-environments \
	  --application-name $(EB_APP) \
	  --environment-names $(EB_PROD) \
	  --query 'Environments[0].Status' \
	  --output text --region $(AWS_REGION))" = "Ready" ]; do \
	  printf '.'; sleep 10; done
	@echo ""
	@echo "Swap complete — verifying:"
	@curl -s https://mimir.featurefactory.io/health/ | python3 -c \
	  "import sys,json; d=json.load(sys.stdin); print(f'  revision={d[\"revision\"]}  status={d[\"status\"]}')"

.PHONY: eb-status
eb-status: ## Show health and version of both EB environments
	@aws elasticbeanstalk describe-environments \
	  --application-name $(EB_APP) \
	  --environment-names $(EB_IDLE) $(EB_PROD) \
	  --query "Environments[*].{Env:EnvironmentName,Status:Status,Health:Health,Version:VersionLabel,CNAME:CNAME}" \
	  --output table --region $(AWS_REGION)

##@ Cleanup

.PHONY: clean
clean: ## Remove Python bytecode and pytest cache
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache htmlcov .coverage coverage.xml report.html
