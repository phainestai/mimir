# Activity: End-to-End Pipeline Verification

**Activity ID**: 87
**Order**: 7
**Phase**: Elaboration
**Dependencies**: None

## Description

End-to-End Pipeline Verification

## Guidance

# End-to-End Pipeline Verification

## Objective

Ship a test feature through the entire pipeline: code change → CI (test, build) → CD (deploy idle, smoke, approve, switch) → verify production. This is the acceptance gate for the DCD workflow.

---

## Process

### 1. Prepare a Test Feature

Make a visible change to verify the full pipeline:

```bash
# Add a version endpoint
# e.g., GET /version returns {"version": "0.1.0", "commit": "{sha}"}
```

Write tests for it:
```bash
# Add test
git add .
git commit -m "feat: add /version endpoint for pipeline verification"
```

### 2. Push and Watch CI

```bash
git push origin main
```

Monitor GitHub Actions → CI workflow:
- ✅ `make provision` — dependencies installed
- ✅ `make lint` — no warnings
- ✅ `make test` — all tests pass
- ✅ `make test-integration` — all pass
- ✅ `make containers` — image pushed to ECR

Verify image in ECR:
```bash
aws ecr describe-images --repository-name {project} \
  --query 'imageDetails | sort_by(@, &imagePushedAt) | [-1].imageTags' --output text
```

### 3. Watch CD Pipeline

CD triggers automatically after CI succeeds:

- ✅ **deploy-idle** — `make deploy ENV=idle` → pods running in idle namespace
- ✅ **smoke-test** — `make smoke-test ENV=idle` → smoke tests pass

Verify idle deployment:
```bash
kubectl get pods -n {idle-namespace}
curl https://idle.{domain}/version
# Should show new version
```

### 4. Approve Switch

In GitHub Actions → CD workflow:
- The `switch` job is waiting for approval
- Review the smoke test results
- **Approve** in the production environment

### 5. Verify Production

After approval:
- ✅ `make switch` — DNS weights swapped
- ✅ `make smoke-test ENV=prod` — production smoke tests pass

```bash
curl https://prod.{domain}/version
# Should show new version with current commit SHA
```

### 6. Test Rollback

```bash
# Trigger rollback via GH Actions or CLI
make rollback

# Verify prod reverted
curl https://prod.{domain}/version
# Should show previous version

# Switch back (re-apply the new version)
make switch
curl https://prod.{domain}/version
# Should show new version again
```

### 7. Create Verification Checklist

Document in `docs/architecture/CICD_VERIFICATION.md`:

```markdown
# CI/CD Verification

## Pipeline Summary
| Step | Status | Duration | Notes |
|------|--------|----------|-------|
| CI: provision | ✅ | ~2 min | Dependencies cached |
| CI: lint | ✅ | ~30 sec | Zero warnings |
| CI: test | ✅ | ~1 min | All pass |
| CI: test-integration | ✅ | ~2 min | All pass |
| CI: containers | ✅ | ~3 min | Image: {sha} |
| CD: deploy-idle | ✅ | ~2 min | Pods healthy |
| CD: smoke-test | ✅ | ~1 min | All pass |
| CD: approval | ✅ | Manual | Approved by {user} |
| CD: switch | ✅ | ~60 sec | DNS propagated |
| CD: verify-prod | ✅ | ~1 min | All pass |
| Rollback | ✅ | ~60 sec | DNS reverted |

## Total Pipeline Time
- CI: ~8 min
- CD (auto): ~5 min
- CD (manual): depends on reviewer
- Rollback: ~60 sec

## Make Targets Verified
| Target | Works Locally | Works in CI/CD |
|--------|--------------|----------------|
| make provision | ✅ | ✅ |
| make lint | ✅ | ✅ |
| make test | ✅ | ✅ |
| make containers | ✅ | ✅ |
| make deploy ENV=... | ✅ | ✅ |
| make smoke-test ENV=... | ✅ | ✅ |
| make switch | ✅ | ✅ |
| make rollback | ✅ | ✅ |
| make pipeline-status | ✅ | ✅ |
```

### 8. Commit

```bash
git add docs/architecture/CICD_VERIFICATION.md
git commit -m "docs: add CI/CD verification checklist — pipeline fully operational"
```

---

## Deliverables

- ✅ **Test feature** shipped through full pipeline
- ✅ **CI pipeline** — test → build → push verified
- ✅ **CD pipeline** — deploy idle → smoke → approve → switch verified
- ✅ **Rollback** tested and verified
- ✅ **`docs/architecture/CICD_VERIFICATION.md`** — checklist documented
- ✅ **Local and CI/CD parity** — all `make` targets work identically in both

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **Helm Chart Template** (Template, Optional) — produced by Create Helm Chart & Values (#82).
- **CI Pipeline (GitHub Actions)** (Code, Required) — produced by Build CI Pipeline (#84).
- **CD Pipeline (GitHub Actions)** (Code, Required) — produced by Build CD Pipeline (#85).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **Helm Chart Template** (Template) - Optional
- **CI Pipeline (GitHub Actions)** (Code) - Required
- **CD Pipeline (GitHub Actions)** (Code) - Required

## Notes

No additional notes.
