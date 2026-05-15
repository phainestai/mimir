"""
MCP HTTP Facade.

Standalone MCP server whose tools call the Mimir REST API via httpx.
No Django, no ORM — just Python + httpx + fastmcp.

Usage:
    python -m mcp_integration.facade.server \\
        --token=DRFTOKEN123 \\
        --server=https://mimir.featurefactory.io \\
        [--transport=stdio|sse] [--port=8001]
"""
