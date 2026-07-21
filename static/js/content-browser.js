/**
 * content-browser.js — Content Browser client-side logic.
 *
 * Responsibilities:
 *   1. Read playbook PK from DOM on init
 *   2. Manage URL state via History API (pushState / replaceState)
 *   3. Normalise canvas URL params on load (layout, routing, compound, nodesize)
 *   4. Fetch graph data from /api/playbooks/<pk>/graph/ (implemented in graph iteration)
 *   5. Initialise Cytoscape.js and render graph (implemented in graph iteration)
 *
 * This file is plain browser JS. No build step, no framework, no import/export.
 * Loaded via <script> tag in browser_graph.html after CDN guard check.
 */

'use strict';

const _ALL_TYPES = ['workflow', 'activity', 'skill', 'agent', 'artifact', 'rule', 'phase'];

/**
 * Theme tokens for Cytoscape stylesheets (professional cool-cyan palette).
 * Cytoscape cannot consume CSS var() strings — values mirror design-system.css.
 * Optional runtime read: getComputedStyle(document.documentElement).getPropertyValue('--bs-primary')
 */
const _BOOTSTRAP_PALETTE = {
  primary: '#0d7ea8',
  success: '#198754',
  warning: '#ffc107',
  danger: '#dc3545',
  info: '#0dcaf0',
  secondary: '#6c757d',
  dark: '#343a40',
  light: '#f8f9fa',
  bodyColor: '#212529',
  white: '#ffffff',
  orange: '#fd7e14',
  borderColor: '#dee2e6',
  compoundWorkflowBg: '#e4f2f7',
  compoundActivityBg: '#e2f3ec',
};

/** Pastel node chrome — Bootstrap-tinted fills for enhanced graph mode (FOB-38). */
const _PASTEL_NODE_PALETTE = {
  playbook: { bg: '#d4eef7', border: '#6bb5cc', text: '#0a4a63' },
  workflow: { bg: '#cfe8f2', border: '#5aa8c2', text: '#0b5570' },
  activity: { bg: '#d4efe8', border: '#6bbfa8', text: '#0d4f40' },
  artifact: { bg: '#f5edd8', border: '#c9a96a', text: '#5c4a1a' },
  skill:    { bg: '#f3e4d6', border: '#c99a78', text: '#5c3a1f' },
  agent:    { bg: '#d6eef4', border: '#7abcc9', text: '#0d4f5c' },
  rule:     { bg: '#e4e8ed', border: '#a8b2c0', text: '#2a3340' },
};

const _PASTEL_NODE_DEFAULT = {
  bg: _BOOTSTRAP_PALETTE.light,
  border: _BOOTSTRAP_PALETTE.borderColor,
  text: _BOOTSTRAP_PALETTE.bodyColor,
};

/** Playbook status → Bootstrap badge class (mirrors Playbook.get_status_badge_color). */
const _PLAYBOOK_STATUS_BADGE = {
  active: 'success',
  draft: 'warning',
  released: 'primary',
  disabled: 'secondary',
};

/** Playbook status code → human-readable label (mirrors Playbook.STATUS_CHOICES). */
const _PLAYBOOK_STATUS_LABEL = {
  active: 'Active',
  draft: 'Draft',
  released: 'Released',
  disabled: 'Disabled',
};

/**
 * Position a JS-injected dropdown above its trigger (fixed coords avoid canvas clipping).
 * Visual styling uses Bootstrap dropdown-menu classes per IA guidelines.
 *
 * @param {HTMLElement} panel
 * @param {DOMRect} btnRect
 * @param {string} [minWidth='180px']
 */
function _positionBrowserDropdown(panel, btnRect, minWidth) {
  panel.classList.add('dropdown-menu', 'show');
  panel.style.position = 'fixed';
  panel.style.bottom = `${window.innerHeight - btnRect.top + 4}px`;
  panel.style.right = `${window.innerWidth - btnRect.right}px`;
  panel.style.zIndex = '1050';
  panel.style.minWidth = minWidth || '180px';
  panel.style.maxHeight = '60vh';
  panel.style.overflowY = 'auto';
}

/** @returns {HTMLDivElement} */
function _createDropdownHeader(testId, text) {
  const header = document.createElement('div');
  header.setAttribute('data-testid', testId);
  header.className = 'dropdown-header';
  header.textContent = text;
  return header;
}

/** @returns {HTMLButtonElement} */
function _createDropdownItem(testId, label, isActive, onSelect) {
  const item = document.createElement('button');
  item.setAttribute('data-testid', testId);
  item.type = 'button';
  item.className = 'dropdown-item' + (isActive ? ' active' : '');
  item.textContent = label + (isActive ? ' ✓' : '');
  item.addEventListener('click', onSelect);
  return item;
}

/**
 * Wire Escape / outside-click dismiss for a body-appended dropdown panel.
 *
 * @param {HTMLElement} panel
 * @param {HTMLElement} btn
 * @returns {{ remove: function(): void }}
 */
function _wireBrowserDropdownDismiss(panel, btn) {
  const remove = () => {
    panel.remove();
    document.removeEventListener('keydown', escHandler);
    document.removeEventListener('click', outsideHandler);
  };
  const escHandler = (e) => {
    if (e.key === 'Escape') remove();
  };
  const outsideHandler = (e) => {
    if (!panel.contains(e.target) && e.target !== btn) remove();
  };
  document.addEventListener('keydown', escHandler);
  setTimeout(() => document.addEventListener('click', outsideHandler), 0);
  return { remove };
}

/** Hide Bootstrap tooltip on a trigger so it does not block dropdown item clicks. */
function _hideButtonTooltip(btn) {
  if (typeof bootstrap !== 'undefined' && btn) {
    const tip = bootstrap.Tooltip.getInstance(btn);
    if (tip) tip.hide();
  }
}

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
const _DEFAULT_LAYOUT_KEY = 'elk-layered'; // module fallback default — see _LAYOUT_CATALOG
let _currentLayout = _DEFAULT_LAYOUT_KEY; // layout key — see _LAYOUT_CATALOG
let _customLayoutMode = false; // false = default mode (FOB-63)

/**
 * Full layout catalog used by the layout picker dropdown (FOB-19, FOB-34).
 * Each entry: { key, label, group }  — key is also the URL param value.
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
  _hideButtonTooltip(btn);

  const panel = document.createElement('div');
  panel.setAttribute('data-testid', 'browser-layout-dropdown');
  _positionBrowserDropdown(panel, btn.getBoundingClientRect());

  const dismiss = _wireBrowserDropdownDismiss(panel, btn);

  // Build grouped content from _LAYOUT_CATALOG.
  const seenGroups = [];
  _LAYOUT_CATALOG.forEach(e => {
    if (!seenGroups.some(g => g.slug === e.groupSlug)) {
      seenGroups.push({ slug: e.groupSlug, name: e.group });
    }
  });

  seenGroups.forEach(g => {
    panel.appendChild(_createDropdownHeader(`browser-layout-group-${g.slug}`, g.name));

    _LAYOUT_CATALOG.filter(e => e.groupSlug === g.slug).forEach(entry => {
      panel.appendChild(_createDropdownItem(
        `browser-layout-option-${entry.key}`,
        entry.label,
        _currentLayout === entry.key,
        () => {
          dismiss.remove();
          _applyLayout(entry.key);
        },
      ));
    });
  });

  document.body.appendChild(panel);
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
 * Parse URL query params for canvas display state.
 * Entity-type and phase filter params were removed with the filter toolbar (FOB-11/11b).
 *
 * @returns {{ types: string[], phases: number[] }} always all types, no phase filter
 */
