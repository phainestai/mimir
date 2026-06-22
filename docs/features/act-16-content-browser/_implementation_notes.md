# Content Browser — Implementation Notes

> Shipped behavior reference for Act-16. Feature scenarios in this folder are the
> source of truth for acceptance criteria; this file documents how the code implements them.

---

## Layout (three-panel)

```
┌──────────────┬──────────────────────────────┬──────────────────┐
│  LEFT PANEL  │         CANVAS               │  DETAIL PANEL    │
│  (collapsible│    Cytoscape.js graph         │  (slide-in right)│
│   ~280px)    │                              │                  │
│              │                              │  fetch embed HTML│
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

### Left panel toggle requirements
- Toggle button sits at `position: absolute; end: 0; top: 50%` on the left panel edge
- `z-index: 30` — must sit above Cytoscape canvas and zoom controls (z-index: 10)
- **When expanded:** button shows `‹`, positioned at right edge of the 280px panel
- **When collapsed:** panel width drops to 0, button shows `›`; its `translate(50%, -50%)`
  transform keeps the button centre at x ≈ 10px — always visible at the left edge of the canvas
- `cy.resize()` must be called after every toggle so Cytoscape redraws to the new canvas width

---

## Tech stack (per SAO.md § Interactive Graph Views)

- **Container page:** Django template at `templates/browser/browser_graph.html`
- **Cytoscape.js + layout extensions:** loaded via CDN in `<head>` (pinned versions; **no SRI**
  integrity hashes on these scripts — guard via inline bootstrap check for `window.cytoscape`)
- **Data API (single endpoint):** `GET /api/playbooks/<pk>/graph/`
  - Response: `{nodes: [...], edges: [...], phases: [...]}`
- **Left panel trees:** client-side derived from graph nodes (no `/tree/` endpoint)
- **Detail panel:** `fetch(embed_url)` into `#browser-panel-content` — **not HTMX**; no iframe
- **Playbook picker:** `GET /api/playbooks/` (client-side list; **no** server `accessible_playbooks` context)
- **Graph scripting:** `static/js/content-browser.js` — plain browser JS, Cytoscape imperative API

---

## Canvas controls (FOB-61, FOB-63)

| Control | data-testid | Default (FOB-63 unchecked) |
|---------|-------------|----------------------------|
| Custom layout checkbox | `browser-custom-layout-toggle` | Unchecked on entry |
| Layout picker | `browser-layout-btn` | Hidden until custom layout checked |
| Edge routing | `browser-routing-btn` | Hidden; default straight when applied |
| Grouping menu | `browser-compound-btn` | Hidden; default workflow-activity grouping |
| Node size | `browser-node-size-toggle` | Visible |
| Re-plot | `browser-replot-btn` | Visible |
| Zoom | `browser-zoom-in/out/fit` | Visible |

**Removed controls (no DOM, no URL params):**
- `browser-seq-toggle` — predecessor edges always shown (FOB-51)
- `browser-compound-toggle` — replaced by FOB-61 dropdown
- `browser-filter-toolbar`, `browser-phase-filter` — entity/phase filters removed (FOB-11/11b)

Default layout mode on entry: layout=klay, routing=straight, compound=workflow-activity.
Custom layout checkbox state is **not** persisted in the URL; full reload resets to defaults.

---

## Node visual style

See FOB-38 / FOB-53 in `07-canvas-controls.feature` for the shipped pastel palette,
round-rectangle shapes, FA6 Unicode icons, and uniform black edges.

Colour tokens are centralized in `static/js/content-browser.js`:
- `_BOOTSTRAP_PALETTE` — Bootstrap 5.3 theme hex values for base node/edge styles
- `_PASTEL_NODE_PALETTE` — per-entity-type pastel fills (enhanced mode, FOB-38)

---

## Embed mode (?embed=1)

- Supported by 7 entity detail views: playbook, workflow, activity, artifact, skill, agent, rule
- Each view checks `request.GET.get('embed') == '1'`
  - If embed: render `templates/<entity>/_embed.html` (no `extends`, pure content)
  - If not embed: render existing full-page template unchanged
- Content loaded via **fetch**, not HTMX or iframe

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

