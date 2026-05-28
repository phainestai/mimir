#!/usr/bin/env python3
"""Import existing AWS resources into MimirApp using the *deployed* CFN template as base.

CDK ``cdk import`` can fail when synthesized templates drift on unchanged resources
(e.g. CDKMetadata). This script merges new resource stubs into the live stack
template and runs a CloudFormation IMPORT change set.

Usage (from repo root):
    .venv/bin/python infra/scripts/cfn_import_resources.py --execute
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

STACK = "MimirApp"
REGION = "us-east-1"
ACCOUNT = "411113550285"

NEW_RESOURCES = {
    "EbEnvMimirprod": {
        "Type": "AWS::ElasticBeanstalk::Environment",
        "DeletionPolicy": "Retain",
        "UpdateReplacePolicy": "Retain",
        "Properties": {
            "ApplicationName": "mimir",
            "EnvironmentName": "mimir-prod",
        },
        "DependsOn": ["EbApp"],
    },
    "EbEnvMimiridle": {
        "Type": "AWS::ElasticBeanstalk::Environment",
        "DeletionPolicy": "Retain",
        "UpdateReplacePolicy": "Retain",
        "Properties": {
            "ApplicationName": "mimir",
            "EnvironmentName": "mimir-idle",
        },
        "DependsOn": ["EbApp"],
    },
    "CiDeployPolicy8DEBE455": {
        "Type": "AWS::IAM::ManagedPolicy",
        "DeletionPolicy": "Retain",
        "UpdateReplacePolicy": "Retain",
        "Properties": {
            "ManagedPolicyName": "mimir-ci-policy",
            "Description": "GitHub Actions deploy (imported)",
            "Path": "/",
            "PolicyDocument": {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": "sts:GetCallerIdentity", "Resource": "*"}],
            },
        },
    },
    "CiDeployUserC7580D90": {
        "Type": "AWS::IAM::User",
        "DeletionPolicy": "Retain",
        "UpdateReplacePolicy": "Retain",
        "Properties": {"UserName": "mimir-ci", "Path": "/"},
    },
}

RESOURCES_TO_IMPORT = [
    {
        "ResourceType": "AWS::ElasticBeanstalk::Environment",
        "LogicalResourceId": "EbEnvMimirprod",
        "ResourceIdentifier": {"EnvironmentName": "mimir-prod"},
    },
    {
        "ResourceType": "AWS::ElasticBeanstalk::Environment",
        "LogicalResourceId": "EbEnvMimiridle",
        "ResourceIdentifier": {"EnvironmentName": "mimir-idle"},
    },
    {
        "ResourceType": "AWS::IAM::ManagedPolicy",
        "LogicalResourceId": "CiDeployPolicy8DEBE455",
        "ResourceIdentifier": {
            "PolicyArn": f"arn:aws:iam::{ACCOUNT}:policy/mimir-ci-policy",
        },
    },
    {
        "ResourceType": "AWS::IAM::User",
        "LogicalResourceId": "CiDeployUserC7580D90",
        "ResourceIdentifier": {"UserName": "mimir-ci"},
    },
]


def _run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=True, text=True, capture_output=True, **kwargs)


def _patch_template_drift(template: dict) -> None:
    """Align template strings with physical resources (get-template can mangle UTF-8)."""
    rds_id = "RdsCpuAlarm29EF1690"
    if rds_id not in template.get("Resources", {}):
        return
    out = subprocess.run(
        [
            "aws", "cloudwatch", "describe-alarms",
            "--alarm-names", "mimir-rds-cpu-high",
            "--region", REGION,
            "--query", "MetricAlarms[0].AlarmDescription",
            "--output", "text",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    desc = out.stdout.strip()
    template["Resources"][rds_id]["Properties"]["AlarmDescription"] = desc
    print(f"Patched {rds_id} AlarmDescription from live alarm ({len(desc)} chars)")


def _get_deployed_template() -> dict:
    out = _run(
        [
            "aws", "cloudformation", "get-template",
            "--stack-name", STACK,
            "--region", REGION,
            "--output", "json",
        ],
    ).stdout
    body = json.loads(out)["TemplateBody"]
    if isinstance(body, str):
        body = json.loads(body)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Create and execute the IMPORT change set (default: dry-run files only)",
    )
    parser.add_argument(
        "--eb-only",
        action="store_true",
        help="Import only mimir-prod and mimir-idle",
    )
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parent.parent / "cfn-import-artifacts"
    out_dir.mkdir(exist_ok=True)

    template = _get_deployed_template()
    resources = NEW_RESOURCES
    to_import = RESOURCES_TO_IMPORT
    if args.eb_only:
        resources = {k: v for k, v in NEW_RESOURCES.items() if k.startswith("EbEnv")}
        to_import = [r for r in RESOURCES_TO_IMPORT if r["LogicalResourceId"].startswith("EbEnv")]

    _patch_template_drift(template)

    for logical_id, spec in resources.items():
        if logical_id in template["Resources"]:
            print(f"Already in stack: {logical_id}", file=sys.stderr)
            return 1
        template["Resources"][logical_id] = spec

    template_path = out_dir / "import-template.json"
    import_path = out_dir / "resources-to-import.json"
    template_path.write_text(json.dumps(template))
    import_path.write_text(json.dumps(to_import))

    print(f"Wrote {template_path}")
    print(f"Wrote {import_path}")

    if not args.execute:
        print("Dry run. Re-run with --execute to apply IMPORT change set.")
        return 0

    change_set = f"mimir-import-{int(time.time())}"
    _run(
        [
            "aws", "cloudformation", "create-change-set",
            "--stack-name", STACK,
            "--region", REGION,
            "--change-set-name", change_set,
            "--change-set-type", "IMPORT",
            "--template-body", f"file://{template_path}",
            "--resources-to-import", f"file://{import_path}",
            "--parameters", "ParameterKey=BootstrapVersion,UsePreviousValue=true",
            "--capabilities", "CAPABILITY_IAM", "CAPABILITY_NAMED_IAM",
        ],
    )

    for _ in range(60):
        status = _run(
            [
                "aws", "cloudformation", "describe-change-set",
                "--stack-name", STACK,
                "--region", REGION,
                "--change-set-name", change_set,
                "--query", "Status",
                "--output", "text",
            ],
        ).stdout.strip()
        if status in ("CREATE_COMPLETE", "FAILED"):
            break
        time.sleep(2)
    else:
        print("Change set did not become ready", file=sys.stderr)
        return 1

    if status == "FAILED":
        reason = _run(
            [
                "aws", "cloudformation", "describe-change-set",
                "--stack-name", STACK,
                "--region", REGION,
                "--change-set-name", change_set,
                "--query", "StatusReason",
                "--output", "text",
            ],
        ).stdout
        print(f"Change set failed: {reason}", file=sys.stderr)
        return 1

    _run(
        [
            "aws", "cloudformation", "execute-change-set",
            "--stack-name", STACK,
            "--region", REGION,
            "--change-set-name", change_set,
        ],
    )
    print("IMPORT change set executed. Wait for stack UPDATE_COMPLETE.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