function _parseUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const layoutRaw = params.get('layout');

  const legacyMap = { layered: 'elk-layered', mrtree: 'elk-mrtree' };
  const resolvedLayout = (layoutRaw && legacyMap[layoutRaw]) || layoutRaw;
  if (resolvedLayout && _LAYOUT_CATALOG.some(e => e.key === resolvedLayout)) {
    _currentLayout = resolvedLayout;
  } else {
    _currentLayout = _DEFAULT_LAYOUT_KEY;
  }

  _parseRoutingParam();
  _parseCompoundParam();
  _parseNodeSizeParam();

  return { types: _ALL_TYPES.slice(), phases: [] };
}

/**
 * Rewrite the browser URL to canonical canvas params (layout/routing/compound/nodesize).
 *
 * @param {{ types: string[], phases: number[] }} filters
 * @param {{ id: number, name: string }[]} _playbookPhases — unused (phase filter removed)
 * @returns {{ types: string[], phases: number[] }}
 */
function _normaliseFilters(filters, _playbookPhases) {
  _replaceCanonicalUrl(_getPlaybookPk(), filters);
  return filters;
}

/**
 * Serialise canvas display state to URL query string.
 * Entity-type and phase filter params are no longer encoded (FOB-11/11b removed).
 *
 * @param {{ types: string[], phases: number[] }} _filters — unused; kept for call-site compat
 * @returns {string} query string including leading '?' or '' if empty
 */
function _filtersToQueryString(_filters) {
  const parts = [];
  if (_currentLayout !== 'elk-layered') {
    parts.push('layout=' + _currentLayout);
  }
  if (_currentRouting !== 'bezier') {
    parts.push('routing=' + _currentRouting);
  }
  if (_compoundLevel !== 'none') {
    parts.push('compound=' + _compoundLevel);
  }
  if (_nodeSizeMode !== _DEFAULT_NODE_SIZE_MODE) {
    parts.push('nodesize=' + _nodeSizeMode);
  }
  return parts.length ? '?' + parts.join('&') : '';
}

/**
 * Update the browser URL when the active playbook changes (pushState).
 *
 * @param {number} pk - New playbook PK
 * @param {{ types: string[], phases: number[] }} _filters — unused; kept for E2E compat
 */
function _pushPlaybookUrl(pk, _filters) {
  const filters = { types: _ALL_TYPES.slice(), phases: [] };
  const qs = _filtersToQueryString(filters);
  const url = '/browser/' + pk + '/' + qs;
  history.pushState({ pk: pk, filters: filters }, '', url);
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
  const elements = _compoundLevel !== 'none'
    ? (_compoundLevel === 'workflow-activity'
        ? _buildWorkflowActivityCompoundElements(activeTypesSet)
        : _buildCompoundElements(activeTypesSet))
    : _buildFilteredElements(activeTypesSet);
  const initialStyle = _compoundLevel !== 'none'
    ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyleForLevel(_compoundLevel))
    : _cytoscapeStyleEnhanced();

  // Create cy without an initial layout — positions will be set by the explicit _runLayout()
  // call below (after listeners are registered). This avoids double-layout for async engines
  // (ELK) and missed-layoutstop for sync engines (Dagre, native Cytoscape layouts).
  window.cy = cytoscape({
    container, elements, style: initialStyle,
    layout: { name: 'null' },
    minZoom: 0.1, maxZoom: 3,
    minZoomedFontSize: 8,
  });
  window.cy.resize();
  requestAnimationFrame(() => { if (window.cy) window.cy.resize(); });

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
  // Hover tooltips — show full node label on mouseover.
  _initNodeTooltip(window.cy);

  // Re-run layout explicitly so the layoutstop listener above always fires at least once.
  // Sync layouts (e.g. Dagre) fire layoutstop during the cytoscape() constructor, before
  // the listener above is registered — this call ensures they are also tracked.
  _runLayout();

  // Apply phase/search dim (no type rebuild — cy was created with correct elements).
  _refreshVisualState();
}

/**
 * Return the Cytoscape stylesheet array.
 * Node labels are set via 'content' property (plain text — no innerHTML).
 *
 * @returns {object[]}
 */
