# BPE-01 Plan — S09 FOB-PLAYBOOKS-VERSIONING-24

## Specification

Admin action: Revert Released → Draft, keep `Playbook.version` numeric, append `PlaybookVersion` admin event (or history row) with `source='admin'`, description per feature.

## Codebase Context Map

| File | Intent |
|------|--------|
| [methodology/admin.py](methodology/admin.py) | `admin.action` on `Playbook` |
| [methodology/services/playbook_service.py](methodology/services/playbook_service.py) | `revert_to_draft(playbook, admin_user)` |

## Testing

- `tests/integration/test_admin_revert.py::test_revert_keeps_version_changes_status`

## Checkpoint

```bash
pytest tests/integration/test_admin_revert.py::test_revert_keeps_version_changes_status -x
```
