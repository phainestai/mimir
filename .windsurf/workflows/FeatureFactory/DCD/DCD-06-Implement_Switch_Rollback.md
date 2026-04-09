# Activity: Implement Switch & Rollback

**Activity ID**: TBD
**Order**: 6
**Phase**: Deploy
**Dependencies**: Predecessor: DCD-05 (Build CD Pipeline)

## Description

Implement Switch & Rollback

## Guidance

# Implement Switch & Rollback

## Objective

Ensure the traffic switch and rollback mechanisms work reliably end-to-end. Add a dedicated rollback workflow in GitHub Actions. Verify that rollback restores the previous production state within 60 seconds.

---

## Process

### 1. Verify `make switch` Works

The `switch` target in the app Makefile delegates to the infra repo:

```makefile
switch: ## Switch prod ↔ idle DNS traffic
	cd ../$(PROJECT)-infra && $(MAKE) traffic-switch
```

Test manually:
```bash
# Show current state
make pipeline-status

# Switch
make switch

# Verify DNS changed
dig +short prod.{domain}
dig +short idle.{domain}

# Verify app responds on new prod
curl -f https://prod.{domain}/health
```

### 2. Verify `make rollback` Works

```bash
# Rollback
make rollback

# Verify DNS reverted
dig +short prod.{domain}
# Should match pre-switch state
```

### 3. Create Rollback GH Actions Workflow

Create `.github/workflows/rollback.yml` — a dedicated emergency rollback trigger:

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
    environment: production  # Requires approval
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

      - name: Show current state
        run: make pipeline-status

      - name: Rollback traffic
        run: make rollback

      - name: Verify rollback
        run: |
          make pipeline-status
          make smoke-test ENV=prod
```

### 4. Document Rollback Procedure

Add to `README.md` or `docs/runbook/`:

```markdown
## Emergency Rollback

### Option 1: GitHub Actions (recommended)
1. Go to Actions → Rollback → Run workflow
2. Type "rollback" to confirm
3. Approve in production environment
4. Wait for completion (~60 seconds)

### Option 2: Command line
1. `make rollback`
2. Verify: `make pipeline-status`
3. Verify: `curl https://prod.{domain}/health`

### What rollback does:
- Swaps DNS weights: prod ↔ idle
- Previous deployment is still running in the other namespace
- DNS propagation: ~60 seconds
- No pods are restarted or redeployed

### When to rollback:
- Smoke tests fail after switch
- Users report errors on production
- Monitoring alerts trigger
```

### 5. Measure Rollback Time

```bash
# Time the full rollback
time make rollback
# Target: < 60 seconds (DNS propagation)
```

### 6. Commit

```bash
git add .github/workflows/rollback.yml
git commit -m "ci: add emergency rollback workflow with confirmation gate"
```

---

## Deliverables

- ✅ **`make switch`** verified end-to-end
- ✅ **`make rollback`** verified end-to-end
- ✅ **`.github/workflows/rollback.yml`** created with confirmation gate
- ✅ **Rollback time** < 60 seconds
- ✅ **Runbook** documented

## Artifacts Produced

- `.github/workflows/rollback.yml` — Emergency rollback workflow
- Rollback documentation in README or runbook

## Artifacts Consumed

- Infra repo Makefile targets: `traffic-switch`, `traffic-rollback`
- App Makefile targets: `switch`, `rollback`, `pipeline-status`, `smoke-test`

## Notes

Rollback is DNS-based, not deployment-based. The previous version's pods are still running in the other namespace. This makes rollback instant (just DNS weight swap) instead of requiring a new deployment.
