# Mimir Information Architecture Guidelines

> Shared with Huginn (`../huginn/docs/ux/IA_guidelines.md`) — same `--hg-*` tokens and `.hg-*` component classes in `static/css/design-system.css`.
> Companion to `docs/features/user_journey.md`. Last updated: July 2026 — unified with Huginn design system.

---

## Philosophy

Bootstrap-first. Use Bootstrap 5.3.8 utilities, components, and CSS variables as the first choice.
Customize only when Bootstrap cannot express the requirement or when brand identity demands it.

Every component must be:
- **Testable** — `data-testid` on all interactive elements
- **Accessible** — semantic HTML, ARIA attributes, keyboard-navigable
- **Traceable** — screen identifiers flow through journey → diagram → feature file → template

---

## Table of Contents

1. [Technology Baseline](#1-technology-baseline)
2. [Design Tokens](#2-design-tokens)
3. [Skeleton & Layout](#3-skeleton--layout)
4. [Navigation](#4-navigation)
5. [Component Kit](#5-component-kit)
6. [Behavior & Interactions](#6-behavior--interactions)
7. [Icon System — Font Awesome Free](#7-icon-system--font-awesome-free)
8. [Charts — Apache ECharts](#8-charts--apache-echarts)
9. [Accessibility](#9-accessibility)
10. [Screen ID Convention](#10-screen-id-convention)

---

## 1. Technology Baseline

| Concern | Library | Version | Load |
|---|---|---|---|
| CSS framework | Bootstrap | 5.3.8 | CDN — `cdn.jsdelivr.net/npm/bootstrap@5.3.8` |
| Icons | Font Awesome Pro | 6.x | Kit — `kit.fontawesome.com` (Mimir production) |
| Charts | Apache ECharts | 5.5.x | CDN — `cdn.jsdelivr.net/npm/echarts@5.5.1` |
| Interactivity | HTMX | 2.0.x | CDN — `unpkg.com/htmx.org@2.0.4` |
| Typography | Montserrat | — | Google Fonts — `fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap` |

**FA note (Mimir):** Production uses Font Awesome Pro via Kit. Prefer `fa-solid` / `fa-regular` / `fa-brands`. Huginn mockups may reference Kit-only icons; keep nav icons aligned with `templates/base.html`.

**Bootstrap upgrade policy**: track 5.3.x patch releases; evaluate minor bumps (5.4+, 6.x) as an explicit ADR.

**CSS load order:** Bootstrap CDN → `static/css/design-system.css` (Huginn `hg-*` system) → `static/css/mimir-app.css` (Content Browser, playbook cards, chrome).

---

## 2. Design Tokens

All tokens are CSS custom properties on `:root`. Bootstrap's own vars are overridden where needed.

### 2.1 Brand Tokens

```css
:root {
  /* Primary — slate-blue "command" */
  --hg-primary:     #1f3a5f;
  --hg-primary-700: #16294a;   /* hover / active state */
  --hg-primary-100: #e7eef7;   /* tinted bg, callout panels */

  /* Accent — muted gold, used sparingly */
  --hg-accent:      #c9a227;
  --hg-accent-700:  #8e7012;

  /* Surface / ink */
  --hg-bg-body:     #f5f7fa;   /* page background */
  --hg-bg-surface:  #ffffff;   /* card / panel surface */
  --hg-ink:         #1a1f2e;   /* primary text */
  --hg-ink-muted:   #5a6478;   /* secondary text, labels */
  --hg-border:      #e3e7ee;   /* card borders, dividers */

  /* Bootstrap overrides */
  --bs-primary:          var(--hg-primary);
  --bs-primary-rgb:      31, 58, 95;
  --bs-body-bg:          var(--hg-bg-body);
  --bs-body-color:       var(--hg-ink);
  --bs-border-color:     var(--hg-border);
  --bs-link-color:       var(--hg-primary);
  --bs-link-hover-color: var(--hg-primary-700);
}
```

### 2.2 RYG Semantic Tokens (locked)

Status colours are fixed — they drive the Tactical Plot health system and must not be repurposed for decoration.

```css
:root {
  --hg-red:    #dc3545;   /* = Bootstrap --bs-danger   */
  --hg-orange: #fd7e14;   /* = Bootstrap --bs-orange   */
  --hg-yellow: #ffc107;   /* = Bootstrap --bs-warning  */
  --hg-green:  #198754;   /* = Bootstrap --bs-success  */
  --hg-blue:   #0dcaf0;   /* = Bootstrap --bs-info     — Scheduled state */
  --hg-grey:   #6c757d;   /* = Bootstrap --bs-secondary — Expired/Revoked/Rejected */
}
```

**RYG usage rules**:

| Colour | Meaning | Examples |
|---|---|---|
| Red | Critical breach / token expired / error | Project card, data connection error |
| Orange | Warning breach / token expiring / degraded | Project card, expiry warning |
| Yellow | Minor breach | Project card |
| Green | OK / connected / accepted | Project card, sync status, Accepted badge |
| Blue | Scheduled / info | FRAGO scheduled state |
| Grey | Inactive / expired / rejected | FRAGO revoked, Decision rejected |

### 2.3 Spacing

Use Bootstrap's spacing utilities as-is (`m-0` through `m-5`, `p-0` through `p-5`). Component-specific spacing:

```css
:root {
  --hg-card-padding:   1.2rem 1.25rem;
  --hg-card-gap:       1rem;          /* row gap in card grid */
  --hg-section-gap:    2rem;          /* vertical gap between page sections */
  --hg-rail-padding:   0.85rem 1rem;
}
```

### 2.4 Typography

**Default typeface: Montserrat** (Google Fonts). Load all four weights used: 400 (body), 500 (medium emphasis), 600 (semi-bold headings), 700 (bold).

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700&display=swap" rel="stylesheet">
```

Override Bootstrap's font stack in the `:root` block:

```css
:root {
  --bs-font-sans-serif: 'Montserrat', system-ui, -apple-system, sans-serif;
  --bs-body-font-family: var(--bs-font-sans-serif);
}
```

Size scale and Huginn-specific classes:

```css
/* Sizes (Bootstrap defaults, documented here for reference) */
--bs-body-font-size: 1rem;      /* 16px */
--bs-h1-font-size:   2.5rem;
--bs-h2-font-size:   2rem;
--bs-h3-font-size:   1.75rem;

/* Huginn-specific overrides */
.hg-page-title  { font-size: 1.75rem; font-weight: 600; }
.hg-card-name   { font-size: 1rem;    font-weight: 600; }
.hg-label-caps  { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.06em; }
```

**Weight conventions**:

| Weight | Token | Usage |
|---|---|---|
| 400 | regular | Body copy, table cells, descriptions |
| 500 | medium | Nav items, badge labels, secondary actions |
| 600 | semibold | Page titles, card names, column headers |
| 700 | bold | Primary CTA buttons, critical status labels |

### 2.5 Brand Assets

**Wordmark / logotype**: "Huginn" set in Montserrat 700, colour `--hg-primary` (`#1f3a5f`). Used in the navbar and on the login page.

**Logo mark** (the raven):

![Huginn raven logo mark](../../static/img/Huginn.jpeg)

*File*: `static/img/Huginn.jpeg` — monochrome geometric raven, black on white.

**Usage rules**:
- Navbar: logo mark at 32 × 32 px beside the "Huginn" wordmark.
- Login page: logo mark at 64 × 64 px above the wordmark.
- Do not recolour, stretch, or place on a busy background.
- Minimum clear-space: half the logo mark's height on every side.

---

## 3. Skeleton & Layout

### 3.1 Page Shell

Every page follows this structure:

```
<navbar .hg-navbar>        ← fixed top, primary + gold accent border-bottom
<div .hg-page-header>      ← white bar: page title + subtitle + top actions (placement: §3.4)
<main .container-fluid>    ← body bg (#f5f7fa), px-4 py-3
  [page-specific content]
</main>
```

### 3.2 Layout Patterns

| Pattern | Used by | Bootstrap classes |
|---|---|---|
| **3-column card grid** | Tactical Plot | `row g-3` / `col-md-6 col-xl-4` |
| **9+3 split** (cards + rail) | Tactical Plot | `col-lg-9` / `col-lg-3` |
| **Detail tabs card** | RoE VIEW, SitAwareness VIEW | `hg-detail-tabs-card` + `nav-tabs` |
| **2-pane chat** (conversation + context) | Gjallarhorn Chat | custom flex, fixed height |
| **Single-column form** | Create / Edit screens | `col-md-8 col-lg-6`, centred |
| **Full-width table** | LIST+FIND screens | Card shell + `table-responsive` + `table-hover` (§5.2 LIST+FIND data table) |
| **Filter row → table** | LIST+FIND screens | Filter controls in a `row` directly above the table card (§5.2) |

### 3.3 Navbar CSS

```css
.hg-navbar {
  background: var(--hg-primary);
  border-bottom: 3px solid var(--hg-accent);
}
.hg-navbar .navbar-brand { color: #fff; font-weight: 600; }
.hg-navbar .navbar-brand .accent { color: var(--hg-accent); }
.hg-navbar .nav-link {
  color: rgba(255,255,255,0.82);
  padding: 0.5rem 0.9rem;
  border-radius: 4px;
  transition: background 0.12s;
}
.hg-navbar .nav-link:hover  { color: #fff; background: rgba(255,255,255,0.07); }
.hg-navbar .nav-link.active { color: #fff; background: rgba(255,255,255,0.13); }
```

### 3.4 Detail page header — primary actions (toolbar placement)

On **VIEW**, **LIST+FIND** (when a single primary CTA sits beside the title), and analogous screens, the row inside **`hg-page-header`** is a flex header:

| Rule | Detail |
|---|---|
| **Horizontal** | Title and meta on the **left**; action buttons grouped on the **right** (`justify-content-between`). |
| **Vertical** | The title block and the button group share **vertical center alignment** (`align-items-center` on the header row). Do **not** top-align the toolbar (`align-items-start`) unless there is an explicit layout exception. |
| **Toolbar semantics** | Wrap actions in `role="toolbar"` with a specific `aria-label` (e.g. `"Project actions"`, `"RoE actions"`). |
| **Responsive** | Use `flex-wrap` + `gap-3` so the toolbar wraps under the title on narrow viewports while preserving reading order. |

**Canonical reference (production):** `ui/templates/ui/projects/detail.html` — Project VIEW header.

Apply the same pattern to mockups and new surfaces (e.g. RoE VIEW, RoE list header with **New Rules of Engagement**) so detail-adjacent headers stay visually consistent with Projects.

### 3.5 List page headers — entity icon (default)

**LIST** and **LIST+FIND** screens (and the Tactical Plot index) use a single **page title row** that identifies the surface at a glance:

| Rule | Detail |
|---|---|
| **Icon + title** | The `<h1 class="hg-page-title">` is a flex row: leading Font Awesome icon + title text. Icon classes include **`hg-page-title-icon text-primary`** and **`aria-hidden="true"`** (decorative). Title words stay in a `<span>` when the `<h1>` is also `d-flex`. |
| **Nav alignment** | Prefer the **same icon** as the primary navbar entry for that surface (e.g. Plot → `fa-sharp fa-solid fa-wave-pulse`, SA → `fa-map-location-dot`, FRAGOs → `fa-puzzle`, RoE → `fa-ballot-check`, Projects → `fa-folder-open`, Data Sources → `fa-plug`). |
| **No count pill on the title row** | Do **not** place **`badge rounded-pill`** (or similar) beside the `<h1>` for row counts. Counts belong in the **subtitle** line below (`<p class="text-muted small">`), optionally wrapped in a `<span data-testid="…-count-badge">` for tests. |
| **Subtitle** | One muted line under the title: sync/meta text, count + short description, or both (e.g. `3 projects · Imported from…`). |

**References:** `ui/templates/ui/dashboard/projects.html` (Tactical Plot), `ui/templates/ui/projects/list.html` (LIST+FIND with toolbar).

### 3.6 Bulk actions bar (LIST with row selection)

Screens that combine **filters → table** with **checkbox-driven bulk operations** (e.g. FRAGO list: Revoke / Deactivate / Activate selected):

| Rule | Detail |
|---|---|
| **Placement** | Render the bulk bar **between** the filter row and the **table card** — same horizontal rhythm as the table (full content width). |
| **Alignment** | The bulk row is a flex container with **`justify-content-end`**: the label **Bulk actions:** and its buttons form a single cluster aligned to the **`inline-end`** (right in LTR). Use `flex-wrap` + `gap-2` so controls wrap cleanly on narrow viewports without overlapping the table. |
| **Button order (FRAGO bulk)** | After **Bulk actions:**, left → right (reading order): **Revoke** (destructive, outline-danger) → **Deactivate** (outline-secondary) → **Activate** (outline-success). |
| **Semantics** | Keep **`data-testid="…-bulk-bar"`** on the wrapper for integration tests; buttons remain outline variants (success / secondary / danger) per action severity. |

**Canonical reference:** `ui/templates/ui/fragos/list.html` (`fragos-bulk-bar`).

---

## 4. Navigation

### 4.1 Primary Nav Items

**Production navbar order** (`templates/base.html`): Home → Playbooks → Workflows → Phases → Activities → Artifacts → Agents → Skills → Rules → Teams → PIPs.

| Nav item | Route | Icon (`data-testid`) |
|---|---|---|
| Home | `/dashboard/` | `fa-gauge` — `nav-dashboard` |
| Playbooks | `/playbooks/` | `fa-book-sparkles` — `nav-playbooks` |
| Workflows | `/workflows/` (global list) | `fa-diagram-project` — `nav-workflows` |
| Phases | `/phases/` | `fa-bars-progress` — `nav-phases` |
| Activities | `/activities/` | `fa-list-check` — `nav-activities` |
| Artifacts | `/artifacts/` | `fa-gift` — `nav-artifacts` |
| Agents | `/agents/` | `fa-brain-circuit` — `nav-agents` |
| Skills | `/skills/` | `fa-hand-holding-magic` — `nav-skills` |
| Rules | `/rules/` | `fa-scale-balanced` — `nav-rules` |
| Teams | `/teams/` | `fa-users` — `nav-teams` |
| PIPs | `/pips/` | `fa-lightbulb` — `nav-pips` |

**Content Browser** is **not** in the navbar. Open it from **Playbook VIEW** via the Content Browser button (`data-testid="playbook-content-browser"`) → `/browser/<playbook_pk>/`. Nav highlight for browser URLs maps to **Playbooks** (`methodology.context_processors.primary_nav_section`).

**Anonymous landing** (`/`): brand + Register + Login only — no app nav items.

Right-side (authenticated): global search, notifications bell, user menu.

### 4.2 Breadcrumbs

Used on detail screens (VIEW, EDIT, CREATE nested under a parent entity):

```html
<nav aria-label="breadcrumb">
  <ol class="breadcrumb">
    <li class="breadcrumb-item"><a href="/playbooks/">Playbooks</a></li>
    <li class="breadcrumb-item active" aria-current="page">{{ playbook.name }}</li>
  </ol>
</nav>
```

### 4.3 Active State

Set `aria-current="page"` on the active nav link and add `.active` class. Active section is computed by `primary_nav_section` in `methodology/context_processors.py`.

### 4.4 Mimir-specific surfaces

| Surface | Pattern | CSS / template |
|---|---|---|
| **Playbook book-card grid** | LIST uses book-style cards (not LIST+FIND table) | `.playbook-book-*` in `static/css/mimir-app.css`; `templates/playbooks/_playbook_list_card.html` |
| **Content Browser** | Full-viewport canvas; playbook-scoped URL only | `body.mm-content-browser`, `.mm-browser-*` in `mimir-app.css`; `templates/browser/browser_graph.html` |
| **PIP status badges** | Reviewed = purple | `.pip-status-reviewed` in `mimir-app.css` |
| **Playbook create wizard** | Multi-step forms with primary card headers | `templates/playbooks/create_wizard_*.html` |
| **Marketing landing** | Full-viewport hero + MCP connect section | `body.hg-landing`, `.hg-landing-*` in `design-system.css`; `templates/methodology/index.html` |

Huginn-only domains (Tactical Plot, FRAGO, RoE, SitRep) live in the Huginn repo — do not duplicate here.

---

## 5. Component Kit

### 5.1 Atoms

#### Buttons

**Icon requirement:** Every **action control** styled as a Bootstrap button (`<button class="btn …">` or `<a class="btn …">`) includes a **leading Font Awesome icon** (`fa-solid` / `fa-regular` / `fa-brands` as appropriate) with `me-1` spacing before the label, **`aria-hidden="true"`** on decorative icons. **Icon-only** buttons use a single icon plus mandatory `aria-label` / `title` (they do not duplicate label text). Plain text links (`<a>` without `.btn`) do not require icons.

All such buttons should also carry a Bootstrap **`tooltip`** (`data-bs-toggle="tooltip"`) where it adds clarity (required actions, destructive confirmations, toolbar overflow).

```html
<!-- Primary action -->
<button class="btn btn-primary" data-bs-toggle="tooltip" title="Import projects from a connected source"
        data-testid="import-projects-btn">
  <i class="fa-solid fa-plus me-1"></i> Import Projects
</button>

<!-- Secondary / outline -->
<button class="btn btn-outline-secondary btn-sm" data-bs-toggle="tooltip" title="Refresh now"
        data-testid="refresh-btn">
  <i class="fa-solid fa-arrows-rotate me-1"></i> Refresh
</button>

<!-- Danger -->
<button class="btn btn-danger" data-bs-toggle="tooltip" title="Disconnect this data source"
        data-testid="disconnect-btn">
  <i class="fa-solid fa-plug-circle-xmark me-1"></i> Disconnect
</button>

<!-- Warning (Archive / Revoke) -->
<button class="btn btn-warning" data-testid="archive-btn">
  <i class="fa-solid fa-box-archive me-1"></i> Archive
</button>
```

Bootstrap btn overrides to apply brand primary:

```css
.btn-primary {
  --bs-btn-bg:              var(--hg-primary);
  --bs-btn-border-color:    var(--hg-primary);
  --bs-btn-hover-bg:        var(--hg-primary-700);
  --bs-btn-hover-border-color: var(--hg-primary-700);
  --bs-btn-active-bg:       var(--hg-primary-700);
}
.btn-outline-primary {
  --bs-btn-color:           var(--hg-primary);
  --bs-btn-border-color:    var(--hg-primary);
  --bs-btn-hover-bg:        var(--hg-primary);
  --bs-btn-hover-border-color: var(--hg-primary);
}
```

#### Status Badges

```html
<!-- RYG status -->
<span class="badge" style="background: var(--hg-green)">Green</span>
<span class="badge" style="background: var(--hg-red)">Red</span>

<!-- Entity state badges -->
<span class="badge bg-success">Connected</span>
<span class="badge bg-warning text-dark">Token expiring</span>
<span class="badge bg-danger">Token expired</span>
<span class="badge bg-info text-dark">Scheduled</span>
<span class="badge bg-secondary">Expired</span>
<span class="badge bg-primary">Proposed</span>
```

#### Form Inputs

```html
<div class="mb-3">
  <label for="name" class="form-label">Name <span class="text-danger">*</span></label>
  <input type="text" class="form-control" id="name" name="name"
         placeholder="e.g. company-gitlab" required
         data-testid="datasource-name-input">
  <div class="invalid-feedback">Name is required.</div>
</div>

<div class="mb-3">
  <label for="type" class="form-label">Type</label>
  <select class="form-select" id="type" name="type" data-testid="datasource-type-select">
    <option value="">— choose —</option>
    <option value="gitlab">GitLab</option>
    <option value="jira" disabled>Jira (coming soon)</option>
  </select>
</div>
```

### 5.2 Molecules

#### LIST+FIND filter row

Scoped lists (RoE, Data Sources, Projects, FRAGOs, Decisions, …) use a **single horizontal filter row** between the page header and the data table.

**Behavior (app-wide)**

| Rule | Detail |
|---|---|
| **Immediate application** | Changing a filter **reloads or narrows results right away**. Do **not** use an **Apply**, **Filter**, or **Submit** button for standard dropdown / preset filters. |
| **Implementation** | Full-page `GET` with query params, HTMX (`change` on `<select>`, debounced `input` on search fields), or client-side filtering for static mocks — the **UX contract** is the same: no separate apply step. |
| **Combined search** | When a text search sits beside dropdowns, it should also take effect as the user types (debounce ~300ms) or on Enter, **without** a dedicated Search button unless the journey explicitly calls for a heavy query. |
| **No Clear / Reset row actions** | Do **not** place **Clear**, **Clear filters**, **Clear project**, or **Reset** buttons in the filter row. Users return to the default view by choosing **All** / the first empty option / clearing typed search — same interaction model everywhere so the row never grows mystery chrome. |

**Look and feel**

| Element | Pattern |
|---|---|
| **Placement** | Directly under **`hg-page-header`**, **`mb-3`** gap, then the table **`card`**. |
| **Layout** | `row g-3` with one **`col-md-*`** per filter (equal-width columns when counts match; responsive wrap on small screens). |
| **Labels** | **`label.form-label.hg-label-caps.mb-1`** above each control — small uppercase labels with letter-spacing (§2.4). |
| **Dropdowns** | **`select.form-select.form-select-sm`** — Bootstrap chevron, compact height. On the global page background, give controls a **soft filled look** with **`bg-body-secondary`**, **`border-0`**, and **`rounded-2`** so they match the RoE LIST+FIND reference screenshot. |
| **No trailing actions** | The filter row ends with the last filter control — **no** Apply, **no** Clear/Reset, **no** extra navigation disguised as filters (those belong in the page toolbar or breadcrumbs if truly needed). |

**Markup sketch**

```html
<div class="row g-3 mb-3" role="search" aria-label="{Entity} filters">
  <div class="col-md-4">
    <label class="form-label hg-label-caps mb-1" for="{id}-author">Author</label>
    <select class="form-select form-select-sm bg-body-secondary border-0 rounded-2"
            id="{id}-author" data-testid="{entity}-filter-author">
      <option>All</option>
      <!-- … -->
    </select>
  </div>
  <!-- one column per filter -->
</div>
```

**Canonical reference (mockup):** `ui/templates/ui/mockups/roe/list.html`.

#### LIST+FIND data table (card + table)

Primary entity lists use one **visual system** so scanning columns and row actions feels the same app-wide. **Canonical mock:** RoE list (`ui/templates/ui/mockups/roe/list.html`). **Canonical production:** RoE list (`ui/templates/ui/roe/list.html`).

**Structure**

| Layer | Classes / markup |
|---|---|
| **Shell** | `<div class="card border-0 shadow-sm rounded-3">` |
| **Body** | `<div class="card-body p-0">` — **always `p-0`** so the table is flush with the card edges; empty states use their own vertical padding (`py-5`) inside this same body. |
| **Scroll** | `<div class="table-responsive" data-testid="{entity}-table-wrap">` — wrapper **inside** `card-body`, never merged into one element with `table-responsive`. |
| **Table** | `<table class="table table-hover align-middle mb-0" data-testid="{entity}-table">` |
| **Header row** | `<thead class="table-light">` with `<th scope="col">` per column. |

**Rules**

| Rule | Detail |
|---|---|
| **Hover rows** | Use **`table-hover`**. Do **not** use **`table-striped`** on LIST+FIND entity lists — it fights the hover affordance and differs from the RoE reference. |
| **Density** | Default lists use **full** `.table` (not `table-sm`) unless the screen is explicitly a dense matrix (e.g. contributors grid) where product asks for compact rows; still keep the same card / `p-0` / `table-responsive` shell. |
| **Actions column** | Narrow `<th class="text-end ps-3" scope="col" style="width:3.25rem;">` with `<span class="visually-hidden">Row actions</span>` when the column holds kebab menus (§5.2 LIST+FIND Table — primary drill-down + kebab). |
| **Secondary tables** | Detail screens, sync logs, editor grids (`table-sm`, bordered variants) are **out of scope** for this pattern unless they are the main list for an entity. |

**Markup sketch**

```html
<div class="card border-0 shadow-sm rounded-3">
  <div class="card-body p-0">
    <div class="table-responsive" data-testid="{entity}-table-wrap">
      <table class="table table-hover align-middle mb-0" data-testid="{entity}-table">
        <thead class="table-light">
          <tr>
            <th scope="col">…</th>
            <th class="text-end ps-3" scope="col" style="width:3.25rem;">
              <span class="visually-hidden">Row actions</span>
            </th>
          </tr>
        </thead>
        <tbody>…</tbody>
      </table>
    </div>
  </div>
</div>
```

#### Project Card (Tactical Plot)

```html
<article class="hg-card" data-testid="project-card">
  <div class="color-bar {red|orange|yellow|green}"></div>
  <div class="card-body">
    <h3 class="hg-card-name">
      <i class="fa-brands fa-gitlab ds-icon"></i>
      {project-name}
      <!-- optional: -->
      <span class="hg-badge-frago ms-auto">FRAGO</span>
    </h3>
    <p class="hg-headline">{headline-from-sitrep}</p>
    <!-- SitRep micro-subcard (`.hg-sitrep-subcard*` in `static/css/huginn.css`): left accent, icon tile, linked headline (2-line clamp), meta row “Last SitRep · {time}”. See `ui/templates/ui/mockups/dashboard/projects.html`. -->
    <div class="hg-var-strip" aria-label="Master Variables">
      <span class="hg-var-dot {color}" title="Transparency"></span>
      <!-- × 7 -->
      <span class="hg-var-label">T·T·C·R·Q·X·N</span>
    </div>
  </div>
  <div class="card-foot">
    <span class="hg-sync {ok|warn|err}">
      <i class="fa-solid fa-circle-check"></i> synced {N} ago
    </span>
    <span>
      <i class="fa-solid fa-ballot-check"></i> {roe-name}
      <i class="fa-solid fa-arrows-rotate" title="Auto-tracking latest"></i>
      <!-- or: <i class="fa-solid fa-thumbtack" title="Pinned to v{N}"></i> -->
    </span>
  </div>
</article>
```

CSS:

```css
.hg-card {
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
  border-radius: 8px;
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: box-shadow 0.15s, transform 0.15s;
  cursor: pointer;
}
.hg-card:hover {
  box-shadow: 0 4px 14px rgba(31, 58, 95, 0.12);
  transform: translateY(-1px);
}
.color-bar        { height: 6px; }
.color-bar.red    { background: var(--hg-red); }
.color-bar.orange { background: var(--hg-orange); }
.color-bar.yellow { background: var(--hg-yellow); }
.color-bar.green  { background: var(--hg-green); }

.card-foot {
  padding: 0.6rem 1.2rem;
  border-top: 1px solid var(--hg-border);
  background: #fafbfd;
  font-size: 0.78rem;
  display: flex; justify-content: space-between; align-items: center;
}
```

#### LIST+FIND Table — primary drill-down + kebab menu

Do **not** use a permanent strip of icon-only buttons in the Actions column (hard to scan on mobile; visually noisy). Instead:

| Rule | Detail |
|---|---|
| **Primary VIEW** | The row’s **canonical entity label** (Name, Title, Headline, Jira key, …) is a **text link** to the VIEW/detail route. Use class **`hg-list-name-link`** (see `static/css/huginn.css`). |
| **Secondary actions** | Place Edit, Clone, Import, Archive, Disconnect, etc. in a **single kebab control** (`fa-ellipsis-vertical`) opening a **Bootstrap dropdown**. |
| **Actions column header** | Omit a visible **Actions** label; use a **narrow column** with `<span class="visually-hidden">Row actions</span>` so screen readers still get a header. |
| **Dropdown clipping** | Inside `.table-responsive`, set **`data-bs-popper-config='{"strategy":"fixed"}'`** on the dropdown toggle so menus are not clipped by overflow. |
| **Destructive actions** | Put **Disconnect / Delete / Revoke** after a **divider**, with **`text-danger`** on the menu item. |
| **`role="toolbar"`** | The kebab column is not a full toolbar (single control); the toggle uses **`aria-label="Actions for {entity}"`**. |

```html
<div class="table-responsive" data-testid="{entity}-table-wrap">
  <table class="table table-hover align-middle mb-0" data-testid="{entity}-table">
    <thead class="table-light">
      <tr>
        <th scope="col">{Col1}</th>
        <th scope="col">{Col2}</th>
        <th class="text-end ps-3" scope="col" style="width:3.25rem;">
          <span class="visually-hidden">Row actions</span>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr data-testid="{entity}-row-{{ id }}">
        <td>{…}</td>
        <td>
          <a href="{detail-url}" class="hg-list-name-link fw-semibold d-inline-block"
             data-testid="{entity}-row-name-{{ id }}">{{ display_name }}</a>
        </td>
        <td class="text-end ps-3 align-middle">
          <div class="dropdown d-inline-block">
            <button type="button" class="btn btn-sm btn-outline-secondary border-0 px-2"
                    id="{entity}-row-menu-{{ id }}"
                    data-bs-toggle="dropdown"
                    data-bs-popper-config='{"strategy":"fixed"}'
                    aria-expanded="false" aria-haspopup="true"
                    aria-label="Actions for {{ display_name }}"
                    data-testid="{entity}-row-actions-{{ id }}">
              <i class="fa-solid fa-ellipsis-vertical" aria-hidden="true"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow-sm" aria-labelledby="{entity}-row-menu-{{ id }}">
              <li><a class="dropdown-item" href="{edit-url}" data-testid="{entity}-action-edit-{{ id }}">…</a></li>
              <li><hr class="dropdown-divider"></li>
              <li><a class="dropdown-item text-danger" href="{delete-url}" data-testid="{entity}-action-delete-{{ id }}">…</a></li>
            </ul>
          </div>
        </td>
      </tr>
    </tbody>
  </table>
</div>
```

**Exceptions:**

- **Dense authoring grids** (e.g. Variables / Tables rows inside CREATE/EDIT forms) may keep **inline duplicate/remove** icon pairs — that is not LIST+FIND.
- Choose whichever column is the stable human identifier per entity (RoE **Name**, FRAGO **Title**, SitRep **Headline**, …).

#### Detail VIEW — primary tabs (RoE, Project, …)

For entity VIEW screens with multiple large regions, use the **same card + tabs pattern** as Project detail (`ui/templates/ui/projects/detail.html`):

- Wrapper: **`card … hg-detail-tabs-card`**
- Tabs: **`ul.nav.nav-tabs.card-header-tabs`** with **`role="tablist"`**; each tab is an **`a.nav-link`** (full-page navigation via query string is fine for MVP).
- Panels: **`div.card-body`** with **`role="tabpanel"`** / **`aria-labelledby`** matching tab ids.

Example RoE VIEW: tabs **Rules of Engagement** (current snapshot: Metadata, Workflow, Variables, Tables, Used by) and **Versions** (immutable version log). Top toolbar stays **above** the tab card (Validate, Clone, Edit).

#### Empty State

```html
<div class="text-center py-5 text-muted" data-testid="{entity}-empty-state">
  <i class="fa-solid fa-{icon} fa-2x mb-3 d-block" style="color: var(--hg-border)"></i>
  <p class="mb-1 fw-medium">{No entities yet.}</p>
  <p class="small mb-3">{Explanatory sentence.}</p>
  <a href="{create-url}" class="btn btn-primary btn-sm" data-testid="empty-state-cta">
    <i class="fa-solid fa-plus me-1"></i> {CTA Label}
  </a>
</div>
```

#### Side Rail

```html
<aside class="hg-rail" aria-label="{Rail title}">
  <h6 class="hg-label-caps">{Section title}</h6>
  <div class="hg-rail-item {err?}">
    <i class="fa-solid fa-{icon}"></i>
    <div>
      <div class="fw-medium">{Title}</div>
      <div class="text-muted small">{Detail}</div>
    </div>
  </div>
</aside>
```

```css
.hg-rail {
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
  border-radius: 8px;
  padding: var(--hg-rail-padding);
}
.hg-rail-item {
  display: flex; gap: 0.5rem;
  padding: 0.4rem 0;
  font-size: 0.83rem;
  border-bottom: 1px dashed var(--hg-border);
}
.hg-rail-item:last-child { border-bottom: 0; }
.hg-rail-item i          { color: var(--hg-orange); margin-top: 0.12rem; flex-shrink: 0; }
.hg-rail-item.err i      { color: var(--hg-red); }
```

### 5.3 Organisms

#### Page Header

Use **`rounded-2`** on the header panel where the shell matches Projects / RoE (white bar inside `main`). Primary actions follow **§3.4** (right-aligned group, **vertically centered** with the title block).

```html
<section class="hg-page-header rounded-2 mb-3 d-flex flex-wrap align-items-center justify-content-between gap-3">
  <div class="flex-grow-1">
    <h1 class="hg-page-title mb-1">{Page Title}</h1>
    <p class="text-muted small mb-0">{subtitle · meta}</p>
  </div>
  <div class="d-flex flex-wrap gap-2 justify-content-end align-items-center flex-shrink-0"
       role="toolbar" aria-label="{Entity} actions">
    <!-- Outline / secondary actions first; primary CTA last when matching Project VIEW -->
    <button type="button" class="btn btn-outline-primary btn-sm">…</button>
    <a class="btn btn-outline-secondary btn-sm" href="#">…</a>
    <a class="btn btn-primary btn-sm" href="#">…</a>
  </div>
</section>
```

```css
.hg-page-header {
  background: var(--hg-bg-surface);
  border-bottom: 1px solid var(--hg-border);
  padding: 1rem 0;
}
```

#### Summary Strip (Tactical Plot)

```html
<div class="hg-summary-strip" role="status" aria-label="Project health summary">
  <span class="hg-pill"><span class="dot red"></span><strong>2</strong>&nbsp;red</span>
  <span class="hg-pill"><span class="dot orange"></span><strong>1</strong>&nbsp;orange</span>
  <span class="hg-pill"><span class="dot yellow"></span><strong>4</strong>&nbsp;yellow</span>
  <span class="hg-pill"><span class="dot green"></span><strong>6</strong>&nbsp;green</span>
</div>
```

```css
.hg-summary-strip { display: flex; gap: 0.65rem; flex-wrap: wrap; }
.hg-pill {
  display: inline-flex; align-items: center; gap: 0.45rem;
  padding: 0.35rem 0.8rem; border-radius: 999px;
  font-size: 0.8125rem; font-weight: 500;
  background: var(--hg-bg-surface);
  border: 1px solid var(--hg-border);
}
.hg-pill .dot { width: 0.5rem; height: 0.5rem; border-radius: 50%; }
.hg-pill .dot.red    { background: var(--hg-red); }
.hg-pill .dot.orange { background: var(--hg-orange); }
.hg-pill .dot.yellow { background: var(--hg-yellow); }
.hg-pill .dot.green  { background: var(--hg-green); }
```

---

## 6. Behavior & Interactions

### 6.1 HTMX Swap Patterns

| Trigger | `hx-target` | `hx-swap` | Notes |
|---|---|---|---|
| Filter / search form | `#table-container` | `innerHTML` | Debounced via `hx-trigger="input changed delay:300ms"`; `<select>` filters fire on **`change`** — **no Apply button** (§5.2 LIST+FIND filter row) |
| Inline form submit | `#form-container` | `outerHTML` | Replaces the whole form section on success |
| Detail panel open | `#detail-panel` | `innerHTML` | Right-rail detail in LIST+FIND screens |
| Toast (server push) | `#toast-container` | `beforeend` | Append new toast; JS auto-shows it |
| Page-level redirect | — | — | Django returns `HX-Redirect` header; HTMX follows it |

CSRF token injection (already in `base.html`):

```js
document.body.addEventListener("htmx:configRequest", (e) => {
  e.detail.headers["X-CSRFToken"] = "{{ csrf_token }}";
});
```

### 6.2 Toast Notifications

```html
<div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3" aria-live="polite">
  <!-- Success -->
  <div class="toast align-items-center text-bg-success border-0 show" role="alert"
       data-bs-autohide="true" data-bs-delay="4000" data-testid="success-toast">
    <div class="d-flex">
      <div class="toast-body">
        <i class="fa-solid fa-circle-check me-2"></i> {Message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  </div>

  <!-- Error -->
  <div class="toast align-items-center text-bg-danger border-0 show" role="alert"
       data-testid="error-toast">
    <div class="d-flex">
      <div class="toast-body">
        <i class="fa-solid fa-circle-exclamation me-2"></i> {Message}
      </div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  </div>
</div>
```

### 6.3 Confirmation Modals

Used for destructive actions (Delete, Disconnect, Archive, Revoke).

```html
<div class="modal fade" id="{action}Modal" tabindex="-1" aria-labelledby="{action}ModalLabel"
     data-testid="{action}-modal">
  <div class="modal-dialog">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="{action}ModalLabel">{Confirm Action}?</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
      </div>
      <div class="modal-body">
        <p>{Consequence sentence. What happens next.}</p>
        <!-- Optional: secondary detail in muted text -->
        <p class="text-muted small">{e.g. "N project(s) will be orphaned."}</p>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
        <button type="button" class="btn btn-{danger|warning}" data-testid="{action}-confirm-btn">
          <i class="fa-solid fa-{icon} me-1"></i> {Action Label}
        </button>
      </div>
    </div>
  </div>
</div>
```

### 6.4 Loading / Empty / Error States

Every list and data section must handle all three:

| State | Pattern |
|---|---|
| Loading | `<div class="spinner-border spinner-border-sm text-secondary" role="status">` inside the target container |
| Empty | `.hg-empty-state` component (§5.2) |
| Error | Inline `<div class="alert alert-danger" role="alert">` with error message and retry option |

---

## 7. Icon System — Font Awesome Free

**Only `fa-solid` (filled) as primary style.** `fa-regular` available for a limited free subset; `fa-brands` for logos.

### 7.1 Standard Icon Mapping

| Action / Concept | Icon class | Notes |
|---|---|---|
| Create / Add | `fa-plus` | |
| Edit | `fa-pen` | |
| View / Inspect | `fa-eye` | |
| Delete | `fa-trash` | |
| Archive | `fa-box-archive` | |
| Revoke | `fa-ban` | |
| Save | `fa-floppy-disk` | |
| Cancel | `fa-xmark` | |
| Search | `fa-magnifying-glass` | |
| Filter | `fa-filter` | |
| Refresh / Sync | `fa-arrows-rotate` | |
| Import | `fa-file-import` | |
| Tactical Plot | `fa-grip-vertical` | |
| Project | `fa-folder-open` | |
| RoE | `fa-ballot-check` | |
| Data Source | `fa-plug` | |
| FRAGO | `fa-flag` | |
| Decision | `fa-gavel` | |
| SitRep | `fa-display-chart-up-circle-currency` | |
| Variables | `fa-chart-line` | |
| Contributors | `fa-users` | |
| Action Stations | `fa-list-check` | |
| Chat / Gjallarhorn | `fa-comments` | |
| Situational Awareness | `fa-map-location-dot` | |
| Status: OK / Connected | `fa-circle-check` | green |
| Status: Warning | `fa-triangle-exclamation` | orange |
| Status: Error | `fa-circle-exclamation` | red |
| Status: Syncing | `fa-circle-half-stroke fa-spin` | |
| Auto-tracking | `fa-arrows-rotate` | small, muted |
| Pinned version | `fa-thumbtack` | small, muted |
| GitLab | `fa-brands fa-gitlab` | |
| GitHub | `fa-brands fa-github` | |
| Jira | `fa-brands fa-jira` | |
| User | `fa-circle-user` | |
| Crow (brand) | `fa-crow` | navbar brand only |

### 7.2 Icon Usage Rules

- **Buttons:** Normative rule — §5.1 Buttons (leading FA icon on every `.btn`, except icon-only controls).
- Icon-only buttons (table row actions) **must** have a `title` tooltip and `aria-label`.
- Use `me-1` margin between icon and label text.
- Never use icons for purely decorative purposes without `aria-hidden="true"`.

---

## 8. Charts — Apache ECharts

### 8.1 Data Pattern

Charts are data-driven. Django views return JSON; the template initialises the chart:

```python
# views/analytics.py
def variables_json(request, project_id):
    data = compute_throughput_series(project_id)
    return JsonResponse({"dates": data["dates"], "values": data["values"]})
```

```html
<!-- template -->
<div id="throughput-chart" style="height: 260px;" data-testid="throughput-chart"
     data-src="{% url 'variables-json' project.id %}"></div>

<script>
  const chart = echarts.init(document.getElementById("throughput-chart"));
  fetch(document.getElementById("throughput-chart").dataset.src)
    .then(r => r.json())
    .then(data => chart.setOption({ /* option */ }));
</script>
```

Tests assert on the JSON endpoint response — no browser rendering required.

### 8.2 Palette in Charts

Use token values in ECharts options:

```js
const HG = {
  primary: "#1f3a5f",
  red:     "#dc3545",
  orange:  "#fd7e14",
  yellow:  "#ffc107",
  green:   "#198754",
  muted:   "#5a6478",
  border:  "#e3e7ee",
};
```

Standard series colours (in order): `HG.primary`, `HG.green`, `HG.orange`, `HG.red`, `HG.yellow`.

### 8.3 Chart Conventions

- **Grid**: minimal — `left: "5%"`, `right: "3%"`, `containLabel: true`.
- **Tooltip**: `trigger: "axis"`, dark background (`backgroundColor: HG.primary`).
- **Legend**: top-right, small font.
- **X-axis**: date strings, `axisLabel.color: HG.muted`.
- **Y-axis**: no border, `splitLine.lineStyle.color: HG.border`.
- **Responsive**: call `chart.resize()` on window resize.

---

## 9. Accessibility

### 9.1 Semantic HTML

| Context | Element |
|---|---|
| Top navigation | `<nav aria-label="Primary navigation">` |
| Page main content | `<main>` |
| Side rail | `<aside aria-label="{rail title}">` |
| Article card | `<article>` |
| Data table | `<table>` with `<caption>` or `aria-label` |
| Status summary | `role="status"` or `aria-live="polite"` |

### 9.2 ARIA Requirements

- All icon-only buttons: `aria-label="{action}"`.
- All form inputs: `<label>` explicitly linked via `for`/`id`.
- Dynamic content updated via HTMX: wrap in `aria-live="polite"` region.
- Modal dialogs: `aria-labelledby` pointing to modal title; `tabindex="-1"` on `.modal`.
- Status badges that convey meaning via colour alone: add `aria-label` with text value.

### 9.3 Keyboard Navigation

- Tab order follows visual reading order.
- Modals trap focus while open (Bootstrap handles this).
- Dropdown menus navigable via arrow keys (Bootstrap handles this).
- Custom components (e.g. variable mini-strip) must have a text alternative (`aria-label` on the container).

### 9.4 Contrast

| Pair | Ratio target |
|---|---|
| Body text on surface | ≥ 4.5:1 (WCAG AA) |
| `--hg-ink` (#1a1f2e) on white | 16.6:1 ✓ |
| White on `--hg-primary` (#1f3a5f) | 8.2:1 ✓ |
| `--hg-ink-muted` (#5a6478) on white | 4.9:1 ✓ |
| Status badges (white text on status colour) | verify per badge; red/green/orange pass at ≥ 3:1 for large text |

---

## 10. Screen ID Convention

### 10.1 Format

```
{ENTITY}-{OPERATION}-{VERSION}
```

- `{ENTITY}` — uppercase entity name: `PLAYBOOKS`, `WORKFLOWS`, `ACTIVITIES`, `PHASES`, `ARTIFACTS`, `AGENTS`, `SKILLS`, `RULES`, `PIPS`, `TEAMS`, `BROWSER`, `AUTH`, `DASHBOARD`
- `{OPERATION}` — operation type (see §10.2)
- `{VERSION}` — integer, starts at `1`

**Mimir prefix:** Feature specs may use `FOB-` or act prefixes in feature files; screen IDs in templates follow `{ENTITY}-{OPERATION}-{VERSION}`.

### 10.2 Operations

Standard CRUDLF:

| Operation | Pattern | Example |
|---|---|---|
| `LIST+FIND` | List with search/filter — entry point | `PROJECTS-LIST+FIND-1` |
| `CREATE_{ENTITY}` | Creation form | `PLAYBOOKS-CREATE_PLAYBOOK-1` |
| `VIEW_{ENTITY}` | Read-only detail | `SITREP-VIEW_SITREP-1` |
| `EDIT_{ENTITY}` | Edit form | `FRAGOS-EDIT_FRAGO-1` |
| `DELETE_{ENTITY}` | Deletion confirmation | `PLAYBOOKS-DELETE_PLAYBOOK-1` |

Huginn extensions (established in `user_journey.md` §System Architecture Notes):

| Operation | Used by | Example |
|---|---|---|
| `IMPORT` | Projects | `PROJECTS-IMPORT-1` |
| `ARCHIVE_{ENTITY}` | Projects | `PROJECTS-ARCHIVE_PROJECT-1` |
| `REVOKE_{ENTITY}` | FRAGOs | `FRAGOS-REVOKE_FRAGO-1` |
| `VIEW` (no entity suffix) | SituationalAwareness, Variables | `VARIABLES-VIEW-1` |
| `EDIT` (no entity suffix) | SituationalAwareness | `SITAWARENESS-EDIT-1` |
| `CHAT` | Gjallarhorn | `CHAT-1` |
