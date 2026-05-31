# Content Browser — Implementation Notes

> These notes are pre-implementation design guidance. They will be progressively
> stripped out and replaced by the formal implementation plan in `docs/plans/`.

---

## Layout (three-panel)

```
┌──────────────┬──────────────────────────────┬──────────────────┐
│  LEFT PANEL  │         CANVAS               │  DETAIL PANEL    │
│  (collapsible│    Cytoscape.js graph         │  (slide-in right)│
│   ~280px)    │                              │                  │
│              │                              │  HTMX content    │
│ [Playbook]   │                              │  + Open new tab  │
│ [Change]     │                              │  + Open full     │
│              │                              │  + ×             │
│ Structure    │                              │                  │
│  Workflow    │                              │                  │
│   Activity   │                              │                  │
│              │                              │                  │
│ Resources    │                              │                  │
│  Artifacts   │                              │                  │
│  Skills      │                              │                  │
│  Agents      │                              │                  │
│  Rules       │                              │                  │
└──────────────┴──────────────────────────────┴──────────────────┘
```

---

## Tech stack (per SAO.md § Interactive Graph Views)

- **Container page:** Django template at `templates/browser/browser_graph.html`
- **Cytoscape.js + cytoscape-dagre + cytoscape-navigator:** loaded via CDN in `<head>`, pinned to specific versions with SRI integrity hashes
- **Data API (single endpoint):** `GET /api/playbooks/<pk>/graph/`
  - Response: `{nodes: [{id(namespaced), type, label, entity_pk, detail_url, embed_url, meta}], edges: [{source, target, relationship}], phases: [{id, name, colour}]}`
- **Left panel structural tree:** client-side derived from graph nodes (type IN [workflow, activity])
- **Left panel resource tree:** client-side derived from graph nodes (type IN [skill, agent, rule, artifact])
- **No separate /tree/ endpoint** — one graph fetch serves all three panels
- **Side panel:** `htmx.ajax('GET', node.embed_url, {target:'#browser-detail-panel', swap:'innerHTML'})` — same HTMX pattern as `methodology/partials/activity_feed.html`; no `<iframe>`, no X-Frame-Options changes needed
- **Playbook picker:** `GET /api/playbooks/` (already exists)
- **Graph scripting:** `static/js/content-browser.js` — plain browser JS using Cytoscape.js imperative API (`cy.add`, `cy.on`, `cy.elements().style()`, etc.) — no JSX, no build step

---

## Node visual style

