# ==============================================================================
# Makefile Template — FeatureFactory
# ==============================================================================
#
# Single entry point for all dev, infra, and deployment operations.
# CI/CD pipelines call these targets — no business logic in GH Actions.
#
# Sections:
#   General        — help
#   Provision      — prerequisites, venv, deps, db
#   Development    — run, shell, dbshell
#   Testing        — test, test-unit, test-integration, test-e2e, coverage
#   Code Quality   — lint, format, typecheck, precommit
#   Database       — migrate, makemigrations
#   Infrastructure — infra-deploy, infra-destroy, infra-status, traffic-switch, traffic-rollback (DCI)
#   Deployment     — containers, deploy, smoke-test, switch, rollback, verify (DCD)
#   Cleanup        — clean, clean-all
#
# Usage:
#   make help          — show all targets
#   make provision     — install everything from scratch
#   make run           — start dev server
#   make test          — run all tests
#
# Extension points:
#   DCI workflow adds ##@ Infrastructure targets
#   DCD workflow adds ##@ Deployment targets
# ==============================================================================

.PHONY: help provision run test test-unit test-integration test-e2e lint format clean

# Default target
.DEFAULT_GOAL := help

# ------------------------------------------------------------------------------
# Variables — adapt to your stack (read from SAO.md Technology Stack Table)
# ------------------------------------------------------------------------------
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest
MANAGE := $(PYTHON) manage.py
PORT := 8000

# Infrastructure variables (set by DCI workflow)
# AWS_REGION := us-east-1
# CDK_DIR := ../$(PROJECT)-infra
# EKS_CLUSTER := $(PROJECT)-cluster

# Deployment variables (set by DCD workflow)
# ECR_REPO := $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com/$(PROJECT)
# HELM_CHART := deploy/helm/$(PROJECT)
# ENV := local
# NAMESPACE := $(ENV)

# ==============================================================================
##@ General
# ==============================================================================

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

# ==============================================================================
##@ Provision
# ==============================================================================

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

# ==============================================================================
##@ Development
# ==============================================================================

run: ## Start development server
	@$(MANAGE) runserver 0.0.0.0:$(PORT)

shell: ## Open Django shell
	@$(MANAGE) shell

dbshell: ## Open database shell
	@$(MANAGE) dbshell

# ==============================================================================
##@ Testing
# ==============================================================================

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

# ==============================================================================
##@ Code Quality
# ==============================================================================

lint: ## Run linter (ruff check)
	@$(VENV)/bin/ruff check .

format: ## Auto-format code (ruff format)
	@$(VENV)/bin/ruff format .
	@$(VENV)/bin/ruff check --fix .

typecheck: ## Run type checker (if configured)
	@$(VENV)/bin/mypy . || echo "mypy not configured — skipping"

precommit: ## Run all pre-commit hooks
	@$(VENV)/bin/pre-commit run --all-files

# ==============================================================================
##@ Database
# ==============================================================================

migrate: ## Run database migrations
	@$(MANAGE) migrate

makemigrations: ## Create new migrations
	@$(MANAGE) makemigrations

# ==============================================================================
##@ Infrastructure (added by DCI workflow)
# ==============================================================================
#
# Uncomment and configure after completing DCI workflow.
# These targets operate on the infra repo (CDK stacks).
#
# infra-deploy: ## Deploy all CDK stacks (VPC, EKS, ECR, Route53)
# 	cd $(CDK_DIR) && cdk deploy --all --require-approval never
#
# infra-destroy: ## Destroy all CDK stacks (DANGEROUS)
# 	cd $(CDK_DIR) && cdk destroy --all --force
#
# infra-status: ## Show CDK stack status
# 	cd $(CDK_DIR) && cdk list && aws cloudformation describe-stacks --query 'Stacks[].{Name:StackName,Status:StackStatus}' --output table
#
# traffic-switch: ## Switch prod/idle DNS (Route53 weighted records)
# 	@echo "Switching traffic: idle → prod..."
# 	$(PYTHON) scripts/traffic_switch.py --action switch --region $(AWS_REGION)
#
# traffic-rollback: ## Rollback DNS to previous prod
# 	@echo "Rolling back traffic..."
# 	$(PYTHON) scripts/traffic_switch.py --action rollback --region $(AWS_REGION)

# ==============================================================================
##@ Deployment (added by DCD workflow)
# ==============================================================================
#
# Uncomment and configure after completing DCD workflow.
# These targets handle containerization, Helm deploys, and blue/green switching.
#
# containers: ## Build and push Docker images to ECR
# 	@echo "Building containers..."
# 	docker build -t $(ECR_REPO):$(shell git rev-parse --short HEAD) .
# 	docker push $(ECR_REPO):$(shell git rev-parse --short HEAD)
#
# deploy: ## Deploy to environment (ENV=local|blue|green)
# 	@echo "Deploying to $(ENV)..."
# 	helm upgrade --install $(PROJECT) $(HELM_CHART) \
# 		-f $(HELM_CHART)/values-$(ENV).yaml \
# 		--set image.tag=$(shell git rev-parse --short HEAD) \
# 		--namespace $(NAMESPACE) --create-namespace
#
# smoke-test: ## Run smoke tests against environment (ENV=blue|green)
# 	@echo "Running smoke tests on $(ENV)..."
# 	$(PYTEST) tests/smoke/ -v --base-url=https://$(ENV).$(DOMAIN)
#
# switch: ## Swap prod ↔ idle (blue/green)
# 	@echo "Switching prod ↔ idle..."
# 	$(PYTHON) scripts/traffic_switch.py --action switch --region $(AWS_REGION)
# 	@echo "✅ Switched. Verify at https://$(DOMAIN)"
#
# rollback: ## Rollback to previous deployment
# 	@echo "Rolling back deployment..."
# 	$(PYTHON) scripts/traffic_switch.py --action rollback --region $(AWS_REGION)
#
# verify: ## Run full verification (test + integration + smoke)
# 	$(MAKE) test
# 	$(MAKE) test-integration
# 	$(MAKE) smoke-test ENV=$(ENV)
#
# pipeline-status: ## Show current pipeline/deployment status
# 	@echo "=== EKS Pods ==="
# 	kubectl get pods -n blue
# 	kubectl get pods -n green
# 	@echo "=== DNS ==="
# 	dig +short prod.$(DOMAIN)
# 	dig +short idle.$(DOMAIN)

# ==============================================================================
##@ Cleanup
# ==============================================================================

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
