# Act-16 Content Browser — Post-Merge Remediation Plan

**BPE-08 Process Change Request** · Activity **#103** (FeatureFactory v13.3, Construction phase)  
**Trigger:** [PR #145](https://github.com/phainestai/mimir/pull/145) merged with known review debt; holistic re-review found bugs, stale tests, spec drift, and **IA guideline violations** beyond the inline PR comments.  
**Status:** **Awaiting Commander approval** — no further code changes until this plan is approved.

---

## Execution order (gates)

| Phase | What | Gate |
|-------|------|------|
| **A — Make CI honest** | E2E fixture speedup (A0), access-control parity, canonical URLs, login redirect, full E2E baseline | **Human approval required** — stop here; no Phase B/C until A checkpoint green |
| **B — Retire stale tests** | Delete/rewrite contradictory E2E; reconcile FOB-63 defaults | Only after Phase A checkpoint passes |
| **C — Spec + dead code** | Feature files, implementation notes, legacy JS wiring, unused context | Only after Phase B checkpoint passes |
| **D — IA alignment** | Bootstrap-first styling, design tokens, icons, tooltips, shared CSS | Only after Phase C / BPE-06 checkpoint passes |

**BPE-08 step 2 (this document):** present plan for review. **Step 3 (execute):** small increments, test-first, commit per step — **do not push** until Commander approves.

**Exit gate (Phases A–C):** retroactive **BPE-06 Definition of Done** (activity #101) — full content-browser integration + E2E batch green, specs match shipped UX.

**Exit gate (Phase D):** Content Browser chrome matches [`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md) Bootstrap-first rules; see [Phase D exit checklist](#d8--phase-d-exit-checklist).

**Process backlog (post-remediation PIPs — not in Phases A–D scope):** mandatory BPE-08 on mid-iteration UI removal, Dr. Dobbs on BPE-06, layout CDN trim / `_LAYOUT_CATALOG` collapse, optional `pytest-xdist` parallel e2e (deferred from A0 unless Commander opts in).

---

## Change summary

Act-16 shipped as **12 MIT iterations, 63 scenarios** with **narrow per-file checkpoints**. Scope changed repeatedly without BPE-08 cleanup:

| Removed / replaced | Replacement | Debt left behind |
|--------------------|-------------|------------------|
| FOB-36 seq toggle | FOB-51 (always show predecessor edges) | `test_content_browser_seq_toggle.py` skipped, not deleted |
| FOB-37 compound toggle | FOB-61 compound dropdown | `test_content_browser_compound_view.py` still asserts toggle |
| FOB-11/11b entity + phase filters | Removed from template | URL param tests + JS filter logic remain |
| FOB-19 ELK “Layered” default | FOB-63 custom-layout mode (klay + straight + workflow-activity) | `layout_position`, `routing_picker`, `node_size_toggle` assert old defaults/visibility |
| `/browser/graph/<pk>/` (iteration artifact) | `/browser/<pk>/` (`browser_urls.py`) | **20 of 29** E2E files still use stale path |
| Per-file MIT checkpoints only | Milestone-close full E2E batch assumed practical | ~274 e2e tests; function-scoped `live_server`, duplicated `_login`, `networkidle`, fixed `wait_for_timeout` — batch takes 15–45+ min serial |
| IA Bootstrap-first rules | Fast iteration on canvas chrome | Inline `style=`, page `<style>` + `!important`, Bootstrap Icons without CDN, duplicate embed CSS, JS-built dropdowns, hardcoded hex in Cytoscape styles |

### IA guideline gaps (PR #145 — Phase D scope)

Holistic review against [`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md) § *Bootstrap-First Approach*, § *Icon System*, § *Design Tokens*, and the pre-ship checklist (*Add tooltips to all action buttons*).

| IA rule | Shipped behavior | Remediation |
|---------|------------------|-------------|
| Font Awesome Pro for icons | Empty states use `bi bi-*` (Bootstrap Icons) but `base.html` does not load Bootstrap Icons | D2 — swap to `fa-solid fa-*` |
| Prefer Bootstrap utilities over custom CSS | 15+ inline `style=` attrs on `browser_graph.html`; compact controls use ad-hoc `font-size: 0.65rem; padding: 2px 6px` | D3 — extract to `design-system.css` classes |
| Extend via CSS variables, not `!important` overrides | Page `<style>` hides footer / zeroes main padding with `!important` | D1 — `body.mm-content-browser` pattern (like `body.mm-landing`) |
| Bootstrap tooltips on action buttons | Canvas controls use bare HTML `title=` only | D4 — `data-bs-toggle="tooltip"` + init in template or JS |
| Shared design-system CSS | Four `_embed.html` files duplicate identical markdown `<style>` blocks | D5 — single rule in `design-system.css` |
| Component composition | Layout/routing/compound pickers built in JS via `cssText` | D6 — restyle to match Bootstrap dropdown (or document exception) |
| Token naming (`--bs-*`, `--mimir-*`) | Cytoscape node/edge colors hardcoded as hex literals in JS | D7 — centralize palette map; read vars where feasible |
| PR planned `static/css/content-browser.css` | File never landed; styling scattered | D1/D3 — fold into `design-system.css` (do **not** add a second global CSS file unless Commander opts in) |

**Out of Phase D scope (acceptable exceptions):** Cytoscape canvas node/edge styling must remain in JS (`content-browser.js` stylesheet API). Phase D targets the **Django template chrome** (panels, buttons, empty states, embeds) and **token consistency** for colors shared between chrome and canvas.

### PR #145 inline review (addressed vs open)

| Finding | Status |
|---------|--------|
| Duplicate `_applyDefaultLayoutMode` in JS | **Draft fix** in working tree (uncommitted) — see [Uncommitted draft work](#uncommitted-draft-work-pending-approval) |
| Dead `_renderFilterToolbar` / `_renderPhaseFilter` | **Draft fix** in working tree |
| Duplicate `_buildEdgeStyle` / `_buildCompoundLabelStyleV2` | **Draft fix** in working tree |
| `_init` mid-file, 500+ lines after it | **Draft fix** in working tree |
| `.mcp.json`, SQLite WAL in PR | Resolved at merge |
| Trim 20+ layout algorithms / CDN bloat | **Deferred** — FOB-63 hides controls; deeper trim is product decision |

---

## Context map

| File | Role in remediation |
|------|---------------------|
| [`methodology/api/viewsets.py`](methodology/api/viewsets.py) | `PlaybookViewSet.get_queryset()`, `_accessible_playbook_ids()`, `graph` action — **P0 team access gap** |
| [`methodology/services/playbook_service.py`](methodology/services/playbook_service.py) | `get_accessible_playbook_ids()` — canonical access set (owned + public + team) |
| [`methodology/browser_views.py`](methodology/browser_views.py) | `_get_accessible_playbooks`, unused `accessible_playbooks` context, `_playbook_readable_or_404` duplicate |
| [`methodology/browser_urls.py`](methodology/browser_urls.py) | Canonical routes: `/browser/`, `/browser/<pk>/` only |
| [`static/js/content-browser.js`](static/js/content-browser.js) | Legacy compound toggle wiring, `_checkSessionExpiry` login URL, filter URL params, CDN-facing layout catalog |
| [`templates/browser/browser_graph.html`](templates/browser/browser_graph.html) | 13 Cytoscape CDN scripts; no `browser-compound-toggle` in template |
| [`tests/e2e/conftest.py`](tests/e2e/conftest.py) | Function-scoped `live_server`; no shared login/graph helpers — **A0 speedup target** |
| [`tests/e2e/pytest.ini`](tests/e2e/pytest.ini) | E2e-only config; add `@pytest.mark.slow` in A0 |
| [`mimir/settings/e2e.py`](mimir/settings/e2e.py) | Signed-cookie sessions (enables session-scoped live server) |
| [`tests/e2e/README.md`](tests/e2e/README.md) | Document fixture scopes + smoke vs full commands after A0 |
| [`tests/e2e/test_content_browser*.py`](tests/e2e/) | 29 files — 20 on stale URL, contradictory FOB-63 assertions, duplicated waits |
| [`tests/integration/test_content_browser_access.py`](tests/integration/test_content_browser_access.py) | Stale TDD docstring; `accessible_playbooks` context assertions |
| [`tests/integration/test_graph_api.py`](tests/integration/test_graph_api.py) | Missing team-playbook graph test; mislabeled FOB-13c section |
| [`tests/e2e/test_content_browser_detail_panel.py`](tests/e2e/test_content_browser_detail_panel.py) | Asserts wrong `/auth/login/` on embed expiry |
| [`docs/features/act-16-content-browser/*.feature`](docs/features/act-16-content-browser/) | Stale compound toggle, filter toolbar, bezier default |
| [`docs/features/act-16-content-browser/_implementation_notes.md`](docs/features/act-16-content-browser/_implementation_notes.md) | HTMX panel, SRI, filter toolbar — none match code |
| [`docs/plans/ACT_16_CONTENT_BROWSER_LESSONS_LEARNED.md`](docs/plans/ACT_16_CONTENT_BROWSER_LESSONS_LEARNED.md) | Documents correct `LOGIN_URL` — embed path still violates |
| [`static/css/design-system.css`](static/css/design-system.css) | Target for Content Browser layout tokens + shared embed markdown styles (Phase D) |
| [`templates/*/_embed.html`](templates/) | Duplicate inline `<style>` blocks — consolidate (Phase D5) |
| [`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md) | Source of truth for Bootstrap-first rules; add Content Browser layout note after D complete (optional D8) |

---

## Do not do

- Do **not** re-run full BPE-01→BPE-07 as a new feature — this is change-request remediation, not greenfield.
- Do **not** create another MIT milestone with per-file-only checkpoints — use **phase batch checkpoints** below.
- Do **not** add new layout algorithms or expand `_LAYOUT_CATALOG` during cleanup.
- Do **not** delete `test_content_browser_seq_toggle.py` or `test_content_browser_compound_view.py` without Commander sign-off per `do-check-before-deleting` (propose → approve → delete with commit tag `deleted def func_x` / file).
- Do **not** push commits until Commander approves push explicitly.
- Do **not** mock Django/ORM in integration tests — use real DB + factories for team-playbook access case.
- Do **not** add a Bootstrap Icons CDN to fix empty states — use Font Awesome per IA § Icon System.
- Do **not** refactor Cytoscape layout algorithm catalog during Phase D — visual chrome only.
- Do **not** change graph node shapes/colors in Phase D unless required for token centralization (D7).
- Do **not** run the full ~274-test e2e suite on every incremental step — use representative modules + `--durations`; full batch only at phase checkpoints.
- Do **not** switch e2e to async Playwright or re-enable the `pytest-playwright` plugin.
- Do **not** weaken test assertions to gain speed (fixture/wait strategy only).

---

## SAO.md sections that apply

- **§5 Test Strategy** — pytest; integration uses real objects; E2E uses Playwright + `mimir.settings.e2e` (signed-cookie sessions).
- **§ E2E Testing with Playwright** — sync API, manual fixtures, `live_server`; update after A0 fixture scope changes.
- **Access control** — `Playbook.can_view()` is authoritative for page; API list/graph must match.
- **UI patterns** — Django templates + fetch (not HTMX for detail panel); `data-testid` on interactive elements.
- **IA guidelines** — Bootstrap 5.3+ first; Font Awesome Pro; design tokens in `design-system.css`; Bootstrap tooltips on action buttons ([`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md)).

---

## Uncommitted draft work (pending approval)

A prior session applied **uncommitted** changes (not part of approved plan yet):

| File | Change |
|------|--------|
| `static/js/content-browser.js` | Removed duplicate `_applyDefaultLayoutMode`; dead filter toolbar functions; consolidated style helpers; moved `_init`/exports to file end (~2723→2494 lines) |
| `tests/e2e/test_content_browser_compound_labels.py` | Label alignment `left` → `center` |
| `tests/e2e/test_content_browser_custom_layout.py` | Module docstring: node-size hidden in default mode |

**Decision needed on approval:** keep as Phase C head-start, or revert and re-apply under formal checkpoints.

---

## Phase A — Make CI honest

**Goal:** Fix real bugs, make the e2e batch runnable in reasonable time, and establish a trustworthy test baseline. Failures after this phase = actionable backlog, not false negatives from wrong URLs.

**Incremental testing rule:** During A0–A3, checkpoint with representative modules only. Run the full `test_content_browser*.py` batch **once** at A4 (and record `--durations` before/after A0).

### A0 — E2E fixture speedup (prerequisite for honest CI)

**Problem:** ~274 e2e tests; function-scoped `live_server` costs ~1–6s setup per test; duplicated `_login()` + `wait_for_load_state('networkidle')` add ~1–3s per navigation; 80+ `wait_for_timeout` calls. Full content-browser batch is impractical for phase gates.

**Partial timing evidence (representative modules):**

| Module | Approx. behavior |
|--------|------------------|
| `test_auth_login.py` (4 tests) | ~12s total (~3s/test incl. setup) |
| `test_content_browser_graph.py` (16 tests) | ~6–14s/test call time; setup dominated by server + login |

**Target after A0:** ≥3× serial speedup on representative modules; full `test_content_browser*.py` batch ≤15 min serial (before optional xdist).

#### A0.1 — Baseline timings (before code changes)

```bash
.venv/bin/python -m pytest tests/e2e/test_auth_login.py -q --durations=10
.venv/bin/python -m pytest tests/e2e/test_content_browser_graph.py -q --durations=10
```

Record results in [A0 baseline timings](#a0-baseline-timings) below.

#### A0.2 — Shared helpers in `tests/e2e/conftest.py`

Add and use from all touched e2e files (migrate incrementally during A2/B2). Implemented in [`tests/e2e/e2e_helpers.py`](../../tests/e2e/e2e_helpers.py) (importable from e2e tests via `pythonpath = .` in `tests/e2e/pytest.ini`):

| Helper | Replaces |
|--------|----------|
| `login(page, live_server_url, username, password)` | ~30 duplicated `_login()` functions |
| `wait_for_cy_graph(page, timeout=10_000)` | Per-file `window.cy` waits |
| `open_content_browser(page, live_server_url, playbook_id)` | Repeated goto + graph wait |

**Wait strategy:** `domcontentloaded` + wait until login URL gone — **not** `networkidle`. Replace `wait_for_timeout` with `wait_for_function` / `expect(...)` except one documented animation settle where required.

#### A0.3 — Session-scoped `live_server` for e2e-only runs

Default **session** scope when running `pytest tests/e2e/` (signed-cookie sessions in `mimir.settings.e2e` avoid the SQLite session race that motivated function scope). Retain **function** scope via `E2E_LIVE_SERVER_SCOPE=function` when mixing suites.

#### A0.4 — Module-scoped auth reuse (optional — Commander Q9)

Playwright `storage_state`: one login per module for read-only content-browser tests. Keep function-scoped fresh login for auth/session-expiry tests (`test_auth_login.py`, `test_content_browser_detail_panel.py` session-expiry scenario).

#### A0.5 — A0 checkpoint

```bash
.venv/bin/python -m pytest tests/e2e/test_auth_login.py tests/e2e/test_content_browser_graph.py -q --durations=10
```

Compare to A0.1 baseline — setup times should drop sharply.

#### A0.6 — Commit

`perf(e2e): session live_server and shared login helpers`

#### A0 baseline timings

**Full-suite snapshot (2026-06-22, pre-A0 — background run on `fix/content-browser-js-cleanup`):**

| Metric | Value |
|--------|-------|
| Wall time | **1519s (~25 min)** |
| Passed | 83 |
| Failed | 41 |
| Skipped | 150 |

Failure clusters align with Phase A/B scope: layout picker/position (FOB-63 defaults), resource tree, URL/filter params, journey tests. Speed target post-A0: same inventory run ≤15 min serial.

**Per-module timings (fill during A0.1):**

| Module | Tests | Wall time | Slowest setup | Slowest call | Notes |
|--------|-------|-----------|---------------|--------------|-------|
| `test_auth_login.py` + `test_content_browser_graph.py` (combined) | 22 | **100.3s** | (per-test, not reported) | 16.2s | Pre-A0, function-scoped `live_server` + `networkidle` |
| `test_auth_login.py` + `test_content_browser_graph.py` (combined) | 22 | **58.8s** | 1.28s (session setup, once) | 10.7s | Post-A0, session `live_server` + `e2e_helpers` |

**Deferred (process backlog unless Commander opts in at Q10–Q11):** `pytest-xdist`, `@pytest.mark.slow` smoke subset for CI, SAO/README doc updates (fold doc updates into Phase C if deferred).

---

### A1 — Align API access with `get_accessible_playbook_ids()`

**Problem:** Team member opens `/browser/<pk>/` (200) but `GET /api/playbooks/<pk>/graph/` returns 404. Picker (`GET /api/playbooks/`) omits team playbooks.

**Change:**
1. Refactor `PlaybookViewSet.get_queryset()` and `_accessible_playbook_ids()` in [`methodology/api/viewsets.py`](methodology/api/viewsets.py) to delegate to `PlaybookService.get_accessible_playbook_ids(user)`.
2. Add integration test: team member → page 200 + graph API 200 (mirror pattern in `tests/unit/test_accessible_global_lists.py`).

**PIT contract violated:** `ITER-20260531-content-browser-access.yaml` S2 — *"Do NOT add new service methods — use `get_accessible_playbook_ids()`"*.

### A2 — Normalize E2E URLs to `/browser/<pk>/`

**Problem:** No `/browser/graph/<pk>/` route exists (`browser_urls.py`). **20 files** navigate there.

**Files to update** (replace `/browser/graph/` → `/browser/`):

`test_content_browser_custom_layout.py`, `compound_labels.py`, `compound_labels_v2.py`, `compound_view.py`, `compound_grouping_menu.py`, `controls_layout.py`, `flat_edges.py`, `font_rendering.py`, `fullscreen_layout.py`, `icons.py`, `node_overflow.py`, `node_size_reflow.py`, `node_size_toggle.py`, `node_styles.py`, `no_seq_toggle.py`, `routing_catalog.py`, `routing_complete.py`, `routing_picker.py`, `seq_toggle.py`, `treeview_navigation.py`

**Already correct (9 files):** `graph.py`, `url.py`, `search.py`, `structure_tree.py`, `resource_tree.py`, `layout_position.py`, `layout_picker.py`, `left_panel.py`, `detail_panel.py`

### A3 — Fix embed session-expiry login redirect

**Problem:** `_fetchGraph` uses `/auth/user/login/` ✓; `_checkSessionExpiry` uses `/auth/login/` ✗ ([lessons learned](docs/plans/ACT_16_CONTENT_BROWSER_LESSONS_LEARNED.md) §2).

**Change:**
1. [`static/js/content-browser.js`](static/js/content-browser.js) — unify `_checkSessionExpiry` redirect to `/auth/user/login/`.
2. [`tests/e2e/test_content_browser_detail_panel.py`](tests/e2e/test_content_browser_detail_panel.py) — update assertion from `/auth/login/` to `/auth/user/login/`.

### A4 — Phase A checkpoint

```bash
.venv/bin/python -m pytest \
  tests/integration/test_content_browser_access.py \
  tests/integration/test_graph_api.py \
  tests/unit/test_accessible_global_lists.py \
  -x -q

# Full E2E batch — first honest inventory after A0 speedup + A2 URL fixes (Playwright required)
.venv/bin/python -m pytest tests/e2e/test_content_browser*.py -q --durations=20 2>&1 | tee tests.log
```

**Approval checkpoint:** Commander reviews A checkpoint log (pass/fail inventory + duration summary vs A0 baseline). Explicit **"approved for Phase B"** before retiring tests.

---

## Phase B — Retire stale tests

**Goal:** One coherent test suite for shipped UX (FOB-61 compound dropdown, FOB-63 custom layout defaults, FOB-51 no seq toggle).

### B1 — Delete or archive obsolete suites

| File | Action | Rationale |
|------|--------|-----------|
| [`tests/e2e/test_content_browser_seq_toggle.py`](tests/e2e/test_content_browser_seq_toggle.py) | **Delete** (after approval) | Entire file `pytest.mark.skip`; FOB-36 removed; `no_seq_toggle.py` is replacement |
| [`tests/e2e/test_content_browser_compound_view.py`](tests/e2e/test_content_browser_compound_view.py) | **Delete or rewrite** | 17 tests assert removed `browser-compound-toggle`; contradicts `compound_grouping_menu.py` |

### B2 — Reconcile FOB-63 (custom layout mode)

**Canonical default behavior** (from JS `_DEFAULT_*` keys + `test_content_browser_custom_layout.py` intent):

- Custom layout checkbox **unchecked** on entry.
- Defaults: layout=`klay`, routing=`straight`, compound=`workflow-activity`.
- Layout, routing, compound, and node-size controls **hidden** until checkbox checked.

**Files needing setup or assertion updates:**

| File | Conflict | Fix |
|------|----------|-----|
| `test_content_browser_custom_layout.py` | `test_always_visible_buttons_present_in_default_mode` lists node-size as always visible | Remove node-size from always-visible list; align with `test_default_mode_hides_node_size_toggle` |
| `test_content_browser_routing_picker.py` | `test_default_routing_is_bezier` | Enable custom layout first, **or** assert `straight` as FOB-63 default |
| `test_content_browser_layout_position.py` | Layout btn visible, default "Layered" | Enable custom layout in fixture; default label should reflect klay in custom mode |
| `test_content_browser_compound_grouping_menu.py` | Compound btn visible without custom layout | Check custom-layout checkbox in `graph_page` fixture before compound tests |
| `test_content_browser_node_size_toggle.py` | Toggle visible on bare page load | Enable custom layout in fixture first |

### B3 — Update legacy JS interaction tests

Replace `_applyCompoundToggle()` / `browser-compound-toggle` clicks with FOB-61 path (`browser-compound-btn` dropdown → `_applyCompoundLevel`):

- `test_content_browser_compound_labels.py`
- `test_content_browser_flat_edges.py`

Consider merging `compound_labels.py` + `compound_labels_v2.py` after v1 stops using legacy toggle.

### B4 — Filter URL tests vs removed UI

[`tests/e2e/test_content_browser_url.py`](tests/e2e/test_content_browser_url.py) — decide with Commander:

| Option | Action |
|--------|--------|
| **A (recommended)** | Drop type/phase filter URL scenarios; keep search + layout/routing/compound params only |
| **B** | Keep URL param behavior as hidden/deep-link API; document in feature file as "URL-only, no toolbar" |

### B5 — Strengthen weak assertions

| File | Test | Fix |
|------|------|-----|
| `test_content_browser_no_seq_toggle.py` | `test_predecessor_edges_always_visible` | Assert `edge_count > 0` and dashed predecessor style present |
| `test_content_browser_flat_edges.py` | `test_contains_edges_hidden_in_compound_mode` | Assert compound parents exist and contains-edge display is `none` |

### B6 — E2E fixture discipline

Replace `pytest.skip('No released playbook available')` in 20 files with deterministic playbook factory (pattern from `test_content_browser_graph.py`).

Migrate remaining content-browser files to A0 conftest helpers (`login`, `wait_for_cy_graph`, `open_content_browser`); drop local `_login` / `networkidle` / unnecessary `wait_for_timeout` as each file is touched in B2–B3.

### B7 — Phase B checkpoint

```bash
.venv/bin/python -m pytest tests/e2e/test_content_browser*.py -x -q 2>&1 | tee -a tests.log
.venv/bin/python -m pytest tests/ -x -q --ignore=tests/e2e  # integration + unit, no regressions
```

**Result (2026-06-22, branch `fix/content-browser-js-cleanup`, uncommitted):**

| Suite | Result | Duration |
|-------|--------|----------|
| Content-browser E2E (`test_content_browser*.py`) | **232 passed**, 0 failed | ~6m 11s |
| Unit + integration (`--ignore=tests/e2e`) | **1363 passed**, 1 failed, 5 skipped | ~29s |

**E2E delta vs pre-Phase-B baseline:** ~35 failed → **0 failed**; ~195 pass → **232 pass** (deleted obsolete files + deterministic fixtures).

**Non-E2E note:** `test_concurrent_creates_get_unique_orders` fails consistently (SQLite thread-pool ordering — pre-existing, unrelated to content-browser). Group-sharing API gap from Phase A1 fixed in `get_accessible_playbook_ids()` (Django `shared_with_groups` M2M).

**JS product fixes (Phase B, uncommitted):** URL deep-link custom canvas mode (`_urlRequestsCustomCanvasMode`); `nodesize` in canonical URL; `window._pushPlaybookUrl` / `_parseUrlParams` exposed for E2E.

**Commander gate:** Phase B E2E checkpoint **green**. Await explicit **"approved for Phase C"** before spec/dead-code work.

---

## Phase C — Spec + dead code

**Goal:** Documentation and code match shipped behavior; no legacy wiring for removed controls.

### C1 — Feature files

Update [`docs/features/act-16-content-browser/`](docs/features/act-16-content-browser/):

| File | Updates |
|------|---------|
| `07-canvas-controls.feature` | Remove `browser-compound-toggle` scenarios; document FOB-61 dropdown + FOB-63 custom layout gate |
| `06-filters-and-search.feature` | Confirm REMOVED status; drop or relabel filter-toolbar scenarios |
| `01-access-and-nav.feature` | Ensure URLs use `/browser/<pk>/` only |

### C2 — Implementation notes

Rewrite stale sections in [`_implementation_notes.md`](docs/features/act-16-content-browser/_implementation_notes.md):

- Detail panel: fetch-based (not HTMX).
- No SRI on CDN scripts (or add SRI if we choose to).
- Remove `browser-filter-toolbar`, `browser-phase-filter` testids.
- Picker: `GET /api/playbooks/` (not server `accessible_playbooks` context).
- Correct `LOGIN_URL` for all JS redirect paths.

### C3 — Backend dead code

| Item | Action |
|------|--------|
| `accessible_playbooks` context | **Remove** from `browser_views.py` + fix integration tests **or** wire server-side picker (Commander choice — default: remove) |
| `_get_accessible_playbooks` | Replace with `get_accessible_playbook_ids()` + single queryset |
| `_playbook_readable_or_404` duplicate | Extract shared helper (PIT copied verbatim — consolidate now) |

### C4 — JS dead code

| Item | Action |
|------|--------|
| `_applyCompoundToggle` + `_init` wiring for `browser-compound-toggle` | Remove (no template button) |
| `_updateCompoundToggleBtn` if only serves legacy toggle | Remove after grep confirms |
| Stale `@throws Not yet implemented` on implemented functions | Clean up |
| Filter URL param logic (`types`/`phases` in `_parseUrlParams`) | Remove if Commander chooses Option A in B4 |

### C5 — Test docstrings

- `test_content_browser_access.py` — remove "NotImplementedError stubs" language.
- `test_graph_api.py` — fix FOB-13c section header; add session-expiry test or remove claim from module docstring.

### C6 — Phase C / BPE-06 exit checkpoint

```bash
.venv/bin/python -m pytest tests/e2e/test_content_browser*.py tests/integration/test_content_browser_access.py tests/integration/test_graph_api.py tests/integration/test_embed_views.py -x -q

node --check static/js/content-browser.js
```

Walk BPE-06 checklist (activity #101): spec ↔ UI ↔ tests ↔ URLs parity.

**Approval checkpoint:** Commander reviews C checkpoint log. Explicit **"approved for Phase D"** before IA styling work.

---

## Phase D — IA alignment

**Goal:** Bring Content Browser **template chrome** (panels, toolbar, empty states, embeds) in line with [`docs/ux/IA_guidelines.md`](../ux/IA_guidelines.md). Functional behavior unchanged; visual and maintainability debt reduced.

**Prerequisite:** Phases A–C complete and BPE-06 checklist green.

**Reference patterns already in repo:**
- Landing page full-viewport layout: `body.mm-landing` + rules in [`static/css/design-system.css`](static/css/design-system.css)
- Navbar tooltips: [`templates/base.html`](templates/base.html) Bootstrap tooltip init
- Embed icons: [`templates/activities/_embed.html`](templates/activities/_embed.html) uses `fa-solid fa-*` correctly

Execute in order (small vertical slices — one D-step per commit after its checkpoint):

### D1 — Full-screen page shell via design-system class

**Problem:** `browser_graph.html` uses inline `<style>` with `!important` to hide footer and zero main padding.

**Change:**
1. Add `{% block body_class %}mm-content-browser{% endblock %}` to [`templates/browser/browser_graph.html`](templates/browser/browser_graph.html).
2. Move layout rules to [`static/css/design-system.css`](static/css/design-system.css):

```css
/* Content Browser — full-viewport three-panel shell */
body.mm-content-browser main.container-fluid { margin-top: 0; padding: 0; overflow: hidden; }
body.mm-content-browser footer.footer { display: none; }
body.mm-content-browser #browser-root { height: calc(100vh - var(--mm-navbar-height, 64px)); overflow: hidden; }
```

3. Remove the page-level `<style>` block from `browser_graph.html` (keep `{% block extra_css %}` empty or drop block if unused).

**Test:** Existing E2E `test_content_browser_fullscreen_layout.py` must still pass.

### D2 — Font Awesome on empty states (remove Bootstrap Icons)

**Problem:** Empty / no-content states reference `bi bi-diagram-project` and `bi bi-inbox` but Bootstrap Icons is not loaded.

**Change:** Replace with Font Awesome equivalents per IA § Icon System:

| Current | Replacement |
|---------|-------------|
| `bi bi-diagram-project` | `fa-solid fa-diagram-project` (or `fa-sitemap` if unavailable in kit) |
| `bi bi-inbox` | `fa-solid fa-inbox` |

Use Bootstrap display utilities already on the element: `display-1 text-muted`.

**Test:** Manual smoke + optional E2E assertion that empty-state icon element has `fa-solid` class (extend `test_content_browser_graph.py` or `fullscreen_layout.py`).

### D3 — Extract inline layout styles to design-system CSS

**Problem:** Panel widths, toggle button geometry, canvas control sizing, and z-index values are inline on `browser_graph.html`.

**Change:** Add semantic classes under `/* Content Browser — panels & controls */` in `design-system.css`, e.g.:

| Class | Replaces |
|-------|----------|
| `.mm-browser-left-panel` | `#browser-left-panel` inline width/min-width/transition |
| `.mm-browser-detail-panel` | detail panel width 420px |
| `.mm-browser-panel-toggle` | collapse button size/position (JS may still set `left` dynamically) |
| `.mm-browser-canvas-controls` | control stack z-index |
| `.mm-browser-btn-compact` | `font-size: 0.65rem; padding: 2px 6px` on canvas buttons — prefer `btn btn-sm btn-outline-secondary` + compact override class |

Prefer Bootstrap utilities (`p-3`, `border-end`, `bg-light`, `overflow-hidden`, `flex-shrink-0`) where they replace one-off inline styles without a new class.

**Test:** Full content-browser E2E batch — no functional regressions; `test_content_browser_controls_layout.py` unchanged behavior.

### D4 — Bootstrap tooltips on canvas action buttons

**Problem:** IA checklist requires tooltips on action buttons; canvas controls only have native `title=` attributes.

**Change:**
1. Add `data-bs-toggle="tooltip"` and `data-bs-placement="left"` (controls are bottom-right) to buttons in `browser_graph.html`: layout, routing, compound, node-size, re-plot, zoom in/out/fit, panel toggle.
2. Initialize tooltips after DOM ready — either extend the pattern in `base.html` or add a small init block in `{% block extra_js %}` before `content-browser.js` loads.

**Test:** E2E optional — assert `data-bs-toggle="tooltip"` present on `browser-zoom-in`; manual verify tooltip renders on hover.

### D5 — Consolidate embed markdown styles

**Problem:** Identical `<style>` blocks in [`templates/activities/_embed.html`](templates/activities/_embed.html), [`templates/agents/_embed.html`](templates/agents/_embed.html), [`templates/skills/_embed.html`](templates/skills/_embed.html), [`templates/rules/_embed.html`](templates/rules/_embed.html).

**Change:**
1. Move rules to `design-system.css` under `.mm-embed .markdown-content` (or reuse existing `.markdown-content` if safe globally).
2. Remove per-template `<style>` blocks; add wrapper class on embed root if needed: `<div class="card mm-embed" …>`.

**Test:** `tests/integration/test_embed_views.py` — all embed endpoints still 200; visual spot-check one activity embed.

### D6 — JS dropdown menus: Bootstrap visual parity

**Problem:** `_toggleLayoutDropdown`, routing picker, and compound grouping menu in [`static/js/content-browser.js`](static/js/content-browser.js) inject custom panels via `cssText` (white box, gray header) that do not match Bootstrap dropdown styling elsewhere in Mimir.

**Change (pick one — Commander clarifies in item 6 below):**

| Option | Action |
|--------|--------|
| **A (recommended)** | Restyle injected markup to use Bootstrap dropdown classes (`dropdown-menu`, `dropdown-item`, `dropdown-header`) and Bootstrap CSS variables for colors — keep imperative JS positioning |
| **B** | Replace with Bootstrap dropdown components in `browser_graph.html` where possible; JS toggles visibility only |
| **C (defer)** | Document as intentional canvas exception in IA guidelines; no code change |

**Test:** E2E layout picker, routing picker, compound grouping menu suites must pass unchanged interaction paths.

### D7 — Centralize Cytoscape palette tokens

**Problem:** Node/edge colors in `_cytoscapeStyle()` / `_buildEnhancedNodeStyle()` use hardcoded hex (`#0d6efd`, `#198754`, …) duplicated from Bootstrap defaults.

**Change:**
1. Add a single JS object at top of `content-browser.js`:

```javascript
const _BOOTSTRAP_PALETTE = {
  primary: '#0d6efd', success: '#198754', warning: '#ffc107', /* … */
};
```

2. Optionally mirror values from CSS custom properties via `getComputedStyle(document.documentElement).getPropertyValue('--bs-primary')` with hex fallback (document in comment — Cytoscape may not accept `var()` strings).
3. Update `_implementation_notes.md` node colour table to reference token map, not raw hex in prose.

**Test:** `test_content_browser_node_styles.py` — pastel palette assertions still pass (values unchanged unless tokens drift).

### D8 — Phase D exit checklist

- [ ] No `!important` layout overrides in `browser_graph.html`
- [ ] No Bootstrap Icons (`bi-*`) in Content Browser templates
- [ ] Empty states render Font Awesome icons
- [ ] Canvas action buttons use Bootstrap tooltips
- [ ] Embed markdown styles defined once in `design-system.css`
- [ ] Inline `style=` count on `browser_graph.html` reduced to JS-dynamic cases only (e.g. toggle `left` position)
- [ ] Cytoscape colors sourced from `_BOOTSTRAP_PALETTE` (or CSS var reader), not scattered literals
- [ ] Full content-browser E2E batch green after D changes
- [ ] Optional: add § *Content Browser layout* to `IA_guidelines.md` documenting `body.mm-content-browser` and canvas JS exceptions

### D9 — Phase D checkpoint

```bash
.venv/bin/python -m pytest tests/e2e/test_content_browser*.py tests/integration/test_embed_views.py -x -q 2>&1 | tee -a tests.log

# Grep guardrails (expect zero matches after D2/D1):
rg 'class="bi ' templates/browser/
rg '!important' templates/browser/browser_graph.html
rg '<style>' templates/*/_embed.html
```

**Approval checkpoint:** Commander visual review of Content Browser in browser (empty state, loaded graph, detail panel, custom-layout controls). Sign off Phase D complete.

---

## Tests — drop / rewrite / add matrix

### Drop (after approval)

- `tests/e2e/test_content_browser_seq_toggle.py` (entire file)
- `tests/e2e/test_content_browser_compound_view.py` (entire file, unless rewritten)
- Filter URL scenarios in `test_content_browser_url.py` (if Option A)
- `test_content_browser_controls_layout.test_seq_toggle_absent_from_dom` (duplicate of `no_seq_toggle`)

### Rewrite

- 20 E2E files: URL path `/browser/graph/` → `/browser/`
- FOB-63 conflicting files (see B2)
- `compound_labels.py`, `flat_edges.py`: FOB-61 interaction path
- `test_content_browser_detail_panel.py`: login URL assertion

### Add

- Integration: team member → `/browser/<pk>/` + `GET .../graph/` 200
- Integration or E2E: embed session expiry → `/auth/user/login/`
- A0 shared E2E conftest helpers + session-scoped `live_server` (required)

### Phase D (IA alignment)

- E2E: empty-state icons use `fa-solid` (optional, D2)
- Grep/CI guard: no `bi-*` in `templates/browser/`; no `<style>` in `_embed.html` (D8)

---

## BPE-06 Definition of Done (exit criteria — Phases A–C)

- [ ] All content-browser E2E + integration tests pass in one batch
- [ ] Feature files in `docs/features/act-16-content-browser/` match shipped UI
- [ ] No `pytest.mark.skip` entire files for removed features
- [ ] No E2E file uses `/browser/graph/`
- [ ] API access matches `Playbook.can_view()` for team playbooks
- [ ] All JS auth redirects use `/auth/user/login/`
- [ ] No duplicate function definitions in `content-browser.js` (`node --check` + manual review)
- [ ] Stale skeleton / "Not yet implemented" comments removed from touched files
- [ ] `tests.log` records final green run
- [ ] A0 e2e speedup landed: shared conftest helpers, session-scoped `live_server`, no new duplicated `_login` in touched files
- [ ] Full `test_content_browser*.py` batch completes in ≤15 min serial (post-A0; record in `tests.log`)

---

## Phase D Definition of Done (IA alignment — optional after BPE-06)

- [ ] All items in [D8 exit checklist](#d8--phase-d-exit-checklist) checked
- [ ] Commander visual sign-off on Content Browser chrome
- [ ] `tests.log` records post–Phase D green E2E run

---

## Process notes (why this happened — for PIPs later)

| Gap | Evidence |
|-----|----------|
| Narrow MIT checkpoints | Per-scenario `pytest file::Class -x` never runs full `test_content_browser*.py`; full batch also impractical until A0 (slow fixtures) |
| BPE-08 skipped on UI removal | Seq toggle skipped not deleted; compound_view left active |
| Dr. Dobbs on BPE-02–05 only | BPE-06 has Agent: None; no holistic merge review |
| Skeleton-first + parallel JS edits | Duplicate `_applyDefaultLayoutMode`, `_init` mid-file |
| PIT prescribed copy-paste | `_playbook_readable_or_404` verbatim; `get_accessible_playbook_ids` partially ignored |
| No IA review gate at merge | Inline styles, wrong icon library, duplicate CSS — not caught by per-scenario E2E |

**PIP candidates (process backlog):** mandatory BPE-08 when removing UI; assign Dr. Dobbs to BPE-06; ban merged `@throws Not yet implemented`; **IA checklist on BPE-06** for any feature touching templates; **milestone-close full E2E batch** now in Phase A4 (enabled by A0).

---

## Clarifications for Commander (before execution)

1. **Uncommitted draft JS cleanup** — keep, revert, or fold into Phase C formally?
2. **`accessible_playbooks` context** — delete unused context (recommended) or implement server-side picker?
3. **Filter URL params** — drop tests + JS logic (Option A) or keep as deep-link-only API (Option B)?
4. **`test_content_browser_compound_view.py`** — delete outright or rewrite against FOB-61?
5. **Layout CDN trim** — in scope for this remediation or separate product ticket?
6. **Phase D6 dropdown restyle** — Option A (Bootstrap classes in JS markup), B (template dropdowns), or C (document exception)?
7. **Phase D scope** — include Phase D in this remediation, or ship A–C first and schedule D separately?
8. **`static/css/content-browser.css`** — fold into `design-system.css` (recommended) or create dedicated file?
9. **A0 session-scoped `live_server`** — default for `pytest tests/e2e/`, function scope only via `E2E_LIVE_SERVER_SCOPE=function`?
10. **A0 auth reuse** — module-scoped Playwright `storage_state` OK for read-only browser tests?
11. **`pytest-xdist`** — defer to process backlog (recommended) or include in A0?
12. **CI smoke subset** — register `@pytest.mark.slow` and run `-m "not slow"` on PRs, full batch at A4/milestone close?

---

## Approval

| Step | Owner | Status |
|------|-------|--------|
| BPE-08 plan presented | Agent | ✅ This document |
| Commander reviews plan | Commander | ✅ Approved Phase A0, A, B |
| Phase A0 execution (e2e speedup) | Agent | ✅ Done (session server + helpers; graph migrated) |
| Phase A1–A4 execution | Agent | ✅ A1–A3 committed; A4 superseded by B7 green batch |
| Phase B execution | Agent | ✅ Done (uncommitted); B7 E2E **232/232 green** |
| Phase C execution | Agent | Blocked — await **"approved for Phase C"** |
| BPE-06 sign-off (A–C) | Commander | Blocked |
| Phase D execution (IA) | Agent | Blocked |
| Phase D sign-off | Commander | Blocked |

**To approve:** reply with answers to clarifications above + explicit **"approved"** (optionally per-phase: e.g. "approved Phase A only" or "approved A–C, defer D").
