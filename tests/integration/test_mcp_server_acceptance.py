"""
Acceptance test for MCP server.

Tests that the MCP server starts and responds to JSON-RPC protocol messages.
This verifies the server works independently of Windsurf configuration.
"""
import json
import subprocess
import time
import logging
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)


class MCPServerTest:
    """Helper class to manage MCP server subprocess for testing."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.process = None
        self.message_id = 0
        
    def start(self):
        """Start the MCP server subprocess."""
        logger.info("Starting MCP server subprocess...")
        
        venv_python = self.project_root / ".venv" / "bin" / "python"
        manage_py = self.project_root / "manage.py"
        
        self.process = subprocess.Popen(
            [str(venv_python), str(manage_py), "mcp_server", "--user=admin"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(self.project_root),
            env={
                "DJANGO_SETTINGS_MODULE": "mimir.settings",
                "PYTHONPATH": str(self.project_root),
            },
            text=True,
            bufsize=0,  # Unbuffered for immediate I/O
        )
        
        logger.info(f"MCP server started with PID {self.process.pid}")
        
        # Give it a moment to initialize
        time.sleep(2)
        
        if self.process.poll() is not None:
            stderr = self.process.stderr.read()
            raise RuntimeError(f"MCP server exited immediately. Stderr: {stderr}")
        
        logger.info("MCP server appears to be running")
        
    def send_message(self, method: str, params: dict = None) -> dict:
        """
        Send a JSON-RPC message to the server and get response.
        
        :param method: JSON-RPC method name
        :param params: Method parameters
        :return: Response dict
        """
        self.message_id += 1
        
        message = {
            "jsonrpc": "2.0",
            "id": self.message_id,
            "method": method,
        }
        
        if params is not None:
            message["params"] = params
        
        message_json = json.dumps(message)
        logger.info(f"Sending to server: {message_json}")
        
        # Send message
        self.process.stdin.write(message_json + "\n")
        self.process.stdin.flush()
        
        # Read response (with timeout)
        response_line = self._read_response_line(timeout=10)
        
        logger.info(f"Received from server: {response_line}")
        
        try:
            response = json.loads(response_line)
            return response
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {response_line}")
            raise ValueError(f"Invalid JSON response: {response_line}") from e
    
    def _read_response_line(self, timeout: int = 10) -> str:
        """
        Read a line from stdout with timeout.
        
        :param timeout: Timeout in seconds
        :return: Line from stdout
        :raises TimeoutError: if no response within timeout
        """
        import select
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if data is available
            readable, _, _ = select.select([self.process.stdout], [], [], 0.1)
            
            if readable:
                line = self.process.stdout.readline()
                if line:
                    return line.strip()
            
            # Check if process died
            if self.process.poll() is not None:
                stderr = self.process.stderr.read()
                raise RuntimeError(f"MCP server died. Stderr: {stderr}")
        
        raise TimeoutError(f"No response from server within {timeout} seconds")
    
    def stop(self):
        """Stop the MCP server subprocess."""
        if self.process:
            logger.info(f"Stopping MCP server PID {self.process.pid}")
            self.process.terminate()
            
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server didn't stop gracefully, killing...")
                self.process.kill()
                self.process.wait()
            
            logger.info("MCP server stopped")


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def mcp_server(project_root):
    """Start and stop MCP server for testing."""
    server = MCPServerTest(project_root)
    server.start()
    
    yield server
    
    server.stop()


def test_server_starts(mcp_server):
    """Test that the MCP server starts without crashing."""
    # If we get here, the server started successfully
    assert mcp_server.process is not None
    assert mcp_server.process.poll() is None, "Server should still be running"
    
    logger.info("✓ Server started successfully")


def test_server_initialize(mcp_server):
    """Test MCP protocol initialization handshake."""
    
    # Send initialize request
    response = mcp_server.send_message(
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    )
    
    # Check response
    assert "result" in response, f"Expected result in response: {response}"
    assert "error" not in response, f"Got error: {response.get('error')}"
    
    result = response["result"]
    assert "protocolVersion" in result
    assert "serverInfo" in result
    assert result["serverInfo"]["name"] == "Mimir Methodology Assistant"
    
    logger.info(f"✓ Server initialized: {result['serverInfo']}")


def test_list_tools(mcp_server):
    """Test that we can list available tools."""
    
    # First initialize
    mcp_server.send_message(
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    mcp_server.send_message(method="notifications/initialized")
    
    # List tools
    response = mcp_server.send_message(method="tools/list")
    
    # Check response
    assert "result" in response, f"Expected result in response: {response}"
    assert "tools" in response["result"]
    
    tools = response["result"]["tools"]
    assert len(tools) >= 20, f"Expected at least 20 tools, got {len(tools)}"
    
    tool_names = [tool["name"] for tool in tools]
    logger.info(f"✓ Found {len(tools)} tools: {tool_names}")
    
    # Verify key tools exist
    expected_tools = [
        "create_playbook",
        "list_playbooks",
        "create_workflow",
        "create_activity",
    ]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Tool {expected} not found in {tool_names}"


def test_call_list_playbooks_tool(mcp_server):
    """Test calling the list_playbooks tool."""
    
    # Initialize
    mcp_server.send_message(
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Send initialized notification
    mcp_server.send_message(method="notifications/initialized")
    
    # Call list_playbooks tool
    response = mcp_server.send_message(
        method="tools/call",
        params={
            "name": "list_playbooks",
            "arguments": {
                "status": "all"
            }
        }
    )
    
    # Check response
    assert "result" in response, f"Expected result in response: {response}"
    assert "error" not in response, f"Got error: {response.get('error')}"
    
    result = response["result"]
    assert "content" in result
    
    logger.info(f"✓ list_playbooks returned: {result}")


@pytest.fixture
def test_user(db):
    """Create test user for async context test."""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(username='testuser', email='test@test.com', password='test123')


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_get_activity_async_context(test_user):
    """
    Test that get_activity works in async context (FastMCP event loop).
    
    This test verifies the fix for the async context error where Django ORM
    calls were failing with "You cannot call this from an async context".
    
    The fix: DJANGO_ALLOW_ASYNC_UNSAFE='true' set in tools.py before imports.
    """
    from asgiref.sync import sync_to_async
    from methodology.models import Playbook, Workflow, Activity
    from mcp_integration.context import set_current_user
    from mcp_integration.tools import get_activity
    
    # Set up user context
    user = test_user
    set_current_user(user)
    
    # Create test data using Django ORM directly
    def create_test_data():
        playbook = Playbook.objects.create(
            name='Test Playbook',
            description='Test',
            category='test',
            status='draft',
            source='owned',
            author=user
        )
        workflow = Workflow.objects.create(
            name='Test Workflow',
            description='Test',
            playbook=playbook,
            order=1
        )
        activity = Activity.objects.create(
            name='Test Activity',
            guidance='Test guidance',
            workflow=workflow,
            order=1
        )
        return activity.id
    
    activity_id = await sync_to_async(create_test_data)()
    
    # Call get_activity - this should NOT raise async context error
    result = await get_activity(activity_id=activity_id)
    
    # Verify we got data back
    assert result is not None
    assert 'id' in result
    assert 'name' in result
    assert 'phase' in result
    assert 'agent' in result
    assert 'skills' in result
    assert 'output_artifacts' in result
    assert 'input_artifacts' in result
    
    logger.info(f"✓ get_activity returned: {result['name']}")
    logger.info(f"  Phase: {result.get('phase')}")
    logger.info(f"  Agent: {result.get('agent')}")
    logger.info(f"  Skills: {result.get('skills')}")
    logger.info(f"  Artifacts: {len(result.get('output_artifacts', []))} out, {len(result.get('input_artifacts', []))} in")


@pytest.mark.skip(reason="Interactive test - run manually to verify server works")
def test_server_runs_indefinitely(mcp_server):
    """
    Manual test to verify server runs without timing out.
    
    Run this with: pytest -v -s tests/integration/test_mcp_server_acceptance.py::test_server_runs_indefinitely
    """
    logger.info("Server is running. Press Ctrl+C to stop...")
    
    # Initialize
    mcp_server.send_message(
        method="initialize",
        params={
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    )
    
    # Keep alive for 60 seconds
    for i in range(60):
        time.sleep(1)
        
        # Ping the server every 10 seconds
        if i % 10 == 0:
            response = mcp_server.send_message(method="tools/list")
            logger.info(f"Ping {i//10 + 1}: Server responded with {len(response['result']['tools'])} tools")
    
    logger.info("✓ Server ran for 60 seconds without issues")
