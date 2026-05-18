"""
SES infrastructure for Mimir transactional emails.

Creates:
  - SES Configuration Set ``mimir-transactional`` for CloudWatch delivery metrics.
  - IAM managed policy ``MimirSESSendEmail`` (ses:SendEmail/SendRawEmail on the
    verified domain identity) attached to the EB instance role so the app can
    send without static access keys.

Domain identity (``featurefactory.io``) is **not** created by this stack: it must
already exist in SES (or be registered once manually / by another IaC repo).
Manage DKIM / MAIL-FROM DNS via Route 53 and ``aws sesv2`` as needed.

SES sandbox:
  After domain is verified, raise a production access request via AWS Support
  (Service limit: SES Sending quota).  Until lifted, email can only reach
  SES-verified addresses.
"""

import aws_cdk as cdk
from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ses as ses
from constructs import Construct

ACCOUNT_ID = "411113550285"
REGION = "us-east-1"
DOMAIN = "featurefactory.io"
EB_INSTANCE_ROLE = "aws-elasticbeanstalk-ec2-role"

# The arn of the SES identity that ses:SendEmail is scoped to.
_SES_IDENTITY_ARN = (
    f"arn:aws:ses:{REGION}:{ACCOUNT_ID}:identity/{DOMAIN}"
)


class MimirSes(Stack):
    """SES configuration set + IAM send-email policy (domain identity is external)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config_set = self._create_configuration_set()
        policy = self._create_send_policy()
        self._attach_policy_to_instance_role(policy)

        # Outputs so CDK diff / deploy shows key values
        cdk.CfnOutput(
            self,
            "SesIdentityArn",
            value=_SES_IDENTITY_ARN,
            description=(
                "Expected SES identity ARN (domain must exist in SES outside this stack)"
            ),
            export_name="mimir-ses-identity-arn",
        )
        cdk.CfnOutput(
            self,
            "SesConfigurationSet",
            value=config_set.ref,
            description="SES Configuration Set name — set as AWS_SES_CONFIGURATION_SET env var",
            export_name="mimir-ses-config-set",
        )
        cdk.CfnOutput(
            self,
            "SesPolicyArn",
            value=policy.managed_policy_arn,
            description="IAM managed policy ARN attached to EB instance role",
            export_name="mimir-ses-policy-arn",
        )

    def _create_configuration_set(self) -> ses.CfnConfigurationSet:
        """
        Configuration set for delivery, bounce, and complaint event tracking.

        Events are published to CloudWatch Metrics under the
        ``mimir-ses`` namespace (no extra setup required).
        """
        cfg_set = ses.CfnConfigurationSet(
            self,
            "SesConfigSet",
            name="mimir-transactional",
            sending_options=ses.CfnConfigurationSet.SendingOptionsProperty(
                sending_enabled=True,
            ),
            suppression_options=ses.CfnConfigurationSet.SuppressionOptionsProperty(
                suppressed_reasons=["BOUNCE", "COMPLAINT"],
            ),
        )

        # Event destination → CloudWatch (no extra IAM needed)
        ses.CfnConfigurationSetEventDestination(
            self,
            "SesCloudWatchDest",
            configuration_set_name=cfg_set.ref,
            event_destination=ses.CfnConfigurationSetEventDestination.EventDestinationProperty(
                enabled=True,
                matching_event_types=[
                    "send",
                    "delivery",
                    "bounce",
                    "complaint",
                    "reject",
                ],
                cloud_watch_destination=ses.CfnConfigurationSetEventDestination.CloudWatchDestinationProperty(
                    dimension_configurations=[
                        ses.CfnConfigurationSetEventDestination.DimensionConfigurationProperty(
                            dimension_name="MessageTag",
                            dimension_value_source="messageTag",
                            default_dimension_value="none",
                        )
                    ]
                ),
            ),
        )
        return cfg_set

    def _create_send_policy(self) -> iam.ManagedPolicy:
        """
        IAM managed policy granting ses:SendEmail on the verified domain only.

        Scoped to the single identity ARN — PoLP.
        """
        return iam.ManagedPolicy(
            self,
            "SesSendPolicy",
            managed_policy_name="MimirSESSendEmail",
            description=(
                "Allow Mimir EB instances to send email via SES "
                f"from {DOMAIN} without static access keys."
            ),
            statements=[
                iam.PolicyStatement(
                    sid="AllowSESSend",
                    effect=iam.Effect.ALLOW,
                    actions=["ses:SendEmail", "ses:SendRawEmail"],
                    resources=[_SES_IDENTITY_ARN],
                )
            ],
        )

    def _attach_policy_to_instance_role(self, policy: iam.ManagedPolicy) -> None:
        """
        Attach MimirSESSendEmail to the existing EB instance role.

        The role is imported (not created by CDK) — it already exists.
        CDK creates an IAM policy attachment resource that references it.
        """
        instance_role = iam.Role.from_role_name(
            self,
            "EbInstanceRole",
            role_name=EB_INSTANCE_ROLE,
        )
        policy.attach_to_role(instance_role)
