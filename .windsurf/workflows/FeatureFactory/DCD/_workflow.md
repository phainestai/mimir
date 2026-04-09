# Design & Deploy CICD

**Playbook**: FeatureFactory v3.9 (Draft)
**Workflow ID**: TBD
**Description**: Design and deploy CI/CD pipeline using GitHub Actions in the application monorepo. Create Helm chart with per-environment values, add container and deployment `make` targets, then wire them into GitHub Actions workflows for CI (test → build → push) and CD (deploy → smoke → approve → switch).
**Phase Organization**: Uses phases (Design → Build → Deploy → Verify)
**Total Activities**: 7
**Export Date**: 2026-04-09

## Prerequisites

- Completed DCI workflow → Cloud infrastructure operational (EKS, ECR, Route53)
- Completed BSP workflow → Makefile with base targets (provision, test, lint, etc.)
- Docker installed locally
- `kubectl` configured for EKS cluster

## Output

- Helm chart with values.yaml for local/blue/green environments
- App Makefile extended with: `containers`, `deploy`, `smoke-test`, `switch`, `rollback`, `verify`, `pipeline-status`
- GitHub Actions CI workflow: test → verify → containers (on every push)
- GitHub Actions CD workflow: deploy to idle → smoke test → approval → switch
- End-to-end pipeline verified (commit → idle → approve → prod)

## Key Principle

> **CICD = wiring `make` commands together.** First define all `make` targets for every operation on every environment. Then GitHub Actions simply calls them in sequence with approval gates. This means:
> - You can reproduce any pipeline step locally with `make`
> - GH Actions YAML contains zero business logic
> - Adding a new pipeline step = adding a `make` target + one line in YAML

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern DCD-XX-Name.md
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use import_workflow_from_local MCP tool to import changes.
