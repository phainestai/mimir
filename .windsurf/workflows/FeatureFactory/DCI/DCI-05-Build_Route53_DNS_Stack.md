# Activity: Build Route53 & DNS Stack

**Activity ID**: TBD
**Order**: 5
**Phase**: Provision
**Dependencies**: Predecessor: DCI-04 (Build EKS Cluster & ECR Stack)

## Description

Build Route53 & DNS Stack

## Guidance

# Build Route53 & DNS Stack

## Objective

Implement the Route53 CDK stack with hosted zone and weighted DNS records for blue/green traffic switching. Create the `traffic_switch.py` script that swaps DNS weights between prod and idle environments.

---

## Process

### 1. Implement `stacks/dns_stack.py`

```python
from aws_cdk import Stack, aws_route53 as route53
from constructs import Construct

class DnsStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        domain = self.node.try_get_context("domain")  # e.g., "app.example.com"

        # Hosted zone (or import existing)
        self.zone = route53.HostedZone(
            self, "Zone",
            zone_name=domain,
        )

        # Blue/green weighted records are managed by traffic_switch.py
        # CDK creates the hosted zone; the script manages record weights
        # Initial state: prod → blue (weight 100), idle → green (weight 100)
```

### 2. Create `scripts/traffic_switch.py`

The traffic switch script manages Route53 weighted records:

```python
#!/usr/bin/env python3
"""
Traffic switch script for blue/green DNS-based deployment.

Manages Route53 weighted records to swap prod ↔ idle traffic.
- prod.{domain} points to the active environment (weight=100)
- idle.{domain} points to the standby environment (weight=100)
- switch action: swap which environment prod/idle point to
- rollback action: reverse the last switch

Usage:
    python scripts/traffic_switch.py --action switch
    python scripts/traffic_switch.py --action rollback
    python scripts/traffic_switch.py --action status
"""

import argparse
import json
import logging
import boto3

logger = logging.getLogger(__name__)

def get_current_state(client, hosted_zone_id, domain):
    """Read current DNS weights and return which color is prod."""
    # Implementation: query Route53 for weighted records
    pass

def switch_traffic(client, hosted_zone_id, domain):
    """Swap prod ↔ idle by updating Route53 weighted record sets."""
    # 1. Get current state (which color is prod?)
    # 2. Swap CNAME/A record targets for prod.{domain} and idle.{domain}
    # 3. Save previous state to .traffic_state.json for rollback
    pass

def rollback_traffic(client, hosted_zone_id, domain):
    """Restore previous state from .traffic_state.json."""
    pass

def show_status(client, hosted_zone_id, domain):
    """Print current traffic routing state."""
    pass

def main():
    parser = argparse.ArgumentParser(description="Blue/green traffic switch")
    parser.add_argument("--action", choices=["switch", "rollback", "status"], required=True)
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument("--hosted-zone-id", required=False, help="Route53 hosted zone ID")
    parser.add_argument("--domain", required=False, help="Base domain")
    args = parser.parse_args()

    client = boto3.client("route53", region_name=args.region)

    if args.action == "switch":
        switch_traffic(client, args.hosted_zone_id, args.domain)
    elif args.action == "rollback":
        rollback_traffic(client, args.hosted_zone_id, args.domain)
    elif args.action == "status":
        show_status(client, args.hosted_zone_id, args.domain)

if __name__ == "__main__":
    main()
```

### 3. Add Make Targets to Infra Makefile

Ensure the infra Makefile has:
```makefile
traffic-switch: ## Switch prod/idle DNS weights
	$(PYTHON) scripts/traffic_switch.py --action switch

traffic-rollback: ## Rollback DNS to previous state
	$(PYTHON) scripts/traffic_switch.py --action rollback

traffic-status: ## Show current traffic routing
	$(PYTHON) scripts/traffic_switch.py --action status
```

### 4. Write CDK Tests

```python
# tests/test_dns_stack.py
import aws_cdk as cdk
from aws_cdk.assertions import Template
from stacks.dns_stack import DnsStack

def test_hosted_zone_created():
    app = cdk.App(context={"domain": "app.example.com"})
    stack = DnsStack(app, "TestDns")
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Route53::HostedZone", 1)
```

### 5. Deploy & Verify

```bash
make deploy   # Deploys all stacks including DNS
make traffic-status  # Shows initial routing state
```

Verify:
- Route53 hosted zone exists
- `dig prod.{domain}` resolves
- `dig idle.{domain}` resolves
- Both point to different targets (blue/green)

### 6. Commit

```bash
git add stacks/dns_stack.py scripts/traffic_switch.py tests/test_dns_stack.py
git commit -m "infra: implement Route53 DNS stack with blue/green traffic switching"
```

---

## Deliverables

- ✅ **`stacks/dns_stack.py`** implemented with hosted zone
- ✅ **`scripts/traffic_switch.py`** with switch/rollback/status actions
- ✅ **Infra Makefile** has `traffic-switch`, `traffic-rollback`, `traffic-status` targets
- ✅ **CDK tests** passing
- ✅ **DNS resolving** for prod and idle subdomains

## Artifacts Produced

- `stacks/dns_stack.py` — Route53 CDK stack
- `scripts/traffic_switch.py` — DNS weight management script

## Artifacts Consumed

- `docs/architecture/INFRA_REQUIREMENTS.md` — domain, blue/green strategy
- `DCI/skills/aws_cdk_python.md` — CDK Route53 patterns

## Notes

DNS propagation can take up to 60 seconds. The traffic_switch.py script should wait and verify after switching. Consider setting TTL to 60s for faster switches.
