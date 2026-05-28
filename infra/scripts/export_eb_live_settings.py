#!/usr/bin/env python3
"""Refresh infra/eb_live_platform_settings.json from running EB envs (no secrets)."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

REGION = "us-east-1"
ENVS = ("mimir-prod", "mimir-idle")
# Keep in sync with stacks.eb_env.EB_SECRET_KEYS
SECRET_NAMES = frozenset({
    "ANTHROPIC_API_KEY",
    "DJANGO_SECRET_KEY",
    "GITHUB_TOKEN",
    "DATABASE_URL",
})
# CFN blob duplicates env vars and embeds secrets.
SKIP_OPTIONS = frozenset({"EnvironmentVariables"})
OUT = Path(__file__).resolve().parent.parent / "eb_live_platform_settings.json"


def _fetch(env: str) -> list[dict[str, str]]:
    out = subprocess.run(
        [
            "aws", "elasticbeanstalk", "describe-configuration-settings",
            "--application-name", "mimir",
            "--environment-name", env,
            "--region", REGION,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    opts = json.loads(out.stdout)["ConfigurationSettings"][0]["OptionSettings"]
    rows = []
    for o in opts:
        if o["OptionName"] in SECRET_NAMES or o["OptionName"] in SKIP_OPTIONS:
            continue
        rows.append({
            "namespace": o["Namespace"],
            "option_name": o["OptionName"],
            "value": o.get("Value", ""),
        })
    return sorted(rows, key=lambda r: (r["namespace"], r["option_name"]))


def main() -> None:
    snap = {env: _fetch(env) for env in ENVS}
    OUT.write_text(json.dumps(snap, indent=2) + "\n")
    print(f"Wrote {OUT} ({len(snap['mimir-prod'])} prod, {len(snap['mimir-idle'])} idle settings)")


if __name__ == "__main__":
    main()
