# Activity: Define Infrastructure

**Activity ID**: 50
**Order**: 9
**Phase**: Inception
**Dependencies**: None

## Description

Define Infrastructure

## Guidance

# Define Infrastructure

## Objective

Define the local development environment, cloud provider and compute model, networking setup, and Infrastructure as Code tooling.

---

## Decisions to Make

### 1. Local Development Environment

- **Containerization**: Docker, Podman, or native?
- **Dev/prod parity**: How close is local to production?
- **Makefile targets**: `make provision` (install all deps), `make run` (start everything)
- **Required tools**: Which CLI tools, SDKs, runtimes must be installed?
- **Environment variables**: How are they managed locally? (.env file, direnv)

### 2. Cloud Provider & Compute Model

Choose compute model:
- **Kubernetes (EKS/GKE/AKS)** — Container orchestration. Best for: complex deployments, auto-scaling.
- **Container service (ECS/Cloud Run)** — Managed containers. Best for: simpler container deployments.
- **Serverless (Lambda/Cloud Functions)** — Event-driven functions. Best for: sporadic workloads.
- **VMs (EC2/Compute Engine)** — Traditional. Best for: legacy apps, specific OS needs.
- **PaaS (Heroku/Railway/Render)** — Managed platform. Best for: fast start, less ops overhead.
- **Desktop only** — No cloud. Best for: single-user desktop applications.

### 3. Networking

- **VPC**: Network isolation, subnets (public/private)
- **DNS**: Domain management, Route53/Cloudflare
- **Load balancing**: ALB/NLB, health checks, SSL termination
- **CDN**: Static asset distribution, edge caching

### 4. Infrastructure as Code

Choose one:
- **AWS CDK** — TypeScript/Python, AWS-native. Best for: AWS-only, programmatic infra.
- **Terraform** — HCL, multi-cloud. Best for: cloud-agnostic, declarative.
- **Pulumi** — General-purpose languages. Best for: developers who prefer Python/TS.
- **CloudFormation** — YAML/JSON, AWS-native. Best for: simple AWS setups.
- **None** — Manual/console setup. Best for: prototypes, desktop apps.

### 5. Scan Skills

Query Playbook Skills where `capability_domain` in:
- `INFRA_LOCAL`
- `INFRA_CLOUD`
- `INFRA_K8S`

Report coverage and gaps.

---

## Deliverables

- ✅ **Local dev environment** defined with provisioning instructions
- ✅ **Cloud provider & compute model** chosen with rationale
- ✅ **Networking** architecture defined
- ✅ **IaC tool** selected
- ✅ **Skill coverage** assessed for this domain
- ✅ **Decision recorded** for inclusion in SAO.md (DTA-18)

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
