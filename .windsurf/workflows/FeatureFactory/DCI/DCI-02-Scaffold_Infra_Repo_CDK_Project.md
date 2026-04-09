# Activity: Scaffold Infra Repo & CDK Project

**Activity ID**: TBD
**Order**: 2
**Phase**: Design
**Dependencies**: Predecessor: DCI-01 (Review SAO & Define Infra Requirements)

## Description

Scaffold Infra Repo & CDK Project

## Guidance

# Scaffold Infra Repo & CDK Project

## Objective

Create a separate infrastructure repository with an AWS CDK Python project, Makefile for infra operations, and GitHub Actions workflow placeholder. The infra repo is independent from the application monorepo.

---

## Process

### 1. Create Infra Repository

```bash
# Create repo: {project}-infra (e.g., nexus-infra)
mkdir {project}-infra
cd {project}-infra
git init
```

### 2. Initialize CDK Project

```bash
# Create venv and install CDK
python3 -m venv .venv
source .venv/bin/activate
pip install aws-cdk-lib constructs

# Initialize CDK app structure
mkdir -p stacks tests
```

Create `app.py` (CDK entry point):

```python
#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.eks_stack import EksStack
from stacks.dns_stack import DnsStack

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region"),
)

vpc = VpcStack(app, "VpcStack", env=env)
eks = EksStack(app, "EksStack", vpc=vpc.vpc, env=env)
dns = DnsStack(app, "DnsStack", env=env)

app.synth()
```

### 3. Create Infra Repo Structure

```
{project}-infra/
├── app.py                    ← CDK entry point
├── cdk.json                  ← CDK configuration
├── requirements.txt          ← Python dependencies (aws-cdk-lib, constructs)
├── Makefile                  ← Infra operations
├── .github/
│   └── workflows/
│       └── infra.yml         ← GH Actions for infra deploy (DCI-06)
├── stacks/
│   ├── __init__.py
│   ├── vpc_stack.py          ← VPC + subnets + NAT (DCI-03)
│   ├── eks_stack.py          ← EKS + ECR (DCI-04)
│   └── dns_stack.py          ← Route53 (DCI-05)
├── scripts/
│   └── traffic_switch.py     ← DNS weight switcher (DCI-05)
├── tests/
│   ├── __init__.py
│   └── test_stacks.py        ← CDK snapshot tests
└── README.md
```

### 4. Create Infra Makefile

```makefile
.PHONY: help synth deploy destroy status traffic-switch traffic-rollback

.DEFAULT_GOAL := help

VENV := .venv
PYTHON := $(VENV)/bin/python
CDK := npx cdk

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Infrastructure

synth: ## Synthesize CDK stacks (dry run)
	$(CDK) synth

deploy: ## Deploy all CDK stacks
	$(CDK) deploy --all --require-approval never

destroy: ## Destroy all CDK stacks (DANGEROUS)
	$(CDK) destroy --all --force

status: ## Show stack status
	$(CDK) list
	aws cloudformation describe-stacks \
		--query 'Stacks[].{Name:StackName,Status:StackStatus}' \
		--output table

##@ Traffic

traffic-switch: ## Switch prod/idle DNS weights
	$(PYTHON) scripts/traffic_switch.py --action switch

traffic-rollback: ## Rollback DNS to previous state
	$(PYTHON) scripts/traffic_switch.py --action rollback

##@ Testing

test: ## Run CDK tests
	$(PYTHON) -m pytest tests/ -v

##@ Setup

provision: ## Install dependencies
	pip install -r requirements.txt
	npm install -g aws-cdk
```

### 5. Create cdk.json

```json
{
  "app": "python3 app.py",
  "context": {
    "account": "{AWS_ACCOUNT_ID}",
    "region": "{AWS_REGION}"
  }
}
```

### 6. Commit

```bash
git add .
git commit -m "infra: scaffold CDK project with VPC/EKS/DNS stack placeholders"
```

---

## Deliverables

- ✅ **Infra repo** created and initialized
- ✅ **CDK project** initialized with `app.py` and stack placeholders
- ✅ **Infra Makefile** with deploy/destroy/status/traffic targets
- ✅ **Directory structure** matching the scaffold template
- ✅ **Committed** to infra repo

## Artifacts Produced

- `{project}-infra/` repository with full scaffold

## Artifacts Consumed

- `docs/architecture/INFRA_REQUIREMENTS.md` (from DCI-01) — AWS region, services list
- `DCI/artifacts/infra_repo_scaffold.md` — reference scaffold template

## Notes

Stack files (`vpc_stack.py`, `eks_stack.py`, `dns_stack.py`) are created as empty placeholders here. They are implemented in DCI-03, DCI-04, and DCI-05 respectively.
