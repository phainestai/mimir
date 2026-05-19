# Activity: Create Helm Chart & Values

**Activity ID**: 82
**Order**: 2
**Phase**: Elaboration
**Dependencies**: None

## Description

Create Helm Chart & Values

## Guidance

# Create Helm Chart & Values

## Objective

Create a Helm chart in the application monorepo with per-environment values files (local, blue, green). The chart templates K8s manifests (Deployment, Service, ConfigMap, Secret) and environment-specific values control image source, replicas, and config.

---

## Process

### 1. Create Helm Chart Structure

Use `DCD/artifacts/helmchart_template.md` as reference.

```bash
mkdir -p deploy/helm/{project}/templates
```

### 2. Create Chart.yaml

```yaml
# deploy/helm/{project}/Chart.yaml
apiVersion: v2
name: {project}
description: Helm chart for {project} application
type: application
version: 0.1.0
appVersion: "0.1.0"
```

### 3. Create templates/

Templates use Helm values for environment-specific configuration:

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Values.namespace | default .Release.Namespace }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - containerPort: {{ .Values.service.targetPort }}
          envFrom:
            - configMapRef:
                name: {{ .Release.Name }}-config
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 15
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .Values.service.targetPort }}
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}
  namespace: {{ .Values.namespace | default .Release.Namespace }}
spec:
  type: {{ .Values.service.type }}
  selector:
    app: {{ .Release.Name }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: {{ .Values.service.targetPort }}
```

**configmap.yaml:**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
  namespace: {{ .Values.namespace | default .Release.Namespace }}
data:
  {{- range $key, $value := .Values.config }}
  {{ $key }}: {{ $value | quote }}
  {{- end }}
```

### 4. Create Values Files

**values.yaml** (defaults):
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
```

**values-local.yaml** (local K8s):
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

**values-blue.yaml**:
```yaml
namespace: blue
config:
  ENVIRONMENT: "blue"
```

**values-green.yaml**:
```yaml
namespace: green
config:
  ENVIRONMENT: "green"
```

### 5. Verify Helm Template

```bash
# Lint chart
helm lint deploy/helm/{project}

# Template with local values (dry run)
helm template {project} deploy/helm/{project} \
  -f deploy/helm/{project}/values-local.yaml

# Template with blue values
helm template {project} deploy/helm/{project} \
  -f deploy/helm/{project}/values-blue.yaml
```

### 6. Commit

```bash
git add deploy/helm/
git commit -m "feat(deploy): add Helm chart with local/blue/green values"
```

---

## Deliverables

- ✅ **Helm chart** created at `deploy/helm/{project}/`
- ✅ **Templates**: deployment, service, configmap
- ✅ **Values files**: values.yaml, values-local.yaml, values-blue.yaml, values-green.yaml
- ✅ **`helm lint`** passes
- ✅ **`helm template`** renders correct manifests for each environment

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **Helm Chart Template** (Template) - Required

## Artifacts Consumed

None

## Notes

No additional notes.
