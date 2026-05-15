# API ↔ MCP Tool Reconciliation

**Status**: ✅ **Complete** - All 53 MCP tools have corresponding API endpoints

**Last Updated**: 2026-05-08

## Summary

This document verifies that every MCP tool in `mcp_integration/tools.py` has a corresponding REST API endpoint implemented in the DRF ViewSets.

### Verification Method

1. **Automated Parity Checker**: `scripts/check_tool_api_parity.py`
   - Extracts all MCP tool function names from `mcp_integration/tools.py`
   - Extracts all API endpoint mappings from `docs/architecture/SAO.md`
   - Validates 1:1 correspondence

2. **Manual Implementation Check**: Verified all action methods exist in ViewSets

## Complete Mapping (53 Tools)

### Playbook Operations (5 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_playbook` | POST | `/api/playbooks/` | PlaybookViewSet.create() | ✅ |
| `list_playbooks` | GET | `/api/playbooks/` | PlaybookViewSet.list() | ✅ |
| `get_playbook` | GET | `/api/playbooks/{id}/` | PlaybookViewSet.retrieve() | ✅ |
| `update_playbook` | PATCH | `/api/playbooks/{id}/` | PlaybookViewSet.update() | ✅ |
| `delete_playbook` | DELETE | `/api/playbooks/{id}/` | PlaybookViewSet.destroy() | ✅ |

### Workflow Operations (9 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_workflow` | POST | `/api/workflows/` | WorkflowViewSet.create() | ✅ |
| `list_workflows` | GET | `/api/workflows/?playbook_id={id}` | WorkflowViewSet.list() | ✅ |
| `get_workflow` | GET | `/api/workflows/{id}/` | WorkflowViewSet.retrieve() | ✅ |
| `update_workflow` | PATCH | `/api/workflows/{id}/` | WorkflowViewSet.update() | ✅ |
| `delete_workflow` | DELETE | `/api/workflows/{id}/` | WorkflowViewSet.destroy() | ✅ |
| `export_workflow_to_local` | POST | `/api/workflows/{id}/export/` | WorkflowViewSet.export() | ✅ |
| `import_workflow_from_local` | POST | `/api/workflows/{id}/import_workflow/` | WorkflowViewSet.import_workflow() | ✅ |
| `apply_upload_protocol` | POST | `/api/workflows/{id}/apply-protocol/` | WorkflowViewSet.apply_protocol() | ✅ |
| `create_pip_from_protocol` | POST | `/api/workflows/{id}/create-pip/` | WorkflowViewSet.create_pip() | ✅ |

### Activity Operations (7 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_activity` | POST | `/api/activities/` | ActivityViewSet.create() | ✅ |
| `list_activities` | GET | `/api/activities/?workflow_id={id}` | ActivityViewSet.list() | ✅ |
| `get_activity` | GET | `/api/activities/{id}/` | ActivityViewSet.retrieve() | ✅ |
| `update_activity` | PATCH | `/api/activities/{id}/` | ActivityViewSet.update() | ✅ |
| `delete_activity` | DELETE | `/api/activities/{id}/` | ActivityViewSet.destroy() | ✅ |
| `set_predecessor` | PUT | `/api/activities/{id}/predecessor/` | ActivityViewSet.predecessor() | ✅ |
| `set_activity_rules` | PUT | `/api/activities/{id}/rules/` | ActivityViewSet.rules() | ✅ |

### Skill Operations (7 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_skill` | POST | `/api/skills/` | SkillViewSet.create() | ✅ |
| `list_skills` | GET | `/api/skills/?playbook_id={id}` | SkillViewSet.list() | ✅ |
| `get_skill` | GET | `/api/skills/{id}/` | SkillViewSet.retrieve() | ✅ |
| `update_skill` | PATCH | `/api/skills/{id}/` | SkillViewSet.update() | ✅ |
| `delete_skill` | DELETE | `/api/skills/{id}/` | SkillViewSet.destroy() | ✅ |
| `link_skill_to_activity` | PUT | `/api/activities/{id}/skill/` | ActivityViewSet.skill() [PUT] | ✅ |
| `unlink_skill_from_activity` | DELETE | `/api/activities/{id}/skill/` | ActivityViewSet.skill() [DELETE] | ✅ |

### Agent Operations (7 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_agent` | POST | `/api/agents/` | AgentViewSet.create() | ✅ |
| `list_agents` | GET | `/api/agents/?playbook_id={id}` | AgentViewSet.list() | ✅ |
| `get_agent` | GET | `/api/agents/{id}/` | AgentViewSet.retrieve() | ✅ |
| `update_agent` | PATCH | `/api/agents/{id}/` | AgentViewSet.update() | ✅ |
| `delete_agent` | DELETE | `/api/agents/{id}/` | AgentViewSet.destroy() | ✅ |
| `link_agent_to_activity` | PUT | `/api/activities/{id}/agent/` | ActivityViewSet.agent() [PUT] | ✅ |
| `unlink_agent_from_activity` | DELETE | `/api/activities/{id}/agent/` | ActivityViewSet.agent() [DELETE] | ✅ |

