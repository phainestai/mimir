"""CDK assertion tests for Mimir infra stacks.

All tests use aws_cdk.assertions — no AWS API calls are made.
Fake VPC / hosted-zone objects are injected so lookups are bypassed.
"""
import aws_cdk as cdk
import pytest
from aws_cdk import assertions, aws_ec2 as ec2, aws_route53 as route53

from stacks.app_stack import MimirApp
from stacks.dns_stack import MimirDns
from stacks.network_stack import MimirNetwork

# ── Shared fixtures ───────────────────────────────────────────────────────────

ACCOUNT = "123456789012"
REGION = "us-east-1"
VPC_ID = "vpc-aaaabbbb"
RDS_SG_ID = "sg-rdsrdsrds"
ACM_CERT_ARN = (
    "arn:aws:acm:us-east-1:123456789012:certificate/test-cert-aaaa-bbbb"
)
DOMAIN = "example.com"

CDK_ENV = cdk.Environment(account=ACCOUNT, region=REGION)


def _fake_vpc(stack: cdk.Stack) -> ec2.IVpc:
    return ec2.Vpc.from_lookup(
        stack,
        "FakeVpc",
        vpc_id=VPC_ID,
    )


def _fake_zone(stack: cdk.Stack) -> route53.IHostedZone:
    return route53.HostedZone.from_hosted_zone_attributes(
        stack,
        "FakeZone",
        hosted_zone_id="Z1234567890",
        zone_name=DOMAIN,
    )


# ── MimirNetwork ──────────────────────────────────────────────────────────────


class TestMimirNetwork:
    @pytest.fixture
    def template(self) -> assertions.Template:
        app = cdk.App(context=VPC_CONTEXT)
        stack = MimirNetwork(
            app,
            "TestNetwork",
            vpc_id=VPC_ID,
            huginn_rds_sg_id=RDS_SG_ID,
            env=CDK_ENV,
        )
        return assertions.Template.from_stack(stack)

    def test_mimir_eb_security_group_created(self, template):
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {"GroupName": "mimir-eb"},
        )

    def test_eb_sg_allows_http_80(self, template):
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "IpProtocol": "tcp",
                        "FromPort": 80,
                        "ToPort": 80,
                        "CidrIp": "0.0.0.0/0",
                    })
                ])
            },
        )

    def test_eb_sg_allows_https_443(self, template):
        template.has_resource_properties(
            "AWS::EC2::SecurityGroup",
            {
                "SecurityGroupIngress": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "IpProtocol": "tcp",
                        "FromPort": 443,
                        "ToPort": 443,
                        "CidrIp": "0.0.0.0/0",
                    })
                ])
            },
        )

    def test_rds_ingress_rule_on_5432_created(self, template):
        template.has_resource_properties(
            "AWS::EC2::SecurityGroupIngress",
            {
                "GroupId": RDS_SG_ID,
                "IpProtocol": "tcp",
                "FromPort": 5432,
                "ToPort": 5432,
            },
        )


# ── MimirApp ──────────────────────────────────────────────────────────────────

VPC_CONTEXT = {
    "vpc-provider:account=123456789012:filter.vpc-id=vpc-aaaabbbb:region=us-east-1:returnAsymmetricSubnets=true": {
        "vpcId": VPC_ID,
        "vpcCidrBlock": "172.31.0.0/16",
        "availabilityZones": [],
        "subnetGroups": [
            {
                "name": "Public",
                "type": "Public",
                "subnets": [
                    {"subnetId": "subnet-aaa", "availabilityZone": "us-east-1a",
                     "cidr": "172.31.0.0/20", "routeTableId": "rtb-aaa"},
                    {"subnetId": "subnet-bbb", "availabilityZone": "us-east-1b",
                     "cidr": "172.31.16.0/20", "routeTableId": "rtb-bbb"},
                ],
            }
        ],
        "vpnGatewayId": None,
    },
}


