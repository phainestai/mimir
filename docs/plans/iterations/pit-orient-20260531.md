# Orient Summary — 2026-05-31

## Input Scope
Goal: Implement Content Browser access layer — Django view scaffold, URL routing,
      login enforcement, nav entry, 404 handling, picker access control, and client-side
      URL management (pushState + param normalisation)

Scenarios from: `docs/features/act-16-content-browser/01-access-and-nav.feature`
  - FOB-CONTENT-BROWSER-01   Content Browser added to top navigation after Home
  - FOB-CONTENT-BROWSER-01b  Unauthenticated user is redirected to login
  - FOB-CONTENT-BROWSER-02   /browser/ with no playbook selected shows empty state
  - FOB-CONTENT-BROWSER-03   /browser/<pk>/ loads the graph for that playbook directly
  - FOB-CONTENT-BROWSER-03b  URL is the source of truth for active playbook and filters
  - FOB-CONTENT-BROWSER-03c  Inaccessible or missing playbook returns 404
  - FOB-CONTENT-BROWSER-03e  Playbook picker only shows accessible playbooks
  - FOB-CONTENT-BROWSER-03f  URL filter params are normalised on load

Grouped into 3 work items:
  S1 — Server-side scaffold     (01, 01b, 02, 03, 03c) — pure Django
  S2 — Picker access control    (03e)                  — API filter validation
  S3 — Client-side URL mgmt     (03b, 03f)             — content-browser.js stub

## Velocity Trend
Last 3 ratios: 1.0 (only 1 entry) — stable (first iteration for this feature)

## Dominant Drift
none (1/1 iterations)

## Footprint Accuracy
met_checkpoints (1/1 iterations)

## Scope Validation
S1: Touches base.html, context_processors.py, new browser_views.py, browser_urls.py,
    browser_graph.html. All well-established Django patterns already present in codebase.
    No risk flagged.
S2: Reuses PlaybookService.get_accessible_playbook_ids (already exists at line 250).
    No new service code needed. Low risk.
S3: New static/js/ directory needed (does not exist yet). First JS file in project.
    CDN-only, no build step — consistent with SAO.md rule 2. Low-medium risk (new territory).

## Watch For
- S3: static/js/ directory creation must not introduce a build pipeline (SAO.md rule 2)
- S3: window.cy must be set to null initially (not yet init'd in this iteration) so
  Playwright tests that check for absence don't get false failures
- S2: verify GET /api/playbooks/ actually filters by accessible — check DRF viewset
  `get_queryset` before writing test assertions
