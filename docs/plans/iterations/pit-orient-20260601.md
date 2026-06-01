## Orient Summary — 2026-06-01

### Input Scope
Goal: Content Browser — Entity-Type Filter Rebuild (filter removes nodes from Cytoscape + auto-re-layout)
Scenarios:
  - #32: [S30] Entity-type filter removes nodes from Cytoscape and auto-re-layouts (FOB-11)
  - #33: [S31] Update Re-plot button test description to match new filter-rebuild model (FOB-29)
  - #34: [S32] Tree-panel click on removed-type node still opens detail panel (FOB-32)

### Velocity Trend
Last 3 ratios: 1.0 (only 1 entry) — insufficient data (first substantive entry)
Trend: stable (single data point)

### Dominant Drift
none (0/1 iterations)

### Footprint Accuracy
met_checkpoints — stable

### Scope Validation
- S30: Core JS rebuild — content-browser.js is a ~1350-line file; _applyTypeFilter is deep inside.
  Risk: moderate complexity. No drift flag triggered (velocity stable, <3 scenarios).
- S31: Test-only update. Low risk.
- S32: Likely test + JS behaviour. Low risk, depends on S30.

### Watch For
- S30 touches content-browser.js which is also touched by S31 and S32 — serialize these.
- ELK layout call after cy.remove/add may need timing care (layout fires before elements settle).
