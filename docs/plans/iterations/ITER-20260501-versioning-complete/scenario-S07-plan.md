# BPE-01 Plan — S07 FOB-PLAYBOOKS-VERSIONING-23

## Specification

Three sequential PIP applies → v1.0 → v1.1 → v1.2 → v1.3.

## Backend Implementation

- Reuse S06 service; integration test with three separate `apply_approved_pip` calls.

## Testing

- `tests/integration/test_pip_implement.py::test_sequential_pips_increment_minor`

## Checkpoint

```bash
pytest tests/integration/test_pip_implement.py::test_sequential_pips_increment_minor -x
```
