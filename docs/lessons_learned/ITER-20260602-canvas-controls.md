# Lessons Learned — ITER-20260602 Canvas Controls

**Milestone:** 9  
**Date:** 2026-06-02  
**Goal:** Content Browser canvas controls (S35/FOB-35, S36/FOB-36, S37/FOB-37, S38/FOB-38)  
**Velocity ratio:** 1.0 (no scope drift)  
**Dominant drift:** sqlite_postgresql_mismatch

## What happened

All 4 scenarios completed cleanly. The main environment issue was that `mimir.settings.test`
and `mimir.settings.e2e` were configured for PostgreSQL, which is not available in the local
dev environment. Switching to SQLite unblocked all test runs.

One pre-existing unit test (`test_concurrent_creates_get_unique_orders`) consistently fails
under SQLite due to table-locking — this test was written for PostgreSQL row-level locking
and is unrelated to canvas controls work.

## Technical decisions

### S35 — Edge routing picker
- Routing is style-only: `cy.edges().style({'curve-style': cyValue})` — no layout re-run.
  This is the key difference from the layout picker (which triggers `_runLayout()`).
- 6 routing options in `_ROUTING_CATALOG` covering all Cytoscape `curve-style` values.
- Mirrors `_toggleLayoutDropdown` pattern exactly (fixed-position dropdown, Esc/outside-click).

### S36 — Sequence edges toggle
- `_filterSeqEdges()` is called inside `_buildFilteredElements()` — this means the filter
  is always applied during any rebuild (entity-type filter, compound toggle, etc.).
- `?seq=0` default ON convention is clean and avoids polluting most URLs.

### S37 — Workflow compound view
- `_buildCompoundElements()` assigns `parent` data fields to activity/resource nodes.
- `contains` edges are omitted in compound mode (they'd create visual redundancy inside boxes).
- Resource nodes inherit workflow parent via activity→workflow map.
- Compound stylesheet uses `:parent` selector — Cytoscape automatically applies this to
  any node that has child nodes.
- Initial load respects `?compound=1` URL param via `_parseCompoundParam()` in `_parseUrlParams()`.

### S38 — Enhanced node visual styling
- `_cytoscapeStyleEnhanced()` + `_buildEnhancedNodeStyle(type)` pattern allows test access
  to individual node style computations without needing to query live cy elements.
- `window._buildEnhancedNodeStyle` exposed automatically as a top-level function declaration.

## Module state exposure for E2E tests
`let` declarations at top-level of non-module scripts are NOT automatic `window` properties.
Used `Object.defineProperty(window, '_seqEdgesOn', { get: () => _seqEdgesOn })` pattern to
expose module state for Playwright assertions. Top-level `function` declarations ARE hoisted
to `window` automatically.

## PIP candidates
1. Install Playwright in CI so E2E tests actually execute (all 44 tests currently skip).
2. Mark `test_concurrent_creates_get_unique_orders` as PostgreSQL-only with `@pytest.mark.skipif`.
