"""Unit tests for Docker workspace mount validation in the MCP facade."""

from pathlib import Path

import pytest

from mcp_integration.facade import workspace_mount as wm
from mcp_integration.facade.workspace_mount import _MountEntry


OVERLAY_ROOT = [_MountEntry(mount_point=Path("/"), fstype="overlay")]
BIND_AT_DEV_ROOT = [
    _MountEntry(mount_point=Path("/"), fstype="overlay"),
    _MountEntry(mount_point=Path("/Users/you/GitHub"), fstype="ext4"),
]


def test_not_docker_passes_without_dev_root(tmp_path, monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: False)
    target = tmp_path / "export"
    resolved = wm.ensure_writable_workspace_path(str(target), purpose="export")
    assert resolved == target.resolve()


def test_docker_without_dev_root_raises(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    monkeypatch.delenv("MIMIR_DEV_ROOT", raising=False)

    with pytest.raises(ValueError, match="MIMIR_DEV_ROOT"):
        wm.ensure_writable_workspace_path("/Users/you/GitHub/export", purpose="export")


def test_docker_path_outside_dev_root_raises(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    monkeypatch.setenv("MIMIR_DEV_ROOT", "/Users/you/GitHub")
    monkeypatch.setattr(wm, "_parse_mountinfo", lambda: BIND_AT_DEV_ROOT)

    with pytest.raises(ValueError, match="outside MIMIR_DEV_ROOT"):
        wm.ensure_writable_workspace_path("/Users/other/project", purpose="export")


def test_docker_overlay_only_dev_root_raises(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    monkeypatch.setenv("MIMIR_DEV_ROOT", "/Users/you/GitHub")
    monkeypatch.setattr(wm, "_parse_mountinfo", lambda: OVERLAY_ROOT)

    with pytest.raises(ValueError, match="not bind-mounted"):
        wm.ensure_writable_workspace_path("/Users/you/GitHub/export", purpose="export")


def test_docker_bind_mount_accepts_path(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    monkeypatch.setenv("MIMIR_DEV_ROOT", "/Users/you/GitHub")
    monkeypatch.setattr(wm, "_parse_mountinfo", lambda: BIND_AT_DEV_ROOT)

    resolved = wm.ensure_writable_workspace_path(
        "/Users/you/GitHub/yggdrasil/.cursor/playbooks/edda",
        purpose="export",
    )
    assert resolved == Path("/Users/you/GitHub/yggdrasil/.cursor/playbooks/edda")


def test_relative_path_resolves_against_dev_root(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    monkeypatch.setenv("MIMIR_DEV_ROOT", "/Users/you/GitHub")
    monkeypatch.setattr(wm, "_parse_mountinfo", lambda: BIND_AT_DEV_ROOT)

    resolved = wm.ensure_writable_workspace_path(
        ".cursor/playbooks/edda",
        purpose="export",
    )
    assert resolved == Path("/Users/you/GitHub/.cursor/playbooks/edda")


def test_readable_path_must_exist(tmp_path, monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: False)
    missing = tmp_path / "missing"

    with pytest.raises(ValueError, match="does not exist"):
        wm.ensure_readable_workspace_path(str(missing), purpose="import")


def test_readable_existing_path_ok(tmp_path, monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: False)
    existing = tmp_path / "ESM"
    existing.mkdir()

    resolved = wm.ensure_readable_workspace_path(str(existing), purpose="import")
    assert resolved == existing.resolve()


@pytest.mark.parametrize(
    ("server_url", "expected"),
    [
        ("http://localhost:8000", False),
        ("http://127.0.0.1:8000", False),
        ("http://host.docker.internal:8000", False),
        ("https://mimir.featurefactory.io", True),
    ],
)
def test_is_remote_server(server_url, expected):
    assert wm.is_remote_server(server_url) is expected


def test_import_blocked_on_remote_server_in_docker(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)

    with pytest.raises(ValueError, match="hosted Mimir server"):
        wm.ensure_import_supported_on_server(
            "https://mimir.featurefactory.io",
            purpose="import",
        )


def test_import_allowed_on_local_server_in_docker(monkeypatch):
    monkeypatch.setattr(wm, "is_running_in_docker", lambda: True)
    wm.ensure_import_supported_on_server("http://host.docker.internal:8000", purpose="import")
