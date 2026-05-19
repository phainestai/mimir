# Activity: Build CI Pipeline

**Activity ID**: 84
**Order**: 4
**Phase**: Elaboration
**Dependencies**: None

## Description

Build CI Pipeline

## Guidance

# Build CI Pipeline (GitHub Actions)

## Objective

Create a GitHub Actions CI workflow in the application monorepo that runs on every push to `main`. The workflow calls `make` targets in sequence: test → lint → containers. This is the "build" half of the pipeline — it produces a tested, tagged container image in ECR.

---

## Process

### 1. Create `.github/workflows/ci.yml`

Use `DCD/artifacts/ci_workflow.yml` template as starting point.

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  id-token: write
  contents: read

env:
  PYTHON_VERSION: '3.12'
  NODE_VERSION: '20'

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: make provision

      - name: Lint
        run: make lint

      - name: Unit tests
        run: make test

      - name: Integration tests
        run: make test-integration

  build:
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials (OIDC)
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Build and push containers
        run: make containers
```

### 2. Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trigger | Push to `main` + PRs | CI on every change; build only on main |
| Test → Build split | Separate jobs | Build only runs if tests pass |
| Image tag | `git rev-parse --short HEAD` | Immutable, traceable to commit |
| ECR auth | OIDC federation | No stored credentials |
| `make` targets | Same as local | Identical behavior in CI and locally |

### 3. Configure GitHub Secrets/Variables

Same OIDC setup as DCI-06:

| Secret/Variable | Value |
|-----------------|-------|
| `AWS_ROLE_ARN` | IAM role for CI (same or scoped-down from infra) |
| `AWS_REGION` | AWS region |

### 4. Test the Pipeline

```bash
# Make a small change
echo "# CI test" >> README.md
git add . && git commit -m "ci: test CI pipeline"
git push origin main

# Watch in GitHub Actions → CI workflow should:
# 1. Run make provision
# 2. Run make lint
# 3. Run make test
# 4. Run make test-integration
# 5. Run make containers (push to ECR)
```

### 5. Verify ECR Image

```bash
# List images in ECR
aws ecr describe-images --repository-name {project} \
  --query 'imageDetails[*].{Tag:imageTags[0],Pushed:imagePushedAt}' \
  --output table

# Should show image tagged with the commit SHA
```

### 6. Commit

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI pipeline (test → lint → build → push)"
```

---

## Deliverables

- ✅ **`.github/workflows/ci.yml`** created
- ✅ **Test job**: `make provision` → `make lint` → `make test` → `make test-integration`
- ✅ **Build job**: `make containers` (only on main, after tests pass)
- ✅ **OIDC auth** configured (no stored AWS keys)
- ✅ **Pipeline tested** — commit triggers CI, image appears in ECR

## Agent

None

## Skill

**Title**: GitHub Actions Patterns
**Capability Domain**: CI_CD
**Technology Stack**: GitHub Actions

## Rules

None

## Artifacts Produced

- **CI Pipeline (GitHub Actions)** (Code) - Required

## Artifacts Consumed

None

## Notes

No additional notes.
