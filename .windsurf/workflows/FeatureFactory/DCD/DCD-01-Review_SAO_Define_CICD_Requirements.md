# Activity: Review SAO & Define CICD Requirements

**Activity ID**: 81
**Order**: 1
**Phase**: Elaboration
**Dependencies**: None

## Description

Review SAO & Define CICD Requirements

## Guidance

# Review SAO & Define CICD Requirements

## Objective

Read `docs/architecture/SAO.md` and the DCI output, define pipeline stages, map each stage to a `make` target, and produce a CICD requirements document that drives all subsequent pipeline work.

---

## Process

### 1. Read SAO.md

Extract:
- **§ Deployment Strategy** (DTA-14) — blue/green, trunk-based
- **§ Test Strategy** (DTA-06) — test types and quality gates
- **§ CI/CD** (DTA-15 or similar) — pipeline requirements

### 2. Review DCI Output

From the completed DCI workflow, confirm:
- EKS cluster name and region
- ECR repository URI
- Route53 hosted zone and domain
- Infra Makefile targets available (`make traffic-switch`, etc.)

### 3. Map Pipeline Stages → Make Targets

| Pipeline Stage | Make Target | When It Runs | Quality Gate |
|---------------|-------------|-------------|-------------|
| Unit tests | `make test` | Every push | All pass |
| Integration tests | `make test-integration` | Every push | All pass |
| Lint + format | `make lint` | Every push | Zero warnings |
| Build containers | `make containers` | After tests pass | Image pushed to ECR |
| Deploy to idle | `make deploy ENV=idle` | After build | Pods healthy |
| Smoke tests | `make smoke-test ENV=idle` | After deploy | All pass |
| Approval gate | (manual in GH Actions) | After smoke | Human approves |
| Switch traffic | `make switch` | After approval | DNS switched |
| Verify prod | `make smoke-test ENV=prod` | After switch | All pass |

### 4. Document CICD Requirements

Create `docs/architecture/CICD_REQUIREMENTS.md`:

```markdown
# CI/CD Requirements

## Pipeline Architecture
- **CI**: Triggered on every push to `main`
- **CD**: Triggered after CI succeeds
- **Switch**: Manual approval gate

## Make Targets Required
| Target | Description | Added By |
|--------|-------------|----------|
| `make test` | All tests | BSP |
| `make lint` | Linting | BSP |
| `make containers` | Build + push Docker | DCD |
| `make deploy ENV=...` | Helm deploy | DCD |
| `make smoke-test ENV=...` | Smoke tests | DCD |
| `make switch` | DNS traffic switch | DCD (calls infra) |
| `make rollback` | Revert switch | DCD (calls infra) |

## Environments
| Name | Namespace | DNS | Purpose |
|------|-----------|-----|---------|
| local | local | localhost | Developer machine |
| blue | blue | blue.{domain} | Blue deployment |
| green | green | green.{domain} | Green deployment |
| prod | (alias) | prod.{domain} | Currently active |
| idle | (alias) | idle.{domain} | Currently standby |

## Image Tagging
- Tag: `{ecr-repo}:{git-short-sha}`
- Latest: `{ecr-repo}:latest` (always updated)
```

---

## Deliverables

- ✅ **SAO.md reviewed** — deployment and testing strategy extracted
- ✅ **DCI output confirmed** — infra targets available
- ✅ **Pipeline stages mapped** to `make` targets
- ✅ **`docs/architecture/CICD_REQUIREMENTS.md`** created

## Inputs

Read these before starting this activity. They are produced earlier in the playbook and are authoritative — raise a drift event instead of deviating.

- **System Architecture Overview Template** (Template, Required) — produced by Write SAO.md (#59).

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

- **System Architecture Overview Template** (Template) - Required

## Notes

No additional notes.
