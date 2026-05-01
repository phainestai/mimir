# BPE-01 Plan — S11 FOB-PLAYBOOKS-VERSIONING-12 (data layer)

## Specification

Expose playbook version history for UI: reverse-chronological, fields: version, kind (major/minor), status-at-time optional, description, source, pip link slug/id.

## Codebase Context Map

| File | Intent |
|------|--------|
| New `methodology/services/playbook_history_service.py` | `list_versions(playbook) -> list[dict]` |
| [methodology/playbook_views.py](methodology/playbook_views.py) | context processor or HTMX partial endpoint |

## Frontend

- Minimal: view returns JSON-like context for template (no full UI yet — S12).

## Testing

- `tests/integration/test_playbook_history.py::test_history_listing_endpoint` — Django client GET playbook detail fragment or `/playbooks/<id>/history-rows/`

## Checkpoint

```bash
pytest tests/integration/test_playbook_history.py::test_history_listing_endpoint -x
```
