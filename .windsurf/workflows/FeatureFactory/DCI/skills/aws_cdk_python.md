# Skill: AWS CDK with Python

**Capability Domain**: INFRASTRUCTURE_AS_CODE
**Technology Stack**: AWS CDK + Python

## Overview

Reference patterns for building AWS infrastructure using CDK with Python. Covers VPC, EKS, ECR, Route53, IAM, and security groups. All patterns follow CDK best practices: typed constructs, explicit dependencies, proper tagging.

## Reference Implementation

### Pattern 1: VPC with Public/Private Subnets

```python
from aws_cdk import Stack, aws_ec2 as ec2
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
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
```

**Key decisions:**
- `max_azs=2` — minimum for HA; 3 for production
- `nat_gateways=1` — cost saving; set to `max_azs` for HA
- CIDR mask 24 = 254 addresses per subnet

### Pattern 2: EKS Cluster with Managed Node Group

```python
from aws_cdk import Stack, aws_eks as eks, aws_ec2 as ec2
from constructs import Construct

class EksStack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.cluster = eks.Cluster(
            self, "Cluster",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_29,
            default_capacity=0,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
        )

        self.cluster.add_nodegroup_capacity(
            "WorkerNodes",
            instance_types=[ec2.InstanceType("t3.medium")],
            min_size=2,
            max_size=4,
            desired_size=2,
            disk_size=50,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
        )
```

**Key decisions:**
- `default_capacity=0` + explicit nodegroup — more control over node config
- `PUBLIC_AND_PRIVATE` endpoint — accessible from CI/CD and within VPC
- Private subnets for nodes — best practice for security
- t3.medium — good starting point; adjust based on workload

### Pattern 3: ECR Repository with Lifecycle

```python
from aws_cdk import Stack, RemovalPolicy, aws_ecr as ecr
from constructs import Construct

class EcrStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.repo = ecr.Repository(
            self, "AppRepo",
            repository_name="my-app",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=20,
                    description="Keep last 20 images",
                ),
            ],
        )
```

**Key decisions:**
- `RETAIN` removal policy — don't delete images when stack is destroyed
- Lifecycle rule — prevent unbounded image storage costs

### Pattern 4: Route53 Hosted Zone

```python
from aws_cdk import Stack, aws_route53 as route53
from constructs import Construct

class DnsStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        domain = self.node.try_get_context("domain")

        self.zone = route53.HostedZone(
            self, "Zone",
            zone_name=domain,
        )
```

**Key decisions:**
- Weighted records managed by script (not CDK) to avoid drift
- CDK creates zone; `traffic_switch.py` manages record weights

### Pattern 5: Security Groups

```python
# EKS node security group
eks_sg = ec2.SecurityGroup(
    self, "EksNodeSg",
    vpc=vpc,
    description="EKS worker nodes",
    allow_all_outbound=True,
)

# Allow inbound from ALB
eks_sg.add_ingress_rule(
    peer=alb_sg,
    connection=ec2.Port.tcp_range(30000, 32767),
    description="ALB to NodePort range",
)

# Allow inbound from other nodes (pod-to-pod)
eks_sg.add_ingress_rule(
    peer=eks_sg,
    connection=ec2.Port.all_traffic(),
    description="Node-to-node communication",
)
```

### Pattern 6: OIDC Provider for GitHub Actions

```python
from aws_cdk import Stack, aws_iam as iam
from constructs import Construct

class OidcStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        github_org = self.node.try_get_context("github_org")
        github_repo = self.node.try_get_context("github_repo")

        # GitHub OIDC provider
        provider = iam.OpenIdConnectProvider(
            self, "GithubOidc",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
        )

        # Role for GitHub Actions
        self.deploy_role = iam.Role(
            self, "GithubActionsRole",
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": f"repo:{github_org}/{github_repo}:*",
                    },
                },
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AdministratorAccess"),
                # TODO: scope down to minimum required permissions
            ],
        )
```

### Pattern 7: CDK Context and Environment

```python
# app.py
import aws_cdk as cdk

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region"),
)

# cdk.json
# {
#   "app": "python3 app.py",
#   "context": {
#     "account": "123456789012",
#     "region": "us-east-1",
#     "domain": "app.example.com",
#     "github_org": "myorg",
#     "github_repo": "myrepo-infra"
#   }
# }
```

### Pattern 8: CDK Testing with Assertions

```python
import aws_cdk as cdk
from aws_cdk.assertions import Template, Match

def test_vpc_has_correct_subnets():
    app = cdk.App()
    stack = VpcStack(app, "TestVpc")
    template = Template.from_stack(stack)

    # Count resources
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::EC2::Subnet", 4)

    # Check properties
    template.has_resource_properties("AWS::EC2::VPC", {
        "EnableDnsHostnames": True,
        "EnableDnsSupport": True,
    })
```

## Cost Reference

| Resource | Approximate Monthly Cost |
|----------|-------------------------|
| NAT Gateway (1) | $30 + data transfer |
| EKS control plane | $70 |
| t3.medium × 2 nodes | $60 |
| Route53 hosted zone | $0.50 |
| ECR storage | $0.10/GB |
| **Total (baseline)** | **~$160/month** |

## Common Pitfalls

1. **EKS creation time** — ~15 min. Don't abort `cdk deploy` early.
2. **NAT Gateway costs** — Can surprise. Use 1 for dev, N for prod.
3. **CDK drift** — Don't modify CDK-managed resources manually in console.
4. **OIDC federation** — Use instead of storing AWS keys in GitHub secrets.
5. **Removal policies** — Set `RETAIN` for ECR and databases to prevent data loss.
