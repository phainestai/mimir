# Activity: Build CD Pipeline

**Activity ID**: 85
**Order**: 5
**Phase**: Elaboration
**Dependencies**: None

## Description

Build CD Pipeline

## Guidance

# Build CD Pipeline (GitHub Actions)

## Objective

Create a GitHub Actions CD workflow that deploys the application to the idle environment, runs smoke tests, and waits for manual approval before switching production traffic. The workflow is triggered after CI succeeds or manually.

---

## Process

### 1. Create `.github/workflows/cd.yml`

Use `DCD/artifacts/cd_workflow.yml` template as starting point.

```yaml
name: CD

on:
  workflow_run:
    workflows: [CI]
    types: [completed]
    branches: [main]
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag to deploy (default: latest)'
        required: false
        default: 'latest'

permissions:
  id-token: write
  contents: read

jobs:
  # --------------------------------------------------------------------------
  # Deploy to idle environment
  # --------------------------------------------------------------------------
  deploy-idle:
    if: >-
      github.event_name == 'workflow_dispatch' ||
      github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    environment: staging
    outputs:
      idle_env: ${{ steps.detect.outputs.idle }}
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Setup tools
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: make provision

      - name: Configure kubectl
        run: aws eks update-kubeconfig --name ${{ vars.EKS_CLUSTER }} --region ${{ vars.AWS_REGION }}

      - name: Detect idle environment
        id: detect
        run: |
          # Determine which environment is currently idle
          # This reads the current DNS state from the infra repo
          IDLE=$(cd ../${{ vars.PROJECT }}-infra && make traffic-status 2>/dev/null | grep "idle" | awk '{print $2}' || echo "green")
          echo "idle=$IDLE" >> $GITHUB_OUTPUT
          echo "Deploying to idle environment: $IDLE"

      - name: Deploy to idle
        run: make deploy ENV=${{ steps.detect.outputs.idle }}

  # --------------------------------------------------------------------------
  # Smoke tests on idle
  # --------------------------------------------------------------------------
  smoke-test:
    needs: deploy-idle
    runs-on: ubuntu-latest
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

      - name: Install dependencies
        run: make provision

      - name: Run smoke tests on idle
        run: make smoke-test ENV=idle

  # --------------------------------------------------------------------------
  # Manual approval → switch traffic
  # --------------------------------------------------------------------------
  switch:
    needs: smoke-test
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
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

      - name: Install dependencies
        run: make provision

      - name: Switch traffic to new deployment
        run: make switch

      - name: Verify production
        run: make smoke-test ENV=prod

      - name: Show final status
        run: make pipeline-status
```

### 2. Configure GitHub Environments

| Environment | Approval Required | Purpose |
|-------------|-------------------|---------|
| `staging` | No | Auto-deploy to idle |
| `production` | Yes (designated reviewers) | Manual approval before traffic switch |

### 3. Configure Additional Variables

| Variable | Value |
|----------|-------|
| `EKS_CLUSTER` | EKS cluster name |
| `PROJECT` | Project name |

### 4. Test the CD Pipeline

```bash
# Option A: Trigger via CI completion
# Push a change → CI runs → CD triggers automatically

# Option B: Manual trigger
# GitHub Actions → CD → Run workflow → image_tag: latest
```

### 5. Verify the Flow

1. **deploy-idle** — Pods running in idle namespace
2. **smoke-test** — Smoke tests pass against idle URL
3. **switch** — Pending approval in GitHub UI
4. Approve → traffic switches → prod smoke tests run

### 6. Commit

```bash
git add .github/workflows/cd.yml
git commit -m "ci: add CD pipeline (deploy idle → smoke → approve → switch)"
```

---

## Deliverables

- ✅ **`.github/workflows/cd.yml`** created
- ✅ **Deploy-idle job**: `make deploy ENV=idle`
- ✅ **Smoke-test job**: `make smoke-test ENV=idle`
- ✅ **Switch job**: manual approval → `make switch` → `make smoke-test ENV=prod`
- ✅ **GitHub environments** configured (staging, production)
- ✅ **Pipeline tested** end-to-end

## Agent

None

## Skill

**Title**: GitHub Actions Patterns
**Capability Domain**: CI_CD
**Technology Stack**: GitHub Actions

## Rules

None

## Artifacts Produced

- **CD Pipeline (GitHub Actions)** (Code) - Required

## Artifacts Consumed

- **Helm Chart Template** (Template) - Required

## Notes

No additional notes.
