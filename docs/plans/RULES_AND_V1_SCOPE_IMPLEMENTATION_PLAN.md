# Rules (V1) & scope — implementation plan

## SAO reconciliation (brief)

**Aligned**

- Shared **services** + thin **MCP** wrappers in [`mcp_integration/tools.py`](/Users/denispetelin/GitHub/mimir/mcp_integration/tools.py).
- Draft vs released playbook: mutations blocked on released for playbook-scoped entities (same pattern as Skill/Activity).

**Updated for this delivery**

- **Rule** added as playbook-scoped entity with CRUDLF (UI + MCP), M2M on Activity.
- **PIP**: implementation remains stub/V2-facing; narratives stay in specs for V2 — no removal of `create_pip_from_protocol` without product decision.

**Released playbook policy**

- TBD (see plan). Current code keeps read-only guards.

## Traceability

| Area | Artifact |
|------|-----------|
| BDD Rules (workflows act) | `docs/features/act-3-workflows/workflows-rules-*.feature`, export in `workflows-export-import.feature` |
| BDD Activities | `docs/features/act-5-activities/*.feature` |
| BDD MCP | `docs/features/act-13-mcp/interact-with-rules-via-mcp.feature`, updates to activities + `mcp-integration.feature` |

## Scenario checklist

- [ ] Rule CRUDLF UI + global list + playbook-scoped URLs
- [ ] Activity view/edit/create: rules section + multiselect
- [ ] Workflow export writes `rules/*.mdc` sibling to workflows folder
- [ ] MCP: `create_rule`, `list_rules`, `get_rule`, `update_rule`, `delete_rule`; `get_activity` includes `rules`
