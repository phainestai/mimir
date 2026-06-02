/**
 * content-browser.js — Content Browser client-side logic.
 *
 * Responsibilities:
 *   1. Read playbook PK from DOM on init
 *   2. Manage URL state via History API (pushState / replaceState)
 *   3. Normalise URL params on load (drop unknown types, drop stale phase IDs)
 *   4. Fetch graph data from /api/playbooks/<pk>/graph/ (implemented in graph iteration)
 *   5. Initialise Cytoscape.js and render graph (implemented in graph iteration)
 *
 * This file is plain browser JS. No build step, no framework, no import/export.
 * Loaded via <script> tag in browser_graph.html after CDN guard check.
 */

'use strict';

const _ALL_TYPES = ['workflow', 'activity', 'skill', 'agent', 'artifact', 'rule', 'phase'];

// ─── Module-level filter + search state ──────────────────────────────────────
// Mutated by _applyFilters / _applySearch; read by _openDetailPanel / _closeDetailPanel.
let _currentFilters = { types: _ALL_TYPES.slice(), phases: [] };

/**
 * Full graph element snapshot from the last successful API fetch.
 * Used as the authoritative source when rebuilding cy after entity-type filter changes.
 * Shape: { nodes: object[], edges: object[] }
 *
 * @type {{ nodes: object[], edges: object[] } | null}
 */
let _fullGraphData = null;
let _currentSearchTerm = '';
let _searchDebounceTimer = null;
let _currentLayout = 'elk-layered'; // layout key — see _LAYOUT_CATALOG

/**
 * Full layout catalog used by the layout picker dropdown (FOB-19, FOB-34).
 * Each entry: { key, label, group }  — key is also the URL param value.
 * TODO S34: implement _applyLayout() to dispatch on these keys.
 */
const _LAYOUT_CATALOG = [
  // ELK sub-algorithms (elkjs already loaded)
  { key: 'elk-layered',   label: 'Layered',      group: 'ELK',          groupSlug: 'elk' },
  { key: 'elk-mrtree',    label: 'Tree',          group: 'ELK',          groupSlug: 'elk' },
  { key: 'elk-force',     label: 'Force',         group: 'ELK',          groupSlug: 'elk' },
  { key: 'elk-stress',    label: 'Stress',        group: 'ELK',          groupSlug: 'elk' },
  { key: 'elk-disco',         label: 'Disco',          group: 'ELK', groupSlug: 'elk' },
  { key: 'elk-radial',        label: 'Radial',         group: 'ELK', groupSlug: 'elk' },
  { key: 'elk-rectpacking',   label: 'Rect Packing',   group: 'ELK', groupSlug: 'elk' },
  { key: 'elk-sporeOverlap',  label: 'SPORE Overlap',  group: 'ELK', groupSlug: 'elk' },
  { key: 'elk-sporeCompaction', label: 'SPORE Compact', group: 'ELK', groupSlug: 'elk' },
  // Dagre (dagre + cytoscape-dagre already loaded)
  { key: 'dagre-tb',      label: 'Top-Down',      group: 'Dagre',        groupSlug: 'dagre' },
  { key: 'dagre-lr',      label: 'Left-Right',    group: 'Dagre',        groupSlug: 'dagre' },
  // Third-party extensions (CDN — added to browser_graph.html)
  { key: 'cola',          label: 'Cola',          group: 'Cola',         groupSlug: 'cola' },
  { key: 'klay',          label: 'Klay',          group: 'Klay',         groupSlug: 'klay' },
  { key: 'cise',          label: 'CiSE',          group: 'CiSE',         groupSlug: 'cise' },
  { key: 'euler',         label: 'Euler',         group: 'Euler',        groupSlug: 'euler' },
  { key: 'avsdf',         label: 'AVSDF',         group: 'AVSDF',        groupSlug: 'avsdf' },
  { key: 'cose-bilkent',  label: 'CoSE-Bilkent',  group: 'CoSE-Bilkent', groupSlug: 'cose-bilkent' },
  { key: 'fcose',         label: 'fCoSE',         group: 'fCoSE',        groupSlug: 'fcose' },
  // Native Cytoscape layouts (already loaded)
  { key: 'cy-grid',         label: 'Grid',          group: 'Cytoscape',  groupSlug: 'cy' },
  { key: 'cy-circle',       label: 'Circle',        group: 'Cytoscape',  groupSlug: 'cy' },
  { key: 'cy-concentric',   label: 'Concentric',    group: 'Cytoscape',  groupSlug: 'cy' },
  { key: 'cy-breadthfirst', label: 'Breadth-first', group: 'Cytoscape',  groupSlug: 'cy' },
  { key: 'cy-cose',         label: 'CoSE',          group: 'Cytoscape',  groupSlug: 'cy' },
  { key: 'cy-random',       label: 'Random',        group: 'Cytoscape',  groupSlug: 'cy' },
];

/**
 * Return Cytoscape layout options object for the given layout key.
 * Used both for initial cy creation and for re-run via _runLayout().
 *
 * @param {string} key  — one of the keys in _LAYOUT_CATALOG
 * @returns {object} Cytoscape layout config
 */
function _buildLayoutOptions(key) {
  if (key.startsWith('elk-')) {
    return {
      name: 'elk',
      elk: {
        algorithm: key.slice(4),
        'elk.direction': 'DOWN',
        'elk.edgeRouting': 'ORTHOGONAL',
        'elk.layered.nodePlacement.strategy': 'BRANDES_KOEPF',
        'elk.spacing.nodeNode': 50,
        'elk.layered.spacing.nodeNodeBetweenLayers': 70,
        'elk.layered.crossingMinimization.strategy': 'LAYER_SWEEP',
      },
      padding: 30,
    };
  }
  if (key === 'dagre-tb') {
    return { name: 'dagre', rankDir: 'TB', nodeSep: 50, rankSep: 70, edgeSep: 10, ranker: 'network-simplex', padding: 30 };
  }
  if (key === 'dagre-lr') {
    return { name: 'dagre', rankDir: 'LR', nodeSep: 50, rankSep: 70, edgeSep: 10, ranker: 'network-simplex', padding: 30 };
  }
  if (key.startsWith('cy-')) {
    return { name: key.slice(3), padding: 30, animate: false };
  }
  // Extension layouts: cola, klay, cise, euler, avsdf, cose-bilkent, fcose
  return { name: key, padding: 30 };
}

/**
 * Apply a layout by key: update _currentLayout, update button, update URL, re-run layout.
 * Ignores unknown keys.
 * @param {string} key  — one of the keys in _LAYOUT_CATALOG
 */
function _applyLayout(key) {
  if (!_LAYOUT_CATALOG.some(e => e.key === key)) return;
  _currentLayout = key;
  _updateLayoutBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  _runLayout();
}

/**
 * Toggle the layout picker dropdown open/closed.
 * Appended to document.body (fixed position) to avoid overflow clipping from canvas wrapper.
 */
