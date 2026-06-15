# MCP E2E DB Isolation & Seed Cleanup Plan (v2)

**Branch:** `fix/mcp-e2e-db-isolation`

---

## Problem statement

Committed `mimir.db` contains ~30 test artifacts named `E2E PIP Playbook {hash}` and occasionally `E2E Playbook {hash}`. These are not intentional seed data — they accumulated because `tests/integration/test_mcp_e2e_all_tools.py` writes to the shared database and teardown is incomplete.

**Goals:**

1. Remove existing pollution from `mimir.db` (one-time).
2. Ensure future runs of this test **never modify** committed `mimir.db`.
3. Fix incomplete teardown so the test cleans up everything it creates (including the PIP playbook, even if released).

---

## How the test works today

One pytest module run = one `uid` (first 8 chars of a UUID) = **two playbooks**:

| Playbook | Created in | Used for | Teardown |
|----------|------------|----------|----------|
| `E2E Playbook {uid}` | `test_01` | Main 53-tool scenario (workflows, activities, …) | `test_55` → `mcp.call("delete_playbook", pb_id)` ✅ |
| `E2E PIP Playbook {uid}` | `test_51` | `create_pip_from_protocol` only | **Nothing** ❌ |

Each full run therefore adds **+1 row** to the database (the PIP playbook). Run 30 times → 30 PIP playbooks in git.

The lone `E2E Playbook cae89a90` is from a run that failed or stopped before `test_55`.

### Misleading comment in `test_51`

The docstring says released playbooks cannot be deleted via MCP. That is true for **MCP** (`delete_playbook` raises on `status == 'released'`).

It is **not** a reason to skip teardown:

- The test’s “release” step only updates the **name**, not `status` → PIP playbook stays **draft** in 29/30 cases anyway.
- Even when released, `PlaybookService.delete_playbook()` has **no status check** — tests can use that for cleanup.
- Teardown is janitor work, not an MCP product test.

The PIP playbook was left behind because **teardown was never written for `pip_pb_id`**, not because deletion is impossible.

---

## The two-database trap

This is critical for any teardown design:

| Process | Settings | Database |
|---------|----------|----------|
| Pytest test methods | `mimir.settings.test` | Postgres `mimir_test` |
| MCP subprocess | `mimir.settings` (dev) | SQLite `mimir.db` (or `MIMIR_DB_PATH`) |

All creates/deletes via `mcp.call(...)` happen in **`mimir.db`**.

Calling `PlaybookService.delete_playbook(pip_pb_id)` **inside a test method** hits **`mimir_test`** — the PIP row in `mimir.db` would remain.

**Rule:** any cleanup of MCP-created data must run in the **same subprocess DB context** as MCP (shared `MIMIR_DB_PATH` env), not via in-process Django ORM from pytest.

---

## Fix strategy (two layers)

```text
Layer 1 — Isolation (primary)
  Test provisions temp SQLite → MCP uses MIMIR_DB_PATH → never touch mimir.db

Layer 2 — Teardown (hygiene inside temp DB)
  Extend existing teardown block to delete pip_pb_id via service-layer subprocess
  (works for draft and released; no new test case)
```

Both layers together. Neither alone is ideal:

| Approach | Stops PIP leak | Protects committed mimir.db | Survives crash mid-test |
|----------|----------------|----------------------------|-------------------------|
| Teardown only (on mimir.db) | Yes, if teardown runs | No — still writes shared DB | No |
| Temp DB only (delete file) | Yes | Yes | Yes |
| **Temp DB + teardown** | Yes | Yes | Yes (file delete in fixture finalizer) |

---

## Part A — One-time seed cleanup

**Remove** from committed `mimir.db`:

- All playbooks where `name LIKE 'E2E%'`

**Keep:**

- FeatureFactory (id 3)
- UAT / Admin seed playbooks (237–241, etc.)

**Do not** remove `Test Playbook` (id 28) in this PR unless confirmed orphan — separate investigation.

```bash
.venv/bin/python manage.py shell -c "
from methodology.models import Playbook
n = Playbook.objects.filter(name__startswith='E2E').count()
print(f'Deleting {n} E2E playbooks...')
Playbook.objects.filter(name__startswith='E2E').delete()
assert not Playbook.objects.filter(name__startswith='E2E').exists()
print('OK')
"
```

Commit as: `chore(db): remove E2E test artifacts from seed database`

---

## Part B — Test isolation (temp SQLite)

### Shared env helper

Extract `_mcp_dev_env(project_root: Path, db_path: Path) -> dict` used by:

- `MCPServer.start()`
- `_provision_e2e_database()`
- `_delete_playbook_via_subprocess(playbook_id, env)`

