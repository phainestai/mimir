# BPE-01 Plan — S01 FOB-PLAYBOOKS-VERSIONING-26

## Specification

PlaybookVersion stores semantic X.Y versions (`DecimalField`), `description`, `is_major`, `source` (author | release | pip | admin), optional FK to PIP proposal record, retains `snapshot_data`, aligns `change_summary` with description.

## Architecture (SAO.md)

- **§Shared Services**: Playbook versioning is authoritative in models + services consumed by UI and MCP.
- **§MCP Access Rules**: Released playbooks read-only via direct edit; versioning rows are audit trail.
- History persistence must remain JSON-serializable snapshots.

## Codebase Context Map

| File | Lines | Intent |
|------|-------|--------|
| [methodology/models/playbook_version.py](../../../methodology/models/playbook_version.py) | 14–31 | Extend model fields; preserve `UniqueConstraint(playbook, version_number)` |
| [methodology/admin.py](../../../methodology/admin.py) | 16–19 | Extend `PlaybookVersionAdmin.list_display` for new columns |
| [methodology/services/playbook_service.py](../../../methodology/services/playbook_service.py) | 69–76 | Replace `version_number=1` int with `Decimal('1.0')` when creating initial row (coordinate with S02) |

## Do Not Do

- Do NOT introduce a repository layer between views and ORM for this scenario.
- Do NOT change `Playbook.version` semantics here (S03).
- Do NOT merge `PlaybookVersion` into `Playbook`; keep normalized history table.

## Backend Implementation

1. Add `VersionSource` TextChoices or CharField with choices on `PlaybookVersion`.
2. Replace `version_number`: `IntegerField` → `DecimalField(max_digits=5, decimal_places=1)`.
3. Add fields: `description` TextField(blank=True), `is_major` BooleanField(default=False), `source` CharField(max_length=20), `pip` FK → **placeholder**: if no `Pip` model exists, add minimal `methodology/models/pip.py` stub with `Playbook` FK + title/status for FK integrity, or use nullable `pip_external_id` until Pip lands — decision in impl: prefer adding minimal `PIP` model to satisfy FK (document in commit).
4. Update `ordering` if needed (`-version_number` remains valid for Decimal).
5. Update `__str__` for X.Y display.
6. Blank migration shell only in S01 if split; combined with S02 migration in practice — **coordinate**: S01 edits model; one migration file after S01+S02 design (see S02).

**Note:** Prefer single migration after S01 schema + S02 data migration in adjacent stories, or S01 adds schema fields with defaults, S02 alters type + backfill.

## Frontend Implementation

None (model-only). Admin list only.

## Testing (pytest, no mocks)

- `tests/unit/test_playbook_version_model.py`
  - `test_version_number_accepts_decimal_xy` — creates row with 1.2
  - `test_unique_constraint_playbook_version`
  - `test_source_choices_and_defaults`
  - `test_pip_fk_nullable`

## Commit Strategy

1. `feat(methodology): playbook version X.Y schema fields` — model + migration
2. `test(methodology): playbook version model assertions`

## Rule References

- `.cursor/rules/do-skeletons-first.mdc`, `do-test-first.mdc`, `do-import-on-module-level.mdc`, `do-write-concise-methods.mdc`, `keep-docstrings-consistent.mdc`

## Checkpoint

```bash
pytest tests/unit/test_playbook_version_model.py -x
```
