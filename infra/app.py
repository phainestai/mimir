import aws_cdk as cdk

from stacks.app_stack import MimirApp
from stacks.dns_stack import MimirDns
from stacks.network_stack import MimirNetwork
from stacks.ses_stack import MimirSes

app = cdk.App()

env = cdk.Environment(
    account=app.node.try_get_context("account"),
    region=app.node.try_get_context("region"),
)
domain = app.node.try_get_context("domain")
vpc_id = app.node.try_get_context("vpc_id")
huginn_rds_sg_id = app.node.try_get_context("huginn_rds_sg_id")
acm_cert_arn = app.node.try_get_context("acm_cert_arn")

network = MimirNetwork(
    app, "MimirNetwork",
    vpc_id=vpc_id,
    huginn_rds_sg_id=huginn_rds_sg_id,
    env=env,
)

app_stack = MimirApp(
    app, "MimirApp",
    vpc=network.vpc,
    eb_sg=network.eb_sg,
    acm_cert_arn=acm_cert_arn,
    env=env,
)

dns = MimirDns(
    app, "MimirDns",
    domain=domain,
    acm_cert_arn=acm_cert_arn,
    env=env,
)

# SES configuration set + IAM send-email policy (domain identity is pre-existing).
# DKIM/DNS are managed outside this stack if you add identities later.
ses = MimirSes(
    app, "MimirSes",
    env=env,
)
# EB needs SES policy before it can send; MimirApp env vars reference the
# configuration set name produced by MimirSes.
app_stack.add_dependency(ses)

app.synth()
