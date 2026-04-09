# Skill: GitHub Actions Patterns

**Capability Domain**: CI_CD
**Technology Stack**: GitHub Actions

## Overview

Reference patterns for building CI/CD pipelines with GitHub Actions. Covers workflow triggers, OIDC federation with AWS, environment protection rules, manual approval gates, Docker builds, ECR authentication, and the Makefile-first architecture.

## Reference Implementation

### Pattern 1: OIDC Federation with AWS (No Stored Credentials)

```yaml
permissions:
  id-token: write   # Required for OIDC
  contents: read

steps:
  - name: Configure AWS credentials
    uses: aws-actions/configure-aws-credentials@v4
    with:
      role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
      aws-region: ${{ vars.AWS_REGION }}
```

**Setup:**
1. Create OIDC provider in AWS IAM (GitHub's token endpoint)
2. Create IAM role with trust policy for GitHub repo
3. Store role ARN in GitHub secrets
4. Never store AWS access keys

### Pattern 2: ECR Authentication + Docker Push

```yaml
- name: Login to ECR
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push
  run: |
    IMAGE_TAG=$(git rev-parse --short HEAD)
    docker build -t ${{ vars.ECR_REPO }}:$IMAGE_TAG .
    docker push ${{ vars.ECR_REPO }}:$IMAGE_TAG
```

Or via Makefile (preferred):
```yaml
- name: Build and push
  run: make containers
```

### Pattern 3: Environment Protection Rules (Manual Approval)

```yaml
jobs:
  deploy:
    environment: staging        # Auto-approve
    # ...

  switch:
    needs: deploy
    environment: production     # Requires manual approval
    # ...
```

**Setup in GitHub:**
1. Settings → Environments → New environment
2. `staging`: no protection rules (auto-deploy)
3. `production`: add required reviewers (1-2 people)
4. Optional: add deployment branch rules (main only)

### Pattern 4: Workflow Triggers

```yaml
# CI: on every push and PR
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

# CD: triggered after CI succeeds
on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]

# Manual trigger with inputs
on:
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options: [deploy, rollback, status]
      environment:
        description: 'Target environment'
        required: false
        default: 'green'

# Path-filtered trigger (infra changes only)
on:
  push:
    branches: [main]
    paths:
      - 'stacks/**'
      - 'cdk.json'
```

### Pattern 5: Makefile-First Architecture

```yaml
# GOOD: Thin wrapper around make
steps:
  - run: make provision
  - run: make lint
  - run: make test
  - run: make containers

# BAD: Business logic in YAML
steps:
  - run: pip install -r requirements.txt
  - run: ruff check .
  - run: pytest tests/ -v
  - run: |
      docker build -t myapp .
      aws ecr get-login-password | docker login ...
      docker push ...
```

**Why Makefile-first:**
- Local and CI use identical commands
- Debug pipeline failures locally with `make {target}`
- Pipeline changes = Makefile changes, not YAML changes
- YAML only handles: checkout, auth, tool setup, `make` calls, approval gates

### Pattern 6: Conditional Job Execution

```yaml
jobs:
  build:
    # Only on main branch pushes (not PRs)
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'

  deploy:
    # Only if triggered manually or CI succeeded
    if: >-
      github.event_name == 'workflow_dispatch' ||
      github.event.workflow_run.conclusion == 'success'

  rollback:
    # Only with explicit confirmation
    if: github.event.inputs.confirm == 'rollback'
```

### Pattern 7: Job Dependencies and Outputs

```yaml
jobs:
  detect:
    outputs:
      environment: ${{ steps.detect.outputs.env }}
    steps:
      - id: detect
        run: echo "env=green" >> $GITHUB_OUTPUT

  deploy:
    needs: detect
    steps:
      - run: make deploy ENV=${{ needs.detect.outputs.environment }}

  verify:
    needs: [detect, deploy]
    steps:
      - run: make smoke-test ENV=${{ needs.detect.outputs.environment }}
```

### Pattern 8: Caching for Speed

```yaml
- name: Setup Python with cache
  uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'

- name: Cache node modules
  uses: actions/cache@v4
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('package-lock.json') }}
```

### Pattern 9: Workflow Status Badges

```markdown
<!-- In README.md -->
[![CI](https://github.com/{org}/{repo}/actions/workflows/ci.yml/badge.svg)](https://github.com/{org}/{repo}/actions/workflows/ci.yml)
[![CD](https://github.com/{org}/{repo}/actions/workflows/cd.yml/badge.svg)](https://github.com/{org}/{repo}/actions/workflows/cd.yml)
```

### Pattern 10: Emergency Rollback Workflow

```yaml
name: Rollback

on:
  workflow_dispatch:
    inputs:
      confirm:
        description: 'Type "rollback" to confirm'
        required: true

jobs:
  rollback:
    if: github.event.inputs.confirm == 'rollback'
    runs-on: ubuntu-latest
    environment: production  # Still requires approval
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}
      - run: make rollback
      - run: make smoke-test ENV=prod
```

## GitHub Environment Configuration

| Environment | Reviewers | Branch Rules | Purpose |
|-------------|-----------|-------------|---------|
| `infrastructure` | 1 reviewer | main only | CDK deployments |
| `staging` | None | main only | Auto-deploy to idle |
| `production` | 2 reviewers | main only | Traffic switch |

## Secrets and Variables

| Name | Type | Scope | Value |
|------|------|-------|-------|
| `AWS_ROLE_ARN` | Secret | Repository | IAM role ARN for OIDC |
| `AWS_REGION` | Variable | Repository | e.g., `us-east-1` |
| `ECR_REPO` | Variable | Repository | ECR repository URI |
| `EKS_CLUSTER` | Variable | Repository | EKS cluster name |
| `PROJECT` | Variable | Repository | Project name |

## Common Pitfalls

1. **Storing AWS keys** — Always use OIDC federation instead
2. **Business logic in YAML** — Move to Makefile targets
3. **Missing `--wait` on Helm** — Deployment may appear successful but pods crash later
4. **No approval gates** — Production switch MUST require human approval
5. **Workflow_run gotcha** — `workflow_run` uses the default branch's workflow file, not the PR's
6. **Permissions** — Always set minimal `permissions:` block; default is too broad