- Phase is NOT a node type; phases returned as top-level array in graph JSON
- Activity nodes carry `phase_id / phase_name / phase_colour` in `meta`
- Phase filter UI removed — all phases always visible; phase metadata used for display only

---

## URL structure

```
/browser/                    → graph view, no playbook (empty state canvas)
/browser/<pk>/               → graph view for playbook <pk> (canonical route)
/browser/<pk>/?layout=klay&routing=straight&compound=workflow-activity  → after custom changes
/api/playbooks/<pk>/graph/   → JSON graph payload
/api/playbooks/              → picker list (ACL-filtered)
```

**Removed URL params:** `types`, `phases`, `seq` (filter toolbar and seq toggle removed).

Both `/browser/` and `/browser/<pk>/` render `browser_graph.html`.
`content-browser.js` reads `data-playbook-pk` on `#browser-root`.

---

## Permission model

- `/browser/<pk>/` → `playbook_readable_or_404(request, pk)` in `methodology/utils/playbook_access.py`
- `/browser/` → shell only; picker uses `GET /api/playbooks/` (same ACL as API list)
- `login_required` on both views; Django redirects to `/auth/user/login/?next=...`

---

## Client JS requirements (`content-browser.js`)

1. Graph fetch: check `response.ok` and `content-type === application/json` before parse
2. Session expiry on graph fetch or embed fetch → redirect to `/auth/user/login/?next=/browser/<pk>/`
3. `AbortController` — abort in-flight graph fetch on playbook switch or popstate
4. Search: debounce 200ms, substring match, dim non-matching nodes (edges not dimmed)
5. Expose `window.cy` for Playwright E2E
6. Playbook switch via picker: full page navigation to `/browser/<pk>/` (FOB-23b)
7. In-session playbook switch via `history.pushState` updates `/browser/<pk>/` only

---

## `data-testid` attributes (Playwright)

| attribute | element |
|-----------|---------|
| `data-testid="nav-browser"` | nav link |
| `data-testid="browser-playbook-name"` | playbook name heading |
| `data-testid="browser-change-playbook"` | [Change Playbook] |
| `data-testid="browser-select-playbook"` | [Select Playbook] (empty state) |
| `data-testid="browser-picker"` | picker container |
| `data-testid="browser-picker-search"` | picker search input |
| `data-testid="browser-picker-item"` | each playbook row |
| `data-testid="browser-structure-tree"` | structural tree |
| `data-testid="browser-resource-tree"` | resource tree |
| `data-testid="browser-canvas"` | Cytoscape container |
| `data-testid="browser-detail-panel"` | right detail panel |
| `data-testid="browser-panel-content"` | embed fetch target |
| `data-testid="browser-panel-open-tab"` | [Open in new tab] |
| `data-testid="browser-panel-open-full"` | [Open full] |
| `data-testid="browser-panel-close"` | [×] close |
| `data-testid="browser-search-input"` | node name search |
| `data-testid="browser-custom-layout-toggle"` | custom layout checkbox |
| `data-testid="browser-compound-btn"` | grouping dropdown (FOB-61) |
| `data-testid="browser-layout-btn"` | layout picker |
| `data-testid="browser-routing-btn"` | edge routing picker |
| `data-testid="browser-node-size-toggle"` | node size mode |
| `data-testid="browser-empty-state"` | empty state card |
| `data-testid="browser-controls-panel"` | canvas controls stack |

---

## Session expiry — two code paths

- **Direct URL / page load:** Django `login_required` → `/auth/user/login/?next=<full-url>`
- **In-session fetch (graph or embed):** JS detects non-JSON or login HTML →
  `window.location.href = '/auth/user/login/?next=/browser/<pk>/'`

---

## Key source files

```
methodology/browser_views.py
methodology/browser_urls.py
methodology/utils/playbook_access.py
methodology/api/viewsets.py          # graph action + playbook list ACL
methodology/services/playbook_service.py  # get_accessible_playbook_ids()
templates/browser/browser_graph.html
static/js/content-browser.js
tests/e2e/test_content_browser*.py
tests/integration/test_content_browser_access.py
tests/integration/test_graph_api.py
tests/integration/test_embed_views.py
```
