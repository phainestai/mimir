# BPE-01 Plan — S10 FOB-PLAYBOOKS-VERSIONING-25

## Specification

After admin revert to Draft at 1.2: edits bump minor (1.3, 1.4); next Release → 2.0.

## Backend Implementation

- Reuse signals for draft increments + S03/S05 release.

## Testing

- `tests/integration/test_admin_revert.py::test_post_revert_edits_then_release`

## Checkpoint

```bash
pytest tests/integration/test_admin_revert.py::test_post_revert_edits_then_release -x
```
