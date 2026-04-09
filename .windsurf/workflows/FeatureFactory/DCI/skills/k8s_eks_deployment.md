# Skill: K8s in EKS — Deployment Patterns

**Capability Domain**: CONTAINER_ORCHESTRATION
**Technology Stack**: Kubernetes + AWS EKS

## Overview

Reference patterns for deploying applications to EKS with blue/green namespaces, Helm charts, ConfigMaps, Secrets, and health checks. Covers both local (Docker Desktop K8s / minikube) and cloud (EKS) deployment.

## Reference Implementation

### Pattern 1: Blue/Green Namespace Setup

```yaml
# namespaces.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: blue
  labels:
    environment: blue
    role: active    # or "idle" — managed by traffic switch
---
apiVersion: v1
kind: Namespace
metadata:
  name: green
  labels:
    environment: green
    role: idle      # or "active"
```

**Convention:**
- `blue` and `green` are permanent namespaces
- `role` label tracks which is currently `active` (prod) vs `idle` (standby)
- Application is always deployed to **both** namespaces
- Traffic switching happens at DNS level (Route53), not K8s level

### Pattern 2: Deployment Manifest

```yaml
# deploy/k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {project}
  namespace: ${NAMESPACE}  # blue or green
  labels:
    app: {project}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {project}
  template:
    metadata:
      labels:
        app: {project}
    spec:
      containers:
        - name: app
          image: ${ECR_REPO}:${IMAGE_TAG}
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: {project}-config
            - secretRef:
                name: {project}-secrets
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              cpu: 250m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
```

### Pattern 3: Service Manifest

```yaml
# deploy/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {project}
  namespace: ${NAMESPACE}
spec:
  type: ClusterIP  # or LoadBalancer for direct access
  selector:
    app: {project}
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
```

### Pattern 4: ConfigMap (per environment)

```yaml
# deploy/k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {project}-config
  namespace: ${NAMESPACE}
data:
  ENVIRONMENT: ${NAMESPACE}
  LOG_LEVEL: "INFO"
  DATABASE_HOST: "${DB_HOST}"
  # Add application-specific config here
```

### Pattern 5: Secrets

```yaml
# deploy/k8s/secrets.yaml (template — values injected at deploy time)
apiVersion: v1
kind: Secret
metadata:
  name: {project}-secrets
  namespace: ${NAMESPACE}
type: Opaque
stringData:
  SECRET_KEY: "${SECRET_KEY}"
  DATABASE_PASSWORD: "${DB_PASSWORD}"
```

**Security note:** Never commit actual secret values. Use:
- `kubectl create secret` at deploy time, or
- AWS Secrets Manager + External Secrets Operator, or
- Sealed Secrets

### Pattern 6: Helm Chart Structure

```
deploy/helm/{project}/
├── Chart.yaml
├── values.yaml              ← defaults
├── values-local.yaml        ← local Docker Desktop / minikube overrides
├── values-blue.yaml         ← blue namespace overrides
├── values-green.yaml        ← green namespace overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── ingress.yaml          ← (optional) ALB Ingress Controller
    └── _helpers.tpl
```

### Pattern 7: Helm Values (per environment)

```yaml
# values.yaml (defaults)
replicaCount: 2
image:
  repository: "{account}.dkr.ecr.{region}.amazonaws.com/{project}"
  tag: "latest"
  pullPolicy: IfNotPresent
service:
  type: ClusterIP
  port: 80
  targetPort: 8000
resources:
  requests:
    cpu: 250m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
config:
  LOG_LEVEL: "INFO"
```

```yaml
# values-local.yaml
replicaCount: 1
image:
  repository: "{project}"
  tag: "local"
  pullPolicy: Never  # Use local image
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

```yaml
# values-blue.yaml
namespace: blue
config:
  ENVIRONMENT: "blue"
```

```yaml
# values-green.yaml
namespace: green
config:
  ENVIRONMENT: "green"
```

### Pattern 8: Helm Deploy Commands (Make Targets)

```makefile
# In app monorepo Makefile

HELM_CHART := deploy/helm/{project}
ENV ?= local
NAMESPACE ?= $(ENV)

deploy: ## Deploy to environment (ENV=local|blue|green)
	helm upgrade --install {project} $(HELM_CHART) \
		-f $(HELM_CHART)/values.yaml \
		-f $(HELM_CHART)/values-$(ENV).yaml \
		--set image.tag=$(shell git rev-parse --short HEAD) \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--wait --timeout 300s

deploy-local: ## Deploy to local K8s (Docker Desktop / minikube)
	$(MAKE) deploy ENV=local

deploy-blue: ## Deploy to blue namespace
	$(MAKE) deploy ENV=blue

deploy-green: ## Deploy to green namespace
	$(MAKE) deploy ENV=green
```

### Pattern 9: kubectl Cheat Sheet

```bash
# Context management
aws eks update-kubeconfig --name {cluster} --region {region}
kubectl config current-context
kubectl config use-context {context}

# Namespace operations
kubectl get ns
kubectl get all -n blue
kubectl get all -n green

# Pod debugging
kubectl get pods -n blue -o wide
kubectl logs -n blue {pod-name} --tail=50 -f
kubectl exec -it -n blue {pod-name} -- /bin/sh
kubectl describe pod -n blue {pod-name}

# Deployment management
kubectl rollout status deployment/{project} -n blue
kubectl rollout undo deployment/{project} -n blue
kubectl scale deployment/{project} -n blue --replicas=3

# Quick health check
kubectl get pods -n blue -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\n"}{end}'
```

### Pattern 10: Local K8s Development

```bash
# Docker Desktop K8s
# Enable in Docker Desktop → Settings → Kubernetes → Enable Kubernetes

# Or minikube
minikube start --cpus 2 --memory 4096

# Build and load local image (no ECR needed)
docker build -t {project}:local .
# For minikube:
minikube image load {project}:local

# Deploy locally
make deploy-local

# Port forward for local testing
kubectl port-forward -n local svc/{project} 8080:80
# Access at http://localhost:8080
```

## Common Pitfalls

1. **Image pull errors** — Ensure ECR auth is configured; for local, use `imagePullPolicy: Never`
2. **Resource limits** — Set them; K8s will OOM-kill pods without limits
3. **Health checks** — Without them, K8s can't detect unhealthy pods
4. **Namespace isolation** — Blue and green should never share resources
5. **Secret management** — Never commit secrets; use external secret managers in production
6. **Helm `--wait`** — Always use in CI/CD to fail fast if deployment doesn't become ready
