# Activity: Add Container & Deploy Make Targets

**Activity ID**: TBD
**Order**: 3
**Phase**: Build
**Dependencies**: Predecessor: DCD-02 (Create Helm Chart & Values)

## Description

Add Container & Deploy Make Targets

## Guidance

# Add Container & Deploy Make Targets

## Objective

Extend the application Makefile (from BSP-06) with container, deployment, and operations targets. Uncomment and configure the `##@ Deployment` section in the Makefile template. After this activity, every deployment operation is a single `make` command.

---

## Process

### 1. Add Dockerfile

Create a multi-stage Dockerfile in the app monorepo:

```dockerfile
# Dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "{project}.wsgi:application"]
```

### 2. Uncomment & Configure Makefile Deployment Section

In the Makefile (from `BSP/artifacts/makefile_template.mk`), uncomment and configure the `##@ Deployment` section:

```makefile
# Add/update these variables at the top
PROJECT := {project}
AWS_REGION := {region}
AWS_ACCOUNT := {account-id}
ECR_REPO := $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com/$(PROJECT)
HELM_CHART := deploy/helm/$(PROJECT)
ENV ?= local
NAMESPACE ?= $(ENV)
DOMAIN := {domain}
IMAGE_TAG := $(shell git rev-parse --short HEAD)

##@ Containers

containers: ## Build and push Docker image to ECR
	@echo "Building container $(ECR_REPO):$(IMAGE_TAG)..."
	docker build -t $(ECR_REPO):$(IMAGE_TAG) -t $(ECR_REPO):latest .
	@echo "Pushing to ECR..."
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(AWS_ACCOUNT).dkr.ecr.$(AWS_REGION).amazonaws.com
	docker push $(ECR_REPO):$(IMAGE_TAG)
	docker push $(ECR_REPO):latest
	@echo "✅ Pushed $(ECR_REPO):$(IMAGE_TAG)"

containers-local: ## Build Docker image for local K8s (no push)
	docker build -t $(PROJECT):local .
	@echo "✅ Built $(PROJECT):local"

##@ Deployment

deploy: ## Deploy to environment (ENV=local|blue|green)
	@echo "Deploying to $(ENV) (namespace: $(NAMESPACE))..."
	helm upgrade --install $(PROJECT) $(HELM_CHART) \
		-f $(HELM_CHART)/values.yaml \
		-f $(HELM_CHART)/values-$(ENV).yaml \
		--set image.tag=$(IMAGE_TAG) \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--wait --timeout 300s
	@echo "✅ Deployed to $(ENV)"

deploy-local: ## Deploy to local K8s
	$(MAKE) containers-local
	$(MAKE) deploy ENV=local

deploy-blue: ## Deploy to blue namespace
	$(MAKE) deploy ENV=blue

deploy-green: ## Deploy to green namespace
	$(MAKE) deploy ENV=green

##@ Traffic & Operations

smoke-test: ## Run smoke tests (ENV=blue|green|prod)
	@echo "Running smoke tests on $(ENV)..."
	$(PYTEST) tests/smoke/ -v --base-url=https://$(ENV).$(DOMAIN) 2>&1 | tee smoke-tests.log
	@echo "✅ Smoke tests passed on $(ENV)"

switch: ## Switch prod ↔ idle DNS traffic
	@echo "Switching traffic: prod ↔ idle..."
	cd ../$(PROJECT)-infra && $(MAKE) traffic-switch
	@echo "✅ Traffic switched. Verify at https://prod.$(DOMAIN)"

rollback: ## Rollback to previous deployment
	@echo "Rolling back traffic..."
	cd ../$(PROJECT)-infra && $(MAKE) traffic-rollback
	@echo "✅ Rolled back"

verify: ## Full verification: test + integration + smoke
	$(MAKE) test
	$(MAKE) test-integration
	$(MAKE) smoke-test ENV=$(ENV)
	@echo "✅ Full verification passed for $(ENV)"

pipeline-status: ## Show current deployment status
	@echo "=== Blue Namespace ==="
	kubectl get pods -n blue 2>/dev/null || echo "  (not deployed)"
	@echo "=== Green Namespace ==="
	kubectl get pods -n green 2>/dev/null || echo "  (not deployed)"
	@echo "=== DNS ==="
	dig +short prod.$(DOMAIN) 2>/dev/null || echo "  (not configured)"
	dig +short idle.$(DOMAIN) 2>/dev/null || echo "  (not configured)"
```

### 3. Verify All New Targets

```bash
make help                  # Should show new sections: Containers, Deployment, Traffic
make containers-local      # Should build Docker image
make deploy-local          # Should deploy to local K8s
make pipeline-status       # Should show pod status
```

### 4. Test Local End-to-End

```bash
# Build and deploy locally
make deploy-local

# Verify pods running
kubectl get pods -n local

# Port forward and test
kubectl port-forward -n local svc/{project} 8080:80
curl http://localhost:8080/health
```

### 5. Commit

```bash
git add Makefile Dockerfile
git commit -m "feat(deploy): add container and deployment make targets"
```

---

## Deliverables

- ✅ **Dockerfile** created (multi-stage)
- ✅ **Makefile extended** with `containers`, `deploy`, `switch`, `rollback`, `verify`, `pipeline-status`
- ✅ **`make help`** shows new sections
- ✅ **Local deploy** verified (`make deploy-local`)
- ✅ **All new `make` targets** functional

## Artifacts Produced

- `Dockerfile`
- Updated `Makefile` with deployment targets

## Artifacts Consumed

- `BSP/artifacts/makefile_template.mk` — extension point for `##@ Deployment`
- `deploy/helm/{project}/` (from DCD-02) — Helm chart
- `DCI/skills/k8s_eks_deployment.md` — deploy commands

## Notes

The `switch` and `rollback` targets delegate to the infra repo's Makefile (`make traffic-switch`). This keeps traffic management logic in one place (infra repo) while the app repo provides a convenient shortcut.
