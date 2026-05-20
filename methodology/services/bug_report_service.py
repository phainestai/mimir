"""
Submit user and AI-reported bugs to GitHub Issues via PyGithub.

Used by the web feedback widget, REST API (MCP HTTP facade), and MCP stdio tools.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Literal

from django.conf import settings

from mimir.versioning import get_deployed_revision

logger = logging.getLogger(__name__)

SourceKind = Literal["ui", "mcp"]

_REDACT_KEY_PARTS = frozenset(
    (
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "authorization",
        "csrf",
        "credit_card",
    )
)


class BugReportService:
    """Create GitHub Issues with structured bodies for triage and Copilot Autofix."""

    @staticmethod
    def submit_bug(
        description: str,
        reporter_email: str,
        *,
        source: SourceKind,
        page_url: str = "",
        form_data: str = "",
        page_context: str = "",
    ) -> dict[str, Any]:
        """
        Open a GitHub Issue for the configured repository.

        :param description: Free-text bug/feedback from the user or AI.
        :param reporter_email: Contact email (required for follow-up).
        :param source: ``ui`` (web widget) or ``mcp`` (assistant).
        :param page_url: Browser URL when reported from the UI.
        :param form_data: Optional JSON string of sanitized form fields.
        :param page_context: Optional extra context from MCP (e.g. tool/session summary).
        :returns: ``{"issue_url": str, "issue_number": int}``
        :raises ValueError: If configuration or input is invalid.
        """
        logger.info(
            "BugReportService.submit_bug start source=%s reporter_domain=%s desc_len=%s",
            source,
            _email_domain(reporter_email),
            len(description or ""),
        )
        _validate_inputs(description, reporter_email)
        body = _build_issue_body(
            description=description.strip(),
            reporter_email=reporter_email.strip(),
            source=source,
            page_url=(page_url or "").strip(),
            form_data=form_data or "",
            page_context=(page_context or "").strip(),
        )
        title = _issue_title(description, source)
        if getattr(settings, "BUG_REPORT_DRY_RUN", False):
            logger.info(
                "BugReportService.submit_bug dry-run; skipping GitHub API title=%r",
                title,
            )
            return {
                "issue_url": f"https://github.com/{settings.GITHUB_BUG_REPO}/issues/0",
                "issue_number": 0,
            }
        return _create_github_issue(title, body, source)

    @staticmethod
    def build_body_for_diagnostics(
        description: str,
        reporter_email: str,
        *,
        source: SourceKind,
        page_url: str = "",
        form_data: str = "",
        page_context: str = "",
    ) -> str:
        """
        Build the markdown body (used in tests and for inspection).

        :returns: Markdown string passed to GitHub as the issue body.
        """
        return _build_issue_body(
            description=description.strip(),
            reporter_email=reporter_email.strip(),
            source=source,
            page_url=(page_url or "").strip(),
            form_data=form_data or "",
            page_context=(page_context or "").strip(),
        )


def _validate_inputs(description: str, reporter_email: str) -> None:
    if not (description or "").strip():
        logger.warning("BugReportService validation failed: empty description")
        raise ValueError("Description is required.")
    if not (reporter_email or "").strip():
        logger.warning("BugReportService validation failed: empty reporter_email")
        raise ValueError("Reporter email is required.")
    if not _EMAIL_RE.match(reporter_email.strip()):
        logger.warning(
            "BugReportService validation failed: invalid email shape %r",
            reporter_email,
        )
        raise ValueError("Reporter email is invalid.")


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.strip().split("@", 1)[-1].lower()


def _issue_title(description: str, source: SourceKind) -> str:
    first = (description.strip().splitlines() or [""])[0].strip()
    if len(first) > 72:
        first = first[:69] + "..."
    prefix = "[mimir:ui]" if source == "ui" else "[mimir:mcp]"
    return f"{prefix} {first or 'Feedback'}"


def _build_issue_body(
    *,
    description: str,
    reporter_email: str,
    source: SourceKind,
    page_url: str,
    form_data: str,
    page_context: str,
) -> str:
    env = getattr(settings, "MIMIR_ENV", "dev")
    version = get_deployed_revision()
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    form_section = _format_form_data_section(form_data)
    ctx_block = (
        f"\n### Page / assistant context (MCP)\n\n{page_context}\n"
        if page_context
        else ""
    )
    url_line = f"\n- **Page URL**: `{page_url}`" if page_url else ""
    return f"""## Description

{description}

## Reproduction

- **Source**: `{source}`{url_line}
{ctx_block}
### Form / field snapshot (sanitized)

{form_section}

## Environment

- **App version**: `{version}`
- **MIMIR_ENV**: `{env}`
- **Reported at (UTC)**: `{ts}`

## Reporter

- **Email**: `{reporter_email}`

---
*Submitted via Mimir Feedback / ``report_bug`` MCP tool. Labels: `bug`, `copilot` for triage / Copilot Autofix.*
"""


def _format_form_data_section(form_data: str) -> str:
    if not (form_data or "").strip():
        return "_No form snapshot provided._"
    parsed = _parse_and_redact_form_data(form_data)
    try:
        pretty = json.dumps(parsed, indent=2, sort_keys=True)
    except (TypeError, ValueError):
        pretty = str(parsed)
    return f"```json\n{pretty}\n```"


def _parse_and_redact_form_data(raw: str) -> Any:
    raw = raw.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.info("BugReportService form_data not JSON; storing truncated raw string")
        return {"_unparsed": raw[:4000]}
    return _redact_sensitive(data)


def _redact_sensitive(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            key_l = str(k).lower()
            if any(part in key_l for part in _REDACT_KEY_PARTS):
                out[k] = "[REDACTED]"
            else:
                out[k] = _redact_sensitive(v)
        return out
    if isinstance(obj, list):
        return [_redact_sensitive(x) for x in obj[:200]]
    return obj


def _create_github_issue(title: str, body: str, source: SourceKind) -> dict[str, Any]:
    token = getattr(settings, "GITHUB_TOKEN", "") or ""
    repo_name = getattr(settings, "GITHUB_BUG_REPO", "") or ""
    if not token:
        logger.error("BugReportService GITHUB_TOKEN not configured")
        raise ValueError(
            "Bug reporting is not configured (missing GITHUB_TOKEN on the server)."
        )
    from github import Github, GithubException

    labels = ["bug", "copilot", f"source-{source}"]
    logger.info(
        "BugReportService creating GitHub issue repo=%s labels=%s",
        repo_name,
        labels,
    )
    g = Github(token)
    repo = g.get_repo(repo_name)
    try:
        issue = repo.create_issue(title=title, body=body, labels=labels)
    except GithubException as exc:
        if exc.status != 422:
            logger.exception("BugReportService GitHub API error: %s", exc)
            raise ValueError(f"GitHub rejected the bug report: {exc}") from exc
        logger.warning(
            "BugReportService label error, retrying without labels: %s", exc
        )
        issue = repo.create_issue(title=title, body=body)
    logger.info(
        "BugReportService created issue #%s url=%s",
        issue.number,
        issue.html_url,
    )
    return {"issue_url": issue.html_url, "issue_number": issue.number}
