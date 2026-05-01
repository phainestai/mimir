# BPE-01 Plan — S12 FOB-PLAYBOOKS-VIEW_PLAYBOOK-08

## Specification

Replace History tab placeholder with timeline listing; major rows visually distinct from minor (`data-testid="history-row-major"` / `history-row-minor`).

## Codebase Context Map

| File | Lines | Intent |
|------|-------|--------|
| [templates/playbooks/detail.html](templates/playbooks/detail.html) | 465–467 | Replace placeholder |
| New `templates/playbooks/_history_row.html` | — | Partial |

## Testing

- `tests/integration/test_history_tab_render.py::test_major_minor_visual_distinction`

## Checkpoint

```bash
pytest tests/integration/test_history_tab_render.py::test_major_minor_visual_distinction -x
```
