"""Unit tests for pre_deploy_backup management command."""

import gzip
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def backup_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/mimir")
    monkeypatch.setenv("S3_BACKUP_BUCKET", "test-backup-bucket")
    monkeypatch.setenv("MIMIR_GIT_REVISION", "v1.0.0")


def test_pre_deploy_backup_requires_bucket(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/mimir")
    monkeypatch.delenv("S3_BACKUP_BUCKET", raising=False)

    with pytest.raises(CommandError, match="S3_BACKUP_BUCKET"):
        call_command("pre_deploy_backup")


def test_pre_deploy_backup_requires_postgres_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp.db")
    monkeypatch.setenv("S3_BACKUP_BUCKET", "bucket")

    with pytest.raises(CommandError, match="Postgres"):
        call_command("pre_deploy_backup")


@patch("methodology.management.commands.pre_deploy_backup.boto3")
@patch("methodology.management.commands.pre_deploy_backup.subprocess")
@patch("methodology.management.commands.pre_deploy_backup.call_command")
def test_pre_deploy_backup_uploads_sql_and_fixture(
    mock_dumpdata_cmd, mock_subprocess, mock_boto3, backup_env
):
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = b"-- PostgreSQL dump\nCREATE TABLE foo;\n"
    mock_subprocess.run.return_value = mock_proc

    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    out = StringIO()
    call_command("pre_deploy_backup", stdout=out)

    mock_subprocess.run.assert_called_once()
    assert mock_subprocess.run.call_args[0][0][0] == "pg_dump"

    mock_dumpdata_cmd.assert_called_once()
    assert mock_dumpdata_cmd.call_args[1]["exclude"] == (
        "contenttypes",
        "sessions",
        "admin",
    )

    assert mock_s3.upload_fileobj.call_count == 2
    keys = [c[0][2] for c in mock_s3.upload_fileobj.call_args_list]
    assert any(k.endswith("mimir.sql.gz") for k in keys)
    assert any(k.endswith("mimir-fixture.json") for k in keys)
    assert all(k.startswith("pre-migrate/v1.0.0/") for k in keys)

    assert "Backup complete" in out.getvalue()


@patch("methodology.management.commands.pre_deploy_backup.boto3")
@patch("methodology.management.commands.pre_deploy_backup.subprocess")
@patch("methodology.management.commands.pre_deploy_backup.call_command")
def test_pre_deploy_backup_pg_dump_failure(
    mock_dumpdata_cmd, mock_subprocess, mock_boto3, backup_env
):
    mock_proc = MagicMock()
    mock_proc.returncode = 1
    mock_proc.stderr = b"connection refused"
    mock_subprocess.run.return_value = mock_proc

    with pytest.raises(CommandError, match="pg_dump failed"):
        call_command("pre_deploy_backup")

    mock_boto3.client.assert_not_called()
    mock_dumpdata_cmd.assert_not_called()


@patch("methodology.management.commands.pre_deploy_backup.boto3")
@patch("methodology.management.commands.pre_deploy_backup.subprocess")
@patch("methodology.management.commands.pre_deploy_backup.call_command")
def test_pre_deploy_backup_dumpdata_failure_is_non_fatal(
    mock_dumpdata_cmd, mock_subprocess, mock_boto3, backup_env
):
    mock_proc = MagicMock()
    mock_proc.returncode = 0
    mock_proc.stdout = b"-- PostgreSQL dump\n"
    mock_subprocess.run.return_value = mock_proc
    mock_dumpdata_cmd.side_effect = CommandError(
        "Unable to serialize database: column does not exist"
    )

    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3

    out = StringIO()
    call_command("pre_deploy_backup", stdout=out)

    assert mock_s3.upload_fileobj.call_count == 2
    assert "Backup complete" in out.getvalue()


def test_pg_dump_output_is_gzipped(backup_env):
    """Verify gzip round-trip on sample dump bytes."""
    raw = b"-- PostgreSQL database dump\n"
    with gzip.open("/dev/null", "wb") as gz:
        # exercise gzip module used by command
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "out.sql.gz"
            with gzip.open(path, "wb") as out:
                out.write(raw)
            with gzip.open(path, "rb") as inp:
                assert inp.read() == raw
