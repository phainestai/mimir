# BPE-01 Plan — S02 FOB-PLAYBOOKS-VERSIONING-27

## Specification

Data migration: existing `PlaybookVersion.version_number` integers 1,2,3 → 1.0, 2.0, 3.0; backfill `is_major=True`, `source='release'`, `description` from `change_summary`; idempotent-safe.

## Architecture (SAO.md)

- Preserve audit trail integrity; no dropped rows.
- Migrations run on SQLite (FOB).

## Codebase Context Map

| File | Lines | Intent |
|------|-------|--------|
| [methodology/migrations/](../../../methodology/migrations/) | newest +1 | Add `RunPython` forwards/backwards or non-destructive noop reverse |
| [methodology/models/playbook_version.py](../../../methodology/models/playbook_version.py) | — | Must match S01 final field set before this migration runs |

## Do Not Do

- Do NOT reset sequence or delete `PlaybookVersion` rows.
- Do NOT assume PostgreSQL-only SQL.

## Backend Implementation

1. After S01 migration applying new columns + type change:
   - `RunPython` to cast int → Decimal string in Python (`Decimal(val)`).
   - Set `description = change_summary` if empty.
   - Set `is_major`, `source` defaults for legacy rows.

2. If using Django multi-step: `AlterField` + `RunPython` order per Django docs.

3. Add integration test creating legacy-like rows via raw SQL or fixtures then `migrate`.

## Frontend Implementation

None.

## Testing

- `tests/integration/test_playbook_version_migration.py`
  - `test_backfill_decimal_versions_from_integers`
  - `test_no_rows_deleted_after_migration`

## Commit Strategy

1. `feat(methodology): data migration playbook version X.Y backfill`

## Rule References

- `do-update-tests-after-bugfixing.mdc`, `do-not-mock-in-integration-tests.mdc`, `pytest.mdc`

## Checkpoint

```bash
pytest tests/integration/test_playbook_version_migration.py -x
```
