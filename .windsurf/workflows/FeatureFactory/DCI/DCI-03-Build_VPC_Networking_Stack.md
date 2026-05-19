# Activity: Build VPC & Networking Stack

**Activity ID**: 76
**Order**: 3
**Phase**: Elaboration
**Dependencies**: None

## Description

Build VPC & Networking Stack

## Guidance

# Build VPC & Networking Stack

## Objective

Implement the VPC CDK stack with public/private subnets, NAT Gateway, and security groups. This is the foundational networking layer that EKS and all other services depend on.

---

## Process

### 1. Implement `stacks/vpc_stack.py`

Use the `aws_cdk_python` skill for reference patterns.

Key constructs:
- **VPC** with 2 AZs, 2 public + 2 private subnets
- **NAT Gateway** (1 per AZ for HA, or 1 shared for cost savings)
- **Security Groups**: EKS control plane, EKS nodes, database (if applicable)

```python
from aws_cdk import Stack, aws_ec2 as ec2
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Security group for EKS nodes
        self.eks_sg = ec2.SecurityGroup(
            self, "EksNodeSg",
            vpc=self.vpc,
            description="Security group for EKS worker nodes",
            allow_all_outbound=True,
        )
```

### 2. Write CDK Tests

```python
# tests/test_vpc_stack.py
import aws_cdk as cdk
from aws_cdk.assertions import Template
from stacks.vpc_stack import VpcStack

def test_vpc_created():
    app = cdk.App()
    stack = VpcStack(app, "TestVpc")
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::EC2::VPC", 1)

def test_subnets_created():
    app = cdk.App()
    stack = VpcStack(app, "TestVpc")
    template = Template.from_stack(stack)
    template.resource_count_is("AWS::EC2::Subnet", 4)  # 2 public + 2 private
```

### 3. Synthesize & Verify

```bash
make synth    # Should produce CloudFormation template without errors
make test     # CDK tests should pass
```

### 4. Deploy VPC Stack Only

```bash
npx cdk deploy VpcStack
```

Verify in AWS Console:
- VPC created with correct CIDR
- 4 subnets (2 public, 2 private)
- NAT Gateway running
- Route tables configured

### 5. Commit

```bash
git add stacks/vpc_stack.py tests/test_vpc_stack.py
git commit -m "infra: implement VPC stack with 2 AZ, NAT Gateway, security groups"
```

---

## Deliverables

- ✅ **`stacks/vpc_stack.py`** implemented with VPC, subnets, NAT, security groups
- ✅ **CDK tests** for VPC stack passing
- ✅ **`make synth`** succeeds
- ✅ **VPC deployed** and verified in AWS Console

## Agent

None

## Skill

None

## Rules

None

## Artifacts Produced

- **CDK Stack Templates** (Code) - Required

## Artifacts Consumed

- **Infra Repo Scaffold** (Template) - Required

## Notes

No additional notes.
