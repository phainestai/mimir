from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_elasticbeanstalk as eb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

# Verified 2026-05-11: aws elasticbeanstalk list-available-solution-stacks
EB_SOLUTION_STACK = "64bit Amazon Linux 2023 v4.12.3 running Docker"

# Web request log group — CloudWatch agent writes here from the EB container.
WEB_LOG_GROUP = "/mimir/web"

# Shared RDS instance endpoint (huginn-db, Postgres 16).
RDS_INSTANCE_ID = "huginn-db"


class MimirApp(Stack):
    """ECR repos (import), EB application + blue/green environments, and alarms.

    EB environments are *infrastructure-only* — CDK owns platform, VPC
    placement, instance type, and static env properties.  Application version
    deployment (Docker image SHA) is handled by the CI/CD pipeline.

    Resource names match existing AWS resources for easy ``cdk import``:
        ECR repos   mimir, mimir-mcp-facade  (already exist — imported, not created)
        EB app      mimir
        EB envs     mimir-blue, mimir-green
        IAM roles   aws-elasticbeanstalk-ec2-role / aws-elasticbeanstalk-service-role
                    (both pre-exist — imported, not created)
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        eb_sg: ec2.ISecurityGroup,
        acm_cert_arn: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._vpc = vpc
        self._eb_sg = eb_sg
        self._acm_cert_arn = acm_cert_arn

        self._create_eb_app()
        self._create_cw_alarms()

    # ── EB Application + Blue/Green Environments ──────────────────────────────

    def _create_eb_app(self) -> None:
        """Create the EB application and both blue/green environments."""
        eb_app = eb.CfnApplication(
            self,
            "EbApp",
            application_name="mimir",
            description="Mimir - Self-Evolving Engineering Playbook (FOB)",
        )

        # t3.small is not available in us-east-1e — limit to AZs that support it.
        public_subnet_ids = self._vpc.select_subnets(
            subnet_type=ec2.SubnetType.PUBLIC,
            availability_zones=["us-east-1a", "us-east-1b", "us-east-1c"],
        ).subnet_ids

        for env_name in ["mimir-blue", "mimir-green"]:
            self._create_eb_env(eb_app, env_name, public_subnet_ids)

    def _create_eb_env(
        self,
        app: eb.CfnApplication,
        env_name: str,
        subnet_ids: list[str],
    ) -> eb.CfnEnvironment:
        """Create one EB environment (blue or green).

        :param app:        Parent CfnApplication resource.
        :param env_name:   Environment name, e.g. ``mimir-blue``.
        :param subnet_ids: Public subnet IDs for ALB + EC2 placement.
        :return:           The created CfnEnvironment.
        """
        env_resource = eb.CfnEnvironment(
            self,
            f"EbEnv{env_name.replace('-', '').title()}",
            application_name=app.ref,
            environment_name=env_name,
            cname_prefix=env_name,
            solution_stack_name=EB_SOLUTION_STACK,
            option_settings=self._eb_option_settings(env_name, subnet_ids),
        )
        env_resource.add_dependency(app)
        return env_resource

    def _eb_option_settings(
        self, env_name: str, subnet_ids: list[str]
    ) -> list[eb.CfnEnvironment.OptionSettingProperty]:
        """Return the full list of EB option settings for an environment."""

        def opt(ns: str, key: str, val: str) -> eb.CfnEnvironment.OptionSettingProperty:
            return eb.CfnEnvironment.OptionSettingProperty(
                namespace=ns, option_name=key, value=val
            )

        return [
            # ── Environment type ────────────────────────────────────────────
            opt("aws:elasticbeanstalk:environment", "EnvironmentType", "LoadBalanced"),
            opt("aws:elasticbeanstalk:environment", "LoadBalancerType", "application"),
            opt("aws:elasticbeanstalk:environment", "ServiceRole",
                "aws-elasticbeanstalk-service-role"),
            # ── EC2 instance ────────────────────────────────────────────────
            opt("aws:autoscaling:asg", "MinSize", "1"),
            opt("aws:autoscaling:asg", "MaxSize", "2"),
            opt("aws:autoscaling:launchconfiguration", "InstanceType", "t3.small"),
            opt("aws:autoscaling:launchconfiguration", "IamInstanceProfile",
                "aws-elasticbeanstalk-ec2-role"),
            opt("aws:autoscaling:launchconfiguration", "DisableIMDSv1", "true"),
            opt("aws:autoscaling:launchconfiguration", "SecurityGroups",
                self._eb_sg.security_group_id),
            # ── VPC placement ───────────────────────────────────────────────
            opt("aws:ec2:vpc", "VPCId", self._vpc.vpc_id),
            opt("aws:ec2:vpc", "Subnets", ",".join(subnet_ids)),
            opt("aws:ec2:vpc", "ELBSubnets", ",".join(subnet_ids)),
            opt("aws:ec2:vpc", "AssociatePublicIpAddress", "true"),
            # ── ALB HTTPS listener (port 443) ────────────────────────────────
            opt("aws:elbv2:listener:443", "ListenerEnabled", "true"),
            opt("aws:elbv2:listener:443", "Protocol", "HTTPS"),
            opt("aws:elbv2:listener:443", "SSLCertificateArns", self._acm_cert_arn),
            # ── Health check ─────────────────────────────────────────────────
            opt("aws:elasticbeanstalk:application", "Application Healthcheck URL",
                "/health/"),
            opt("aws:elasticbeanstalk:healthreporting:system", "SystemType", "enhanced"),
            # ── CloudWatch logs ──────────────────────────────────────────────
            opt("aws:elasticbeanstalk:cloudwatch:logs", "StreamLogs", "true"),
            opt("aws:elasticbeanstalk:cloudwatch:logs", "DeleteOnTerminate", "false"),
            opt("aws:elasticbeanstalk:cloudwatch:logs", "RetentionInDays", "30"),
            # ── Django app env vars ────────────────────────────────────────────
            # Non-secret static values are set here.
            # Secrets (DJANGO_SECRET_KEY, DATABASE_URL, ANTHROPIC_API_KEY, etc.)
            # must be set manually via AWS Console or CLI:
            #   aws elasticbeanstalk update-environment \
            #     --environment-name mimir-blue \
            #     --option-settings \
            #       Namespace=aws:elasticbeanstalk:application:environment,\
            #       OptionName=ANTHROPIC_API_KEY,Value=sk-ant-...
            # Or store in SSM Parameter Store at /mimir/prod/ANTHROPIC_API_KEY
            # and inject at deploy time.
            opt("aws:elasticbeanstalk:application:environment", "DJANGO_SETTINGS_MODULE",
                "mimir.settings.prod"),
            opt("aws:elasticbeanstalk:application:environment", "MIMIR_ENV", "prod"),
            # ── Galdr AI Engine ────────────────────────────────────────────────
            # ANTHROPIC_API_KEY is a secret — set manually (see comment above).
            # GALDR_MODEL is non-secret: default Anthropic model for Galdr assessment.
            opt("aws:elasticbeanstalk:application:environment", "GALDR_MODEL",
                "claude-sonnet-4-5"),
            # ── Email (AWS SES via django-ses) ─────────────────────────────────
            # Credentials come from the EB instance role (MimirSESSendEmail policy).
            # No AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY needed.
            # DEFAULT_FROM_EMAIL and AWS_SES_CONFIGURATION_SET are set here;
            # they are not secrets.
            opt("aws:elasticbeanstalk:application:environment",
                "AWS_SES_REGION_NAME", "us-east-1"),
            opt("aws:elasticbeanstalk:application:environment",
                "DEFAULT_FROM_EMAIL", "noreply@featurefactory.io"),
            opt("aws:elasticbeanstalk:application:environment",
                "AWS_SES_CONFIGURATION_SET", "mimir-transactional"),
            opt("aws:elasticbeanstalk:application:environment",
                "FRONTEND_URL", "https://mimir.featurefactory.io"),
        ]

    # ── CloudWatch Alarms ──────────────────────────────────────────────────────

    def _create_cw_alarms(self) -> None:
        """Create CloudWatch log group and key operational alarms."""
        log_group = logs.LogGroup(
            self,
            "WebLogGroup",
            log_group_name=WEB_LOG_GROUP,
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.RETAIN,
        )

        self._alarm_5xx(log_group)
        self._alarm_rds_cpu()
        self._alarm_eb_unhealthy()

    def _alarm_5xx(self, log_group: logs.LogGroup) -> None:
        """Alarm on > 5 HTTP 5xx log entries per 5 minutes."""
        metric_filter = logs.MetricFilter(
            self,
            "Http5xxFilter",
            log_group=log_group,
            filter_pattern=logs.FilterPattern.literal('"HTTP/1." 5'),
            metric_namespace="Mimir",
            metric_name="Http5xxErrors",
            metric_value="1",
            default_value=0,
        )
        cw.Alarm(
            self,
            "Http5xxAlarm",
            alarm_name="mimir-http-5xx-rate",
            alarm_description="More than 5 HTTP 5xx responses in 5 minutes",
            metric=metric_filter.metric(period=Duration.minutes(5)),
            threshold=5,
            evaluation_periods=1,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )

    def _alarm_rds_cpu(self) -> None:
        """Alarm when huginn-db CPU stays above 80% for 10 minutes."""
        rds_cpu = cw.Metric(
            namespace="AWS/RDS",
            metric_name="CPUUtilization",
            dimensions_map={"DBInstanceIdentifier": RDS_INSTANCE_ID},
            period=Duration.minutes(5),
            statistic="Average",
        )
        cw.Alarm(
            self,
            "RdsCpuAlarm",
            alarm_name="mimir-rds-cpu-high",
            alarm_description="huginn-db CPU > 80% for 10 minutes — consider dedicated RDS",
            metric=rds_cpu,
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )

    def _alarm_eb_unhealthy(self) -> None:
        """Alarm when any EB environment reports unhealthy instances."""
        unhealthy = cw.Metric(
            namespace="AWS/ElasticBeanstalk",
            metric_name="EnvironmentHealth",
            dimensions_map={"EnvironmentName": "mimir-blue"},
            period=Duration.minutes(5),
            statistic="Maximum",
        )
        cw.Alarm(
            self,
            "EbUnhealthyAlarm",
            alarm_name="mimir-eb-unhealthy",
            alarm_description="mimir-blue EB environment health degraded",
            metric=unhealthy,
            threshold=15,  # EB health: 0=Ok, 5=Warning, 10=Degraded, 15=Severely Degraded, 20=Critical
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