function _cytoscapeStyle() {
  const P = _BOOTSTRAP_PALETTE;
  const _nodeBase = {
    'label': 'data(label)',
    'text-valign': 'center',
    'text-halign': 'center',
    'font-size': 11,
    'text-wrap': 'wrap',
    'text-max-width': 110,
    'width': 120,
    'height': 40,
    'color': P.white,
  };
  return [
    { selector: 'node[type = "workflow"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const abbr = ele.data('meta') && ele.data('meta').abbreviation;
                 return abbr ? `${abbr}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': P.primary, 'shape': 'round-rectangle',
               'width': 130, 'height': 50, 'font-size': 10 } },
    { selector: 'node[type = "activity"]',
      style: { ..._nodeBase,
               'label': function(ele) {
                 const code = ele.data('meta') && ele.data('meta').display_code;
                 return code ? `${code}\n${ele.data('label')}` : ele.data('label');
               },
               'background-color': P.success, 'shape': 'round-rectangle',
               'height': 50, 'font-size': 10, 'text-max-width': 110 } },
    { selector: 'node[type = "artifact"]',
      style: { ..._nodeBase, 'background-color': P.warning, 'shape': 'ellipse', 'color': P.bodyColor } },
    { selector: 'node[type = "skill"]',
      style: { ..._nodeBase, 'background-color': P.orange, 'shape': 'ellipse' } },
    { selector: 'node[type = "agent"]',
      style: { ..._nodeBase, 'background-color': P.info, 'shape': 'ellipse', 'color': P.bodyColor } },
    { selector: 'node[type = "rule"]',
      style: { ..._nodeBase, 'background-color': P.secondary, 'shape': 'ellipse' } },
    { selector: 'node:selected',
      style: { 'border-width': 3, 'border-color': _selectionBorderColor() } },
    // Edges — taxi (right-angle) routing for clean hierarchical layout.
    // 'contains' and 'predecessor' use downward/auto taxi; resource edges use
    // a shorter turn so they branch off activities cleanly.
    { selector: 'edge[relationship = "contains"]',
      style: { 'line-color': P.primary, 'target-arrow-color': P.primary, 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%', 'width': 2 } },
    { selector: 'edge[relationship = "predecessor"]',
      style: { 'line-color': P.success, 'target-arrow-color': P.success, 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'auto', 'taxi-turn': '50%',
               'width': 1, 'opacity': 0.7 } },
    { selector: 'edge[relationship = "sequence"]',
      style: { 'line-color': P.dark, 'target-arrow-color': P.dark, 'target-arrow-shape': 'triangle',
               'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '50%',
               'width': 2, 'opacity': 0.55 } },
    { selector: 'edge[relationship = "produces"]',
      style: { 'line-color': P.warning, 'target-arrow-color': P.warning, 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "consumes"]',
      style: { 'line-color': P.warning, 'target-arrow-color': P.warning, 'target-arrow-shape': 'triangle',
               'line-style': 'dashed', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5, 'opacity': 0.8 } },
    { selector: 'edge[relationship = "uses_skill"]',
      style: { 'line-color': P.orange, 'target-arrow-color': P.orange, 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "assigned_agent"]',
      style: { 'line-color': P.info, 'target-arrow-color': P.info, 'target-arrow-shape': 'triangle',
               'line-style': 'dotted', 'curve-style': 'taxi', 'taxi-direction': 'downward', 'taxi-turn': '30%',
               'width': 1.5 } },
    { selector: 'edge[relationship = "governed_by_rule"]',
      style: { 'line-color': P.secondary, 'target-arrow-color': P.secondary, 'target-arrow-shape': 'triangle',
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
  const filteredEdges = typeEdges;

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
 * Apply the combined visual state (phase dim, search dim) to canvas nodes and edges.
 * Also re-renders the structural tree so it stays in sync with the active filter.
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

  // Keep structural tree in sync.
  _renderStructureTree();
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

  // Section label stays compact; row labels inherit panel 0.875rem (no nested .small).
  let html = '<div class="fw-semibold text-muted text-uppercase mb-1 mt-2" style="font-size:0.75rem;">Structure</div>';
  wfNodes.forEach(wfNode => {
    const wfId    = wfNode.id();
    const abbr    = (wfNode.data('meta') || {}).abbreviation || '';
    const wfLabel = wfNode.data('label') || wfId;
    const sectionId = 'tree-wf-' + wfNode.data('entity_pk');

    // All activities ordered, then filtered by active phases.
    // In compound mode, "contains" edges are absent from window.cy; use compound
    // children instead (activities are direct children of workflow compound nodes).
    let actNodes = (_compoundLevel !== 'none'
      ? wfNode.children().filter(n => n.data('type') === 'activity')
      : wfNode.outgoers('edge[relationship="contains"]').targets()
    ).sort((a, b) => ((a.data('meta') || {}).order || 0) - ((b.data('meta') || {}).order || 0));

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
          <span class="browser-tree-toggle text-muted" data-section="${sectionId}">▸</span>
          ${abbr ? `<span class="text-muted" style="min-width:2.2em;font-size:0.8em;">${abbr}</span>` : ''}
          <span class="fw-semibold text-truncate" title="${wfLabel}">${wfLabel}</span>
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
            ${code ? `<span class="text-muted" style="min-width:2.8em;font-size:0.8em;">${code}</span>` : ''}
            <span class="text-truncate flex-grow-1" title="${actLabel}">${actLabel}</span>
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
  if (window.cy) {
    const node = window.cy.getElementById(nodeId);
    if (node && node.length) {
      window.cy.animate({ fit: { eles: node, padding: 80 } }, { duration: 400 });
      _openDetailPanel(node);
      return;
    }
  }
  // Node is filtered out — try tree row first (structural nodes), then full graph data
  // (resource nodes: agent/skill/rule/artifact have no tree rows).
  const row = document.querySelector(`[data-testid="browser-tree-row"][data-node-id="${nodeId}"]`);
  if (row) {
    const proxy = {
      id: () => nodeId,
      data: key => ({ embed_url: row.dataset.embedUrl || '', detail_url: row.dataset.detailUrl || '', type: row.dataset.nodeType || '' }[key]),
      style: () => 'hidden',
      length: 1,
    };
    _openDetailPanel(proxy);
    return;
  }
  // Fall back to full graph data cache (covers resource nodes not in tree).
  const nodeData = _fullGraphData ? (_fullGraphData.nodes || []).find(n => n.id === nodeId) : null;
  if (nodeData) {
    const proxy = {
      id: () => nodeId,
      data: key => ({ embed_url: nodeData.embed_url || '', detail_url: nodeData.detail_url || '', type: nodeData.type || '' }[key]),
      style: () => 'hidden',
      length: 1,
    };
    _openDetailPanel(proxy);
  }
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
  _expandTreeNodeAccordion(nodeId);
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
    container.innerHTML = '<span class="text-muted">No resources linked.</span>';
    return;
  }

  let html = '<div class="fw-semibold text-muted text-uppercase mb-1" style="font-size:0.75rem;">Resources</div>';
  _RESOURCE_ORDER.forEach(rType => {
    if (grouped[rType].size === 0) return;
    const label = rType.charAt(0).toUpperCase() + rType.slice(1) + 's';
    html += `<div class="text-muted mt-1 mb-1" style="font-size:0.8em;">${label}</div>`;
    grouped[rType].forEach((rNode, _epk) => {
      const icon  = _RESOURCE_ICONS[rType] || '';
      const label = rNode.data('label') || '';
      const nId   = rNode.id();
      html += `
        <div class="d-flex align-items-center gap-1 px-1 py-1 rounded browser-resource-row"
             data-node-id="${nId}" data-testid="browser-resource-row" style="cursor:pointer;"
             title="${label}">
          <span>${icon}</span>
          <span class="text-truncate">${label}</span>
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
  if (container) container.innerHTML = '<span class="text-muted">Select a Workflow to see its resources.</span>';
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
      window.cy.nodes().forEach(n => { n.style('border-width', 0); });
      node.style({ 'border-width': 3, 'border-color': _selectionBorderColor() });
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
 * Detect session expiry in fetched embed HTML.
 * If the login page is returned, redirect the tab.
 *
 * @param {string} html
 */
function _checkSessionExpiry(html) {
  if (
    html.includes('id="login-form"') ||
    html.includes('/auth/user/login/') ||
    html.includes('/auth/login/')
  ) {
    const pk = _getPlaybookPk();
    window.location.href = '/auth/user/login/?next=' + encodeURIComponent('/browser/' + (pk || '') + '/');
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
    _allPlaybooks = await _fetchAllPlaybooks();
    _renderPickerItems(_allPlaybooks);
  } catch (_) {
    _renderPickerError();
  }
}

/**
 * Fetch every accessible playbook, following DRF's paginated `next` link
 * so accounts with more than one page of results aren't silently truncated.
 * @returns {Promise<Array>}
 */
async function _fetchAllPlaybooks() {
  const results = [];
  let url = '/api/playbooks/';
  while (url) {
    const resp = await fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    });
    if (!resp.ok) throw new Error('Failed to fetch playbooks: ' + resp.status);
    const data = await resp.json();
    results.push(...(data.results || data));
    url = data.next || null;
  }
  return results;
}

/**
 * Render an error row in the picker list when the playbooks fetch fails.
 */
function _renderPickerError() {
  const list = document.getElementById('browser-picker-list');
  if (!list) return;
  list.innerHTML = '<div class="list-group-item text-danger small">Could not load playbooks. Please try again.</div>';
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
function _playbookStatusBadgeClass(status) {
  const key = (status || '').toLowerCase();
  return 'badge bg-' + (_PLAYBOOK_STATUS_BADGE[key] || 'secondary') + ' small';
}

function _playbookStatusLabel(status) {
  const key = (status || '').toLowerCase();
  return _PLAYBOOK_STATUS_LABEL[key] || status || '';
}

function _updatePlaybookHeader(pk, name, status) {
  const nameEl = document.querySelector('[data-testid="browser-playbook-title"]');
  if (nameEl) nameEl.textContent = name;
  const statusEl = document.querySelector('[data-testid="browser-playbook-status"]');
  if (statusEl) {
    statusEl.textContent = _playbookStatusLabel(status);
    statusEl.className = _playbookStatusBadgeClass(status);
  }

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

// ---------------------------------------------------------------------------
// Default/Custom layout mode (FOB-63)
// Default mode: klay + straight + workflow-activity compound; hides advanced buttons.
// Custom mode:  all buttons visible; user controls freely.
// ---------------------------------------------------------------------------

const _DEFAULT_LAYOUT_MODE_KEY = 'klay';
const _DEFAULT_ROUTING_MODE_KEY = 'straight';
const _DEFAULT_COMPOUND_MODE_KEY = 'workflow-activity';
const _DEFAULT_NODE_SIZE_MODE = 'fixed';

function _showCustomControls(visible) {
  document.querySelectorAll('.browser-custom-controls').forEach(el => {
    el.classList.toggle('d-none', !visible);
  });
}

function _applyDefaultLayoutMode() {
  _customLayoutMode = false;
  _showCustomControls(false);
  _applyLayout(_DEFAULT_LAYOUT_MODE_KEY);
  _applyRouting(_DEFAULT_ROUTING_MODE_KEY);
  _applyCompoundLevel(_DEFAULT_COMPOUND_MODE_KEY);
  if (_nodeSizeMode !== _DEFAULT_NODE_SIZE_MODE) {
    _nodeSizeMode = _DEFAULT_NODE_SIZE_MODE;
    _updateNodeSizeModeBtn();
    if (window.cy) {
      const style = _compoundLevel !== 'none'
        ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyleForLevel(_compoundLevel))
        : _cytoscapeStyleEnhanced();
      window.cy.style(style);
      _runLayout();
    }
  }
}

/**
 * True when URL query params explicitly request non-FOB-63-default canvas options.
 * Used at init to preserve deep-link layout/routing/compound/nodesize instead of
 * resetting via _applyDefaultLayoutMode().
 *
 * @returns {boolean}
 */
function _urlRequestsCustomCanvasMode() {
  const params = new URLSearchParams(window.location.search);
  const legacyMap = { layered: 'elk-layered', mrtree: 'elk-mrtree' };
  if (params.has('layout')) {
    const raw = params.get('layout');
    const resolved = legacyMap[raw] || raw;
    const isValid = _LAYOUT_CATALOG.some(e => e.key === resolved);
    if (isValid && resolved !== _DEFAULT_LAYOUT_MODE_KEY) return true;
  }
  if (params.has('routing')) {
    const raw = params.get('routing');
    const isValid = _ROUTING_CATALOG.some(e => e.key === raw);
    if (isValid && raw !== _DEFAULT_ROUTING_MODE_KEY) return true;
  }
  if (params.has('compound')) {
    const raw = params.get('compound');
    const resolved = raw === '1' ? 'workflow' : raw;
    const isValid = ['none', 'workflow', 'workflow-activity'].includes(resolved);
    if (isValid && resolved !== _DEFAULT_COMPOUND_MODE_KEY) return true;
  }
  if (params.has('nodesize')) {
    const raw = params.get('nodesize');
    const isValid = raw === 'auto' || raw === 'fixed';
    if (isValid && raw !== _DEFAULT_NODE_SIZE_MODE) return true;
  }
  return false;
}

function _applyCustomLayoutModeFromUrl() {
  _applyCustomLayoutMode();
  const toggle = document.querySelector('[data-testid="browser-custom-layout-toggle"]');
  if (toggle) toggle.checked = true;
  _updateLayoutBtn();
  _updateRoutingBtn();
  _updateCompoundBtn();
  _updateNodeSizeModeBtn();
}

function _applyCustomLayoutMode() {
  _customLayoutMode = true;
  _showCustomControls(true);
}

function _initCustomLayoutToggle() {
  const toggle = document.querySelector('[data-testid="browser-custom-layout-toggle"]');
  if (!toggle) return;
  toggle.checked = false;
  toggle.addEventListener('change', () => {
    if (toggle.checked) {
      _applyCustomLayoutMode();
    } else {
      _applyDefaultLayoutMode();
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Enhanced node visual styling (FOB-38)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Read a CSS custom property from the document root.
 *
 * @param {string} name — e.g. '--mimir-graph-edge'
 * @param {string} fallback
 * @returns {string}
 */
function _cssVar(name, fallback) {
  try {
    const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return value || fallback;
  } catch (err) {
    console.log('content-browser: css var read failed', { name: name, err: String(err) });
    return fallback;
  }
}

/** @returns {string} Selection ring colour for the active theme */
function _selectionBorderColor() {
  return _cssVar('--mimir-graph-select', '#0d7ea8');
}

/** @returns {string} Uniform edge colour for the active theme */
function _edgeColor() {
  return _cssVar('--mimir-graph-edge', '#5a6575');
}

/**
 * UI font stack from design tokens (IBM Plex Sans, with a system-font fallback).
 * Appends Font Awesome so node icon glyphs still render in labels.
 * Fallback string: keep in sync with --mimir-graph-font in design-system.css
 * and GRAPHVIZ_FONTNAME in activity_graph_service.py.
 *
 * @returns {string}
 */
function _graphFontFamily() {
  const base = _cssVar(
    '--mimir-graph-font',
    'IBM Plex Sans, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
  );
  return `${base}, "Font Awesome 6 Free", "Font Awesome 6 Pro"`;
}

/**
 * Compound / parent label font (no Font Awesome — text only).
 *
 * @returns {string}
 */
function _graphLabelFontFamily() {
  return _cssVar(
    '--mimir-graph-font',
    'IBM Plex Sans, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif'
  );
}

/**
 * Rebuild Cytoscape stylesheet from current theme tokens (light/dark toggle).
 * Preserves selection border on the open detail panel node when present.
 */
function _reapplyCytoscapeTheme() {
  if (!window.cy) return;
  const theme = document.documentElement.getAttribute('data-bs-theme') || 'light';
  console.log('content-browser: reapplying cytoscape theme styles', { theme: theme });
  const style = _compoundLevel !== 'none'
    ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyleForLevel(_compoundLevel))
    : _cytoscapeStyleEnhanced();
  window.cy.style(style);
  if (_currentPanelNode && _currentPanelNode.length) {
    _currentPanelNode.style({ 'border-width': 3, 'border-color': _selectionBorderColor() });
  }
}

/**
 * Watch data-bs-theme changes and restyle the graph when light/dark toggles.
 * Called once from _init().
 */
function _initThemeSync() {
  if (window._mimirBrowserThemeObserver) return;
  const observer = new MutationObserver(mutations => {
    for (const m of mutations) {
      if (m.type === 'attributes' && m.attributeName === 'data-bs-theme') {
        _reapplyCytoscapeTheme();
        break;
      }
    }
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-bs-theme'] });
  window._mimirBrowserThemeObserver = observer;
  console.log('content-browser: theme sync observer attached');
}

/**
 * Build the Cytoscape stylesheet with enhanced node shapes and Mimir design-aligned
 * visual style (FOB-38).
 *
 * @returns {object[]} Cytoscape stylesheet array
 */
function _cytoscapeStyleEnhanced() {
  const edgeStyles = _buildEdgeStyleForMode(_compoundLevel !== 'none');
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
    'label': ele => `${icon} ${ele.data('label') || ''}`,
    'text-valign': 'center',
    'text-halign': 'center',
    'font-family': _graphFontFamily(),
    'font-weight': 600,
    'text-wrap': 'ellipsis',
    'border-width': 2,
    'border-opacity': 1,
    'background-opacity': 1,
    'shape': 'round-rectangle',
    'background-color': colors.bg,
    'border-color': colors.border,
    'color': colors.text,
    'font-size': 13,
    'width': _nodeSizeMode === 'auto' ? 'label' : 180,
    'height': 60,
    'text-overflow-wrap': 'whitespace',
    ..._buildNodeTextOverflowStyle(_nodeSizeMode),
    ..._buildFontRenderingGuards(),
  };
}

/**
 * Return colour tokens for a given node type, read from CSS theme variables.
 *
 * Colours come from --mimir-graph-<type>-{bg,border,text} on the active
 * data-bs-theme, so nodes track light/dark automatically. Falls back to the
 * cool cyan-family light palette when a variable is unavailable.
 *
 * @param {string} type — entity type string
 * @returns {{ bg: string, border: string, text: string }}
 */
function _buildNodeColor(type) {
  const keys = {
    playbook: 'playbook',
    workflow: 'workflow',
    activity: 'activity',
    artifact: 'artifact',
    skill: 'skill',
    agent: 'agent',
    rule: 'rule',
  };
  const key = keys[type];
  if (!key) {
    return {
      bg: _cssVar('--mimir-bg-surface', '#f8f9fa'),
      border: _cssVar('--mimir-border', '#dee2e6'),
      text: _cssVar('--bs-body-color', '#212529'),
    };
  }
  return {
    bg: _cssVar(`--mimir-graph-${key}-bg`, '#e8ecf1'),
    border: _cssVar(`--mimir-graph-${key}-border`, '#a8b2c0'),
    text: _cssVar(`--mimir-graph-${key}-text`, '#1c2430'),
  };
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
  // All codepoints verified against FA6 Free solid (font-weight 900).
  // \uf542 = diagram-project, \uf0ae = list-check, \uf06b = gift
  // \ue05d = hand-sparkles, \uf5dc = brain, \uf24e = scale-balanced
  const icons = {
    playbook: '\uf5da',   // book-open-reader
    workflow: '\uf542',   // diagram-project
    activity: '\uf0ae',   // list-check
    artifact: '\uf06b',   // gift
    skill:    '\ue05d',   // hand-sparkles
    agent:    '\uf5dc',   // brain
    rule:     '\uf24e',   // scale-balanced
  };
  return icons[type] || '\uf111';
}

/**
 * Return edge stylesheet entries for the enhanced style.
 * All edges use a uniform theme-aware colour (--mimir-graph-edge via _edgeColor()).
 * Inherits curve-style from _currentRouting via _applyRouting().
 *
 * @returns {object[]} Cytoscape stylesheet entries for edges
 */
function _buildEdgeStyle() {
  return _buildEdgeStyleForMode(_compoundLevel !== 'none');
}

// ─────────────────────────────────────────────────────────────────────────────
// FOB-52 — Mode-aware edge style helper (skeleton — implemented in MIT)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Return edge stylesheet entries, aware of the current view mode.
 * In flat mode: 'contains' edges are VISIBLE (workflow→activity connections shown).
 * In compound mode: 'contains' edges are HIDDEN (they become compound parent-child relationships).
 *
 * @param {boolean} compoundOn — true when compound (grouped) view is active
 * @returns {object[]} Cytoscape stylesheet entries for edges
 */
function _buildEdgeStyleForMode(compoundOn) {
  const edge = _edgeColor();
  const base = [
    {
      selector: 'edge',
      style: {
        'line-color': edge,
        'target-arrow-color': edge,
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'width': 1.5,
        'opacity': 0.85,
      },
    },
    {
      selector: 'edge[relationship = "predecessor"]',
      style: {
        'line-style': 'dashed',
        'line-dash-pattern': [6, 3],
      },
    },
    {
      selector: 'edge[relationship = "contains"]',
      style: {
        'display': compoundOn ? 'none' : 'element',
      },
    },
  ];
  return base;
}

// ─────────────────────────────────────────────────────────────────────────────
// FOB-58 — Expand workflow accordion row (skeleton — implemented in MIT)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Expand the accordion section for a workflow node in the structure tree.
 * If workflowNodeId corresponds to a workflow row, expands its OWN section.
 * If workflowNodeId is an activity, expands the PARENT workflow's section.
 *
 * Called by _highlightTreeNode to ensure the highlighted node is visible.
 *
 * @param {string} nodeId — cy node ID (workflow or activity)
 */
function _expandTreeNodeAccordion(nodeId) {
  const targetRow = document.querySelector(`[data-testid="browser-tree-row"][data-node-id="${nodeId}"]`);
  if (!targetRow) return;

  // Workflow row: has a browser-tree-toggle span whose data-section is the accordion id.
  const toggle = targetRow.querySelector('.browser-tree-toggle');
  if (toggle && toggle.dataset.section) {
    _accordionWorkflow(toggle.dataset.section);
    return;
  }

  // Activity row: the section div is a SIBLING of the parent workflow row,
  // found by walking up to the containing <div class="mb-1"> then finding the section.
  let el = targetRow.parentElement;
  while (el) {
    if (el.id && el.id.startsWith('tree-wf-')) {
      _accordionWorkflow(el.id);
      return;
    }
    el = el.parentElement;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// S35 — Edge routing picker (FOB-35)
// ─────────────────────────────────────────────────────────────────────────────

/** Current edge routing key. Defaults to 'bezier'. Read by _filtersToQueryString. */
const _DEFAULT_ROUTING_KEY = 'bezier'; // module fallback default — see _ROUTING_CATALOG
let _currentRouting = _DEFAULT_ROUTING_KEY;

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
  { key: 'round-segments',    label: 'Round Segments',    cyValue: 'round-segments' },
  // S59 skeleton — straight-triangle entry (FOB-59)
  { key: 'straight-triangle', label: 'Straight Triangle', cyValue: 'straight-triangle' },
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
  _hideButtonTooltip(btn);

  const panel = document.createElement('div');
  panel.setAttribute('data-testid', 'browser-routing-dropdown');
  _positionBrowserDropdown(panel, btn.getBoundingClientRect());

  const dismiss = _wireBrowserDropdownDismiss(panel, btn);

  _ROUTING_CATALOG.forEach(entry => {
    panel.appendChild(_createDropdownItem(
      `browser-routing-option-${entry.key}`,
      entry.label,
      _currentRouting === entry.key,
      () => {
        dismiss.remove();
        _applyRouting(entry.key);
      },
    ));
  });

  document.body.appendChild(panel);
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
    _currentRouting = _DEFAULT_ROUTING_KEY;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// S37 — Workflow compound view toggle (FOB-37)
// ─────────────────────────────────────────────────────────────────────────────

/** Whether compound view mode is active. Derived alias kept for backward compat. */
let _compoundViewOn = false; // maintained as alias only — use _compoundLevel instead

// ─────────────────────────────────────────────────────────────────────────────
// S48 — Node size mode toggle (FOB-39)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Node size mode. One of:
 *   'fixed'  — all nodes are a uniform fixed size; long labels truncate with ellipsis.
 *   'auto'   — node width expands to fit label text; font size stays constant.
 * Initialised from URL param ?nodesize= (see _parseNodeSizeParam).
 */
let _nodeSizeMode = _DEFAULT_NODE_SIZE_MODE;

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
  _nodeSizeMode = _nodeSizeMode === 'fixed' ? 'auto' : 'fixed';
  _updateNodeSizeModeBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  if (!window.cy) return;
  const style = _compoundLevel !== 'none'
    ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyleForLevel(_compoundLevel))
    : _cytoscapeStyleEnhanced();
  window.cy.style(style);
  _runLayout();
}

/**
 * Update the node size mode button to reflect the current _nodeSizeMode.
 *   'fixed' → button text "Fixed size ✓",  adds class 'active'
 *   'auto'  → button text "Auto-width ✓",  adds class 'active'
 */
function _updateNodeSizeModeBtn() {
  const btn = document.querySelector('[data-testid="browser-node-size-toggle"]');
  if (!btn) return;
  if (_nodeSizeMode === 'fixed') {
    btn.textContent = 'Fixed size ✓';
    btn.classList.add('active');
  } else {
    btn.textContent = 'Auto-width ✓';
    btn.classList.remove('active');
  }
}

/**
 * Read ?nodesize= URL parameter and set _nodeSizeMode accordingly.
 * Valid values: 'fixed' (default), 'auto'.
 * Called once on page load before cy is initialised.
 */
function _parseNodeSizeParam() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('nodesize');
  if (raw === 'auto' || raw === 'fixed') {
    _nodeSizeMode = raw;
  } else {
    _nodeSizeMode = _DEFAULT_NODE_SIZE_MODE;
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
  const filteredEdges = nonContainsEdges;

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
  nodeData['elk:algorithm'] = 'layered';
  nodeData['elk:direction'] = 'DOWN';
  nodeData['elk:padding'] = '[top=30,left=10,bottom=10,right=10]';
}

/**
 * Return compound parent label style using the padding-top approach.
 *
 * @returns {object} Cytoscape style overrides for the :parent selector label
 */
function _buildCompoundLabelStyle() {
  return {
    'label': ele => ele.data('label') || '',
    'padding-top': '28px',
    'text-valign': 'top',
    'text-halign': 'center',
    'text-margin-x': 0,
    'text-margin-y': 4,
    'font-size': 20,
    'font-family': _graphLabelFontFamily(),
    'font-weight': 600,
    'text-transform': 'none',
    'text-max-width': 200,
    'text-wrap': 'ellipsis',
    'text-background-color': _cssVar('--mimir-graph-compound-label-bg', '#ffffff'),
    'text-background-opacity': 0.85,
    'text-background-padding': '4px',
    'color': _cssVar('--mimir-graph-compound-label', '#0a4a63'),
  };
}

/**
 * Return the Cytoscape stylesheet additions for compound parent (workflow) nodes.
 * These entries augment the base stylesheet when compound view is active:
 *   - background-color / border from --mimir-graph-compound-wf-* theme tokens
 *   - border-radius: 8px (via shape: round-rectangle)
 *   - text-valign: top, text-halign: center
 *   - padding via label style v2
 *
 * @returns {object[]} additional stylesheet entries for :parent selector
 */
function _cytoscapeCompoundStyle() {
  return [
    {
      selector: ':parent',
      style: {
        'background-color': _compoundBackgroundForType('workflow'),
        'border-color': _cssVar('--mimir-graph-compound-wf-border', '#0d7ea8'),
        'border-width': 2,
        'border-style': 'solid',
        'shape': 'round-rectangle',
        ..._buildCompoundLabelStyle(),
      },
    },
  ];
}

/**
 * Parse the ?compound= URL parameter and set _compoundLevel accordingly.
 * Delegates to _parseCompoundLevelParam (S61).
 * Kept for backward compat with existing call sites.
 */
function _parseCompoundParam() {
  _parseCompoundLevelParam();
}

// ─────────────────────────────────────────────────────────────────────────────
// S58 — Font all-caps fix skeleton (FOB-58)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Return explicit text-transform:none and min-zoomed-font-size style entry
 * to prevent all-caps rendering at extreme zoom levels.
 *
 * Expected output (when implemented):
 *   { 'text-transform': 'none' }
 *
 * @returns {object} Cytoscape style properties preventing all-caps rendering
 */
function _buildFontRenderingGuards() {
  return { 'text-transform': 'none' };
}

// ─────────────────────────────────────────────────────────────────────────────
// S59 — Straight-triangle routing catalog entry skeleton (FOB-59)
// ─────────────────────────────────────────────────────────────────────────────

// (Implementation: add { key: 'straight-triangle', label: 'Straight (Triangle)', cyValue: 'straight-triangle' }
//  to _ROUTING_CATALOG. No new function needed — skeleton is the catalog entry itself.)

/**
 * Return background colour for compound nodes by compound level and node type.
 *
 * @param {string} nodeType — 'workflow' or 'activity'
 * @returns {string} CSS colour string
 */
function _compoundBackgroundForType(nodeType) {
  if (nodeType === 'activity') {
    return _cssVar('--mimir-graph-compound-act-bg', '#e2f3ec');
  }
  return _cssVar('--mimir-graph-compound-wf-bg', '#e4f2f7');
}

// ─────────────────────────────────────────────────────────────────────────────
// S61 — 3-level compound grouping context menu (FOB-61)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Compound grouping level. One of:
 *   'none'               — flat mode; no compound boxes
 *   'workflow'           — workflows are compound parents for activities + resources
 *   'workflow-activity'  — workflows AND activities are compound parents
 * Initialised from URL param ?compound= (see _parseCompoundLevelParam).
 *
 * NOTE: replaces the old boolean _compoundViewOn (see FOB-61 migration).
 */
let _compoundLevel = 'none';

const _COMPOUND_OPTIONS = [
  { key: 'none',               label: 'No grouping' },
  { key: 'workflow',           label: 'Group by workflow' },
  { key: 'workflow-activity',  label: 'Group by workflow + activity' },
];

function _buildWorkflowActivityCompoundElements(activeTypes) {
  if (!_fullGraphData) return [];
  const { nodes, edges } = _fullGraphData;
  const resourceTypes = new Set(['skill', 'agent', 'rule', 'artifact']);

  const typeFilteredNodes = nodes.filter(n => activeTypes.has(n.type));
  const typeFilteredIds = new Set(typeFilteredNodes.map(n => n.id));

  const activityToWorkflow = new Map();
  edges.forEach(e => {
    if (e.relationship === 'contains' && typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target)) {
      activityToWorkflow.set(e.target, e.source);
    }
  });

  const nonContainsEdges = edges.filter(
    e => e.relationship !== 'contains' && typeFilteredIds.has(e.source) && typeFilteredIds.has(e.target)
  );

  const activityResourceMap = new Map();
  nonContainsEdges.forEach(e => {
    const targetNode = typeFilteredNodes.find(n => n.id === e.target);
    if (targetNode && resourceTypes.has(targetNode.type) && activityToWorkflow.has(e.source)) {
      if (!activityResourceMap.has(e.source)) activityResourceMap.set(e.source, new Set());
      activityResourceMap.get(e.source).add(e.target);
    }
    const sourceNode = typeFilteredNodes.find(n => n.id === e.source);
    if (sourceNode && resourceTypes.has(sourceNode.type) && activityToWorkflow.has(e.target)) {
      if (!activityResourceMap.has(e.target)) activityResourceMap.set(e.target, new Set());
      activityResourceMap.get(e.target).add(e.source);
    }
  });

  const resourceToActivity = new Map();
  activityResourceMap.forEach((resources, actId) => {
    resources.forEach(rId => resourceToActivity.set(rId, actId));
  });

  const connectedIds = new Set();
  nonContainsEdges.forEach(e => { connectedIds.add(e.source); connectedIds.add(e.target); });

  const finalNodes = typeFilteredNodes.filter(n => !resourceTypes.has(n.type) || connectedIds.has(n.id));

  const compoundNodes = finalNodes.map(n => {
    const nodeData = { ...n };
    if (n.type === 'workflow') {
      _addElkCompoundData(nodeData);
    } else if (n.type === 'activity') {
      const wfId = activityToWorkflow.get(n.id);
      if (wfId) nodeData.parent = wfId;
      if (activityResourceMap.has(n.id)) nodeData['elk:algorithm'] = 'layered';
    } else if (resourceTypes.has(n.type)) {
      const actId = resourceToActivity.get(n.id);
      if (actId) {
        nodeData.parent = actId;
      } else {
        const wfId = Array.from(activityToWorkflow.values()).find(
          wf => nonContainsEdges.some(e => (e.source === n.id || e.target === n.id))
        );
        if (wfId) nodeData.parent = wfId;
      }
    }
    return { data: nodeData };
  });

  const finalIds = new Set(finalNodes.map(n => n.id));
  const compoundEdges = nonContainsEdges
    .filter(e => finalIds.has(e.source) && finalIds.has(e.target))
    .filter(e => {
      // In workflow-activity mode, resource nodes are compound children of activity nodes.
      // Suppress edges between an activity and its own compound children — containment is implied.
      if (resourceToActivity.get(e.target) === e.source) return false;
      if (resourceToActivity.get(e.source) === e.target) return false;
      return true;
    })
    .map(e => ({ data: e }));

  return [...compoundNodes, ...compoundEdges];
}

function _cytoscapeCompoundStyleForLevel(level) {
  const base = _cytoscapeCompoundStyle();
  if (level !== 'workflow-activity') return base;
  return [
    ...base,
    {
      selector: 'node[type = "activity"]:parent',
      style: {
        'background-color': _compoundBackgroundForType('activity'),
        'border-color': _cssVar('--mimir-graph-compound-act-border', '#2a9b78'),
        'border-width': 2,
        ..._buildCompoundLabelStyle(),
      },
    },
  ];
}

function _toggleCompoundDropdown() {
  const existing = document.querySelector('[data-testid="browser-compound-dropdown"]');
  if (existing) { existing.remove(); return; }

  const btn = document.querySelector('[data-testid="browser-compound-btn"]');
  if (!btn) return;
  _hideButtonTooltip(btn);

  const panel = document.createElement('div');
  panel.setAttribute('data-testid', 'browser-compound-dropdown');
  _positionBrowserDropdown(panel, btn.getBoundingClientRect(), '200px');

  const dismiss = _wireBrowserDropdownDismiss(panel, btn);

  _COMPOUND_OPTIONS.forEach(opt => {
    panel.appendChild(_createDropdownItem(
      `browser-compound-option-${opt.key}`,
      opt.label,
      _compoundLevel === opt.key,
      () => {
        dismiss.remove();
        _applyCompoundLevel(opt.key);
      },
    ));
  });

  document.body.appendChild(panel);
}

function _applyCompoundLevel(level) {
  const valid = new Set(['none', 'workflow', 'workflow-activity']);
  if (!valid.has(level)) return;
  _compoundLevel = level;
  _updateCompoundBtn();
  _replaceCanonicalUrl(_getPkFromPath(), _currentFilters);
  if (!window.cy || !_fullGraphData) return;
  const activeTypes = new Set(_currentFilters.types);
  let elements;
  if (level === 'none') {
    elements = _buildFilteredElements(activeTypes);
  } else if (level === 'workflow-activity') {
    elements = _buildWorkflowActivityCompoundElements(activeTypes);
  } else {
    elements = _buildCompoundElements(activeTypes);
  }
  const style = level !== 'none'
    ? _cytoscapeStyleEnhanced().concat(_cytoscapeCompoundStyleForLevel(level))
    : _cytoscapeStyleEnhanced();
  window.cy.remove(window.cy.elements());
  window.cy.style(style);
  window.cy.add(elements);
  _renderStructureTree();
  _runLayout();
}

function _updateCompoundBtn() {
  const btn = document.querySelector('[data-testid="browser-compound-btn"]');
  if (!btn) return;
  const opt = _COMPOUND_OPTIONS.find(o => o.key === _compoundLevel) || _COMPOUND_OPTIONS[0];
  btn.textContent = opt.label + ' ▾';
  if (_compoundLevel !== 'none') {
    btn.classList.add('active');
  } else {
    btn.classList.remove('active');
  }
}

function _parseCompoundLevelParam() {
  const params = new URLSearchParams(window.location.search);
  const raw = params.get('compound');
  const valid = new Set(['none', 'workflow', 'workflow-activity']);
  // Backward compat: '1' from old URLs means 'workflow'.
  if (raw === '1') {
    _compoundLevel = 'workflow';
  } else if (valid.has(raw)) {
    _compoundLevel = raw;
  } else {
    _compoundLevel = 'none';
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// S62 — Node text/icon overflow fix skeleton (FOB-62)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Return text-max-width and text-wrap properties for a node in the current size mode.
 *
 * Expected output (when implemented):
 *   Fixed mode: { 'text-max-width': 96, 'text-wrap': 'ellipsis' }
 *   Auto mode:  { 'text-max-width': 999, 'text-wrap': 'none' }
 *
 * The text-max-width of 96 (fixed) leaves ~24px for the icon without clipping it.
 * The text-max-width of 999 (auto) effectively removes the constraint.
 *
 * @param {string} mode — 'fixed' or 'auto'
 * @returns {object} Cytoscape style properties for text overflow control
 */
function _buildNodeTextOverflowStyle(mode) {
  if (mode === 'auto') {
    return { 'text-max-width': 999, 'text-wrap': 'none' };
  }
  // Fixed mode: wrap text within node width leaving room for the icon (~24px).
  // Node width is 180px; max-text-width 150 keeps text inside with padding.
  return { 'text-max-width': 150, 'text-wrap': 'wrap' };
}

// ─────────────────────────────────────────────────────────────────────────────
// Node hover tooltip
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Create (or return existing) the floating tooltip DOM element used to display
 * the full node label on hover.  The element is appended to document.body so it
 * is unclipped by the canvas container's overflow:hidden.
 *
 * @returns {HTMLElement}
 */
function _createTooltipEl() {
  let el = document.getElementById('cy-node-tooltip');
  if (!el) {
    el = document.createElement('div');
    el.id = 'cy-node-tooltip';
    el.setAttribute('data-testid', 'cy-node-tooltip');
    // Appearance comes from #cy-node-tooltip in design-system.css (theme-aware).
    document.body.appendChild(el);
  }
  return el;
}

/**
 * Attach mouseover/mousemove/mouseout listeners to the given Cytoscape instance
 * so that a tooltip showing the full node label is displayed on hover.
 *
 * @param {cytoscape.Core} cy — Cytoscape instance
 */
function _initNodeTooltip(cy) {
  const tip = _createTooltipEl();

  cy.on('mouseover', 'node', function(evt) {
    const label = evt.target.data('label') || '';
    const type  = evt.target.data('type')  || '';
    tip.textContent = type ? `[${type}]  ${label}` : label;
    tip.style.display = 'block';
  });

  cy.on('mousemove', 'node', function(evt) {
    const oe = evt.originalEvent;
    if (!oe) return;
    tip.style.left = `${oe.clientX + 14}px`;
    tip.style.top  = `${oe.clientY - 10}px`;
  });

  cy.on('mouseout', 'node', function() {
    tip.style.display = 'none';
  });

  // Hide tooltip while the user pans or zooms so it never sticks.
  cy.on('pan zoom', function() {
    tip.style.display = 'none';
  });
}

/**
 * Wire event delegation on the detail panel content area so that
 * [data-navigate-canvas] links in embed templates navigate the canvas.
 *
 * Called once from _init(). Uses a single delegated listener on the
 * persistent panel container — works correctly when innerHTML is replaced
 * on every panel open.
 */
function _initPanelNavigation() {
  const panelContent = document.querySelector('[data-testid="browser-panel-content"]');
  if (!panelContent) return;
  panelContent.addEventListener('click', function(e) {
    const link = e.target.closest('[data-navigate-canvas]');
    if (!link) return;
    e.preventDefault();
    const nodeId = link.dataset.navigateCanvas;
    if (nodeId) _selectTreeNode(nodeId);
  });
}

/**
 * Main entry point — called on DOMContentLoaded.
 * Reads PK, normalises URL params, fetches graph if PK present.
 */
function _init() {
  const pk = _getPlaybookPk();
  const phases = _getPlaybookPhases();
  const customCanvasFromUrl = _urlRequestsCustomCanvasMode();
  const filters = _parseUrlParams();

  const panelClose = document.querySelector('[data-testid="browser-panel-close"]');
  if (panelClose) panelClose.addEventListener('click', _closeDetailPanel);

  _initPanelNavigation();
  _initCustomLayoutToggle();
  _initThemeSync();

  const toggleBtn = document.querySelector('[data-testid="browser-toggle-left-panel"]');
  if (toggleBtn) toggleBtn.addEventListener('click', _toggleLeftPanel);

  document.querySelectorAll('[data-testid="browser-change-playbook"], [data-testid="browser-select-playbook"]').forEach(btn => {
    btn.addEventListener('click', _openPicker);
  });

  const pickerSearch = document.querySelector('[data-testid="browser-picker-search"]');
  if (pickerSearch) pickerSearch.addEventListener('input', e => _filterPickerItems(e.target.value));

  const nodeSearch = document.querySelector('[data-testid="browser-search-input"]');
  if (nodeSearch) nodeSearch.addEventListener('input', e => _applySearch(e.target.value));

  if (!pk) {
    _normaliseFilters(filters, phases);
    _showEmptyState();
    return;
  }

  const zoomIn = document.querySelector('[data-testid="browser-zoom-in"]');
  const zoomOut = document.querySelector('[data-testid="browser-zoom-out"]');
  const zoomFit = document.querySelector('[data-testid="browser-zoom-fit"]');
  if (zoomIn) zoomIn.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() * 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomOut) zoomOut.addEventListener('click', () => window.cy && window.cy.zoom({ level: window.cy.zoom() / 1.3, renderedPosition: { x: window.cy.width() / 2, y: window.cy.height() / 2 } }));
  if (zoomFit) zoomFit.addEventListener('click', () => window.cy && window.cy.fit());

  const layoutBtn = document.querySelector('[data-testid="browser-layout-btn"]');
  if (layoutBtn) layoutBtn.addEventListener('click', _toggleLayoutDropdown);
  _updateLayoutBtn();

  const routingBtn = document.querySelector('[data-testid="browser-routing-btn"]');
  if (routingBtn) routingBtn.addEventListener('click', _toggleRoutingDropdown);
  _updateRoutingBtn();

  const compoundBtn = document.querySelector('[data-testid="browser-compound-btn"]');
  if (compoundBtn) compoundBtn.addEventListener('click', _toggleCompoundDropdown);
  _updateCompoundBtn();

  const nodeSizeToggle = document.querySelector('[data-testid="browser-node-size-toggle"]');
  if (nodeSizeToggle) nodeSizeToggle.addEventListener('click', _applyNodeSizeToggle);
  _updateNodeSizeModeBtn();

  const replotBtn = document.querySelector('[data-testid="browser-replot-btn"]');
  if (replotBtn) replotBtn.addEventListener('click', _replot);

  if (customCanvasFromUrl) {
    _applyCustomLayoutModeFromUrl();
  } else {
    _applyDefaultLayoutMode();
  }
  _normaliseFilters(filters, phases);
  _fetchGraph(pk);
}

window.cy = null;
Object.defineProperty(window, '_currentRouting', { get: () => _currentRouting });
Object.defineProperty(window, '_compoundViewOn', { get: () => _compoundLevel !== 'none' });
Object.defineProperty(window, '_compoundLevel', { get: () => _compoundLevel });
Object.defineProperty(window, '_nodeSizeMode', { get: () => _nodeSizeMode });
Object.defineProperty(window, '_customLayoutMode', { get: () => _customLayoutMode });
Object.defineProperty(window, '_currentLayout', { get: () => _currentLayout });
window._pushPlaybookUrl = _pushPlaybookUrl;
window._parseUrlParams = _parseUrlParams;
window._buildEdgeStyle = _buildEdgeStyle;
window._buildCompoundLabelStyle = _buildCompoundLabelStyle;

document.addEventListener('DOMContentLoaded', _init);
window.addEventListener('popstate', _onPopState);
