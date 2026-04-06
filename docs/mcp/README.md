# MCP Integration

This directory contains documentation for the Model Context Protocol (MCP) integration in Mimir.

## Quick Start

```bash
# Start MCP server for user "maria"
python manage.py mcp_server --user=maria

# Run integration tests
pytest tests/integration/test_mcp_playbook_tools.py tests/integration/test_mcp_workflow_tools.py tests/integration/test_mcp_skill_tools.py tests/integration/test_mcp_agent_tools.py -v
```

## Documentation

- **[EXISTING_SERVICES.md](./EXISTING_SERVICES.md)** - Service layer methods available for MCP tools
- **[MCP_IMPLEMENTATION_STATUS.md](./MCP_IMPLEMENTATION_STATUS.md)** - Current implementation status
- **[../architecture/SAO.md](../architecture/SAO.md)** - Architecture documentation (Hybrid MCP Access model)

## Feature Files (BDD Specifications)

- **[../features/act-13-mcp/interact-with-playbooks-via-mcp.feature](../features/act-13-mcp/interact-with-playbooks-via-mcp.feature)** - 18 playbook scenarios
- **[../features/act-13-mcp/interact-with-workflows-via-mcp.feature](../features/act-13-mcp/interact-with-workflows-via-mcp.feature)** - 19 workflow scenarios
- **[../features/act-13-mcp/interact-with-activities-via-mcp.feature](../features/act-13-mcp/interact-with-activities-via-mcp.feature)** - 23 activity scenarios
- **[../features/act-13-mcp/interact-with-skills-via-mcp.feature](../features/act-13-mcp/interact-with-skills-via-mcp.feature)** - 15 skill scenarios
- **[../features/act-13-mcp/interact-with-agents-via-mcp.feature](../features/act-13-mcp/interact-with-agents-via-mcp.feature)** - 13 agent scenarios

## Status

✅ **FUNCTIONAL** - 34 tools implemented (5 playbook + 5 workflow + 6 activity + 4 export/import + 7 skill + 7 agent)

See [MCP_IMPLEMENTATION_STATUS.md](./MCP_IMPLEMENTATION_STATUS.md) for details.
