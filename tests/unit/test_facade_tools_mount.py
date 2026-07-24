"""Unit tests for export mount guard in HTTP facade tools."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

import mcp_integration.facade.tools_http as tools
from mcp_integration.facade import workspace_mount as workspace_mount
from mcp_integration.facade.client import configure


@pytest.fixture
def configured_client():
    configure("https://mimir.featurefactory.io", "test-token")


def test_export_raises_in_docker_without_mount_before_write(
    configured_client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(workspace_mount, "is_running_in_docker", lambda: True)
    monkeypatch.delenv("MIMIR_DEV_ROOT", raising=False)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_id": 8,
        "workflow_name": "Envision the System",
        "folder_name": "ESM",
        "workflow_files": [
            {"filename": "_workflow.md", "content": "# Workflow\n"},
        ],
        "rule_files": [],
    }
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(tools, "get_client", lambda: mock_client)

    export_dir = tmp_path / "export"
    with pytest.raises(ValueError, match="MIMIR_DEV_ROOT"):
        tools.export_workflow_to_local(
            workflow_id=8,
            target_directory=str(export_dir),
            folder_name="ESM",
        )

    assert not export_dir.exists()
    mock_client.post.assert_called_once()


def test_export_writes_when_not_in_docker(
    configured_client,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(workspace_mount, "is_running_in_docker", lambda: False)

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "workflow_id": 8,
        "workflow_name": "Envision the System",
        "folder_name": "ESM",
        "workflow_files": [
            {"filename": "_workflow.md", "content": "# Workflow\n"},
        ],
        "rule_files": [],
    }
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    monkeypatch.setattr(tools, "get_client", lambda: mock_client)

    export_dir = tmp_path / "export"
    result = tools.export_workflow_to_local(
        workflow_id=8,
        target_directory=str(export_dir),
        folder_name="ESM",
    )

    workflow_md = export_dir / "ESM" / "_workflow.md"
    assert result["status"] == "exported"
    assert workflow_md.exists()
    assert workflow_md.read_text(encoding="utf-8") == "# Workflow\n"
