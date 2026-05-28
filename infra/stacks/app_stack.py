import json
from pathlib import Path

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_elasticbeanstalk as eb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from constructs import Construct

from stacks.eb_env import EB_APP_ENV_NS, EB_SECRET_KEYS, secret_env_values

# Verified 2026-05-11: aws elasticbeanstalk list-available-solution-stacks
EB_SOLUTION_STACK = "64bit Amazon Linux 2023 v4.12.3 running Docker"

# Web request log group — CloudWatch agent writes here from the EB container.
WEB_LOG_GROUP = "/mimir/web"

# Shared RDS instance endpoint (huginn-db, Postgres 16).
RDS_INSTANCE_ID = "huginn-db"

# Platform option_settings mirrored from live EB (refresh: export_eb_live_settings.py).
_LIVE_EB_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "eb_live_platform_settings.json"


class MimirApp(Stack):
    """ECR repo reference, EB application + prod/idle environments, CI IAM, alarms.

    EB platform settings are loaded from ``eb_live_platform_settings.json``
    (exported from live envs) so ``cdk deploy`` can recreate the same infra.
    Application image deploy is handled by the CI/CD pipeline.

    Resource names match existing AWS resources:
        ECR repo    mimir          (referenced, not created — CI pushes images here)
                    mimir-mcp-facade  (legacy; MCP facade ships from Docker Hub: featurefactory/mimir-mcp)
        EB app      mimir
        EB envs     mimir-prod, mimir-idle
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

        self._create_ecr_repos()
        if self.node.try_get_context("ci_deploy") != "false":
            self._create_ci_user()
        self._create_eb_app()
        self._create_cw_alarms()

    # ── ECR Repositories ──────────────────────────────────────────────────────

    def _create_ecr_repos(self) -> None:
        """Reference the existing ``mimir`` ECR repo (created by CI / console).

        Do not call ``ecr.Repository()`` here — the repo already exists and
        ``cdk deploy`` would fail with "already exists". Lifecycle rules on the
        repo are managed in AWS console or a one-time ``cdk import`` if needed.
        """
        self.web_repo = ecr.Repository.from_repository_name(
            self,
            "EcrRepoMimir",
            "mimir",
        )

    # ── IAM: CI deploy user ───────────────────────────────────────────────────

    def _create_ci_user(self) -> None:
        """GitHub Actions deploy user ``mimir-ci`` and ``mimir-ci-policy``.

        Both pre-exist in IAM — adopt with ``cdk import`` (infra/import-mapping.json)
        before the first deploy. Access keys live in GitHub Secrets only.
        """
        deploy_policy = iam.ManagedPolicy(
            self,
            "CiDeployPolicy",
            managed_policy_name="mimir-ci-policy",
            description="GitHub Actions: ECR push, EB deploy, SSM pre-deploy backup, S3 verify",
            statements=[
                iam.PolicyStatement(
                    sid="ECRAuth",
                    actions=["ecr:GetAuthorizationToken"],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="ECRPush",
                    actions=[
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "ecr:PutImage",
                        "ecr:InitiateLayerUpload",
                        "ecr:UploadLayerPart",
                        "ecr:CompleteLayerUpload",
                    ],
                    resources=[
                        f"arn:aws:ecr:us-east-1:{self.account}:repository/mimir",
                    ],
                ),
                iam.PolicyStatement(
                    sid="EBDeploy",
                    actions=[
                        "elasticbeanstalk:*",
                        "ec2:Describe*",
                        "ec2:CreateSecurityGroup",
                        "ec2:CreateTags",
                        "elasticloadbalancing:*",
                        "autoscaling:*",
                        "cloudwatch:*",
                        "cloudformation:*",
                        "s3:*",
                        "logs:*",
                        "iam:PassRole",
                        "iam:GetRole",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="SSMPreDeployBackup",
                    actions=[
                        "ssm:SendCommand",
                        "ssm:GetCommandInvocation",
                        "ssm:ListCommandInvocations",
                        "ssm:DescribeInstanceInformation",
                    ],
                    resources=["*"],
                ),
                iam.PolicyStatement(
                    sid="S3BackupBucket",
                    actions=["s3:ListBucket", "s3:GetObject"],
                    resources=[
                        f"arn:aws:s3:::mimir-db-backups-{self.account}",
                        f"arn:aws:s3:::mimir-db-backups-{self.account}/*",
                    ],
                ),
            ],
        )
        deploy_user = iam.User(self, "CiDeployUser", user_name="mimir-ci")
        deploy_user.add_managed_policy(deploy_policy)

    # ── EB Application + prod/idle environments ───────────────────────────────

    def _create_eb_app(self) -> None:
        """EB application and prod/idle environments (import if already exist)."""
        eb_app = eb.CfnApplication(
            self,
            "EbApp",
            application_name="mimir",
            description="Mimir - Self-Evolving Engineering Playbook (FOB)",
        )

        if self.node.try_get_context("eb_environments") != "false":
            minimal = self.node.try_get_context("eb_minimal_import") == "true"
            for env_name in ("mimir-prod", "mimir-idle"):
                self._create_eb_env(eb_app, env_name, minimal=minimal)

    def _create_eb_env(
        self,
        app: eb.CfnApplication,
        env_name: str,
        *,
        minimal: bool = False,
    ) -> eb.CfnEnvironment:
        """Create one EB environment; settings mirror ``eb_live_platform_settings.json``."""
        props: dict = {
            "application_name": app.ref,
            "environment_name": env_name,
        }
        if not minimal:
            props["cname_prefix"] = env_name
            props["solution_stack_name"] = EB_SOLUTION_STACK
            props["option_settings"] = self._eb_option_settings(env_name)

        env_resource = eb.CfnEnvironment(
            self,
            f"EbEnv{env_name.replace('-', '').title()}",
            **props,
        )
        env_resource.add_dependency(app)
        return env_resource

    def _eb_option_settings(
        self, env_name: str
    ) -> list[eb.CfnEnvironment.OptionSettingProperty]:
        """Platform settings from JSON; secrets from ``.env`` / environment only."""
        rows = json.loads(_LIVE_EB_SETTINGS_PATH.read_text())[env_name]
        settings = [
            eb.CfnEnvironment.OptionSettingProperty(
                namespace=row["namespace"],
                option_name=row["option_name"],
                value=row["value"],
            )
            for row in rows
            if not (
                row["namespace"] == EB_APP_ENV_NS
                and row["option_name"] in EB_SECRET_KEYS
            )
        ]
        for key, value in secret_env_values().items():
            settings.append(
                eb.CfnEnvironment.OptionSettingProperty(
                    namespace=EB_APP_ENV_NS,
                    option_name=key,
                    value=value,
                )
            )
        return settings

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
        if self.node.try_get_context("eb_unhealthy_alarms") != "legacy":
            for env_name in ("mimir-prod", "mimir-idle"):
                self._alarm_eb_unhealthy(env_name)
        else:
            self._alarm_eb_unhealthy_legacy()

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
            alarm_description=(
                "huginn-db CPU > 80% for 10 minutes \u2014 consider dedicated RDS"
            ),
            metric=rds_cpu,
            threshold=80,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )

    def _alarm_eb_unhealthy_legacy(self) -> None:
        """Matches deployed EbUnhealthyAlarmE0ACF0D9 until stack import completes."""
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
            threshold=15,
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )

    def _alarm_eb_unhealthy(self, env_name: str) -> None:
        """Alarm when an EB environment reports severely degraded health."""
        suffix = env_name.split("-", 1)[1]
        unhealthy = cw.Metric(
            namespace="AWS/ElasticBeanstalk",
            metric_name="EnvironmentHealth",
            dimensions_map={"EnvironmentName": env_name},
            period=Duration.minutes(5),
            statistic="Maximum",
        )
        cw.Alarm(
            self,
            f"EbUnhealthyAlarm{suffix.title()}",
            alarm_name=f"mimir-eb-unhealthy-{suffix}",
            alarm_description=f"{env_name} EB environment health degraded",
            metric=unhealthy,
            threshold=15,  # 0=Ok, 5=Warning, 10=Degraded, 15=Severe, 20=Critical
            evaluation_periods=2,
            comparison_operator=cw.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cw.TreatMissingData.NOT_BREACHING,
        )
