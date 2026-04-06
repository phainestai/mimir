# Activity: Define CI/CD Pipeline

**Activity ID**: TBD
**Order**: 10
**Phase**: Operations
**Dependencies**: Predecessor: DTA-09 (Define Infrastructure)

## Description

Define CI/CD Pipeline

## Guidance

# Define CI/CD Pipeline

## Objective

Choose CI platform, define pipeline stages, configure artifact registry, set promotion gates, and establish trunk-based development flow.

---

## Decisions to Make

### 1. CI Platform

Choose one:
- **GitHub Actions** — GitHub-native, YAML workflows. Best for: GitHub-hosted repos.
- **GitLab CI** — GitLab-native, `.gitlab-ci.yml`. Best for: GitLab-hosted repos.
- **Jenkins** — Self-hosted, Groovy pipelines. Best for: complex custom pipelines.
- **CircleCI** — Cloud-hosted, YAML config. Best for: fast builds, Docker-native.
- **None** — Local-only builds. Best for: desktop apps, early prototypes.

### 2. Pipeline Stages

Define the standard pipeline stages:
```
lint → test → build → publish → deploy
```

For each stage:
- What runs? (commands, scripts)
- What triggers it? (push, PR, tag, manual)
- What blocks the next stage? (failure criteria)
- Estimated duration target

### 3. Artifact Registry

- **Container images**: Docker Hub, ECR, GCR, GitHub Container Registry
- **Packages**: npm registry, PyPI, private registry
- **Build artifacts**: S3, GCS, artifact storage in CI platform
- **Retention policy**: How long are artifacts kept?

### 4. Promotion Gates

- **Automated gates**: All tests pass, linting clean, security scan clean
- **Manual gates**: Human approval for production deploy
- **Environment promotion**: dev → staging → production
- **Rollback trigger**: Automated on health check failure? Manual only?

### 5. Trunk-Based Development Flow

- **Branch strategy**: Trunk-based (short-lived feature branches, merge to main)
- **PR requirements**: Reviews, CI pass, no conflicts
- **Merge strategy**: Squash, rebase, merge commit
- **Release tagging**: Semantic versioning, automated changelog

### 6. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `CICD_BUILD`
- `CICD_DEPLOY`
- `CICD_PIPELINE`

Report coverage and gaps.

---

## Deliverables

- ✅ **CI platform** chosen
- ✅ **Pipeline stages** defined with triggers and gates
- ✅ **Artifact registry** configured
- ✅ **Promotion gates** established
- ✅ **Trunk-based flow** documented
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- CI/CD pipeline decision (section for SAO.md)

## Artifacts Consumed

- Infrastructure decision from DTA-09
- Test strategy decision from DTA-06

## Notes

No additional notes.
