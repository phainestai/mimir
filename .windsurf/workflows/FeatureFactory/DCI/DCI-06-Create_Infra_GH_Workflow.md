# Activity: Create Infra GH Workflow

**Activity ID**: 79
**Order**: 6
**Phase**: Elaboration
**Dependencies**: None

## Description

Create Infra GH Workflow

## Guidance

# Create Infra GitHub Actions Workflow

## Objective

Create a GitHub Actions workflow in the infra repo that automates CDK deployment and traffic switching. The workflow is a **thin wrapper around `make` targets** — no business logic in YAML.

---

## Process

### 1. Create `.github/workflows/infra.yml`

Use the `DCI/artifacts/infra_gh_workflow.yml` template as starting point.

The workflow has three jobs:

1. **deploy** — runs on push to `main`, calls `make deploy`
2. **traffic-switch** — manual trigger (`workflow_dispatch`), calls `make traffic-switch`
3. **traffic-rollback** — manual trigger, calls `make traffic-rollback`

```yaml
name: Infrastructure

on:
  push:
    branches: [main]
    paths:
      - 'stacks/**'
      - 'app.py'
      - 'cdk.json'
  workflow_dispatch:
    inputs:
      action:
        description: 'Action to perform'
        required: true
        type: choice
        options:
          - deploy
          - traffic-switch
          - traffic-rollback
          - status

permissions:
  id-token: write
  contents: read

jobs:
  infra:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.action == 'traffic-switch' && 'production' || 'infrastructure' }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Setup Node (for CDK)
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: make provision

      - name: Run action
        run: |
          ACTION="${{ github.event.inputs.action || 'deploy' }}"
          case "$ACTION" in
            deploy)          make deploy ;;
            traffic-switch)  make traffic-switch ;;
            traffic-rollback) make traffic-rollback ;;
            status)          make status ;;
          esac
```

### 2. Configure GitHub Environments

In GitHub repo settings, create two environments:

- **infrastructure** — auto-approve for `make deploy` (CDK changes)
- **production** — require manual approval for `make traffic-switch` (DNS changes affect live traffic)

### 3. Configure Secrets

| Secret | Description |
|--------|-------------|
| `AWS_ROLE_ARN` | IAM role ARN for CDK deployment (OIDC federation) |

| Variable | Description |
|----------|-------------|
| `AWS_REGION` | AWS region (e.g., `us-east-1`) |

### 4. Configure OIDC Federation

Instead of storing AWS access keys, use GitHub OIDC provider:

```python
# Add to a new stacks/github_oidc_stack.py (or inline in app.py)
# Creates IAM role that GitHub Actions can assume via OIDC
```

### 5. Test Workflow

```bash
# Push a CDK change → workflow should trigger and deploy
git push origin main

# Manually trigger traffic-switch
# GitHub UI → Actions → Infrastructure → Run workflow → action: traffic-switch
```

### 6. Commit

```bash
git add .github/workflows/infra.yml
git commit -m "ci: add GitHub Actions workflow for infra deploy and traffic switching"
```

---

## Deliverables

- ✅ **`.github/workflows/infra.yml`** created with deploy/switch/rollback jobs
- ✅ **GitHub environments** configured (infrastructure, production)
- ✅ **AWS OIDC federation** configured (no stored credentials)
- ✅ **Manual approval** required for traffic-switch
- ✅ **Workflow tested** — deploy on push, manual switch

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Infra Repo Scaffold** (Template, Required) — produced by Scaffold Infra Repo & CDK Project (#75).
- **CDK Stack Templates** (Code, Required) — produced by Build VPC & Networking Stack (#76).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **Infra GH Actions Workflow** (Code) - Required

## Artifacts Consumed

- **Infra Repo Scaffold** (Template) - Required
- **CDK Stack Templates** (Code) - Required

## Notes

No additional notes.
