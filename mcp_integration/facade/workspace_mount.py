"""Docker workspace mount validation for HTTP MCP facade filesystem tools."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import NamedTuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_CONTAINER_ROOT_FSTYPES = frozenset({"overlay", "aufs", "rootfs"})


class _MountEntry(NamedTuple):
    mount_point: Path
    fstype: str


def is_running_in_docker() -> bool:
    """Return True when the facade process runs inside a Docker container."""
    return Path("/.dockerenv").exists()


def get_dev_root() -> str | None:
    """Return MIMIR_DEV_ROOT env value, or None when unset/blank."""
    value = os.environ.get("MIMIR_DEV_ROOT", "").strip()
    return value or None


def resolve_workspace_path(path: str) -> Path:
    """
    Resolve a workspace path, anchoring relatives to MIMIR_DEV_ROOT when set.

    :param path: Target or source path from the MCP tool call
    :return: Resolved absolute Path
    """
    candidate = Path(path)
    dev_root = get_dev_root()
    if not candidate.is_absolute() and dev_root:
        candidate = Path(dev_root) / candidate
    return candidate.resolve()


def _parse_mountinfo() -> list[_MountEntry]:
    mountinfo = Path("/proc/self/mountinfo")
    if not mountinfo.exists():
        return []

    entries: list[_MountEntry] = []
    for line in mountinfo.read_text(encoding="utf-8").splitlines():
        if " - " not in line:
            continue
        before, after = line.split(" - ", 1)
        before_fields = before.split()
        after_fields = after.split()
        if len(before_fields) < 5 or not after_fields:
            continue
        mount_point = Path(before_fields[4])
        fstype = after_fields[0]
        entries.append(_MountEntry(mount_point=mount_point, fstype=fstype))
    return entries


def _nearest_mount(path: Path, entries: list[_MountEntry]) -> _MountEntry | None:
    resolved = path.resolve()
    mount_points = sorted(
        {entry.mount_point.resolve() for entry in entries},
        key=lambda mount_point: len(str(mount_point)),
        reverse=True,
    )
    current = resolved
    while True:
        for mount_point in mount_points:
            if current == mount_point:
                for entry in entries:
                    if entry.mount_point.resolve() == mount_point:
                        return entry
        if current == current.parent:
            break
        current = current.parent
    return None


def is_bind_mount(path: Path) -> bool:
    """
    Return True when path sits on a bind mount rather than container overlay root.

    :param path: Absolute path to validate
    """
    entries = _parse_mountinfo()
    if not entries:
        return not is_running_in_docker()

    mount = _nearest_mount(path, entries)
    if mount is None:
        return False
    if mount.mount_point == Path("/"):
        return mount.fstype not in _CONTAINER_ROOT_FSTYPES
    return True


def format_mount_setup_error(
    *,
    reason: str,
    dev_root: str | None = None,
) -> str:
    """Build an actionable error message for missing or invalid workspace mounts."""
    lines = [
        "Local filesystem access requires a bind-mounted workspace in the "
        "Mimir MCP Docker container.",
        "",
        f"Reason: {reason}",
        "",
    ]
    if dev_root:
        lines.extend(
            [
                f"MIMIR_DEV_ROOT is set to {dev_root!r} but that path is not bind-mounted.",
                "Add a matching volume mount in your IDE MCP config:",
                "",
                f'  "-e", "MIMIR_DEV_ROOT={dev_root}",',
                f'  "-v", "{dev_root}:{dev_root}"',
                "",
            ]
        )
    else:
        lines.extend(
            [
                "Set MIMIR_DEV_ROOT to your development folder and mount it in "
                "your IDE MCP config:",
                "",
                '  "-e", "MIMIR_DEV_ROOT=<your-dev-folder>",',
                '  "-v", "<your-dev-folder>:<your-dev-folder>"',
                "",
                "Examples:",
                "  macOS:  MIMIR_DEV_ROOT=/Users/you/GitHub",
                "  Windows (Docker Desktop): MIMIR_DEV_ROOT=C:/Users/you/GitHub",
                "",
            ]
        )

    lines.extend(
        [
            'Relative paths like ".cursor/playbooks/edda" are resolved against '
            "MIMIR_DEV_ROOT.",
            "",
            "Alternative: use mimir-local (manage.py mcp_server) for filesystem "
            "tools without Docker mounts.",
        ]
    )
    return "\n".join(lines)


def _validate_docker_workspace(path: str, *, purpose: str) -> Path:
    dev_root = get_dev_root()
    if not dev_root:
        message = format_mount_setup_error(
            reason=f"{purpose} requested but MIMIR_DEV_ROOT is not set",
        )
        logger.warning(
            "workspace_mount: rejected %s path=%r reason=no_dev_root",
            purpose,
            path,
        )
        raise ValueError(message)

    dev_root_path = Path(dev_root).resolve()
    resolved = resolve_workspace_path(path)

    try:
        resolved.relative_to(dev_root_path)
    except ValueError as exc:
        message = format_mount_setup_error(
            reason=(
                f"{purpose} path {path!r} resolves to {resolved} which is outside "
                f"MIMIR_DEV_ROOT {dev_root_path}"
            ),
            dev_root=dev_root,
        )
        logger.warning(
            "workspace_mount: rejected %s path=%r resolved=%s dev_root=%s",
            purpose,
            path,
            resolved,
            dev_root_path,
        )
        raise ValueError(message) from exc

    if not is_bind_mount(dev_root_path):
        message = format_mount_setup_error(
            reason=(
                f"MIMIR_DEV_ROOT {dev_root_path} is not bind-mounted into the "
                "container (writes would land in ephemeral container storage)"
            ),
            dev_root=dev_root,
        )
        logger.warning(
            "workspace_mount: rejected %s path=%r dev_root=%s reason=not_bind_mount",
            purpose,
            path,
            dev_root_path,
        )
        raise ValueError(message)

    logger.info(
        "workspace_mount: validated %s path=%r resolved=%s dev_root=%s",
        purpose,
        path,
        resolved,
        dev_root_path,
    )
    return resolved


def ensure_writable_workspace_path(path: str, *, purpose: str = "export") -> Path:
    """
    Validate that a path can be written from the Docker facade.

    :param path: Target directory from the MCP tool call
    :param purpose: Short label for logs/errors
    :return: Resolved path ready for writes
    :raises ValueError: when Docker mount requirements are not met
    """
    if not is_running_in_docker():
        return resolve_workspace_path(path)
    return _validate_docker_workspace(path, purpose=purpose)


def ensure_readable_workspace_path(path: str, *, purpose: str = "import") -> Path:
    """
    Validate that a path can be read from the Docker facade.

    :param path: Source file or directory from the MCP tool call
    :param purpose: Short label for logs/errors
    :return: Resolved path ready for reads
    :raises ValueError: when Docker mount requirements are not met or path missing
    """
    resolved = (
        _validate_docker_workspace(path, purpose=purpose)
        if is_running_in_docker()
        else resolve_workspace_path(path)
    )
    if not resolved.exists():
        raise ValueError(
            f"{purpose}: path does not exist: {resolved} "
            f"(original: {path!r})"
        )
    return resolved


def is_remote_server(server_url: str) -> bool:
    """Return True when the facade targets a hosted FOB rather than local dev."""
    hostname = (urlparse(server_url).hostname or "").lower()
    return hostname not in {
        "localhost",
        "127.0.0.1",
        "host.docker.internal",
        "web",
    }


def ensure_import_supported_on_server(server_url: str, *, purpose: str) -> None:
    """
    Reject import/protocol tools against hosted FOB when running in Docker.

    Import still reads paths on the server filesystem; hosted FOB cannot see
    the client's mounted workspace until payload-based import is implemented.
    """
    if not is_running_in_docker() or not is_remote_server(server_url):
        return

    raise ValueError(
        f"{purpose} against a hosted Mimir server is not supported from the Docker "
        "MCP facade because the server cannot read files on your machine.\n\n"
        "Use one of:\n"
        "  • mimir-local (manage.py mcp_server) for import/protocol tools\n"
        "  • Docker MCP with MIMIR_SERVER_URL=http://host.docker.internal:8000 "
        "and a local FOB instance\n"
        "  • Export-only sync via Docker MCP with MIMIR_DEV_ROOT bind mount"
    )
