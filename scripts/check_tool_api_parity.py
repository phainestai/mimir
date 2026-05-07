#!/usr/bin/env python
"""
Check MCP tool to API endpoint parity.

Verifies that every MCP tool in mcp_integration/tools.py has a corresponding
REST API endpoint documented in docs/architecture/SAO.md.

Usage:
    python scripts/check_tool_api_parity.py
"""

import re
import sys
from pathlib import Path


def extract_mcp_tools(tools_file: Path) -> list[str]:
    """
    Extract all MCP tool function names from tools.py.
    
    :param tools_file: Path to mcp_integration/tools.py
    :return: List of tool function names
    """
    content = tools_file.read_text()
    
    # Match async function definitions (MCP tools)
    # Pattern: async def function_name(
    pattern = r'^async def ([a-z_]+)\('
    matches = re.findall(pattern, content, re.MULTILINE)
    
    # Filter out private/helper functions (start with _)
    tools = [name for name in matches if not name.startswith('_')]
    
    return sorted(tools)


def extract_api_endpoints(sao_file: Path) -> dict[str, str]:
    """
    Extract MCP tool to API endpoint mappings from SAO.md.
    
    :param sao_file: Path to docs/architecture/SAO.md
    :return: Dict mapping tool name to endpoint description
    """
    content = sao_file.read_text()
    
    # Find the REST API Specification section
    api_section_start = content.find('## REST API Specification')
    if api_section_start == -1:
        return {}
    
    api_section = content[api_section_start:]
    
    # Match table rows: | `tool_name` | METHOD | /api/path/ | Description |
    pattern = r'\|\s*`([a-z_]+)`\s*\|\s*([A-Z]+)\s*\|\s*`([^`]+)`\s*\|'
    matches = re.findall(pattern, api_section)
    
    # Build mapping: tool_name -> "METHOD /api/path/"
    endpoints = {}
    for tool_name, method, endpoint in matches:
        endpoints[tool_name] = f"{method} {endpoint}"
    
    return endpoints


def main():
    """Main entry point."""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # File paths
    tools_file = project_root / 'mcp_integration' / 'tools.py'
    sao_file = project_root / 'docs' / 'architecture' / 'SAO.md'
    
    # Validate files exist
    if not tools_file.exists():
        print(f"❌ Error: {tools_file} not found")
        sys.exit(1)
    
    if not sao_file.exists():
        print(f"❌ Error: {sao_file} not found")
        sys.exit(1)
    
    # Extract tools and endpoints
    print("Extracting MCP tools from mcp_integration/tools.py...")
    mcp_tools = extract_mcp_tools(tools_file)
    print(f"Found {len(mcp_tools)} MCP tools")
    
    print("\nExtracting API endpoints from docs/architecture/SAO.md...")
    api_endpoints = extract_api_endpoints(sao_file)
    print(f"Found {len(api_endpoints)} API endpoint mappings")
    
    # Check parity
    print("\n" + "="*80)
    print("MCP Tool → API Endpoint Parity Check")
    print("="*80)
    
    missing_endpoints = []
    for tool in mcp_tools:
        if tool in api_endpoints:
            print(f"✓ {tool:40} → {api_endpoints[tool]}")
        else:
            print(f"✗ {tool:40} → MISSING API ENDPOINT")
            missing_endpoints.append(tool)
    
    # Summary
    print("\n" + "="*80)
    if missing_endpoints:
        print(f"❌ FAILED: {len(missing_endpoints)} MCP tools missing API endpoints:")
        for tool in missing_endpoints:
            print(f"   - {tool}")
        sys.exit(1)
    else:
        print(f"✅ SUCCESS: All {len(mcp_tools)} MCP tools have API endpoints")
        sys.exit(0)


if __name__ == '__main__':
    main()
