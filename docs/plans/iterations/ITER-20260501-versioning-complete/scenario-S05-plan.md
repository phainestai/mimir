# BPE-01 Plan — S05 FOB-PLAYBOOKS-VERSIONING-21

## Specification

Released playbook at v1.3 (minor bumps after v1.0) → Release with description → v2.0.

## Backend Implementation

- Extend `release` to accept **released** playbooks transitioning to next major: if `status == released`, allow release action that only bumps major + appends history (no illegal draft constraint).

**Current code** `release()` only allows draft — **must change** so product rule matches: Released author can trigger Release for next major milestone.

Alternatively: playbook stays released, version bumps 1.3→2.0 in one transaction.

## Testing

- `tests/integration/test_playbook_release.py::test_re_release_bumps_next_major` — playbook at 1.3 released → release → 2.0

## Checkpoint

```bash
pytest tests/integration/test_playbook_release.py::test_re_release_bumps_next_major -x
```
