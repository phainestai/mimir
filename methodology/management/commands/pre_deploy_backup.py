"""Pre-deploy database backup: pg_dump + dumpdata uploaded to S3."""

import gzip
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import boto3
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)

DUMP_EXCLUDE_APPS = ("contenttypes", "sessions", "admin")


class Command(BaseCommand):
    """Snapshot Postgres via pg_dump and dumpdata; upload both to S3."""

    help = "Upload pg_dump and dumpdata artifacts to S3 before migrations."

    def handle(self, *args, **options):
        bucket, revision, prefix = self._validate_and_build_prefix()
        logger.info(
            "pre_deploy_backup: start bucket=%s revision=%s prefix=%s",
            bucket,
            revision,
            prefix,
        )

        sql_key = f"{prefix}/mimir.sql.gz"
        fixture_key = f"{prefix}/mimir-fixture.json"

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sql_gz = tmp_path / "mimir.sql.gz"
            fixture = tmp_path / "mimir-fixture.json"

            self._run_pg_dump(sql_gz)
            self._run_dumpdata(fixture)
            self._upload_file(bucket, sql_key, sql_gz, "application/gzip")
            self._upload_file(bucket, fixture_key, fixture, "application/json")

        self.stdout.write(
            self.style.SUCCESS(
                f"Backup complete: s3://{bucket}/{prefix}/"
            )
        )
        logger.info("pre_deploy_backup: done s3://%s/%s/", bucket, prefix)

    def _validate_and_build_prefix(self) -> tuple[str, str, str]:
        database_url = os.environ.get("DATABASE_URL", "")
        bucket = os.environ.get("S3_BACKUP_BUCKET", "").strip()
        revision = os.environ.get("MIMIR_GIT_REVISION", "unknown").strip() or "unknown"

        if not bucket:
            raise CommandError("S3_BACKUP_BUCKET is required")
        if not database_url:
            raise CommandError("DATABASE_URL is required")

        parsed = urlparse(database_url)
        if parsed.scheme not in ("postgres", "postgresql"):
            raise CommandError(
                f"pre_deploy_backup requires Postgres DATABASE_URL, got scheme={parsed.scheme!r}"
            )

        engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
        if engine and "postgresql" not in engine and "sqlite" not in engine:
            logger.warning(
                "pre_deploy_backup: unexpected ENGINE=%s with postgres URL", engine
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prefix = f"pre-migrate/{revision}/{timestamp}"
        return bucket, revision, prefix

    def _run_pg_dump(self, dest: Path) -> None:
        database_url = os.environ["DATABASE_URL"]
        logger.info("pre_deploy_backup: running pg_dump")
        proc = subprocess.run(
            ["pg_dump", database_url],
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8", errors="replace")
            logger.error("pre_deploy_backup: pg_dump failed: %s", err)
            raise CommandError(f"pg_dump failed: {err}")

        with gzip.open(dest, "wb") as gz:
            gz.write(proc.stdout)
        logger.info("pre_deploy_backup: pg_dump wrote %s bytes (gzip)", dest.stat().st_size)

    def _run_dumpdata(self, dest: Path) -> None:
        """Write JSON fixture; non-fatal if schema lags the deploying image (pre-migrate)."""
        logger.info("pre_deploy_backup: running dumpdata exclude=%s", DUMP_EXCLUDE_APPS)
        try:
            with dest.open("w", encoding="utf-8") as out:
                call_command(
                    "dumpdata",
                    natural_foreign=True,
                    indent=2,
                    exclude=DUMP_EXCLUDE_APPS,
                    stdout=out,
                )
        except CommandError as exc:
            logger.warning(
                "pre_deploy_backup: dumpdata skipped (schema may lag deploying revision): %s",
                exc,
            )
            dest.write_text("[]\n", encoding="utf-8")
            return
        logger.info("pre_deploy_backup: dumpdata wrote %s bytes", dest.stat().st_size)

    def _upload_file(
        self, bucket: str, key: str, path: Path, content_type: str
    ) -> None:
        logger.info("pre_deploy_backup: uploading s3://%s/%s", bucket, key)
        client = boto3.client("s3")
        with path.open("rb") as body:
            client.upload_fileobj(
                body,
                bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
        logger.info("pre_deploy_backup: uploaded s3://%s/%s", bucket, key)
