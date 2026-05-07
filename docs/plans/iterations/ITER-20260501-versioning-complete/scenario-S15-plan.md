# BPE-01 Plan — S15 FOB-PLAYBOOKS-VIEW_PLAYBOOK-11

## Specification

PIP-sourced rows show PIP badge and link to PIP detail (URL pattern TBD when PIP UI exists).

## Backend Implementation

- Extend `_history_row.html` conditional on `entry.source == 'pip'`

## Testing

- `tests/integration/test_history_tab_render.py::test_pip_sourced_rows_link_to_pip`

## Checkpoint

```bash
pytest tests/integration/test_history_tab_render.py::test_pip_sourced_rows_link_to_pip -x
```
