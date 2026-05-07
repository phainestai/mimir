# BPE-01 Plan — S04 FOB-PLAYBOOKS-VERSIONING-20

## Specification

Release blocked when description empty — server-side `ValidationError` + modal stays invalid (HTML5 optional + server round-trip).

## Codebase Context Map

| File | Intent |
|------|--------|
| [methodology/models/playbook.py](methodology/models/playbook.py) / service | reuse `release` validation branch |
| [templates/playbooks/detail.html](templates/playbooks/detail.html) | display field error |

## Backend Implementation

- `release_playbook`: `if not description or not description.strip(): raise ValidationError(...)`

## Frontend Implementation

- optional `required` on textarea + server error alert

## Testing

- `tests/integration/test_playbook_release.py::test_release_without_description_blocked`

## Commit Strategy

Same commit as S03 acceptable if simultaneous; separate `test(methodology): ...` ok.

## Checkpoint

```bash
pytest tests/integration/test_playbook_release.py::test_release_without_description_blocked -x
```
