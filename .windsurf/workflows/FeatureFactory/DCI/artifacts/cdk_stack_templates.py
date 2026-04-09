#!/usr/bin/env python3
"""
CDK Stack Templates — FeatureFactory DCI Workflow

Skeleton implementations for VPC, EKS+ECR, and Route53 CDK stacks.
Copy these into your infra repo's stacks/ directory and adapt to your
project's INFRA_REQUIREMENTS.md.

Usage:
    1. Copy each class to its own file in stacks/
    2. Replace {project} placeholders with your project name
    3. Update context values in cdk.json
    4. Run `make synth` to verify
"""

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_eks as eks,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_route53 as route53,
)
from constructs import Construct


# ==============================================================================
# VPC Stack — stacks/vpc_stack.py
# ==============================================================================

class VpcStack(Stack):
    """
    Network foundation: VPC with public/private subnets and NAT Gateway.

    Outputs:
        self.vpc — ec2.Vpc instance (consumed by EksStack)
        self.eks_sg — Security group for EKS worker nodes
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC with 2 AZs
        self.vpc = ec2.Vpc(
            self, "Vpc",
            max_azs=2,
            nat_gateways=1,  # 1 shared for cost; set to 2 for HA in production
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

        # Security group for EKS worker nodes
        self.eks_sg = ec2.SecurityGroup(
            self, "EksNodeSg",
            vpc=self.vpc,
            description="Security group for EKS worker nodes",
            allow_all_outbound=True,
        )

        # Tag all resources
        cdk.Tags.of(self).add("managed-by", "cdk")
        cdk.Tags.of(self).add("stack", "vpc")


# ==============================================================================
# EKS + ECR Stack — stacks/eks_stack.py
# ==============================================================================

class EksStack(Stack):
    """
    Compute layer: EKS cluster with managed node group and ECR repository.

    Requires:
        vpc — ec2.Vpc from VpcStack

    Outputs:
        self.cluster — eks.Cluster instance
        self.ecr_repo — ecr.Repository instance
    """

    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # EKS Cluster
        self.cluster = eks.Cluster(
            self, "Cluster",
            vpc=vpc,
            version=eks.KubernetesVersion.V1_29,
            default_capacity=0,
            endpoint_access=eks.EndpointAccess.PUBLIC_AND_PRIVATE,
        )

        # Managed Node Group
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

        # ECR Repository
        self.ecr_repo = ecr.Repository(
            self, "AppRepo",
            repository_name="{project}",  # TODO: replace with actual project name
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    max_image_count=20,
                    description="Keep last 20 images",
                )
            ],
        )

        # Create blue/green namespaces
        for ns in ["blue", "green"]:
            self.cluster.add_manifest(
                f"{ns}-namespace",
                {
                    "apiVersion": "v1",
                    "kind": "Namespace",
                    "metadata": {"name": ns},
                },
            )

        cdk.Tags.of(self).add("managed-by", "cdk")
        cdk.Tags.of(self).add("stack", "eks")


# ==============================================================================
# DNS Stack — stacks/dns_stack.py
# ==============================================================================

class DnsStack(Stack):
    """
    DNS layer: Route53 hosted zone for blue/green traffic switching.

    Context:
        domain — Base domain (e.g., "app.example.com")

    Outputs:
        self.zone — route53.HostedZone instance
    """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        domain = self.node.try_get_context("domain")

        # Hosted zone
        self.zone = route53.HostedZone(
            self, "Zone",
            zone_name=domain,
        )

        # Note: Weighted records for prod/idle are managed by
        # scripts/traffic_switch.py, not by CDK. CDK only creates the zone.
        # This avoids CDK drift when the switch script modifies records.

        cdk.Tags.of(self).add("managed-by", "cdk")
        cdk.Tags.of(self).add("stack", "dns")


# ==============================================================================
# App Entry Point — app.py
# ==============================================================================

def create_app():
    """
    CDK app entry point. Wire stacks with dependencies.

    Usage in app.py:
        from cdk_stack_templates import create_app
        create_app()
    """
    app = cdk.App()

    env = cdk.Environment(
        account=app.node.try_get_context("account"),
        region=app.node.try_get_context("region"),
    )

    vpc = VpcStack(app, "VpcStack", env=env)
    eks = EksStack(app, "EksStack", vpc=vpc.vpc, env=env)
    dns = DnsStack(app, "DnsStack", env=env)

    # Explicit dependencies
    eks.add_dependency(vpc)

    app.synth()


if __name__ == "__main__":
    create_app()