function _toggleLayoutDropdown() {
  const existing = document.querySelector('[data-testid="browser-layout-dropdown"]');
  if (existing) { existing.remove(); return; }

  const btn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (!btn) return;

  const panel = document.createElement('div');
  panel.setAttribute('data-testid', 'browser-layout-dropdown');
  const rect = btn.getBoundingClientRect();
  panel.style.cssText =
    `position:fixed;bottom:${window.innerHeight - rect.top + 4}px;right:${window.innerWidth - rect.right}px;` +
    'z-index:1050;background:#fff;border:1px solid rgba(0,0,0,.15);border-radius:6px;' +
    'box-shadow:0 4px 16px rgba(0,0,0,.15);padding:4px 0;min-width:180px;max-height:60vh;overflow-y:auto;';

  // Build grouped content from _LAYOUT_CATALOG.
  const seenGroups = [];
  _LAYOUT_CATALOG.forEach(e => {
    if (!seenGroups.some(g => g.slug === e.groupSlug)) {
      seenGroups.push({ slug: e.groupSlug, name: e.group });
    }
  });

  seenGroups.forEach(g => {
    const header = document.createElement('div');
    header.setAttribute('data-testid', `browser-layout-group-${g.slug}`);
    header.style.cssText = 'padding:4px 12px 2px;font-size:0.7rem;font-weight:600;color:#6c757d;text-transform:uppercase;letter-spacing:0.05em;';
    header.textContent = g.name;
    panel.appendChild(header);

    _LAYOUT_CATALOG.filter(e => e.groupSlug === g.slug).forEach(entry => {
      const item = document.createElement('button');
      item.setAttribute('data-testid', `browser-layout-option-${entry.key}`);
      item.type = 'button';
      const isActive = _currentLayout === entry.key;
      item.style.cssText =
        'display:block;width:100%;padding:4px 20px;text-align:left;border:none;cursor:pointer;font-size:0.85rem;' +
        (isActive ? 'background:#e9ecef;font-weight:600;' : 'background:transparent;');
      item.textContent = entry.label + (isActive ? ' ✓' : '');
      item.addEventListener('click', () => {
        panel.remove();
        document.removeEventListener('keydown', escHandler);
        document.removeEventListener('click', outsideHandler);
        _applyLayout(entry.key);
      });
      panel.appendChild(item);
    });
  });

  document.body.appendChild(panel);

  const escHandler = (e) => {
    if (e.key === 'Escape') {
      panel.remove();
      document.removeEventListener('keydown', escHandler);
      document.removeEventListener('click', outsideHandler);
    }
  };
  const outsideHandler = (e) => {
    if (!panel.contains(e.target) && e.target !== btn) {
      panel.remove();
      document.removeEventListener('keydown', escHandler);
      document.removeEventListener('click', outsideHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
  // Defer outside-click handler to avoid immediately closing on the triggering click.
  setTimeout(() => document.addEventListener('click', outsideHandler), 0);
}

/**
 * Read the playbook PK from the #browser-root data attribute.
 * Returns null if no PK is set (empty state: /browser/).
 *
 * @returns {number|null}
 */
function _getPlaybookPk() {
  const root = document.getElementById('browser-root');
  const raw = root ? root.dataset.playbookPk : '';
  return raw ? parseInt(raw, 10) : null;
}

/**
 * Read the phase list from the #browser-root data-playbook-phases attribute.
 * Returns an array of {id, name} objects.
 *
 * @returns {{ id: number, name: string }[]}
 */
function _getPlaybookPhases() {
  const root = document.getElementById('browser-root');
  try {
    return JSON.parse(root ? root.dataset.playbookPhases || '[]' : '[]');
  } catch (_) {
    return [];
  }
}

/**
 * Parse URL query params into a structured filters object.
 * Normalises on read:
 *   - Unknown type values are discarded
 *   - Empty types param → all entity types active (not zero)
 *   - Phase IDs that are not positive integers are discarded
 *
 * @returns {{ types: string[], phases: number[] }}
 */
function _parseUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const typesRaw = params.get('types');
  const phasesRaw = params.get('phases');
  const layoutRaw = params.get('layout');

  let types;
  if (typesRaw === null || typesRaw === '') {
    types = _ALL_TYPES.slice();
  } else {
    types = typesRaw.split(',').filter(t => _ALL_TYPES.includes(t));
    if (types.length === 0) types = _ALL_TYPES.slice();
  }

  const phases = phasesRaw
    ? phasesRaw.split(',')
        .map(s => parseInt(s, 10))
        .filter(n => Number.isFinite(n) && n >= 0)
    : [];

  const legacyMap = { layered: 'elk-layered', mrtree: 'elk-mrtree' };
  const resolvedLayout = (layoutRaw && legacyMap[layoutRaw]) || layoutRaw;
  if (resolvedLayout && _LAYOUT_CATALOG.some(e => e.key === resolvedLayout)) {
    _currentLayout = resolvedLayout;
  }

  _parseRoutingParam();
  _parseSeqParam();
  _parseCompoundParam();

  return { types, phases };
}

/**
 * Validate parsed filters against the loaded playbook data.
 * Drops phase IDs not present in the playbook's phases array.
 * Rewrites the URL to canonical form (removes invalid/default params).
 *
 * @param {{ types: string[], phases: number[] }} filters
 * @param {{ id: number, name: string }[]} playbookPhases
 * @returns {{ types: string[], phases: number[] }} validated filters
 */
function _normaliseFilters(filters, playbookPhases) {
  const validPhaseIds = new Set(playbookPhases.map(p => p.id));
  // 0 is the "Unphased" sentinel — always valid when the playbook has ≥1 phase.
  const hasPhases = playbookPhases.length > 0;
  const cleanPhases = filters.phases.filter(id => (id === 0 && hasPhases) || validPhaseIds.has(id));
  const normalised = { types: filters.types, phases: cleanPhases };
  _replaceCanonicalUrl(_getPlaybookPk(), normalised);
  return normalised;
}

/**
 * Serialise a filters object back to URL query string.
 * Clean URL rules: omit types param if all entity types are active;
 * omit phases param if no phase filter is active.
 *
 * @param {{ types: string[], phases: number[] }} filters
 * @returns {string} query string including leading '?' or '' if empty
 */
function _filtersToQueryString(filters) {
  const parts = [];
  const FILTERABLE = ['workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
  const allActive = FILTERABLE.every(t => filters.types.includes(t));
  if (!allActive && filters.types.length > 0) {
    const encodable = filters.types.filter(t => FILTERABLE.includes(t));
    if (encodable.length > 0 && encodable.length < FILTERABLE.length) {
      parts.push('types=' + encodable.join(','));
    }
  }
  if (filters.phases.length > 0) {
    parts.push('phases=' + filters.phases.join(','));
  }
  if (_currentLayout !== 'elk-layered') {
    parts.push('layout=' + _currentLayout);
  }
  if (_currentRouting !== 'bezier') {
    parts.push('routing=' + _currentRouting);
  }
  if (!_seqEdgesOn) {
    parts.push('seq=0');
  }
  if (_compoundViewOn) {
    parts.push('compound=1');
  }
  return parts.length ? '?' + parts.join('&') : '';
}

/**
 * Update the browser URL when the active playbook changes.
 * Uses pushState so the back button returns to the previous playbook.
 * Resets phase filters on switch (phase IDs are playbook-scoped).
 *
 * @param {number} pk - New playbook PK
 * @param {{ types: string[], phases: number[] }} filters - Current filter state
 */
function _pushPlaybookUrl(pk, filters) {
  const resetFilters = { types: filters.types, phases: [] };
  const qs = _filtersToQueryString(resetFilters);
  const url = '/browser/' + pk + '/' + qs;
  history.pushState({ pk: pk, filters: resetFilters }, '', url);
}

/**
 * Replace the current URL with the canonical form of the current state.
 * Used during init to clean up invalid params without creating a history entry.
 *
 * @param {number|null} pk
 * @param {{ types: string[], phases: number[] }} filters
 */
function _replaceCanonicalUrl(pk, filters) {
  const qs = _filtersToQueryString(filters);
  const url = pk ? '/browser/' + pk + '/' + qs : '/browser/';
  history.replaceState({ pk: pk, filters: filters }, '', url);
}

/**
 * Handle browser back/forward navigation (popstate event).
 * Reads the new URL state and re-fetches graph or shows empty state.
 *
 * @param {PopStateEvent} event
 */
function _onPopState(event) {
  const pk = _getPkFromPath();
  if (!pk) {
    _showEmptyState();
    return;
  }
  const filters = _parseUrlParams();
  _fetchGraph(pk).then(() => _applyFilters(filters));
}

/**
 * Extract playbook PK from the current URL path.
 * @returns {number|null}
 */
function _getPkFromPath() {
  const match = window.location.pathname.match(/^\/browser\/(\d+)\/$/);
  return match ? parseInt(match[1], 10) : null;
}

/**
 * Show the empty state canvas card (no playbook selected).
 */
function _showEmptyState() {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (empty) empty.classList.remove('d-none');
  if (loading) loading.classList.add('d-none');
  if (error) error.classList.add('d-none');
}

/**
 * Show the loading spinner on the canvas.
 */
function _showLoadingState() {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (empty) empty.classList.add('d-none');
  if (loading) loading.classList.remove('d-none');
  if (error) error.classList.add('d-none');
}

/**
 * Show the error state canvas card with an optional message.
 *
 * @param {string} [message='Could not load graph data.']
 */
function _showErrorState(message) {
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const errorEl = document.querySelector('[data-testid="browser-error-state"]');
  const msgEl = errorEl ? errorEl.querySelector('p') : null;
  if (empty) empty.classList.add('d-none');
  if (loading) loading.classList.add('d-none');
  if (errorEl) {
    errorEl.classList.remove('d-none');
    if (msgEl) msgEl.textContent = message || 'Could not load graph data.';
  }
}

// AbortController for in-flight graph fetch — aborted on playbook switch.
let _currentAbortController = null;

/**
 * Fetch graph data from the API, show loading state first, render on success.
 * Handles: 401 (session expired → redirect to login), 404, network errors.
 * On a transient JSON 401 (DRF auth failure, e.g. brief session lock), retries
 * once after 400 ms before giving up and redirecting to login.
 *
 * @param {number} pk
 * @param {boolean} [_retry=false] - internal flag; true on the single retry attempt
 */
async function _fetchGraph(pk, _retryCount = 0) {
  if (_currentAbortController) {
    _currentAbortController.abort();
  }
  _currentAbortController = new AbortController();
  _showLoadingState();

  try {
    const response = await fetch(`/api/playbooks/${pk}/graph/`, {
      signal: _currentAbortController.signal,
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });

    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      // Non-JSON response usually means Django returned a login redirect page.
      window.location.href = '/auth/user/login/?next=' + encodeURIComponent('/browser/' + pk + '/');
      return;
    }
    if (response.status === 401) {
      if (_retryCount < 3) {
        // Transient session miss (e.g. concurrent DB write on page load) — retry with backoff.
        await new Promise((r) => setTimeout(r, 600 * (_retryCount + 1)));
        return _fetchGraph(pk, _retryCount + 1);
      }
      window.location.href = '/auth/user/login/?next=' + encodeURIComponent('/browser/' + pk + '/');
      return;
    }
    if (response.status === 404) {
      _showErrorState('This playbook is no longer available.');
      return;
    }
    if (!response.ok) {
      _showErrorState('Could not load graph data.');
      return;
    }

    const data = await response.json();
    _fullGraphData = { nodes: data.nodes || [], edges: data.edges || [] };
    const filters = _parseUrlParams();
    _renderGraph(pk, data, filters);
    _updatePlaybookHeader(pk, data.playbook_name || '', data.playbook_status || '');
  } catch (err) {
    if (err.name === 'AbortError') return;
    _showErrorState('Could not load graph data.');
  }
}

/**
 * Initialise (or re-initialise) Cytoscape with fetched graph data.
 * Destroys any existing cy instance before mounting a new one.
 *
 * @param {number} pk - Playbook PK (used for "Go to Playbook" link)
 * @param {{ nodes: object[], edges: object[], phases: object[] }} graphData
 * @param {{ types: string[], phases: number[] }} filters
 */
function _renderGraph(pk, graphData, filters) {
  if (window.cy) {
    window.cy.destroy();
    window.cy = null;
  }

  const container = document.getElementById('cy');
  if (!container) return;

  const { nodes, edges } = graphData;

  // Empty playbook — show no-content state, not the canvas.
  if (nodes.length === 0) {
    _showNoContentState(pk);
    return;
  }

  // Node count badge (always shows total, not filtered).
  const countBadge = document.querySelector('[data-testid="browser-node-count"]');
  if (countBadge) countBadge.textContent = `${nodes.length} nodes`;

  // Build initial elements respecting URL type-filter params so the first render
  // is already correct — avoids a redundant remove+re-add cycle after cy creation.
  _currentFilters = filters;
  const activeTypesSet = new Set(filters.types);
  const elements = _compoundViewOn ? _buildCompoundElements(activeTypesSet) : _buildFilteredElements(activeTypesSet);
  const initialStyle = _compoundViewOn
    ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyle())
    : _cytoscapeStyleEnhanced();

  // Create cy without an initial layout — positions will be set by the explicit _runLayout()
  // call below (after listeners are registered). This avoids double-layout for async engines
  // (ELK) and missed-layoutstop for sync engines (Dagre, native Cytoscape layouts).
  window.cy = cytoscape({
    container, elements, style: initialStyle,
    layout: { name: 'null' },
    minZoom: 0.1, maxZoom: 3,
  });

  // Hide overlay states, make canvas visible.
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const noContent = document.querySelector('[data-testid="browser-no-content-state"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (loading) loading.classList.add('d-none');
  if (empty) empty.classList.add('d-none');
  if (noContent) noContent.classList.add('d-none');
  if (error) error.classList.add('d-none');

  // Wire node tap → detail panel.
  window.cy.on('tap', 'node', function(evt) { _openDetailPanel(evt.target); });
  // Canvas background tap → close panel; edges do nothing.
  window.cy.on('tap', function(evt) {
    if (evt.target === window.cy) { _closeDetailPanel(); }
  });
  // Track layout completion count (used by E2E tests to wait for any layout to finish).
  window.cy.on('layoutstop', function() {
    window._elkLayoutCount = (window._elkLayoutCount || 0) + 1;
  });

  // Re-run layout explicitly so the layoutstop listener above always fires at least once.
  // Sync layouts (e.g. Dagre) fire layoutstop during the cytoscape() constructor, before
  // the listener above is registered — this call ensures they are also tracked.
  _runLayout();

  // Apply phase/search dim (no type rebuild — cy was created with correct elements).
  _refreshVisualState();

  // Render entity-type filter toolbar after graph loads (counts won't change).
  _renderFilterToolbar(filters);
}

/**
 * Return the Cytoscape stylesheet array.
 * Node labels are set via 'content' property (plain text — no innerHTML).
 *
 * @returns {object[]}
 */
function _cytoscapeStyle() {
  const _nodeBase = {
    'label': 'data(label)',
    'text-valign': 'center',
    'text-halign': 'center',
    'font-size': 11,
    'text-wrap': 'wrap',
    'text-max-width': 110,
    'width': 120,
    'height': 40,
    'color': '#fff',
  };
  return [
    { selector: 'node[type = "workflow"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const abbr = ele.data('meta') && ele.data('meta').abbreviation;
                 return abbr ? `${abbr}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': '#0d6efd', 'shape': 'round-rectangle',
               'width': 130, 'height': 50, 'font-size': 10 } },
    { selector: 'node[type = "activity"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const code = ele.data('meta') && ele.data('meta').display_code;
                 return code ? `${code}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': '#198754', 'shape': 'round-rectangle',
               'height': 50, 'font-size': 10, 'text-max-width': 110 } },
    { selector: 'node[type = "artifact"]',
      style: { ..._nodeBase, 'background-color': '#ffc107', 'shape': 'ellipse', 'color': '#212529' } },
    { selector: 'node[type = "skill"]',
      style: { ..._nodeBase, 'background-color': '#fd7e14', 'shape': 'ellipse' } },
    { selector: 'node[type = "agent"]',
      style: { ..._nodeBase, 'background-color': '#0dcaf0', 'shape': 'ellipse', 'color': '#212529' } },
    { selector: 'node[type = "rule"]',
      style: { ..._nodeBase, 'background-color': '#6c757d', 'shape': 'ellipse' } },
    { selector: 'node:selected',
      style: { 'border-width': 3, 'border-color': '#dc3545' } },
    // Edges — taxi (right-angle) routing for clean hierarchical layout.
    // 'contains' and 'predecessor' use downward/auto taxi; resource edges use
    // a shorter turn so they branch off activities cleanly.
    { selector: 'edge[relationship = "contains"]',
      style: { 'line-color': '#0d6efd', 'target-arrow-color': '#0d6efd', 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%', 'width': 2 } },
    { selector: 'edge[relationship = "predecessor"]',
      style: { 'line-color': '#198754', 'target-arrow-color': '#198754', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'auto', 'taxi-turn': '50%',
               'width': 1, 'opacity': 0.7 } },
    { selector: 'edge[relationship = "sequence"]',
      style: { 'line-color': '#343a40', 'target-arrow-color': '#343a40', 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%',
               'width': 2, 'opacity': 0.55 } },
    { selector: 'edge[relationship = "produces"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "consumes"]',
      style: { 'line-color': '#ffc107', 'target-arrow-color': '#ffc107', 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5, 'opacity': 0.8 } },
    { selector: 'edge[relationship = "uses_skill"]',
      style: { 'line-color': '#fd7e14', 'target-arrow-color': '#fd7e14', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "assigned_agent"]',
      style: { 'line-color': '#0dcaf0', 'target-arrow-color': '#0dcaf0', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "governed_by_rule"]',
      style: { 'line-color': '#6c757d', 'target-arrow-color': '#6c757d', 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
  ];
}

/**
 * Apply filter state to the graph.
 * Stores state to _currentFilters and calls _refreshVisualState.
 * Also closes detail panel if the currently-selected node's type is now hidden.
 *
 * @param {{ types: string[], phases: number[] }} filters
 */
function _applyFilters(filters) {
  _currentFilters = filters;
  _applyTypeRebuild(new Set(filters.types));
  _refreshVisualState();
  // Close panel if the selected node's type is now excluded.
  if (_currentPanelNode) {
    const activeTypes = new Set(filters.types);
    if (!activeTypes.has(_currentPanelNode.data('type'))) {
      _closeDetailPanel();
    }
  }
}

/**
 * Rebuild the Cytoscape element set to include only nodes of the active types,
 * plus any edges whose both endpoints are in the active set.
 * After rebuilding, automatically re-runs the current ELK layout.
 *
 * Only entity-type filtering causes a rebuild. Phase filter and search use
 * the dim model (_refreshVisualState) and do NOT trigger a rebuild.
 *
 * @param {Set<string>} activeTypes - set of type strings that should be present in cy
 */
function _applyTypeRebuild(activeTypes) {
  if (!window.cy || !_fullGraphData) return;
  const elements = _buildFilteredElements(activeTypes);
  window.cy.remove(window.cy.elements());
  window.cy.add(elements);
  _runLayout();
}

/**
 * From _fullGraphData, return the Cytoscape element array (nodes + edges) for
 * the given set of active types. Orphaned resource nodes (nodes whose type is
 * active but whose Activity parent was excluded) are also removed.
 *
 * @param {Set<string>} activeTypes
 * @returns {{ data: object }[]}
 */
function _buildFilteredElements(activeTypes) {
  if (!_fullGraphData) return [];
  const { nodes, edges } = _fullGraphData;
  const resourceTypes = new Set(['skill', 'agent', 'rule', 'artifact']);

  // Step 1: Keep nodes whose type is active.
  const typeFilteredNodes = nodes.filter(n => activeTypes.has(n.type));
  const typeFilteredIds = new Set(typeFilteredNodes.map(n => n.id));

  // Step 2: Filter edges — both endpoints must remain.
  const typeEdges = edges.filter(e => typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target));
  const filteredEdges = _filterSeqEdges(typeEdges);

  // Step 3: Find all node IDs that have at least one edge.
  const connectedIds = new Set();
  filteredEdges.forEach(e => { connectedIds.add(e.source); connectedIds.add(e.target); });

  // Step 4: Remove orphaned resource nodes (active type but no remaining edges).
  const finalNodes = typeFilteredNodes.filter(n => !resourceTypes.has(n.type) || connectedIds.has(n.id));
  const finalIds = new Set(finalNodes.map(n => n.id));

  // Step 5: Re-filter edges for the final node set.
  const finalEdges = filteredEdges.filter(e => finalIds.has(e.source) && finalIds.has(e.target));

  const orderedNodes = _sortForLayout(finalNodes);
  // Expose insertion order for E2E tests (FOB-33 checkpoint).
  window._lastElementOrder = orderedNodes.map(n => ({ id: n.id, type: n.type }));

  return [
    ...orderedNodes.map(n => ({ data: n })),
    ...finalEdges.map(e => ({ data: e })),
  ];
}

/**
 * Sort nodes so ELK sees them in an order that produces a clean layout.
 * Tier 0: workflow nodes → Tier 1: activity nodes → Tier 2: resource nodes.
 * Resource nodes (skill/rule/agent/artifact) are grouped immediately after
 * their parent activity using the parent activity PK encoded in the node ID.
 *
 * @param {object[]} nodes  Raw node data objects
 * @returns {object[]}      New array sorted for layout insertion
 */
function _sortForLayout(nodes) {
  const TYPE_TIER = { workflow: 0, activity: 1 };

  // Build activity-pk → sort index map from the already-ordered activity nodes.
  const activitySortIndex = new Map();
  let idx = 0;
  nodes.forEach(n => { if (n.type === 'activity') activitySortIndex.set(String(n.entity_pk), idx++); });

  // Extract parent activity PK from resource node IDs like "skill:3:activity:7".
  const parentActPk = id => { const m = id.match(/:activity:(\d+)$/); return m ? m[1] : null; };

  return [...nodes].sort((a, b) => {
    const tierA = TYPE_TIER[a.type] ?? 2;
    const tierB = TYPE_TIER[b.type] ?? 2;
    if (tierA !== tierB) return tierA - tierB;

    if (a.type === 'activity') {
      const ordA = (a.meta && a.meta.order != null) ? a.meta.order : 9999;
      const ordB = (b.meta && b.meta.order != null) ? b.meta.order : 9999;
      return ordA !== ordB ? ordA - ordB : a.entity_pk - b.entity_pk;
    }

    // Resource nodes: group by parent activity sort position.
    const posA = activitySortIndex.get(parentActPk(a.id)) ?? 9999;
    const posB = activitySortIndex.get(parentActPk(b.id)) ?? 9999;
    return posA - posB;
  });
}

/**
 * Apply the combined visual state (entity type visibility, phase dim, search dim)
 * to all canvas nodes and edges. Also re-renders the structural tree and phase filter
 * controls so they stay in sync with the active filter.
 */
function _refreshVisualState() {
  if (!window.cy) return;
  const activePhases = _currentFilters.phases.length > 0 ? new Set(_currentFilters.phases) : null;
  const searchLower = _currentSearchTerm.toLowerCase().trim();

  // All nodes in cy are of active types (excluded types are removed by _applyTypeRebuild).
  // This pass applies phase-dim and search-dim only.
  window.cy.nodes().forEach(node => {
    const nodeType = node.data('type');
    let dimmed = false;
    // Phase dim — activity nodes only; 0 = unphased sentinel
    if (activePhases && nodeType === 'activity') {
      const meta = node.data('meta') || {};
      const phaseId = meta.phase_id != null ? meta.phase_id : 0;
      if (!activePhases.has(phaseId)) dimmed = true;
    }
    // Search dim — all nodes; edges are NOT dimmed by search (per FOB-12)
    if (searchLower) {
      const label = (node.data('label') || '').toLowerCase();
      if (!label.includes(searchLower)) dimmed = true;
    }
    node.style({ visibility: 'visible', opacity: dimmed ? 0.2 : 1 });
  });

  window.cy.edges().forEach(edge => {
    edge.style('visibility', 'visible');
    // Phase dim on edges connected to phase-dimmed activities (not search)
    if (activePhases) {
      const srcType = edge.source().data('type');
      const tgtType = edge.target().data('type');
      let edgeDimmed = false;
      if (srcType === 'activity') {
        const m = edge.source().data('meta') || {};
        const pid = m.phase_id != null ? m.phase_id : 0;
        if (!activePhases.has(pid)) edgeDimmed = true;
      }
      if (tgtType === 'activity') {
        const m = edge.target().data('meta') || {};
        const pid = m.phase_id != null ? m.phase_id : 0;
        if (!activePhases.has(pid)) edgeDimmed = true;
      }
      edge.style('opacity', edgeDimmed ? 0.2 : 1);
    } else {
      edge.style('opacity', 1);
    }
  });

  // Keep structural tree and phase filter controls in sync.
  _renderStructureTree();
  _renderPhaseFilter();
}

/**
 * Apply a name-based search term. Matching nodes are bright; others dimmed.
 * Edges are unaffected by search (per FOB-12).
 * Uses 250 ms debounce to avoid thrashing during typing.
 *
 * @param {string} term
 */
function _applySearch(term) {
  if (_searchDebounceTimer) clearTimeout(_searchDebounceTimer);
  _searchDebounceTimer = setTimeout(() => {
    _currentSearchTerm = term;
    _refreshVisualState();
  }, 250);
}

/**
 * Render the entity-type filter toolbar on the canvas.
 * One toggle button per type that has nodes; shows total count (static).
 * Called once after graph loads — recreated on playbook switch.
 *
 * @param {{ types: string[], phases: number[] }} filters
 */
function _renderFilterToolbar(filters) {
  const container = document.querySelector('[data-testid="browser-type-filter-row"]');
  if (!container || !window.cy) return;

  const displayTypes = ['workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
  const typeCounts = {};
  displayTypes.forEach(t => { typeCounts[t] = 0; });
  (_fullGraphData ? _fullGraphData.nodes : []).forEach(n => {
    if (n.type in typeCounts) typeCounts[n.type]++;
  });

  container.innerHTML = '';
  displayTypes.forEach(type => {
    if (typeCounts[type] === 0) return;
    const isActive = filters.types.includes(type);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `btn btn-sm ${isActive ? 'btn-secondary' : 'btn-outline-secondary'}`;
    btn.setAttribute('data-testid', 'browser-filter-btn');
    btn.setAttribute('data-filter-type', type);
    btn.title = `Toggle ${type} nodes`;
    const label = type.charAt(0).toUpperCase() + type.slice(1);
    btn.textContent = `${label} (${typeCounts[type]})`;
    btn.addEventListener('click', () => {
      const types = _currentFilters.types.slice();
      const idx = types.indexOf(type);
      if (idx >= 0) {
        types.splice(idx, 1);
      } else {
        types.push(type);
      }
      const newFilters = { ..._currentFilters, types };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
      _renderFilterToolbar(newFilters);
    });
    container.appendChild(btn);
  });
}

/**
 * Render phase filter pills in the canvas filter toolbar (second row).
 * Hidden entirely when the playbook has no phases.
 * Called from _refreshVisualState to stay in sync.
 */
function _renderPhaseFilter() {
  const playbookPhases = _getPlaybookPhases();
  const container = document.querySelector('[data-testid="browser-phase-filter"]');

  if (!container) return;
  if (playbookPhases.length === 0) {
    container.innerHTML = '';
    return;
  }

  const activePhases = new Set(_currentFilters.phases);
  const allPhaseIds = playbookPhases.map(p => p.id);
  // Include 0 (Unphased) as an option
  const phaseOptions = [{ id: 0, name: '(Unphased)' }, ...playbookPhases];

  container.innerHTML = '';
  phaseOptions.forEach(phase => {
    const isActive = activePhases.size === 0 || activePhases.has(phase.id);
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = `btn btn-sm me-1 mb-1 ${isActive ? 'btn-primary' : 'btn-outline-secondary'}`;
    pill.setAttribute('data-testid', 'browser-phase-pill');
    pill.setAttribute('data-phase-id', String(phase.id));
    pill.textContent = phase.name;
    pill.addEventListener('click', () => {
      let phases = _currentFilters.phases.slice();
      if (phases.length === 0) {
        phases = [phase.id];
      } else if (phases.includes(phase.id)) {
        phases = phases.filter(id => id !== phase.id);
        if (phases.length === 0) phases = [];
      } else {
        phases = phases.concat([phase.id]);
        if (phaseOptions.every(p => phases.includes(p.id))) phases = [];
      }
      const newFilters = { ..._currentFilters, phases };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
    });
    container.appendChild(pill);
  });

  // "All" reset button when filter is active
  if (activePhases.size > 0) {
    const clearBtn = document.createElement('button');
    clearBtn.type = 'button';
    clearBtn.className = 'btn btn-sm btn-outline-danger mb-1';
    clearBtn.setAttribute('data-testid', 'browser-phase-clear');
    clearBtn.textContent = 'All';
    clearBtn.addEventListener('click', () => {
      const newFilters = { ..._currentFilters, phases: [] };
      _applyFilters(newFilters);
      _replaceCanonicalUrl(_getPkFromPath(), newFilters);
    });
    container.appendChild(clearBtn);
  }
}

/**
 * Show "no content" overlay (empty playbook — graph API returned 0 nodes).
 *
 * @param {number} pk
 */
function _showNoContentState(pk) {
  const loading = document.querySelector('[data-testid="browser-loading"]');
  const empty = document.querySelector('[data-testid="browser-empty-state"]');
  const noContent = document.querySelector('[data-testid="browser-no-content-state"]');
  const error = document.querySelector('[data-testid="browser-error-state"]');
  if (loading) loading.classList.add('d-none');
  if (empty) empty.classList.add('d-none');
  if (error) error.classList.add('d-none');
  if (noContent) {
    // Update the "Go to Playbook" link with the current PK.
    const link = noContent.querySelector('[data-testid="browser-go-to-playbook"]');
    if (link && pk) link.href = `/playbooks/${pk}/`;
    noContent.classList.remove('d-none');
  }
}

// ─── Detail panel state ───────────────────────────────────────────────────────
let _currentPanelNode = null;   // Cytoscape node currently shown in panel

/**
 * Build and render the Workflow → Activity collapsible tree in the left panel.
 * Called after each graph load. Tree rows navigate the canvas on click.
 */
function _renderStructureTree() {
  const container = document.querySelector('[data-testid="browser-structure-tree"]');
  if (!container || !window.cy) return;

  const activePhases = _currentFilters.phases.length > 0 ? new Set(_currentFilters.phases) : null;
  const wfNodes = window.cy.nodes('[type="workflow"]').sort((a, b) => a.data('entity_pk') - b.data('entity_pk'));
  if (wfNodes.length === 0) { container.innerHTML = ''; return; }

  let html = '<div class="small fw-semibold text-muted text-uppercase mb-1 mt-2">Structure</div>';
  wfNodes.forEach(wfNode => {
    const wfId    = wfNode.id();
    const abbr    = (wfNode.data('meta') || {}).abbreviation || '';
    const wfLabel = wfNode.data('label') || wfId;
    const sectionId = 'tree-wf-' + wfNode.data('entity_pk');

    // All activities ordered, then filtered by active phases
    let actNodes = wfNode.outgoers('edge[relationship="contains"]').targets()
      .sort((a, b) => ((a.data('meta') || {}).order || 0) - ((b.data('meta') || {}).order || 0));

    if (activePhases) {
      actNodes = actNodes.filter(actNode => {
        const meta = actNode.data('meta') || {};
        const phaseId = meta.phase_id != null ? meta.phase_id : 0;
        return activePhases.has(phaseId);
      });
      if (actNodes.length === 0) return; // skip this workflow when no activities match
    }

    html += `
      <div class="mb-1">
        <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-tree-row"
             data-node-id="${wfId}" data-testid="browser-tree-row" style="cursor:pointer;">
          <span class="browser-tree-toggle small text-muted" data-section="${sectionId}">▸</span>
          ${abbr ? `<span class="small text-muted" style="min-width:2.2em;">${abbr}</span>` : ''}
          <span class="small fw-semibold text-truncate" title="${wfLabel}">${wfLabel}</span>
        </div>
        <div id="${sectionId}" class="ps-3" style="display:none;">`;

    actNodes.forEach(actNode => {
      const actId    = actNode.id();
      const meta     = actNode.data('meta') || {};
      const code     = meta.display_code || '';
      const colour   = meta.phase_colour || '';
      const actLabel = actNode.data('label') || actId;

      const chip = colour
        ? `<span class="rounded-circle flex-shrink-0"
                style="width:8px;height:8px;background:${colour};display:inline-block;"></span>`
        : '';

      html += `
          <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-tree-row"
               data-node-id="${actId}" data-testid="browser-tree-row" style="cursor:pointer;">
            ${code ? `<span class="small text-muted" style="min-width:2.8em;">${code}</span>` : ''}
            <span class="small text-truncate flex-grow-1" title="${actLabel}">${actLabel}</span>
            ${chip}
          </div>`;
    });

    html += `</div></div>`;
  });

  container.innerHTML = html;

  // Wire chevron clicks: accordion only (does NOT navigate canvas or open panel).
  container.querySelectorAll('.browser-tree-toggle').forEach(chevron => {
    chevron.addEventListener('click', function(e) {
      e.stopPropagation();
      _accordionWorkflow(this.dataset.section);
    });
  });

  // Wire row clicks: navigate canvas + open detail panel (same as canvas tap).
  container.querySelectorAll('[data-node-id]').forEach(row => {
    row.addEventListener('click', function(e) {
      e.stopPropagation();
      _selectTreeNode(this.dataset.nodeId);
    });
  });
}

/**
 * Cycle the ELK layout between 'layered' and 'mrtree'.
 * Re-runs layout on the existing cy instance without re-fetching.
 */
/**
 * Handle a structural tree row click.
 * Produces the same outcome as clicking the node directly on the Cytoscape canvas:
 *   1. Pan + zoom canvas to centre the node (animate fit, padding 80px).
 *   2. Open the right detail panel with the node's embed content (_openDetailPanel).
 *   3. Apply selection ring to the node (handled inside _openDetailPanel).
 *   4. Highlight the tree row (handled inside _openDetailPanel → _highlightTreeNode).
 *
 * If the node is not present in the current cy graph (e.g. filtered out),
 * the canvas step is skipped but the panel still opens using the tree row data.
 *
 * @param {string} nodeId — Cytoscape node id (string matching data-node-id attribute)
 */
function _selectTreeNode(nodeId) {
  // TODO: NotImplementedError — implement uniform tree-to-canvas selection
  throw new Error('NotImplementedError: _selectTreeNode');
}

/**
 * Run the current layout algorithm on the existing cy instance without recreating it.
 * Dispatches to ELK / dagre / native-cy / extension based on _currentLayout key.
 * Fits the graph to screen after layout completes.
 */
function _runLayout() {
  if (!window.cy) return;
  const fallbacks = [_currentLayout, 'dagre-tb', 'cy-breadthfirst'];
  for (const key of fallbacks) {
    const opts = _buildLayoutOptions(key);
    try {
      const layout = window.cy.layout(opts);
      layout.one('layoutstop', () => { window.cy && window.cy.fit(undefined, 40); });
      layout.run();
      return;
    } catch (err) {
      console.warn(`Layout "${key}" failed (plugin may not be loaded):`, err);
    }
  }
}

/**
 * Re-run current layout on the existing cy instance.
 * Useful after hiding node types or filtering, so freed space is reclaimed.
 */
function _replot() {
  _runLayout();
}

/**
 * Update the layout button label to reflect the current layout's human-readable name.
 */
function _updateLayoutBtn() {
  const btn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (!btn) return;
  const entry = _LAYOUT_CATALOG.find(e => e.key === _currentLayout);
  btn.textContent = (entry ? entry.label : _currentLayout) + ' ▾';
}

/**
 * @param {string} sectionId - The id of the section div to expand (e.g. "tree-wf-3")
 */
function _accordionWorkflow(sectionId) {
  document.querySelectorAll('[data-testid="browser-structure-tree"] .browser-tree-toggle').forEach(span => {
    const sid = span.dataset.section;
    const section = document.getElementById(sid);
    if (!section) return;
    if (sid === sectionId) {
      section.style.display = '';
      span.textContent = '▾';
    } else {
      section.style.display = 'none';
      span.textContent = '▸';
    }
  });
}

/**
 * Highlight the tree row matching `nodeId` (bold + accent).
 * @param {string} nodeId
 */
function _highlightTreeNode(nodeId) {
  document.querySelectorAll('[data-testid="browser-tree-row"]').forEach(row => {
    if (row.dataset.nodeId === nodeId) {
      row.classList.add('fw-bold', 'text-primary', 'bg-primary-subtle');
    } else {
      row.classList.remove('fw-bold', 'text-primary', 'bg-primary-subtle');
    }
  });

  // Accordion: find the section this node belongs to and expand only it.
  const targetRow = document.querySelector(`[data-testid="browser-tree-row"][data-node-id="${nodeId}"]`);
  if (targetRow) {
    // Walk up to find the nearest parent section div (id starts with "tree-wf-")
    let el = targetRow.parentElement;
    while (el) {
      if (el.id && el.id.startsWith('tree-wf-')) {
        _accordionWorkflow(el.id);
        break;
      }
      el = el.parentElement;
    }
  }
}

/**
 * Clear all tree row highlights.
 */
function _clearTreeHighlight() {
  document.querySelectorAll('[data-testid="browser-tree-row"]').forEach(row => {
    row.classList.remove('fw-bold', 'text-primary', 'bg-primary-subtle');
  });
}

// ─── Resource tree ────────────────────────────────────────────────────────────

const _RESOURCE_ICONS = { artifact: '📦', skill: '🔧', agent: '🤖', rule: '📋' };
const _RESOURCE_ORDER = ['artifact', 'skill', 'agent', 'rule'];

/**
 * Render resource tree for a selected Workflow or Activity node.
 * Groups resource nodes by type, deduplicates by entity_pk.
 *
 * @param {cytoscape.NodeSingular} node
 */
function _renderResourceTree(node) {
  const container = document.querySelector('[data-testid="browser-resource-tree"]');
  if (!container || !window.cy) return;

  const nodeType = node.data('type');
  let activityNodes;

  if (nodeType === 'workflow') {
    activityNodes = node.outgoers('edge[relationship="contains"]').targets();
  } else if (nodeType === 'activity') {
    // FOB-28: show resources for the parent Workflow (all siblings), not just this activity.
    const parentWf = node.incomers('edge[relationship="contains"]').sources();
    if (parentWf && parentWf.length) {
      activityNodes = parentWf.outgoers('edge[relationship="contains"]').targets();
    } else {
      activityNodes = node; // fallback if orphaned activity
    }
  } else {
    return; // resource node clicked — keep existing tree (no change)
  }

  // Collect resource nodes connected to each activity; deduplicate by entity_pk within type.
  const grouped = {};
  _RESOURCE_ORDER.forEach(t => { grouped[t] = new Map(); }); // entity_pk → cy node

  activityNodes.forEach(actNode => {
    actNode.outgoers('node').forEach(rNode => {
      const rType = rNode.data('type');
      if (!_RESOURCE_ORDER.includes(rType)) return;
      const epk = rNode.data('entity_pk');
      if (!grouped[rType].has(epk)) grouped[rType].set(epk, rNode);
    });
  });

  const anyResources = _RESOURCE_ORDER.some(t => grouped[t].size > 0);
  if (!anyResources) {
    container.innerHTML = '<span class="small text-muted">No resources linked.</span>';
    return;
  }

  let html = '<div class="small fw-semibold text-muted text-uppercase mb-1">Resources</div>';
  _RESOURCE_ORDER.forEach(rType => {
    if (grouped[rType].size === 0) return;
    const label = rType.charAt(0).toUpperCase() + rType.slice(1) + 's';
    html += `<div class="small text-muted mt-1 mb-1">${label}</div>`;
    grouped[rType].forEach((rNode, _epk) => {
      const icon  = _RESOURCE_ICONS[rType] || '';
      const label = rNode.data('label') || '';
      const nId   = rNode.id();
      html += `
        <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-resource-row"
             data-node-id="${nId}" data-testid="browser-resource-row" style="cursor:pointer;"
             title="${label}">
          <span>${icon}</span>
          <span class="small text-truncate">${label}</span>
        </div>`;
    });
  });

  container.innerHTML = html;

  container.querySelectorAll('[data-node-id]').forEach(row => {
    row.addEventListener('click', function(e) {
      e.stopPropagation();
      const nodeId = this.dataset.nodeId;
      if (window.cy) {
        const rNode = window.cy.getElementById(nodeId);
        if (rNode && rNode.length) _openDetailPanel(rNode);
      }
    });
  });
}

/**
 * Clear the resource tree back to its default placeholder.
 */
function _clearResourceTree() {
  const container = document.querySelector('[data-testid="browser-resource-tree"]');
  if (container) container.innerHTML = '<span class="small text-muted">Select a Workflow to see its resources.</span>';
}

/**
 * Open (or replace content of) the detail panel for a given node.
 * Applies selection ring to the tapped node; dims all others.
 *
 * @param {cytoscape.NodeSingular} node
 */
function _openDetailPanel(node) {
  const panel = document.querySelector('[data-testid="browser-detail-panel"]');
  const panelContent = document.querySelector('[data-testid="browser-panel-content"]');
  const openTabBtn = document.querySelector('[data-testid="browser-panel-open-tab"]');
  const openFullBtn = document.querySelector('[data-testid="browser-panel-open-full"]');
  if (!panel || !panelContent) return;

  // Only apply canvas selection ring + dim when the node is actually visible.
  // FOB-32: resource nodes filtered out (visibility:hidden) open panel without canvas update.
  if (window.cy) {
    const nodeIsVisible = node.style('visibility') !== 'hidden';
    if (nodeIsVisible) {
      window.cy.nodes().forEach(n => {
        n.style('border-width', 0);
        if (n.style('visibility') !== 'hidden') n.style('opacity', 0.4);
      });
      node.style({ 'border-width': 3, 'border-color': '#dc3545', 'opacity': 1 });
    }
  }
  _currentPanelNode = node;

  // FOB-27: only highlight structural tree for Workflow / Activity nodes.
  // Resource entity types (skill, agent, artifact, rule) must NOT highlight tree rows.
  const nodeType = node.data('type');
  if (nodeType === 'workflow' || nodeType === 'activity') {
    _highlightTreeNode(node.id());
  } else {
    _clearTreeHighlight();
  }
  _renderResourceTree(node);

  const embedUrl = node.data('embed_url');
  const detailUrl = node.data('detail_url');

  // Wire header buttons.
  if (openTabBtn) openTabBtn.onclick = () => detailUrl && window.open(detailUrl, '_blank');
  if (openFullBtn) openFullBtn.onclick = () => detailUrl && (window.location.href = detailUrl);

  // Show panel.
  panel.classList.remove('d-none');

  // Load embed content via fetch.
  if (embedUrl) {
    panelContent.innerHTML = '<p class="text-muted p-3 small">Loading…</p>';
    fetch(embedUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(r => r.text())
      .then(html => {
        _checkSessionExpiry(html);
        // Only update panel if it's still open (user may have closed it).
        if (_currentPanelNode === node) panelContent.innerHTML = html;
      })
      .catch(() => { panelContent.innerHTML = '<p class="text-danger p-3">Failed to load.</p>'; });
  }
}

/**
 * Close the detail panel and clear selection ring.
 */
function _closeDetailPanel() {
  const panel = document.querySelector('[data-testid="browser-detail-panel"]');
  const panelContent = document.querySelector('[data-testid="browser-panel-content"]');
  if (panel) panel.classList.add('d-none');
  if (panelContent) panelContent.innerHTML = '';
  if (window.cy) {
    window.cy.nodes().style({ 'border-width': 0 });
    // Re-apply filter/search visual state (restores correct opacity + visibility).
    _refreshVisualState();
  }
  _currentPanelNode = null;
  _clearTreeHighlight();
  _clearResourceTree();
}

/**
 * Detect session expiry in HTMX-swapped HTML.
 * If the login page is swapped in, redirect the tab.
 *
 * @param {string} html
 */
function _checkSessionExpiry(html) {
  if (html.includes('id="login-form"') || html.includes('/auth/login/')) {
    const pk = _getPlaybookPk();
    window.location.href = '/auth/login/?next=' + encodeURIComponent('/browser/' + (pk || '') + '/');
  }
}

// ─── Picker state ────────────────────────────────────────────────────────────
let _allPlaybooks = [];   // cached from last GET /api/playbooks/
let _pickerOpen  = false;

/**
 * Open the playbook picker: fetch list, render, show.
 * Auto-expands left panel if it was collapsed.
 */
async function _openPicker() {
  const panel = document.getElementById('browser-left-panel');
  if (panel && panel.classList.contains('browser-collapsed')) {
    _toggleLeftPanel();
  }
  const picker = document.getElementById('browser-picker');
  if (!picker) return;

  if (!_pickerOpen) {
    picker.classList.remove('d-none');
    _pickerOpen = true;
    const search = picker.querySelector('[data-testid="browser-picker-search"]');
    if (search) { search.value = ''; search.focus(); }
  }

  try {
    const resp = await fetch('/api/playbooks/', {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!resp.ok) return;
    const data = await resp.json();
    _allPlaybooks = data.results || data;
    _renderPickerItems(_allPlaybooks);
  } catch (_) { /* network error — leave list empty */ }
}

/**
 * Render picker rows from a playbooks array.
 * @param {Array} playbooks
 */
function _renderPickerItems(playbooks) {
  const list = document.getElementById('browser-picker-list');
  if (!list) return;
  const currentPk = _getPlaybookPk();
  list.innerHTML = '';
  if (!playbooks.length) {
    list.innerHTML = '<div class="list-group-item text-muted small">No playbooks found.</div>';
    return;
  }
  playbooks.forEach(pb => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.setAttribute('data-testid', 'browser-picker-item');
    btn.setAttribute('data-pk', String(pb.id));
    btn.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center small py-2';
    if (String(pb.id) === String(currentPk)) {
      btn.classList.add('active');
    }
    const nameSpan = document.createElement('span');
    nameSpan.textContent = pb.name;
    const right = document.createElement('span');
    right.className = 'd-flex align-items-center gap-1';
    const badge = document.createElement('span');
    badge.className = 'badge bg-secondary';
    badge.textContent = pb.status;
    right.appendChild(badge);
    if (String(pb.id) === String(currentPk)) {
      const check = document.createElement('i');
      check.className = 'fa-solid fa-check text-white ms-1';
      right.appendChild(check);
    }
    btn.appendChild(nameSpan);
    btn.appendChild(right);
    btn.addEventListener('click', () => _selectPlaybook(pb.id));
    list.appendChild(btn);
  });
}

/**
 * Filter picker items by substring on keyup.
 * @param {string} term
 */
function _filterPickerItems(term) {
  const lower = term.toLowerCase();
  const filtered = lower
    ? _allPlaybooks.filter(pb => pb.name.toLowerCase().includes(lower))
    : _allPlaybooks;
  _renderPickerItems(filtered);
}

/**
 * Close the picker.
 */
function _closePicker() {
  const picker = document.getElementById('browser-picker');
  if (picker) picker.classList.add('d-none');
  _pickerOpen = false;
}

/**
 * Select a playbook: close picker, update URL, update header, fetch graph.
 * @param {number|string} pk
 */
function _selectPlaybook(pk) {
  // FOB-23b: full page navigation so initialisation is identical to opening /browser/<pk>/ directly.
  window.location.href = '/browser/' + pk + '/';
}

/**
 * Update playbook name and status badge in left panel header.
 * Called after graph data arrives.
 * @param {string|number} pk
 * @param {string} name
 * @param {string} status
 */
function _updatePlaybookHeader(pk, name, status) {
  const nameEl = document.querySelector('[data-testid="browser-playbook-title"]');
  if (nameEl) nameEl.textContent = name;
  const statusEl = document.querySelector('[data-testid="browser-playbook-status"]');
  if (statusEl) { statusEl.textContent = status; statusEl.className = 'badge bg-secondary small'; }

  // Ensure Change Playbook button is visible; swap Select → Change if needed.
  const select = document.querySelector('[data-testid="browser-select-playbook"]');
  if (select) { select.setAttribute('data-testid', 'browser-change-playbook'); select.textContent = 'Change Playbook'; select.className = 'btn btn-sm btn-outline-secondary mb-2'; }
}

/**
 * Toggle left panel collapsed / expanded.
 * The toggle button lives outside the panel (sibling in browser-root) so it is
 * never clipped. Its `left` CSS position tracks the panel width.
 */
function _toggleLeftPanel() {
  const panel = document.getElementById('browser-left-panel');
  const toggle = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (!panel) return;
  const collapsed = panel.classList.toggle('browser-collapsed');
  const expandedWidth = '280px';
  panel.style.width = collapsed ? '0' : expandedWidth;
  panel.style.minWidth = collapsed ? '0' : expandedWidth;
  const content = document.getElementById('browser-left-panel-content');
  if (content) content.style.display = collapsed ? 'none' : '';
  if (toggle) {
    toggle.textContent = collapsed ? '›' : '‹';
    toggle.style.left = collapsed ? '0' : expandedWidth;
  }
  if (window.cy) window.cy.resize();
}

/**
 * Main entry point — called on DOMContentLoaded.
 * Reads PK, normalises URL params, fetches graph if PK present.
 */
function _init() {
  const pk = _getPlaybookPk();
  const phases = _getPlaybookPhases();
  const filters = _parseUrlParams();
  _normaliseFilters(filters, phases);

  // Wire panel close button.
  const panelClose = document.querySelector('[data-testid="browser-panel-close"]');
  if (panelClose) panelClose.addEventListener('click', _closeDetailPanel);

  // Wire collapse toggle.
  const toggleBtn = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (toggleBtn) toggleBtn.addEventListener('click', _toggleLeftPanel);

  // Wire picker open — both Change Playbook and Select Playbook buttons.
  document.querySelectorAll('[data-testid="browser-change-playbook"], [data-testid="browser-select-playbook"]').forEach(btn => {
    btn.addEventListener('click', _openPicker);
  });

  // Wire picker search input.
  const pickerSearch = document.querySelector('[data-testid="browser-picker-search"]');
  if (pickerSearch) pickerSearch.addEventListener('input', e => _filterPickerItems(e.target.value));

  // Wire node search input (debounced canvas node name filter).
  const nodeSearch = document.querySelector('[data-testid="browser-search-input"]');
  if (nodeSearch) nodeSearch.addEventListener('input', e => _applySearch(e.target.value));

  if (!pk) {
    _showEmptyState();
    return;
  }

  // Wire zoom controls.
  const zoomIn = document.querySelector('[data-testid="browser-zoom-in"]');
  const zoomOut = document.querySelector('[data-testid="browser-zoom-out"]');
  const zoomFit = document.querySelector('[data-testid="browser-zoom-fit"]');
  if (zoomIn) zoomIn.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() * 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomOut) zoomOut.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() / 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomFit) zoomFit.addEventListener('click', () => window.cy && window.cy.fit());

  // Wire layout switcher.
  const layoutBtn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (layoutBtn) layoutBtn.addEventListener('click', _toggleLayoutDropdown);
  _updateLayoutBtn();

  // Wire routing picker.
  const routingBtn = document.querySelector('[data-testid="browser-routing-btn"]');
  if (routingBtn) routingBtn.addEventListener('click', _toggleRoutingDropdown);
  _updateRoutingBtn();

  // Wire seq edges toggle.
  const seqToggle = document.querySelector('[data-testid="browser-seq-toggle"]');
  if (seqToggle) seqToggle.addEventListener('click', _applySeqToggle);
  _updateSeqToggleBtn();

  // Wire compound view toggle.
  const compoundToggle = document.querySelector('[data-testid="browser-compound-toggle"]');
  if (compoundToggle) compoundToggle.addEventListener('click', _applyCompoundToggle);
  _updateCompoundToggleBtn();

  // Wire re-plot button.
  const replotBtn = document.querySelector('[data-testid="browser-replot-btn"]');
  if (replotBtn) replotBtn.addEventListener('click', _replot);

  _fetchGraph(pk);
}

// Expose instance globally for Playwright E2E tests.
window.cy = null;
// Expose module state for Playwright E2E tests.
Object.defineProperty(window, '_seqEdgesOn', { get: () => _seqEdgesOn });
Object.defineProperty(window, '_currentRouting', { get: () => _currentRouting });
Object.defineProperty(window, '_compoundViewOn', { get: () => _compoundViewOn });

document.addEventListener('DOMContentLoaded', _init);
window.addEventListener('popstate', _onPopState);

// ─────────────────────────────────────────────────────────────────────────────
// S38 — Enhanced node visual styling (FOB-38)
// All functions below are skeletons — implementation fills in the bodies.
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Build the Cytoscape stylesheet with enhanced node shapes and Mimir design-aligned
 * visual style (FOB-38). Replaces _cytoscapeStyle() when implemented.
 *
 * Node shapes per entity type:
 *   playbook    → round-octagon
 *   workflow    → round-rectangle (wider, bolder)
 *   activity    → bottom-round-rectangle
 *   artifact    → round-diamond
 *   skill       → hexagon
 *   agent       → ellipse (unchanged)
 *   rule        → cut-rectangle
 *
 * Typography: Montserrat font, weight 600 structural / 400 resource.
 * Borders: 2px solid on all node types.
 *
 * @returns {object[]} Cytoscape stylesheet array
 */
function _cytoscapeStyleEnhanced() {
  const edgeStyles = _buildEdgeStyle();
  const nodeTypes = ['playbook', 'workflow', 'activity', 'artifact', 'skill', 'agent', 'rule'];
  const nodeStyles = nodeTypes.map(type => ({
    selector: `node[type = "${type}"]`,
    style: _buildEnhancedNodeStyle(type),
  }));
  const selectedStyle = _cytoscapeStyle().filter(s => s.selector === 'node:selected');
  return [...nodeStyles, ...edgeStyles, ...selectedStyle];
}

/**
 * Return enhanced style properties for a single entity type node.
 * Helper extracted from _cytoscapeStyleEnhanced() for testability.
 *
 * @param {string} type — one of: playbook, workflow, activity, artifact, skill, agent, rule
 * @returns {object} Cytoscape style property map
 */
function _buildEnhancedNodeStyle(type) {
  const colors = _buildNodeColor(type);
  const icon = _buildNodeIcon(type);
  return {
    'label': `${icon} data(label)`,
    'text-valign': 'center',
    'text-halign': 'center',
    'font-family': 'Montserrat, system-ui',
    'text-wrap': 'wrap',
    'border-width': 2,
    'border-opacity': 1,
    'background-opacity': 1,
    'shape': 'round-rectangle',
    'background-color': colors.bg,
    'border-color': colors.border,
    'color': colors.text,
    'font-size': 13,
    'width': 120,
    'height': 40,
    'text-max-width': 108,
  };
}

/**
 * Return pastel Bootstrap 5.3 colour tokens for a given node type.
 *
 * Expected palette (when implemented):
 *   playbook  → { bg: '#e0cffc', border: '#9461fb', text: '#3d0a91' }
 *   workflow  → { bg: '#cfe2ff', border: '#9ec5fe', text: '#084298' }
 *   activity  → { bg: '#d1e7dd', border: '#a3cfbb', text: '#0a3622' }
 *   artifact  → { bg: '#fff3cd', border: '#ffda6a', text: '#664d03' }
 *   skill     → { bg: '#ffe5d0', border: '#fecba1', text: '#6e1d0b' }
 *   agent     → { bg: '#cff4fc', border: '#9eeaf9', text: '#055160' }
 *   rule      → { bg: '#e2e3e5', border: '#c4c8cb', text: '#2b2d2f' }
 *
 * @param {string} type — entity type string
 * @returns {{ bg: string, border: string, text: string }}
 */
function _buildNodeColor(type) {
  // TODO: NotImplementedError — implement pastel palette
  throw new Error('NotImplementedError: _buildNodeColor');
}

/**
 * Return the FontAwesome 6 unicode glyph string for a given node type.
 *
 * Expected glyphs (when implemented, using FA6 Solid):
 *   playbook  → '\uf5da'  (fa-book-sparkles)
 *   workflow  → '\ue598'  (fa-diagram-project)
 *   activity  → '\ue141'  (fa-bars-progress)
 *   artifact  → '\uf06b'  (fa-gift)
 *   skill     → '\ue05d'  (fa-hand-holding-magic)
 *   agent     → '\ue0c4'  (fa-brain-circuit)
 *   rule      → '\uf24e'  (fa-scale-balanced)
 *
 * The icon is rendered via 'font-family': '"Font Awesome 6 Free"' on the label.
 * Weight must be 900 for solid icons.
 *
 * @param {string} type — entity type string
 * @returns {string} Unicode glyph character
 */
function _buildNodeIcon(type) {
  // TODO: NotImplementedError — implement FA icon map
  throw new Error('NotImplementedError: _buildNodeIcon');
}

/**
 * Return edge stylesheet entries for the enhanced style.
 * All edges must use uniform black (#212529) colour.
 * Inherits curve-style from _currentRouting via _applyRouting().
 *
 * Expected output (when implemented):
 *   [
 *     { selector: 'edge', style: { 'line-color': '#212529', 'target-arrow-color': '#212529',
 *         'target-arrow-shape': 'triangle', 'curve-style': 'bezier', 'width': 1.5 } },
 *     { selector: 'edge[relationship = "predecessor"]', style: { 'line-style': 'dashed', ... } },
 *     { selector: 'edge[relationship = "contains"]', style: { 'display': 'none' } },
 *   ]
 *
 * @returns {object[]} Cytoscape stylesheet entries for edges
 */
function _buildEdgeStyle() {
  // TODO: NotImplementedError — implement uniform black edge styles
  throw new Error('NotImplementedError: _buildEdgeStyle');
}

// ─────────────────────────────────────────────────────────────────────────────
// S35 — Edge routing picker (FOB-35)
// ─────────────────────────────────────────────────────────────────────────────

/** Current edge routing key. Defaults to 'bezier'. Read by _filtersToQueryString. */
let _currentRouting = 'bezier';

/**
 * Routing catalog — all 6 selectable Cytoscape curve-style options.
 * key      → URL param value and cy curve-style value (or mapping via _applyRouting)
 * label    → human-readable button/dropdown label
 * cyValue  → the actual Cytoscape curve-style string to apply
 */
const _ROUTING_CATALOG = [
  { key: 'bezier',           label: 'Bezier (default)', cyValue: 'bezier' },
  { key: 'unbundled-bezier', label: 'Unbundled Bezier', cyValue: 'unbundled-bezier' },
  { key: 'straight',         label: 'Straight',         cyValue: 'straight' },
  { key: 'taxi',             label: 'Orthogonal',        cyValue: 'taxi' },
  { key: 'haystack',         label: 'Haystack',          cyValue: 'haystack' },
  { key: 'segments',         label: 'Segments',          cyValue: 'segments' },
  { key: 'round-seg',        label: 'Round Segments',    cyValue: 'round-segments' },
];

/**
 * Apply a routing style by key.
 * Updates _currentRouting, button label, URL param, and applies curve-style to all cy edges.
 * Does NOT trigger a layout re-run — style update only.
 *
 * @param {string} key — one of the keys in _ROUTING_CATALOG
 */
function _applyRouting(key) {
  if (!_ROUTING_CATALOG.some(e => e.key === key)) return;
  _currentRouting = key;
  _updateRoutingBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  if (window.cy) {
    const entry = _ROUTING_CATALOG.find(e => e.key === key);
    window.cy.edges().style({ 'curve-style': entry.cyValue });
  }
}

/**
 * Toggle the edge routing picker dropdown open/closed.
 * Mirrors _toggleLayoutDropdown pattern: appended to document.body, Escape closes it.
 */
function _toggleRoutingDropdown() {
  const existing = document.querySelector('[data-testid="browser-routing-dropdown"]');
  if (existing) { existing.remove(); return; }

  const btn = document.querySelector('[data-testid="browser-routing-btn"]');
  if (!btn) return;

  const panel = document.createElement('div');
  panel.setAttribute('data-testid', 'browser-routing-dropdown');
  const rect = btn.getBoundingClientRect();
  panel.style.cssText =
    `position:fixed;bottom:${window.innerHeight - rect.top + 4}px;right:${window.innerWidth - rect.right}px;` +
    'z-index:1050;background:#fff;border:1px solid rgba(0,0,0,.15);border-radius:6px;' +
    'box-shadow:0 4px 16px rgba(0,0,0,.15);padding:4px 0;min-width:180px;max-height:60vh;overflow-y:auto;';

  _ROUTING_CATALOG.forEach(entry => {
    const item = document.createElement('button');
    item.setAttribute('data-testid', `browser-routing-option-${entry.key}`);
    item.type = 'button';
    const isActive = _currentRouting === entry.key;
    item.style.cssText =
      'display:block;width:100%;padding:4px 20px;text-align:left;border:none;cursor:pointer;font-size:0.85rem;' +
      (isActive ? 'background:#e9ecef;font-weight:600;' : 'background:transparent;');
    item.textContent = entry.label + (isActive ? ' ✓' : '');
    item.addEventListener('click', () => {
      panel.remove();
      document.removeEventListener('keydown', escHandler);
      document.removeEventListener('click', outsideHandler);
      _applyRouting(entry.key);
    });
    panel.appendChild(item);
  });

  document.body.appendChild(panel);

  const escHandler = (e) => {
    if (e.key === 'Escape') {
      panel.remove();
      document.removeEventListener('keydown', escHandler);
      document.removeEventListener('click', outsideHandler);
    }
  };
  const outsideHandler = (e) => {
    if (!panel.contains(e.target) && e.target !== btn) {
      panel.remove();
      document.removeEventListener('keydown', escHandler);
      document.removeEventListener('click', outsideHandler);
    }
  };
  document.addEventListener('keydown', escHandler);
  setTimeout(() => document.addEventListener('click', outsideHandler), 0);
}

/**
 * Update the routing button label to reflect the current routing's human-readable name.
 */
function _updateRoutingBtn() {
  const btn = document.querySelector('[data-testid="browser-routing-btn"]');
  if (!btn) return;
  const entry = _ROUTING_CATALOG.find(e => e.key === _currentRouting);
  btn.textContent = (entry ? entry.label : _currentRouting) + ' ▾';
}

/**
 * Parse the ?routing= URL parameter and set _currentRouting accordingly.
 * Unknown values silently fall back to 'bezier'.
 * Called from _parseUrlParams (S35 implementation extends that function).
 */
function _parseRoutingParam() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('routing');
  if (raw && _ROUTING_CATALOG.some(e => e.key === raw)) {
    _currentRouting = raw;
  } else {
    _currentRouting = 'bezier';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// S36 — Activity sequence edges toggle (FOB-36)
// ─────────────────────────────────────────────────────────────────────────────

/** Whether predecessor (sequence) edges are shown. Default: true (ON). */
let _seqEdgesOn = true;

/**
 * Toggle sequence edges on or off.
 * Triggers a full graph rebuild + relayout (same as entity-type filter rebuild).
 * Updates _seqEdgesOn, button visual state, and URL param.
 */
function _applySeqToggle() {
  _seqEdgesOn = !_seqEdgesOn;
  _updateSeqToggleBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  _rebuildRespectingMode(new Set(_currentFilters.types));
}

/**
 * Rebuild the graph using either flat or compound layout depending on the
 * current value of _compoundViewOn. Called by _applySeqToggle so that toggling
 * sequence edges does not inadvertently reset compound/flat state.
 *
 * When _compoundViewOn === true:
 *   1. Build compound elements via _buildCompoundElements(activeTypes).
 *   2. Apply compound + base stylesheet.
 *   3. Re-run the current layout with _buildLayoutOptions(_currentLayout).
 *   4. Fit the viewport.
 * When _compoundViewOn === false:
 *   delegate to _applyTypeRebuild(activeTypes) (existing flat path).
 *
 * @param {Set<string>} activeTypes — currently active entity-type filter set
 */
function _rebuildRespectingMode(activeTypes) {
  // TODO: NotImplementedError — implement compound-aware rebuild
  throw new Error('NotImplementedError: _rebuildRespectingMode');
}

/**
 * Update the seq toggle button visual state to match _seqEdgesOn.
 * ON:  button appears pressed/active, label "Seq ✓"
 * OFF: button appears inactive, label "Seq ✗"
 */
function _updateSeqToggleBtn() {
  const btn = document.querySelector('[data-testid="browser-seq-toggle"]');
  if (!btn) return;
  if (_seqEdgesOn) {
    btn.textContent = 'Seq ✓';
    btn.classList.add('active');
  } else {
    btn.textContent = 'Seq ✗';
    btn.classList.remove('active');
  }
}

/**
 * Filter edges for sequence toggle: when _seqEdgesOn is false, remove all
 * edges whose relationship is 'predecessor' from the element set.
 * Called inside _buildFilteredElements (S36 implementation modifies that function).
 *
 * @param {object[]} edges — raw edge data objects from _fullGraphData
 * @returns {object[]} filtered edges array
 */
function _filterSeqEdges(edges) {
  if (_seqEdgesOn) return edges;
  return edges.filter(e => e.relationship !== 'predecessor');
}

/**
 * Parse the ?seq= URL parameter and set _seqEdgesOn accordingly.
 * seq=0 → false; absent or any other value → true (default ON).
 * Called from _parseUrlParams (S36 implementation extends that function).
 */
function _parseSeqParam() {
  const params = new URLSearchParams(window.location.search);
  _seqEdgesOn = params.get('seq') !== '0';
}

// ─────────────────────────────────────────────────────────────────────────────
// S37 — Workflow compound view toggle (FOB-37)
// ─────────────────────────────────────────────────────────────────────────────

/** Whether compound view mode is active. Default: false (flat mode). */
let _compoundViewOn = false;

// ─────────────────────────────────────────────────────────────────────────────
// S48 — Node size mode toggle (FOB-39)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Node size mode. One of:
 *   'fixed'  — all nodes are a uniform fixed size; long labels truncate with ellipsis.
 *   'auto'   — node width expands to fit label text; font size stays constant.
 * Initialised from URL param ?nodesize= (see _parseNodeSizeParam).
 */
let _nodeSizeMode = 'fixed';

/**
 * Toggle node size mode between 'fixed' and 'auto', update the button,
 * write the URL param, then re-apply the stylesheet so the change is visible
 * immediately without a full graph rebuild.
 *
 * Steps (when implemented):
 *   1. Toggle _nodeSizeMode: 'fixed' ↔ 'auto'
 *   2. Call _updateNodeSizeModeBtn() to update button label/class
 *   3. Call _replaceCanonicalUrl(_getPkFromPath(), _currentFilters)
 *   4. Reapply stylesheet: window.cy.style(_cytoscapeStyleEnhanced() + compound if active)
 */
function _applyNodeSizeToggle() {
  // TODO: NotImplementedError — implement node size mode toggle
  throw new Error('NotImplementedError: _applyNodeSizeToggle');
}

/**
 * Update the node size mode button to reflect the current _nodeSizeMode.
 *   'fixed' → button text "Fixed size ✓",  adds class 'active'
 *   'auto'  → button text "Auto-width ✓",  adds class 'active'
 */
function _updateNodeSizeModeBtn() {
  // TODO: NotImplementedError — implement node size button update
  throw new Error('NotImplementedError: _updateNodeSizeModeBtn');
}

/**
 * Read ?nodesize= URL parameter and set _nodeSizeMode accordingly.
 * Valid values: 'fixed' (default), 'auto'.
 * Called once on page load before cy is initialised.
 */
function _parseNodeSizeParam() {
  // TODO: NotImplementedError — implement URL param parsing for nodesize
  throw new Error('NotImplementedError: _parseNodeSizeParam');
}

/**
 * Toggle compound view on or off.
 * Triggers a full graph rebuild with compound parent assignments (ON)
 * or clears all parent assignments and rebuilds flat (OFF).
 * Updates _compoundViewOn, button visual state, and URL param.
 */
function _applyCompoundToggle() {
  _compoundViewOn = !_compoundViewOn;
  _updateCompoundToggleBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  const activeTypes = new Set(_currentFilters.types);
  if (!window.cy || !_fullGraphData) return;
  const elements = _compoundViewOn ? _buildCompoundElements(activeTypes) : _buildFilteredElements(activeTypes);
  window.cy.remove(window.cy.elements());
  if (_compoundViewOn) {
    window.cy.style(_cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyle()));
  } else {
    window.cy.style(_cytoscapeStyleEnhanced());
  }
  window.cy.add(elements);
  _runLayout();
}

/**
 * Update the compound toggle button visual state to match _compoundViewOn.
 * ON:  label "Grouped ✓"
 * OFF: label "Grouped ✗"
 */
function _updateCompoundToggleBtn() {
  const btn = document.querySelector('[data-testid="browser-compound-toggle"]');
  if (!btn) return;
  if (_compoundViewOn) {
    btn.textContent = 'Grouped ✓';
    btn.classList.add('active');
  } else {
    btn.textContent = 'Grouped ✗';
    btn.classList.remove('active');
  }
}

/**
 * Build Cytoscape element array in compound mode.
 * Sets each activity node's `parent` data field to its workflow node ID.
 * Resource nodes connected to an activity inherit the same workflow parent.
 * Workflow nodes become compound parents (no `parent` set on them).
 *
 * @param {Set<string>} activeTypes — set of entity type strings currently visible
 * @returns {{ data: object }[]} Cytoscape element array with parent assignments
 */
function _buildCompoundElements(activeTypes) {
  if (!_fullGraphData) return [];
  const { nodes, edges } = _fullGraphData;
  const resourceTypes = new Set(['skill', 'agent', 'rule', 'artifact']);

  const typeFilteredNodes = nodes.filter(n => activeTypes.has(n.type));
  const typeFilteredIds = new Set(typeFilteredNodes.map(n => n.id));

  // Build workflow → activity map from 'contains' edges.
  const activityToWorkflow = new Map();
  edges.forEach(e => {
    if (e.relationship === 'contains' && typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target)) {
      activityToWorkflow.set(e.target, e.source); // target is activity, source is workflow
    }
  });

  // Edges excluding 'contains' (workflow→activity become compound parents instead).
  const nonContainsEdges = edges.filter(
    e => e.relationship !== 'contains' && typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target)
  );
  const filteredEdges = _filterSeqEdges(nonContainsEdges);

  // Build resource → workflow parent map via activity parent.
  const resourceToWorkflow = new Map();
  filteredEdges.forEach(e => {
    const targetNode = typeFilteredNodes.find(n => n.id === e.target);
    if (targetNode && resourceTypes.has(targetNode.type)) {
      const wfId = activityToWorkflow.get(e.source);
      if (wfId) resourceToWorkflow.set(e.target, wfId);
    }
    const sourceNode = typeFilteredNodes.find(n => n.id === e.source);
    if (sourceNode && resourceTypes.has(sourceNode.type)) {
      const wfId = activityToWorkflow.get(e.target);
      if (wfId) resourceToWorkflow.set(e.source, wfId);
    }
  });

  const connectedIds = new Set();
  filteredEdges.forEach(e => { connectedIds.add(e.source); connectedIds.add(e.target); });

  const finalNodes = typeFilteredNodes.filter(n => !resourceTypes.has(n.type) || connectedIds.has(n.id));

  const compoundNodes = finalNodes.map(n => {
    const nodeData = { ...n };
    if (n.type === 'activity') {
      const wfId = activityToWorkflow.get(n.id);
      if (wfId) nodeData.parent = wfId;
    } else if (resourceTypes.has(n.type)) {
      const wfId = resourceToWorkflow.get(n.id);
      if (wfId) nodeData.parent = wfId;
    } else if (n.type === 'workflow') {
      _addElkCompoundData(nodeData);
    }
    return { data: nodeData };
  });

  const finalIds = new Set(finalNodes.map(n => n.id));
  const compoundEdges = filteredEdges
    .filter(e => finalIds.has(e.source) && finalIds.has(e.target))
    .map(e => ({ data: e }));

  return [...compoundNodes, ...compoundEdges];
}

/**
 * Mutate a workflow nodeData object to include ELK layout attributes so that
 * ELK recursively lays out the children (activity nodes) inside the compound box.
 *
 * Expected mutations (when implemented):
 *   nodeData['elk:algorithm'] = 'layered';
 *   nodeData['elk:direction'] = 'DOWN';
 *   nodeData['elk:padding'] = '[top=30,left=10,bottom=10,right=10]';
 *
 * Without these, cytoscape-elk only positions the top-level boxes and ignores
 * the internal structure of each compound parent.
 *
 * @param {object} nodeData — mutable nodeData object for a workflow node
 */
function _addElkCompoundData(nodeData) {
  // TODO: NotImplementedError — add ELK compound layout data
  throw new Error('NotImplementedError: _addElkCompoundData');
}

/**
 * Return the label positioning overrides that float the compound parent's label
 * gently above the top-left corner of the compound boundary.
 *
 * Expected output (when implemented):
 *   {
 *     'text-margin-y': -14,      // push label above top border
 *     'text-margin-x': 6,        // slight left indent
 *     'text-background-color': '#ffffff',
 *     'text-background-opacity': 0.85,
 *     'text-background-padding': '3px',
 *   }
 *
 * @returns {object} Cytoscape style overrides for the :parent selector label
 */
function _buildCompoundLabelStyle() {
  return {
    'text-margin-y': -14,
    'text-margin-x': 6,
    'text-background-color': '#ffffff',
    'text-background-opacity': 0.85,
    'text-background-padding': '3px',
    'text-border-opacity': 0,
    'color': '#084298',
  };
}

/**
 * Return the Cytoscape stylesheet additions for compound parent (workflow) nodes.
 * These entries augment the base stylesheet when compound view is active:
 *   - background-color: #eef2ff (light periwinkle)
 *   - border: 2px solid #0d6efd
 *   - border-radius: 8px (via shape: round-rectangle)
 *   - text-valign: top, text-halign: left
 *   - padding: 20px
 *
 * @returns {object[]} additional stylesheet entries for :parent selector
 */
function _cytoscapeCompoundStyle() {
  return [
    {
      selector: ':parent',
      style: {
        'background-color': '#eef2ff',
        'border-color': '#0d6efd',
        'border-width': 2,
        'border-style': 'solid',
        'shape': 'round-rectangle',
        'text-valign': 'top',
        'text-halign': 'left',
        'padding': '20px',
        'font-size': '0.85rem',
        'font-weight': 600,
        ..._buildCompoundLabelStyle(),
      },
    },
  ];
}

/**
 * Parse the ?compound= URL parameter and set _compoundViewOn accordingly.
 * compound=1 → true; absent or other value → false (default flat).
 * Called from _parseUrlParams (S37 implementation extends that function).
 */
function _parseCompoundParam() {
  const params = new URLSearchParams(window.location.search);
  _compoundViewOn = params.get('compound') === '1';
}
