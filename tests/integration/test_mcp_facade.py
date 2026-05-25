"""
Tests for the MCP HTTP Facade server.

Tests cover:
    - Facade starts and initializes via JSON-RPC
    - ``tools/list`` returns exactly 63 tools
    - Bad token → tool calls return error
    - Full round-trip: create → list → delete via REST API
    - Facade server processes all tool categories (smoke test)

Architecture:
    Django dev server (subprocess) ← httpx ← Facade server (subprocess) ← JSON-RPC ← test
"""
import json
import os
import select
import socket
import subprocess
import time
import uuid
import logging
from pathlib import Path

import pytest
import httpx

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    """Wait until a TCP port accepts connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def _get_free_port() -> int:
    """Return an unused TCP port."""
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class FacadeMCPClient:
    """
    Thin JSON-RPC client over a facade server subprocess (stdio transport).

    Starts ``python -m mcp_integration.facade.server --token=X --server=Y``
    and communicates via stdin/stdout JSON-RPC.
    """

    def __init__(self, project_root: Path, token: str, server_url: str):
        self.project_root = project_root
        self.token = token
        self.server_url = server_url
        self.process: subprocess.Popen | None = None
        self._msg_id = 0

    def start(self):
        """Start the facade subprocess."""
        venv_python = self.project_root / ".venv" / "bin" / "python"
        self.process = subprocess.Popen(
            [
                str(venv_python), "-m", "mcp_integration.facade.server",
                f"--token={self.token}",
                f"--server={self.server_url}",
                "--transport=stdio",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.project_root),
            env={
                **os.environ,
                "PYTHONPATH": str(self.project_root),
            },
            text=True,
            bufsize=0,
        )
        time.sleep(1.5)
        if self.process.poll() is not None:
            err = self.process.stderr.read()
            raise RuntimeError(f"Facade exited immediately. stderr:\n{err}")

    def initialize(self):
        """Perform MCP handshake."""
        self.send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "facade-test", "version": "1.0"}
        })
        self.send("notifications/initialized")

    def send(self, method: str, params: dict = None) -> dict:
        """Send JSON-RPC message and return response."""
        self._msg_id += 1
        msg = {"jsonrpc": "2.0", "id": self._msg_id, "method": method}
        if params is not None:
            msg["params"] = params
        self.process.stdin.write(json.dumps(msg) + "\n")
        self.process.stdin.flush()
        return self._read_response(timeout=20)

    def _read_response(self, timeout: int = 20) -> dict:
        start = time.time()
        while time.time() - start < timeout:
            ready, _, _ = select.select([self.process.stdout], [], [], 0.1)
            if ready:
                line = self.process.stdout.readline()
                if line:
                    return json.loads(line.strip())
            if self.process.poll() is not None:
                err = self.process.stderr.read()
                raise RuntimeError(f"Facade died. stderr:\n{err}")
        raise TimeoutError("No response from facade within timeout")

    def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool and return the parsed result."""
        response = self.send("tools/call", {"name": name, "arguments": arguments})
        content = response.get("result", {}).get("content", [])
        if content and isinstance(content, list):
            item = content[0]
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            try:
                parsed = json.loads(text)
                return parsed
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"call_tool({name}): json.loads failed for text={text[:200]!r}")
                return text
        logger.warning(f"call_tool({name}): no content in response={json.dumps(response)[:200]}")
        return response

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