class TestMimirApp:
    @pytest.fixture
    def template(self) -> assertions.Template:
        app = cdk.App(context=VPC_CONTEXT)
        net = MimirNetwork(
            app, "Net",
            vpc_id=VPC_ID,
            huginn_rds_sg_id=RDS_SG_ID,
            env=CDK_ENV,
        )
        stack = MimirApp(
            app, "TestApp",
            vpc=net.vpc,
            eb_sg=net.eb_sg,
            acm_cert_arn=ACM_CERT_ARN,
            env=CDK_ENV,
        )
        return assertions.Template.from_stack(stack)

    def test_eb_application_named_mimir(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Application",
            {"ApplicationName": "mimir"},
        )

    def test_two_eb_environments_created(self, template):
        template.resource_count_is("AWS::ElasticBeanstalk::Environment", 2)

    def test_eb_env_blue_exists(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Environment",
            {"EnvironmentName": "mimir-blue"},
        )

    def test_eb_env_green_exists(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Environment",
            {"EnvironmentName": "mimir-green"},
        )

    def test_eb_envs_load_balanced(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Environment",
            {
                "OptionSettings": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Namespace": "aws:elasticbeanstalk:environment",
                        "OptionName": "EnvironmentType",
                        "Value": "LoadBalanced",
                    })
                ])
            },
        )

    def test_https_listener_configured(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Environment",
            {
                "OptionSettings": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Namespace": "aws:elbv2:listener:443",
                        "OptionName": "SSLCertificateArns",
                        "Value": ACM_CERT_ARN,
                    })
                ])
            },
        )

    def test_health_check_url_configured(self, template):
        template.has_resource_properties(
            "AWS::ElasticBeanstalk::Environment",
            {
                "OptionSettings": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Namespace": "aws:elasticbeanstalk:application",
                        "OptionName": "Application Healthcheck URL",
                        "Value": "/health/",
                    })
                ])
            },
        )

    def test_cloudwatch_log_group_created(self, template):
        template.has_resource_properties(
            "AWS::Logs::LogGroup",
            {"LogGroupName": "/mimir/web"},
        )

    def test_5xx_alarm_created(self, template):
        template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {"AlarmName": "mimir-http-5xx-rate"},
        )

    def test_rds_cpu_alarm_created(self, template):
        template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {"AlarmName": "mimir-rds-cpu-high"},
        )

    def test_eb_unhealthy_alarm_created(self, template):
        template.has_resource_properties(
            "AWS::CloudWatch::Alarm",
            {"AlarmName": "mimir-eb-unhealthy"},
        )


# ── MimirDns ──────────────────────────────────────────────────────────────────

ZONE_CONTEXT = {
    "hosted-zone:account=123456789012:domainName=example.com:region=us-east-1": {
        "Id": "/hostedzone/ZFAKEZONEID",
        "Name": "example.com.",
    }
}


class TestMimirDns:
    @pytest.fixture
    def template(self) -> assertions.Template:
        app = cdk.App(context=ZONE_CONTEXT)
        stack = MimirDns(
            app, "TestDns",
            domain=DOMAIN,
            acm_cert_arn=ACM_CERT_ARN,
            env=CDK_ENV,
        )
        return assertions.Template.from_stack(stack)

    def test_cloudfront_distribution_created(self, template):
        template.resource_count_is("AWS::CloudFront::Distribution", 1)

    def test_distribution_uses_mimir_cert(self, template):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": assertions.Match.object_like({
                    "ViewerCertificate": assertions.Match.object_like({
                        "AcmCertificateArn": ACM_CERT_ARN,
                    })
                })
            },
        )

    def test_distribution_domain_name_is_mimir_subdomain(self, template):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": assertions.Match.object_like({
                    "Aliases": ["mimir.example.com"],
                })
            },
        )

    def test_https_redirect_enabled(self, template):
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": assertions.Match.object_like({
                    "DefaultCacheBehavior": assertions.Match.object_like({
                        "ViewerProtocolPolicy": "redirect-to-https",
                    })
                })
            },
        )

    def test_route53_alias_record_created(self, template):
        template.resource_count_is("AWS::Route53::RecordSet", 1)

    def test_route53_record_targets_mimir_subdomain(self, template):
        template.has_resource_properties(
            "AWS::Route53::RecordSet",
            {"Name": "mimir.example.com."},
        )
