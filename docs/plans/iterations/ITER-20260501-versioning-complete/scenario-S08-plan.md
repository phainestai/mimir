# BPE-01 Plan — S08 PIP-MANAGE-05 (contract test)

## Specification

Align `pips-manage.feature` behavior: Implement PIP → single minor bump, major unchanged, history links PIP, status stays Released.

## Backend Implementation

- Thin test that drives same service as S06 from a "manage" flow (view or service entrypoint).

## Testing

- `tests/integration/test_pip_implement.py::test_pip_manage_05_minor_bump_contract`

## Checkpoint

```bash
pytest tests/integration/test_pip_implement.py::test_pip_manage_05_minor_bump_contract -x
```