| entity   | Bootstrap colour var     | icon (tree/resource) | shape      |
|----------|--------------------------|----------------------|------------|
| Playbook | `--bs-purple` (#6f42c1)  | `bi-book`            | diamond    |
| Workflow | `--bs-primary` (#0d6efd) | `bi-diagram-3`       | round-rect |
| Activity | `--bs-success` (#198754) | `bi-list-check`      | round-rect |
| Artifact | `--bs-warning` (#ffc107) | `bi-gift`            | ellipse    |
| Skill    | `--bs-orange` (#fd7e14)  | `bi-hand-index-thumb`| ellipse    |
| Agent    | `--bs-cyan` (#0dcaf0)    | `bi-person-badge`    | ellipse    |
| Rule     | `--bs-secondary` (#6c757d)| `bi-file-ruled`     | ellipse    |

- **Selected node:** 3px selection ring in `--bs-danger` (#dc3545); all other nodes dim to 0.4 opacity
- **Dimmed node opacity** (phase filter / search): 0.2
- **Phase chip on Activity node:** small filled circle in `phase.colour`, overlaid bottom-right of node

---

## Edge visual style

| relationship         | style              | colour                  |
|----------------------|--------------------|-------------------------|
| contains (→Workflow) | solid, thick       | `--bs-primary`          |
| contains (→Activity) | solid, medium      | `--bs-success`          |
| produces Artifact    | dashed             | `--bs-warning`          |
| consumes Artifact    | dashed, reversed   | `--bs-warning`          |
| uses Skill           | dotted             | `--bs-orange`           |
| assigned Agent       | dotted             | `--bs-cyan`             |
| governed by Rule     | dotted             | `--bs-secondary`        |
| predecessor (→Act)   | solid, thin, dashed| `--bs-success` (muted)  |

---

## Embed mode (?embed=1)

- Supported by 7 entity detail views: playbook, workflow, activity, artifact, skill, agent, rule
- Phase is NOT a graph node — no embed needed
- Each view checks `request.GET.get('embed') == '1'`
  - If embed: render `templates/<entity>/_embed.html` (no `extends`, pure content)
  - If not embed: render existing full-page template unchanged
- `_embed.html` templates contain the content card only (Bootstrap card markup OK)
- No X-Frame-Options or CSP changes needed — content is loaded via HTMX, not iframe

Entity embed URLs:
| entity   | embed_url                                              |
|----------|--------------------------------------------------------|
| Playbook | `/playbooks/<pk>/?embed=1`                             |
| Workflow | `/playbooks/<pb>/workflows/<wf>/?embed=1`              |
| Activity | `/playbooks/<pb>/workflows/<wf>/activities/<act>/?embed=1` |
| Artifact | `/artifacts/<art>/?embed=1`                            |
| Skill    | `/playbooks/<pb>/skills/<sk>/?embed=1`                 |
| Agent    | `/agents/<ag>/?embed=1`                                |
| Rule     | `/playbooks/<pb>/rules/<r>/?embed=1`                   |

---

## Phase in graph API

- Phase is NOT a node type and NOT an edge endpoint
- Phases returned as top-level array: `[{id, name, colour}]`
- Activity nodes carry `phase_id / phase_name / phase_colour` in `meta`
- JS uses this to: render Phase chips on nodes; populate Phase filter; apply `cy.elements().style()` for dim/show on filter change

---

## URL structure

```
/browser/                    → graph view, no playbook (empty state canvas)
/browser/<pk>/               → graph view for playbook <pk>
/browser/<pk>/?types=workflow,activity&phases=2,5  → with active filters
/api/playbooks/<pk>/graph/   → JSON: {nodes, edges, phases}
/api/playbooks/              → already exists; used for playbook picker
```

Both `/browser/` and `/browser/<pk>/` render the same Django template (`browser_graph.html`).
The view passes `pk=None` or `pk=<int>` as a data attribute on `#browser-root`.
`content-browser.js` reads it on init: if `null` → show empty state; if `pk` → fetch graph + render.

---

## Permission model (no new code needed)

- `/browser/<pk>/` → view calls `_playbook_readable_or_404(request, pk)` → 404 on fail
- `/browser/` → just render shell; JS loads `GET /api/playbooks/` (already ACL'd)
- Picker list → `GET /api/playbooks/` filters by accessible playbooks (existing logic)
- `login_required` → both views; Django redirects with `?next=` preserved

---

## Defensive implementation requirements

### Graph API serializer (server-side) MUST:
1. Use `select_related`/`prefetch_related` to avoid N+1 queries
2. Detect and skip circular predecessor chains (log warning; drop cyclic edges)
3. Emit only edges whose source AND target node both exist in the nodes list (skip dangling FK references to deleted entities)
4. Scope ALL related entities to current playbook (skills, agents, rules, phases) — drop cross-playbook FK leaks
5. Namespace all node IDs: `"workflow:7"`, `"activity:12"`, `"artifact:3"` — prevents PK collisions in Cytoscape

### Client JS (content-browser.js) MUST:
1. Check `response.ok AND content-type === 'application/json'` before `JSON.parse()` → catches session-expired redirects
2. Use `AbortController` — abort in-flight graph fetch on playbook switch or popstate
3. Normalise URL params on init:
   - Unknown type values → ignored (not hidden)
   - Empty types param → treat as all types shown
   - Phase IDs not in current playbook's phases array → dropped + URL rewritten
   - Phase filter reset on playbook switch (phase IDs are playbook-scoped)
4. Check swapped HTML for login-page indicator; redirect tab to `/auth/login/?next=/browser/<pk>/` if detected
5. CDN bootstrap guard: inline `<script>` checks `window.cytoscape` before init; if missing, shows static "scripts failed to load" fallback without JS
6. Search: treat input as literal substring (escape regex chars), debounce 200ms, cap at 100 chars; use `cy.elements('[label @*= "term"]')` selector
7. Node labels: plain text only — set via Cytoscape stylesheet `content` property, not `innerHTML`
8. Call `cy.destroy()` before re-initialising on playbook switch:
   ```js
   if (window.cy) { window.cy.destroy(); window.cy = null; }
   ```
9. Expose Cytoscape instance as `window.cy` — required for Playwright E2E tests:
   ```js
   await page.evaluate(() =>
     window.cy.getElementById('workflow:3').emit('tap', [{position:{x:0,y:0}}])
   );
   await expect(page.locator('[data-testid="browser-detail-panel"]')).toBeVisible();
   ```

---

## Performance envelope (SAO.md rule 8)

- Supported size: up to ~300 nodes + ~500 edges without degraded mode
- Expected load time: graph API < 500ms (server); render < 2s (client)
- Degraded mode: if node count > 300, canvas shows a warning banner and offers `[Collapse to Workflows only]`
- Pagination: not supported in MVP-1

---

## Navigation

- Content Browser = second nav item in `base.html` (after Home, before Playbooks)
- `nav_section = 'browser'` for active state

---

## Responsive / mobile

- Desktop-first feature. Three-panel layout requires ~900px minimum width.
- On viewports < 768px (Bootstrap `md` breakpoint):
  - Canvas rendered full-width (left and detail panels hidden)
  - Banner: "For the best experience, use a desktop browser."
- All Django views and API endpoints still work — only the layout adapts.
- No mobile-specific interaction tested in Playwright (viewport = 1280×800).

---

## `data-testid` attributes (required for Playwright)

| attribute                        | element                              |
|----------------------------------|--------------------------------------|
| `data-testid="nav-browser"`      | nav link                             |
| `data-testid="browser-playbook-name"` | playbook name heading in left panel |
| `data-testid="browser-change-playbook"` | [Change Playbook] button          |
| `data-testid="browser-select-playbook"` | [Select Playbook] button (empty state) |
| `data-testid="browser-picker"`   | picker slide-down container          |
| `data-testid="browser-picker-search"` | picker search input               |
| `data-testid="browser-picker-item"` | each playbook row in picker        |
| `data-testid="browser-structure-tree"` | structural tree container        |
| `data-testid="browser-phase-filter"` | phase filter control              |
| `data-testid="browser-resource-tree"` | resource tree container          |
| `data-testid="browser-canvas"`   | Cytoscape canvas container           |
| `data-testid="browser-detail-panel"` | right detail panel               |
| `data-testid="browser-panel-content"` | HTMX swap target inside panel   |
| `data-testid="browser-panel-open-tab"` | [Open in new tab] button        |
| `data-testid="browser-panel-open-full"` | [Open full] button             |
| `data-testid="browser-panel-close"` | [×] close button                  |
| `data-testid="browser-filter-toolbar"` | entity type filter toolbar      |
| `data-testid="browser-search"`   | node name search input               |
| `data-testid="browser-empty-state"` | empty state canvas card           |
| `data-testid="browser-error-state"` | error state canvas card           |
| `data-testid="browser-loading"`  | loading spinner                      |

---

## New files expected

```
methodology/browser_views.py
methodology/browser_urls.py
templates/browser/browser_graph.html
templates/playbooks/_embed.html
templates/workflows/_embed.html
templates/activities/_embed.html
templates/artifacts/_embed.html
templates/skills/_embed.html
templates/agents/_embed.html
templates/rules/_embed.html
methodology/api/graph_viewset.py
static/js/content-browser.js
tests/integration/test_content_browser_view.py
tests/integration/test_graph_api.py
tests/integration/test_embed_views.py
tests/e2e/test_content_browser.py
```

## Modified files

```
templates/base.html              (add Content Browser as second nav item)
methodology/playbook_views.py    (add ?embed=1 branch)
methodology/workflow_views.py    (add ?embed=1 branch)
methodology/activity_views.py    (add ?embed=1 branch)
methodology/artifact_views.py    (add ?embed=1 branch)
methodology/skill_views.py       (add ?embed=1 branch)
methodology/agent_views.py       (add ?embed=1 branch)
methodology/rule_views.py        (add ?embed=1 branch)
methodology/api/viewsets.py      (add @action graph on PlaybookViewSet)
mimir/urls.py                    (include browser_urls)
```

---

## Scenario implementation notes

### Scenario ordering rationale
- **08b (Embed mode) must be implemented before 08 (Detail panel)**: the panel JS fetches
  `?embed=1` URLs; if embed mode is not working the panel will render full-page HTML inside
  the side panel. Build embed mode in all 7 entity views first.

### Session expiry — two distinct code paths
- **FOB-CONTENT-BROWSER-01b** (direct URL access): handled by Django `login_required`.
  Django redirects server-side and preserves the full requested URL (including query params)
  in `?next=`. No JS involved.
- **FOB-CONTENT-BROWSER-08c / 13c** (JS-triggered fetch during session): detected
  client-side by `content-browser.js` checking `response.ok && content-type === application/json`.
  JS redirects to `/auth/login/?next=/browser/<pk>/` without filter params — intentionally
  simpler; user re-applies filters after re-auth.

### Deleted playbook — two distinct code paths
- **FOB-CONTENT-BROWSER-03c** (page load / direct URL): `_playbook_readable_or_404` in the
  Django view returns HTTP 404 → standard Django 404 page. No JS involved.
- **FOB-CONTENT-BROWSER-13d** (in-session, on retry): JS receives 404 from graph API and
  shows "This playbook is no longer available." with a [Browse other playbooks] button.

### Empty playbook test fixture (FOB-CONTENT-BROWSER-15)
- The Background fixture ("FeatureFactory") has content. Scenario 15 requires a **separate
  fixture**: a playbook with no workflows, activities, or phases. Create it in `setUp` or as
  a factory fixture in the acceptance test file — do not rely on Background.

---

## Deferred

- Large graph degraded mode (>200 nodes: simplified layout, clustering)
- Node drag-to-reposition
- Export graph as PNG/SVG
- Multi-playbook view (compare two playbooks side by side)
- Inline edit from graph panel (requires Released/PIP logic)
