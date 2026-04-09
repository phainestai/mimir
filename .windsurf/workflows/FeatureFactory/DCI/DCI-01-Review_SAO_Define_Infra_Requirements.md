# Activity: Review SAO & Define Infra Requirements

**Activity ID**: TBD
**Order**: 1
**Phase**: Design
**Dependencies**: None (first activity — requires SAO.md from DTA workflow)

## Description

Review SAO & Define Infra Requirements

## Guidance

# Review SAO & Define Infra Requirements

## Objective

Read `docs/architecture/SAO.md`, identify the AWS services needed for the application, and produce a concise infrastructure requirements document that drives all subsequent CDK stack decisions.

---

## Process

### 1. Read SAO.md

Extract from SAO.md:

- **Technology Stack Table** — runtime versions, databases, caches, queues
- **§ Deployment Strategy** (DTA-14) — blue/green, canary, rolling
- **§ Infrastructure** (DTA-15) — cloud provider, region, K8s flavor
- **§ Observability** (DTA-13) — logging, metrics, tracing services

### 2. Map Application Needs → AWS Services

| Application Need | AWS Service | CDK Stack |
|-----------------|-------------|-----------|
| Container orchestration | EKS | EKS Stack |
| Container registry | ECR | EKS Stack |
| Networking (VPC, subnets) | VPC | VPC Stack |
| DNS for blue/green | Route53 | DNS Stack |
| NAT for private subnets | NAT Gateway | VPC Stack |
| TLS termination | ALB + ACM | EKS Stack (ingress) |
| Secrets | AWS Secrets Manager or K8s Secrets | EKS Stack |
| Logging | CloudWatch Logs | EKS Stack (add-ons) |

### 3. Document Infra Requirements

Create `docs/architecture/INFRA_REQUIREMENTS.md`:

```markdown
# Infrastructure Requirements

## AWS Region
{region from SAO.md, e.g., us-east-1}

## Services Required
| Service | Purpose | Configuration |
|---------|---------|---------------|
| VPC | Network isolation | 2 public + 2 private subnets, NAT GW |
| EKS | Container orchestration | Managed node group, 2-3 nodes |
| ECR | Container registry | 1 repo per service |
| Route53 | DNS + blue/green switching | Hosted zone, prod/idle weighted records |

## Blue/Green Strategy
- Two namespaces: `blue`, `green`
- Route53 weighted records: `prod.{domain}` → active, `idle.{domain}` → standby
- Switch = swap DNS weights (0/100 ↔ 100/0)

## Cost Estimate
{Rough monthly cost for EKS + NAT + Route53}

## Security Requirements
- Private subnets for EKS nodes
- Security groups: EKS ↔ database, ALB ↔ EKS
- IAM roles: EKS node role, CDK deploy role
```

### 4. Validate with SAO.md

Cross-check: every service in INFRA_REQUIREMENTS.md must trace back to a decision in SAO.md. If SAO.md doesn't cover infra decisions, flag it and update DTA first.

---

## Deliverables

- ✅ **SAO.md reviewed** — infra-relevant sections extracted
- ✅ **AWS service mapping** — application needs → AWS services
- ✅ **`docs/architecture/INFRA_REQUIREMENTS.md`** created
- ✅ **Blue/green strategy** documented
- ✅ **Cost estimate** included

## Artifacts Produced

- `docs/architecture/INFRA_REQUIREMENTS.md`

## Artifacts Consumed

- `docs/architecture/SAO.md` — Technology Stack Table, Deployment Strategy, Infrastructure sections

## Notes

This activity is design-only — no AWS resources are created yet. The output drives DCI-02 through DCI-05.