### Artifact Operations (7 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_artifact` | POST | `/api/artifacts/` | ArtifactViewSet.create() | ✅ |
| `list_artifacts` | GET | `/api/artifacts/?playbook_id={id}` | ArtifactViewSet.list() | ✅ |
| `get_artifact` | GET | `/api/artifacts/{id}/` | ArtifactViewSet.retrieve() | ✅ |
| `update_artifact` | PATCH | `/api/artifacts/{id}/` | ArtifactViewSet.update() | ✅ |
| `delete_artifact` | DELETE | `/api/artifacts/{id}/` | ArtifactViewSet.destroy() | ✅ |
| `link_artifact_to_activity` | POST | `/api/artifacts/{id}/consumers/` | ArtifactViewSet.consumers() | ✅ |
| `unlink_artifact_from_activity` | DELETE | `/api/artifact-inputs/{id}/` | ArtifactInputViewSet.destroy() | ✅ |

### Phase Operations (6 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_phase` | POST | `/api/phases/` | PhaseViewSet.create() | ✅ |
| `list_phases` | GET | `/api/phases/?playbook_id={id}` | PhaseViewSet.list() | ✅ |
| `get_phase` | GET | `/api/phases/{id}/` | PhaseViewSet.retrieve() | ✅ |
| `update_phase` | PATCH | `/api/phases/{id}/` | PhaseViewSet.update() | ✅ |
| `delete_phase` | DELETE | `/api/phases/{id}/` | PhaseViewSet.destroy() | ✅ |
| `reorder_phases` | PUT | `/api/playbooks/{id}/phases/reorder/` | PlaybookViewSet.reorder_phases() | ✅ |

### Rule Operations (5 tools)
| MCP Tool | HTTP Method | API Endpoint | ViewSet | Status |
|----------|-------------|--------------|---------|--------|
| `create_rule` | POST | `/api/rules/` | RuleViewSet.create() | ✅ |
| `list_rules` | GET | `/api/rules/?playbook_id={id}` | RuleViewSet.list() | ✅ |
| `get_rule` | GET | `/api/rules/{id}/` | RuleViewSet.retrieve() | ✅ |
| `update_rule` | PATCH | `/api/rules/{id}/` | RuleViewSet.update() | ✅ |
| `delete_rule` | DELETE | `/api/rules/{id}/` | RuleViewSet.destroy() | ✅ |

## Implementation Notes

### Standard CRUD Operations
Most resources use Django REST Framework's `ModelViewSet` which automatically provides:
- `create()` → POST `/api/{resource}/`
- `list()` → GET `/api/{resource}/`
- `retrieve()` → GET `/api/{resource}/{id}/`
- `update()` / `partial_update()` → PATCH `/api/{resource}/{id}/`
- `destroy()` → DELETE `/api/{resource}/{id}/`

### Custom Actions
Special operations use DRF's `@action` decorator:
- **Workflow Export/Import**: File-based operations for local markdown sync
- **Protocol Application**: Upload protocol processing for draft/released playbooks
- **Phase Reordering**: Bulk update of phase order within playbook
- **Linking Operations**: M2M and FK relationships (skill/agent/artifact to activity)

### Service Layer Integration
All ViewSets delegate business logic to service classes:
- `PlaybookService` - playbook CRUD and versioning
- `WorkflowService` - workflow CRUD
- `ActivityService` - activity CRUD and dependencies
- `WorkflowExportService` - markdown export
- `WorkflowImportService` - markdown import and protocol application
- `PhaseService` - phase reordering
- `PIPService` - PIP creation from protocols

## Testing Coverage

### Current Tests
- **7 integration tests** in `tests/integration/test_api_basic.py`:
  - Token authentication
  - Playbook CRUD operations
  - Error handling and format
  - Permission checks

### Planned Tests (Phase 4+)
- Comprehensive endpoint tests for all 53 tools
- Group-based visibility tests
- Multi-user ownership tests
- Rate limiting tests
- CORS policy tests

## Verification Commands

```bash
# Run parity checker
python scripts/check_tool_api_parity.py

# Expected output:
# ✅ SUCCESS: All 53 MCP tools have API endpoints

# Run API tests
pytest tests/integration/test_api_basic.py -v

# Expected: 7 passed
```

## Future Enhancements

### Phase 4: Group-Based Visibility
- Add group membership filtering to all list endpoints
- Update permissions to check group access
- Add shared playbook endpoints

### Phase 5: Token Management
- Add token refresh endpoint
- Add token revocation endpoint
- Add user registration endpoint

### Phase 6: MCP Facade
- Lightweight container that proxies stdio MCP requests to HTTP API
- Handles token management for user
- Provides seamless MCP experience while using centralized API

## Conclusion

✅ **All 53 MCP tools have corresponding API endpoints implemented**

The REST API provides complete feature parity with the MCP tool interface, enabling:
1. Multi-user access via token authentication
2. External integrations via standard HTTP
3. MCP facade container for stdio → HTTP proxying
4. Consistent business logic via shared service layer
