# Activity: Define Release & Rollback

**Activity ID**: TBD
**Order**: 11
**Phase**: Operations
**Dependencies**: Predecessor: DTA-10 (Define CI/CD Pipeline)

## Description

Define Release & Rollback

## Guidance

# Define Release & Rollback

## Objective

Choose deployment strategy, define version tagging, establish rollback triggers and procedures, and set release cadence.

---

## Decisions to Make

### 1. Deployment Strategy

Choose one:
- **Blue-Green** — Two identical environments, switch traffic. Best for: zero-downtime, instant rollback.
- **Canary** — Gradual traffic shift to new version. Best for: risk mitigation, large user base.
- **Rolling Update** — Replace instances one by one. Best for: K8s default, resource-efficient.
- **Recreate** — Stop old, start new. Best for: stateful apps, dev environments.
- **Feature Flags** — Deploy code dark, enable via flags. Best for: decoupling deploy from release.

### 2. Version Tagging & Changelog

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Tagging**: Git tags on release commits
- **Changelog generation**: Automated from commit messages (conventional commits)
- **Release notes**: Automated or manual? Where published?

### 3. Rollback Triggers

- **Automated**: Health check failures, error rate spike, latency threshold
- **Manual**: Operator decision, customer report
- **Rollback procedure**: Revert traffic? Redeploy previous version? DB rollback?
- **Rollback time target**: How fast must rollback complete?

### 4. Release Cadence & Policies

- **Cadence**: Continuous delivery (every merge)? Weekly? Sprint-aligned?
- **Freeze policies**: Code freeze before major releases?
- **Hotfix process**: How are urgent fixes deployed outside normal cadence?
- **Communication**: Who is notified of releases? How?

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `RELEASE_DEPLOY`
- `RELEASE_ROLLBACK`

Report coverage and gaps.

---

## Deliverables

- ✅ **Deployment strategy** chosen with rationale
- ✅ **Version tagging** and changelog approach defined
- ✅ **Rollback triggers** and procedures established
- ✅ **Release cadence** and policies documented
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Artifacts Produced

- Release & rollback decision (section for SAO.md)

## Artifacts Consumed

- CI/CD pipeline decision from DTA-10

## Notes

No additional notes.
