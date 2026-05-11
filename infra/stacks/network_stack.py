from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class MimirNetwork(Stack):
    """Networking layer for Mimir on AWS.

    Reuses the existing default VPC (vpc-a2af05df) instead of creating a new
    one.  Creates a security group for the Elastic Beanstalk EC2 instances and
    punches a hole into the pre-existing ``huginn-rds`` security group so Mimir
    can reach the shared RDS instance.

    Exports:
        vpc    — default VPC (lookup only, no mutation)
        eb_sg  — security group for EB instances; passed to MimirApp
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc_id: str,
        huginn_rds_sg_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── Default VPC (lookup — not managed by CDK) ─────────────────────────
        self.vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", vpc_id=vpc_id)

        # ── Mimir EB security group ───────────────────────────────────────────
        self.eb_sg = ec2.SecurityGroup(
            self,
            "MimirEbSg",
            vpc=self.vpc,
            security_group_name="mimir-eb",
            description="Mimir EB EC2 - inbound HTTP/HTTPS from internet",
            allow_all_outbound=True,
        )
        self.eb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="HTTP from internet (CloudFront origin)",
        )
        self.eb_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="HTTPS from internet",
        )

        # ── Grant Mimir EB access to huginn-rds on port 5432 ─────────────────
        # We import the existing SG by ID and add a single ingress rule.
        # CDK will synthesise this as a standalone AWS::EC2::SecurityGroupIngress
        # resource — it does NOT touch any other rules on huginn-rds.
        huginn_rds_sg = ec2.SecurityGroup.from_security_group_id(
            self,
            "HuginnRdsSg",
            security_group_id=huginn_rds_sg_id,
            allow_all_outbound=False,
            mutable=True,
        )
        huginn_rds_sg.add_ingress_rule(
            peer=self.eb_sg,
            connection=ec2.Port.tcp(5432),
            description="PostgreSQL from mimir-eb security group",
        )
