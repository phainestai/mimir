#!/usr/bin/env python3
"""
S8 — Post-deploy SES verification smoke check.

Verifies that all pieces of the SES integration are in place:

  1. Domain identity ``featurefactory.io`` is verified in SES.
  2. DKIM signing is enabled and (optionally) confirmed via DNS.
  3. Configuration set ``mimir-transactional`` exists and sending is enabled.
  4. IAM managed policy ``MimirSESSendEmail`` exists and is attached to
     ``aws-elasticbeanstalk-ec2-role``.
  5. (Optional) Sends a real test email to the address in $TEST_EMAIL_RECIPIENT
     and prints the SES message-id.

Usage
-----
    # With IAM role assumed (e.g. on the EB instance, or locally after aws login):
    python scripts/verify_ses.py

    # Also send a live test email:
    TEST_EMAIL_RECIPIENT=you@example.com python scripts/verify_ses.py

Requirements
------------
    boto3>=1.34  (already in requirements.txt)

Exit codes:  0 = all checks passed  |  1 = at least one check failed
"""

import os
import sys
import textwrap

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
DOMAIN = "featurefactory.io"
FROM_EMAIL = f"noreply@{DOMAIN}"
CONFIG_SET = "mimir-transactional"
EB_INSTANCE_ROLE = "aws-elasticbeanstalk-ec2-role"
POLICY_NAME = "MimirSESSendEmail"

ses_v2 = boto3.client("sesv2", region_name=REGION)
ses_v1 = boto3.client("ses", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)

_PASS = "\033[32m✔\033[0m"
_FAIL = "\033[31m✘\033[0m"
_WARN = "\033[33m⚠\033[0m"

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    sym = _PASS if ok else _FAIL
    print(f"  {sym}  {label}", f"— {detail}" if detail else "")
    if not ok:
        failures.append(label)


def section(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ── 1. Domain identity ─────────────────────────────────────────────────────


section("1 · SES domain identity")

try:
    resp = ses_v2.get_email_identity(EmailIdentity=DOMAIN)
    verified = resp.get("VerifiedForSendingStatus", False)
    check(f"Identity {DOMAIN!r} exists in SES", True)
    check(
        "Domain verified for sending",
        verified,
        "run aws ses verify-domain-identity or add DKIM CNAMEs if not verified",
    )

    dkim = resp.get("DkimAttributes", {})
    dkim_enabled = dkim.get("SigningEnabled", False)
    dkim_status = dkim.get("Status", "unknown")
    check(
        "DKIM signing enabled",
        dkim_enabled,
        f"status={dkim_status}",
    )
    check(
        "DKIM verification complete",
        dkim_status == "SUCCESS",
        f"status={dkim_status} — add CNAME records to DNS if pending",
    )
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    if code == "NotFoundException":
        check(f"Identity {DOMAIN!r} exists in SES", False, "not found — deploy MimirSes CDK stack first")
    else:
        check(f"Identity {DOMAIN!r} exists in SES", False, str(exc))


# ── 2. SES sandbox status ─────────────────────────────────────────────────


section("2 · Sending limits / sandbox")

try:
    quota = ses_v1.get_send_quota()
    max24h = quota.get("Max24HourSend", 0)
    sent24h = quota.get("SentLast24Hours", 0)
    max_rate = quota.get("MaxSendRate", 0)
    in_sandbox = max24h <= 200

    print(f"     Max24h={max24h:.0f}  Sent24h={sent24h:.0f}  MaxRate={max_rate}/s")

    if in_sandbox:
        print(
            f"  {_WARN}  Account is likely in SES sandbox (Max24h≤200).\n"
            "       Open a service-limit increase request via AWS Support\n"
            "       to send to unverified addresses."
        )
    else:
        check("SES production access", True, f"Max24h={max24h:.0f}")
except ClientError as exc:
    check("SES quota check", False, str(exc))


# ── 3. Configuration set ──────────────────────────────────────────────────


section("3 · Configuration set")

try:
    resp = ses_v2.get_configuration_set(ConfigurationSetName=CONFIG_SET)
    sending = resp.get("SendingOptions", {}).get("SendingEnabled", False)
    check(f"Config set {CONFIG_SET!r} exists", True)
    check("Sending enabled in config set", sending)
except ClientError as exc:
    code = exc.response["Error"]["Code"]
    if code == "NotFoundException":
        check(f"Config set {CONFIG_SET!r} exists", False, "deploy MimirSes CDK stack")
    else:
        check(f"Config set {CONFIG_SET!r} exists", False, str(exc))


# ── 4. IAM policy + role attachment ──────────────────────────────────────


section("4 · IAM policy & EB role attachment")

try:
    paginator = iam.get_paginator("list_policies")
    policy_arn = None
    for page in paginator.paginate(Scope="Local"):
        for p in page["Policies"]:
            if p["PolicyName"] == POLICY_NAME:
                policy_arn = p["Arn"]
                break
        if policy_arn:
            break

    check(f"Policy {POLICY_NAME!r} exists", bool(policy_arn), policy_arn or "not found")

    if policy_arn:
        attached = iam.list_entities_for_policy(PolicyArn=policy_arn, EntityFilter="Role")
        role_names = [r["RoleName"] for r in attached.get("PolicyRoles", [])]
        check(
            f"Policy attached to {EB_INSTANCE_ROLE!r}",
            EB_INSTANCE_ROLE in role_names,
            f"attached to: {role_names or 'nobody'}",
        )
except ClientError as exc:
    check("IAM policy check", False, str(exc))


# ── 5. Optional live send ─────────────────────────────────────────────────


recipient = os.environ.get("TEST_EMAIL_RECIPIENT", "").strip()
if recipient:
    section(f"5 · Live test email → {recipient}")
    try:
        resp = ses_v2.send_email(
            FromEmailAddress=FROM_EMAIL,
            Destination={"ToAddresses": [recipient]},
            ConfigurationSetName=CONFIG_SET,
            Content={
                "Simple": {
                    "Subject": {"Data": "[Mimir SES verify] smoke test"},
                    "Body": {
                        "Text": {
                            "Data": textwrap.dedent(
                                """\
                                This is an automated SES smoke test from scripts/verify_ses.py.
                                If you received this, Mimir → AWS SES is wired correctly.
                                """
                            )
                        }
                    },
                }
            },
        )
        msg_id = resp.get("MessageId", "?")
        check(f"Email sent to {recipient}", True, f"MessageId={msg_id}")
    except ClientError as exc:
        check(f"Email sent to {recipient}", False, str(exc))
else:
    print(
        f"\n  {_WARN}  Skipping live send (set TEST_EMAIL_RECIPIENT=you@example.com to enable)"
    )


# ── Summary ───────────────────────────────────────────────────────────────


print(f"\n{'═' * 60}")
if failures:
    print(f"  {_FAIL}  {len(failures)} check(s) failed:")
    for f in failures:
        print(f"       • {f}")
    sys.exit(1)
else:
    print(f"  {_PASS}  All checks passed.")
print(f"{'═' * 60}\n")
