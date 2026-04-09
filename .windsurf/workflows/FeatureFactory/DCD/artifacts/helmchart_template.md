# Artifact: Helm Chart Template

**Workflow**: DCD — Design & Deploy CICD
**Purpose**: Reference Helm chart structure for application deployment

## Chart Structure

```
deploy/helm/{project}/
├── Chart.yaml                ← Chart metadata
├── values.yaml               ← Default values (production-like)
├── values-local.yaml         ← Local K8s overrides (1 replica, no ECR)
├── values-blue.yaml          ← Blue namespace overrides
├── values-green.yaml         ← Green namespace overrides
└── templates/
    ├── _helpers.tpl           ← Template helper functions
    ├── deployment.yaml        ← Deployment manifest
    ├── service.yaml           ← Service manifest
    ├── configmap.yaml         ← ConfigMap manifest
    ├── secret.yaml            ← Secret manifest (template only)
    └── ingress.yaml           ← (optional) Ingress/ALB manifest
```

## Chart.yaml

```yaml
apiVersion: v2
name: {project}
description: Helm chart for {project}
type: application
version: 0.1.0
appVersion: "0.1.0"
```

## values.yaml (defaults)

```yaml
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
  ENVIRONMENT: "production"

healthCheck:
  path: /health
  port: 8000
  livenessInitialDelay: 15
  readinessInitialDelay: 5
```

## values-local.yaml

```yaml
replicaCount: 1
namespace: local

image:
  repository: "{project}"
  tag: "local"
  pullPolicy: Never

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi

config:
  ENVIRONMENT: "local"
  LOG_LEVEL: "DEBUG"
```

## values-blue.yaml

```yaml
namespace: blue
config:
  ENVIRONMENT: "blue"
```

## values-green.yaml

```yaml
namespace: green
config:
  ENVIRONMENT: "green"
```

## Deployment Commands

```bash
# Local
helm upgrade --install {project} deploy/helm/{project} \
  -f deploy/helm/{project}/values-local.yaml \
  --namespace local --create-namespace

# Blue
helm upgrade --install {project} deploy/helm/{project} \
  -f deploy/helm/{project}/values-blue.yaml \
  --set image.tag=$(git rev-parse --short HEAD) \
  --namespace blue --create-namespace --wait

# Green
helm upgrade --install {project} deploy/helm/{project} \
  -f deploy/helm/{project}/values-green.yaml \
  --set image.tag=$(git rev-parse --short HEAD) \
  --namespace green --create-namespace --wait
```

## Conventions

- `values.yaml` = production-like defaults (always merged first)
- Per-env files only override what differs (namespace, config, resources)
- Image tag set at deploy time via `--set image.tag=...`
- `--wait` flag in CI/CD ensures deployment health before proceeding
- Secrets: never stored in values files; use `kubectl create secret` or external secrets
