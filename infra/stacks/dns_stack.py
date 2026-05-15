from aws_cdk import Duration, Stack
from aws_cdk import aws_certificatemanager as acm
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_route53 as route53
from aws_cdk import aws_route53_targets as targets
from constructs import Construct

# EB CNAME for the initial production environment.
# After the first blue/green swap this should be updated to whichever env is live.
EB_ORIGIN_HOST = "mimir-blue.us-east-1.elasticbeanstalk.com"


class MimirDns(Stack):
    """CloudFront distribution + Route53 CNAME for mimir.featurefactory.io.

    Creates a *new* CloudFront distribution for Mimir (distinct from the
    existing static-site distribution E1RVYM4PQIZHGZ which is left intact).
    Uses the pre-issued ACM certificate for mimir.featurefactory.io and points
    at the mimir-blue EB environment as the initial origin.

    After cutover the Route53 CNAME for mimir.featurefactory.io is updated to
    point at this distribution's domain name, replacing the old S3/CloudFront
    entry.

    ``acm_cert_arn`` must be in us-east-1 (CloudFront requirement) — the
    existing cert arn:aws:acm:us-east-1:411113550285:certificate/b0d774c7-…
    satisfies this.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        domain: str,
        acm_cert_arn: str,
        hosted_zone: route53.IHostedZone | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._domain = domain
        self._subdomain = f"mimir.{domain}"

        if hosted_zone is None:
            hosted_zone = route53.HostedZone.from_lookup(
                self, "Zone", domain_name=domain
            )

        cert = acm.Certificate.from_certificate_arn(
            self, "MimirCert", certificate_arn=acm_cert_arn
        )

        distribution = self._create_distribution(cert)
        self._create_route53_record(hosted_zone, distribution)

    def _create_distribution(self, cert: acm.ICertificate) -> cloudfront.Distribution:
        """Create the CloudFront distribution for mimir.featurefactory.io."""
        hsts_policy = cloudfront.ResponseHeadersPolicy(
            self,
            "HstsPolicy",
            security_headers_behavior=cloudfront.ResponseSecurityHeadersBehavior(
                strict_transport_security=cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(3600),
                    override=True,
                    include_subdomains=True,
                ),
            ),
        )

        return cloudfront.Distribution(
            self,
            "MimirCdn",
            domain_names=[self._subdomain],
            certificate=cert,
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    EB_ORIGIN_HOST,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                    http_port=80,
                    # Tell Django this connection is HTTPS so SECURE_SSL_REDIRECT
                    # doesn't loop (Django checks SECURE_PROXY_SSL_HEADER).
                    custom_headers={"X-Forwarded-Proto": "https"},
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                # Disable caching — Django renders dynamic pages, DRF returns live data.
                cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                # Forward all headers/cookies/query strings so Django sessions work.
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                response_headers_policy=hsts_policy,
                # Allow all methods so POST/PUT/PATCH/DELETE reach Django.
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            ),
            comment="Mimir FOB — mimir.featurefactory.io",
        )

    def _create_route53_record(
        self,
        hosted_zone: route53.IHostedZone,
        distribution: cloudfront.Distribution,
    ) -> None:
        """Create an A-alias record pointing mimir.featurefactory.io → CloudFront."""
        route53.ARecord(
            self,
            "MimirAliasRecord",
            zone=hosted_zone,
            record_name="mimir",
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(distribution)
            ),
            ttl=Duration.minutes(5),
            comment="mimir.featurefactory.io → Mimir CloudFront distribution",
        )
