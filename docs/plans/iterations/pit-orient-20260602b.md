## Orient Summary — 2026-06-02 (iteration 2 of day)

### Input Scope
Goal: Fix canvas control bugs and complete node visual overhaul
Scenarios: #43, #44, #45, #46, #47, #48

| Issue | Title |
|-------|-------|
| #43 | FOB-35 bug: add unbundled-bezier to edge routing catalog |
| #44 | FOB-36+37 bug: sequence toggle broken when compound view is active |
| #45 | FOB-37 bug: workflow label not visible in compound mode |
| #46 | FOB-37 bug: compound layout does not reflow activity nodes inside boxes |
| #47 | FOB-38 enhancement: node visual overhaul — icons, uniform shape, pastel palette, black edges |
| #48 | FOB-39 feature: node size mode toggle — fixed-size vs auto-width |

### Velocity Trend
Last 2 ratios: 1.0, 1.0 — stable (only 2 data points; first iteration had no log)

### Dominant Drift
sqlite_postgresql_mismatch (1/2 iterations) — resolved in prior iteration by switching tests to SQLite

### Footprint Accuracy
met_checkpoints — 100% (both iterations)

### Scope Validation
- #43 small (1 array entry in JS) — no risk
- #44 medium (logic branching in _applySeqToggle, _applyTypeRebuild, _buildCompoundElements) — touches content-browser.js in same area as #45, #46 → CONFLICT GROUP
- #45 small (CSS-only in _cytoscapeCompoundStyle) — touches same JS file but different function; low conflict risk
- #46 medium (ELK layout options, compound node data) — touches _buildCompoundElements + layout options; shares file with #44 → CONFLICT GROUP
- #47 large (full _cytoscapeStyleEnhanced rewrite) — touches content-browser.js stylesheet functions extensively; independent of #44/#45/#46 logic branches but shares the file
- #48 medium (new toggle + stylesheet mode) — touches _cytoscapeStyleEnhanced (same as #47) → CONFLICT with #47

Scope risk assessment:
- #43 can run in parallel with all others (isolated array entry)
- #44, #45, #46 share compound view logic in content-browser.js → serialize
- #47, #48 share stylesheet functions in content-browser.js → serialize; #48 depends on #47 (new sizing mode extends the style system #47 creates)
- velocity_ratio 1.0 stable — 6 scenarios is ambitious but all are JS-only (no backend), reducing risk

### Watch For
- content-browser.js is a single large file (~2000 lines) — all 6 scenarios touch it; surgical edits and careful conflict avoidance required
- ELK compound layout configuration (#46) needs runtime verification — no automated Playwright tests available
- FontAwesome unicode glyphs (#47) must match FA6 icon codes exactly; verify before commit
