"""EB secrets for CDK deploy — loaded from process env or ``.env`` (never committed)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

EB_APP_ENV_NS = "aws:elasticbeanstalk:application:environment"

EB_SECRET_KEYS = frozenset({
    "ANTHROPIC_API_KEY",
    "DJANGO_SECRET_KEY",
    "GITHUB_TOKEN",
    "DATABASE_URL",
})

_INFRA_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _INFRA_DIR.parent


def load_deploy_env() -> None:
    """Load ``infra/.env`` then repo ``.env``; does not override existing env vars."""
    for path in (_INFRA_DIR / ".env", _REPO_ROOT / ".env"):
        if path.is_file():
            load_dotenv(path, override=False)


def secret_env_values() -> dict[str, str]:
    """Return EB secret option values present in the environment."""
    load_deploy_env()
    return {key: os.environ[key] for key in EB_SECRET_KEYS if os.environ.get(key)}
