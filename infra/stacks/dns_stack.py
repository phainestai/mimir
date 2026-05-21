from pathlib import Path

from aws_cdk import CustomResource, Duration, Stack
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_route53 as route53
from aws_cdk.custom_resources import Provider
from constructs import Construct

# EB CNAME for the live production environment.
# Route53 points here; make swap swaps EB CNAMEs between mimir-prod and mimir-idle,
# so after a swap the mimir-prod CNAME belongs to the newly-deployed environment.
EB_PROD_CNAME = "mimir-prod.eba-8hqkems3.us-east-1.elasticbeanstalk.com"

_LAMBDA_DIR = Path(__file__).resolve().parent.parent / "lambda" / "route53_cname"


class MimirDns(Stack):
    """Route53 CNAME for mimir.featurefactory.io → mimir-prod EB environment.

    Uses an idempotent custom-resource Lambda (infra/lambda/route53_cname/handler.py)
    that UPSERTs the CNAME rather than failing if the record already exists.

    Blue/green deployment:
        gh release vX.Y.Z  → CI deploys to mimir-idle
        make swap          → swap-environment-cnames: mimir-prod ↔ mimir-idle
        Route53 CNAME (mimir-prod.eba-…) now resolves to the new code.
        mimir-idle becomes the previous prod, ready for next release.

    HTTPS is terminated at the ALB (wildcard cert on the ALB listener) — no
    CloudFront layer needed.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain: str,
        hosted_zone: route53.IHostedZone | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._domain = domain

        if hosted_zone is None:
            hosted_zone = route53.HostedZone.from_lookup(
                self, "Zone", domain_name=domain
            )

        self._upsert_cname(hosted_zone)

    def _upsert_cname(self, hosted_zone: route53.IHostedZone) -> None:
        """Idempotent CNAME upsert via Lambda custom resource.

        Survives re-deploys when the record already exists (avoids
        ConflictingResourceExists from the Route53 API).
        """
        on_event_fn = lambda_.Function(
            self,
            "Route53CnameFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.on_event",
            code=lambda_.Code.from_asset(str(_LAMBDA_DIR)),
            timeout=Duration.minutes(2),
        )

        on_event_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "route53:ListResourceRecordSets",
                    "route53:ChangeResourceRecordSets",
                ],
                resources=[
                    f"arn:aws:route53:::hostedzone/{hosted_zone.hosted_zone_id}",
                ],
            )
        )

        provider = Provider(self, "Route53CnameProvider", on_event_handler=on_event_fn)

        CustomResource(
            self,
            "MimirCnameResource",
            service_token=provider.service_token,
            properties={
                "HostedZoneId": hosted_zone.hosted_zone_id,
                "RecordName": f"mimir.{self._domain}.",
                "TargetDomain": EB_PROD_CNAME,
                "Ttl": "60",
            },
        )
