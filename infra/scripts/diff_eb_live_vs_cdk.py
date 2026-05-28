#!/usr/bin/env python3
"""Compare live Elastic Beanstalk option settings to CDK ``_eb_option_settings`` output.

Does not call AWS for CDK values — reads a synthesized template or prints the
keys/values the stack would apply when ``eb_minimal_import`` is off.

Usage:
    # Live settings from AWS (both envs):
    .venv/bin/python infra/scripts/diff_eb_live_vs_cdk.py

    # After editing app_stack, preview CDK-side settings:
    cd infra && cdk synth MimirApp -q
    .venv/bin/python ../infra/scripts/diff_eb_live_vs_cdk.py --cdk-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REGION = "us-east-1"
ENVS = ("mimir-prod", "mimir-idle")
SECRET_NAMES = frozenset({
    "ANTHROPIC_API_KEY",
    "DJANGO_SECRET_KEY",
    "GITHUB_TOKEN",
    "DATABASE_URL",
})
CDK_OPTION_KEYS = (
    "EnvironmentType",
    "LoadBalancerType",
    "ServiceRole",
    "MinSize",
    "MaxSize",
    "InstanceType",
    "IamInstanceProfile",
    "DisableIMDSv1",
    "SecurityGroups",
    "VPCId",
    "Subnets",
    "ELBSubnets",
    "AssociatePublicIpAddress",
    "ListenerEnabled",
    "Protocol",
    "SSLCertificateArns",
    "Application Healthcheck URL",
    "SystemType",
    "StreamLogs",
    "DeleteOnTerminate",
    "RetentionInDays",
    "DJANGO_SETTINGS_MODULE",
    "MIMIR_ENV",
    "GALDR_MODEL",
    "AWS_SES_REGION_NAME",
    "DEFAULT_FROM_EMAIL",
    "AWS_SES_CONFIGURATION_SET",
    "FRONTEND_URL",
    "COOKIE_SECURE",
)


def _fetch_live_settings(env_name: str) -> dict[str, str]:
    out = subprocess.run(
        [
            "aws", "elasticbeanstalk", "describe-configuration-settings",
            "--application-name", "mimir",
            "--environment-name", env_name,
            "--region", REGION,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(out.stdout)
    settings: dict[str, str] = {}
    for block in data.get("ConfigurationSettings", []):
        for opt in block.get("OptionSettings", []):
            if opt["OptionName"] in SECRET_NAMES:
                continue
            key = f"{opt['Namespace']}|{opt['OptionName']}"
            settings[key] = opt.get("Value", "")
    return settings


def _fetch_cdk_settings_from_synth(env_name: str = "mimir-prod") -> dict[str, str]:
    """Read option_settings from synthesized MimirApp template."""
    infra = Path(__file__).resolve().parent.parent
    subprocess.run(
        ["cdk", "synth", "MimirApp", "-q"],
        cwd=infra,
        check=True,
        capture_output=True,
    )
    logical = "EbEnvMimirprod" if env_name == "mimir-prod" else "EbEnvMimiridle"
    template = json.loads((infra / "cdk.out" / "MimirApp.template.json").read_text())
    resource = template["Resources"][logical]
    settings: dict[str, str] = {}
    for opt in resource["Properties"].get("OptionSettings", []):
        key = f"{opt['Namespace']}|{opt['OptionName']}"
        settings[key] = opt.get("Value", "")
    return settings


def _report(env_name: str, live: dict[str, str], cdk: dict[str, str]) -> int:
    """Print diff for one env. Returns count of differing keys."""
    print(f"\n=== {env_name} ===")
    diffs = 0
    for key in sorted(set(live) | set(cdk)):
        lv = live.get(key)
        cv = cdk.get(key)
        if lv != cv:
            print(f"  DIFF {key}")
            print(f"    live: {lv!r}")
            print(f"    cdk:  {cv!r}")
            diffs += 1
    live_only = set(live) - set(cdk)
    secret_prefix = "aws:elasticbeanstalk:application:environment|"
    extra = sorted(k for k in live_only if k.startswith(secret_prefix))
    if extra:
        print(f"  Live-only env vars ({len(extra)}) — not in CDK template:")
        for k in extra[:20]:
            name = k.split("|", 1)[1]
            if any(s in name.upper() for s in ("KEY", "SECRET", "PASSWORD", "TOKEN", "URL")):
                print(f"    {name}=<redacted>")
            else:
                print(f"    {name}={live[k]!r}")
        if len(extra) > 20:
            print(f"    ... and {len(extra) - 20} more")
    return diffs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cdk-only",
        action="store_true",
        help="Only print CDK synthesized option_settings (no AWS calls)",
    )
    args = parser.parse_args()

    if args.cdk_only:
        cdk = _fetch_cdk_settings_from_synth()
        print(json.dumps(cdk, indent=2, sort_keys=True))
        return 0

    total = 0
    for env in ENVS:
        live = _fetch_live_settings(env)
        cdk = _fetch_cdk_settings_from_synth(env)
        total += _report(env, live, cdk)

    print(f"\nTotal tracked diffs (prod template vs live): {total}")
    if total:
        print(
            "Do NOT run `cdk deploy MimirApp` without resolving these — "
            "deploy would push CDK values to EB."
        )
    else:
        print("Tracked platform keys match. Review live-only env vars before codifying.")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
