"""
MCP HTTP Facade Server — standalone entry point.

Runs a FastMCP server with tools that call the Mimir REST API via httpx.
No Django, no ORM — only Python + httpx + fastmcp.

Usage:
    python -m mcp_integration.facade.server \\
        --token=DRFTOKEN123 \\
        --server=https://mimir.example.com \\
        [--transport=stdio]  [--port=8001]

    Environment variables (override CLI flags):
        MIMIR_TOKEN       DRF auth token
        MIMIR_SERVER_URL  Base URL of the Mimir API
"""
import argparse
import logging
import os
import sys

from fastmcp import FastMCP

import mcp_integration.facade.tools_http as tools
from mcp_integration.facade.client import configure

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mcp_facade",
        description="Mimir MCP Facade — HTTP/SSE transport MCP server",
    )
    p.add_argument("--token", default=os.environ.get("MIMIR_TOKEN", ""),
                   help="DRF auth token (or MIMIR_TOKEN env var)")
    p.add_argument("--server", default=os.environ.get("MIMIR_SERVER_URL", "http://localhost:8000"),
                   help="Mimir API base URL (or MIMIR_SERVER_URL env var)")
    p.add_argument("--transport", default="stdio", choices=["stdio", "sse"],
                   help="MCP transport: stdio (default) or sse")
    p.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8001")),
                   help="Port for SSE transport (default: 8001)")
    p.add_argument("--host", default=os.environ.get("MCP_HOST", "0.0.0.0"),
                   help="Host for SSE transport (default: 0.0.0.0)")
    return p


def _configure_logging(transport: str) -> None:
    """Configure logging — avoid stdout noise when using stdio transport."""
    level = logging.INFO
    if transport == "stdio":
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
            stream=sys.stderr,
        )
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(name)s %(levelname)s %(message)s",
        )


def _build_mcp() -> FastMCP:
    """Create and register all MCP facade tools with a FastMCP instance."""
    mcp = FastMCP("Mimir Methodology Assistant")

    # Playbooks (5)
    mcp.tool()(tools.create_playbook)
    mcp.tool()(tools.list_playbooks)
    mcp.tool()(tools.get_playbook)
    mcp.tool()(tools.update_playbook)
    mcp.tool()(tools.delete_playbook)

    # Workflows (5)
    mcp.tool()(tools.create_workflow)
    mcp.tool()(tools.list_workflows)
    mcp.tool()(tools.get_workflow)
    mcp.tool()(tools.update_workflow)
    mcp.tool()(tools.delete_workflow)

    # Activities (6)
    mcp.tool()(tools.create_activity)
    mcp.tool()(tools.list_activities)
    mcp.tool()(tools.get_activity)
    mcp.tool()(tools.update_activity)
    mcp.tool()(tools.delete_activity)
    mcp.tool()(tools.set_predecessor)

    # Export / Import (4)
    mcp.tool()(tools.export_workflow_to_local)
    mcp.tool()(tools.import_workflow_from_local)
    mcp.tool()(tools.apply_upload_protocol)
    mcp.tool()(tools.create_pip_from_protocol)

    # Skills (8)
    mcp.tool()(tools.create_skill)
    mcp.tool()(tools.list_skills)
    mcp.tool()(tools.get_skill)
    mcp.tool()(tools.update_skill)
    mcp.tool()(tools.delete_skill)
    mcp.tool()(tools.link_skill_to_activity)
    mcp.tool()(tools.unlink_skill_from_activity)
    mcp.tool()(tools.set_activity_skills)

    # Rules (6)
    mcp.tool()(tools.create_rule)
    mcp.tool()(tools.list_rules)
    mcp.tool()(tools.get_rule)
    mcp.tool()(tools.update_rule)
    mcp.tool()(tools.delete_rule)
    mcp.tool()(tools.set_activity_rules)

    # Agents (7)
    mcp.tool()(tools.create_agent)
    mcp.tool()(tools.list_agents)
    mcp.tool()(tools.get_agent)
    mcp.tool()(tools.update_agent)
    mcp.tool()(tools.delete_agent)
    mcp.tool()(tools.link_agent_to_activity)
    mcp.tool()(tools.unlink_agent_from_activity)

    # Artifacts (7)
    mcp.tool()(tools.create_artifact)
    mcp.tool()(tools.list_artifacts)
    mcp.tool()(tools.get_artifact)
    mcp.tool()(tools.update_artifact)
    mcp.tool()(tools.delete_artifact)
    mcp.tool()(tools.link_artifact_to_activity)
    mcp.tool()(tools.unlink_artifact_from_activity)

    # Phases (6)
    mcp.tool()(tools.create_phase)
    mcp.tool()(tools.list_phases)
    mcp.tool()(tools.get_phase)
    mcp.tool()(tools.update_phase)
    mcp.tool()(tools.delete_phase)
    mcp.tool()(tools.reorder_phases)

    # PIPs — Process Improvement Proposals (8)
    mcp.tool()(tools.list_pips)
    mcp.tool()(tools.get_pip)
    mcp.tool()(tools.create_pip)
    mcp.tool()(tools.add_pip_change)
    mcp.tool()(tools.remove_pip_change)
    mcp.tool()(tools.submit_pip)
    mcp.tool()(tools.cancel_pip)
    mcp.tool()(tools.preview_pip_diff)
    mcp.tool()(tools.report_bug)

    logger.info("MCP Facade: All tools registered (incl. report_bug)")
    return mcp


def main() -> None:
    """Entry point: parse args, configure client, start server."""
    args = _build_parser().parse_args()
    _configure_logging(args.transport)

    token = args.token
    server_url = args.server

    if not token:
        logger.error("No token provided. Use --token=TOKEN or MIMIR_TOKEN env var.")
        sys.exit(1)

    configure(server_url=server_url, token=token)
    logger.info(
        f"MCP Facade starting — server={server_url} transport={args.transport}"
    )

    mcp = _build_mcp()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port, show_banner=False)
    else:
        mcp.run(transport="stdio", show_banner=False, log_level="ERROR")


if __name__ == "__main__":
    main()
