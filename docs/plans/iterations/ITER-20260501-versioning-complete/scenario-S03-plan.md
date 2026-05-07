# BPE-01 Plan — S03 FOB-PLAYBOOKS-VERSIONING-07

## Specification

Release requires non-empty release description; increments **major only**: `next_major = Decimal(self.version).to_integral_value(rounding=ROUND_FLOOR) // 1` logic: use `current = Decimal(str(self.version)); major = current.to_integral_value(rounding=ROUND_DOWN)` then for draft 0.x releasing, spec says v0.9 → v1.0: i.e. **ceiling toward next integer major line** per product rule: "Release bumps major" — implement as `new_version = (current.quantize(Decimal('1'), rounding=ROUND_FLOOR) + Decimal('1'))` only when current has fractional part? 

**Clarify per feature:** First release 0.9 → 1.0 = `floor(0.9)+1` = 1? floor(0.9)=0 → +1 = 1.0 ✓. Released at 1.3 → next release 2.0 = `floor(1.3)+1 = 2` ✓.

Formula: `major_unit = Decimal(int(current))` is wrong for 0.9.

Use: `whole = current.to_integral_value(rounding=ROUND_DOWN)` — for 0.9 whole=0 → next = whole + 1 = 1.0. For 1.3 whole=1 → next = 2.0. For 2.0 released, next = 3.0 (`whole + 1`).

Implementation: `whole = int(current)  # trunc toward zero for positive` matches `to_integral_value ROUND_DOWN` for non-negative.

Actually 0.9 int()=0 → +1 = 1.0 ✓. 1.3 int()=1 → +1 = 2.0 ✓.

Persist `PlaybookVersion` with snapshot, `is_major=True`, `source='release'`.

## Architecture (SAO.md)

- **§Hybrid MCP Access**: align `PlaybookService` if release is invoked from views.

## Codebase Context Map

| File | Lines | Intent |
|------|-------|--------|
| [methodology/models/playbook.py](../../../methodology/models/playbook.py) | 129–141 | `release(self, description: str, user)` |
| [methodology/services/playbook_service.py](../../../methodology/services/playbook_service.py) | — | Add `release_playbook(playbook, description, user)` delegating to model + version row |
| [templates/playbooks/detail.html](../../../templates/playbooks/detail.html) | header actions | Release modal + `data-testid` |
| [methodology/playbook_views.py](../../../methodology/playbook_views.py) | — | Wire POST |

## Do Not Do

- Do NOT hardcode `1.0`.
- Do NOT allow release without `Workflow` if VERSIONING-18 still applies.

## Backend Implementation

1. `Playbook.release(description, user)` validation: `description.strip()` non-empty → else `ValidationError`.
2. Validate at least one workflow (existing rule from VERSIONING-18).
3. Compute next major as `Decimal(int(current_version) + 1)` for positive versions (see formula above).
4. `transaction.atomic`: update playbook, create `PlaybookVersion` snapshot (reuse existing snapshot builder if any).

## Frontend Implementation

1. Bootstrap modal: field `release_description`, confirm button.
2. `data-testid="release-modal"`, `release-description-input`, `release-confirm`.

## Testing

- `tests/integration/test_playbook_release.py::test_release_creates_major_version_with_description`
- Fixture: draft playbook 0.9 with one workflow

## Commit Strategy

1. `feat(methodology): playbook release with description and next major`

## Rule References

- `do-semantic-versioning-on-ui-elements.mdc`, `tooltips.mdc`

## Checkpoint

```bash
pytest tests/integration/test_playbook_release.py::test_release_creates_major_version_with_description -x
```
