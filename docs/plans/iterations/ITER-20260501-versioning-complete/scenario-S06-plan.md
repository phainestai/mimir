# BPE-01 Plan — S06 FOB-PLAYBOOKS-VERSIONING-22

## Specification

PIP approved/implement applies N entity edits transactionally → **exactly one** minor bump (+0.1 on current `Playbook.version` if Released), one `PlaybookVersion` row with aggregated description, `is_major=False`, `source='pip'`, FK to PIP record.

## Architecture

- Aggregate all mutations inside single `@transaction.atomic` block; defer signal-driven increments OR disable signals during batch and call `increment_version_minor_released(playbook)` once.

## Codebase Context Map

| File | Intent |
|------|--------|
| [methodology/signals.py](methodology/signals.py) | prevent N×0.1 from N saves — use `transaction.on_commit` or threading.local flag `SUPPRESS_PLAYBOOK_VERSION_SIGNAL` |
| New `methodology/services/pip_apply_service.py` | `apply_approved_pip(pip, user)` |

## Do Not Do

- Do NOT call `increment_version()` per activity save for PIP batch.

## Backend Implementation

1. Introduce context manager `suppress_playbook_version_signals`.
2. Implement PIP apply stub that performs N ORM operations then single version bump + history row.

## Testing

- `tests/integration/test_pip_implement.py::test_pip_with_n_changes_produces_single_minor_bump`

## Checkpoint

```bash
pytest tests/integration/test_pip_implement.py::test_pip_with_n_changes_produces_single_minor_bump -x
```

## Note

If `Pip` model missing, add minimal model + migration in this scenario or earlier.
