# BPE-01 Plan — S13 FOB-PLAYBOOKS-VIEW_PLAYBOOK-09

## Specification

Read-only view of playbook at historical version snapshot; banner with release description.

## Backend Implementation

- URL `playbooks/<int:pk>/at-version/<decimal:version>/`
- Load `PlaybookVersion` by `(playbook, version_number)`, render snapshot JSON into template stubs.

## Testing

- `tests/integration/test_history_tab_render.py::test_view_historical_version`

## Checkpoint

```bash
pytest tests/integration/test_history_tab_render.py::test_view_historical_version -x
```
