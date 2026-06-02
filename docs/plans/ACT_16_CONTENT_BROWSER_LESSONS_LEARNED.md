# Act-16 Content Browser — Lessons Learned

**Iteration:** ITER-20260601g (Milestone #8)
**Closed:** 2025-06-01
**Scenarios:** S33 (deterministic node order), S34 (layout picker dropdown + full layout catalog)
**Branch:** `iteration/20260531-content-browser-access`
**Release:** v0.0.48
**PR:** #27

---

## 1. In-memory SQLite + pytest-django LiveServer connection race

### Problem
E2E tests passed individually but failed intermittently (401 Unauthorized) when run as a full suite.
Different tests failed each run — a classic non-deterministic ordering bug.

### Root cause
`pytest-django`'s `LiveServer.__init__` calls `connections.all()`, finds the in-memory SQLite
connection, and passes it to the WSGI server thread via `connections_override` +
`conn.inc_thread_sharing()`. Both the test thread and the WSGI thread now **share a single
connection object**.

`SESSION_SAVE_EVERY_REQUEST = True` (base.py) means every authenticated request writes a session
row. With a shared connection and concurrent threads, reads and writes on `django_session` race
→ session not found → 401.

### Fix
`mimir/settings/e2e.py` sets:
```python
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
```
This eliminates all `django_session` table access. Session data is signed and stored in the
cookie; the only DB access needed is a user PK lookup, which is always committed.

### Takeaway
**Never use database-backed sessions in E2E tests that use `LiveServer` with SQLite.**
The fix is general: create a dedicated `settings/e2e.py` that inherits from `dev.py` and
switches to signed-cookie sessions. Reference it from `tests/e2e/pytest.ini` via
`DJANGO_SETTINGS_MODULE = mimir.settings.e2e`.

---

## 2. Wrong login-redirect URL in JavaScript API client

### Problem
`_fetchGraph` in `content-browser.js` redirected on 401 to `/auth/login/` which returned 404.

### Root cause
The correct `LOGIN_URL` (set in `mimir/settings/base.py` line 165) is `/auth/user/login/`.
The JS was using a hardcoded guess.

### Fix
Update JS redirect check to use the correct URL, and add a 3-retry backoff (600 ms × retryCount)
so transient session issues don't immediately redirect the user.

### Takeaway
Keep `LOGIN_URL` in one place (settings). When JS needs to detect auth redirects, compare
`response.url` against the known login path — or use `response.redirected` combined with a
path check. Add a comment citing the settings constant.

---

## 3. `gh` CLI hangs on long heredoc bodies

### Problem
`gh issue comment --body-file -` and heredoc variants hang indefinitely when the body is large
(> ~2 KB in some terminal configurations).

### Fix
Use `gh api -X POST /repos/strek/mimir/issues/N/comments -f body="..."` directly.
`gh api` does not have this hang issue.

### Takeaway
Prefer `gh api` over higher-level `gh` subcommands for any operation with large string payloads
or when piping is involved.

---

## 4. Cytoscape layout CDN scripts must be loaded before JS initialization

### Problem
Layout algorithms (Cola, Klay, CiSE, etc.) are plugins that must register themselves on the
`cytoscape` global before the first `cytoscape({...})` call. Loading them after instantiation
causes "Layout `cola` not found" errors.

### Fix
All layout CDN `<script>` tags are placed in `<head>` (before DOMContentLoaded), not at the
bottom of `<body>`.

### Takeaway
Cytoscape layout plugins are registered by side-effect on import. Always load them before any
page script that might call `cytoscape({layout: {name: 'cola'}})`.

---

## 5. Legacy layout key mapping for URL backward-compatibility

### Problem
When S34 expanded the layout picker from 2 options to 20, existing bookmarked URLs with old
layout keys (e.g., `?layout=elk-mrtree`) would silently fall back to the default.

### Fix
`_LAYOUT_CATALOG` includes a `legacyKeys` array per entry. `_applyLayout` checks
`legacyKeys.includes(urlParam)` when no direct match is found, so old URLs still resolve.

### Takeaway
When changing URL param vocabulary, always add a legacy-key mapping rather than breaking
existing links. Bookmarked URLs are part of the UX contract.

---

## EST-08 Sprint Rebaseline

| Scenario | Estimated | Actual | Notes |
|----------|-----------|--------|-------|
| S33 deterministic order | 2h | ~1h | Straightforward sort insertion |
| S34 layout picker | 4h | ~6h | E2E intermittent 401 debugging added ~2h |
| E2E 401 root-cause investigation | — | ~2h | Unplanned; now covered by e2e.py pattern |
| **Iteration total** | **6h** | **~9h** | 1.5× overrun; root cause: novel infra bug |

**Velocity note:** The intermittent-401 investigation was a one-time infrastructure discovery.
Now that `mimir/settings/e2e.py` exists as a pattern, future E2E sessions should not
encounter this class of failure. Estimate future E2E-heavy scenarios at the original rate.
