## Orient Summary — 2026-06-02

### Input Scope
Goal: Fix 9 canvas bugs — icons, flat-mode connectivity, node-size reflow, treeview accordion, button layout, full-screen layout, compound labels, seq-toggle removal, routing catalog
Scenarios: 9 new issues (to be created in PIT-03)
  - S50: FOB-53 FA icons showing blank rectangle (wrong codepoints)
  - S51: FOB-52 Flat mode — workflows not connected to activities (contains edges)
  - S52: FOB-50 Node size toggle doesn't trigger layout reflow
  - S53: FOB-58 Treeview: workflow row click must expand accordion + canvas tap must expand parent
  - S54: FOB-55 Canvas controls: half-size buttons grouped in rows
  - S55: FOB-56 Full-screen layout — no scroll, no gaps
  - S56: FOB-54 Compound mode workflow labels still not visible
  - S57: FOB-51 Remove seq toggle button entirely
  - S58: FOB-57 Routing catalog: taxi missing, round-seg→round-segments fix

### Velocity Trend
Last 2 ratios: 1.0, 1.0 — stable

### Dominant Drift
sqlite_postgresql_mismatch (1/2 iterations) — watch: always use `uv run pytest` with sqlite settings

### Footprint Accuracy
met_checkpoints both iterations — stable

### Scope Validation
- S50 (icons): small JS change, low risk
- S51 (flat edges): stylesheet change, low complexity
- S52 (reflow): one-liner addition to _applyNodeSizeToggle
- S53 (treeview accordion): _selectTreeNode + _highlightTreeNode updates, moderate
- S54 (button layout): HTML template change, low risk but visual
- S55 (layout): CSS/template change, moderate — touches base layout
- S56 (compound labels): Cytoscape stylesheet ":parent" label property, moderate
- S57 (seq removal): deletion of feature — touches JS + HTML + tests, moderate
- S58 (routing catalog): JS constant + key mapping, low risk

### Watch For
- Always `uv run pytest --ds=mimir.settings.test` or equivalent sqlite-mode settings
- E2E tests skip on CI (no Playwright) — acceptable; run locally to verify