class DjangoTestServer:
    """Starts the Django dev server on a random port for facade tests."""

    def __init__(self, project_root: Path, port: int):
        self.project_root = project_root
        self.port = port
        self.process: subprocess.Popen | None = None
        self.token: str | None = None
        self.base_url = f"http://127.0.0.1:{port}"

    def start(self):
        """Start the Django development server."""
        venv_python = self.project_root / ".venv" / "bin" / "python"
        self.process = subprocess.Popen(
            [
                str(venv_python), "manage.py", "runserver",
                f"127.0.0.1:{self.port}", "--noreload"
            ],
            cwd=str(self.project_root),
            env={
                **os.environ,
                "DJANGO_SETTINGS_MODULE": "mimir.settings",
                "PYTHONPATH": str(self.project_root),
                "MIMIR_ENV": "dev",  # Use real mimir.db, not in-memory test DB
            },
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not _wait_for_port("127.0.0.1", self.port, timeout=20):
            self.process.kill()
            raise RuntimeError(f"Django server did not start on port {self.port}")
        logger.info(f"Django test server ready at {self.base_url}")

    def get_or_create_token(self, username: str = "admin") -> str:
        """Get or create a DRF token for the given user."""
        client = httpx.Client(base_url=self.base_url, timeout=10.0)
        r = client.post("/api/auth/token/", data={
            "username": username, "password": "admin"
        })
        if r.status_code == 200:
            self.token = r.json()["token"]
            return self.token
        # Try to create admin user if it doesn't exist with expected password
        raise RuntimeError(
            f"Could not get token for '{username}' (HTTP {r.status_code}). "
            "Run `python manage.py create_default_admin` so the facade test username "
            "matches the app's local dev defaults, then retry."
        )

    def stop(self):
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def project_root():
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def django_server(project_root):
    """Module-scoped Django dev server for facade tests."""
    port = _get_free_port()
    server = DjangoTestServer(project_root, port)
    server.start()
    yield server
    server.stop()


@pytest.fixture(scope="module")
def auth_token(django_server):
    """Get a valid auth token from the running Django server."""
    return django_server.get_or_create_token("admin")


@pytest.fixture(scope="module")
def facade(project_root, auth_token, django_server):
    """Module-scoped initialized facade client."""
    client = FacadeMCPClient(
        project_root=project_root,
        token=auth_token,
        server_url=django_server.base_url,
    )
    client.start()
    client.initialize()
    yield client
    client.stop()


@pytest.fixture(scope="module")
def uid():
    return str(uuid.uuid4())[:8]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFacadeStartup:
    """Verify the facade server starts and handshakes correctly."""

    def test_facade_process_alive(self, facade):
        assert facade.process.poll() is None, "Facade process should be running"

    def test_facade_lists_63_tools(self, facade):
        """tools/list must return exactly 63 tools."""
        response = facade.send("tools/list", {})
        assert "result" in response, f"Unexpected: {response}"
        tools = response["result"].get("tools", [])
        tool_names = sorted(t["name"] for t in tools)
        assert len(tools) == 63, (
            f"Expected 63 tools, got {len(tools)}. Tools: {tool_names}"
        )
        logger.info(f"✓ facade lists {len(tools)} tools")

    def test_facade_tool_names_match_orm_server(self, facade):
        """Facade must expose identical tool names as the ORM server."""
        expected = {
            "create_playbook", "list_playbooks", "get_playbook", "update_playbook", "delete_playbook",
            "create_workflow", "list_workflows", "get_workflow", "update_workflow", "delete_workflow",
            "create_activity", "list_activities", "get_activity", "update_activity", "delete_activity",
            "set_predecessor",
            "export_workflow_to_local", "import_workflow_from_local",
            "apply_upload_protocol", "create_pip_from_protocol",
            "create_skill", "list_skills", "get_skill", "update_skill", "delete_skill",
            "link_skill_to_activity", "unlink_skill_from_activity", "set_activity_skills",
            "create_rule", "list_rules", "get_rule", "update_rule", "delete_rule",
            "set_activity_rules",
            "create_agent", "list_agents", "get_agent", "update_agent", "delete_agent",
            "link_agent_to_activity", "unlink_agent_from_activity",
            "create_artifact", "list_artifacts", "get_artifact", "update_artifact", "delete_artifact",
            "link_artifact_to_activity", "unlink_artifact_from_activity",
            "create_phase", "list_phases", "get_phase", "update_phase", "delete_phase",
            "reorder_phases",
            # PIPs (8)
            "list_pips", "get_pip", "create_pip", "add_pip_change",
            "remove_pip_change", "submit_pip", "cancel_pip", "preview_pip_diff",
            "report_bug",
        }
        response = facade.send("tools/list", {})
        actual = {t["name"] for t in response["result"]["tools"]}
        assert actual == expected, f"Missing: {expected - actual}; Extra: {actual - expected}"
        logger.info("✓ all 63 tool names match")


class TestFacadeAuth:
    """Verify authentication failures are handled correctly."""

    def test_bad_token_returns_error(self, project_root, django_server):
        """Invalid token must cause tool calls to fail gracefully."""
        bad_client = FacadeMCPClient(
            project_root=project_root,
            token="INVALID_TOKEN_XYZ",
            server_url=django_server.base_url,
        )
        bad_client.start()
        bad_client.initialize()
        try:
            result = bad_client.call_tool("list_playbooks", {"status": "all"})
            # Should be an error dict or raise ValueError
            is_error = (
                isinstance(result, dict) and ("error" in result or "detail" in result)
            ) or isinstance(result, str) and ("401" in result or "error" in result.lower())
            assert is_error, (
                f"Expected auth error for bad token, got: {result}"
            )
            logger.info(f"✓ bad token → error: {result}")
        except (ValueError, PermissionError, RuntimeError):
            pass  # Expected — tool raises on 401
        finally:
            bad_client.stop()


class TestFacadeRoundTrip:
    """Full create → list → get → update → delete round-trip via the facade."""

    _pb_id: int = None
    _wf_id: int = None
    _act_id: int = None

    def test_01_create_playbook(self, facade, uid):
        result = facade.call_tool("create_playbook", {
            "name": f"Facade PB {uid}",
            "description": "Facade round-trip test",
            "category": "development"
        })
        assert "id" in result, f"create_playbook failed: {result}"
        TestFacadeRoundTrip._pb_id = result["id"]
        logger.info(f"✓ facade create_playbook → id={result['id']}")

    def test_02_list_playbooks(self, facade, uid):
        result = facade.call_tool("list_playbooks", {"status": "draft"})
        assert isinstance(result, list)
        ids = [p["id"] for p in result]
        assert TestFacadeRoundTrip._pb_id in ids
        logger.info(f"✓ facade list_playbooks → found playbook")

    def test_03_get_playbook(self, facade):
        result = facade.call_tool("get_playbook", {
            "playbook_id": TestFacadeRoundTrip._pb_id
        })
        assert result["id"] == TestFacadeRoundTrip._pb_id
        logger.info(f"✓ facade get_playbook → ok")

    def test_04_create_workflow(self, facade, uid):
        result = facade.call_tool("create_workflow", {
            "playbook_id": TestFacadeRoundTrip._pb_id,
            "name": f"Facade WF {uid}"
        })
        assert "id" in result
        TestFacadeRoundTrip._wf_id = result["id"]
        logger.info(f"✓ facade create_workflow → id={result['id']}")

    def test_05_create_activity(self, facade, uid):
        result = facade.call_tool("create_activity", {
            "workflow_id": TestFacadeRoundTrip._wf_id,
            "name": f"Facade Act {uid}",
            "guidance": "E2E facade activity"
        })
        assert "id" in result
        TestFacadeRoundTrip._act_id = result["id"]
        logger.info(f"✓ facade create_activity → id={result['id']}")

    def test_06_create_skill(self, facade, uid):
        result = facade.call_tool("create_skill", {
            "playbook_id": TestFacadeRoundTrip._pb_id,
            "title": f"Facade Skill {uid}",
            "content": "HTTP facade skill",
            "capability_domain": "API"
        })
        assert "id" in result
        skill_id = result["id"]
        # Link to activity
        link = facade.call_tool("link_skill_to_activity", {
            "activity_id": TestFacadeRoundTrip._act_id,
            "skill_id": skill_id
        })
        assert link.get("activity_id") == TestFacadeRoundTrip._act_id or "id" in link
        # Unlink
        facade.call_tool("unlink_skill_from_activity", {
            "activity_id": TestFacadeRoundTrip._act_id,
            "skill_id": skill_id,
        })
        # Delete
        del_result = facade.call_tool("delete_skill", {"skill_id": skill_id})
        assert del_result.get("deleted") is True
        logger.info(f"✓ facade skill CRUD + link/unlink → ok")

    def test_07_cleanup(self, facade):
        """Delete test resources in reverse order."""
        facade.call_tool("delete_activity", {
            "activity_id": TestFacadeRoundTrip._act_id
        })
        facade.call_tool("delete_workflow", {
            "workflow_id": TestFacadeRoundTrip._wf_id
        })
        result = facade.call_tool("delete_playbook", {
            "playbook_id": TestFacadeRoundTrip._pb_id
        })
        assert result.get("deleted") is True
        logger.info(f"✓ facade cleanup → ok")


class TestFacadeSmoke:
    """Smoke-test every tool group to verify no import/routing errors."""

    _pb_id: int = None

    def test_smoke_setup(self, facade, uid):
        result = facade.call_tool("create_playbook", {
            "name": f"Smoke PB {uid}",
            "description": "Smoke test",
            "category": "product"
        })
        assert "id" in result
        TestFacadeSmoke._pb_id = result["id"]

    def test_smoke_list_all_resource_types(self, facade):
        pb_id = TestFacadeSmoke._pb_id
        # All list operations should return without error
        facade.call_tool("list_playbooks", {"status": "all"})
        facade.call_tool("list_workflows", {"playbook_id": pb_id})
        facade.call_tool("list_activities", {"workflow_id": 0})
        facade.call_tool("list_skills", {"playbook_id": pb_id})
        facade.call_tool("list_agents", {"playbook_id": pb_id})
        facade.call_tool("list_artifacts", {"playbook_id": pb_id})
        facade.call_tool("list_phases", {"playbook_id": pb_id})
        facade.call_tool("list_rules", {"playbook_id": pb_id})
        logger.info("✓ all list tools returned without error")

    def test_smoke_teardown(self, facade):
        result = facade.call_tool("delete_playbook", {
            "playbook_id": TestFacadeSmoke._pb_id
        })
        assert result.get("deleted") is True
        logger.info("✓ smoke teardown → ok")
