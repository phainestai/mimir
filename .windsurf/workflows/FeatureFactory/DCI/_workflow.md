# Design & Deploy Cloud Infra

**Playbook**: FeatureFactory v3.9 (Draft)
**Workflow ID**: TBD
**Description**: Design and deploy cloud infrastructure using AWS CDK with Python. Create a separate infra repo with VPC, EKS, ECR, and Route53 stacks. Establish Makefile targets for infra operations and GitHub Actions workflow for automated deployment and blue/green traffic switching.
**Phase Organization**: Uses phases (Design → Provision → Deploy → Verify)
**Total Activities**: 7
**Export Date**: 2026-04-09

## Prerequisites

- Completed DTA workflow → `docs/architecture/SAO.md` (with Technology Stack Table)
- Completed EST workflow → estimation complete (infra scope sized)
- AWS account with programmatic access (IAM user with admin or scoped permissions)
- AWS CLI configured (`~/.aws/credentials`)

## Output

- Separate infra repo with AWS CDK Python project
- CDK stacks: VPC, EKS cluster + node group, ECR repository, Route53 DNS (prod/idle)
- Infra Makefile with `infra-deploy`, `infra-destroy`, `infra-status`, `traffic-switch`, `traffic-rollback` targets
- GitHub Actions workflow for automated infra deployment and traffic switching
- Verified cloud environment (EKS healthy, ECR accessible, DNS resolving)

## Key Principle

> **Makefile is the single orchestration layer.** Every infra operation is a `make` target. GitHub Actions workflows are thin wrappers that call `make` in sequence. Local and CI/CD use identical commands.

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern DCI-XX-Name.md
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use import_workflow_from_local MCP tool to import changes.
