# ADR-001: Content Browser graph rendering stack (Cytoscape.js)

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-05-31 (decision) · 2026-06-22 (ADR drafted retroactively) |
| **Deciders** | Act-16 planning (commit `40ec953`); shipped in [PR #145](https://github.com/phainestai/mimir/pull/145) |
| **Feature** | Act-16 Content Browser (`/browser/`, `/browser/<pk>/`) |
| **Supersedes** | — |
| **Superseded by** | — (see [Revisit criteria](#revisit-criteria)) |

---

## Context

Mimir's default FOB web stack is **Django templates + HTMX + Graphviz** (see [`SAO.md`](../SAO.md) § *Technology Choice: HTMX + Graphviz*). Graphviz already powers **static, server-rendered** workflow activity diagrams via `ActivityGraphService` on workflow detail pages.

Act-15/16 in the user journey introduced a new capability: a **full-playbook graph explorer** — a dedicated route where Maria sees *all* entity types (workflows, activities, artifacts, skills, agents, rules) and their relationships on one canvas, with exploration affordances beyond a single-workflow SVG.

Requirements captured in `docs/features/act-16-content-browser/` and `docs/features/user_journey.md` (Act 15) included:

- Three-panel layout: structural tree, central canvas, detail panel
- **Interactive canvas**: pan, zoom, fit, click-to-select, animate-to-node from tree
- **Live visual filtering**: entity-type toggles, phase filter, name search (dim/highlight) without full page reload
- **Layout experimentation**: hierarchical default; later iterations added ELK, dagre, klay, and 15+ additional layout plugins
- **Performance envelope**: ~300 nodes / ~500 edges; graph API < 500 ms; client render < 2 s
- **Shareable URL state**: playbook in path; layout/routing/compound params in query string (post-FOB-63)
- **Single data fetch** feeding canvas and client-derived left-panel trees

At planning time (2026-05-31), no formal Architecture Decision Record compared Graphviz to client-side graph libraries. The choice was embedded in the feature spec pack, `_implementation_notes.md`, and an SAO amendment (`§ Interactive Graph Views — Cytoscape.js`) in the same commit.

---

## Decision

**Use Cytoscape.js (CDN, no build step) with a dedicated JSON graph API and a single view script (`static/js/content-browser.js`) for the Content Browser canvas.**

Concretely:

1. **Canvas** — Cytoscape.js + layout plugins (dagre, ELK, klay, cola, …) loaded via CDN in `templates/browser/browser_graph.html`.
2. **Data** — `GET /api/playbooks/<pk>/graph/` returns Cytoscape-shaped `{ nodes, edges, phases }` built in `methodology/api/viewsets.py` (`_build_playbook_graph`).
3. **Page shell** — Django template for chrome (nav, panels, controls); imperative JS for graph lifecycle.
4. **Scope boundary** — Cytoscape restricted to `/browser/` route family only; must not appear in HTMX partials or existing CRUD pages.
5. **Testing** — Integration tests for API; Playwright E2E for canvas interactions (`window.cy` contract).

SAO was amended to carve out this exception while keeping Graphviz as the default for all other graph visualizations.

---

## Alternatives considered

### A. HTMX + Graphviz (original SAO default) — **not selected**

| Aspect | Assessment |
|--------|------------|
| **Fit** | Strong for **single-workflow** diagrams already shipped (`ActivityGraphService`). |
| **Pan/zoom** | Requires scroll container or additional JS (e.g. svg-pan-zoom); not in original Act-16 spec. |
| **Filter/search dimming** | Each toggle implies **server re-render** of SVG via HTMX (`hx-get` → new fragment). Acceptable for small graphs; latency on 100+ node playbooks. |
| **Layout picker (20 algos)** | Graphviz engines differ from Cytoscape plugin catalog; each layout = round-trip. Act-16 spec explicitly named Cytoscape/ELK layout keys. |
| **Compound grouping** | Graphviz `cluster_*` subgraphs possible but awkward for dynamic mode switching (workflow / phase / flat). |
| **Tree → canvas focus** | No built-in animate-to-node; would need fragment IDs + scroll-into-view or custom JS. |
| **Testing** | Integration tests on SVG output — **aligns with SAO testing philosophy**. |
| **Why not chosen** | Act-16 was spec'd as an **interactive explorer**, not a static diagram page. Planners judged Graphviz + HTMX insufficient for live canvas manipulation at playbook scale without re-specifying most of Act-16. **No spike or ADR documented this comparison at the time.** |

### B. HTMX + Graphviz with drill-down (hybrid) — **not evaluated at planning time**

- Default view: playbook → workflows only; HTMX loads workflow subgraph on selection.
- Most SAO-native; avoids mega-SVG.
- **Not written into May 2026 specs.** Reasonable candidate for a future ADR if scope is reduced.

### C. React/Vue + graph library — **rejected per SAO**

- Build toolchain, bundle size, and Playwright-heavy testing contradict FOB conventions.

### D. Cytoscape.js (CDN, plain JS) — **selected**

- Pan/zoom/drag, stylesheet API, compound nodes, layout plugins, canvas performance for 300+ nodes.
- No webpack/vite; consistent with "no build step" constraint.
- Trade-off: large imperative JS surface and Playwright dependency for canvas behavior.

---

## Consequences

### Positive

- Shipped full Act-16 vision: interactive playbook graph, detail panel, trees, URL shareability ([PR #145](https://github.com/phainestai/mimir/pull/145), 63 scenarios).
- Reuses existing REST/auth layer; graph API also usable by future clients.
- Canvas performance acceptable for FeatureFactory-scale playbooks (Canvas renderer vs DOM SVG).

### Negative

- **`static/js/content-browser.js` grew to ~2,500 lines** across 12 MIT iterations — scope expansion (4 → 29 canvas-control scenarios) without BPE-08 cleanup.
- **13 Cytoscape CDN scripts**; layout catalog complexity flagged in PR review as unsuitable for end users without feature-flagging.
- **Testing split**: canvas behavior requires Playwright; contradicts SAO headline claim that FOB graphs are "testable without browser automation."
- **Spec/implementation drift**: original notes planned HTMX for detail panel; shipped code uses `fetch()`. SAO rule 6 ("prefer HTMX over iframes") partially honored via embed partials, not HTMX swap.
- **No comparative spike on record** — Graphviz path was not prototyped; decision reads as spec-driven rather than evidence-driven.

### Neutral

- Graph API (`_build_playbook_graph`) is **renderer-agnostic** — could feed Graphviz builder in a future replatform with service extraction.

---

## Compliance with SAO rules (Cytoscape carve-out)

| SAO rule | Shipped compliance |
|----------|-------------------|
| 1. Dedicated route family only | ✅ `/browser/` only |
| 2. CDN, no build step | ✅ (SRI hashes not applied — documented drift) |
| 3. Data via `/api/` | ✅ |
| 4. No HTMX global coupling | ✅ |
| 5. URL as source of truth | ✅ playbook path; layout params after FOB-63 |
| 6. Prefer HTMX for embed panel | ⚠️ Uses `fetch()`, not `htmx.ajax()` |
| 7. Testable contract | ⚠️ API integration tests ✅; canvas requires E2E |
| 8. Performance envelope | ✅ Declared in `_implementation_notes.md` |

---

## PR #145 review notes (post-decision, not stack selection)

PR #145 did **not** debate Graphviz vs Cytoscape. Relevant product feedback:

- **Layout complexity** ([review on `03-graph-rendering.feature`](https://github.com/phainestai/mimir/pull/145)): 20-algorithm picker is too complex for typical users — feature-flag in production or collapse to 1–3 layouts.
- **Author response (strek)**: layout/compound/routing experimentation drove "dirty JS"; intent to trim to pre-vetted defaults after team review.
- **Merge note (sourishsarkar-epam)**: layout simplification acceptable as follow-up; uncertain about prod promotion.

These comments target **canvas control bloat**, not reversing Cytoscape.

---

## Revisit criteria

Re-open this ADR (or supersede with ADR-002) if any of the following are agreed:

1. **Product scope reduction** — Content Browser no longer requires live pan/zoom, client-side filter dimming, or multi-layout experimentation on one canvas.
2. **Maintainability gate** — `content-browser.js` cannot be reduced below an agreed line/complexity budget after layout trim and CDN collapse.
3. **Testing strategy** — team requires canvas graph assertions via Django integration tests only (no Playwright for structure).
4. **Production policy** — deploy Graphviz-first or drill-down explorer; feature-flag or remove Cytoscape canvas in production.

A Graphviz replatform would require:

- BPE-08 change request + Act-16 feature file rewrite
- `PlaybookGraphService` (extract `_build_playbook_graph` → Graphviz SVG builder)
- HTMX partials for detail panel, layout/filter changes, and optional drill-down
- Retire or shrink `content-browser.js` and Cytoscape CDN includes
- E2E scope reduction in favor of integration tests on SVG/HTML

---

## References

- [`docs/architecture/SAO.md`](../SAO.md) — § *Technology Choice: HTMX + Graphviz*; § *Interactive Graph Views — Cytoscape.js*
- [`docs/features/act-16-content-browser/_implementation_notes.md`](../../features/act-16-content-browser/_implementation_notes.md)
- [`docs/features/user_journey.md`](../../features/user_journey.md) — Act 15: Content Browser
- [`docs/plans/iterations/ITER-20260601-content-browser-graph.yaml`](../../plans/iterations/ITER-20260601-content-browser-graph.yaml) — S4/S5 manifest
- [`methodology/services/activity_graph_service.py`](../../../methodology/services/activity_graph_service.py) — existing Graphviz pattern
- [PR #145](https://github.com/phainestai/mimir/pull/145) — merge (2026-06)
