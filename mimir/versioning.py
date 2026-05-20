"""
Deployed app revision — single source for health JSON and bug-report payloads.

Mirrors Huginn exactly: ``MIMIR_GIT_REVISION`` env var, fallback ``"unknown"``.
Set by CI at deploy time (e.g. git SHA or tag).  No VERSION file involved.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def get_deployed_revision() -> str:
    """
    Return the deployed revision string for health checks and diagnostics.

    Mirrors Huginn: ``os.environ.get("HUGINN_GIT_REVISION", "unknown")``.

    :returns: ``MIMIR_GIT_REVISION`` env value, or ``"unknown"`` when unset.
    """
    revision = os.environ.get("MIMIR_GIT_REVISION", "unknown")
    logger.debug("revision=%s", revision)
    return revision
