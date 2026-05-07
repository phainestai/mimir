# BPE-01 Plan — S14 FOB-PLAYBOOKS-VIEW_PLAYBOOK-10

## Specification

Compare selected historical version vs current (split-pane); green/red/yellow diff semantics — start with JSON field-level diff of snapshot_data.

## Backend Implementation

- `methodology/services/version_diff_service.py` — `diff_snapshots(old, new) -> structured deltas`

## Testing

- `tests/integration/test_history_tab_render.py::test_compare_versions_split_pane`

## Checkpoint

```bash
pytest tests/integration/test_history_tab_render.py::test_compare_versions_split_pane -x
```