```python
{
    "DJANGO_SETTINGS_MODULE": "mimir.settings",
    "PYTHONPATH": str(project_root),
    "MIMIR_MCP_MODE": "1",
    "MIMIR_DB_PATH": str(db_path),
    "PATH": os.environ.get("PATH", ""),
}
```

### Module fixture `e2e_isolated_db`

```
tmp_path / mimir_e2e.db
  → subprocess: migrate --noinput
  → subprocess: create_default_admin
  → yield db_path
  → fixture finalizer: unlink db_path (always, even on failure)
```

Use `tmp_path_factory` (module scope) so failed runs retain the file for debugging when pytest is run with `--tmp-path-retention`.

### `mcp` fixture

Depends on `e2e_isolated_db`. Passes `db_path` into `MCPServer`.

### Docstring update

Replace prerequisite “admin must exist in mimir.db” with: *provisions isolated temp SQLite; does not read or write committed `mimir.db`.*

---

## Part C — Teardown fix (extend existing block, no new test)

Keep `test_52`–`test_55` as-is for the **main sandbox** (MCP deletes exercise the tools under test).

After `test_55` (same teardown section, still part of the ordered scenario — either appended to `test_55` or a final step in the module `mcp` fixture **after** server stop):

**Delete PIP playbook via service subprocess** (not MCP):

```python
def _delete_playbook_via_subprocess(project_root: Path, db_path: Path, playbook_id: int) -> None:
    """Test cleanup only — bypasses MCP released-playbook restriction."""
    env = _mcp_dev_env(project_root, db_path)
    subprocess.run(
        [
            str(project_root / ".venv/bin/python"),
            str(project_root / "manage.py"),
            "shell", "-c",
            (
                "from methodology.services.playbook_service import PlaybookService; "
                f"PlaybookService.delete_playbook({playbook_id})"
            ),
        ],
        env=env,
        check=True,
        cwd=str(project_root),
    )
```

Call when `TestMCPAllTools.pip_pb_id` is set. Do **not** assert on MCP error for released — service delete always succeeds.

**Preferred placement:** module-scoped `mcp` fixture finalizer (after `server.stop()`), so PIP cleanup runs even if a late test fails before reaching an extended `test_55`. Pass `pip_pb_id` from class attr or a small module-level registry.

---

## What we are NOT doing

- **No `test_56`** — cleanup is fixture/teardown hygiene, not a separate MCP tool test.
- **No in-process `PlaybookService` from pytest** — wrong database.
- **No relying on MCP `delete_playbook` for PIP** — unnecessary; service layer is simpler and handles released.
- **No change to MCP product rules** — released playbooks stay undeletable via MCP; only test cleanup bypasses that.

---

## Out of scope (follow-up)

| Item | Notes |
|------|-------|
| `test_mcp_facade.py` | Still uses `mimir.db` via runserver; has its own cleanup |
| `test_mcp_server_acceptance.py` | Smoke only; minimal creates |
| Contributor docs in CLAUDE.md | Optional one-liner after fix lands |

---

## Implementation slices

| Step | Deliverable | Verify |
|------|-------------|--------|
| 1 | Revised plan + branch | — |
| 2 | `_mcp_dev_env`, `_provision_e2e_database`, `_delete_playbook_via_subprocess` | small helper test or manual |
| 3 | `e2e_isolated_db` + `MCPServer(db_path=…)` fixtures | — |
| 4 | PIP cleanup in `mcp` fixture finalizer | — |
| 5 | `pytest tests/integration/test_mcp_e2e_all_tools.py -v` × 2 | `git diff mimir.db` empty |
| 6 | Purge `E2E%` from `mimir.db`, commit seed | shell assert |
| 7 | Full integration smoke | `pytest tests/integration/test_mcp_playbook_tools.py -v` |

---

## Acceptance criteria

- [ ] Zero `E2E%` playbooks in committed `mimir.db`
- [ ] FeatureFactory + UAT seeds unchanged
- [ ] Two consecutive runs of `test_mcp_e2e_all_tools.py` leave `git diff mimir.db` empty
- [ ] PIP playbook deleted after each run (verify via temp DB query before file unlink, or zero rows if using subprocess shell)
- [ ] No new numbered test case for cleanup

---

## PR commits (suggested)

```
fix(tests): isolate MCP E2E all-tools on temp SQLite and fix teardown

- Provision module-scoped temp DB via MIMIR_DB_PATH
- Delete pip_pb_id in fixture finalizer via PlaybookService subprocess
- Shared _mcp_dev_env for MCP server and cleanup subprocesses

chore(db): remove E2E test artifacts from seed database

Deletes E2E* playbooks accumulated from prior test runs against mimir.db.
```

---

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_mcp_e2e_all_tools.py -v
git diff mimir.db   # must be empty after test runs (before chore(db) commit)
```
