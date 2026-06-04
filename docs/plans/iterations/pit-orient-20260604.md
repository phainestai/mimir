## Orient Summary — 2026-06-04

### Input Scope
Goal: ITER-20260602d | Canvas Bug-Fix & Compound Grouping (FOB-58–62)
Scenarios:
  - FOB-58: Fix canvas node font all-caps rendering on zoom
  - FOB-59: Add straight-triangle to edge routing catalog
  - FOB-60: Fix compound node label visibility + font size + activity colour
  - FOB-61: 3-level compound grouping context menu (no-group / workflow / workflow+activity)
  - FOB-62: Fix node text/icon overflow in fixed and auto-width modes

### Velocity Trend
Last 3 ratios: 1.0, 1.0, 1.1 — stable/slightly improving

### Dominant Drift
implementation_complexity (1/3 iterations — most recent)

### Footprint Accuracy
met_checkpoints in all iterations — stable

### Scope Validation
- FOB-58 (font rendering): Low risk — single style property addition
- FOB-59 (routing catalog): Low risk — one catalog entry addition
- FOB-60 (compound labels): Medium risk — compound label positioning requires careful CSS tuning
- FOB-61 (3-level compound): HIGH risk — largest change, replaces boolean with enum, adds new compound mode, touches compound building and HTML dropdown
- FOB-62 (overflow fix): Medium risk — node sizing logic change in two code paths

### Watch For
- implementation_complexity on FOB-61 (compound grouping redesign) — monitor for scope expansion
- FA6 font issues may affect FOB-58 (font rendering) — verify against Free tier glyphs
- E2E tests skip without released playbook in test DB — checkpoint commands must handle graceful skip
- FOB-61 removes _compoundViewOn boolean — all references must be updated; grep thoroughly before skeleton
