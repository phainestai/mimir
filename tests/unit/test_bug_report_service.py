"""Unit tests for BugReportService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings  # still used for GITHUB_* settings

from methodology.services.bug_report_service import BugReportService


@pytest.mark.unit
def test_submit_bug_requires_description():
    with pytest.raises(ValueError, match="Description"):
        BugReportService.submit_bug("", "a@b.com", source="ui")


@pytest.mark.unit
def test_submit_bug_requires_email():
    with pytest.raises(ValueError, match="email"):
        BugReportService.submit_bug("something broke", "", source="ui")


@pytest.mark.unit
def test_submit_bug_invalid_email():
    with pytest.raises(ValueError, match="invalid"):
        BugReportService.submit_bug("x", "not-an-email", source="ui")


@pytest.mark.unit
@override_settings(
    BUG_REPORT_DRY_RUN=True,
    GITHUB_TOKEN="",
    GITHUB_BUG_REPO="phainestai/mimir",
    MIMIR_ENV="test",
)
def test_submit_bug_dry_run_short_circuits_github():
    out = BugReportService.submit_bug(
        "Something failed\non save",
        "rep@example.com",
        source="ui",
        page_url="https://mimir.example/p",
        form_data='{"password":"sec","title":"ok"}',
    )
    assert out["issue_number"] == 0
    assert "github.com" in out["issue_url"]


@pytest.mark.unit
def test_build_body_uses_mimir_git_revision(monkeypatch):
    monkeypatch.setenv("MIMIR_GIT_REVISION", "sha-from-deploy")
    body = BugReportService.build_body_for_diagnostics(
        "Desc",
        "u@example.com",
        source="ui",
    )
    assert "sha-from-deploy" in body


@pytest.mark.unit
@override_settings(MIMIR_ENV="test")
def test_build_body_redacts_sensitive_keys():
    body = BugReportService.build_body_for_diagnostics(
        "Desc here",
        "u@example.com",
        source="ui",
        page_url="/dashboard/",
        form_data='{"username": "alice", "api_key": "secret", "nested": {"token": "x"}}',
    )
    assert "alice" in body
    assert "secret" not in body
    assert "[REDACTED]" in body


@pytest.mark.unit
@override_settings(
    GITHUB_TOKEN="ghp_test",
    GITHUB_BUG_REPO="org/repo",
    BUG_REPORT_DRY_RUN=False,
)
@patch("github.Github")
def test_submit_bug_calls_github_create_issue(mock_gh_class):
    mock_issue = MagicMock()
    mock_issue.html_url = "https://github.com/org/repo/issues/7"
    mock_issue.number = 7
    mock_repo = MagicMock()
    mock_repo.create_issue.return_value = mock_issue
    mock_gh_class.return_value.get_repo.return_value = mock_repo

    out = BugReportService.submit_bug(
        "Crash",
        "r@example.com",
        source="mcp",
        page_context="User was merging workflows",
    )

    assert out["issue_url"] == "https://github.com/org/repo/issues/7"
    assert out["issue_number"] == 7
    mock_repo.create_issue.assert_called_once()
    call_kw = mock_repo.create_issue.call_args.kwargs
    assert "Crash" in call_kw["body"]
    assert "merging workflows" in call_kw["body"]
    assert "mcp" in call_kw["title"] or "[mimir:mcp]" in call_kw["title"]
